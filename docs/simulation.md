# Simulation Engine

## Overview

The simulation engine (`dmdt-sim`) is a pure-Python async fixed-timestep simulation of Delhi Metro operations. It models train physics, signalling (CBTC/ATP/ATO), passenger flow, and incident management.

## Architecture

```
SimulationEngine
├── NetworkGraph        # Line + station + track graph
├── TimetableGenerator  # Schedule and timetable entries
├── BlockManager        # Track block occupancy
├── CBTCController      # Movement authority and speed targeting
├── TrainMotionModel    # Physics: accel, brake, drag, energy
├── PassengerFlowModel  # Boarding, alighting, dwell time
├── PassengerPopulation # Agent generation and queues
├── IncidentManager     # Spawn and resolve incidents
├── DynamicRouter       # Rerouting around disruptions
├── MetricsCollector    # Performance metrics
├── EventBus            # Pub/sub event system
└── DepotYard           # Train stabling and dispatch
```

## Key Parameters

| Parameter | Default | Description |
|---|---|---|
| `dt_s` | 1.0 | Simulation timestep (seconds) |
| `duration_s` | 3600 | Simulation duration |
| `seed` | 42 | RNG seed for determinism |
| `n_passengers` | 50000 | Total passenger agents |
| `headway_target_s` | 120 | Target headway |
| `max_trains_per_line` | 30 | Max active trains per line |

## Train Physics

- **Acceleration**: 0.8 m/s² (service), 1.0 m/s² (emergency)
- **Braking**: 0.9 m/s² (service), 1.2 m/s² (emergency)
- **Max speed**: 80 km/h (22.22 m/s)
- **Mass**: 320,000 kg
- **Length**: 200 m
- **Capacity**: 350 seated, 650 standing
- **Drag**: Davis equation with rolling + aerodynamic resistance
- **Regenerative braking**: Energy recovery model

## Signalling

- **CBTC**: Continuous movement authority based on train position
- **Block occupancy**: Fixed-block signalling with overlap protection
- **ATP**: Automatic Train Protection enforces speed limits
- **ATO**: Automatic Train Operation targets optimal speed profile
- **Headway enforcement**: Minimum 90s separation

## Passenger Flow

- Origin-destination matrix based on station popularity
- Boarding time: 2-5s per passenger
- Alighting time: 1-3s per passenger
- Dwell time: min 15s, max 90s
- Platforms fill and drain based on train arrivals

## Incidents

- Types: signal failure, track obstruction, door fault, medical emergency
- Duration: 5-30 minutes
- Impact: cascading delays, rerouting
- Automatic resolution or manual intervention

## Running

```bash
# Headless simulation for 24 hours
make sim-run

# Run simulation tests
make sim-test

# Direct CLI
python -m dmdt_sim.main --duration 86400 --seed 42
```
