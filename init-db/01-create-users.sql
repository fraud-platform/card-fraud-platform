-- =============================================================================
-- Card Fraud Platform - PostgreSQL Initialization
-- =============================================================================
-- This script runs automatically on FIRST PostgreSQL start only.
-- It creates application users for the shared fraud_gov database.
--
-- Users:
--   fraud_gov_app_user      - Used by rule-management and transaction-management
--   fraud_gov_analytics_user - Read-only, used by intelligence-portal and analytics
--
-- The fraud_gov database is created by POSTGRES_DB environment variable.
-- Schema migrations are managed by each application (Alembic, etc.).
-- =============================================================================

\getenv FRAUD_GOV_APP_PASSWORD FRAUD_GOV_APP_PASSWORD
\if :{?FRAUD_GOV_APP_PASSWORD}
\else
\set FRAUD_GOV_APP_PASSWORD localdevpass
\endif

\getenv FRAUD_GOV_ANALYTICS_PASSWORD FRAUD_GOV_ANALYTICS_PASSWORD
\if :{?FRAUD_GOV_ANALYTICS_PASSWORD}
\else
\set FRAUD_GOV_ANALYTICS_PASSWORD localdevpass
\endif

-- Application user (read/write)
SELECT format(
    'CREATE ROLE fraud_gov_app_user WITH LOGIN PASSWORD %L',
    :'FRAUD_GOV_APP_PASSWORD'
)
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fraud_gov_app_user')
\gexec

SELECT format(
    'ALTER ROLE fraud_gov_app_user WITH PASSWORD %L',
    :'FRAUD_GOV_APP_PASSWORD'
)
WHERE EXISTS (SELECT FROM pg_roles WHERE rolname = 'fraud_gov_app_user')
\gexec

-- Analytics user (read-only)
SELECT format(
    'CREATE ROLE fraud_gov_analytics_user WITH LOGIN PASSWORD %L',
    :'FRAUD_GOV_ANALYTICS_PASSWORD'
)
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'fraud_gov_analytics_user')
\gexec

SELECT format(
    'ALTER ROLE fraud_gov_analytics_user WITH PASSWORD %L',
    :'FRAUD_GOV_ANALYTICS_PASSWORD'
)
WHERE EXISTS (SELECT FROM pg_roles WHERE rolname = 'fraud_gov_analytics_user')
\gexec

-- Grant privileges on the fraud_gov database
GRANT ALL PRIVILEGES ON DATABASE fraud_gov TO fraud_gov_app_user;
GRANT CONNECT ON DATABASE fraud_gov TO fraud_gov_analytics_user;

-- Grant schema-level privileges (for tables created later by migrations)
GRANT ALL ON SCHEMA public TO fraud_gov_app_user;
GRANT USAGE ON SCHEMA public TO fraud_gov_analytics_user;

-- Set default privileges so future tables are accessible
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO fraud_gov_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO fraud_gov_analytics_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO fraud_gov_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO fraud_gov_analytics_user;
