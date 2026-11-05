-- Permisos de solo lectura para el rol bi_lector, que usan Grafana y Power BI.
-- El ETL recrea los esquemas dw y audit en cada ejecucion, asi que los permisos se vuelven a
-- conceder aqui. El rol lo crea db/init/01_roles.sh; si no existe (volumen anterior), se omite.
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'bi_lector') THEN
        GRANT USAGE ON SCHEMA dw, audit TO bi_lector;
        GRANT SELECT ON ALL TABLES IN SCHEMA dw, audit TO bi_lector;
    END IF;
END
$$;
