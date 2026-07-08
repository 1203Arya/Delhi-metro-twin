"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useState } from "react";
import type { TrainPositionsResponse, TrainDebugPosition } from "@/types/api";

const LINE_COLORS: Record<string, string> = {
  RD: "text-red-500",
  YL: "text-yellow-500",
  BL: "text-blue-500",
  GR: "text-green-500",
  V:  "text-violet-500",
  PK: "text-pink-500",
  MG: "text-magenta-500",
  OG: "text-orange-500",
  BR: "text-amber-600",
  GY: "text-gray-500",
};

const STATUS_LABELS: Record<string, string> = {
  running: "Running",
  stopped: "Stopped",
  door_open: "Dwelling (Doors Open)",
  door_close: "Door Closing",
  turnback: "Turning Back",
  departing: "Departing",
  emergency_brake: "Emergency Brake",
  incident_halt: "Halted (Incident)",
  returning_to_depot: "Returning to Depot",
  in_depot: "In Depot",
  deadheading: "Deadheading",
  stopping: "Stopping",
  dooring: "Dooring",
};

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    running: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
    stopped: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
    door_open: "bg-cyan-100 text-cyan-800 dark:bg-cyan-900/30 dark:text-cyan-400",
    door_close: "bg-teal-100 text-teal-800 dark:bg-teal-900/30 dark:text-teal-400",
    turnback: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400",
    departing: "bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-400",
    emergency_brake: "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
    incident_halt: "bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400",
    returning_to_depot: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400",
    in_depot: "bg-gray-100 text-gray-500 dark:bg-gray-800/30 dark:text-gray-500",
    deadheading: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400",
  };
  const cls = colors[status] || "bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-300";
  const label = STATUS_LABELS[status] || status;
  return <span className={`rounded px-1.5 py-0.5 text-xs font-medium ${cls}`}>{label}</span>;
}

function TrainRow({ train, seq }: { train: TrainDebugPosition; seq: number }) {
  const location = train.is_at_platform
    ? train.current_station
    : `${train.current_station} → ${train.next_station}`;

  return (
    <tr className="border-b border-surface-200 text-xs dark:border-surface-700 hover:bg-surface-50 dark:hover:bg-surface-800/50">
      <td className="px-2 py-1.5 text-surface-500">{seq}</td>
      <td className="px-2 py-1.5 font-mono font-medium">{train.train_id}</td>
      <td className={`px-2 py-1.5 font-semibold ${LINE_COLORS[train.line_code] || ""}`}>
        {train.line_name}
      </td>
      <td className="px-2 py-1.5">{train.direction_destination}</td>
      <td className="px-2 py-1.5">
        <StatusBadge status={train.status} />
      </td>
      <td className="px-2 py-1.5 font-mono">{train.speed_kmh.toFixed(1)}</td>
      <td className="px-2 py-1.5 font-mono">{train.occupancy}</td>
      <td className="px-2 py-1.5 max-w-64 truncate" title={location}>
        {location}
      </td>
      <td className="px-2 py-1.5 font-mono text-surface-500">
        {train.distance_to_next_m.toFixed(0)}m
      </td>
      <td className="px-2 py-1.5 font-mono text-surface-500">
        {train.eta_s >= 999 ? "—" : `${train.eta_s.toFixed(0)}s`}
      </td>
      <td className="px-2 py-1.5 text-center">
        {train.doors_open ? <span className="text-green-500 font-medium">OPEN</span> : "—"}
      </td>
    </tr>
  );
}

function LineSection({
  line,
  lineTrains,
  lineStations,
  terminalUp,
  terminalDown,
}: {
  line: string;
  lineTrains: TrainDebugPosition[];
  lineStations: { station_name: string; at_platform: number; approaching: number }[];
  terminalUp: string;
  terminalDown: string;
}) {
  const [expanded, setExpanded] = useState(true);
  const atPlatform = lineTrains.filter((t) => t.is_at_platform).length;
  const inTransit = lineTrains.length - atPlatform;
  const lineName = lineTrains[0]?.line_name || line;
  const color = LINE_COLORS[line] || "";

  return (
    <div className="card overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex w-full items-center justify-between px-4 py-3 text-left hover:bg-surface-50 dark:hover:bg-surface-800/50"
      >
        <div className="flex items-center gap-3">
          <span className={`text-lg font-bold ${color}`}>{lineName}</span>
          <span className="text-sm font-medium text-surface-600 dark:text-surface-400">
            {lineTrains.length} active
          </span>
        </div>
        <div className="flex items-center gap-4 text-xs text-surface-500">
          <span>{atPlatform} at platform</span>
          <span>{inTransit} in transit</span>
          <span className="text-surface-400">{expanded ? "▲" : "▼"}</span>
        </div>
      </button>

      {expanded && (
        <div className="overflow-x-auto">
          <table className="w-full whitespace-nowrap">
            <thead>
              <tr className="border-y border-surface-200 bg-surface-50 text-xs font-semibold uppercase text-surface-500 dark:border-surface-700 dark:bg-surface-800/50">
                <th className="px-2 py-1.5 text-left">#</th>
                <th className="px-2 py-1.5 text-left">ID</th>
                <th className="px-2 py-1.5 text-left">Line</th>
                <th className="px-2 py-1.5 text-left">Direction</th>
                <th className="px-2 py-1.5 text-left">Status</th>
                <th className="px-2 py-1.5 text-left">Speed</th>
                <th className="px-2 py-1.5 text-left">Occupancy</th>
                <th className="px-2 py-1.5 text-left">Location</th>
                <th className="px-2 py-1.5 text-left">Dist</th>
                <th className="px-2 py-1.5 text-left">ETA</th>
                <th className="px-2 py-1.5 text-center">Doors</th>
              </tr>
            </thead>
            <tbody>
              {lineTrains.length === 0 ? (
                <tr>
                  <td colSpan={11} className="px-4 py-6 text-center text-sm text-surface-400">
                    No active trains
                  </td>
                </tr>
              ) : (
                lineTrains.map((t, i) => (
                  <TrainRow key={t.train_id} train={t} seq={i + 1} />
                ))
              )}
            </tbody>
          </table>

          {lineStations.length > 0 && (
            <details className="border-t border-surface-200 dark:border-surface-700">
              <summary className="cursor-pointer px-4 py-2 text-xs font-medium text-surface-500 hover:text-surface-700 dark:hover:text-surface-300">
                Station Summary ({lineStations.length})
              </summary>
              <div className="overflow-x-auto px-4 pb-3">
                <table className="w-full whitespace-nowrap text-xs">
                  <thead>
                    <tr className="text-surface-500">
                      <th className="pr-4 text-left font-medium">Station</th>
                      <th className="pr-4 text-left font-medium">At Platform</th>
                      <th className="text-left font-medium">Approaching</th>
                    </tr>
                  </thead>
                  <tbody>
                    {lineStations.map((s) => (
                      <tr key={s.station_name} className="hover:bg-surface-50 dark:hover:bg-surface-800/30">
                        <td className="pr-4 py-0.5 font-medium">{s.station_name}</td>
                        <td className="pr-4 py-0.5">{s.at_platform}</td>
                        <td className="py-0.5">{s.approaching}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </details>
          )}
        </div>
      )}
    </div>
  );
}

export default function TrainsDebugPage() {
  const [autoRefresh, setAutoRefresh] = useState(true);

  const { data, error, isLoading, refetch } = useQuery<TrainPositionsResponse>({
    queryKey: ["train-positions"],
    queryFn: () => api.simulation.trainPositions(),
    refetchInterval: autoRefresh ? 5000 : false,
  });

  return (
    <div className="flex h-full flex-col gap-4 overflow-y-auto p-4">
      <div className="flex items-center justify-between">
        <h1 className="text-lg font-bold">Train Positions — Per-Train Diagnostic</h1>
        <div className="flex items-center gap-3 text-sm">
          <label className="flex items-center gap-1.5">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="rounded"
            />
            Auto-refresh (5s)
          </label>
          <button
            onClick={() => refetch()}
            className="btn-ghost rounded px-2.5 py-1 text-xs font-medium"
          >
            Refresh
          </button>
        </div>
      </div>

      {data && (
        <div className="flex flex-wrap gap-3 text-xs text-surface-500">
          <span>Generated at: <strong>{data.ist_time}</strong></span>
          <span>Sim time: <strong>{data.generated_at_s.toFixed(0)}s</strong></span>
          <span>Period: <strong>{data.service_period}</strong></span>
          <span>Total: <strong>{data.total_trains}</strong></span>
          <span>Active: <strong>{data.total_active}</strong></span>
        </div>
      )}

      {isLoading && <div className="py-8 text-center text-sm text-surface-400">Loading…</div>}

      {error && (
        <div className="rounded border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
          Failed to load train positions: {(error as Error).message}
        </div>
      )}

      {data && (
        <div className="flex flex-col gap-3">
          {data.lines.map((lg) => (
            <LineSection
              key={lg.line_code}
              line={lg.line_code}
              lineTrains={lg.active_trains}
              lineStations={lg.station_summary}
              terminalUp={lg.terminal_up}
              terminalDown={lg.terminal_down}
            />
          ))}
          {data.lines.length === 0 && (
            <div className="py-8 text-center text-sm text-surface-400">
              No lines with active trains. Is the simulation running?
            </div>
          )}
        </div>
      )}
    </div>
  );
}
