import random
from datetime import datetime, timedelta

import pytest

from bi_sim.motor import Causa, Orden, Perfil, Referencia, generar_lectura, turno_de

HORA = datetime(2025, 3, 31, 6)


def causa(codigo, tasa, programado=False, es_falla=False):
    return Causa(codigo, f"[{codigo:02d}] causa", "General", "General", programado, es_falla, tasa)


def perfil(causas=None, rendimiento=0.9):
    causas = causas if causas is not None else (
        causa(1, 0.05, es_falla=True),
        causa(5, 3.0),
        causa(6, 3.0),
        causa(16, 5.0, programado=True),
    )
    return Perfil("Vinilos_9", tuple(causas), (Referencia("Ref A", 80.0, 1.0),), rendimiento)


def simular(perfil_, modo, horas, semilla=1):
    rng = random.Random(semilla)
    orden = Orden()
    return [generar_lectura(perfil_, orden, modo, HORA + timedelta(hours=h), rng) for h in range(horas)]


@pytest.mark.parametrize("hora,turno", [(6, "6am-2pm (Turno 1)"), (13, "6am-2pm (Turno 1)"), (14, "2pm-10pm (Turno 2)"),
                                        (21, "2pm-10pm (Turno 2)"), (22, "10pm-6am (Turno 3)"), (0, "10pm-6am (Turno 3)"),
                                        (5, "10pm-6am (Turno 3)")])
def test_turno_segun_la_hora(hora, turno):
    assert turno_de(hora) == turno


def test_es_reproducible_con_la_misma_semilla():
    assert simular(perfil(), "normal", 50, semilla=7) == simular(perfil(), "normal", 50, semilla=7)


@pytest.mark.parametrize("modo", ["normal", "degradado", "falla"])
def test_cumple_las_restricciones_de_la_tabla(modo):
    for lectura in simular(perfil(), modo, 400):
        assert lectura.minutos_programados + lectura.minutos_planificados == pytest.approx(60)
        assert lectura.minutos_operativos == pytest.approx(max(lectura.minutos_planificados - lectura.minutos_no_programados, 0))
        assert 0 <= lectura.minutos_no_programados <= lectura.minutos_planificados
        assert lectura.unidades_producidas >= 0 and lectura.unidades_teoricas >= 0
        no_prog = sum(p.minutos for p in lectura.paros if not p.causa.programado)
        prog = sum(p.minutos for p in lectura.paros if p.causa.programado)
        assert no_prog == pytest.approx(lectura.minutos_no_programados)
        assert prog == pytest.approx(lectura.minutos_programados)


def disponibilidad(lecturas):
    return sum(l.minutos_operativos for l in lecturas) / sum(l.minutos_planificados for l in lecturas)


def test_los_minutos_de_paro_respetan_la_tasa_historica():
    lecturas = simular(perfil(), "normal", 6000)
    esperado = 3.0 + 3.0 + 0.05  # minutos por hora de los paros no programados
    observado = sum(l.minutos_no_programados for l in lecturas) / len(lecturas)
    assert observado == pytest.approx(esperado, rel=0.1)
    programado = sum(l.minutos_programados for l in lecturas) / len(lecturas)
    assert programado == pytest.approx(5.0, rel=0.1)


def test_la_falla_hunde_la_disponibilidad_y_registra_una_causa_de_falla():
    normal = disponibilidad(simular(perfil(), "normal", 300))
    falla = simular(perfil(), "falla", 300)
    assert disponibilidad(falla) < normal - 0.4
    assert all(any(p.causa.es_falla for p in l.paros) for l in falla)


def test_el_modo_degradado_queda_entre_normal_y_falla():
    normal = disponibilidad(simular(perfil(), "normal", 2000))
    degradado = disponibilidad(simular(perfil(), "degradado", 2000))
    falla = disponibilidad(simular(perfil(), "falla", 2000))
    assert falla < degradado < normal


def test_sin_causas_de_falla_usa_una_generica():
    sin_fallas = perfil([causa(5, 3.0)])
    for lectura in simular(sin_fallas, "falla", 20):
        assert any(p.causa.es_falla and p.causa.codigo == 1 for p in lectura.paros)


def test_la_referencia_se_mantiene_durante_una_orden():
    dos = Perfil("V", (causa(5, 1.0),), (Referencia("A", 80, 1), Referencia("B", 60, 1)), 0.9)
    lecturas = simular(dos, "normal", 200)
    cambios = sum(1 for a, b in zip(lecturas, lecturas[1:]) if a.referencia != b.referencia)
    assert cambios < 10


def test_modo_desconocido_falla():
    with pytest.raises(ValueError):
        simular(perfil(), "caos", 1)


def test_unidades_son_teoricas_por_rendimiento():
    lectura = simular(perfil(rendimiento=1.0), "normal", 1)[0]
    assert lectura.unidades_teoricas == pytest.approx(lectura.minutos_operativos * 80, abs=0.01)
    assert lectura.unidades_producidas <= lectura.unidades_teoricas * 1.25 + 0.01
