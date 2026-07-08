"use client";

import { useSimulationStore } from "@/stores/simulation";

export function Header() {
  const { state, metrics, time_s, tick, ist_time, service_period, depot_trains } = useSimulationStore();

  const periodColors: Record<string, string> = {
    pre_service: "text-gray-400",
    startup: "text-yellow-500",
    early_service: "text-blue-400",
    morning_peak: "text-red-500",
    midday: "text-green-500",
    evening_peak: "text-red-500",
    late_service: "text-blue-400",
    wind_down: "text-yellow-500",
    post_service: "text-gray-400",
  };

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

      {ist_time && (
        <span className="hidden text-xs font-semibold text-surface-700 dark:text-surface-300 md:inline">
          {ist_time}
        </span>
      )}

      {service_period && (
        <span className={`hidden text-xs font-medium md:inline ${periodColors[service_period] || "text-surface-500"}`}>
          {service_period.replace("_", " ")}
        </span>
      )}

      {state && (
        <div className="hidden gap-4 text-xs text-surface-500 md:flex">
          <span>Tick #{tick}</span>
          <span>Trains: {state.active_trains}/{state.trains}</span>
          <span>Depot: {depot_trains}</span>
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
