import { describe, it, expect } from "vitest";
import { useSimulationStore } from "@/stores/simulation";
import type { TrainPosition } from "@/types/api";

describe("Simulation Store", () => {
  it("starts with empty state", () => {
    const state = useSimulationStore.getState();
    expect(state.trains).toEqual([]);
    expect(state.metrics).toBeNull();
    expect(state.state).toBeNull();
    expect(state.tick).toBe(0);
  });

  it("setTrains updates train list", () => {
    const train: TrainPosition = {
      train_id: "T001",
      line_code: "RD",
      direction: "up",
      status: "running",
      speed_kmh: 45,
      speed_mps: 12.5,
      position_m: 1000,
      current_station: "STA",
      next_station: "STB",
      occupancy: 200,
      doors_open: false,
      block_id: "B-01",
    };
    useSimulationStore.getState().setTrains([train]);
    expect(useSimulationStore.getState().trains).toHaveLength(1);
    expect(useSimulationStore.getState().trains[0].train_id).toBe("T001");
  });
});
