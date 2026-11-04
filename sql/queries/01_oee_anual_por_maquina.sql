-- 01 · OEE anual por máquina
-- Pregunta: ¿qué línea rinde mejor cada año y desde cuándo el OEE es confiable?
-- Usuario: alta dirección y jefatura de producción.
-- Técnica: agregación (se suman tiempos y unidades antes de dividir), RANK y totales de planta con funciones de ventana.
-- Cuidado: la calidad es un supuesto del 100 %, así que el OEE es un máximo. Solo se clasifica
-- una máquina cuando al menos el 80 % de su tiempo operativo tiene estándar de velocidad.

WITH anual AS (
    SELECT f.anio,
           m.maquina_nk AS maquina,
           SUM(b.minutos_planificados)            AS minutos_planificados,
           SUM(b.minutos_operativos)              AS minutos_operativos,
           SUM(b.unidades_producidas)             AS unidades_producidas,
           SUM(b.unidades_teoricas)               AS unidades_teoricas,
           SUM(b.minutos_operativos_con_estandar) AS minutos_con_estandar
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio, m.maquina_nk
),
kpi AS (
    SELECT anio,
           maquina,
           minutos_operativos,
           minutos_planificados,
           minutos_operativos / NULLIF(minutos_planificados, 0)                       AS disponibilidad,
           unidades_producidas / NULLIF(unidades_teoricas, 0)                         AS rendimiento,
           minutos_operativos / NULLIF(minutos_planificados, 0)
             * unidades_producidas / NULLIF(unidades_teoricas, 0)                     AS oee,
           minutos_con_estandar / NULLIF(minutos_operativos, 0)                       AS cobertura
    FROM anual
)
SELECT anio,
       maquina,
       ROUND(100 * disponibilidad, 1)  AS disponibilidad_pct,
       ROUND(100 * rendimiento, 1)     AS rendimiento_pct,
       ROUND(100 * oee, 1)             AS oee_pct,
       ROUND(100 * cobertura, 1)       AS cobertura_rendimiento_pct,
       cobertura >= 0.8                AS oee_confiable,
       CASE WHEN cobertura >= 0.8
            THEN RANK() OVER (PARTITION BY anio, cobertura >= 0.8 ORDER BY oee DESC)
       END                             AS posicion_en_el_anio,
       ROUND(100 * SUM(minutos_operativos) OVER (PARTITION BY anio)
             / NULLIF(SUM(minutos_planificados) OVER (PARTITION BY anio), 0), 1) AS disponibilidad_planta_pct
FROM kpi
ORDER BY anio, posicion_en_el_anio NULLS LAST, maquina;
