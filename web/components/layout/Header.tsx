"use client";

import { useSimulationStore } from "@/stores/simulation";

export function Header() {
  const { state, metrics, time_s, tick } = useSimulationStore();

  return (
    <header className="flex h-14 items-center gap-4 border-b border-surface-200 bg-white/80 px-4 backdrop-blur dark:border-surface-700 dark:bg-surface-900/80">
      <div className="flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${
            state?.running
              ? state?.paused
                ? "bg-yellow-400"
                : "bg-green-400 animate-pulse"
              : "bg-surface-400"
          }`}
        />
        <span className="text-xs font-medium text-surface-600 dark:text-surface-400">
          {state?.running
            ? state.paused
              ? "Paused"
              : "Live"
            : "Offline"}
        </span>
      </div>

      {state && (
        <div className="hidden gap-4 text-xs text-surface-500 md:flex">
          <span>T+{time_s.toFixed(0)}s</span>
          <span>Tick #{tick}</span>
          <span>Trains: {state.active_trains}/{state.trains}</span>
          <span>Passengers: {state.completed_passengers}/{state.passengers}</span>
        </div>
      )}

      {metrics && (
        <div className="hidden gap-4 text-xs text-surface-500 lg:flex">
          <span>Headway: {metrics.avg_headway_s.toFixed(0)}s</span>
          <span>Speed: {(metrics.avg_speed_mps * 3.6).toFixed(0)} km/h</span>
          <span>Energy: {(metrics.total_energy_wh / 1000).toFixed(1)} kWh</span>
        </div>
      )}

      <div className="flex-1" />

      <div className="flex items-center gap-2">
        <input
          className="input h-8 w-48 text-xs"
          placeholder="Search stations, trains..."
        />
      </div>
    </header>
  );
}
