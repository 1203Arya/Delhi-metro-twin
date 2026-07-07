"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import { EmptyState } from "@/components/ui/EmptyState";
import { useSimulationStore } from "@/stores/simulation";
import { useState } from "react";

export default function TimetablePage() {
  const { data: lines, isLoading } = useQuery({
    queryKey: ["lines"],
    queryFn: () => api.lines.list(),
  });
  const { trains, state } = useSimulationStore();
  const [selectedLine, setSelectedLine] = useState("all");

  const filteredTrains = selectedLine === "all" ? trains : trains.filter((t) => t.line_code === selectedLine);

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <LoadingSpinner className="h-8 w-8" />
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col p-4">
      <div className="mb-4 flex items-center justify-between">
        <h1 className="text-lg font-bold">Timetable</h1>
        <div className="flex items-center gap-2">
          <span className="text-xs text-surface-500">
            Sim Time: T+{state?.time_s.toFixed(0) || 0}s
          </span>
          <select
            className="input h-8 w-36 text-xs"
            value={selectedLine}
            onChange={(e) => setSelectedLine(e.target.value)}
          >
            <option value="all">All Lines</option>
            {(lines || []).map((l) => (
              <option key={l.code} value={l.code}>
                {l.name}
              </option>
            ))}
          </select>
        </div>
      </div>

      {filteredTrains.length === 0 ? (
        <EmptyState title="No trains running" description="Start the simulation to see train timetables." />
      ) : (
        <div className="flex-1 overflow-auto rounded-lg border border-surface-200 dark:border-surface-700">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-surface-100 dark:bg-surface-800">
              <tr>
                <th className="px-3 py-2 font-medium">Train</th>
                <th className="px-3 py-2 font-medium">Line</th>
                <th className="px-3 py-2 font-medium">Direction</th>
                <th className="px-3 py-2 font-medium">From</th>
                <th className="px-3 py-2 font-medium">To</th>
                <th className="px-3 py-2 font-medium">Speed</th>
                <th className="px-3 py-2 font-medium">Status</th>
                <th className="px-3 py-2 font-medium">Occupancy</th>
                <th className="px-3 py-2 font-medium">Block</th>
              </tr>
            </thead>
            <tbody>
              {filteredTrains.map((t) => (
                <tr
                  key={t.train_id}
                  className="border-t border-surface-100 transition-colors hover:bg-surface-50 dark:border-surface-800 dark:hover:bg-surface-800/50"
                >
                  <td className="px-3 py-2 font-mono font-bold">{t.train_id}</td>
                  <td className="px-3 py-2">
                    <span className={`badge`} style={{ backgroundColor: t.line_code === "RD" ? "#fef2f2" : "#eff6ff", color: t.line_code === "RD" ? "#991b1b" : "#1e40af" }}>
                      {t.line_code}
                    </span>
                  </td>
                  <td className="px-3 py-2">{t.direction}</td>
                  <td className="px-3 py-2">{t.current_station}</td>
                  <td className="px-3 py-2">{t.next_station}</td>
                  <td className="px-3 py-2 font-mono">{t.speed_kmh.toFixed(0)} km/h</td>
                  <td className="px-3 py-2">
                    <span className={`badge ${t.status === "running" ? "badge-green" : t.status === "stopped" ? "badge-red" : "badge-yellow"}`}>
                      {t.status}
                    </span>
                  </td>
                  <td className="px-3 py-2 font-mono">{t.occupancy}</td>
                  <td className="px-3 py-2 font-mono text-surface-400">{t.block_id}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
