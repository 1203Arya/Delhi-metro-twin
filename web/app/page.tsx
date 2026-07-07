"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { LiveMap } from "@/components/map/LiveMap";
import { StationPanel } from "@/components/panels/StationPanel";
import { TrainPanel } from "@/components/panels/TrainPanel";
import { SignalPanel } from "@/components/panels/SignalPanel";
import { IncidentPanel } from "@/components/panels/IncidentPanel";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export default function HomePage() {
  useWebSocket();
  const [selectedStation, setSelectedStation] = useState<string | null>(null);
  const [selectedTrain, setSelectedTrain] = useState<string | null>(null);
  const [showSignalPanel, setShowSignalPanel] = useState(false);
  const [showIncidentPanel, setShowIncidentPanel] = useState(false);

  const { data: linesData } = useQuery({
    queryKey: ["lines"],
    queryFn: () => api.lines.list(),
  });

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list(),
  });

  return (
    <DashboardLayout>
      <div className="flex h-full">
        <div className="relative flex-1">
          <LiveMap
            lines={linesData || []}
            stations={stationsData?.items || []}
            onStationClick={(id) => setSelectedStation(id)}
            onTrainClick={(id) => setSelectedTrain(id)}
          />

          <div className="absolute right-2 top-2 z-10 flex gap-2">
            <button
              className="btn-secondary text-xs"
              onClick={() => setShowSignalPanel(!showSignalPanel)}
            >
              🚦 Signals
            </button>
            <button
              className="btn-secondary text-xs"
              onClick={() => setShowIncidentPanel(!showIncidentPanel)}
            >
              ⚠ Incidents
            </button>
          </div>
        </div>

        <div className="flex w-80 flex-col gap-2 overflow-y-auto border-l border-surface-200 bg-white p-2 dark:border-surface-700 dark:bg-surface-900">
          {selectedStation && (
            <StationPanel
              stationId={selectedStation}
              onClose={() => setSelectedStation(null)}
            />
          )}
          {selectedTrain && (
            <TrainPanel
              trainId={selectedTrain}
              onClose={() => setSelectedTrain(null)}
            />
          )}
          {showSignalPanel && (
            <SignalPanel onClose={() => setShowSignalPanel(false)} />
          )}
          {showIncidentPanel && (
            <IncidentPanel onClose={() => setShowIncidentPanel(false)} />
          )}
          {!selectedStation && !selectedTrain && !showSignalPanel && !showIncidentPanel && (
            <div className="flex flex-1 items-center justify-center text-center text-xs text-surface-400">
              Click a station or train on the map to view details
            </div>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
