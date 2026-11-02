# BI de líneas de envasado de vinilos y témperas

Solución de inteligencia de negocios que lleva los registros históricos de producción y paros de un Excel con macros a un modelo dimensional en PostgreSQL, para calcular OEE, MTBF y MTTR y consumirlos en Power BI y Grafana.

Integrantes: Isaac Madera Jiménez y Daniela Montoya Quintero.

## Reproducir desde cero

Requisitos: Docker con Docker Compose y el archivo fuente, que no se versiona porque contiene datos personales.

```powershell
Copy-Item .env.example .env
# Editar .env, reemplazar cada "cambiar_esto" y colocar el Excel en data/source/
docker compose up -d
docker compose logs -f etl
```

El servicio `etl` se ejecuta una vez y termina: crea los esquemas, limpia los datos, los seudonimiza, cuadra las cifras y carga. Grafana queda en `http://localhost:3000` y PostgreSQL en `localhost:5432`.

## Estructura

| Carpeta | Contenido |
|---|---|
| `etl/` | Proceso ETL en Python y sus pruebas |
| `sql/ddl/` | Tablas, restricciones, índices y vistas de indicadores |
| `sql/queries/` | Consultas de negocio |
| `simulator/` | Simulación de llegada de datos hora a hora |
| `grafana/` | Provisioning y tablero de Grafana |
| `powerbi/` | Proyecto de Power BI |
| `docs/` | Análisis, catálogo de KPI, modelo dimensional y ETL |
| `data/source/` | Archivo fuente local, ignorado por Git |

## Documentación

1. [Análisis de negocio y diagnóstico](docs/01_analisis_negocio.md)
2. [Catálogo de indicadores](docs/02_catalogo_kpi.md)
3. [Modelo dimensional](docs/03_modelo_dimensional.md)
4. [Proceso ETL](docs/04_etl.md)
5. [Entrega al Bloque 2](docs/05_entrega_bloque_2.md)
6. [Reporte de la última ejecución](docs/generated/reporte_etl.md)
