import { create } from "zustand";
import type { TrainPosition, SimulationMetrics, SimulationState } from "@/types/api";

interface SimulationStore {
  trains: TrainPosition[];
  metrics: SimulationMetrics | null;
  state: SimulationState | null;
  tick: number;
  time_s: number;
  setTrains: (trains: TrainPosition[]) => void;
  setMetrics: (m: SimulationMetrics) => void;
  setState: (s: SimulationState) => void;
  setTick: (tick: number, time_s: number) => void;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  trains: [],
  metrics: null,
  state: null,
  tick: 0,
  time_s: 0,
  setTrains: (trains) => set({ trains }),
  setMetrics: (metrics) => set({ metrics }),
  setState: (state) => set({ state }),
  setTick: (tick, time_s) => set({ tick, time_s }),
}));
