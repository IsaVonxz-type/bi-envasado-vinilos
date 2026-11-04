"""Acceso a la base de datos para el esquema ops."""

from datetime import datetime, timedelta
from pathlib import Path

import psycopg2

from .motor import Lectura


def conectar(cfg):
    conexion = psycopg2.connect(
        host=cfg.db_host, port=cfg.db_port, dbname=cfg.db_name, user=cfg.db_user, password=cfg.db_password
    )
    conexion.autocommit = False
    return conexion


def aplicar_ddl(conexion, directorio: str) -> None:
    with conexion.cursor() as cursor:
        for archivo in sorted(Path(directorio).glob("*.sql")):
            cursor.execute(archivo.read_text(encoding="utf-8"))
    conexion.commit()


def sembrar_escenarios(conexion, maquinas) -> None:
    with conexion.cursor() as cursor:
        for maquina in maquinas:
            cursor.execute("INSERT INTO ops.escenario (maquina) VALUES (%s) ON CONFLICT DO NOTHING", (maquina,))
    conexion.commit()


def leer_modos(conexion) -> dict[str, str]:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT maquina, modo FROM ops.escenario")
        modos = dict(cursor.fetchall())
    conexion.commit()
    return modos


def ultima_hora_simulada(conexion) -> datetime | None:
    with conexion.cursor() as cursor:
        cursor.execute("SELECT MAX(hora_simulada) FROM ops.lectura_hora")
        valor = cursor.fetchone()[0]
    conexion.commit()
    return valor


def insertar_lecturas(conexion, lecturas: list[Lectura], ts: datetime) -> None:
    with conexion.cursor() as cursor:
        for lectura in lecturas:
            cursor.execute(
                """
                INSERT INTO ops.lectura_hora
                    (ts, hora_simulada, maquina, turno, referencia, escenario, minutos_programados,
                     minutos_planificados, minutos_no_programados, minutos_operativos,
                     unidades_teoricas, unidades_producidas)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING lectura_id
                """,
                (
                    ts, lectura.hora_simulada, lectura.maquina, lectura.turno, lectura.referencia, lectura.escenario,
                    lectura.minutos_programados, lectura.minutos_planificados, lectura.minutos_no_programados,
                    lectura.minutos_operativos, lectura.unidades_teoricas, lectura.unidades_producidas,
                ),
            )
            lectura_id = cursor.fetchone()[0]
            for paro in lectura.paros:
                causa = paro.causa
                cursor.execute(
                    """
                    INSERT INTO ops.paro_hora
                        (lectura_id, ts, maquina, codigo, causa, sistema, subcodigo, clasificacion, es_falla, minutos)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        lectura_id, ts, lectura.maquina, causa.codigo, causa.nombre, causa.sistema, causa.subcodigo,
                        "Programado" if causa.programado else "No programado", causa.es_falla, paro.minutos,
                    ),
                )
    conexion.commit()


def purgar(conexion, retencion_dias: int) -> int:
    with conexion.cursor() as cursor:
        cursor.execute(
            "DELETE FROM ops.lectura_hora WHERE ts < %s", (datetime.now().astimezone() - timedelta(days=retencion_dias),)
        )
        borradas = cursor.rowcount
        cursor.execute(
            "DELETE FROM ops.alerta_recibida WHERE recibido_en < %s",
            (datetime.now().astimezone() - timedelta(days=retencion_dias * 10),),
        )
    conexion.commit()
    return borradas


def registrar_alerta(conexion, estado, regla, maquina, valor, severidad, resumen) -> None:
    with conexion.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO ops.alerta_recibida (estado, regla, maquina, valor, severidad, resumen)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (estado, regla[:120], maquina, valor, severidad, resumen),
        )
    conexion.commit()
