-- archivo: database/sql/01_create_database.sql
-- Ejecutar conectado a la base de mantenimiento (ej. postgres)
SELECT 'CREATE DATABASE siged_pnp'
WHERE NOT EXISTS (
    SELECT 1
    FROM pg_database
    WHERE datname = 'siged_pnp'
)\gexec
