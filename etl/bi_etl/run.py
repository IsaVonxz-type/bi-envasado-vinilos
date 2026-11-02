import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import psycopg2

from .extract import extraer, sha256_archivo
from .load import aplicar_ddl, cargar
from .report import escribir_reporte
from .transform import transformar

SAL_POR_DEFECTO = "cambiar_esto"


def main() -> int:
    inicio = datetime.now(timezone.utc)
    ruta = Path(os.environ["SOURCE_PATH"])
    if not ruta.is_file():
        print(f"ERROR: no existe el archivo fuente {ruta}. Colóquelo en data/source/.", file=sys.stderr)
        return 1
    sal = os.environ.get("ANONYMIZATION_SALT", "")
    if not sal or sal == SAL_POR_DEFECTO:
        print("ERROR: defina ANONYMIZATION_SALT en .env con un valor propio.", file=sys.stderr)
        return 1

    print(f"Extrayendo {ruta.name}")
    sha256 = sha256_archivo(ruta)
    base, estandares = extraer(ruta)
    print(f"Filas leídas: {len(base):,}")

    resultado = transformar(base, estandares, sal)
    sin_cuadrar = [c["metrica"] for c in resultado.cuadre if not c["cuadra"]]
    if sin_cuadrar:
        print(f"ERROR: el cuadre falló en {sin_cuadrar}. No se cargó nada.", file=sys.stderr)
        return 1

    conexion = psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )
    try:
        with conexion, conexion.cursor() as cursor:
            aplicar_ddl(cursor, Path(os.environ["DDL_DIR"]))
            cargar(cursor, resultado)
            cursor.execute(
                "INSERT INTO audit.etl_ejecucion (inicio, fin, archivo_sha256, filas_fuente) VALUES (%s, %s, %s, %s)",
                (inicio, datetime.now(timezone.utc), sha256, len(base)),
            )
    finally:
        conexion.close()

    escribir_reporte(Path(os.environ["REPORT_DIR"]), resultado, sha256)
    for conteo in resultado.conteos:
        print(f"{conteo['etapa']}: {conteo['filas']:,}")
    print("Carga terminada; cuadre correcto.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
