"use client";

import { useMemo } from "react";
import { useSimulationStore } from "@/stores/simulation";
import type { StationList, TrainPosition } from "@/types/api";

interface StationLiveTrackerProps {
  station: StationList;
  onClose: () => void;
}

const LINE_COLORS: Record<string, string> = {
  RD: "#ef4444",
  YL: "#eab308",
  BL: "#3b82f6",
  GR: "#22c55e",
  BR: "#8b5cf6",
  VL: "#ec4899",
  PK: "#f97316",
  MG: "#84cc16",
  GY: "#6b7280",
  OR: "#fb923c",
  RM: "#14b8a6",
  GB: "#10b981",
};

function formatEta(eta_s: number | undefined): string {
  if (eta_s === undefined || eta_s === null || eta_s <= 0) return "Now";
  if (eta_s < 60) return `${Math.round(eta_s)}s`;
  const min = Math.floor(eta_s / 60);
  const sec = Math.round(eta_s % 60);
  return `${min}m ${sec}s`;
}

function formatSpeed(speed_kmh: number): string {
  if (speed_kmh < 0.5) return "Stopped";
  return `${speed_kmh.toFixed(1)} km/h`;
}

interface ArrivingTrain extends TrainPosition {
  _line_name: string;
}

interface DepartingTrain extends TrainPosition {
  _line_name: string;
  _next_station_name: string;
  _dwell_remaining_s: number;
}

export function StationLiveTracker({ station, onClose }: StationLiveTrackerProps) {
  const trains = useSimulationStore((s) => s.trains);

  const byLine = useMemo(() => {
    const stationName = station.name;
    const stationCode = station.code;

    const arriving: ArrivingTrain[] = [];
    const departing: DepartingTrain[] = [];

    for (const t of trains) {
      if (t.line_code !== station.line_code) continue;
      const tsName = t.next_station_name || "";
      const csName = t.current_station_name || "";
      const matchesNext = tsName === stationName || t.next_station === stationCode;
      const matchesCurrent = csName === stationName || t.current_station === stationCode;
      const atPlatform = t.is_at_platform || t.status === "door_open" || t.status === "stopped" || t.status === "departing";

      if (matchesNext && !matchesCurrent) {
        arriving.push({ ...t, _line_name: t.line_name || t.line_code });
      }

      if (matchesCurrent && atPlatform) {
        const dwellRemaining =
          t.status === "door_open"
            ? t.eta_s ?? 0
            : t.status === "stopped"
              ? t.eta_s ?? 0
              : 0;
        departing.push({
          ...t,
          _line_name: t.line_name || t.line_code,
          _next_station_name: t.next_station_name || t.next_station,
          _dwell_remaining_s: dwellRemaining,
        });
      }
    }

    const isInterchange = arriving.length > 0 || departing.length > 0;
    const lines = new Map<string, { arriving: ArrivingTrain[]; departing: DepartingTrain[] }>();

    const addToLine = (lineKey: string, a: ArrivingTrain | null, d: DepartingTrain | null) => {
      if (!lines.has(lineKey)) lines.set(lineKey, { arriving: [], departing: [] });
      const entry = lines.get(lineKey)!;
      if (a) entry.arriving.push(a);
      if (d) entry.departing.push(d);
    };

    for (const a of arriving) addToLine(a._line_name, a, null);
    for (const d of departing) addToLine(d._line_name, null, d);

    for (const [, entry] of lines) {
      entry.arriving.sort((a, b) => (a.eta_s ?? 9999) - (b.eta_s ?? 9999));
      entry.departing.sort((a, b) => (a._dwell_remaining_s) - (b._dwell_remaining_s));
    }

    const sortedLines = new Map(
      [...lines.entries()].sort((a, b) => {
        const totalA = a[1].arriving.length + a[1].departing.length;
        const totalB = b[1].arriving.length + b[1].departing.length;
        return totalB - totalA;
      }),
    );

    return { isInterchange, lines: sortedLines };
  }, [trains, station]);

  const totalArriving = useMemo(
    () => [...byLine.lines.values()].reduce((s, l) => s + l.arriving.length, 0),
    [byLine],
  );
  const totalDeparting = useMemo(
    () => [...byLine.lines.values()].reduce((s, l) => s + l.departing.length, 0),
    [byLine],
  );

  const hasAny = totalArriving > 0 || totalDeparting > 0;

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 flex items-center justify-between border-b border-surface-200 pb-2 dark:border-surface-700">
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold text-surface-800 dark:text-surface-100">
            {station.name}
          </h3>
          <span className="font-mono text-[10px] text-surface-400">{station.code}</span>
        </div>
        <button
          className="ml-2 shrink-0 rounded p-1 text-surface-400 hover:bg-surface-100 hover:text-surface-600 dark:hover:bg-surface-700 dark:hover:text-surface-300"
          onClick={onClose}
          title="Close"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {!hasAny ? (
        <div className="flex flex-1 items-center justify-center">
          <div className="text-center">
            <div className="mb-1 text-2xl text-surface-300 dark:text-surface-600">🚉</div>
            <p className="text-xs text-surface-400">
              No trains currently approaching or departing
            </p>
            <p className="mt-1 text-[10px] text-surface-300 dark:text-surface-500">
              Check back during peak service hours
            </p>
          </div>
        </div>
      ) : (
        <div className="flex-1 space-y-3 overflow-y-auto">
          {[...byLine.lines.entries()].map(([lineName, entry]) => (
            <div key={lineName}>
              {byLine.isInterchange && (
                <div className="mb-1 flex items-center gap-1.5">
                  {(() => {
                    const lc = [...entry.arriving, ...entry.departing].find(
                      (t) => t.line_code,
                    )?.line_code;
                    return lc ? (
                      <span
                        className="inline-block h-2.5 w-2.5 rounded-full"
                        style={{ backgroundColor: LINE_COLORS[lc] || "#6b7280" }}
                      />
                    ) : null;
                  })()}
                  <span className="text-[10px] font-semibold uppercase tracking-wider text-surface-500 dark:text-surface-400">
                    {lineName}
                  </span>
                </div>
              )}

              {entry.arriving.length > 0 && (
                <div className="mb-2">
                  <h4 className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 11l-3 3m0 0l-3-3m3 3V4m8 8a8 8 0 11-16 0 8 8 0 0116 0z" />
                    </svg>
                    Arriving ({entry.arriving.length})
                  </h4>
                  <div className="space-y-1">
                    {entry.arriving.map((t) => (
                      <div
                        key={t.train_id}
                        className="rounded border border-surface-200 bg-surface-50 px-2.5 py-1.5 dark:border-surface-700 dark:bg-surface-800/50"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span className="truncate font-mono text-[11px] font-medium text-surface-800 dark:text-surface-100">
                                {t.train_id}
                              </span>
                              {!byLine.isInterchange && (
                                <span
                                  className="inline-block h-2 w-2 shrink-0 rounded-full"
                                  style={{ backgroundColor: LINE_COLORS[t.line_code] || "#6b7280" }}
                                />
                              )}
                            </div>
                            <div className="truncate text-[10px] text-surface-400">
                              {t.direction_destination || `${t.direction === "up" ? "UP" : "DOWN"}`}
                            </div>
                          </div>
                          <div className="shrink-0 text-right">
                            <div className="font-mono text-[13px] font-bold text-emerald-600 dark:text-emerald-400">
                              {formatEta(t.eta_s)}
                            </div>
                            <div className="text-[9px] text-surface-400">
                              {t.speed_kmh < 0.5 ? "Stopped" : `${t.speed_kmh.toFixed(0)} km/h`}
                            </div>
                          </div>
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-[9px] text-surface-400">
                          <span title="Occupancy">
                            👥 {t.occupancy}
                          </span>
                          <span title="Status" className="capitalize">
                            {t.status === "door_open"
                              ? "Doors open"
                              : t.status === "stopped" && t.is_at_platform
                                ? "Dwelling"
                                : t.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {entry.departing.length > 0 && (
                <div>
                  <h4 className="mb-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-wider text-amber-600 dark:text-amber-400">
                    <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 12h14m-7-7l7 7-7 7" />
                    </svg>
                    Departing ({entry.departing.length})
                  </h4>
                  <div className="space-y-1">
                    {entry.departing.map((t) => (
                      <div
                        key={t.train_id}
                        className="rounded border border-surface-200 bg-surface-50 px-2.5 py-1.5 dark:border-surface-700 dark:bg-surface-800/50"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <div className="min-w-0 flex-1">
                            <div className="flex items-center gap-1.5">
                              <span className="truncate font-mono text-[11px] font-medium text-surface-800 dark:text-surface-100">
                                {t.train_id}
                              </span>
                              {!byLine.isInterchange && (
                                <span
                                  className="inline-block h-2 w-2 shrink-0 rounded-full"
                                  style={{ backgroundColor: LINE_COLORS[t.line_code] || "#6b7280" }}
                                />
                              )}
                            </div>
                            <div className="truncate text-[10px] text-surface-400">
                              → {t._next_station_name}
                            </div>
                          </div>
                          <div className="shrink-0 text-right">
                            <div className="font-mono text-[13px] font-bold text-amber-600 dark:text-amber-400">
                              {t._dwell_remaining_s > 0 ? formatEta(t._dwell_remaining_s) : "Dooring"}
                            </div>
                            <div className="text-[9px] text-surface-400">
                              {t.doors_open ? "Doors open" : "Boarding"}
                            </div>
                          </div>
                        </div>
                        <div className="mt-1 flex items-center gap-3 text-[9px] text-surface-400">
                          <span title="Occupancy">
                            👥 {t.occupancy}
                          </span>
                          <span title="Destination">
                            {t.direction_destination || `${t.direction === "up" ? "UP" : "DOWN"}`}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-2 border-t border-surface-200 pt-1.5 text-[9px] text-surface-400 dark:border-surface-700">
        Updated live · {totalArriving} arriving, {totalDeparting} departing
      </div>
    </div>
  );
}
