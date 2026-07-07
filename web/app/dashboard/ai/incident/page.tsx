"use client";

import { useSimulationStore } from "@/stores/simulation";
import { AIPredictionCard, MetricRow } from "@/components/ai/AIPredictionCard";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from "recharts";
import { useMemo } from "react";

export default function IncidentRiskPage() {
  const { trains, state } = useSimulationStore();

  const riskData = useMemo(() => {
    const lines = ["RD", "YL", "BL", "GR", "BR"];
    return lines.map((code) => {
      const lineTrains = trains.filter((t) => t.line_code === code);
      const count = lineTrains.length;
      const stopped = lineTrains.filter((t) => t.status === "stopped").length;
      const risk = count > 0 ? Math.min(100, Math.round((stopped / count) * 100 + Math.random() * 10)) : 0;
      const level = risk >= 50 ? "High" : risk >= 20 ? "Medium" : "Low";
      return { line: code, risk, level, stopped, count };
    });
  }, [trains]);

  const avgRisk = riskData.length > 0
    ? Math.round(riskData.reduce((s, d) => s + d.risk, 0) / riskData.length)
    : 0;

  const totalStopped = trains.filter((t) => t.status === "stopped").length;

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <h1 className="text-lg font-bold">⚠ Incident Risk Assessment</h1>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        <AIPredictionCard title="Risk Level" icon="📊">
          <MetricRow
            label="Network Avg Risk"
            value={avgRisk >= 50 ? "High" : avgRisk >= 20 ? "Medium" : "Low"}
          />
        </AIPredictionCard>
        <AIPredictionCard title="Active Incidents" icon="⚠">
          <MetricRow label="Stopped Trains" value={String(totalStopped)} />
        </AIPredictionCard>
        <AIPredictionCard title="Highest Risk" icon="🔴">
          <MetricRow
            label="Line"
            value={riskData.reduce((max, d) => (d.risk > max.risk ? d : max), riskData[0] || { line: "N/A", risk: 0 }).line}
          />
        </AIPredictionCard>
        <AIPredictionCard title="Safe Lines" icon="🟢">
          <MetricRow
            label="Count"
            value={String(riskData.filter((d) => d.level === "Low").length)}
          />
        </AIPredictionCard>
      </div>

      <div className="card">
        <h3 className="mb-3 text-sm font-semibold">Incident Risk by Line</h3>
        <ResponsiveContainer width="100%" height={350}>
          <BarChart data={riskData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis dataKey="line" stroke="#9CA3AF" fontSize={12} />
            <YAxis stroke="#9CA3AF" fontSize={12} domain={[0, 100]} />
            <Tooltip contentStyle={{ background: "#1f2937", border: "1px solid #374151", borderRadius: "6px", fontSize: "12px" }} />
            <Bar dataKey="risk" radius={[4, 4, 0, 0]} name="Risk %">
              {riskData.map((entry) => (
                <Cell
                  key={entry.line}
                  fill={entry.risk >= 50 ? "#EF4444" : entry.risk >= 20 ? "#F59E0B" : "#22C55E"}
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
