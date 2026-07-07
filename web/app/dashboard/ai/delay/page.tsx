"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AIPredictionCard, MetricRow } from "@/components/ai/AIPredictionCard";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export default function DelayPredictionPage() {
  const { trains } = useSimulationStore();

  const byLine = ["RD", "YL", "BL", "GR", "BR"].map((code) => {
    const lineTrains = trains.filter((t) => t.line_code === code);
    const total = lineTrains.length;
    const stopped = lineTrains.filter((t) => t.status === "stopped").length;
    const avgSpeed = total > 0 ? lineTrains.reduce((s, t) => s + t.speed_kmh, 0) / total : 0;
    return { line: code, total, stopped, avgSpeed: Math.round(avgSpeed) };
  });

  const totalStopped = trains.filter((t) => t.status === "stopped").length;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">📊 Delay Prediction</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AIPredictionCard title="Total Trains" icon="🚆">
          <MetricRow label="Active" value={String(trains.length)} />
        </AIPredictionCard>
        <AIPredictionCard title="Stopped" icon="⛔">
          <MetricRow label="Delayed" value={String(totalStopped)} />
        </AIPredictionCard>
        <AIPredictionCard title="Avg Speed" icon="📊">
          <MetricRow label="All Trains" value={
            trains.length > 0
              ? (trains.reduce((s, t) => s + t.speed_kmh, 0) / trains.length).toFixed(0)
              : "0"
          } unit="km/h" />
        </AIPredictionCard>
        <AIPredictionCard title="Lines" icon="🛤">
          <MetricRow label="Active" value={String(new Set(trains.map((t) => t.line_code)).size)} />
        </AIPredictionCard>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold">Delays by Line</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={byLine}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="line" stroke="#9CA3AF" fontSize={12} />
            <YAxis stroke="#9CA3AF" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "6px", fontSize: "12px" }} />
            <Bar dataKey="total" fill="#3B82F6" radius={[4, 4, 0, 0]} name="Total Trains" />
            <Bar dataKey="stopped" fill="#EF4444" radius={[4, 4, 0, 0]} name="Stopped" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
