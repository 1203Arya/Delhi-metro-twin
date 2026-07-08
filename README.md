# Delhi Metro Digital Twin

**Production-grade real-time digital twin and simulation platform for the Delhi Metro network.**

[![CI](https://github.com/your-org/delhi-metro-digital-twin/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/delhi-metro-digital-twin/actions/workflows/ci.yml)

---

## Overview

Models the entire operational Delhi Metro network — 12 lines, ~220 stations, all rolling stock — with real-time physics simulation, CBTC/ATP/ATO signalling, passenger flow, ML-powered predictions, and a full-featured control center dashboard.

### Key Capabilities

- **Simulate** train physics, signalling, timetables, and passenger flow at 1s granularity
- **Visualize** live train positions, speed, crowd occupancy, and ETA on an interactive 3D map
- **Predict** delays, demand, crowding, ETAs, and incident risk with scikit-learn models
- **Control** the system via dashboard widgets and a natural-language control-room assistant
- **Analyze** performance metrics, delay patterns, and network utilization in real time

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, MapLibre GL + Deck.gl, React Query, Zustand, Framer Motion, Recharts |
| Backend | FastAPI, Python 3.12, SQLAlchemy 2.x, Alembic, Pydantic v2, WebSockets |
| Simulation | Pure Python async fixed-timestep engine |
| GIS | Shapely, pyproj, PostGIS, GeoJSON |
| Database | PostgreSQL 16 + PostGIS |
| Cache | Redis |
| Messaging | RabbitMQ |
| AI/ML | scikit-learn, joblib, numpy, scipy, pandas |
| Testing | pytest, Vitest, Playwright |
| CI/CD | GitHub Actions |
| Deployment | Docker, Docker Compose |

---

## Quick Start

```bash
# Prerequisites: Docker 24+, Docker Compose v2

# Start the full stack
make up

# Apply database migrations
make migrate

# Seed the network
make seed

# Open the control center
open http://localhost:3000
```

**Login credentials:** `admin` / `admin`

---

## Architecture

```
┌─────────────────────────────────────────────┐
│              Web Frontend                    │
│  Next.js · MapLibre GL · Zustand · Recharts │
├─────────────────────────────────────────────┤
│              Backend API                     │
│  FastAPI · WebSocket · JWT Auth · REST      │
├─────────────────────────────────────────────┤
│           Simulation Engine                  │
│  Physics · Signalling · Passengers · Events │
├─────────────────────────────────────────────┤
│            Data & GIS Layer                  │
│  PostgreSQL/PostGIS · Redis · RabbitMQ      │
└─────────────────────────────────────────────┘
```

---

## Project Structure

```
├── backend/        # FastAPI REST + WebSocket API (dmdt-backend)
├── simulation/     # Physics/signalling/passenger engine (dmdt-sim)
├── database/       # SQLAlchemy models + Alembic (dmdt-database)
├── gis/            # GIS geometry + network validation (dmdt-gis)
├── web/            # Next.js control center (dmdt-web)
├── docker/         # Dockerfiles + docker-compose.yml
├── configs/        # Environment configuration
├── docs/           # Documentation
│   ├── architecture.md
│   ├── api.md
│   ├── database.md
│   ├── simulation.md
│   ├── deployment.md
│   └── developer.md
├── tests/          # Cross-cutting test suites
├── assets/         # Icons, sprites, basemap resources
└── Makefile        # Operational commands
```

---

## Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System design, data flow, layers |
| [API Reference](docs/api.md) | All REST and WebSocket endpoints |
| [Database Schema](docs/database.md) | ER diagram, entities, conventions |
| [Simulation Engine](docs/simulation.md) | Physics, signalling, passenger model |
| [Deployment Guide](docs/deployment.md) | Docker, configuration, production |
| [Developer Guide](docs/developer.md) | Setup, workflow, contributing |

---

## Running Tests

```bash
# Python tests (backend + simulation + gis)
make backend-test
make sim-test

# Frontend tests
make fe-test

# All Python tests
pytest backend/tests/ simulation/tests/ gis/tests/ -v

# All frontend tests
cd web && npm run test && npm run type-check && npm run lint
```

---

## License

Proprietary. Copyright 2026 Delhi Metro Digital Twin Project.
All rights reserved. For DMRC and authorized transit operators only.
Contact: twin@dmrc.local
# Delhi-metro-twin
