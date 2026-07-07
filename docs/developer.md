# Developer Guide

## Setup

### Prerequisites

- Python 3.12+
- Node.js 24+
- Docker 24+ (for full stack)
- PostgreSQL 16 (optional, for local dev)

### Python Environment

```bash
# Create virtual environment
make venv
# Or manually:
python3.12 -m venv .venv
source .venv/bin/activate

# Install all packages in editable mode
pip install -e gis/ -e database/ -e simulation/ -e backend/

# Install dev dependencies
pip install -r backend/requirements-dev.txt
```

### Frontend Setup

```bash
make fe-venv
# Or:
cd web && npm install
```

## Development Workflow

### Backend

```bash
# Start the backend with hot-reload
cd backend
uvicorn app.main:app --reload --port 8000

# Run tests
make backend-test

# Lint and format
make backend-lint
make backend-fmt
```

### Frontend

```bash
cd web
npm run dev          # Development server on :3000
npm run test         # Vitest unit tests
npm run type-check   # TypeScript type checking
npm run lint         # ESLint
npm run build        # Production build
```

### Simulation

```bash
# Headless run
make sim-run

# Run tests
make sim-test
```

## Project Commands

See the `Makefile` for all available commands:

| Command | Description |
|---|---|
| `make up` | Start full Docker stack |
| `make down` | Stop Docker stack |
| `make migrate` | Apply DB migrations |
| `make migrate-new MSG="desc"` | Create migration |
| `make seed` | Seed network data |
| `make psql` | Open psql shell |
| `make backend-shell` | Shell into backend container |

## Make targets reference

Run `make help` to see all available targets.

## Testing Strategy

- **Unit tests**: Vitest (frontend), pytest (backend/simulation/gis)
- **Integration tests**: pytest with test database
- **E2E tests**: Playwright (frontend)
- **Load tests**: Locust or k6 (tests/load/)

## Code Style

- **Python**: Ruff for linting and formatting (compatible with Black)
- **TypeScript**: ESLint `next/core-web-vitals`
- **Imports**: isort-style (Ruff handles this)

## Adding a New API Endpoint

1. Create the schema in `backend/app/schemas/`
2. Create the service in `backend/app/services/`
3. Create the route in `backend/app/api/v1/`
4. Register the route in `backend/app/api/v1/router.py`
5. Add the client method in `web/lib/api.ts`
6. Add TypeScript types in `web/types/api.ts`
7. Write tests for all layers

## Architecture Decisions

- **Monorepo** with editable pip packages for shared code
- **Repository pattern** for data access (testable with mocks)
- **Zustand** over Redux for state management (minimal boilerplate)
- **React Query** for server state (caching, refetching, optimistic updates)
- **MapLibre GL** over Google Maps (open source, Deck.gl integration)
- **WebSocket** for real-time updates (lower latency than polling)
