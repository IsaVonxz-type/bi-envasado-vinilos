# Diccionario de datos y linaje

Generado desde los metadatos reales de la base (tipos, nulos, llaves) y el linaje del ETL (`etl/bi_etl/extract.py` y `transform.py`). Las columnas de la hoja «Base De Datos» se identifican por su letra en Excel.

Convenciones: **PK** llave primaria (clave sustituta), **FK** llave foránea, **UK** llave única o natural. «Generada» significa que el ETL la crea y no existe en el Excel.

## `dw.dim_fecha`

Calendario con un día por fila, desde el primer hasta el último día del año del archivo.

**Grano:** Un día.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `fecha_key` | integer | no | PK | Generada por el ETL | Clave sustituta con la forma AAAAMMDD. |
| `fecha` | date | no | UK | Generada por el ETL | Un día por fila entre el 01/01/2022 y el 31/12/2025. Llave natural. |
| `anio` | smallint | no |  | Generada por el ETL | Año de `fecha`. |
| `semestre` | smallint | no |  | Generada por el ETL | 1 de enero a junio, 2 el resto. |
| `trimestre` | smallint | no |  | Generada por el ETL | Trimestre calendario. |
| `mes` | smallint | no |  | Generada por el ETL | Mes 1 a 12. |
| `nombre_mes` | varchar(12) | no |  | Generada por el ETL | Nombre del mes en español. |
| `anio_mes` | char(7) | no |  | Generada por el ETL | Texto AAAA-MM, ordenable. |
| `semana_iso` | smallint | no |  | Generada por el ETL | Semana ISO 8601. |
| `dia_semana` | smallint | no |  | Generada por el ETL | 1 lunes a 7 domingo. |
| `nombre_dia` | varchar(10) | no |  | Generada por el ETL | Nombre del día en español. |
| `es_fin_semana` | boolean | no |  | Generada por el ETL | Verdadero si es sábado o domingo. |

## `dw.dim_maquina`

Las cuatro líneas de envasado.

**Grano:** Una máquina.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `maquina_key` | smallint | no | PK | Generada por el ETL | Igual al número de línea. |
| `maquina_nk` | varchar(20) | no | UK | Hoja «Base De Datos», columna D (Maquina) | Llave natural: `Vinilos_1` a `Vinilos_4`. |
| `numero_linea` | smallint | no | UK | Generada por el ETL | Número extraído del nombre. |

## `dw.dim_turno`

Turnos y esquemas de turno. **Dimensión construida por el equipo.**

**Grano:** Un turno.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `turno_key` | smallint | no | PK | Generada por el ETL | Clave sustituta. |
| `turno_nk` | varchar(30) | no | UK | Hoja «Base De Datos», columna L (Turno) | R04: los vacíos pasan a `Desconocido`. Los turnos sin etiqueta de número se unifican con su versión numerada. |
| `esquema` | varchar(20) | no |  | Conocimiento del negocio (`catalogs.py`) | Agrupa los turnos por esquema: 3 de 8 h, 2 de 12 h o jornada de 10,5 h. |
| `hora_inicio` | time without time zone | sí |  | Conocimiento del negocio | Hora de inicio; nula en `No aplica` y `Desconocido`. |
| `hora_fin` | time without time zone | sí |  | Conocimiento del negocio | Hora de fin; el turno 3 y el de 6 pm cruzan la medianoche. |
| `horas_nominales` | numeric(4,1) | sí |  | Conocimiento del negocio | Duración nominal del turno. |

## `dw.dim_referencia`

Referencias de producto (familia, volumen y colores).

**Grano:** Una referencia.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `referencia_key` | integer | no | PK | Generada por el ETL | Clave sustituta. |
| `referencia_nk` | varchar(60) | no | UK | Hoja «Base De Datos», columna F (Referencia) | R06: se normaliza a `Familia NNcc (K col)`. R07: los vacíos pasan a `Desconocida`. |
| `familia` | varchar(40) | no |  | Derivado del nombre | Primera parte del nombre de la referencia. |
| `volumen_cc` | smallint | sí |  | Derivado del nombre | Número antes de `cc`. |
| `colores` | smallint | sí |  | Derivado del nombre | Número antes de `col`. |

## `dw.dim_persona`

Operarias y personal de mantenimiento, **solo con seudónimo**.

**Grano:** Una persona.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `persona_key` | integer | no | PK | Generada por el ETL | Clave sustituta. |
| `seudonimo` | varchar(20) | no | UK | Hoja «Base De Datos», columnas E (Operario) y AD (Personal involucrado) | R11: HMAC-SHA256 con sal secreta, con la forma `PER-` y 10 caracteres hexadecimales; ningún nombre llega a la base. R12 unifica variantes de escritura. R13: `No` y `No aplica` pasan al miembro `NO-APLICA`; los vacíos, a `SIN-REGISTRO`. |
| `rol` | varchar(20) | no |  | Columna de origen | `Operación` si la persona aparece como operario; `Mantenimiento` si solo aparece como personal involucrado; `Sin registro` y `No aplica` para los miembros especiales. |

## `dw.dim_causa_paro`

Causas de paro con la jerarquía clasificación → área → código → sistema → subcódigo, aplanada. **Dimensión construida por el equipo.**

**Grano:** Una hoja de la jerarquía (código, sistema y subcódigo).

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `causa_key` | integer | no | PK | Generada por el ETL | Clave sustituta. |
| `causa_nk` | varchar(20) | no | UK | Generada por el ETL | Llave natural: el subcódigo (`1.2.C`); `N.SE` si no se especificó y `N.NA` si el código no tiene detalle. |
| `codigo` | smallint | no |  | Hoja «Base De Datos», 18 columnas «Codigo de paro N» | Número 1 a 18. |
| `codigo_nombre` | varchar(90) | no |  | P-MTO-22 y Hoja «Tablas Desplegables» | Nombre del código. El 18 es «Desinfección» y no «Paro de máquina». |
| `area_impacto` | varchar(40) | no |  | Hoja «Tablas Desplegables» | Área responsable; los códigos 15, 16 y 17 son `Paro programado`. |
| `clasificacion_oee` | varchar(15) | no |  | Hoja «Tablas Desplegables» | `Programado` para los códigos 15, 16 y 17; `No programado` para el resto. |
| `es_falla` | boolean | no |  | Conocimiento del negocio | Verdadero para los códigos 01 y 03; base del MTBF y MTTR. |
| `sistema` | varchar(70) | no |  | Hoja «Base De Datos», columnas Q, V y AA (subcódigos 1, 3 y 5) | Sistema del subcódigo; `Sin especificar` (R16, R17, R18) o `No aplica` según el caso. |
| `subcodigo` | varchar(70) | no |  | Hoja «Base De Datos», columnas Q, V y AA | R20: se unifican formatos y numeración anterior (`1.2C`→`1.2.C`; `4.x`→`5.x`). |

## `dw.dim_motivo_no_operacion`

Motivos por los que una línea no operó. **Dimensión construida por el equipo**: unifica dos catálogos.

**Grano:** Un motivo.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `motivo_key` | integer | no | PK | Generada por el ETL | Clave sustituta. |
| `tipo` | varchar(50) | no | UK | Hoja «Base De Datos», columna N (Tipo de paro) | R21: dos catálogos (`17. PARO DE MAQUINA` y `[18] Paro de maquina por ventas`) se unifican. R22: sin clasificación pasa a `Sin clasificar`. |
| `categoria` | varchar(20) | no |  | Conocimiento del negocio | Comercial, Planeación, Producción, Calidad, Materiales, Mantenimiento o Sin clasificar. |
| `motivo` | varchar(70) | no | UK | Hoja «Base De Datos», columna O (Observación del paro) | R24: se normalizan mayúsculas y errores de escritura; lista cerrada sin nombres. |

## `dw.dim_estandar_produccion`

Estándar de velocidad y unidades por paca por máquina y referencia. **SCD tipo 2.**

**Grano:** Una versión de un estándar.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `estandar_key` | integer | no | PK | Generada por el ETL | Clave sustituta de la versión. |
| `maquina_key` | smallint | no | FK → dim_maquina, UK | Hoja «Tablas Desplegables», columna C | Máquina del estándar. |
| `referencia_key` | integer | no | FK → dim_referencia, UK | Hoja «Tablas Desplegables», columna D | Referencia del estándar. |
| `unidades_por_paca` | integer | no |  | Hoja «Tablas Desplegables», columna H | R15: se excluyen filas repetidas o sin estándar. |
| `unidades_por_minuto` | numeric(6,1) | no |  | Hoja «Tablas Desplegables», columna I | R26: si la referencia solo está en otra máquina se usa la velocidad habitual de la máquina. |
| `origen` | varchar(15) | no |  | Generada por el ETL | `catalogo` si el estándar es exacto; `inferido` (R26) si no. |
| `valido_desde` | date | no | UK | Generada por el ETL | 01/01/2022: la fuente no dice desde cuándo rige cada velocidad. |
| `valido_hasta` | date | no |  | Generada por el ETL | 31/12/9999 para la versión vigente. |
| `es_vigente` | boolean | no |  | Generada por el ETL | Verdadero para la versión abierta. |

## `dw.fact_produccion`

Producción de cada línea transcrita del formato «hora a hora».

**Grano:** Una fila de origen con pacas u horas trabajadas.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `produccion_key` | bigint | no | PK | Generada por el ETL | Clave sustituta. |
| `fila_origen` | integer | no | UK | Hoja «Base De Datos», número de fila | Dimensión degenerada: trazabilidad hasta la fila del Excel. R02 elimina duplicados exactos con producción. |
| `fecha_key` | integer | no | FK → dim_fecha | Hoja «Base De Datos», columna A | Fecha a clave AAAAMMDD. |
| `maquina_key` | smallint | no | FK → dim_maquina | Hoja «Base De Datos», columna D | Nombre a clave. |
| `turno_key` | smallint | no | FK → dim_turno | Hoja «Base De Datos», columna L | R04. |
| `referencia_key` | integer | no | FK → dim_referencia | Hoja «Base De Datos», columna F | R06, R07. |
| `operario_key` | integer | no | FK → dim_persona | Hoja «Base De Datos», columna E | R11, R12, R13. |
| `estandar_key` | integer | sí | FK → dim_estandar_produccion | Generada por el ETL | Versión del estándar vigente para la máquina y referencia; nula si no hay estándar (R25). |
| `pacas_reportadas` | numeric(10,2) | sí |  | Hoja «Base De Datos», columna J (Pacas producidas) | Valor tal como se transcribió. |
| `pacas_validas` | numeric(10,2) | sí |  | Derivado | R08: nulo cuando hay más de 100 pacas por hora (11 filas). |
| `unidades_producidas` | numeric(14,2) | sí |  | Derivado | Pacas válidas × unidades por paca; nulo sin estándar. |
| `horas_trabajadas` | numeric(6,2) | sí |  | Hoja «Base De Datos», columna K | R10: se conservan las filas con 0 horas. |
| `alerta_pacas_atipicas` | boolean | no |  | Derivado | R08. |
| `alerta_paro_excede` | boolean | no |  | Derivado | R09: más minutos de paro que horas trabajadas. |

## `dw.fact_paro`

Minutos de paro por código dentro de cada fila de origen.

**Grano:** Un código de paro con minutos en una fila de origen.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `paro_key` | bigint | no | PK | Generada por el ETL | Clave sustituta. |
| `fila_origen` | integer | no | UK | Hoja «Base De Datos», número de fila | Con `causa_key` es único. |
| `fecha_key` | integer | no | FK → dim_fecha | Hoja «Base De Datos», columna A |  |
| `maquina_key` | smallint | no | FK → dim_maquina | Hoja «Base De Datos», columna D |  |
| `turno_key` | smallint | no | FK → dim_turno | Hoja «Base De Datos», columna L | R04. |
| `referencia_key` | integer | no | FK → dim_referencia | Hoja «Base De Datos», columna F | R06, R07. |
| `operario_key` | integer | no | FK → dim_persona | Hoja «Base De Datos», columna E | R11 a R13. |
| `causa_key` | integer | no | FK → dim_causa_paro, UK | Hoja «Base De Datos», 18 columnas «Codigo de paro N» y subcódigos Q, V, AA | Una fila por cada código con minutos mayores que cero (las 18 columnas se vuelven filas). |
| `persona_involucrada_key` | integer | no | FK → dim_persona | Hoja «Base De Datos», columna AD | Solo para el código 05; en los demás, `NO-APLICA`. |
| `area_involucrada` | varchar(30) | sí |  | Hoja «Base De Datos», columna AC | Solo para el código 05. |
| `minutos_paro` | numeric(8,2) | no |  | Hoja «Base De Datos», columnas «Codigo de paro N» | Mayor que cero; R03 conserva paros idénticos sin producción. |

## `dw.fact_no_operacion`

Horas en que una línea no operó, por día y motivo.

**Grano:** Una máquina, un día y un motivo.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `no_operacion_key` | bigint | no | PK | Generada por el ETL | Clave sustituta. |
| `fecha_key` | integer | no | FK → dim_fecha, UK | Hoja «Base De Datos», columna A |  |
| `maquina_key` | smallint | no | FK → dim_maquina, UK | Hoja «Base De Datos», columna D |  |
| `motivo_key` | integer | no | FK → dim_motivo_no_operacion, UK | Hoja «Base De Datos», columnas N y O | R21, R22, R24. |
| `filas_origen` | smallint | no |  | Generada por el ETL | Cuántas filas del Excel se agruparon. |
| `horas_reportadas` | numeric(8,2) | no |  | Hoja «Base De Datos», columna M (Horas no trabajadas) | Suma de las filas del grupo. |
| `horas_ajustadas` | numeric(8,2) | no |  | Derivado | R23: se reduce proporcionalmente si el día supera 24 h menos las trabajadas. |

## `ops.escenario`

Panel de control de la simulación.

**Grano:** Una máquina.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `maquina` | varchar(20) | no | PK | Simulador | Nombre de la máquina. |
| `modo` | varchar(10) | no |  | Usuario | `normal`, `degradado` o `falla`. Se cambia con UPDATE. |
| `actualizado_en` | timestamptz | no |  | Usuario o sistema | Última modificación. |

## `ops.lectura_hora`

Lectura de una hora de producción de una máquina; alimenta Grafana.

**Grano:** Una máquina durante una hora.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `lectura_id` | bigint | no | PK | Simulador | Clave sustituta. |
| `ts` | timestamptz | no |  | Simulador | Instante real en que llega el registro; es el eje de tiempo de Grafana. |
| `hora_simulada` | timestamp | no | UK | Simulador | Hora de producción que representa. |
| `maquina` | varchar(20) | no | UK | Simulador | Nombre de la máquina. |
| `turno` | varchar(30) | no |  | Simulador | Según la hora simulada. |
| `referencia` | varchar(60) | no |  | Simulador | Muestreada con el peso histórico de la máquina. |
| `escenario` | varchar(10) | no |  | `ops.escenario` | Modo vigente al generar la lectura. |
| `minutos_programados` | numeric(6,2) | no |  | Simulador | Paros programados de la hora. |
| `minutos_planificados` | numeric(6,2) | no |  | Simulador | 60 menos los programados. |
| `minutos_no_programados` | numeric(6,2) | no |  | Simulador | Paros no programados, sin exceder lo planificado. |
| `minutos_operativos` | numeric(6,2) | no |  | Simulador | Planificados menos no programados. |
| `unidades_teoricas` | numeric(12,2) | no |  | Simulador | Minutos operativos × velocidad estándar. |
| `unidades_producidas` | numeric(12,2) | no |  | Simulador | Teóricas × rendimiento sorteado. |

## `ops.paro_hora`

Cada paro de una lectura, con su causa.

**Grano:** Un paro dentro de una lectura.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `paro_id` | bigint | no | PK | Simulador | Clave sustituta. |
| `lectura_id` | bigint | no | FK → lectura_hora | Simulador | Lectura a la que pertenece. |
| `ts` | timestamptz | no |  | Simulador | Igual al de la lectura. |
| `maquina` | varchar(20) | no |  | Simulador | Nombre de la máquina. |
| `codigo` | smallint | no |  | `dw.dim_causa_paro` | Código 1 a 18. |
| `causa` | varchar(90) | no |  | `dw.dim_causa_paro` | Nombre del código. |
| `sistema` | varchar(70) | no |  | `dw.dim_causa_paro` |  |
| `subcodigo` | varchar(70) | no |  | `dw.dim_causa_paro` |  |
| `clasificacion` | varchar(15) | no |  | `dw.dim_causa_paro` | Programado o no programado. |
| `es_falla` | boolean | no |  | `dw.dim_causa_paro` | Códigos 01 y 03. |
| `minutos` | numeric(6,2) | no |  | Simulador | Duración del evento dentro de la hora. |

## `ops.alerta_recibida`

Alertas que Grafana entrega por webhook.

**Grano:** Una notificación de una alerta.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `alerta_id` | bigint | no | PK | Receptor | Clave sustituta. |
| `recibido_en` | timestamptz | no |  | Receptor | Instante de recepción. |
| `estado` | varchar(10) | no |  | Grafana | `firing` o `resolved`. |
| `regla` | varchar(120) | no |  | Grafana | Nombre de la regla. |
| `maquina` | varchar(20) | sí |  | Grafana | Etiqueta de la alerta. |
| `valor` | numeric(12,2) | sí |  | Grafana | Medida observada en el momento de la alerta. |
| `severidad` | varchar(20) | sí |  | Grafana | Etiqueta de la regla. |
| `resumen` | text | sí |  | Grafana | Anotación `summary`. |

## `audit.etl_ejecucion`

Una fila por ejecución del ETL.

**Grano:** Una ejecución.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `ejecucion_id` | integer | no | PK | Generada por el ETL | Clave sustituta. |
| `inicio` | timestamptz | no |  | Generada por el ETL | Inicio. |
| `fin` | timestamptz | no |  | Generada por el ETL | Fin. |
| `archivo_sha256` | char(64) | no |  | Generada por el ETL | Huella del archivo fuente: identifica exactamente qué se cargó. |
| `filas_fuente` | integer | no |  | Generada por el ETL | Filas leídas. |

## `audit.calidad_datos`

Efecto de cada regla de limpieza.

**Grano:** Una regla.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `regla` | varchar(10) | no | PK | Generada por el ETL | R01 a R26. |
| `descripcion` | text | no |  | Generada por el ETL | Problema. |
| `tratamiento` | text | no |  | Generada por el ETL | Qué se hizo. |
| `afectados` | integer | no |  | Generada por el ETL | Cuántas filas, personas o valores. |
| `unidad` | varchar(20) | no |  | Generada por el ETL | Unidad de lo contado. |

## `audit.conteo_filas`

Filas tras cada etapa del ETL.

**Grano:** Una etapa.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `orden` | smallint | no | PK | Generada por el ETL | Orden de la etapa. |
| `etapa` | text | no |  | Generada por el ETL | Descripción. |
| `filas` | integer | no |  | Generada por el ETL | Filas que quedan. |

## `audit.cuadre_cifras`

Comparación entre la fuente y lo cargado.

**Grano:** Una métrica.

| Columna | Tipo | Nulo | Llaves | Origen | Regla de transformación |
|---|---|---|---|---|---|
| `metrica` | varchar(30) | no | PK | Generada por el ETL | Pacas, horas, minutos. |
| `unidad` | varchar(10) | no |  | Generada por el ETL |  |
| `fuente` | numeric(14,2) | no |  | Generada por el ETL | Total del Excel. |
| `excluido` | numeric(14,2) | no |  | Generada por el ETL | Lo eliminado por R02. |
| `esperado` | numeric(14,2) | no |  | Generada por el ETL | Fuente menos excluido. |
| `cargado` | numeric(14,2) | no |  | Generada por el ETL | Total en la base. |
| `diferencia` | numeric(14,2) | no |  | Generada por el ETL | Cargado menos esperado. |
| `cuadra` | boolean | no |  | Generada por el ETL | Verdadero si la diferencia no supera 0,01. |
| `explicacion` | text | no |  | Generada por el ETL | Justificación de las diferencias. |
