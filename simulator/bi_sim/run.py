import random
import signal
import sys
import threading
import time
from datetime import datetime, timedelta

import psycopg2

from . import almacen, calibracion, webhook
from .config import Config, ConfiguracionError
from .motor import Orden, generar_lectura

ESPERA_MODELO_SEGUNDOS = 5


def _esperar_modelo(cfg: Config, detener: threading.Event):
    """Espera a que el ETL haya cargado dw; devuelve una conexion lista."""
    while not detener.is_set():
        try:
            conexion = almacen.conectar(cfg)
            if calibracion.hay_datos(conexion):
                return conexion
            conexion.close()
            print("Esperando a que el ETL cargue el modelo dimensional...", flush=True)
        except psycopg2.OperationalError as error:
            print(f"Base de datos no disponible: {error}", flush=True)
        detener.wait(ESPERA_MODELO_SEGUNDOS)
    return None


def _generar(perfiles, ordenes, modos, hora, rng):
    return [
        generar_lectura(perfil, ordenes[maquina], modos.get(maquina, "normal"), hora, rng)
        for maquina, perfil in perfiles.items()
    ]


def main() -> int:
    try:
        cfg = Config.desde_entorno()
    except ConfiguracionError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1

    detener = threading.Event()
    listo = threading.Event()
    for senal in (signal.SIGTERM, signal.SIGINT):
        signal.signal(senal, lambda *_: detener.set())

    servidor = webhook.crear_servidor(cfg, lambda: almacen.conectar(cfg), listo)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    print(f"Receptor de alertas en el puerto {cfg.puerto_webhook}", flush=True)

    conexion = _esperar_modelo(cfg, detener)
    if conexion is None:
        return 0
    almacen.aplicar_ddl(conexion, cfg.ddl_dir)
    perfiles = calibracion.calibrar(conexion, cfg.calibracion_desde)
    almacen.sembrar_escenarios(conexion, perfiles)
    for perfil in perfiles.values():
        print(
            f"{perfil.maquina}: {len(perfil.causas)} causas, {len(perfil.referencias)} referencias, "
            f"rendimiento medio {perfil.rendimiento_medio:.1%}",
            flush=True,
        )

    rng = random.Random(cfg.semilla)
    ordenes = {maquina: Orden() for maquina in perfiles}
    intervalo = cfg.segundos_por_hora
    ahora = datetime.now().astimezone()

    ultima = almacen.ultima_hora_simulada(conexion)
    if ultima is None:
        hora = ahora.replace(minute=0, second=0, microsecond=0, tzinfo=None) - timedelta(hours=cfg.lecturas_iniciales)
        for i in range(cfg.lecturas_iniciales):
            ts = ahora - timedelta(seconds=intervalo * (cfg.lecturas_iniciales - i))
            almacen.insertar_lecturas(conexion, _generar(perfiles, ordenes, {}, hora, rng), ts)
            hora += timedelta(hours=1)
        print(f"Se generaron {cfg.lecturas_iniciales} lecturas iniciales por maquina", flush=True)
    else:
        hora = ultima + timedelta(hours=1)

    listo.set()
    print(f"Simulando 1 hora de produccion cada {intervalo:g} s", flush=True)
    proximo = time.monotonic() + intervalo
    ticks = 0
    while not detener.wait(max(0.0, proximo - time.monotonic())):
        proximo += intervalo
        try:
            modos = almacen.leer_modos(conexion)
            lecturas = _generar(perfiles, ordenes, modos, hora, rng)
            almacen.insertar_lecturas(conexion, lecturas, datetime.now().astimezone())
            hora += timedelta(hours=1)
            ticks += 1
            if ticks % 240 == 0:
                almacen.purgar(conexion, cfg.retencion_dias)
        except psycopg2.Error as error:
            print(f"Error de base de datos, se reintenta: {error}", flush=True)
            try:
                conexion.close()
            except psycopg2.Error:
                pass
            conexion = _esperar_modelo(cfg, detener)
            if conexion is None:
                break
    servidor.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
