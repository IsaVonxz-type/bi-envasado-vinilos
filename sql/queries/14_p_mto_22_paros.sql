-- 14 · Indicadores de paros que reporta hoy el procedimiento P-MTO-22
-- Pregunta: reproducir «porcentaje de códigos de paro por máquina» y el análisis detallado de los códigos 01, 03 y 05.
-- Usuario: coordinación de mantenimiento.
-- Técnica: participación con SUM() OVER por partición.

-- (a) Porcentaje de cada código de paro dentro del total de paros de cada máquina, incluidos los programados,
-- como en el informe de Excel.
SELECT m.maquina_nk AS maquina,
       c.codigo,
       c.codigo_nombre AS causa,
       ROUND(SUM(x.minutos_paro) / 60, 1) AS horas,
       ROUND(100 * SUM(x.minutos_paro) / SUM(SUM(x.minutos_paro)) OVER (PARTITION BY m.maquina_nk), 1) AS pct_de_la_maquina
FROM dw.fact_paro x
JOIN dw.dim_causa_paro c USING (causa_key)
JOIN dw.dim_maquina m USING (maquina_key)
GROUP BY m.maquina_nk, c.codigo, c.codigo_nombre
ORDER BY m.maquina_nk, horas DESC;

-- (b) Análisis detallado de los códigos 01, 03 y 05 por máquina y año: horas y participación
-- de cada máquina en el total de horas del código en ese año.
SELECT f.anio,
       c.codigo,
       m.maquina_nk AS maquina,
       ROUND(SUM(x.minutos_paro) / 60, 1) AS horas,
       COUNT(*) AS registros,
       ROUND(100 * SUM(x.minutos_paro) / SUM(SUM(x.minutos_paro)) OVER (PARTITION BY f.anio, c.codigo), 1) AS pct_del_codigo_en_el_anio
FROM dw.fact_paro x
JOIN dw.dim_causa_paro c USING (causa_key)
JOIN dw.dim_fecha f USING (fecha_key)
JOIN dw.dim_maquina m USING (maquina_key)
WHERE c.codigo IN (1, 3, 5)
GROUP BY f.anio, c.codigo, m.maquina_nk
ORDER BY f.anio, c.codigo, horas DESC;
