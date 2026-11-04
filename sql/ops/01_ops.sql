-- Esquema operativo: lecturas hora a hora que alimentan el tablero de Grafana.
--
-- Es independiente de dw y audit. El ETL elimina y recrea esos dos esquemas en cada
-- ejecucion, y esto debe sobrevivir. Por eso no hay llaves foraneas hacia dw: las
-- lecturas guardan el nombre de la maquina, el turno y la referencia como texto.
-- Todas las sentencias son idempotentes: el simulador las aplica al iniciar.

CREATE SCHEMA IF NOT EXISTS ops;

-- Panel de control de la simulacion: permite provocar una falla durante la demostracion
-- con un UPDATE desde DBeaver, sin reiniciar nada.
CREATE TABLE IF NOT EXISTS ops.escenario (
    maquina         VARCHAR(20) PRIMARY KEY,
    modo            VARCHAR(10) NOT NULL DEFAULT 'normal' CHECK (modo IN ('normal', 'degradado', 'falla')),
    actualizado_en  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Una lectura por maquina y hora de produccion simulada.
-- Grano: una maquina durante una hora. Las medidas son aditivas (minutos y unidades);
-- los porcentajes se calculan al agregar, igual que en el modelo dimensional.
CREATE TABLE IF NOT EXISTS ops.lectura_hora (
    lectura_id            BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    ts                    TIMESTAMPTZ NOT NULL DEFAULT now(),
    hora_simulada         TIMESTAMP NOT NULL,
    maquina               VARCHAR(20) NOT NULL,
    turno                 VARCHAR(30) NOT NULL,
    referencia            VARCHAR(60) NOT NULL,
    escenario             VARCHAR(10) NOT NULL CHECK (escenario IN ('normal', 'degradado', 'falla')),
    minutos_programados   NUMERIC(6,2) NOT NULL CHECK (minutos_programados BETWEEN 0 AND 60),
    minutos_planificados  NUMERIC(6,2) NOT NULL CHECK (minutos_planificados BETWEEN 0 AND 60),
    minutos_no_programados NUMERIC(6,2) NOT NULL CHECK (minutos_no_programados >= 0),
    minutos_operativos    NUMERIC(6,2) NOT NULL CHECK (minutos_operativos >= 0),
    unidades_teoricas     NUMERIC(12,2) NOT NULL CHECK (unidades_teoricas >= 0),
    unidades_producidas   NUMERIC(12,2) NOT NULL CHECK (unidades_producidas >= 0),
    UNIQUE (maquina, hora_simulada),
    CHECK (minutos_programados + minutos_planificados = 60),
    CHECK (minutos_operativos = GREATEST(minutos_planificados - minutos_no_programados, 0))
);

-- Un paro dentro de una lectura, con su causa. Mismo catalogo de codigos que dim_causa_paro.
CREATE TABLE IF NOT EXISTS ops.paro_hora (
    paro_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    lectura_id     BIGINT NOT NULL REFERENCES ops.lectura_hora ON DELETE CASCADE,
    ts             TIMESTAMPTZ NOT NULL,
    maquina        VARCHAR(20) NOT NULL,
    codigo         SMALLINT NOT NULL CHECK (codigo BETWEEN 1 AND 18),
    causa          VARCHAR(90) NOT NULL,
    sistema        VARCHAR(70) NOT NULL,
    subcodigo      VARCHAR(70) NOT NULL,
    clasificacion  VARCHAR(15) NOT NULL CHECK (clasificacion IN ('Programado', 'No programado')),
    es_falla       BOOLEAN NOT NULL,
    minutos        NUMERIC(6,2) NOT NULL CHECK (minutos > 0)
);

-- Alertas que Grafana entrega por webhook al simulador: deja constancia de que la
-- alerta se disparo y se resolvio, sin depender de correo ni de servicios externos.
CREATE TABLE IF NOT EXISTS ops.alerta_recibida (
    alerta_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    recibido_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
    estado       VARCHAR(10) NOT NULL CHECK (estado IN ('firing', 'resolved')),
    regla        VARCHAR(120) NOT NULL,
    maquina      VARCHAR(20),
    valor        NUMERIC(12,2),
    severidad    VARCHAR(20),
    resumen      TEXT
);

-- Consultas frecuentes: ventana reciente por maquina (tableros y alertas) y purga por antiguedad.
CREATE INDEX IF NOT EXISTS ix_lectura_maquina_ts ON ops.lectura_hora (maquina, ts DESC);
CREATE INDEX IF NOT EXISTS ix_lectura_ts ON ops.lectura_hora (ts);
CREATE INDEX IF NOT EXISTS ix_paro_maquina_ts ON ops.paro_hora (maquina, ts DESC);
CREATE INDEX IF NOT EXISTS ix_paro_lectura ON ops.paro_hora (lectura_id);
CREATE INDEX IF NOT EXISTS ix_alerta_recibida_en ON ops.alerta_recibida (recibido_en DESC);

-- Indicadores por lectura. Para ventanas mayores, sumar primero y dividir despues.
CREATE OR REPLACE VIEW ops.vw_lectura_hora AS
SELECT l.*,
       l.minutos_operativos / NULLIF(l.minutos_planificados, 0) AS disponibilidad,
       l.unidades_producidas / NULLIF(l.unidades_teoricas, 0) AS rendimiento,
       l.minutos_operativos / NULLIF(l.minutos_planificados, 0)
         * l.unidades_producidas / NULLIF(l.unidades_teoricas, 0) AS oee
FROM ops.lectura_hora l;

-- Estado actual por maquina: ultimas 4 lecturas (4 horas de produccion), agregadas con
-- suma antes de division. Es la base del panel de estado y de la regla de alerta.
CREATE OR REPLACE VIEW ops.vw_estado_actual AS
WITH ordenadas AS (
    SELECT l.*, ROW_NUMBER() OVER (PARTITION BY maquina ORDER BY ts DESC, lectura_id DESC) AS posicion
    FROM ops.lectura_hora l
)
SELECT maquina,
       MAX(ts) AS ultima_lectura,
       COUNT(*) AS lecturas,
       SUM(minutos_operativos) / NULLIF(SUM(minutos_planificados), 0) AS disponibilidad_4h,
       SUM(unidades_producidas) / NULLIF(SUM(unidades_teoricas), 0) AS rendimiento_4h,
       SUM(minutos_operativos) / NULLIF(SUM(minutos_planificados), 0)
         * SUM(unidades_producidas) / NULLIF(SUM(unidades_teoricas), 0) AS oee_4h,
       SUM(minutos_no_programados) AS minutos_no_programados_4h
FROM ordenadas
WHERE posicion <= 4
GROUP BY maquina;
