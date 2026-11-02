CREATE VIEW dw.vw_oee_base AS
WITH produccion AS (
    SELECT fecha_key,
           maquina_key,
           turno_key,
           referencia_key,
           MAX(estandar_key) AS estandar_key,
           SUM(COALESCE(horas_trabajadas, 0)) * 60 AS minutos_trabajados,
           SUM(unidades_producidas) AS unidades_producidas,
           BOOL_AND(unidades_producidas IS NOT NULL) AS unidades_completas
    FROM dw.fact_produccion
    GROUP BY fecha_key, maquina_key, turno_key, referencia_key
),
paro AS (
    SELECT p.fecha_key,
           p.maquina_key,
           p.turno_key,
           p.referencia_key,
           SUM(p.minutos_paro) FILTER (WHERE c.clasificacion_oee = 'Programado') AS minutos_programados,
           SUM(p.minutos_paro) FILTER (WHERE c.clasificacion_oee = 'No programado') AS minutos_no_programados
    FROM dw.fact_paro p
    JOIN dw.dim_causa_paro c USING (causa_key)
    GROUP BY p.fecha_key, p.maquina_key, p.turno_key, p.referencia_key
),
base AS (
    SELECT COALESCE(pr.fecha_key, pa.fecha_key) AS fecha_key,
           COALESCE(pr.maquina_key, pa.maquina_key) AS maquina_key,
           COALESCE(pr.turno_key, pa.turno_key) AS turno_key,
           COALESCE(pr.referencia_key, pa.referencia_key) AS referencia_key,
           pr.estandar_key,
           COALESCE(pr.minutos_trabajados, 0) AS minutos_trabajados,
           COALESCE(pa.minutos_programados, 0) AS minutos_programados,
           COALESCE(pa.minutos_no_programados, 0) AS minutos_no_programados,
           pr.unidades_producidas,
           COALESCE(pr.unidades_completas, FALSE) AS unidades_completas
    FROM produccion pr
    FULL JOIN paro pa
      ON pr.fecha_key = pa.fecha_key
     AND pr.maquina_key = pa.maquina_key
     AND pr.turno_key = pa.turno_key
     AND pr.referencia_key = pa.referencia_key
),
tiempos AS (
    SELECT b.*,
           GREATEST(b.minutos_trabajados - b.minutos_programados, 0) AS minutos_planificados,
           GREATEST(b.minutos_trabajados - b.minutos_programados - b.minutos_no_programados, 0) AS minutos_operativos,
           e.unidades_por_minuto
    FROM base b
    LEFT JOIN dw.dim_estandar_produccion e USING (estandar_key)
)
SELECT fecha_key,
       maquina_key,
       turno_key,
       referencia_key,
       minutos_trabajados,
       minutos_programados,
       minutos_no_programados,
       minutos_planificados,
       minutos_operativos,
       CASE WHEN unidades_completas AND unidades_por_minuto IS NOT NULL THEN unidades_producidas END AS unidades_producidas,
       CASE WHEN unidades_completas AND unidades_por_minuto IS NOT NULL THEN minutos_operativos * unidades_por_minuto END AS unidades_teoricas,
       CASE WHEN unidades_completas AND unidades_por_minuto IS NOT NULL THEN minutos_operativos ELSE 0 END AS minutos_operativos_con_estandar,
       minutos_no_programados * unidades_por_minuto AS unidades_perdidas_no_programado
FROM tiempos;

CREATE VIEW dw.vw_oee_mensual AS
SELECT f.anio,
       f.mes,
       f.anio_mes,
       m.maquina_nk AS maquina,
       SUM(b.minutos_planificados) / 60 AS horas_planificadas,
       SUM(b.minutos_operativos) / 60 AS horas_operativas,
       SUM(b.minutos_operativos)::NUMERIC / NULLIF(SUM(b.minutos_planificados), 0) AS disponibilidad,
       SUM(b.unidades_producidas)::NUMERIC / NULLIF(SUM(b.unidades_teoricas), 0) AS rendimiento,
       1.0::NUMERIC AS calidad_supuesta,
       SUM(b.minutos_operativos)::NUMERIC / NULLIF(SUM(b.minutos_planificados), 0)
         * SUM(b.unidades_producidas)::NUMERIC / NULLIF(SUM(b.unidades_teoricas), 0) AS oee,
       SUM(b.minutos_operativos_con_estandar)::NUMERIC / NULLIF(SUM(b.minutos_operativos), 0) AS cobertura_rendimiento,
       SUM(b.unidades_perdidas_no_programado) AS unidades_perdidas_no_programado
FROM dw.vw_oee_base b
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
GROUP BY f.anio, f.mes, f.anio_mes, m.maquina_nk;

CREATE VIEW dw.vw_confiabilidad_mensual AS
WITH operacion AS (
    SELECT f.anio_mes, m.maquina_nk AS maquina, SUM(b.minutos_operativos) AS minutos_operativos
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio_mes, m.maquina_nk
),
fallas AS (
    SELECT f.anio_mes,
           m.maquina_nk AS maquina,
           COUNT(*) FILTER (WHERE c.es_falla) AS fallas,
           SUM(p.minutos_paro) FILTER (WHERE c.codigo IN (1, 2, 3)) AS minutos_reparacion
    FROM dw.fact_paro p
    JOIN dw.dim_causa_paro c USING (causa_key)
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio_mes, m.maquina_nk
)
SELECT o.anio_mes,
       o.maquina,
       COALESCE(x.fallas, 0) AS fallas,
       o.minutos_operativos / 60 / NULLIF(x.fallas, 0) AS mtbf_horas,
       x.minutos_reparacion / 60 / NULLIF(x.fallas, 0) AS mttr_horas
FROM operacion o
LEFT JOIN fallas x USING (anio_mes, maquina);

CREATE VIEW dw.vw_utilizacion_mensual AS
WITH trabajadas AS (
    SELECT f.anio_mes, m.maquina_nk AS maquina, SUM(COALESCE(p.horas_trabajadas, 0)) AS horas_trabajadas
    FROM dw.fact_produccion p
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio_mes, m.maquina_nk
),
no_trabajadas AS (
    SELECT f.anio_mes, m.maquina_nk AS maquina, SUM(n.horas_ajustadas) AS horas_no_trabajadas
    FROM dw.fact_no_operacion n
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    GROUP BY f.anio_mes, m.maquina_nk
)
SELECT anio_mes,
       maquina,
       COALESCE(t.horas_trabajadas, 0) AS horas_trabajadas,
       COALESCE(n.horas_no_trabajadas, 0) AS horas_no_trabajadas,
       COALESCE(t.horas_trabajadas, 0)
         / NULLIF(COALESCE(t.horas_trabajadas, 0) + COALESCE(n.horas_no_trabajadas, 0), 0) AS utilizacion
FROM trabajadas t
FULL JOIN no_trabajadas n USING (anio_mes, maquina);

CREATE VIEW dw.vw_completitud_mensual AS
SELECT f.anio_mes,
       m.maquina_nk AS maquina,
       COUNT(*) AS registros,
       AVG(CASE WHEN r.referencia_nk <> 'Desconocida' THEN 1.0 ELSE 0.0 END) AS con_referencia,
       AVG(CASE WHEN t.turno_nk <> 'Desconocido' THEN 1.0 ELSE 0.0 END) AS con_turno,
       AVG(CASE WHEN p.estandar_key IS NOT NULL THEN 1.0 ELSE 0.0 END) AS con_estandar,
       AVG(CASE WHEN r.referencia_nk <> 'Desconocida' AND t.turno_nk <> 'Desconocido' AND p.estandar_key IS NOT NULL
                THEN 1.0 ELSE 0.0 END) AS completitud
FROM dw.fact_produccion p
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
JOIN dw.dim_referencia r USING (referencia_key)
JOIN dw.dim_turno t USING (turno_key)
GROUP BY f.anio_mes, m.maquina_nk;
