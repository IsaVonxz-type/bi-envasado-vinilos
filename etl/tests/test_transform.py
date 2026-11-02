import pandas as pd
import pytest

from bi_etl import anonymize
from bi_etl.catalogs import CODIGOS, SUBCODIGOS
from bi_etl.transform import (
    COLUMNAS_MINUTOS,
    atributos_referencia,
    formato_referencia,
    normalizar_motivo,
    normalizar_subcodigo,
    normalizar_turno,
    transformar,
)

SAL = "sal-de-prueba"


def fila(numero, **valores):
    base = {
        "fila_origen": numero,
        "fecha": pd.Timestamp("2024-03-20"),
        "maquina": "Vinilos_1",
        "operario": "Persona Prueba",
        "referencia": "Kids 22cc (6 col)",
        "unidad_por_display": None,
        "pacas": None,
        "horas_trabajadas": None,
        "turno": "6am-2pm (Turno 1)",
        "horas_no_trabajadas": None,
        "tipo_paro": None,
        "observacion_paro": None,
        "subcodigo_1": None,
        "subcodigo_3": None,
        "subcodigo_5": None,
        "area_involucrada": None,
        "personal_involucrado": None,
        "observaciones": None,
    }
    base.update({columna: None for columna in COLUMNAS_MINUTOS})
    base.update(valores)
    return base


def estandares():
    return pd.DataFrame(
        [{"tabla": "Tabla8", "maquina": "Vinilos_1", "referencia": "Kids 22cc (6 col)", "unidades_por_paca": 600, "unidades_por_minuto": 86}]
    )


def cuadre(resultado, metrica):
    return next(c for c in resultado.cuadre if c["metrica"] == metrica)


def regla(resultado, codigo):
    return next(c for c in resultado.calidad if c["regla"] == codigo)["afectados"]


@pytest.mark.parametrize(
    "crudo,esperado",
    [
        ("1.2C  CAMBIO DE VALVULA ", "1.2.C"),
        ("1.2.C Cambio de Valvula", "1.2.C"),
        ("1.2A  CAMBIO DE RAGORES ", "1.2.A"),
        ("1.4.3 Sensor", "1.4.C"),
        ("1.7A CAMBIO DE ROSCADORES ", "1.7.B"),
        ("1.6 VIDEO JET", "1.6"),
        ("4.2  SISTEMA DOSIFICADOR DE PINTURA, FRONTAL Y POSTERIOR.", "5.2"),
        ("4.5  SISTEMA ALIMENTADOR DE TAPA. YBTOBOGAN ", "5.6"),
        ("5.11 Lavado de boquilla", "5.11"),
        ("Sin especificar", None),
        (None, None),
    ],
)
def test_subcodigos_se_unifican_al_catalogo(crudo, esperado):
    assert normalizar_subcodigo(crudo) == esperado


def test_todo_alias_apunta_a_un_subcodigo_existente():
    from bi_etl.catalogs import SUBCODIGO_ALIAS

    assert set(SUBCODIGO_ALIAS.values()) <= set(SUBCODIGOS)


@pytest.mark.parametrize(
    "crudo,esperado",
    [
        ("Alocdor 22cc (6col)", "Alocolor 22cc (6 col)"),
        ("Stilo Kids 22cc (6 col)", "Estilo Kids 22cc (6 col)"),
        ("Klips 15cc (12col)", "Klips 15cc (12 col)"),
        ("Arti 30 cc (7 col)", "Arti 30cc (7 col)"),
    ],
)
def test_referencias_se_normalizan(crudo, esperado):
    assert formato_referencia(crudo) == esperado


def test_atributos_de_referencia():
    assert atributos_referencia("Klips 15cc (12 col)") == {"familia": "Klips", "volumen_cc": 15, "colores": 12}


def test_turno_vacio_y_alias():
    assert normalizar_turno(None) == "Desconocido"
    assert normalizar_turno("6am-2pm") == "6am-2pm (Turno 1)"


def test_motivo_corrige_errores_y_unifica_mayusculas():
    assert normalizar_motivo("SEMANA DE RESESO") == normalizar_motivo("Semana de reseso") == "Semana de receso"


def test_nombre_de_pila_no_se_une_a_nombre_completo():
    grupos = anonymize.agrupar_variantes(["Zoe", "Zoe Q.", "Zoe Ficticia Inventada"])
    assert grupos["ZOE"] == "ZOE"
    assert grupos["ZOE Q"] == "ZOE Q"


def test_variantes_de_nombre_completo_se_unen():
    grupos = anonymize.agrupar_variantes(["Zoe Inventada", "Zoe Ficticia Inventada Prueba", "Zoe Ficticia Inventada Prueva"])
    assert len(set(grupos.values())) == 1


def test_seudonimo_estable_y_sin_el_nombre():
    primero = anonymize.seudonimo("PERSONA PRUEBA", SAL)
    assert primero == anonymize.seudonimo("PERSONA PRUEBA", SAL)
    assert primero != anonymize.seudonimo("PERSONA PRUEBA", "otra-sal")
    assert "PERSONA" not in primero


def test_ningun_nombre_llega_a_las_tablas():
    base = pd.DataFrame([fila(10, pacas=40, horas_trabajadas=8, min_5=30, subcodigo_5="5.7 Video Jet", personal_involucrado="Tecnico Secreto Uno")])
    resultado = transformar(base, estandares(), SAL)
    tablas = {**resultado.dimensiones, **resultado.hechos}
    contenido = " ".join(tabla.astype(str).to_csv() for tabla in tablas.values()).upper()
    assert "PERSONA PRUEBA" not in contenido
    assert "SECRETO" not in contenido


def test_fila_solo_con_horas_no_trabajadas_no_se_elimina():
    base = pd.DataFrame(
        [fila(10, operario=None, referencia=None, turno=None, horas_no_trabajadas=24, tipo_paro="[18] Paro de maquina por ventas", observacion_paro="No aplica")]
    )
    resultado = transformar(base, estandares(), SAL)
    assert regla(resultado, "R01") == 0
    assert resultado.hechos["fact_no_operacion"]["horas_ajustadas"].sum() == 24


def test_fila_realmente_vacia_se_elimina():
    resultado = transformar(pd.DataFrame([fila(10, pacas=40, horas_trabajadas=8), fila(11)]), estandares(), SAL)
    assert regla(resultado, "R01") == 1
    assert len(resultado.hechos["fact_produccion"]) == 1


def test_duplicado_con_produccion_se_excluye_y_el_cuadre_lo_explica():
    base = pd.DataFrame([fila(10, pacas=40, horas_trabajadas=8, min_5=30), fila(11, pacas=40, horas_trabajadas=8, min_5=30)])
    resultado = transformar(base, estandares(), SAL)
    assert regla(resultado, "R02") == 1
    pacas = cuadre(resultado, "pacas")
    assert (pacas["fuente"], pacas["excluido"], pacas["cargado"], pacas["cuadra"]) == (80, 40, 40, True)
    assert cuadre(resultado, "minutos_paro")["cargado"] == 30


def test_paro_repetido_sin_produccion_se_conserva():
    base = pd.DataFrame([fila(10, pacas=40, horas_trabajadas=8), fila(11, min_5=10), fila(12, min_5=10)])
    resultado = transformar(base, estandares(), SAL)
    assert regla(resultado, "R03") == 1
    assert resultado.hechos["fact_paro"]["minutos_paro"].sum() == 20


def test_pacas_imposibles_quedan_reportadas_pero_no_validas():
    resultado = transformar(pd.DataFrame([fila(10, pacas=9000, horas_trabajadas=8)]), estandares(), SAL)
    hecho = resultado.hechos["fact_produccion"].iloc[0]
    assert hecho["pacas_reportadas"] == 9000
    assert pd.isna(hecho["pacas_validas"])
    assert hecho["alerta_pacas_atipicas"]
    assert pd.isna(hecho["unidades_producidas"])
    assert cuadre(resultado, "pacas")["cuadra"]


def test_paro_con_cero_horas_trabajadas_queda_con_alerta():
    resultado = transformar(pd.DataFrame([fila(10, pacas=0, horas_trabajadas=0, min_6=30)]), estandares(), SAL)
    assert regla(resultado, "R09") == 1
    assert resultado.hechos["fact_produccion"].iloc[0]["alerta_paro_excede"]


def test_unidades_usan_el_estandar_de_la_referencia():
    resultado = transformar(pd.DataFrame([fila(10, pacas=40, horas_trabajadas=8)]), estandares(), SAL)
    assert resultado.hechos["fact_produccion"].iloc[0]["unidades_producidas"] == 24000


def test_referencia_ausente_no_tiene_estandar():
    resultado = transformar(pd.DataFrame([fila(10, referencia=None, pacas=40, horas_trabajadas=8)]), estandares(), SAL)
    hecho = resultado.hechos["fact_produccion"].iloc[0]
    assert pd.isna(hecho["estandar_key"])
    assert regla(resultado, "R25") == 1


def test_horas_no_trabajadas_repetidas_se_limitan_al_dia():
    tipo = "[18] Paro de maquina por ventas"
    base = pd.DataFrame(
        [
            fila(10, pacas=11, horas_trabajadas=8, horas_no_trabajadas=16, tipo_paro=tipo, observacion_paro="No aplica"),
            fila(11, pacas=12, horas_trabajadas=8, horas_no_trabajadas=16, tipo_paro=tipo, observacion_paro="No aplica"),
        ]
    )
    resultado = transformar(base, estandares(), SAL)
    hecho = resultado.hechos["fact_no_operacion"].iloc[0]
    assert (hecho["horas_reportadas"], hecho["horas_ajustadas"]) == (32, 8)
    assert regla(resultado, "R23") == 1


def test_subcodigo_de_otro_codigo_detiene_el_proceso():
    base = pd.DataFrame([fila(10, min_1=30, subcodigo_1="5.7 Video Jet")])
    with pytest.raises(ValueError, match="no reconocidos"):
        transformar(base, estandares(), SAL)


def test_medida_negativa_detiene_el_proceso():
    with pytest.raises(ValueError, match="negativas"):
        transformar(pd.DataFrame([fila(10, pacas=-1, horas_trabajadas=8)]), estandares(), SAL)


def test_catalogo_de_paros_completo_y_programados_segun_fuente():
    assert set(CODIGOS) == set(range(1, 19))
    assert {codigo for codigo, datos in CODIGOS.items() if datos[2]} == {15, 16, 17}
