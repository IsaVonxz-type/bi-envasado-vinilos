# Generación del PDF entregable

El PDF `BI_ProyectoFinal_Madera_Montoya.pdf` se genera a partir de la documentación del repositorio, de modo que siempre queda sincronizado con ella. No se versiona (está en `.gitignore`).

## Requisitos

- Windows con **Microsoft Edge** (imprime el HTML a PDF en modo sin cabeza).
- Python 3.10 o superior: `pip install markdown pymupdf pillow`
- La base de datos levantada (`docker compose up -d`): el capítulo de consultas ejecuta tres de ellas y muestra sus resultados.
- Conexión a internet: los diagramas de Mermaid se cargan desde un CDN al imprimir.

## Pasos

```powershell
python tools/entregable/build_pdf.py . BI_ProyectoFinal_Madera_Montoya.pdf $env:TEMP\pdf_trabajo <POSTGRES_USER> <POSTGRES_DB>
```

| Archivo | Para qué sirve |
|---|---|
| `build_pdf.py` | Convierte `docs/*.md` a HTML, dibuja los esquemas, inserta las capturas y los resultados, y genera el PDF con portada, índice y numeración. |
| `pdf.css` | Estilo del documento. |
| `capturar_power_bi.ps1` | Recorre las páginas de Power BI Desktop y captura cada una (UI Automation). Debe estar abierto el proyecto, maximizado. |
| `recortar_capturas.py` | Recorta cada captura a la página del informe y la deja en `docs/capturas/`. |

Las capturas de Grafana (`gf_*.jpg`) se toman con el tablero en modo quiosco (`?kiosk`) y se guardan en `docs/capturas/`.
