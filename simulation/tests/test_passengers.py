from __future__ import annotations

from dmdt_sim.passengers.population import PassengerPopulation
from dmdt_sim.types import Direction, SimulationConfig


def test_passenger_generation():
    config = SimulationConfig(dt_s=1.0, seed=42, duration_s=3600.0, n_passengers=100)
    pop = PassengerPopulation(config)
    stations = {
        "STA": {"code": "STA", "line_code": "RED", "sequence": 1},
        "STB": {"code": "STB", "line_code": "RED", "sequence": 2},
        "STC": {"code": "STC", "line_code": "BLUE", "sequence": 1},
    }
    lines = {"RED": {"code": "RED"}, "BLUE": {"code": "BLUE"}}
    pop.generate(stations, lines)
    assert len(pop.agents) == 100
    for agent in pop.agents:
        assert agent.origin_station_code in stations
        assert agent.destination_station_code in stations


def test_boarding_alighting():
    config = SimulationConfig(dt_s=1.0, seed=42, duration_s=3600.0, n_passengers=10)
    pop = PassengerPopulation(config)
    stations = {
        "STA": {"code": "STA", "line_code": "RED", "sequence": 1},
        "STB": {"code": "STB", "line_code": "RED", "sequence": 2},
    }
    lines = {"RED": {"code": "RED"}}
    pop.generate(stations, lines)
    agent = pop.agents[0]
    pop.add_agent_to_queue(agent, "RED", Direction.UP)
    boarding = pop.process_boarding("STA", "RED", Direction.UP, 5, 100.0)
    assert len(boarding) > 0
    remaining = [a for a in pop.agents if a not in boarding]
    assert len(boarding) + len(remaining) == len(pop.agents)
    alighted, still_on = pop.process_alighting(boarding, "STB", 200.0)
    for a in alighted:
        assert a.state.value == "completed"
