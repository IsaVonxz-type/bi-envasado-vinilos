from pathlib import Path

import numpy as np
import pandas as pd
from psycopg2.extras import execute_values


def _nativo(valor):
    if valor is None or valor is pd.NaT:
        return None
    if isinstance(valor, float) and np.isnan(valor):
        return None
    if isinstance(valor, np.generic):
        return None if pd.isna(valor) else valor.item()
    if isinstance(valor, pd.Timestamp):
        return valor.to_pydatetime()
    return valor


def insertar(cursor, tabla: str, datos: pd.DataFrame) -> None:
    columnas = ", ".join(datos.columns)
    filas = [tuple(_nativo(valor) for valor in fila) for fila in datos.astype(object).itertuples(index=False, name=None)]
    execute_values(cursor, f"INSERT INTO {tabla} ({columnas}) VALUES %s", filas, page_size=1000)


def aplicar_ddl(cursor, directorio: Path) -> None:
    for archivo in sorted(directorio.glob("*.sql")):
        cursor.execute(archivo.read_text(encoding="utf-8"))


def cargar(cursor, resultado) -> None:
    for tabla, datos in resultado.dimensiones.items():
        insertar(cursor, f"dw.{tabla}", datos)
    for tabla, datos in resultado.hechos.items():
        insertar(cursor, f"dw.{tabla}", datos)
    insertar(cursor, "audit.calidad_datos", pd.DataFrame(resultado.calidad))
    insertar(cursor, "audit.conteo_filas", pd.DataFrame(resultado.conteos))
    insertar(cursor, "audit.cuadre_cifras", pd.DataFrame(resultado.cuadre))
