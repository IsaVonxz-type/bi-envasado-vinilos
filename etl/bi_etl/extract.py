import hashlib
import re
from pathlib import Path

import openpyxl
import pandas as pd

from .catalogs import TABLAS_ESTANDAR

HOJA_BASE = "Base De Datos"
HOJA_CATALOGO = "Tablas Desplegables"
FILA_ENCABEZADO = 9
COLUMNAS_BASE = 58
COLUMNA_INICIO_ESTANDAR = 3
COLUMNA_FIN_ESTANDAR = 13

COLUMNAS = {
    0: "fecha",
    3: "maquina",
    4: "operario",
    5: "referencia",
    7: "unidad_por_display",
    9: "pacas",
    10: "horas_trabajadas",
    11: "turno",
    12: "horas_no_trabajadas",
    13: "tipo_paro",
    14: "observacion_paro",
    16: "subcodigo_1",
    21: "subcodigo_3",
    26: "subcodigo_5",
    28: "area_involucrada",
    29: "personal_involucrado",
    57: "observaciones",
}

ENCABEZADOS_ESPERADOS = {
    0: "Fecha",
    3: "Maquina",
    4: "Operario",
    5: "Referencia",
    9: "Pacas producidas",
    10: "Horas trabajadas",
    11: "Turno",
    12: "Horas no trabajadas",
    13: "Tipo de paro",
    16: "Sub Codigo de paro 1",
    21: "Subcodigo 3",
    26: "Subcodigo 5",
    29: "Personal involucrado",
    57: "Observaciones",
}


def sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _validar_encabezados(encabezados: list[str]) -> None:
    for posicion, esperado in ENCABEZADOS_ESPERADOS.items():
        if encabezados[posicion] != esperado:
            raise ValueError(
                f"Columna {posicion} inesperada: '{encabezados[posicion]}', se esperaba '{esperado}'"
            )


def extraer_base(libro) -> pd.DataFrame:
    hoja = libro[HOJA_BASE]
    filas = hoja.iter_rows(min_row=FILA_ENCABEZADO, max_col=COLUMNAS_BASE, values_only=True)
    encabezados = [str(valor).replace("\n", " ").strip() for valor in next(filas)]
    _validar_encabezados(encabezados)

    columnas_paro = {
        indice: f"min_{int(re.fullmatch(r'Codigo de paro (\d+)', nombre).group(1))}"
        for indice, nombre in enumerate(encabezados)
        if re.fullmatch(r"Codigo de paro \d+", nombre)
    }
    if len(columnas_paro) != 18:
        raise ValueError(f"Se esperaban 18 columnas de paro y hay {len(columnas_paro)}")

    nombres = {**COLUMNAS, **columnas_paro}
    registros = []
    for numero, fila in enumerate(filas, start=FILA_ENCABEZADO + 1):
        if fila[0] is None:
            continue
        registro = {nombre: fila[indice] for indice, nombre in nombres.items()}
        registro["fila_origen"] = numero
        registros.append(registro)
    return pd.DataFrame(registros)


def extraer_estandares(libro) -> pd.DataFrame:
    hoja = libro[HOJA_CATALOGO]
    registros = []
    for tabla, (inicio, fin) in TABLAS_ESTANDAR.items():
        filas = hoja.iter_rows(
            min_row=inicio,
            max_row=fin,
            min_col=COLUMNA_INICIO_ESTANDAR,
            max_col=COLUMNA_FIN_ESTANDAR,
            values_only=True,
        )
        for fila in filas:
            if fila[0] in (None, "maquina ") or fila[1] in (None, "Nombre de referencia"):
                continue
            registros.append(
                {
                    "tabla": tabla,
                    "maquina": fila[0],
                    "referencia": fila[1],
                    "unidades_por_paca": fila[5],
                    "unidades_por_minuto": fila[6],
                }
            )
    return pd.DataFrame(registros)


def extraer(ruta: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    libro = openpyxl.load_workbook(ruta, data_only=True, read_only=True)
    try:
        return extraer_base(libro), extraer_estandares(libro)
    finally:
        libro.close()
