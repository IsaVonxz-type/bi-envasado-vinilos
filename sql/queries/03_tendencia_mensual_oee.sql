-- 03 · Tendencia mensual del OEE por máquina
-- Pregunta: ¿cómo evoluciona cada línea mes a mes y frente al mismo mes del año anterior?
-- Usuario: coordinación de mantenimiento, jefatura de producción.
-- Técnica: funciones de ventana sobre una rejilla completa de meses (LAG de 1 y 12 meses y media móvil de 3 meses).
-- La media móvil suma tiempos y unidades de los 3 meses antes de dividir: promediar porcentajes daría el mismo peso
-- a un mes de 100 horas que a uno de 1.000. Desde 2024, que es cuando el OEE es confiable.

WITH limite AS (
    SELECT MAX(f.anio_mes) AS ultimo_mes
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
),
rejilla AS (
    SELECT DISTINCT f.anio_mes, m.maquina_key, m.maquina_nk AS maquina
    FROM dw.dim_fecha f
    CROSS JOIN dw.dim_maquina m
    CROSS JOIN limite
    WHERE f.anio_mes >= '2024-01' AND f.anio_mes <= limite.ultimo_mes
),
mensual AS (
    SELECT f.anio_mes,
           b.maquina_key,
           SUM(b.minutos_planificados) AS pl,
           SUM(b.minutos_operativos)   AS op,
           SUM(b.unidades_producidas)  AS up,
           SUM(b.unidades_teoricas)    AS ut
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    GROUP BY f.anio_mes, b.maquina_key
),
serie AS (
    SELECT r.anio_mes,
           r.maquina,
           COALESCE(m.pl, 0) AS pl,
           COALESCE(m.op, 0) AS op,
           COALESCE(m.up, 0) AS up,
           COALESCE(m.ut, 0) AS ut
    FROM rejilla r
    LEFT JOIN mensual m USING (anio_mes, maquina_key)
),
calculo AS (
    SELECT anio_mes,
           maquina,
           op / NULLIF(pl, 0) * up / NULLIF(ut, 0) AS oee,
           SUM(op) OVER m3 / NULLIF(SUM(pl) OVER m3, 0)
             * SUM(up) OVER m3 / NULLIF(SUM(ut) OVER m3, 0) AS oee_movil_3m
    FROM serie
    WINDOW m3 AS (PARTITION BY maquina ORDER BY anio_mes ROWS BETWEEN 2 PRECEDING AND CURRENT ROW)
)
SELECT anio_mes,
       maquina,
       ROUND(100 * oee, 1)                                     AS oee_pct,
       ROUND(100 * (oee - LAG(oee, 1) OVER w), 1)              AS variacion_vs_mes_anterior_puntos,
       ROUND(100 * oee_movil_3m, 1)                            AS oee_movil_3_meses_pct,
       ROUND(100 * (oee - LAG(oee, 12) OVER w), 1)             AS variacion_vs_mismo_mes_anio_anterior_puntos
FROM calculo
WINDOW w AS (PARTITION BY maquina ORDER BY anio_mes)
ORDER BY maquina, anio_mes;
