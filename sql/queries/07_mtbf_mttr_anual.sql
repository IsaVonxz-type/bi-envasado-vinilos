-- 07 · MTBF y MTTR anuales por máquina
-- Pregunta: ¿las fallas son menos frecuentes y se reparan más rápido que el año anterior?
-- Usuario: coordinación de mantenimiento.
-- Técnica: agregación, LAG para el año anterior y RANK dentro de cada año.
-- Mismas definiciones que dw.vw_confiabilidad_mensual: una falla es una línea con código 01 o 03; el MTTR incluye
-- la espera de mantenimiento (código 02). Varias fallas en una misma línea cuentan como una, así que ambos
-- indicadores quedan sobrestimados. Se suma antes de dividir, no se promedian los meses.
-- Con pocas fallas (columna fallas) el MTBF y el MTTR son inestables: 2025 solo cubre tres meses.

WITH operacion AS (
    SELECT f.anio, m.maquina_nk AS maquina, SUM(b.minutos_operativos) AS minutos_operativos
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio, m.maquina_nk
),
fallas AS (
    SELECT f.anio,
           m.maquina_nk AS maquina,
           COUNT(*) FILTER (WHERE c.es_falla)                          AS fallas,
           SUM(p.minutos_paro) FILTER (WHERE c.codigo IN (1, 2, 3))    AS minutos_reparacion
    FROM dw.fact_paro p
    JOIN dw.dim_causa_paro c USING (causa_key)
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio, m.maquina_nk
),
kpi AS (
    SELECT o.anio,
           o.maquina,
           COALESCE(x.fallas, 0) AS fallas,
           o.minutos_operativos / 60 / NULLIF(x.fallas, 0)  AS mtbf_horas,
           x.minutos_reparacion / 60 / NULLIF(x.fallas, 0)  AS mttr_horas
    FROM operacion o
    LEFT JOIN fallas x USING (anio, maquina)
)
SELECT anio,
       maquina,
       fallas,
       ROUND(mtbf_horas, 1)                                   AS mtbf_horas,
       ROUND(mtbf_horas - LAG(mtbf_horas) OVER w, 1)          AS variacion_mtbf_horas,
       ROUND(mttr_horas, 2)                                   AS mttr_horas,
       ROUND(mttr_horas - LAG(mttr_horas) OVER w, 2)          AS variacion_mttr_horas,
       RANK() OVER (PARTITION BY anio ORDER BY mtbf_horas DESC NULLS LAST) AS puesto_por_mtbf
FROM kpi
WINDOW w AS (PARTITION BY maquina ORDER BY anio)
ORDER BY anio, puesto_por_mtbf, maquina;
