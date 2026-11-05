"""Receptor HTTP de las alertas de Grafana (webhook) y comprobacion de salud del contenedor."""

import hmac
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from . import almacen

LIMITE_CUERPO = 64 * 1024


def _numero(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        return None
    return float(valor)


def extraer_alertas(carga: dict) -> list[dict]:
    """Normaliza la carga de Grafana a una fila por alerta."""
    filas = []
    for alerta in carga.get("alerts", []):
        etiquetas = alerta.get("labels", {}) or {}
        anotaciones = alerta.get("annotations", {}) or {}
        valores = alerta.get("values") or {}
        # A es la consulta (la medida observada); B es el resultado del umbral (0 o 1).
        valor = _numero(valores.get("A"))
        if valor is None:
            valor = next((n for n in map(_numero, valores.values()) if n is not None), None)
        estado = alerta.get("status", carga.get("status", ""))
        if estado not in ("firing", "resolved"):
            continue
        filas.append(
            {
                "estado": estado,
                "regla": etiquetas.get("alertname", "(sin nombre)"),
                "maquina": etiquetas.get("maquina"),
                "valor": valor,
                "severidad": etiquetas.get("severidad"),
                "resumen": anotaciones.get("summary") or anotaciones.get("description"),
            }
        )
    return filas


def crear_servidor(cfg, abrir_conexion, listo: threading.Event) -> ThreadingHTTPServer:
    class Manejador(BaseHTTPRequestHandler):
        def _responder(self, codigo: int, texto: str = "") -> None:
            cuerpo = texto.encode()
            self.send_response(codigo)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            self.end_headers()
            self.wfile.write(cuerpo)

        def do_GET(self):
            if self.path == "/salud":
                self._responder(200 if listo.is_set() else 503, "ok" if listo.is_set() else "iniciando")
            else:
                self._responder(404)

        def do_POST(self):
            if self.path != "/alertas":
                return self._responder(404)
            esperado = f"Bearer {cfg.token_webhook}"
            recibido = self.headers.get("Authorization", "")
            if not hmac.compare_digest(recibido, esperado):
                # Nunca se registra el valor: solo el esquema y la longitud, para diagnosticar.
                esquema = recibido.split(" ", 1)[0] if recibido else "(sin cabecera)"
                print(f"Entrega rechazada: esquema={esquema} longitud={len(recibido)} esperada={len(esperado)}", flush=True)
                return self._responder(401, "no autorizado")
            largo = int(self.headers.get("Content-Length", "0"))
            if largo <= 0 or largo > LIMITE_CUERPO:
                return self._responder(400, "cuerpo invalido")
            try:
                carga = json.loads(self.rfile.read(largo))
                filas = extraer_alertas(carga)
            except (ValueError, AttributeError):
                return self._responder(400, "json invalido")
            conexion = abrir_conexion()
            try:
                for fila in filas:
                    almacen.registrar_alerta(conexion, **fila)
            finally:
                conexion.close()
            print(f"Alertas recibidas: {len(filas)} ({', '.join(f['estado'] for f in filas)})", flush=True)
            self._responder(200, "ok")

        def log_message(self, formato, *argumentos):
            pass

    return ThreadingHTTPServer(("0.0.0.0", cfg.puerto_webhook), Manejador)
