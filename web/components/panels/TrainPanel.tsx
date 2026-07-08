"use client";

import { useSimulationStore } from "@/stores/simulation";

interface TrainPanelProps {
  trainId: string;
  onClose: () => void;
}

export function TrainPanel({ trainId, onClose }: TrainPanelProps) {
  const { trains } = useSimulationStore();
  const train = trains.find((t) => t.train_id === trainId);

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">{train?.train_id || "Train"}</h3>
        <button onClick={onClose} className="btn-ghost p-1 text-xs">✕</button>
      </div>

      {train ? (
        <div className="space-y-2 text-xs">
          <Row label="Status" value={train.status} />
          <Row label="Line" value={train.line_name || train.line_code} />
          <Row label="Direction" value={train.direction_destination || train.direction} />
          <Row label="Speed" value={`${train.speed_kmh.toFixed(0)} km/h`} />
          <Row label="Position" value={`${train.position_m.toFixed(0)} m`} />
          <Row label="Current Station" value={train.current_station_name || train.current_station} />
          <Row label="Next Station" value={train.next_station_name || train.next_station} />
          <Row label="Occupancy" value={`${train.occupancy} pax`} />
          <Row label="Doors" value={train.doors_open ? "Open" : "Closed"} />
          <Row label="Block" value={train.block_id} />
        </div>
      ) : (
        <p className="py-4 text-center text-xs text-surface-400">Train not found</p>
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
