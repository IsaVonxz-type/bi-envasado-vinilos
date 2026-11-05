# Análisis de negocio y diagnóstico de la fuente

## Usuarios y preguntas de negocio

| Usuario | Capa | Preguntas que necesita responder |
|---|---|---|
| Alta dirección | Power BI | ¿Mejora o empeora el OEE frente al año anterior? ¿Cuánta capacidad queda sin usar y por qué? ¿Dónde conviene invertir? |
| Coordinación de mantenimiento | Power BI y Grafana | ¿Qué sistemas fallan más? ¿Cómo evolucionan MTBF y MTTR? ¿Qué subcódigos justifican un plan preventivo? |
| Jefatura de producción | Power BI | ¿Qué máquinas, turnos y referencias rinden menos? ¿Qué causas operativas concentran los paros? |
| Supervisión de turno | Grafana | ¿Cómo va cada línea en esta hora? ¿Qué línea está fuera de rango y necesita atención ahora? |
| Personal de mantenimiento | Grafana | ¿Hay una falla activa o un paro que crece? ¿A qué línea debo acudir primero? |
| Planeación y ventas | Power BI | ¿Cuántas horas se pierden por falta de demanda o de programación? |

## Estructura de la fuente

| Hoja | Visible | Uso en el proyecto |
|---|---|---|
| `Base De Datos` (tabla `T_baseDeDatos`) | Sí | Fuente principal: 8.208 filas y 58 columnas, del 01/01/2022 al 28/03/2025 |
| `Tablas Desplegables` | Sí | Catálogos de códigos y subcódigos; estándares de velocidad y unidades por paca |
| `Base de datos de Sub codigos` | No | Copia parcial (1.251 registros, oct/2023 a may/2024). Sus minutos son iguales o menores que los de la base principal en ese periodo, así que no se carga |
| `Registro` y `Tiempos` | Sí | Formulario de captura y cálculo de eficiencia por registro |
| `Calculadora de tiempos`, `TABLA CODIGOS` | No | Apoyo al formulario; no se cargan |
| `TD_*`, `prod*`, `fallaMecanica`, `ajusteOperativo`, `novPotencia` | Sí | Tablas dinámicas y gráficos que reemplaza el BI |

**Cómo se forman las filas.** El botón "Ingreso total" guarda una línea con pacas y horas. "Ingreso subcódigo" guarda otra línea del mismo turno, solo con el paro y su subcódigo. Por eso un turno puede ocupar varias filas, y por eso una fila sin pacas no es un error. Hay además filas de máquina-día sin operación, que solo traen horas no trabajadas y su motivo.

## Problemas de calidad encontrados

Los conteos exactos de cada ejecución están en [`generated/reporte_etl.md`](generated/reporte_etl.md).

| Problema | Evidencia | Impacto si no se trata |
|---|---|---|
| Pacas imposibles | 11 filas de `Vinilos_1` (22 al 29/07/2023) con 3.552 a 9.417 pacas en un turno; suman 52.493 de 378.778 pacas (13,9 %). El ideal por turno es de 53 a 147 | Infla producción y rendimiento. Es posible que sean unidades y no pacas, pero la fuente no permite confirmarlo |
| Referencia ausente | 2.405 filas con pacas, 17.987 h (47 % de las horas), casi todas de 2022 y 2023 | Sin referencia no hay unidades por paca: el rendimiento no se puede calcular |
| Turno ausente | 3.890 filas tras limpiar, sobre todo 2022 y 2023 | Impide comparar turnos en ese periodo |
| Horas no trabajadas repetidas | 79 máquina-día superan las 24 h menos las trabajadas: una misma cifra se copia en varias filas del día | Suma cruda de 41.520 h, sobrestimada en 934 h |
| Dos catálogos de `Tipo de paro` | `17. PARO DE MAQUINA` y `[18] Paro de maquina por ventas` conviven | Fragmenta la misma causa |
| Conflicto en el código 18 | El formulario y el PDF lo llaman "Desinfección"; `Tablas Desplegables` lo llama "Paro de maquina" (Ventas) | Se adopta Desinfección para la columna de minutos; los paros por ventas están en `Tipo de paro` |
| Subcódigos inconsistentes | `1.2C` y `1.2.C`; `4.2` y `5.2` para el mismo sistema; errores como `RAGORES` | Divide causas iguales en el Pareto |
| Subcódigos faltantes | Código 03: 92 de 151 paros sin subcódigo. Códigos 01 y 05: casi completos | El análisis del código 03 es parcial |
| Referencias mal escritas | `Alocdor`, `Stilo Kids`, `(12col)` | Duplica referencias |
| Columnas vacías | `Unidades producidas cada minuto` y `Display por paca` nunca se diligencian | Se obtienen del catálogo |
| Columna repetida | `Unidad por display` contiene el turno, siempre igual a la columna `Turno` | Se ignora |
| Duplicados exactos | 22 filas con producción y 11 sin producción | Se eliminan las primeras; las segundas se conservan porque pueden ser eventos reales |
| Paro incoherente | 45 filas con más paro que horas trabajadas | Se conservan con alerta; el tiempo operativo se limita a cero |
| Catálogo con errores | Celdas `#VALUE!` en `minutos * turno`, porque dependen del formulario | Se usan solo las columnas base del catálogo |
| Periodos incompletos | Sin junio de 2022; julio a septiembre de 2022 con 25 filas; marzo de 2025 parcial | Los comparativos deben avisarlo |
| Registro de no operación interrumpido | Los meses normales tienen entre 38 y 125 filas de horas no trabajadas; agosto de 2023 tiene 11 y, desde julio de 2024, 9, 4, 6 y ninguna desde octubre, mientras la producción sigue registrándose | La utilización se infla: en 13 de los 38 meses nadie anotó los paros. Debe medirse solo en los 25 meses con registro (consulta 08 y medida de Power BI) |
| Datos personales | Nombres completos y parciales de operarias y mantenimiento; texto libre en `Observaciones`; autores en los metadatos | Exposición de personas en un repositorio público |

## Limitaciones del esquema actual

- **El indicador principal no es OEE.** `% Productividad = (horas trabajadas − paro) / horas trabajadas` se parece a una disponibilidad, y cuenta como pérdida el aseo y la pausa activa, que la propia fuente clasifica como paro programado.
- **Sin dato de calidad.** El formato en papel tiene "No conforme", pero no se transcribe. El componente de calidad del OEE no se puede medir.
- **Sin hora de inicio ni número de eventos.** Solo hay minutos por código en cada línea, lo que limita MTBF, MTTR y el análisis hora a hora.
- **Modelo no normalizado.** Una columna por código impide agregar por causa sin fórmulas repetidas, y una jerarquía de subcódigos solo para los códigos 01, 03 y 05.
- **Reporte mensual y manual.** La información llega semanas después del evento, tras pasar del papel a producción y de ahí a mantenimiento.
- **Sin controles.** Nada impide pacas imposibles, duplicados o escrituras distintas, y no hay trazabilidad de cambios.
