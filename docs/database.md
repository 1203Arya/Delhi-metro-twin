# Database Documentation

## Technology

- **PostgreSQL 16** with **PostGIS 3.4** extension
- **SQLAlchemy 2.x** async ORM via `asyncpg`
- **Alembic** for schema migrations
- **GeoAlchemy2** for spatial column support

## Connection

Default connection string:
`postgresql+asyncpg://dmdt:change-me-in-dev@postgres:5432/dmdt`

Configurable via `DATABASE_URL` environment variable.

## Entity-Relationship Diagram

```
Line 1──* Station 1──* Platform
  │         │
  │         ├──* TrackSegment
  │         │
  │         └──* Junction 1──* Switch
  │
  ├──* Depot 1──* Siding
  │
  └──* Crossover
```

## Entities

### Line
| Column | Type | Notes |
|---|---|---|
| `code` | VARCHAR(10) PK | e.g., `RD`, `YL`, `BL` |
| `name` | VARCHAR(100) | e.g., "Red Line" |
| `number` | INTEGER | 1-based |
| `color_hex` | VARCHAR(7) | `#FF0000` |
| `corridor` | VARCHAR(200) | Terminal stations |
| `total_length_km` | FLOAT | |
| `station_count` | INTEGER | |

### Station
| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | gen_random_uuid() |
| `code` | VARCHAR(10) | e.g., `DIL` |
| `line_code` | VARCHAR(10) FK → Line | |
| `sequence` | INTEGER | Order on line |
| `latitude` / `longitude` | FLOAT | WGS84 |
| `location` | GEOGRAPHY(Point, 4326) | PostGIS |
| `is_terminus` | BOOLEAN | |
| `structure` | ENUM | `elevated`, `underground`, `at_grade` |

### TrackSegment
- LINESTRING geometry between stations
- Speed limits, curvature, gradient metadata
- Bidirectional (one record per direction per track)

### Platform
- Linked to station, has precise geometry
- Heading, length, width for passenger modeling

### Depot
- Stabling and maintenance facility
- Linked to a line, contains sidings

### TrainClass
- Rolling stock characteristics (speed, acceleration, capacity)

## Conventions

- All PKs use UUID v4 (`gen_random_uuid()`)
- Singular table names
- `ON DELETE RESTRICT` for core entities
- GIST indexes on geometry columns
- B-tree indexes on foreign keys
- GIN trigram index for station name search
- `created_at` / `updated_at` timestamps on all entities
