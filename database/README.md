# dmdt-database

The database layer of the Delhi Metro Digital Twin: a fully-normalised
PostgreSQL 16 + PostGIS schema, owned by SQLAlchemy 2.x declarative models and
managed with Alembic migrations. Seed loaders populate the schema from the
canonical GIS dataset (`gis/data/network.json`).

## Layout

| Path | Purpose |
|---|---|
| `database/dmdt_db/__init__.py` | Package root. |
| `database/dmdt_db/base.py` | Declarative `Base`, naming convention, shared mixins (`UUIDPK`, `Timestamps`). |
| `database/dmdt_db/types.py` | Custom SQLAlchemy/GeoAlchemy2 types (geography point/line/polygon, line code enum). |
| `database/dmdt_db/enums.py` | Domain enums: line codes, structure class, signalling system, depot role, etc. |
| `database/dmdt_db/models/` | One module per entity: `line.py`, `station.py`, `platform.py`, `track_segment.py`, `crossover.py`, `junction.py`, `switch.py`, `depot.py`, `siding.py`, `train_class.py`. |
| `database/dmdt_db/models/__init__.py` | Re-exports every model for Alembic autogenerate + imports. |
| `database/alembic.ini` | Alembic configuration. |
| `database/migrations/env.py` | Alembic environment: imports metadata, runs migrations offline + online against PostGIS. |
| `database/migrations/versions/0001_initial_schema.py` | Hand-authored base migration creating every table, constraint, FK and spatial index. |
| `database/seed/load_network.py` | Loads `gis/data/network.json` into the schema (idempotent). |
| `database/seed/seed_network.py` | Entry point invoked by `scripts/seed_network.py` / the Makefile `seed` target. |

## Conventions

- All primary keys are UUID (`gen_random_uuid()`).
- Every spatial column is `GEOGRAPHY(geometry, 4326)` (spherical, metre units) for
  distance queries, with a matching `GEOMETRY(geometry, 4326)` column
  used by the GIST index and planar `ST_` analysis. This dual-column pattern is
  the same one DMRC-style control rooms use to get both "distance true to the
  globe" queries and fast tiled rendering.
- Tables use singular names. Foreign keys are `ON DELETE RESTRICT` for entities
  that must never lose their parent (a station cannot outlive its line); a few
  audit/relation tables use `ON DELETE CASCADE`.
- Spatial indexes are `CREATE INDEX ... USING GIST (geom)`.
- B-tree indexes on every FK column and on lookup columns (`line_code`,
  `station_code`, `name_trgm` with a trigram GIN index for fuzzy station search).

## Apply + seed

```bash
# From repo root, with the stack running:
make migrate
make seed
# Or standalone, pointing at any PostGIS 16 instance:
DATABASE_URL=postgresql://dmdt:dmdt@localhost:5432/dmdt \
  alembic -c database/alembic.ini upgrade head
python -m dmdt_db.seed.seed_network  # or scripts/seed_network.py
```
