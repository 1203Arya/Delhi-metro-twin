"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { LoadingSpinner } from "@/components/ui/LoadingSpinner";
import type { StationDetail } from "@/types/api";

interface StationPanelProps {
  stationId: string;
  onClose: () => void;
}

export function StationPanel({ stationId, onClose }: StationPanelProps) {
  const { data: station, isLoading } = useQuery<StationDetail>({
    queryKey: ["station", stationId],
    queryFn: () => api.stations.get(stationId),
  });

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">Station Details</h3>
        <button onClick={onClose} className="btn-ghost p-1 text-xs">✕</button>
      </div>

      {isLoading ? (
        <div className="flex justify-center py-8"><LoadingSpinner /></div>
      ) : station ? (
        <div className="space-y-2 text-xs">
          <Row label="Name" value={station.name} />
          <Row label="Code" value={station.code} />
          <Row label="Line" value={station.line_code} />
          <Row label="Sequence" value={String(station.sequence)} />
          <Row label="Structure" value={station.structure} />
          <Row label="Platforms" value={String(station.platforms)} />
          <Row label="Terminus" value={station.is_terminus ? "Yes" : "No"} />
          <Row label="Junction" value={station.has_junction ? "Yes" : "No"} />
          <Row label="Opened" value={String(station.opened_year)} />
          <Row label="Latitude" value={station.latitude.toFixed(4)} />
          <Row label="Longitude" value={station.longitude.toFixed(4)} />
        </div>
      ) : (
        <p className="py-4 text-center text-xs text-surface-400">Station not found</p>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-surface-500">{label}</span>
      <span className="font-medium">{value}</span>
    </div>
  );
}
