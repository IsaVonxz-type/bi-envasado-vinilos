# Proyecto final de Inteligencia de Negocios

## Objetivo General

Diseñar, implementar y desplegar de forma contenerizada una solución de Inteligencia de Negocios de extremo a extremo () que integre los registros históricos de producción y paros de las líneas de envasado en un modelo dimensional sobre un motor relacional (PostgreSQL o MySQL), mediante un proceso ETL reproducible con validación de calidad de datos. La solución debe habilitar dos capas de consumo complementarias: un tablero operativo en Grafana para el monitoreo casi en tiempo real () con alertas, y un tablero analítico en Power BI para la toma de decisiones estratégicas. El propósito es calcular, auditar y comunicar indicadores de eficiencia operativa, con énfasis en el OEE () y en sus componentes de disponibilidad, rendimiento y calidad.

## 1. Contexto

Una empresa fabricante de vinilos y témperas opera cuatro líneas de envasado (Vinilos_1 a Vinilos_4). Cada turno, las operarias registran a mano en el formato  la producción, los códigos de paro y su duración. El área de mantenimiento transcribe después esa información a un libro de Excel con macros, del que salen tablas dinámicas y gráficos para el comité mensual de la alta dirección (procedimiento ).

La dirección tiene hoy dos necesidades que el Excel no resuelve:

- Analizar tendencias, comparar máquinas, turnos, referencias y años, e identificar las causas principales de los paros para decidir inversiones y planes de mantenimiento.
- Que supervisores y mantenimiento vean el comportamiento de las líneas casi en tiempo real (near real-time) y reciban alertas cuando un indicador se sale de rango, sin esperar el informe mensual.

El equipo debe diseñar e implementar una  que atienda ambas necesidades.

## 2. Insumos entregados

| Archivo | Uso |
|---|---|
| `SEGUIMIENTO TEMPERAS Y VINILOS Actividad.xlsm` | Fuente de datos histórica (source system): registros de producción y paros, catálogos de códigos y subcódigos, indicadores y tablas dinámicas actuales. |
| `P-MTO-22 Registro de paros de producción.pdf` | Reglas de negocio: proceso, campos, códigos de paro e indicadores que se reportan hoy. |

Los datos de origen son . Detectar y tratar los problemas de calidad de datos (data quality) es parte de la evaluación.

## 3. Objetivo

Construir una solución de BI que integre los datos del Excel en un repositorio analítico con modelo dimensional. A partir de ese modelo, la solución debe ofrecer:

- Un  para la toma de decisiones gerenciales, y
- Un  para el monitoreo y las alertas.

Todo debe estar documentado y versionado en GitHub.

## 4. Requerimientos mínimos

- Identificación de los usuarios de la solución (stakeholders) y de las preguntas de negocio que cada uno necesita responder.
- Diagnóstico de la fuente: estructura, problemas de calidad de datos y limitaciones del esquema actual de reporte.
- Catálogo de indicadores. Para cada uno: nombre, fórmula, unidad, granularidad, meta o umbral, fuente y usuario que lo consume.
- Deben incluir, como mínimo, los indicadores que reporta hoy el P-MTO-22:  por máquina, mes y año,  y .
- Deben proponer  que el Excel actual no calcula, con su justificación.
- Diseño de un modelo en  (star / snowflake schema), con justificación de la elección.
- Declaración explícita del  (grain) de cada tabla de hechos.
- Dimensiones con sus atributos y jerarquías. Debe existir al menos una  construida por ustedes.
- Justificación de cómo se modela la jerarquía código → subcódigo de los paros.
- Matriz de bus (bus matrix) que relacione los procesos de negocio con las dimensiones.
- Bonificación: identificar alguna dimensión que requiera Slowly Changing Dimension (SCD) y decidir qué tipo aplicar.

Para cada tabla de hechos y dimensión: descripción, columnas, tipos, llaves (surrogate key / natural key), reglas de transformación aplicadas y origen de cada campo (data lineage).

- Proceso que extraiga los datos del Excel, los limpie, los transforme y los cargue en el modelo dimensional. La herramienta es libre: Python, SQL, Power Query u otra, pero debe justificarse.
- Documentación de las reglas de limpieza aplicadas y de su efecto, con conteos antes y después.
- Demostrar que los totales cargados (horas, unidades, tiempo de paro) concuerdan con la fuente, o explicar y justificar las diferencias.
- El proceso debe ser  desde cero.
- DDL del modelo dimensional en PostgreSQL o MySQL, administrado desde DBeaver.
- Restricciones e índices justificados según el tipo de consultas analíticas.
- Que respondan preguntas de negocio. Deben incluir agregaciones, funciones de ventana (window functions) y comparativos entre periodos.
- Conexión a la base de datos (no al Excel).
- Modelo semántico con relaciones correctas y  propias. Deben incluir al menos una de inteligencia de tiempo (time intelligence).
- Mínimo  con navegación, segmentaciones (slicers) y profundización (drill-down) sobre la jerarquía de paros.
- Al menos un  de las causas de paro.
- El diseño visual y la narrativa (data storytelling) son de libre propuesta.
- Conexión a la base de datos como fuente (data source).
- Paneles de series de tiempo (time series) y de estado actual por máquina.
- Uso de  de tablero para filtrar, por ejemplo, por máquina o turno.
- Al menos  (alert rule) sobre un KPI operativo, con umbral justificado.
- Como Grafana es para monitoreo continuo, deben  hora a hora (data streaming / simulación) y demostrar que el tablero y la alerta reaccionan. El mecanismo de simulación es libre.
- Diagrama de la arquitectura completa de la solución, desde la fuente hasta el consumo.
- Análisis comparativo : qué pregunta de negocio resuelve cada uno, para qué usuario, con qué frecuencia de actualización y por qué no se intercambian.
- Propuesta de cómo evolucionaría la solución si en el futuro los datos llegaran directamente desde los PLCs o el SCADA de las líneas.

Tratamiento de los datos personales (operarios y personal de mantenimiento) y de la seguridad de acceso a los tableros.

## 5. Repositorio Git / GitHub

- Repositorio  con un `README.md` que explique el proyecto, su arquitectura y cómo reproducir la solución desde cero.
- Deben estar versionados: scripts SQL, código del ETL, el tablero de Grafana exportado y el proyecto de Power BI. Elijan y justifiquen un formato de Power BI que sea compatible con el control de versiones.
- Ni cadenas de conexión con contraseñas.
- Historial de commits , con aportes visibles de .
- Incluir un `.gitignore` adecuado.

## 6. Entregables

Con portada que incluya los , el enlace al repositorio y todos los componentes de la sección 4, con capturas de los tableros.

**Nombre del archivo:** `BI_ProyectoFinal_Apellido1_Apellido2.pdf`

## 7. Sustentación

- Exposición en clase del flujo completo: problema, fuente, ETL, modelo dimensional, base de datos, Power BI y Grafana con datos simulados en vivo.
- Se presenta únicamente con las herramientas usadas: DBeaver, el ETL, Power BI, Grafana, GitHub y el PDF.
- La sustentación debe contar una : qué hallazgos encontraron y qué recomendaciones le harían a la gerencia.
- Ambos integrantes deben dominar todo el proyecto. El docente puede pedir en vivo una nueva medida DAX, un nuevo panel o una modificación de una consulta.

## OPCIONAL: BONIFICACIÓN

- Los componentes de servidor de la solución (base de datos, Grafana y, si aplica, el proceso ETL) deben desplegarse con .
- El despliegue debe ser reproducible con un solo comando, con persistencia de datos mediante volúmenes y credenciales gestionadas por variables de entorno (`.env` excluido del repositorio, con un `.env.example` versionado).
- El tablero y la fuente de datos de Grafana deben cargarse automáticamente al iniciar el contenedor (provisioning), sin configuración manual.
- Power BI y DBeaver se ejecutan en el equipo anfitrión y se conectan a los servicios contenerizados.
- En la sustentación, la solución se levanta .

### NOTA OPCIONAL

Es el requisito que mejor resalta a  a quien entendió Docker de quien solo copió un `docker-compose.yml`. Si  configuras Grafana a mano en la sustentación, ahí se notara el trabajo.
