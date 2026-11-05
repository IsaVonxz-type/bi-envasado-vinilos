"""Recorta las capturas crudas de Power BI a la página del informe.

Uso: python recortar_capturas.py <carpeta con las capturas crudas> <carpeta de salida>
Los límites (72, 321, 2028, 1456) corresponden a una pantalla de 2560x1600 con la ventana maximizada.
Si su pantalla es distinta, ajústelos con las coordenadas del grupo «Informe de Power BI» (UI Automation).
"""
import sys
from pathlib import Path

from PIL import Image

NOMBRES = ["pbi_01_resumen", "pbi_02_paros", "pbi_03_confiabilidad", "pbi_04_capacidad", "pbi_05_calidad"]
crudas, destino = Path(sys.argv[1]), Path(sys.argv[2])
destino.mkdir(parents=True, exist_ok=True)
for nombre in NOMBRES:
    Image.open(crudas / f"{nombre}.png").convert("RGB").crop((72, 321, 2028, 1456)).save(destino / f"{nombre}.png", optimize=True)
    print("recortada", nombre)
