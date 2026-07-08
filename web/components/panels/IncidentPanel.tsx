"use client";

import { useMemo, useState } from "react";
import { useSimulationStore } from "@/stores/simulation";

const INCIDENT_STATUSES = new Set(["stopped", "emergency_brake", "incident_halt", "turnback"]);

interface IncidentPanelProps {
  onClose: () => void;
}

export function IncidentPanel({ onClose }: IncidentPanelProps) {
  const { trains, state } = useSimulationStore();
  const [filter, setFilter] = useState("all");

  const incidentTrains = useMemo(
    () => trains.filter((t) => INCIDENT_STATUSES.has(t.status)),
    [trains],
  );

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">⚠ Incidents</h3>
        <button onClick={onClose} className="btn-ghost p-1 text-xs">✕</button>
      </div>

      <div className="mb-2">
        <span className={`badge ${(state?.active_incidents || 0) > 0 ? "badge-red" : "badge-green"} mb-2`}>
          {state?.active_incidents || 0} active incidents
        </span>
      </div>

      <div className="mb-2 flex gap-1">
        {["all", "stopped", "delayed"].map((f) => (
          <button
            key={f}
            className={`rounded px-2 py-1 text-xs ${
              filter === f
                ? "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
                : "bg-surface-100 text-surface-600 dark:bg-surface-800 dark:text-surface-400"
            }`}
            onClick={() => setFilter(f)}
          >
            {f}
          </button>
        ))}
      </div>

      <div className="max-h-60 space-y-1 overflow-y-auto scrollbar-thin">
        {incidentTrains.length === 0 ? (
          <p className="py-4 text-center text-xs text-surface-400">No active incidents</p>
        ) : (
          incidentTrains
            .filter((t) => filter === "all" || t.status === filter)
            .map((t) => (
              <div
                key={t.train_id}
                className="rounded border border-red-200 bg-red-50 p-2 dark:border-red-900/30 dark:bg-red-900/10"
              >
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold">{t.train_id}</span>
                  <span className="badge-red">{t.status.replace(/_/g, " ")}</span>
                </div>
                <p className="mt-1 text-xs text-surface-500">
                  {t.current_station_name || t.current_station} → {t.next_station_name || t.next_station}
                </p>
              </div>
            ))
        )}
      </div>
    </div>
  );
}
