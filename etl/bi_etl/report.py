from pathlib import Path


def _tabla(encabezados: list[str], filas: list[list]) -> list[str]:
    lineas = ["| " + " | ".join(encabezados) + " |", "|" + "---|" * len(encabezados)]
    lineas.extend("| " + " | ".join(str(celda) for celda in fila) + " |" for fila in filas)
    return lineas


def _numero(valor: float) -> str:
    return f"{valor:,.2f}"


def escribir_reporte(directorio: Path, resultado, sha256: str) -> None:
    lineas = ["# Reporte de la última ejecución del ETL", "", f"Archivo fuente (SHA-256): `{sha256}`", "", "## Conteo de filas", ""]
    lineas += _tabla(["Etapa", "Filas"], [[c["etapa"], f"{c['filas']:,}"] for c in resultado.conteos])
    lineas += ["", "## Cuadre de cifras", ""]
    lineas += _tabla(
        ["Métrica", "Unidad", "Fuente", "Excluido", "Esperado", "Cargado", "Diferencia", "Cuadra", "Explicación"],
        [
            [
                c["metrica"], c["unidad"], _numero(c["fuente"]), _numero(c["excluido"]), _numero(c["esperado"]),
                _numero(c["cargado"]), _numero(c["diferencia"]), "Sí" if c["cuadra"] else "No", c["explicacion"],
            ]
            for c in resultado.cuadre
        ],
    )
    lineas += ["", "## Reglas de calidad de datos", ""]
    lineas += _tabla(
        ["Regla", "Problema", "Tratamiento", "Afectados", "Unidad"],
        [[c["regla"], c["descripcion"], c["tratamiento"], f"{c['afectados']:,}", c["unidad"]] for c in resultado.calidad],
    )
    directorio.mkdir(parents=True, exist_ok=True)
    (directorio / "reporte_etl.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")
