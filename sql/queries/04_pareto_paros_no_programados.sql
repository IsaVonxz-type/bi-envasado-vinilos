-- 04 · Pareto de paros no programados
-- Pregunta: ¿qué pocas causas concentran la mayor parte de las horas perdidas?
-- Usuario: coordinación de mantenimiento y jefatura de producción.
-- Técnica: porcentaje acumulado con SUM() OVER ordenado, y clasificación A/B/C a partir del acumulado anterior.
-- Zona A: causas que, juntas, explican hasta el 80 % de las horas. Para un solo año, agregue AND f.anio = 2024.
-- No incluye los paros programados (códigos 15, 16 y 17) ni la no operación por ventas, que es otra pérdida.

WITH causas AS (
    SELECT c.codigo,
           c.codigo_nombre,
           c.area_impacto,
           SUM(x.minutos_paro) / 60 AS horas
    FROM dw.fact_paro x
    JOIN dw.dim_causa_paro c USING (causa_key)
    JOIN dw.dim_fecha f USING (fecha_key)
    WHERE c.clasificacion_oee = 'No programado'
    GROUP BY c.codigo, c.codigo_nombre, c.area_impacto
)
SELECT ROW_NUMBER() OVER (ORDER BY horas DESC, codigo) AS posicion,
       codigo_nombre AS causa,
       area_impacto,
       ROUND(horas)  AS horas,
       ROUND(100 * horas / SUM(horas) OVER (), 1) AS pct,
       ROUND(100 * SUM(horas) OVER (ORDER BY horas DESC, codigo) / SUM(horas) OVER (), 1) AS pct_acumulado,
       CASE
           WHEN (SUM(horas) OVER (ORDER BY horas DESC, codigo) - horas) / SUM(horas) OVER () < 0.80 THEN 'A'
           WHEN (SUM(horas) OVER (ORDER BY horas DESC, codigo) - horas) / SUM(horas) OVER () < 0.95 THEN 'B'
           ELSE 'C'
       END AS zona
FROM causas
ORDER BY posicion;
