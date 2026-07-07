# Architecture

## System Overview

The Delhi Metro Digital Twin is a production-grade real-time simulation and operations platform modeled on the entire Delhi Metro network. It comprises five main layers:

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (Web)                        │
│  Next.js 15 · React 19 · MapLibre GL · Deck.gl          │
│  Zustand · React Query · Recharts · Framer Motion        │
│  Tailwind CSS · TypeScript                               │
├──────────────────────────────────────────────────────────┤
│                    API (Backend)                          │
│  FastAPI · Python 3.12 · Pydantic v2 · WebSocket         │
│  SQLAlchemy 2.x · Alembic · Prometheus · SlowAPI         │
├──────────────────────────────────────────────────────────┤
│               Simulation Engine                           │
│  Pure Python async loop · Fixed-timestep physics          │
│  CBTC/ATO signalling · Passenger flow · Incident mgmt    │
├──────────────────────────────────────────────────────────┤
│              Data Layer                                   │
│  PostgreSQL 16 + PostGIS · Redis · RabbitMQ              │
│  GeoJSON/network dataset · Alembic migrations             │
├──────────────────────────────────────────────────────────┤
│              GIS Layer                                    │
│  shapely · pyproj · GeoJSON · PostGIS · network.json     │
│  Track geometry · Station polygons · Platform alignment  │
└──────────────────────────────────────────────────────────┘
```

## Directory Structure

```
delhi-metro-digital-twin/
├── backend/        # FastAPI REST + WebSocket API
├── simulation/     # Physics/signalling/passenger engine
├── database/       # SQLAlchemy models + Alembic migrations
├── gis/            # GIS geometry + network data + validation
├── web/            # Next.js control center UI
├── docker/         # Dockerfiles + docker-compose.yml
├── configs/        # Environment config files
├── scripts/        # Operational scripts
├── docs/           # Documentation
├── tests/          # Cross-cutting E2E/integration/load tests
└── assets/         # Icons, sprites, audio, basemap
```

## Data Flow

### Real-Time Simulation
1. Simulation engine runs in a fixed-timestep loop (dt=1s)
2. State snapshots publish to RabbitMQ every 30s
3. Backend WebSocket server pushes train positions to frontend every 2s
4. MapLibre + Deck.gl renders animated trains and station markers

### REST API
1. Frontend queries backend via REST endpoints (React Query with 10s stale time)
2. Backend reads from PostgreSQL via async SQLAlchemy sessions
3. Repository pattern separates data access from business logic
4. All responses are Pydantic-validated

### AI Predictions
1. Training pipeline generates synthetic data and trains sklearn models
2. Models saved as joblib files with JSON metadata
3. InferenceEngine loads all models at startup
4. ControlRoomAssistant provides natural-language query interface
