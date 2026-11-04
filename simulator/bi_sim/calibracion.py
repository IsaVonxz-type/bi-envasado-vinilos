"""Calibra el simulador con el modelo dimensional: cada maquina se comporta como lo hizo en la historia."""

from datetime import date

from .motor import Causa, Perfil, Referencia

_HORAS = """
SELECT m.maquina_nk, SUM(COALESCE(p.horas_trabajadas, 0))
FROM dw.fact_produccion p
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
WHERE f.fecha >= %(desde)s
GROUP BY m.maquina_nk
"""

_PAROS = """
SELECT m.maquina_nk, c.codigo, c.codigo_nombre, c.sistema, c.subcodigo,
       c.clasificacion_oee = 'Programado', c.es_falla, SUM(x.minutos_paro)
FROM dw.fact_paro x
JOIN dw.dim_causa_paro c USING (causa_key)
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
WHERE f.fecha >= %(desde)s
GROUP BY m.maquina_nk, c.codigo, c.codigo_nombre, c.sistema, c.subcodigo, c.clasificacion_oee, c.es_falla
"""

_REFERENCIAS = """
SELECT m.maquina_nk, r.referencia_nk, e.unidades_por_minuto, SUM(p.horas_trabajadas)
FROM dw.fact_produccion p
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
JOIN dw.dim_referencia r USING (referencia_key)
JOIN dw.dim_estandar_produccion e USING (estandar_key)
WHERE f.fecha >= %(desde)s AND p.horas_trabajadas > 0
GROUP BY m.maquina_nk, r.referencia_nk, e.unidades_por_minuto
"""

# Mismo calculo que vw_oee_mensual: unidades producidas sobre unidades teoricas, solo donde hay estandar.
_RENDIMIENTO = """
SELECT m.maquina_nk, SUM(b.unidades_producidas) / NULLIF(SUM(b.unidades_teoricas), 0)
FROM dw.vw_oee_base b
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
WHERE f.fecha >= %(desde)s AND b.unidades_teoricas > 0
GROUP BY m.maquina_nk
"""


class CalibracionError(Exception):
    pass


def hay_datos(conexion) -> bool:
    """True si el ETL ya cargo el modelo dimensional."""
    with conexion.cursor() as cursor:
        cursor.execute("SELECT to_regclass('dw.fact_paro') IS NOT NULL AND to_regclass('dw.vw_oee_base') IS NOT NULL")
        if not cursor.fetchone()[0]:
            return False
        cursor.execute("SELECT EXISTS (SELECT 1 FROM dw.fact_produccion)")
        return cursor.fetchone()[0]


def calibrar(conexion, desde: date) -> dict[str, Perfil]:
    parametros = {"desde": desde}
    with conexion.cursor() as cursor:
        cursor.execute(_HORAS, parametros)
        horas = {maquina: float(valor) for maquina, valor in cursor.fetchall()}
        cursor.execute(_PAROS, parametros)
        paros = cursor.fetchall()
        cursor.execute(_REFERENCIAS, parametros)
        referencias = cursor.fetchall()
        cursor.execute(_RENDIMIENTO, parametros)
        rendimientos = {maquina: float(valor) for maquina, valor in cursor.fetchall()}

    perfiles = {}
    for maquina, horas_trabajadas in sorted(horas.items()):
        if horas_trabajadas <= 0:
            continue
        causas = tuple(
            Causa(codigo, nombre, sistema, subcodigo, bool(programado), bool(es_falla), float(minutos) / horas_trabajadas)
            for m, codigo, nombre, sistema, subcodigo, programado, es_falla, minutos in paros
            if m == maquina and minutos and minutos > 0
        )
        refs = tuple(
            Referencia(nombre, float(velocidad), float(h))
            for m, nombre, velocidad, h in referencias
            if m == maquina and h and h > 0
        )
        if not refs or maquina not in rendimientos:
            raise CalibracionError(f"{maquina}: no hay referencias con estandar desde {desde}.")
        perfiles[maquina] = Perfil(maquina, causas, refs, rendimientos[maquina])
    if not perfiles:
        raise CalibracionError(f"No hay produccion desde {desde}; revise SIM_CALIBRACION_DESDE.")
    return perfiles
