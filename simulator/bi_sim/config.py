import os
from dataclasses import dataclass
from datetime import date


class ConfiguracionError(Exception):
    pass


@dataclass(frozen=True)
class Config:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    ddl_dir: str
    segundos_por_hora: float
    lecturas_iniciales: int
    retencion_dias: int
    calibracion_desde: date
    semilla: int | None
    token_webhook: str
    puerto_webhook: int

    @classmethod
    def desde_entorno(cls, entorno=None) -> "Config":
        e = os.environ if entorno is None else entorno
        faltan = [k for k in ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD") if not e.get(k)]
        if faltan:
            raise ConfiguracionError(f"Faltan variables de entorno: {', '.join(faltan)}")
        token = e.get("ALERT_WEBHOOK_TOKEN", "")
        if not token or token == "cambiar_esto":
            raise ConfiguracionError("Defina ALERT_WEBHOOK_TOKEN en .env con un valor propio.")
        segundos = float(e.get("SIM_SEGUNDOS_POR_HORA", "15"))
        if segundos <= 0:
            raise ConfiguracionError("SIM_SEGUNDOS_POR_HORA debe ser mayor que cero.")
        semilla = e.get("SIM_SEMILLA", "")
        return cls(
            db_host=e["DB_HOST"],
            db_port=int(e["DB_PORT"]),
            db_name=e["DB_NAME"],
            db_user=e["DB_USER"],
            db_password=e["DB_PASSWORD"],
            ddl_dir=e.get("OPS_DDL_DIR", "/app/sql/ops"),
            segundos_por_hora=segundos,
            lecturas_iniciales=int(e.get("SIM_LECTURAS_INICIALES", "40")),
            retencion_dias=int(e.get("SIM_RETENCION_DIAS", "3")),
            calibracion_desde=date.fromisoformat(e.get("SIM_CALIBRACION_DESDE", "2024-01-01")),
            semilla=int(semilla) if semilla else None,
            token_webhook=token,
            puerto_webhook=int(e.get("WEBHOOK_PORT", "8080")),
        )
