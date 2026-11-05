#!/bin/sh
# Se ejecuta una sola vez, cuando PostgreSQL crea el volumen de datos por primera vez.
# Crea el usuario de solo lectura que usan Grafana y Power BI, para que ningun tablero
# se conecte con el usuario administrador. Si cambia la clave, recree el volumen
# (docker compose down -v) o use ALTER ROLE bi_lector PASSWORD '...' desde DBeaver.
if [ -z "$BI_READER_PASSWORD" ]; then
    echo "ERROR: defina BI_READER_PASSWORD en .env" >&2
    exit 1
fi
psql -v ON_ERROR_STOP=1 -v lector_clave="$BI_READER_PASSWORD" --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
CREATE ROLE bi_lector LOGIN PASSWORD :'lector_clave' NOSUPERUSER NOCREATEDB NOCREATEROLE;
ALTER ROLE bi_lector SET default_transaction_read_only = on;
ALTER ROLE bi_lector SET statement_timeout = '30s';
SQL
