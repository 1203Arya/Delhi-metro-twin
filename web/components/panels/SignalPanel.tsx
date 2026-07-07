"use client";

import { useSimulationStore } from "@/stores/simulation";

interface SignalPanelProps {
  onClose: () => void;
}

export function SignalPanel({ onClose }: SignalPanelProps) {
  const { trains, metrics, state } = useSimulationStore();

  return (
    <div className="card">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold">🚦 Signal Status</h3>
        <button onClick={onClose} className="btn-ghost p-1 text-xs">✕</button>
      </div>

      <div className="space-y-3 text-xs">
        <div>
          <h4 className="mb-1 font-medium text-surface-600 dark:text-surface-400">Network Summary</h4>
          <div className="space-y-1">
            <Row label="Active Trains" value={String(state?.active_trains || 0)} />
            <Row label="Avg Headway" value={metrics ? `${metrics.avg_headway_s.toFixed(0)}s` : "N/A"} />
            <Row label="Avg Speed" value={metrics ? `${(metrics.avg_speed_mps * 3.6).toFixed(0)} km/h` : "N/A"} />
            <Row label="Energy" value={metrics ? `${(metrics.total_energy_wh / 1000).toFixed(1)} kWh` : "N/A"} />
          </div>
        </div>

        <div>
          <h4 className="mb-1 font-medium text-surface-600 dark:text-surface-400">Block Status</h4>
          <div className="max-h-40 space-y-1 overflow-y-auto scrollbar-thin">
            {trains.slice(0, 20).map((t) => (
              <div
                key={t.train_id}
                className="flex items-center gap-2 rounded bg-surface-50 p-1.5 dark:bg-surface-800/50"
              >
                <span
                  className={`h-2 w-2 rounded-full ${
                    t.status === "running" ? "bg-green-400" : t.status === "stopped" ? "bg-red-400" : "bg-yellow-400"
                  }`}
                />
                <span className="font-mono text-xs">{t.train_id}</span>
                <span className="font-mono text-xs text-surface-400">{t.block_id}</span>
                <span className="ml-auto text-surface-500">{t.speed_kmh.toFixed(0)} km/h</span>
              </div>
            ))}
          </div>
        </div>
      </div>
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
