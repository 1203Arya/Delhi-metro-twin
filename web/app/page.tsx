"use client";

import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { LiveMap } from "@/components/map/LiveMap";
import { StationView } from "@/components/station/StationView";
import { StationLiveTracker } from "@/components/station/StationLiveTracker";
import { StationPanel } from "@/components/panels/StationPanel";
import { TrainPanel } from "@/components/panels/TrainPanel";
import { SignalPanel } from "@/components/panels/SignalPanel";
import { IncidentPanel } from "@/components/panels/IncidentPanel";
import { NetworkHealthPanel } from "@/components/panels/NetworkHealthPanel";
import { useWebSocket } from "@/hooks/useWebSocket";
import { useState, useCallback } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { StationList } from "@/types/api";

export default function HomePage() {
  useWebSocket();
  const [selectedStation, setSelectedStation] = useState<string | null>(null);
  const [selectedStationCode, setSelectedStationCode] = useState<string | null>(null);
  const [selectedTrain, setSelectedTrain] = useState<string | null>(null);
  const [showSignalPanel, setShowSignalPanel] = useState(false);
  const [showIncidentPanel, setShowIncidentPanel] = useState(false);
  const [showLabels, setShowLabels] = useState(true);
  const [announcementsOn, setAnnouncementsOn] = useState(false);
  const [disrupting, setDisrupting] = useState(false);
  const [stationView, setStationView] = useState(false);
  const [showStationLiveTracker, setShowStationLiveTracker] = useState(false);

  const { data: linesData } = useQuery({
    queryKey: ["lines"],
    queryFn: () => api.lines.list(),
  });

  const { data: stationsData } = useQuery({
    queryKey: ["stations"],
    queryFn: () => api.stations.list(),
  });

  const { data: tracksData } = useQuery({
    queryKey: ["tracks"],
    queryFn: () => api.tracks.list(),
  });

  const stationsList = stationsData?.items || [];
  const tracksList = tracksData?.items || [];
  const selectedStationObj = stationsList.find((s) => s.code === selectedStationCode) || null;

  const selectAndFlyTo = useCallback(
    (station: StationList) => {
      setSelectedStation(station.id);
      setSelectedStationCode(station.code);
      setShowStationLiveTracker(true);
    },
    [],
  );

  const handleMapStationClick = useCallback(
    (id: string) => {
      setSelectedStation(id);
      const stn = stationsList.find((s) => s.id === id);
      if (stn) setSelectedStationCode(stn.code);
      setShowStationLiveTracker(false);
    },
    [stationsList],
  );

  const handleDisrupt = useCallback(
    async (station: StationList) => {
      setDisrupting(true);
      try {
        await api.simulation.disrupt(station.code, station.line_code, 300);
      } catch (e) {
        console.error("Disrupt failed:", e);
      } finally {
        setDisrupting(false);
      }
    },
    [],
  );

  const handleEnterStationView = useCallback(() => {
    setStationView(true);
  }, []);

  const handleLeaveStationView = useCallback(() => {
    setStationView(false);
  }, []);

  if (stationView && selectedStationObj) {
    return (
      <DashboardLayout>
        <StationView
          station={selectedStationObj}
          allStations={stationsList}
          tracks={tracksList}
          onBack={handleLeaveStationView}
        />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="flex h-full">
        <div className="relative flex-1">
          <LiveMap
            lines={linesData || []}
            stations={stationsList}
            onStationClick={handleMapStationClick}
            onTrainClick={(id) => setSelectedTrain(id)}
            showLabels={showLabels}
            announcementsOn={announcementsOn}
            onToggleLabels={() => setShowLabels((v) => !v)}
            onToggleAnnouncements={() => setAnnouncementsOn((v) => !v)}
            selectedStationCode={selectedStationCode}
            onSelectStation={selectAndFlyTo}
            onDisruptStation={handleDisrupt}
            disrupting={disrupting}
          />

          <div className="absolute right-2 top-2 z-10 flex flex-col gap-2">
            <div className="flex justify-end gap-2">
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
            <div className="self-end">
              <NetworkHealthPanel lines={linesData || []} />
            </div>
          </div>
        </div>

        <div className="flex w-80 flex-col gap-2 overflow-y-auto border-l border-surface-200 bg-white p-2 dark:border-surface-700 dark:bg-surface-900">
          {selectedStation && showStationLiveTracker && selectedStationObj && (
            <div className="flex flex-col gap-2">
              <StationLiveTracker
                station={selectedStationObj}
                onClose={() => { setShowStationLiveTracker(false); setSelectedStation(null); }}
              />
            </div>
          )}
          {selectedStation && !showStationLiveTracker && (
            <StationPanel
              stationId={selectedStation}
              onClose={() => setSelectedStation(null)}
            />
          )}
          {selectedStation && (
            <div className="flex gap-2">
              <button
                className="btn-primary flex-1 text-xs"
                onClick={handleEnterStationView}
              >
                Station View
              </button>
              <button
                className={`btn flex-1 text-xs ${showStationLiveTracker ? "btn-primary" : "btn-ghost"}`}
                onClick={() => setShowStationLiveTracker((v) => !v)}
              >
                Live Tracker
              </button>
            </div>
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
