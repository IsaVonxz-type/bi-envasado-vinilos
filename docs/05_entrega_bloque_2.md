# Entrega del Bloque 1 al Bloque 2

> **Estado:** el Bloque 2 ya está construido. Sus documentos son [monitoreo y alertas](06_monitoreo_grafana.md), [Power BI](07_power_bi.md), [arquitectura y evolución](08_arquitectura_y_evolucion.md), [seguridad y datos personales](09_seguridad_y_datos_personales.md) y el [diccionario de datos](10_diccionario_de_datos.md). Este documento se conserva como la entrega original; una corrección importante: la utilización de capacidad.

## Cómo arrancar

1. Clonar el repositorio y copiar `.env.example` a `.env`, con valores propios.
2. Colocar el Excel en `data/source/`. No se versiona.
3. Ejecutar `docker compose up -d`. Grafana queda en `http://localhost:3000` y PostgreSQL en `localhost:5432`, con las credenciales del `.env`.
4. Conectar DBeaver a `localhost:5432` para revisar los esquemas `dw` y `audit`.

Cada `docker compose up -d` vuelve a ejecutar el ETL, que elimina y recarga `dw` y `audit`. **Lo que se cree en esos esquemas se pierde.** Los objetos propios del Bloque 2 van en otro esquema, por ejemplo `ops` para la simulación, o en un archivo de `sql/ddl/` si deben recrearse con el ETL.

## Qué usar según la tarea

| Tarea | Punto de partida |
|---|---|
| Medidas de OEE en Power BI | Importar `vw_oee_base` y sumar sus columnas de tiempo y unidades antes de dividir. No promediar `vw_oee_mensual` |
| Pareto y drill-down | `fact_paro` con `dim_causa_paro`: clasificación → área → código → sistema → subcódigo |
| MTBF y MTTR | `vw_confiabilidad_mensual` |
| Indicadores nuevos | `vw_utilizacion_mensual`, `vw_completitud_mensual` y `unidades_perdidas_no_programado` |
| Filtro por turno | 2022 y 2023 tienen muchas filas con turno "Desconocido", que no conviene ocultar sin aviso |
| Diccionario y linaje | `sql/ddl/`, `etl/bi_etl/extract.py` (posición de cada columna) y `etl/bi_etl/transform.py` |

## Cuidados al presentar cifras

- **Mostrar OEE con su cobertura.** Solo es fiable desde 2024; en 2022 no existe y en 2023 cubre cerca del 20 % del tiempo. `Vinilos_3` en 2025 cubre el 51 %.
- **Calidad es 100 % supuesto.** Hay que decir que el OEE es un máximo.
- **Dos relaciones con persona.** `fact_paro` tiene `operario_key` y `persona_involucrada_key`; en Power BI una de ellas queda inactiva.
- **Datos hasta marzo de 2025.** El PDF muestra abril de 2025, pero este archivo termina el 28/03/2025. Un comparativo de 2025 contra 2024 debe usar los mismos meses.
- **Simulación:** la fuente no tiene horas. Repartir cada turno por horas es un supuesto que debe declararse.

## Primeros hallazgos para la historia

Calculados sobre los datos cargados:

- **La mayor pérdida no está en la máquina.** La utilización es del 38,8 % en los 25 meses con registro completo (el 48,4 % que sale de incluir todo el archivo está inflado, porque desde julio de 2024 casi no se anotó la no operación). 28.842 de 40.466 h sin operar se deben a paros por ventas (71 %).
- **Dentro de los paros no programados, los primeros son operativos:** ajuste operativo (1.817 h), limpieza por derrame (1.546 h) y alistamiento (621 h). La falla electromecánica suma 323 h.
- **Hay dos grupos de máquinas.** En 2024, el OEE es de 81,6 % en `Vinilos_3` y 79,6 % en `Vinilos_4`, frente a 55,9 % en `Vinilos_1` y 60,8 % en `Vinilos_2`.
- **La disponibilidad cae cada año:** 91,7 % en 2022, 85,0 % en 2023, 80,7 % en 2024 y 78,3 % en 2025 (hasta marzo).
