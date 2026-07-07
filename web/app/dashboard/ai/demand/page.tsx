"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AIPredictionCard, MetricRow } from "@/components/ai/AIPredictionCard";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from "recharts";
import { useMemo } from "react";

export default function DemandForecastPage() {
  const { trains, state } = useSimulationStore();

  const occupancyByLine = useMemo(() => {
    const lines = ["RD", "YL", "BL", "GR", "BR"];
    return lines.map((code) => {
      const lineTrains = trains.filter((t) => t.line_code === code);
      const avgOcc = lineTrains.length > 0
        ? lineTrains.reduce((s, t) => s + t.occupancy, 0) / lineTrains.length
        : 0;
      return { line: code, avgOccupancy: Math.round(avgOcc), count: lineTrains.length };
    });
  }, [trains]);

  const totalCapacity = trains.reduce((s, t) => s + t.occupancy, 0);
  const estimatedDemand = totalCapacity + Math.round(totalCapacity * 0.15);

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">📈 Demand Forecast</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AIPredictionCard title="Current Load" icon="👥">
          <MetricRow label="Total Passengers" value={String(totalCapacity)} />
        </AIPredictionCard>
        <AIPredictionCard title="Forecast" icon="🔮">
          <MetricRow label="Estimated Demand" value={String(estimatedDemand)} />
        </AIPredictionCard>
        <AIPredictionCard title="Active Trains" icon="🚆">
          <MetricRow label="In Service" value={String(trains.length)} />
        </AIPredictionCard>
        <AIPredictionCard title="Completion" icon="✅">
          <MetricRow label="Completed" value={String(state?.completed_passengers || 0)} />
        </AIPredictionCard>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold">Average Occupancy by Line</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={occupancyByLine}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="line" stroke="#9CA3AF" fontSize={12} />
            <YAxis stroke="#9CA3AF" fontSize={12} />
            <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "6px", fontSize: "12px" }} />
            <Bar dataKey="avgOccupancy" fill="#F59E0B" radius={[4, 4, 0, 0]} name="Avg Occupancy" />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
