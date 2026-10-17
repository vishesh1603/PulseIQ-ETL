-- PulseIQ Analytics Warehouse: Read-only user for Apache Superset.
-- Superset connects using this role so that it can only read from schema dw,
-- and can never modify or delete warehouse data.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'superset_ro') THEN
        CREATE ROLE superset_ro WITH LOGIN PASSWORD 'superset_ro_pass';
    ELSE
        ALTER ROLE superset_ro WITH PASSWORD 'superset_ro_pass';
    END IF;
END
$$;

-- Grant connection to database
GRANT CONNECT ON DATABASE pulseiq TO superset_ro;

-- Restrict schema access strictly to schema "dw"
GRANT USAGE ON SCHEMA dw TO superset_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA dw TO superset_ro;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA dw TO superset_ro;

-- Ensure any future tables/views in dw are also readable by superset_ro
ALTER DEFAULT PRIVILEGES IN SCHEMA dw GRANT SELECT ON TABLES TO superset_ro;
