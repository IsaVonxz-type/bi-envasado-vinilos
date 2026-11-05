# Hallazgos y recomendaciones a la gerencia

## El mensaje en tres frases

1. **Las líneas no pierden tiempo por averías, sino por la forma de operar:** tres paros operativos (ajuste, limpieza por derrame y alistamiento) explican el 72 % del paro no programado, y pesan cada año más.
2. **La brecha entre líneas es grande:** Vinilos_3 y Vinilos_4 rinden un OEE de casi 80 % y Vinilos_1 y Vinilos_2, de 56 % a 61 %.
3. **Invertir en más capacidad no se justifica con estos datos:** la planta opera cerca del 39 % del tiempo y el 71 % de las horas sin operar se debe a paros por ventas.

Todas las cifras salen de los datos cargados y se pueden reproducir con las consultas de [`sql/queries/`](../sql/queries/) o en el tablero de Power BI.

## Hallazgos

### 1. Dos grupos de máquinas, y la disponibilidad cae cada año

| OEE de 2024 | Vinilos_1 | Vinilos_2 | Vinilos_3 | Vinilos_4 |
|---|---|---|---|---|
| OEE | 55,9 % | 60,8 % | 81,6 % | 79,6 % |

| Año | 2022 | 2023 | 2024 | 2025 (a marzo) |
|---|---|---|---|---|
| Disponibilidad de la planta | 91,7 % | 85,0 % | 80,7 % | 78,3 % |

Comparando los **mismos meses** (enero a marzo) de 2025 y 2024, el OEE cae 11,2 puntos en Vinilos_2, 8,2 en Vinilos_3 (con la salvedad de que su cobertura de estándar en 2025 es de solo 49 %) y 4,8 en Vinilos_4; solo Vinilos_1 sube 4,8 puntos. *Fuente: consultas 01 y 02, página «Resumen ejecutivo».*

### 2. La mayor pérdida está en la operación, no en el mantenimiento

El paro no programado suma **5.557 h**.

| Causa | Horas | % | % acumulado |
|---|---|---|---|
| Ajuste operativo | 1.817 | 32,7 | 32,7 |
| Limpieza por derrame operativo | 1.546 | 27,8 | 60,5 |
| Alistamiento / cambio de referencia | 621 | 11,2 | 71,7 |
| Paro por ventaja / evacuación | 356 | 6,4 | 78,1 |
| Falla electromecánica | 323 | 5,8 | 83,9 |

Las dos causas de mantenimiento (falla electromecánica, 323 h, y novedad en sistemas de potencia, 87 h) suman 410 h, el **7,4 %**. Además, las tres causas operativas principales crecen como parte del tiempo trabajado: 3,9 % en 2022, 9,8 % en 2023, 13,6 % en 2024 y 16,3 % en el primer trimestre de 2025. *Fuente: consultas 04, 05 y 06, página «Causas de paro».*

### 3. El sistema de dosificación es el punto caliente

- Dentro de los ajustes operativos (código 05), el subcódigo **5.2 Dosificación de pintura** suma 784 h: el 43,2 % del código.
- Dentro de las fallas electromecánicas (código 01), el sistema **1.2 Dosificación** suma 117 h: el 36 %, con el cambio de válvula (1.2.C) como mayor subcódigo individual (46,5 h en 72 registros).
- Juntos son **901 h, el 16 % de todo el paro no programado**, en un solo sistema.

Hay una hipótesis, que los datos no confirman, de que la limpieza por derrame (1.546 h) esté ligada a la dosificación. Vale la pena comprobarla en planta. *Fuente: consulta 06, profundización en Power BI.*

### 4. La planta tiene capacidad de sobra

En los 25 meses con registro completo de no operación, la utilización de capacidad es de **38,8 %**: 25.390 h trabajadas frente a 40.034 h sin operar. El 71 % de las horas no trabajadas del archivo es paro por ventas. Esto quiere decir que el límite es la demanda y la programación, no las máquinas. *Fuente: consultas 08 y 09, página «Capacidad».*

### 5. Las fallas no son el problema principal, y mejoraron

Tras caer en 2023 en tres de las cuatro líneas (en Vinilos_4 quedó igual), el tiempo medio entre fallas (MTBF) subió en 2024 en las cuatro (de 55,8 h en Vinilos_1 a 110,1 h en Vinilos_4), y el tiempo de reparación se mantiene entre 0,5 y 0,8 h. Ambos están sobrestimados porque la fuente no registra eventos. *Fuente: consulta 07, página «Confiabilidad».*

### 6. El primer turno rinde menos

En las cuatro líneas, el turno de 6 am a 2 pm rinde por debajo del mejor turno, con una diferencia de 2,5 puntos (Vinilos_3) a 7,8 (Vinilos_2). Es el más bajo en Vinilos_2 y Vinilos_3, está empatado como el más bajo en Vinilos_4, y en Vinilos_1 solo la jornada de 6 am a 4:30 pm es más baja. Una explicación posible, que debe verificarse, es el arranque y los cambios de referencia al inicio de la jornada. *Fuente: consulta 10.*

### 7. El dato limita lo que se puede afirmar

- **La calidad se supone 100 %:** el OEE es un máximo.
- **El OEE solo es confiable desde 2024:** en 2022 ninguna línea tiene estándar de velocidad y en 2023 solo del 15 % al 24 %.
- **El registro de no operación casi desaparece desde julio de 2024:** sin corregirlo, la utilización saldría cercana al 100 %.
- **El indicador actual de Excel castiga el aseo programado** (2.000 h): por eso su 77,8 % difiere de la disponibilidad de 84,4 %.
- **Un posible sesgo:** parte de la caída de la disponibilidad podría deberse a que cada vez se anotan mejor los paros y no a que haya más. Los datos no permiten separarlo.

## Recomendaciones

| # | Recomendación | Evidencia | Responsable | Cómo medir el éxito |
|---|---|---|---|---|
| 1 | **Atacar los tres paros operativos con un proyecto de mejora**, empezando por el sistema de dosificación (análisis de causa raíz de derrames y desajustes) | Hallazgos 2 y 3 | Jefatura de producción con mantenimiento | Horas de ajuste, limpieza y alistamiento por cada 100 h trabajadas: de 13,6 en 2024 a menos de 11 |
| 2 | **Convertir los subcódigos más repetidos en plan preventivo**: válvula y retenedores de dosificación, sujeción y roscadores, Video Jet | Hallazgo 3 (consulta 06) | Coordinación de mantenimiento | Fallas del sistema 1.2 por trimestre |
| 3 | **Revisar los estándares de velocidad de las referencias con bajo rendimiento**, como Parchesitos 30 cc (68,1 %): o el estándar está desactualizado o hay un problema real | Consulta 11 | Jefatura de producción | Rendimiento de la referencia dentro de 85 % a 105 % |
| 4 | **Investigar Vinilos_1 y Vinilos_2**: bajo OEE, y Vinilos_2 con la disponibilidad en caída (71,9 % a 64,9 %) y la limpieza por derrame como primera causa | Hallazgo 1 | Jefatura de producción | OEE de ambas líneas por encima de 70 % |
| 5 | **Estandarizar el arranque del primer turno y los cambios de referencia** (programar por familia) | Hallazgos 2 y 6 | Supervisión de turno | Brecha del primer turno con el mejor, por debajo de 2 puntos |
| 6 | **No invertir en capacidad nueva por ahora**; atender primero demanda y programación | Hallazgo 4 | Dirección con planeación y ventas | Utilización de capacidad por encima de 50 % |
| 7 | **Mejorar lo que se registra**: rechazos (calidad), hora de inicio y fin de cada paro, referencia y turno siempre, y la no operación sin interrupciones. Aclarar si «17. PARO DE MAQUINA» equivale a paro por ventas | Hallazgo 7 | Coordinación de mantenimiento | Completitud del registro por encima de 95 % (hoy 82 % en 2024) |
| 8 | **Adoptar el monitoreo con alerta**: disponibilidad de 4 horas por debajo de 40 % y aviso inmediato de fallas | [Documento 06](06_monitoreo_grafana.md) | Supervisión y mantenimiento | Tiempo entre el inicio de un paro grave y la atención |

### Cuánto vale la recomendación 1

Es una estimación para dimensionar, no una promesa. En 2024, ajuste, limpieza y alistamiento sumaron 1.971 h. Si se redujeran en un **20 %**, se recuperarían unas **394 h al año**. Con la velocidad estándar media de las líneas (76 unidades por minuto), son unos **1,8 millones de unidades** de producción posible. Esa producción solo se vende si hay demanda, lo que conecta con el hallazgo 4.

## Guion de la sustentación

Unos 10 minutos, usando solo DBeaver, el ETL, Power BI, Grafana, GitHub y el PDF.

| # | Qué se cuenta | Dónde se muestra | Quién |
|---|---|---|---|
| 1 | El problema: Excel manual, informe mensual, dos necesidades | PDF (portada y contexto) | |
| 2 | La fuente y sus problemas de calidad | PDF; consulta `00_cuadre_etl.sql` en DBeaver | |
| 3 | El ETL y el cuadre: totales que concuerdan con la fuente | Terminal con `docker compose logs etl`; DBeaver | |
| 4 | El modelo dimensional y la jerarquía de paros | DBeaver (diagrama del modelo) | |
| 5 | **Levantar todo con un comando** | `docker compose down -v` y luego `up -d` | |
| 6 | Power BI: hallazgos 1 a 4 y profundización por la jerarquía de paros | Páginas «Resumen», «Causas de paro» y «Capacidad» | |
| 7 | Grafana con datos simulados y una falla provocada | Tablero y `30_demo_escenarios.sql` | |
| 8 | Recomendaciones | PDF o Power BI | |

Conviene repartir los bloques para que ambos hablen, y que cada uno sepa explicar los del otro.

## Cambios en vivo que el docente podría pedir

Ejemplos resueltos para practicar.

**Una medida DAX nueva.** Horas de paro no programado por cada 100 horas trabajadas, que es el indicador de éxito de la recomendación 1:

```dax
Paro por cada 100 h trabajadas =
DIVIDE ( [Horas de paro no programado], [Horas trabajadas] ) * 100
```

Se crea con *Nueva medida* sobre la tabla `Medidas` y se arrastra a una tarjeta o a una tabla por año.

**Un panel nuevo en Grafana.** Minutos de paro no programado por línea en el periodo elegido. *Añadir → Visualización*, fuente `BI Envasado (PostgreSQL)`, formato *Tabla*, visualización *Bar gauge*:

```sql
SELECT maquina AS "Máquina", SUM(minutos_no_programados) AS "Minutos"
FROM ops.lectura_hora
WHERE $__timeFilter(ts) AND maquina IN ($maquina)
GROUP BY maquina
ORDER BY maquina
```

**Modificar una consulta.** Pareto de un solo año o de una sola máquina: en `04_pareto_paros_no_programados.sql`, añadir `AND f.anio = 2024` o `AND x.maquina_key = 3` al `WHERE`. Para ver solo las cinco causas principales, añadir `LIMIT 5` al final.
