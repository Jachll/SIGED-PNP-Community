-- archivo: database/sql/02_enable_postgis.sql
\connect siged_pnp;

CREATE EXTENSION IF NOT EXISTS postgis;
