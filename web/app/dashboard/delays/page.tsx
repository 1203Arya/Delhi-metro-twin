"use client";

import { useSimulationStore } from "@/stores/simulation";
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar,
} from "recharts";

export default function DelayAnalyticsPage() {
  const { trains, metrics, state, tick } = useSimulationStore();

  const lineData = ["RD", "YL", "BL", "GR", "BR"].map((code) => {
    const lineTrains = trains.filter((t) => t.line_code === code);
    const avgSpeed = lineTrains.length > 0
      ? lineTrains.reduce((s, t) => s + t.speed_kmh, 0) / lineTrains.length
      : 0;
    return { line: code, avgSpeed: Math.round(avgSpeed), count: lineTrains.length };
  });

  const occupancyData = trains.slice(0, 15).map((t) => ({
    name: t.train_id,
    occupancy: t.occupancy,
  }));

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">Delay Analytics</h1>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="card">
          <h3 className="mb-3 text-sm font-semibold">Average Speed by Line</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={lineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="line" stroke="#9CA3AF" fontSize={12} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="avgSpeed" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Avg Speed (km/h)" />
              <Bar dataKey="count" fill="#8B5CF6" radius={[4, 4, 0, 0]} name="Train Count" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-semibold">Train Occupancy</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={occupancyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
              <XAxis dataKey="name" stroke="#9CA3AF" fontSize={10} />
              <YAxis stroke="#9CA3AF" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: "#1f2937",
                  border: "1px solid #374151",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              />
              <Bar dataKey="occupancy" fill="#F59E0B" radius={[4, 4, 0, 0]} name="Passengers" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-semibold">Network Metrics</h3>
          {metrics ? (
            <div className="grid grid-cols-2 gap-3">
              <MetricBox label="Avg Headway" value={`${metrics.avg_headway_s.toFixed(0)}s`} />
              <MetricBox label="Avg Dwell" value={`${metrics.avg_dwell_s.toFixed(0)}s`} />
              <MetricBox label="Avg Journey" value={`${(metrics.avg_journey_time_s / 60).toFixed(0)}min`} />
              <MetricBox label="Avg Speed" value={`${(metrics.avg_speed_mps * 3.6).toFixed(0)} km/h`} />
              <MetricBox label="Energy" value={`${(metrics.total_energy_wh / 1000).toFixed(1)} kWh`} />
              <MetricBox label="Tick" value={`#${tick}`} />
            </div>
          ) : (
            <p className="text-xs text-surface-400">No metrics available. Start the simulation.</p>
          )}
        </div>

        <div className="card">
          <h3 className="mb-3 text-sm font-semibold">Simulation State</h3>
          {state ? (
            <div className="grid grid-cols-2 gap-3">
              <MetricBox label="Status" value={state.running ? state.paused ? "Paused" : "Running" : "Stopped"} />
              <MetricBox label="Sim Time" value={`${state.time_s.toFixed(0)}s`} />
              <MetricBox label="Active Trains" value={String(state.active_trains)} />
              <MetricBox label="Total Trains" value={String(state.trains)} />
              <MetricBox label="Passengers" value={String(state.passengers)} />
              <MetricBox label="Completed" value={String(state.completed_passengers)} />
            </div>
          ) : (
            <p className="text-xs text-surface-400">Simulation not started</p>
          )}
        </div>
      </div>
    </div>
  );
}

function MetricBox({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-surface-50 p-3 dark:bg-surface-800">
      <p className="text-xs text-surface-500">{label}</p>
      <p className="mt-1 text-lg font-bold">{value}</p>
    </div>
  );
}
