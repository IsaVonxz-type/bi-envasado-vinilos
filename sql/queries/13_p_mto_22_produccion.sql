-- 13 · Indicadores de producción que reporta hoy el procedimiento P-MTO-22
-- Pregunta: reproducir, desde el modelo dimensional, los gráficos de producción del informe mensual de Excel.
-- Usuario: alta dirección (comité mensual).
-- Técnica: acumulado anual con SUM() OVER y comparativo entre años con LAG.

-- (a) «Producción general»: pacas válidas por mes y acumulado del año.
-- Las pacas imposibles (R08) no suman: el valor original queda en pacas_reportadas.
-- La variación contra el mismo mes del año anterior solo se calcula si ambos meses tienen al menos 40 líneas de
-- producción: julio a septiembre de 2022 tienen entre 5 y 7, y compararlos con 2023 daría variaciones sin sentido.
SELECT f.anio,
       f.mes,
       f.anio_mes,
       COUNT(*) AS lineas_del_mes,
       ROUND(SUM(p.pacas_validas)) AS pacas,
       ROUND(SUM(SUM(p.pacas_validas)) OVER (PARTITION BY f.anio ORDER BY f.mes)) AS pacas_acumuladas_del_anio,
       CASE WHEN COUNT(*) >= 40 AND LAG(COUNT(*)) OVER (PARTITION BY f.mes ORDER BY f.anio) >= 40
            THEN ROUND(100 * (SUM(p.pacas_validas) / NULLIF(LAG(SUM(p.pacas_validas)) OVER (PARTITION BY f.mes ORDER BY f.anio), 0) - 1), 1)
       END AS variacion_vs_mismo_mes_anio_anterior_pct
FROM dw.fact_produccion p
JOIN dw.dim_fecha f USING (fecha_key)
GROUP BY f.anio, f.mes, f.anio_mes
ORDER BY f.anio, f.mes;

-- (b) «Producción por máquina, comparativo 2024 vs 2025», con los mismos meses.
-- Marzo de 2025 es parcial (el archivo termina el 28/03).
WITH meses_2025 AS (
    SELECT DISTINCT f.mes FROM dw.fact_produccion p JOIN dw.dim_fecha f USING (fecha_key) WHERE f.anio = 2025
),
por_maquina AS (
    SELECT m.maquina_nk AS maquina, f.anio, SUM(p.pacas_validas) AS pacas
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    JOIN meses_2025 USING (mes)
    WHERE f.anio IN (2024, 2025)
    GROUP BY m.maquina_nk, f.anio
),
comparado AS (
    SELECT maquina,
           anio,
           LAG(pacas) OVER (PARTITION BY maquina ORDER BY anio) AS pacas_anterior,
           pacas
    FROM por_maquina
)
SELECT maquina,
       ROUND(pacas_anterior)                                       AS pacas_2024,
       ROUND(pacas)                                                AS pacas_2025,
       ROUND(pacas - pacas_anterior)                               AS diferencia,
       ROUND(100 * (pacas / NULLIF(pacas_anterior, 0) - 1), 1)     AS variacion_pct
FROM comparado
WHERE anio = 2025
ORDER BY maquina;
