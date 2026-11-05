import pytest

from bi_sim.config import Config, ConfiguracionError
from bi_sim.webhook import extraer_alertas

BASE = {"DB_HOST": "db", "DB_PORT": "5432", "DB_NAME": "x", "DB_USER": "u", "DB_PASSWORD": "p", "ALERT_WEBHOOK_TOKEN": "t0k3n"}


def test_extrae_una_fila_por_alerta():
    carga = {
        "status": "firing",
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "Disponibilidad baja", "maquina": "Vinilos_2", "severidad": "critica"},
                "annotations": {"summary": "Vinilos_2 por debajo del umbral"},
                "values": {"A": 41.5, "B": 1},
            },
            {"status": "resolved", "labels": {"alertname": "Disponibilidad baja", "maquina": "Vinilos_3"}, "values": {"A": 80, "B": 0}},
        ],
    }
    filas = extraer_alertas(carga)
    assert [f["estado"] for f in filas] == ["firing", "resolved"]
    assert filas[0] == {
        "estado": "firing", "regla": "Disponibilidad baja", "maquina": "Vinilos_2", "valor": 41.5,
        "severidad": "critica", "resumen": "Vinilos_2 por debajo del umbral",
    }
    assert filas[1]["valor"] == 80


def test_ignora_estados_desconocidos_y_valores_no_numericos():
    carga = {"alerts": [{"status": "pending", "labels": {}}, {"status": "firing", "labels": {}, "values": {"A": "x"}}]}
    filas = extraer_alertas(carga)
    assert len(filas) == 1 and filas[0]["valor"] is None and filas[0]["regla"] == "(sin nombre)"


def test_config_lee_el_entorno_y_aplica_valores_por_defecto():
    cfg = Config.desde_entorno(BASE)
    assert cfg.segundos_por_hora == 15 and cfg.puerto_webhook == 8080 and cfg.semilla is None
    assert Config.desde_entorno({**BASE, "SIM_SEMILLA": "3", "SIM_SEGUNDOS_POR_HORA": "2.5"}).semilla == 3


@pytest.mark.parametrize("cambio", [{"ALERT_WEBHOOK_TOKEN": ""}, {"ALERT_WEBHOOK_TOKEN": "cambiar_esto"}, {"DB_HOST": ""},
                                    {"SIM_SEGUNDOS_POR_HORA": "0"}])
def test_config_rechaza_valores_inseguros_o_incompletos(cambio):
    with pytest.raises(ConfiguracionError):
        Config.desde_entorno({**BASE, **cambio})
