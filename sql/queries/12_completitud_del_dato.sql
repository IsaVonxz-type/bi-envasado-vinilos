-- 12 · Completitud del registro por año
-- Pregunta: ¿el dato mejora con el tiempo? ¿Desde cuándo se puede confiar en el OEE?
-- Usuario: mantenimiento y responsables de datos.
-- Técnica: promedio ponderado por número de registros (no promedio de promedios) y LAG para la mejora anual.
-- Completitud: línea de producción con referencia, turno y estándar de velocidad.

SELECT LEFT(anio_mes, 4)::int AS anio,
       SUM(registros) AS registros,
       ROUND(100 * SUM(registros * con_referencia) / SUM(registros), 1) AS con_referencia_pct,
       ROUND(100 * SUM(registros * con_turno) / SUM(registros), 1)      AS con_turno_pct,
       ROUND(100 * SUM(registros * con_estandar) / SUM(registros), 1)   AS con_estandar_pct,
       ROUND(100 * SUM(registros * completitud) / SUM(registros), 1)    AS completitud_pct,
       ROUND(100 * (SUM(registros * completitud) / SUM(registros)
             - LAG(SUM(registros * completitud) / SUM(registros)) OVER (ORDER BY LEFT(anio_mes, 4))), 1) AS mejora_vs_anio_anterior_puntos
FROM dw.vw_completitud_mensual
GROUP BY LEFT(anio_mes, 4)
ORDER BY anio;
