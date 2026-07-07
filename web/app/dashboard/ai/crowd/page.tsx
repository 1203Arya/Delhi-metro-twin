"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AIPredictionCard, MetricRow } from "@/components/ai/AIPredictionCard";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from "recharts";
import { useMemo } from "react";

const LINE_COLORS: Record<string, string> = {
  RD: "#EF4444",
  YL: "#EAB308",
  BL: "#3B82F6",
  GR: "#22C55E",
  BR: "#8B5CF6",
};

export default function CrowdForecastPage() {
  const { trains } = useSimulationStore();

  const crowdData = useMemo(() => {
    const lines = ["RD", "YL", "BL", "GR", "BR"];
    return lines.map((code) => {
      const lineTrains = trains.filter((t) => t.line_code === code);
      const count = lineTrains.length;
      const avgOcc = count > 0 ? lineTrains.reduce((s, t) => s + t.occupancy, 0) / count : 0;
      const crowdLevel = avgOcc > 500 ? "High" : avgOcc > 200 ? "Medium" : "Low";
      return { line: code, crowd: Math.round(avgOcc), level: crowdLevel, count };
    });
  }, [trains]);

  const totalCrowdScore = crowdData.reduce((s, d) => s + d.crowd, 0);
  const avgCrowd = crowdData.filter((d) => d.count > 0).length > 0
    ? Math.round(totalCrowdScore / crowdData.filter((d) => d.count > 0).length)
    : 0;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">👥 Crowd Forecast</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AIPredictionCard title="Avg Crowding" icon="📊">
          <MetricRow label="Network Avg" value={String(avgCrowd)} unit="pax" />
        </AIPredictionCard>
        <AIPredictionCard title="Highest" icon="🔴">
          <MetricRow
            label="Line"
            value={crowdData.reduce((max, d) => (d.crowd > max.crowd ? d : max), crowdData[0] || { line: "N/A", crowd: 0 }).line}
          />
        </AIPredictionCard>
        <AIPredictionCard title="Lowest" icon="🟢">
          <MetricRow
            label="Line"
            value={crowdData.reduce((min, d) => (d.crowd < min.crowd ? d : min), crowdData[0] || { line: "N/A", crowd: 0 }).line}
          />
        </AIPredictionCard>
        <AIPredictionCard title="Active Trains" icon="🚆">
          <MetricRow label="In Service" value={String(trains.length)} />
        </AIPredictionCard>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold">Crowding by Line</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={crowdData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="line" stroke="#9CA3AF" fontSize={12} />
            <YAxis stroke="#9CA3AF" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "6px", fontSize: "12px" }} />
            <Bar dataKey="crowd" radius={[4, 4, 0, 0]} name="Crowding Level">
              {crowdData.map((entry) => (
                <Cell key={entry.line} fill={LINE_COLORS[entry.line] || "#6B7280"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
