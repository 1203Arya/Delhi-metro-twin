# Delhi Metro Digital Twin

A production-grade real-time digital twin and simulation platform for the Delhi Metro network, modeled to the engineering standards of Siemens Mobility, Alstom, Hitachi Rail, and the Delhi Metro Rail Corporation (DMRC).

> **Status:** Active development. This is a full-stack, deployable system — not a demo or MVP.

---

## What this is

A digital twin is a live virtual representation of a physical system, kept in sync with it and able to simulate its future. This project models the **entire operational Delhi Metro network** (Red, Yellow, Blue, Blue Branch, Green, Green Branch, Violet, Pink, Magenta, Grey, Orange Airport Express, Rapid Metro), its trains, signalling, passengers, and depots — then renders it on a 60 FPS map with a control-room dashboard.

It is built to:

1. **Simulate** train physics, signalling (CBTC/ATP/ATO), timetables, and passenger flow as independent agents.
2. **Visualize** live position, speed, crowd, occupancy, and ETA in real time.
3. **Predict** delays, demand, crowds, ETAs, and incidents with ML models.
4. **Control** via dashboards and a natural-language control-room assistant.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind, MapLibre GL + Deck.gl, React Query, Zustand, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.x, Alembic, Pydantic v2, asyncio, WebSockets |
| Simulation Engine | Pure Python (async event loop, fixed-timestep physics) |
| GIS | PostGIS, MapLibre (XYZ/vector tiles) |
| Database | PostgreSQL 16 |
| Cache | Redis |
| Messaging | RabbitMQ |
| Deployment | Docker, Docker Compose |
| CI | GitHub Actions |
| Testing | pytest, Playwright, Vitest |

---

## Repository layout

```
delhi-metro-digital-twin/
├── frontend/      # Next.js control center + map
├── backend/       # FastAPI REST + WebSocket services
├── simulation/    # Pure-Python physics + signalling + passengers
├── gis/           # GeoJSON, PostGIS layers, geometry tooling
├── database/      # Schema, Alembic migrations, seed data
├── docker/        # Service Dockerfiles + compose
├── docs/          # Architecture, API, simulation, DB guides
├── scripts/       # Operational + dev scripts
├── assets/        # Station icons, sprites, basemap resources
├── configs/       # Env configs for each environment
├── tests/         # Cross-cutting + load tests
└── .github/       # CI workflows
```

Each top-level directory has its own README explaining its contents.

---

## Quick start

The fastest path to a running system:

```bash
# 1. Copy environment defaults
cp configs/dev.env.example configs/dev.env
#    (edit secrets — see docs/deployment.md)

# 2. Boot the full stack (Postgres+PostGIS, Redis, RabbitMQ, backend, sim, frontend)
docker compose -f docker/docker-compose.yml --env-file configs/dev.env up --build

# 3. Apply migrations + seed the network
docker compose -f docker/docker-compose.yml exec backend alembic upgrade head
docker compose -f docker/docker-compose.yml exec backend python scripts/seed_network.py

# 4. Open the control center
#    Frontend → http://localhost:3000
#    API      → http://localhost:8000/docs
```

See `docs/quickstart.md` for the guided walkthrough.

---

## Documentation

- [Architecture](docs/architecture.md) — system design, data flow, domain model
- [Quick start](docs/quickstart.md) — first-run guide
- [API reference](docs/api.md) — REST + WebSocket contracts
- [Simulation guide](docs/simulation.md) — physics, signalling, scheduling
- [Database guide](docs/database.md) — schema, migrations, spatial indexes
- [GIS guide](docs/gis.md) — coordinate systems, track geometry, tile pipeline
- [Deployment guide](docs/deployment.md) — environments, secrets, scaling
- [Developer guide](docs/developer.md) — local setup, conventions, contributing
- [Control center](docs/control-center.md) — dashboard reference

---

## Engineering principles

- **No mocks in the critical path.** The simulation engine runs the same physics the operator sees.
- **Everything must compile and run.** No TODOs, no placeholder stubs, no "implement later."
- **Tests are part of the build.** Unit, integration, simulation, and load tests run in CI.
- **Reproducibility.** Pinned dependencies, deterministic random seeds, versioned migrations.
- **Operational realism.** Every line, station, platform, depot, siding, crossover, and junction in the operational network is modeled.

---

## License

Proprietary — built for DMRC-style deployment. See `LICENSE`.
