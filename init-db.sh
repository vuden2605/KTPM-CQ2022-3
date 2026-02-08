#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOSQL
    -- Create databases
    CREATE DATABASE authdb;
    CREATE DATABASE paymentdb;
    CREATE DATABASE marketdb;

    -- Grant privileges
    GRANT ALL PRIVILEGES ON DATABASE authdb TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE paymentdb TO postgres;
    GRANT ALL PRIVILEGES ON DATABASE marketdb TO postgres;

    -- Connect and create schemas if needed
    \c authdb
    CREATE SCHEMA IF NOT EXISTS public;

    \c paymentdb
    CREATE SCHEMA IF NOT EXISTS public;

    \c marketdb
    CREATE SCHEMA IF NOT EXISTS public;
EOSQL

echo "✅ Databases created: authdb, paymentdb, marketdb"