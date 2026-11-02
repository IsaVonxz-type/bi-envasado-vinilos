# Reporte de la última ejecución del ETL

Archivo fuente (SHA-256): `c7d7eabbd55844757c2be07bd61efcee9eb5e0b03aaf9fd76b798737a92d5c55`

## Conteo de filas

| Etapa | Filas |
|---|---|
| Filas leídas de Base De Datos | 8,208 |
| Tras eliminar filas sin medidas (R01) | 7,977 |
| Tras eliminar duplicados con producción (R02) | 7,955 |
| fact_produccion | 5,138 |
| fact_paro (una fila por código con minutos) | 16,490 |
| fact_no_operacion (máquina, día y motivo) | 2,127 |

## Cuadre de cifras

| Métrica | Unidad | Fuente | Excluido | Esperado | Cargado | Diferencia | Cuadra | Explicación |
|---|---|---|---|---|---|---|---|---|
| pacas | pacas | 378,778.00 | 1,019.00 | 377,759.00 | 377,759.00 | 0.00 | Sí | Se excluye lo de R02. Además, pacas válidas descuenta 52,493 pacas imposibles (R08) |
| horas_trabajadas | horas | 38,063.35 | 129.00 | 37,934.35 | 37,934.35 | 0.00 | Sí | Se excluye lo de filas duplicadas con producción (R02) |
| minutos_paro | minutos | 506,979.10 | 859.00 | 506,120.10 | 506,120.10 | 0.00 | Sí | Se excluye lo de filas duplicadas con producción (R02) |
| horas_no_trabajadas | horas | 41,519.85 | 120.00 | 41,399.85 | 41,399.85 | 0.00 | Sí | Se excluye lo de R02. El análisis debe usar horas_ajustadas: 934.00 h menos por R23 |

## Reglas de calidad de datos

| Regla | Problema | Tratamiento | Afectados | Unidad |
|---|---|---|---|---|
| R01 | Filas sin pacas, horas trabajadas, horas no trabajadas ni minutos de paro | Se eliminan: no aportan ninguna medida | 231 | filas |
| R02 | Filas idénticas en todas las columnas y con producción | Se conserva la primera: una transcripción repetida contaría dos veces las pacas | 22 | filas |
| R03 | Filas idénticas sin producción, solo con paro u horas no trabajadas | Se conservan: dos paros iguales en un turno pueden ser eventos distintos | 11 | filas |
| R04 | Filas sin turno, concentradas en 2022 y 2023 | Se asigna el miembro 'Desconocido': no hay datos para recuperarlo | 3,890 | filas |
| R05 | Columna 'Unidad por display' con valores de turno, siempre iguales a la columna Turno | Se ignora: es redundante y no aporta datos nuevos | 551 | filas |
| R06 | Referencias con errores de escritura o formato inconsistente | Se normalizan al formato 'Familia NNcc (K col)' | 491 | filas |
| R07 | Filas sin referencia | Se asigna 'Desconocida'; el rendimiento no se calcula | 3,858 | filas |
| R08 | Pacas imposibles: más de 100 pacas por hora | Se conserva el valor reportado y se excluye de pacas válidas, unidades y rendimiento | 11 | filas |
| R09 | Filas con más minutos de paro que horas trabajadas | Se conservan con alerta; el tiempo operativo se limita a cero | 45 | filas |
| R10 | Producción con 0 horas trabajadas | Se conserva; se evita la división por cero al agregar tiempos antes de dividir | 396 | filas |
| R11 | Nombres de personas en Operario y Personal involucrado | Se reemplazan por un seudónimo HMAC-SHA256 con sal secreta; ningún nombre llega a la base | 43 | personas |
| R12 | Variantes de escritura de una misma persona (nombre completo o error tipográfico) | Se unifican por reglas; un nombre de pila suelto no se une, porque podría ser otra persona | 4 | variantes |
| R13 | Valores 'No' y 'No aplica' en Operario | Se asignan al miembro 'NO-APLICA' | 401 | filas |
| R14 | Columna Observaciones con texto libre que puede contener nombres | No se carga: minimización de datos personales | 275 | filas |
| R15 | Catálogo de velocidades: filas sin estándar o repetidas para la misma máquina y referencia | Se excluyen; se conserva la primera aparición | 5 | filas |
| R25 | Producción sin estándar de velocidad o de unidades por paca (referencia ausente o fuera de catálogo) | Disponibilidad sí se calcula; rendimiento y OEE no. La vista informa la cobertura | 2,686 | filas |
| R26 | Referencia en catálogo de otra máquina, no en la máquina que la produjo | Se usa sus unidades por paca y la velocidad habitual de la máquina; origen = 'inferido' | 4 | filas |
| R16 | Paros de código 01 sin subcódigo | Se asignan a 'Sin especificar' dentro del código 01 | 5 | filas |
| R17 | Paros de código 03 sin subcódigo | Se asignan a 'Sin especificar' dentro del código 03 | 92 | filas |
| R18 | Paros de código 05 sin subcódigo | Se asignan a 'Sin especificar' dentro del código 05 | 10 | filas |
| R19 | Subcódigo 5 diligenciado sin minutos de paro | Se ignora: no hay duración que asignar | 14 | filas |
| R20 | Subcódigos con formato o numeración anterior (1.2C frente a 1.2.C; 4.x frente a 5.x) | Se unifican al catálogo vigente | 1,115 | filas |
| R21 | Dos catálogos de 'Tipo de paro' conviviendo en la fuente | Se unifican por equivalencia documentada | 7 | valores |
| R22 | Horas no trabajadas sin tipo de paro clasificable | Se asignan a 'Sin clasificar' | 15 | filas |
| R23 | Máquina-día con más horas no trabajadas de las posibles (24 h menos las trabajadas) | Se conserva lo reportado y se ajusta proporcionalmente al tope en horas_ajustadas | 79 | máquina-día |
| R24 | Observaciones de paro con mayúsculas y errores de escritura | Se normalizan; lista cerrada sin nombres de personas | 1,578 | filas |
