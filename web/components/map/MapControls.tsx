"use client";

import { StationSearch } from "./StationSearch";
import type { StationList } from "@/types/api";

interface MapControlsProps {
  showLabels: boolean;
  onToggleLabels: () => void;
  onResetView: () => void;
  announcementsOn: boolean;
  onToggleAnnouncements: () => void;
  stations: StationList[];
  selectedStationCode: string | null;
  onFlyToStation: (lat: number, lng: number) => void;
  onSelectStation: (station: StationList) => void;
  onDisruptStation: (station: StationList) => void;
  disrupting: boolean;
}

export function MapControls({
  showLabels,
  onToggleLabels,
  onResetView,
  announcementsOn,
  onToggleAnnouncements,
  stations,
  selectedStationCode,
  onFlyToStation,
  onSelectStation,
  onDisruptStation,
  disrupting,
}: MapControlsProps) {
  const selectedStation = stations.find((s) => s.code === selectedStationCode) || null;

  return (
    <div className="absolute left-2 top-2 z-20 flex items-center gap-2 rounded-lg border border-surface-300 bg-white/90 px-3 py-2 shadow-sm backdrop-blur-sm dark:border-surface-600 dark:bg-surface-800/90">
      <button
        className={`btn text-xs ${showLabels ? "btn-primary" : "btn-ghost"}`}
        onClick={onToggleLabels}
      >
        Labels: {showLabels ? "On" : "Off"}
      </button>
      <div className="h-4 w-px bg-surface-300 dark:bg-surface-600" />
      <button className="btn btn-ghost text-xs" onClick={onResetView}>
        Reset view
      </button>
      <div className="h-4 w-px bg-surface-300 dark:bg-surface-600" />
      <button
        className={`btn text-xs ${announcementsOn ? "btn-primary" : "btn-ghost"}`}
        onClick={onToggleAnnouncements}
      >
        Announcements: {announcementsOn ? "On" : "Off"}
      </button>
      <div className="h-4 w-px bg-surface-300 dark:bg-surface-600" />
      <StationSearch
        stations={stations}
        selectedCode={selectedStationCode}
        onSelect={(s) => {
          onSelectStation(s);
          onFlyToStation(s.latitude, s.longitude);
        }}
      />
      <div className="h-4 w-px bg-surface-300 dark:bg-surface-600" />
      <button
        className={`btn text-xs ${selectedStation ? "btn-primary" : "btn-ghost"} ${disrupting ? "cursor-wait opacity-60" : ""}`}
        disabled={!selectedStation || disrupting}
        onClick={() => selectedStation && onDisruptStation(selectedStation)}
      >
        {disrupting
          ? "Disrupting..."
          : selectedStation
            ? `Disrupt at ${selectedStation.name}`
            : "Disrupt at ..."}
      </button>
    </div>
  );
}
