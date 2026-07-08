import { create } from "zustand";
import type { TrainPosition, SimulationMetrics, SimulationState } from "@/types/api";

interface SimulationStore {
  trains: TrainPosition[];
  metrics: SimulationMetrics | null;
  state: SimulationState | null;
  tick: number;
  time_s: number;
  ist_time: string;
  service_period: string;
  depot_trains: number;
  completed_passengers: number;
  active_incidents: number;
  passengers: number;
  prev_completed: number;
  prev_time_s: number;
  setTrains: (trains: TrainPosition[]) => void;
  setMetrics: (m: SimulationMetrics) => void;
  setState: (s: SimulationState) => void;
  setTick: (tick: number, time_s: number) => void;
  setSimStats: (completed: number, incidents: number, passengers: number) => void;
  setServiceMeta: (istTime: string, period: string, depotTrains: number) => void;
}

export const useSimulationStore = create<SimulationStore>((set) => ({
  trains: [],
  metrics: null,
  state: null,
  tick: 0,
  time_s: 0,
  ist_time: "",
  service_period: "",
  depot_trains: 0,
  completed_passengers: 0,
  active_incidents: 0,
  passengers: 0,
  prev_completed: 0,
  prev_time_s: 0,
  setTrains: (trains) => set({ trains }),
  setMetrics: (metrics) => set({
    metrics: {
      avg_headway_s: metrics.avg_headway_s ?? 0,
      avg_dwell_s: metrics.avg_dwell_s ?? 0,
      avg_journey_time_s: metrics.avg_journey_time_s ?? 0,
      avg_speed_mps: metrics.avg_speed_mps ?? 0,
      total_energy_wh: metrics.total_energy_wh ?? 0,
    },
  }),
  setState: (state) => set({ state }),
  setTick: (tick, time_s) => set({ tick, time_s }),
  setSimStats: (completed, incidents, passengers) => set((s) => ({
    completed_passengers: completed,
    active_incidents: incidents,
    passengers,
    prev_completed: s.completed_passengers,
    prev_time_s: s.time_s,
  })),
  setServiceMeta: (ist_time, service_period, depot_trains) => set({ ist_time, service_period, depot_trains }),
}));
