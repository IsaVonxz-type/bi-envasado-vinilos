-- 05 · Las tres principales causas de paro no programado de cada máquina
-- Pregunta: ¿qué debe atacar primero el plan de mantenimiento en cada línea?
-- Usuario: coordinación de mantenimiento, supervisión.
-- Técnica: ROW_NUMBER por partición de máquina y participación sobre el total de la máquina con SUM() OVER.
-- Se ordena por horas y se desempata por código, para que el resultado sea estable.

WITH por_causa AS (
    SELECT m.maquina_nk AS maquina,
           c.codigo,
           c.codigo_nombre AS causa,
           SUM(x.minutos_paro) / 60 AS horas
    FROM dw.fact_paro x
    JOIN dw.dim_causa_paro c USING (causa_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    WHERE c.clasificacion_oee = 'No programado'
    GROUP BY m.maquina_nk, c.codigo, c.codigo_nombre
),
ordenadas AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY maquina ORDER BY horas DESC, codigo) AS puesto,
           100 * horas / SUM(horas) OVER (PARTITION BY maquina)                 AS pct_de_la_maquina
    FROM por_causa
)
SELECT maquina,
       puesto,
       causa,
       ROUND(horas)                      AS horas,
       ROUND(pct_de_la_maquina, 1)       AS pct_de_la_maquina,
       ROUND(SUM(pct_de_la_maquina) OVER (PARTITION BY maquina ORDER BY puesto), 1) AS pct_acumulado
FROM ordenadas
WHERE puesto <= 3
ORDER BY maquina, puesto;
