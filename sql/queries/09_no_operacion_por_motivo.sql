-- 09 · Por qué no operan las líneas
-- Pregunta: del tiempo en que las máquinas no trabajan, ¿cuánto se debe a ventas, a programación o a causas operativas?
-- Usuario: alta dirección, planeación y ventas.
-- Técnica: participación sobre el total del año con SUM() OVER, ranking del motivo en cada año y variación contra el año anterior.
-- 17. PARO DE MAQUINA se asigna a 'Paro de máquina por ventas' por equivalencia con el catálogo vigente: es un
-- supuesto del ETL que pesa mucho en este resultado y conviene validarlo con la empresa.
-- Cuidado: desde julio de 2024 el registro de no operación se interrumpe (ver la consulta 08), así que las horas
-- de 2024 corresponden a menos meses (columna meses_con_registro) y no hay datos de 2025. No son comparables en horas;
-- compare los porcentajes.

WITH anual AS (
    SELECT f.anio,
           d.categoria,
           d.tipo,
           COUNT(DISTINCT f.anio_mes) AS meses_con_registro,
           SUM(n.horas_ajustadas) AS horas
    FROM dw.fact_no_operacion n
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_motivo_no_operacion d USING (motivo_key)
    GROUP BY f.anio, d.categoria, d.tipo
)
SELECT anio,
       categoria,
       tipo AS motivo,
       meses_con_registro,
       ROUND(horas)                                              AS horas,
       ROUND(100 * horas / SUM(horas) OVER (PARTITION BY anio), 1) AS pct_del_anio,
       RANK() OVER (PARTITION BY anio ORDER BY horas DESC)         AS puesto_en_el_anio,
       ROUND(horas - LAG(horas) OVER (PARTITION BY tipo ORDER BY anio)) AS variacion_horas_vs_anio_anterior
FROM anual
ORDER BY anio, puesto_en_el_anio;
