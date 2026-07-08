"use client";

import { useMemo } from "react";
import { useSimulationStore } from "@/stores/simulation";
import type { LineList, StationList } from "@/types/api";

const LINE_COLORS: Record<string, string> = {
  RD: "bg-red-500",
  YL: "bg-yellow-500",
  BL: "bg-blue-500",
  GR: "bg-green-500",
  BR: "bg-purple-500",
  VL: "bg-pink-500",
  PK: "bg-orange-500",
  MG: "bg-lime-500",
  GY: "bg-gray-500",
  OR: "bg-orange-400",
  RM: "bg-teal-500",
};

interface NetworkHealthPanelProps {
  lines: LineList[];
}

export function NetworkHealthPanel({ lines }: NetworkHealthPanelProps) {
  const { trains, state, completed_passengers, active_incidents, time_s } =
    useSimulationStore();

  const activeTrains = state?.active_trains ?? 0;
  const totalTrains = state?.trains ?? 0;

  const disruptedTrains = useMemo(
    () =>
      trains.filter((t) =>
        ["stopped", "emergency_brake", "incident_halt", "turnback"].includes(
          t.status,
        ),
      ).length,
    [trains],
  );

  const runningRatio = totalTrains > 0 ? activeTrains / totalTrains : 0;
  const disruptedRatio =
    totalTrains > 0 ? 1 - disruptedTrains / totalTrains : 1;
  const incidentFactor = 1 - Math.min(1, active_incidents / 10);

  const healthScore = Math.round(
    (runningRatio * 0.5 + disruptedRatio * 0.3 + incidentFactor * 0.2) * 100,
  );

  const healthLabel =
    healthScore >= 90
      ? "All services normal"
      : healthScore >= 70
        ? "Minor delays expected"
        : healthScore >= 50
          ? "Service disruptions"
          : healthScore >= 30
            ? "Major disruptions"
            : "Severe service outage";

  const healthColor =
    healthScore >= 80
      ? "bg-green-500"
      : healthScore >= 60
        ? "bg-yellow-500"
        : healthScore >= 40
          ? "bg-orange-500"
          : "bg-red-500";

  const mostCrowdedStation = useMemo(() => {
    const stationOccupancy: Record<string, { count: number; name: string }> = {};
    for (const t of trains) {
      const code = t.current_station;
      if (code) {
        const prev = stationOccupancy[code] || { count: 0, name: t.current_station_name || code };
        stationOccupancy[code] = { count: prev.count + t.occupancy, name: prev.name };
      }
    }
    let best: string | null = null;
    let bestCount = 0;
    for (const [code, val] of Object.entries(stationOccupancy)) {
      if (val.count > bestCount) {
        bestCount = val.count;
        best = code;
      }
    }
    return best ? { code: best, name: stationOccupancy[best]?.name || best, count: bestCount } : null;
  }, [trains]);

  const passengersPerHour = useMemo(() => {
    if (time_s <= 0) return 0;
    const hours = time_s / 3600;
    return Math.round(completed_passengers / Math.max(1, hours));
  }, [completed_passengers, time_s]);

  const lineBreakdown = useMemo(() => {
    const counts: Record<string, { total: number; active: number }> = {};
    for (const t of trains) {
      if (!counts[t.line_code])
        counts[t.line_code] = { total: 0, active: 0 };
      counts[t.line_code].total++;
      if (t.status === "running") counts[t.line_code].active++;
    }
    return lines
      .map((l) => ({
        code: l.code,
        name: l.name,
        total: counts[l.code]?.total ?? 0,
        active: counts[l.code]?.active ?? 0,
      }))
      .filter((l) => l.total > 0 || lines.find((x) => x.code === l.code));
  }, [trains, lines]);

  return (
    <div className="flex w-72 flex-col gap-3 rounded-lg border border-surface-300 bg-white/95 p-4 shadow-md backdrop-blur-sm dark:border-surface-600 dark:bg-surface-800/95">
      {/* Network Health Score */}
      <div className="text-center">
        <div className="text-xs font-semibold uppercase tracking-wider text-surface-500">
          Network Health
        </div>
        <div className="mt-1 text-4xl font-bold">{healthScore}</div>
        <div className="mt-0.5 text-xs text-surface-500">{healthLabel}</div>
        <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-surface-200 dark:bg-surface-700">
          <div
            className={`h-full rounded-full transition-all duration-1000 ${healthColor}`}
            style={{ width: `${healthScore}%` }}
          />
        </div>
      </div>

      <div className="h-px bg-surface-200 dark:bg-surface-700" />

      {/* Live Stats */}
      <div>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-surface-500">
          Live Stats
        </div>
        <div className="space-y-1.5">
          <StatRow
            label="Trains running"
            value={`${activeTrains} / ${totalTrains}`}
          />
          <StatRow
            label="Avg delay"
            value="N/A — no delay tracking yet"
            muted
          />
          <StatRow
            label="Disrupted trains"
            value={String(disruptedTrains)}
          />
          <StatRow
            label="Most crowded"
            value={
              mostCrowdedStation
                ? `${mostCrowdedStation.name} (${mostCrowdedStation.count} riders)`
                : "—"
            }
          />
          <StatRow
            label="Passengers / sim-hour"
            value={passengersPerHour.toLocaleString()}
          />
        </div>
      </div>

      <div className="h-px bg-surface-200 dark:bg-surface-700" />

      {/* Per-line breakdown */}
      <div>
        <div className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-surface-500">
          Lines
        </div>
        <div className="space-y-1">
          {lineBreakdown.map((l) => (
            <div
              key={l.code}
              className="flex items-center justify-between text-xs"
            >
              <div className="flex items-center gap-2">
                <span
                  className={`inline-block h-2.5 w-2.5 rounded-full ${
                    LINE_COLORS[l.code] || "bg-surface-400"
                  }`}
                />
                <span className="text-surface-700 dark:text-surface-300">
                  {l.name}
                </span>
              </div>
              <span className="font-mono text-surface-500">
                {l.active}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function StatRow({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-surface-500">{label}</span>
      <span
        className={`font-mono ${muted ? "text-surface-400 italic" : "text-surface-700 dark:text-surface-200"}`}
      >
        {value}
      </span>
    </div>
  );
}
