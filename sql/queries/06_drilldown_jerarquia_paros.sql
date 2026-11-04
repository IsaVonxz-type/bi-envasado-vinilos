-- 06 · Profundización por la jerarquía de paros: código → sistema → subcódigo
-- Pregunta: dentro de las fallas electromecánicas (01), de potencia (03) y los ajustes operativos (05),
-- ¿qué sistema y qué subcódigo concentran el tiempo?
-- Usuario: coordinación de mantenimiento (justificar planes preventivos).
-- Técnica: la jerarquía está aplanada en dim_causa_paro, así que se recorre con porcentajes sobre el padre
-- calculados con SUM() OVER por partición: el padre inmediato es el sistema, y el abuelo, el código.
-- Los paros de estos códigos sin detalle quedan en 'Sin especificar'. En el código 03 son la mayoría,
-- por lo que su análisis es parcial.

WITH hojas AS (
    SELECT c.codigo,
           c.codigo_nombre,
           c.sistema,
           c.subcodigo,
           SUM(x.minutos_paro) / 60 AS horas,
           COUNT(*)                 AS registros
    FROM dw.fact_paro x
    JOIN dw.dim_causa_paro c USING (causa_key)
    WHERE c.codigo IN (1, 3, 5)
    GROUP BY c.codigo, c.codigo_nombre, c.sistema, c.subcodigo
)
SELECT codigo_nombre AS codigo,
       sistema,
       subcodigo,
       ROUND(horas, 1)  AS horas,
       registros,
       ROUND(100 * horas / SUM(horas) OVER (PARTITION BY codigo), 1)           AS pct_del_codigo,
       ROUND(100 * horas / SUM(horas) OVER (PARTITION BY codigo, sistema), 1)  AS pct_del_sistema,
       ROUND(100 * SUM(horas) OVER (PARTITION BY codigo ORDER BY horas DESC, sistema, subcodigo)
             / SUM(horas) OVER (PARTITION BY codigo), 1)                       AS pct_acumulado_en_el_codigo
FROM hojas
ORDER BY codigo, horas DESC, sistema, subcodigo;

-- Subtotales por nivel (código, sistema, subcódigo) en una sola consulta, con ROLLUP.
SELECT c.codigo_nombre AS codigo,
       c.sistema,
       c.subcodigo,
       CASE GROUPING(c.codigo_nombre, c.sistema, c.subcodigo)
            WHEN 0 THEN 'subcódigo'
            WHEN 1 THEN 'sistema'
            WHEN 3 THEN 'código'
            ELSE 'total'
       END AS nivel,
       ROUND(SUM(x.minutos_paro) / 60, 1) AS horas
FROM dw.fact_paro x
JOIN dw.dim_causa_paro c USING (causa_key)
WHERE c.codigo IN (1, 3, 5)
GROUP BY ROLLUP (c.codigo_nombre, c.sistema, c.subcodigo)
ORDER BY c.codigo_nombre NULLS LAST, c.sistema NULLS LAST, horas DESC;
