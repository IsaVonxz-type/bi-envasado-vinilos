DROP SCHEMA IF EXISTS dw CASCADE;
DROP SCHEMA IF EXISTS audit CASCADE;
CREATE SCHEMA dw;
CREATE SCHEMA audit;

CREATE TABLE dw.dim_fecha (
    fecha_key      INTEGER PRIMARY KEY,
    fecha          DATE NOT NULL UNIQUE,
    anio           SMALLINT NOT NULL,
    semestre       SMALLINT NOT NULL CHECK (semestre BETWEEN 1 AND 2),
    trimestre      SMALLINT NOT NULL CHECK (trimestre BETWEEN 1 AND 4),
    mes            SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    nombre_mes     VARCHAR(12) NOT NULL,
    anio_mes       CHAR(7) NOT NULL,
    semana_iso     SMALLINT NOT NULL,
    dia_semana     SMALLINT NOT NULL CHECK (dia_semana BETWEEN 1 AND 7),
    nombre_dia     VARCHAR(10) NOT NULL,
    es_fin_semana  BOOLEAN NOT NULL
);

CREATE TABLE dw.dim_maquina (
    maquina_key  SMALLINT PRIMARY KEY,
    maquina_nk   VARCHAR(20) NOT NULL UNIQUE,
    numero_linea SMALLINT NOT NULL UNIQUE
);

CREATE TABLE dw.dim_turno (
    turno_key        SMALLINT PRIMARY KEY,
    turno_nk         VARCHAR(30) NOT NULL UNIQUE,
    esquema          VARCHAR(20) NOT NULL,
    hora_inicio      TIME,
    hora_fin         TIME,
    horas_nominales  NUMERIC(4,1)
);

CREATE TABLE dw.dim_referencia (
    referencia_key  INTEGER PRIMARY KEY,
    referencia_nk   VARCHAR(60) NOT NULL UNIQUE,
    familia         VARCHAR(40) NOT NULL,
    volumen_cc      SMALLINT,
    colores         SMALLINT
);

CREATE TABLE dw.dim_persona (
    persona_key  INTEGER PRIMARY KEY,
    seudonimo    VARCHAR(20) NOT NULL UNIQUE,
    rol          VARCHAR(20) NOT NULL
);

CREATE TABLE dw.dim_causa_paro (
    causa_key           INTEGER PRIMARY KEY,
    causa_nk            VARCHAR(20) NOT NULL UNIQUE,
    codigo              SMALLINT NOT NULL CHECK (codigo BETWEEN 1 AND 18),
    codigo_nombre       VARCHAR(90) NOT NULL,
    area_impacto        VARCHAR(40) NOT NULL,
    clasificacion_oee   VARCHAR(15) NOT NULL CHECK (clasificacion_oee IN ('Programado', 'No programado')),
    es_falla            BOOLEAN NOT NULL,
    sistema             VARCHAR(70) NOT NULL,
    subcodigo           VARCHAR(70) NOT NULL
);

CREATE TABLE dw.dim_motivo_no_operacion (
    motivo_key  INTEGER PRIMARY KEY,
    tipo        VARCHAR(50) NOT NULL,
    categoria   VARCHAR(20) NOT NULL,
    motivo      VARCHAR(70) NOT NULL,
    UNIQUE (tipo, motivo)
);

CREATE TABLE dw.dim_estandar_produccion (
    estandar_key         INTEGER PRIMARY KEY,
    maquina_key          SMALLINT NOT NULL REFERENCES dw.dim_maquina,
    referencia_key       INTEGER NOT NULL REFERENCES dw.dim_referencia,
    unidades_por_paca    INTEGER NOT NULL CHECK (unidades_por_paca > 0),
    unidades_por_minuto  NUMERIC(6,1) NOT NULL CHECK (unidades_por_minuto > 0),
    origen               VARCHAR(15) NOT NULL CHECK (origen IN ('catalogo', 'inferido')),
    valido_desde         DATE NOT NULL,
    valido_hasta         DATE NOT NULL,
    es_vigente           BOOLEAN NOT NULL,
    CHECK (valido_desde <= valido_hasta),
    UNIQUE (maquina_key, referencia_key, valido_desde)
);

CREATE TABLE dw.fact_produccion (
    produccion_key         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fila_origen            INTEGER NOT NULL UNIQUE,
    fecha_key              INTEGER NOT NULL REFERENCES dw.dim_fecha,
    maquina_key            SMALLINT NOT NULL REFERENCES dw.dim_maquina,
    turno_key              SMALLINT NOT NULL REFERENCES dw.dim_turno,
    referencia_key         INTEGER NOT NULL REFERENCES dw.dim_referencia,
    operario_key           INTEGER NOT NULL REFERENCES dw.dim_persona,
    estandar_key           INTEGER REFERENCES dw.dim_estandar_produccion,
    pacas_reportadas       NUMERIC(10,2) CHECK (pacas_reportadas >= 0),
    pacas_validas          NUMERIC(10,2) CHECK (pacas_validas >= 0),
    unidades_producidas    NUMERIC(14,2) CHECK (unidades_producidas >= 0),
    horas_trabajadas       NUMERIC(6,2) CHECK (horas_trabajadas >= 0),
    alerta_pacas_atipicas  BOOLEAN NOT NULL DEFAULT FALSE,
    alerta_paro_excede     BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE dw.fact_paro (
    paro_key                BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fila_origen             INTEGER NOT NULL,
    fecha_key               INTEGER NOT NULL REFERENCES dw.dim_fecha,
    maquina_key             SMALLINT NOT NULL REFERENCES dw.dim_maquina,
    turno_key               SMALLINT NOT NULL REFERENCES dw.dim_turno,
    referencia_key          INTEGER NOT NULL REFERENCES dw.dim_referencia,
    operario_key            INTEGER NOT NULL REFERENCES dw.dim_persona,
    causa_key               INTEGER NOT NULL REFERENCES dw.dim_causa_paro,
    persona_involucrada_key INTEGER NOT NULL REFERENCES dw.dim_persona,
    area_involucrada        VARCHAR(30),
    minutos_paro            NUMERIC(8,2) NOT NULL CHECK (minutos_paro > 0),
    UNIQUE (fila_origen, causa_key)
);

CREATE TABLE dw.fact_no_operacion (
    no_operacion_key   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    fecha_key          INTEGER NOT NULL REFERENCES dw.dim_fecha,
    maquina_key        SMALLINT NOT NULL REFERENCES dw.dim_maquina,
    motivo_key         INTEGER NOT NULL REFERENCES dw.dim_motivo_no_operacion,
    filas_origen       SMALLINT NOT NULL CHECK (filas_origen > 0),
    horas_reportadas   NUMERIC(8,2) NOT NULL CHECK (horas_reportadas > 0),
    horas_ajustadas    NUMERIC(8,2) NOT NULL CHECK (horas_ajustadas >= 0),
    UNIQUE (fecha_key, maquina_key, motivo_key),
    CHECK (horas_ajustadas <= horas_reportadas)
);

CREATE INDEX ix_produccion_fecha_maquina ON dw.fact_produccion (fecha_key, maquina_key);
CREATE INDEX ix_produccion_maquina_turno ON dw.fact_produccion (maquina_key, turno_key);
CREATE INDEX ix_produccion_referencia ON dw.fact_produccion (referencia_key);
CREATE INDEX ix_produccion_operario ON dw.fact_produccion (operario_key);
CREATE INDEX ix_paro_fecha_maquina ON dw.fact_paro (fecha_key, maquina_key);
CREATE INDEX ix_paro_causa_fecha ON dw.fact_paro (causa_key, fecha_key);
CREATE INDEX ix_paro_grupo_oee ON dw.fact_paro (fecha_key, maquina_key, turno_key, referencia_key);
CREATE INDEX ix_no_operacion_motivo ON dw.fact_no_operacion (motivo_key);
CREATE INDEX ix_causa_jerarquia ON dw.dim_causa_paro (codigo, sistema, subcodigo);

CREATE TABLE audit.etl_ejecucion (
    ejecucion_id    INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    inicio          TIMESTAMPTZ NOT NULL,
    fin             TIMESTAMPTZ NOT NULL,
    archivo_sha256  CHAR(64) NOT NULL,
    filas_fuente    INTEGER NOT NULL
);

CREATE TABLE audit.calidad_datos (
    regla        VARCHAR(10) PRIMARY KEY,
    descripcion  TEXT NOT NULL,
    tratamiento  TEXT NOT NULL,
    afectados    INTEGER NOT NULL CHECK (afectados >= 0),
    unidad       VARCHAR(20) NOT NULL
);

CREATE TABLE audit.conteo_filas (
    orden      SMALLINT PRIMARY KEY,
    etapa      TEXT NOT NULL,
    filas      INTEGER NOT NULL CHECK (filas >= 0)
);

CREATE TABLE audit.cuadre_cifras (
    metrica      VARCHAR(30) PRIMARY KEY,
    unidad       VARCHAR(10) NOT NULL,
    fuente       NUMERIC(14,2) NOT NULL,
    excluido     NUMERIC(14,2) NOT NULL,
    esperado     NUMERIC(14,2) NOT NULL,
    cargado      NUMERIC(14,2) NOT NULL,
    diferencia   NUMERIC(14,2) NOT NULL,
    cuadra       BOOLEAN NOT NULL,
    explicacion  TEXT NOT NULL
);
