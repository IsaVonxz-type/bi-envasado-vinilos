-- 11 · Rendimiento por referencia
-- Pregunta: ¿qué referencias rinden por debajo de lo que la máquina puede dar y deberían revisarse?
-- Usuario: jefatura de producción.
-- Técnica: agregación, PERCENT_RANK y NTILE para ubicar cada referencia dentro de la distribución de la planta.
-- Desde 2024 y solo referencias con estándar de velocidad y al menos 100 horas operativas.
-- Un rendimiento superior al 120 % sugiere pacas mal transcritas o estándares desactualizados: no se recorta.

WITH por_referencia AS (
    SELECT r.referencia_nk AS referencia,
           r.familia,
           SUM(b.minutos_operativos_con_estandar) AS minutos_con_estandar,
           SUM(b.unidades_producidas)              AS up,
           SUM(b.unidades_teoricas)                AS ut
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_referencia r USING (referencia_key)
    WHERE f.anio >= 2024 AND r.referencia_nk <> 'Desconocida'
    GROUP BY r.referencia_nk, r.familia
    HAVING SUM(b.minutos_operativos_con_estandar) >= 60 * 100
),
kpi AS (
    SELECT referencia, familia, minutos_con_estandar / 60 AS horas, up, up / NULLIF(ut, 0) AS rendimiento
    FROM por_referencia
)
SELECT referencia,
       familia,
       ROUND(horas)                         AS horas_operativas,
       ROUND(up)                            AS unidades_producidas,
       ROUND(100 * rendimiento, 1)          AS rendimiento_pct,
       ROUND(100 * (rendimiento - AVG(rendimiento) OVER ()), 1) AS puntos_vs_promedio_de_referencias,
       NTILE(4) OVER (ORDER BY rendimiento) AS cuartil_de_rendimiento,
       ROUND(PERCENT_RANK() OVER (ORDER BY rendimiento)::numeric, 2) AS percentil,
       rendimiento > 1.2                    AS revisar_dato
FROM kpi
ORDER BY rendimiento;
