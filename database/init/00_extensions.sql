-- ─────────────────────────────────────────────────────────────
-- Delhi Metro Digital Twin — Postgres bootstrap
-- Loaded automatically on first container start (docker-entrypoint-initdb.d).
-- Enables required extensions. Schema creation is handled by Alembic.
-- ─────────────────────────────────────────────────────────────

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_topology;
CREATE EXTENSION IF NOT EXISTS pgcrypto;        -- gen_random_uuid(), cryptographic randomness
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;      -- composite unique btree+gist constraints
CREATE EXTENSION IF NOT EXISTS pg_trgm;          -- fuzzy text search for station names
