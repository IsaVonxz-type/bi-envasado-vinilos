-- 10 · Desempeño por turno
-- Pregunta: ¿qué turno rinde menos y qué tan grande es la brecha con el mejor?
-- Usuario: jefatura de producción, supervisión de turno.
-- Técnica: agregación, FIRST_VALUE para la brecha contra el mejor turno de la máquina, y RANK.
-- Solo desde 2024, cuando el OEE es confiable. Los turnos 'Desconocido' y 'No aplica' se muestran aparte y
-- no se ocultan: en 2022 y 2023 la mayoría de las filas no tiene turno, y eso es en sí un hallazgo.

WITH por_turno AS (
    SELECT m.maquina_nk AS maquina,
           t.turno_nk    AS turno,
           SUM(b.minutos_planificados) AS pl,
           SUM(b.minutos_operativos)   AS op,
           SUM(b.unidades_producidas)  AS up,
           SUM(b.unidades_teoricas)    AS ut
    FROM dw.vw_oee_base b
    JOIN dw.dim_fecha f USING (fecha_key)
    JOIN dw.dim_maquina m USING (maquina_key)
    JOIN dw.dim_turno t USING (turno_key)
    WHERE f.anio >= 2024
    GROUP BY m.maquina_nk, t.turno_nk
    HAVING SUM(b.minutos_planificados) >= 60 * 100  -- al menos 100 horas, para que la cifra signifique algo
),
kpi AS (
    SELECT maquina, turno, op / 60 AS horas_operativas,
           op / NULLIF(pl, 0) AS disponibilidad,
           up / NULLIF(ut, 0) AS rendimiento,
           op / NULLIF(pl, 0) * up / NULLIF(ut, 0) AS oee
    FROM por_turno
)
SELECT maquina,
       turno,
       ROUND(horas_operativas)        AS horas_operativas,
       ROUND(100 * disponibilidad, 1) AS disponibilidad_pct,
       ROUND(100 * rendimiento, 1)    AS rendimiento_pct,
       ROUND(100 * oee, 1)            AS oee_pct,
       RANK() OVER (PARTITION BY maquina ORDER BY oee DESC NULLS LAST) AS puesto_en_la_maquina,
       ROUND(100 * (oee - FIRST_VALUE(oee) OVER (PARTITION BY maquina ORDER BY oee DESC NULLS LAST)), 1) AS brecha_con_el_mejor_puntos
FROM kpi
ORDER BY maquina, puesto_en_la_maquina;
