"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AIPredictionCard, MetricRow } from "@/components/ai/AIPredictionCard";
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";

export default function ETAPredictionPage() {
  const { trains, metrics } = useSimulationStore();

  const chartData = trains.slice(0, 20).map((t) => ({
    name: t.train_id,
    speed: t.speed_kmh,
    line: t.line_code,
  }));

  const avgSpeed = trains.length > 0
    ? trains.reduce((s, t) => s + t.speed_kmh, 0) / trains.length
    : 0;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">🚄 ETA Prediction</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AIPredictionCard title="Avg Speed" icon="📊">
          <MetricRow label="Network Average" value={avgSpeed.toFixed(1)} unit="km/h" />
        </AIPredictionCard>
        <AIPredictionCard title="Headway" icon="⏱">
          <MetricRow label="Avg Headway" value={metrics?.avg_headway_s.toFixed(0) || "N/A"} unit="s" />
        </AIPredictionCard>
        <AIPredictionCard title="Dwell Time" icon="🚉">
          <MetricRow label="Avg Dwell" value={metrics?.avg_dwell_s.toFixed(0) || "N/A"} unit="s" />
        </AIPredictionCard>
        <AIPredictionCard title="Journey Time" icon="🕐">
          <MetricRow
            label="Avg Journey"
            value={metrics ? (metrics.avg_journey_time_s / 60).toFixed(0) : "N/A"}
            unit="min"
          />
        </AIPredictionCard>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold">Train Speeds</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="name" stroke="#9CA3AF" fontSize={10} />
            <YAxis stroke="#9CA3AF" fontSize={12} label={{ value: "km/h", angle: -90, position: "insideLeft", style: { fill: "#9CA3AF", fontSize: 12 } }} />
            <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "6px", fontSize: "12px" }} />
            <Line type="monotone" dataKey="speed" stroke="#3B82F6" strokeWidth={2} dot={{ r: 3 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
