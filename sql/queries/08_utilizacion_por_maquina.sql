-- 08 · Utilización de la capacidad por máquina y año
-- Pregunta: ¿qué parte del tiempo disponible opera cada línea realmente?
-- Usuario: alta dirección y planeación (decidir si conviene invertir en capacidad).
-- Técnica: agregación sobre dos hechos de grano distinto (producción y no operación), cada uno agregado por
-- separado antes de unirlos para no duplicar horas; filtro de meses confiables; LAG para la variación.
--
-- HALLAZGO DE CALIDAD: el registro de horas no trabajadas se interrumpe. Desde julio de 2024 casi no hay filas
-- (9 en julio, 0 desde octubre) mientras la producción sigue registrándose. Si se midiera todo el 2024-2025, la
-- utilización saldría cercana al 100 % solo porque nadie anotó los paros. Por eso solo se usan los meses con al
-- menos 30 filas de no operación: los meses normales tienen entre 38 y 125, y los interrumpidos, 11 o menos, así
-- que el umbral cae en una brecha sin casos intermedios. Las horas no trabajadas son las ajustadas (R23).

WITH meses_con_produccion AS (
    SELECT DISTINCT f.anio_mes, f.anio
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
),
filas_por_mes AS (
    SELECT f.anio_mes, COUNT(*) AS filas_no_operacion
    FROM dw.fact_no_operacion n
    JOIN dw.dim_fecha f USING (fecha_key)
    GROUP BY f.anio_mes
),
meses_confiables AS (
    SELECT m.anio_mes, m.anio, COALESCE(x.filas_no_operacion, 0) >= 30 AS confiable
    FROM meses_con_produccion m
    LEFT JOIN filas_por_mes x USING (anio_mes)
),
trabajadas AS (
    SELECT c.anio, m.maquina_nk AS maquina, SUM(COALESCE(p.horas_trabajadas, 0)) AS horas
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN meses_confiables c USING (anio_mes)
    JOIN dw.dim_maquina m USING (maquina_key)
    WHERE c.confiable
    GROUP BY c.anio, m.maquina_nk
),
no_trabajadas AS (
    SELECT c.anio, m.maquina_nk AS maquina, SUM(n.horas_ajustadas) AS horas
    FROM dw.fact_no_operacion n
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN meses_confiables c USING (anio_mes)
    JOIN dw.dim_maquina m USING (maquina_key)
    WHERE c.confiable
    GROUP BY c.anio, m.maquina_nk
),
resumen_meses AS (
    SELECT anio, COUNT(*) FILTER (WHERE confiable) AS meses_con_registro, COUNT(*) AS meses_con_produccion
    FROM meses_confiables
    GROUP BY anio
),
unidas AS (
    SELECT anio,
           maquina,
           COALESCE(t.horas, 0) AS horas_trabajadas,
           COALESCE(n.horas, 0) AS horas_no_trabajadas
    FROM trabajadas t
    FULL JOIN no_trabajadas n USING (anio, maquina)
)
SELECT u.anio,
       u.maquina,
       r.meses_con_registro || ' de ' || r.meses_con_produccion AS meses_usados,
       ROUND(u.horas_trabajadas)       AS horas_trabajadas,
       ROUND(u.horas_no_trabajadas)    AS horas_no_trabajadas,
       ROUND(100 * u.horas_trabajadas / NULLIF(u.horas_trabajadas + u.horas_no_trabajadas, 0), 1) AS utilizacion_pct,
       ROUND(100 * (u.horas_trabajadas / NULLIF(u.horas_trabajadas + u.horas_no_trabajadas, 0)
             - LAG(u.horas_trabajadas / NULLIF(u.horas_trabajadas + u.horas_no_trabajadas, 0)) OVER (PARTITION BY u.maquina ORDER BY u.anio)), 1)
         AS variacion_vs_anio_anterior_puntos,
       ROUND(100 * SUM(u.horas_trabajadas) OVER (PARTITION BY u.anio)
             / NULLIF(SUM(u.horas_trabajadas + u.horas_no_trabajadas) OVER (PARTITION BY u.anio), 0), 1) AS utilizacion_planta_pct
FROM unidas u
JOIN resumen_meses r USING (anio)
ORDER BY u.anio, u.maquina;
