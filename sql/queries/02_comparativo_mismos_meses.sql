-- 02 · Comparativo de 2025 contra 2024 con los mismos meses
-- Pregunta: ¿mejora o empeora el OEE frente al año anterior?
-- Usuario: alta dirección.
-- Técnica: comparativo entre periodos con LAG sobre el año. Solo se comparan los meses que ya existen en 2025,
-- porque el archivo termina el 28/03/2025: comparar el 2025 parcial con el 2024 completo sería engañoso.
-- Marzo de 2025 es un mes parcial.

WITH meses_comparables AS (
    SELECT DISTINCT f.mes
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
    WHERE f.anio = 2025
),
periodo AS (
    SELECT f.anio,
           m.maquina_nk AS maquina,
           SUM(b.minutos_planificados) AS minutos_planificados,
           SUM(b.minutos_operativos)   AS minutos_operativos,
           SUM(b.unidades_producidas)  AS unidades_producidas,
           SUM(b.unidades_teoricas)    AS unidades_teoricas,
           SUM(b.minutos_operativos_con_estandar) AS minutos_con_estandar
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    JOIN meses_comparables USING (mes)
    WHERE f.anio IN (2024, 2025)
    GROUP BY f.anio, m.maquina_nk
),
kpi AS (
    SELECT anio,
           maquina,
           minutos_operativos / 60 AS horas_operativas,
           minutos_con_estandar / NULLIF(minutos_operativos, 0) AS cobertura,
           minutos_operativos / NULLIF(minutos_planificados, 0) AS disponibilidad,
           unidades_producidas / NULLIF(unidades_teoricas, 0)   AS rendimiento,
           minutos_operativos / NULLIF(minutos_planificados, 0)
             * unidades_producidas / NULLIF(unidades_teoricas, 0) AS oee
    FROM periodo
),
con_anterior AS (
    SELECT *,
           LAG(disponibilidad) OVER w AS disponibilidad_anterior,
           LAG(rendimiento)    OVER w AS rendimiento_anterior,
           LAG(oee)            OVER w AS oee_anterior,
           LAG(horas_operativas) OVER w AS horas_operativas_anterior
    FROM kpi
    WINDOW w AS (PARTITION BY maquina ORDER BY anio)
)
SELECT maquina,
       ROUND(100 * oee_anterior, 1)                    AS oee_2024_pct,
       ROUND(100 * oee, 1)                             AS oee_2025_pct,
       ROUND(100 * (oee - oee_anterior), 1)            AS variacion_oee_puntos,
       ROUND(100 * disponibilidad_anterior, 1)         AS disponibilidad_2024_pct,
       ROUND(100 * disponibilidad, 1)                  AS disponibilidad_2025_pct,
       ROUND(100 * (disponibilidad - disponibilidad_anterior), 1) AS variacion_disponibilidad_puntos,
       ROUND(100 * (rendimiento - rendimiento_anterior), 1)       AS variacion_rendimiento_puntos,
       ROUND(horas_operativas_anterior)                AS horas_operativas_2024,
       ROUND(horas_operativas)                         AS horas_operativas_2025,
       ROUND(100 * cobertura, 1)                       AS cobertura_rendimiento_2025_pct
FROM con_anterior
WHERE anio = 2025
ORDER BY variacion_oee_puntos;
