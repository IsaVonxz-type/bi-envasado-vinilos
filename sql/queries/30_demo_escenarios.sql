-- 30 · Guion de la demostración en vivo
-- Ejecute las sentencias de una en una desde DBeaver mientras el tablero de Grafana está abierto.
-- El simulador lee ops.escenario en cada lectura, así que el cambio se nota en la siguiente (unos 15 s).

-- 1. Estado inicial: todas las líneas en operación normal.
SELECT maquina, modo, actualizado_en FROM ops.escenario ORDER BY maquina;

-- 2. Provocar una falla en Vinilos_2. La disponibilidad cae, la regla "Disponibilidad baja" pasa a
--    Pending y luego a Firing, y llega el aviso al webhook.
UPDATE ops.escenario SET modo = 'falla', actualizado_en = now() WHERE maquina = 'Vinilos_2';

-- 3. Degradar Vinilos_4: más paros pequeños y menor rendimiento, sin una falla franca.
UPDATE ops.escenario SET modo = 'degradado', actualizado_en = now() WHERE maquina = 'Vinilos_4';

-- 4. Reparar: todas vuelven a operación normal. La alerta pasa a Normal y se registra como resuelta.
UPDATE ops.escenario SET modo = 'normal', actualizado_en = now();

-- 5. Comprobar las alertas recibidas.
SELECT recibido_en, estado, regla, maquina, valor FROM ops.alerta_recibida ORDER BY recibido_en DESC LIMIT 10;
