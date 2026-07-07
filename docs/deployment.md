# Deployment Guide

## Prerequisites

- Docker 24+ and Docker Compose v2
- 8 GB RAM minimum (16 GB recommended)
- 20 GB free disk space
- Ports 3000, 8000, 5432, 6379, 5672, 15672, 9090 available

## Quick Start

```bash
# Clone the repository
git clone <repo-url> delhi-metro-digital-twin
cd delhi-metro-digital-twin

# Start the full stack
make up

# Apply database migrations
make migrate

# Seed the network data
make seed

# Check running services
make ps
```

The control center is available at `http://localhost:3000`.

## Service Ports

| Service | Port | Description |
|---|---|---|
| Frontend | 3000 | Next.js UI |
| Backend API | 8000 | FastAPI REST + WebSocket |
| PostgreSQL | 5432 | Primary database |
| Redis | 6379 | Cache |
| RabbitMQ | 5672 (AMQP) / 15672 (Management UI) | Message broker |
| Prometheus | 9090 | Metrics (profile: `observe`) |

## Configuration

Copy the example config and customize:

```bash
cp configs/dev.env.example configs/dev.env
# Edit configs/dev.env with your settings
```

Key environment variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `postgresql+asyncpg://dmdt:change-me-in-dev@postgres:5432/dmdt` | Database connection |
| `REDIS_URL` | `redis://dmdt:change-me-in-dev@redis:6379/0` | Redis connection |
| `RABBITMQ_URL` | `amqp://dmdt:change-me-in-dev@rabbitmq:5672/` | RabbitMQ connection |
| `JWT_SECRET` | `change-this-to-a-long-random-string` | JWT signing key |
| `ENVIRONMENT` | `development` | Runtime environment |
| `LOG_LEVEL` | `DEBUG` | Logging verbosity |

## Production Deployment

For production, update `configs/prod.env`:

1. Generate strong passwords and JWT secret
2. Set `ENVIRONMENT=production`
3. Set `LOG_LEVEL=INFO`
4. Configure CORS origins for your domain
5. Enable TLS/SSL via reverse proxy (nginx/traefik)

```bash
docker compose -f docker/docker-compose.yml --env-file configs/prod.env up -d
```

## Scaling

- Backend: Increase `WORKERS` (default 4) for more concurrency
- Simulation: Run multiple simulation instances with different line codes
- Frontend: Next.js standalone output supports horizontal scaling behind a load balancer

## Monitoring

- Prometheus metrics at `/metrics` on backend and simulation services
- Grafana dashboards (add `docker/grafana/dashboards/`)
- RabbitMQ management UI at port 15672
- Application logs via `docker compose logs -f`

## Backup

```bash
# Database backup
docker exec dmdt-postgres pg_dump -U dmdt dmdt > backup_$(date +%Y%m%d).sql

# Restore
cat backup.sql | docker exec -i dmdt-postgres psql -U dmdt dmdt
```
