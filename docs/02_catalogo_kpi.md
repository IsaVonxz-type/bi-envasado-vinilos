# Catálogo de indicadores

Todos los indicadores se calculan **sumando primero los tiempos y las unidades y dividiendo después**. Promediar porcentajes daría el mismo peso a un turno de 2 h que a uno de 12 h.

## Definiciones de tiempo

| Término | Definición | Fuente en el modelo |
|---|---|---|
| Tiempo trabajado | `horas_trabajadas × 60` | `fact_produccion` |
| Paro programado | Códigos 15, 16 y 17, según el área "Paro programado" del catálogo de la fuente | `fact_paro` + `dim_causa_paro` |
| Tiempo planificado | Tiempo trabajado − paro programado | `vw_oee_base` |
| Paro no programado | Los demás códigos | `fact_paro` + `dim_causa_paro` |
| Tiempo operativo | Tiempo planificado − paro no programado, con mínimo de cero | `vw_oee_base` |

## Indicadores exigidos

| Indicador | Fórmula | Unidad | Granularidad | Meta o umbral | Fuente | Usuario |
|---|---|---|---|---|---|---|
| Disponibilidad | Tiempo operativo / tiempo planificado | % | Máquina, turno, día, mes, año | ≥ 90 % (referencia de clase mundial) | `vw_oee_base` | Mantenimiento, producción, supervisión |
| Rendimiento | Unidades producidas / (tiempo operativo × unidades por minuto estándar) | % | Máquina, referencia, mes, año | ≥ 95 % (referencia); revisar si es > 120 % | `vw_oee_base` | Producción |
| Calidad | 100 % como supuesto: la fuente no registra rechazos | % | Constante | ≥ 99 % cuando exista el dato | `vw_oee_mensual.calidad_supuesta` | Calidad, dirección |
| OEE | Disponibilidad × rendimiento × calidad | % | Máquina, mes, año | 85 % a largo plazo; 75 % como primera meta | `vw_oee_mensual` | Dirección, producción |
| MTBF | Tiempo operativo / número de fallas | Horas | Máquina, mes, año | Mayor que el año anterior | `vw_confiabilidad_mensual` | Mantenimiento |
| MTTR | Minutos de los códigos 01, 02 y 03 / número de fallas | Horas | Máquina, mes, año | Menor que el año anterior | `vw_confiabilidad_mensual` | Mantenimiento |
| `% Productividad` (Excel actual) | (Horas trabajadas − paro) / horas trabajadas | % | Máquina, mes, año | Se conserva para comparar con el informe actual | `fact_produccion`, `fact_paro` | Dirección |

Las metas de 85 %, 90 %, 95 % y 99 % son referencias habituales de OEE, no metas definidas por la empresa. Deben validarse con la dirección.

### Supuestos y límites

- **Calidad:** como es 100 % supuesto, el OEE publicado es un **máximo**: el real será igual o menor.
- **OEE y rendimiento:** solo son fiables desde 2024. Cobertura del rendimiento por máquina: 0 % en 2022, 17 % a 20 % en 2023, 91 % a 100 % en 2024 y 51 % a 100 % en 2025. La columna `cobertura_rendimiento` debe mostrarse junto al indicador.
- **Falla:** cada línea con código 01 o 03 cuenta como una falla, porque la fuente no registra eventos. Varias fallas en una misma línea cuentan como una, de modo que el MTBF y el MTTR quedan sobrestimados.
- **MTTR:** incluye la espera de mantenimiento (código 02), porque para producción ese tiempo también es parte de la reparación.
- **Mantenimiento preventivo (código 04):** figura como no programado para respetar el catálogo de la fuente. Con 8,5 h en total, el efecto es insignificante.
- **Rendimiento mayor que 100 %:** 51 de 4.005 grupos superan el 120 %, lo que sugiere pacas mal transcritas o estándares desactualizados. No se recortan para no ocultar el problema.

## Indicadores adicionales propuestos

| Indicador | Fórmula | Unidad | Granularidad | Meta o umbral | Fuente | Usuario |
|---|---|---|---|---|---|---|
| Utilización de capacidad | Horas trabajadas / (horas trabajadas + horas no trabajadas ajustadas) | % | Máquina, mes, año | Definir con planeación | `vw_utilizacion_mensual` | Dirección, planeación |
| Unidades perdidas por paros no programados | Minutos no programados × unidades por minuto estándar | Unidades | Máquina, referencia, mes | Reducción interanual | `vw_oee_mensual` | Dirección, producción |
| Completitud del registro | Líneas con referencia, turno y estándar / total de líneas | % | Máquina, mes | ≥ 95 % | `vw_completitud_mensual` | Mantenimiento, responsables de datos |

**Por qué estos tres:**

- **Utilización:** el OEE solo mide las horas en que la línea estuvo programada, así que puede verse bien con la planta casi parada. En los 25 meses con registro completo de no operación, la utilización es del 38,8 %, y "Paro de máquina por ventas" concentra el 71 % de las horas no trabajadas (28.842 de 40.466 h en todo el archivo). La decisión de invertir en capacidad depende de este dato.
  - **Corrección:** `vw_utilizacion_mensual` incluye los 13 meses en que casi no se registró la no operación (desde julio de 2024 y agosto de 2023, entre otros), y con ellos la utilización total sale en 48,4 %, una cifra inflada. La consulta [`08_utilizacion_por_maquina.sql`](../sql/queries/08_utilizacion_por_maquina.sql) y la medida de Power BI usan solo los meses con al menos 30 filas de no operación.
- **Unidades perdidas:** traduce los minutos a producción, un lenguaje más útil para priorizar inversiones que un porcentaje. Solo se calcula cuando existe un estándar.
- **Completitud:** el 47 % de las horas no tiene referencia. Medirlo permite gobernar la calidad del dato de forma continua, y fue lo que limitó el OEE histórico.
