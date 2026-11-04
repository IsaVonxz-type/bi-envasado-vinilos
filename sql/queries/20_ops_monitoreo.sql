-- 20 · Consultas sobre el monitoreo en vivo (esquema ops)
-- Para ejecutar con el simulador en marcha. Son las mismas ideas que usa el tablero de Grafana.

-- (a) Estado actual por máquina: últimas 4 lecturas, sumando antes de dividir.
SELECT maquina,
       ultima_lectura,
       ROUND(100 * disponibilidad_4h, 1) AS disponibilidad_4h_pct,
       ROUND(100 * rendimiento_4h, 1)    AS rendimiento_4h_pct,
       ROUND(100 * oee_4h, 1)            AS oee_4h_pct,
       minutos_no_programados_4h
FROM ops.vw_estado_actual
ORDER BY maquina;

-- (b) Evolución de la disponibilidad móvil de 4 lecturas, con función de ventana.
SELECT maquina,
       ts,
       hora_simulada,
       ROUND(100 * disponibilidad, 1) AS disponibilidad_pct,
       ROUND(100 * SUM(minutos_operativos) OVER w / NULLIF(SUM(minutos_planificados) OVER w, 0), 1) AS disponibilidad_movil_4h_pct
FROM ops.vw_lectura_hora
WHERE ts > now() - interval '10 minutes'
WINDOW w AS (PARTITION BY maquina ORDER BY ts ROWS BETWEEN 3 PRECEDING AND CURRENT ROW)
ORDER BY maquina, ts DESC
LIMIT 40;

-- (c) Causas de paro de la última hora real, con su participación.
SELECT causa,
       clasificacion,
       ROUND(SUM(minutos), 1) AS minutos,
       ROUND(100 * SUM(minutos) / SUM(SUM(minutos)) OVER (), 1) AS pct
FROM ops.paro_hora
WHERE ts > now() - interval '1 hour'
GROUP BY causa, clasificacion
ORDER BY minutos DESC;

-- (d) Alertas que Grafana entregó al webhook.
SELECT recibido_en, estado, regla, maquina, valor, severidad, resumen
FROM ops.alerta_recibida
ORDER BY recibido_en DESC
LIMIT 20;
