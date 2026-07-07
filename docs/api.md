# API Documentation

## Base URL

All API endpoints are prefixed with `/api/v1`. Example: `http://localhost:8000/api/v1/health`.

## Authentication

### POST `/auth/login`

Authenticate and receive JWT tokens.

**Request:**
```json
{ "username": "admin", "password": "admin" }
```

**Response (200):**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Error (401):** Invalid credentials.

Access tokens expire after 30 minutes; refresh tokens after 7 days.

---

## Health

### GET `/health`

**Response (200):**
```json
{ "status": "ok", "version": "0.1.0", "timestamp": "2026-07-07T12:00:00Z" }
```

---

## Lines

### GET `/lines`

List all metro lines.

| Query | Type | Default |
|---|---|---|
| `skip` | int | 0 |
| `limit` | int | 100 (max 500) |

### GET `/lines/{code}`

Get a single line by code (e.g., `RD`, `YL`, `BL`).

### GET `/lines/{code}/stations`

Get a line including its stations.

---

## Stations

### GET `/stations`

List stations (paginated).

| Query | Type | Default |
|---|---|---|
| `line_code` | string | optional |
| `skip` | int | 0 |
| `limit` | int | 100 |

### GET `/stations/{id}`

Get station detail by UUID.

---

## Tracks

### GET `/tracks`

List track segments. Supports `line_code`, `skip`, `limit`.

### GET `/tracks/{id}`

Get track segment detail by UUID.

---

## Train Classes

### GET `/trains/classes`

List all train classes.

### GET `/trains/classes/{id}`

Get train class detail by UUID.

---

## Depots

### GET `/depots`

List depots. Supports `line_code`, `skip`, `limit`.

### GET `/depots/{id}`

Get depot detail by UUID.

---

## Simulation Control

### POST `/simulation/start`

Start the simulation. Optional config body:

```json
{
  "duration_s": 3600,
  "dt_s": 1.0,
  "seed": 42,
  "n_passengers": 50000,
  "headway_target_s": 120,
  "snapshot_interval_s": 30
}
```

### POST `/simulation/stop`

Stop the simulation.

### POST `/simulation/pause`

Pause the simulation.

### POST `/simulation/resume`

Resume a paused simulation.

### GET `/simulation/state`

Get current simulation state:

```json
{
  "running": true,
  "paused": false,
  "time_s": 1250.0,
  "trains": 12,
  "active_trains": 12,
  "passengers": 50000,
  "completed_passengers": 15230,
  "active_incidents": 0
}
```

### GET `/simulation/snapshots`

Get the full snapshot history.

---

## WebSocket

### WS `/ws/simulation`

Real-time global simulation feed. Server pushes every 2s:

```json
{
  "type": "position_update",
  "tick": 42,
  "time_s": 1250.0,
  "trains": [{
    "train_id": "T001",
    "line_code": "RD",
    "direction": "up",
    "status": "running",
    "speed_kmh": 45.0,
    "speed_mps": 12.5,
    "position_m": 8500.0,
    "current_station": "CST",
    "next_station": "KSH",
    "occupancy": 320,
    "doors_open": false,
    "block_id": "B-12"
  }],
  "metrics": {
    "avg_headway_s": 120.0,
    "avg_dwell_s": 20.0,
    "avg_journey_time_s": 1800.0,
    "avg_speed_mps": 12.5,
    "total_energy_wh": 45000.0
  }
}
```

### WS `/ws/simulation/{line_code}`

Same format, filtered to a single line.

---

## Error Format

```json
{
  "detail": "Resource not found",
  "error_code": "NOT_FOUND"
}
```
