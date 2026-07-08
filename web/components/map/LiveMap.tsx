"use client";

import { useEffect, useRef, useMemo, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Deck } from "@deck.gl/core";
import { ScatterplotLayer, TextLayer } from "@deck.gl/layers";
import { useSimulationStore } from "@/stores/simulation";
import { MapControls } from "@/components/map/MapControls";
import type { LineList, StationList, TrainPosition } from "@/types/api";

const INITIAL_VIEW = {
  longitude: 77.2,
  latitude: 28.6,
  zoom: 11,
  pitch: 45,
  bearing: 0,
};

const LINE_COLORS: Record<string, [number, number, number, number]> = {
  RD: [239, 68, 68, 200],
  YL: [234, 179, 8, 200],
  BL: [59, 130, 246, 200],
  GR: [34, 197, 94, 200],
  BR: [139, 92, 246, 200],
  VL: [236, 72, 153, 200],
  PK: [249, 115, 22, 200],
  MG: [132, 204, 22, 200],
  GY: [107, 114, 128, 200],
  OR: [251, 146, 60, 200],
  RM: [20, 184, 166, 200],
};

function getLineColor(code: string): [number, number, number, number] {
  return LINE_COLORS[code] || [100, 100, 100, 200];
}

interface LiveMapProps {
  lines: LineList[];
  stations: StationList[];
  onStationClick: (id: string) => void;
  onTrainClick: (id: string) => void;
  showLabels: boolean;
  announcementsOn: boolean;
  onToggleLabels: () => void;
  onToggleAnnouncements: () => void;
  selectedStationCode: string | null;
  onSelectStation: (station: StationList) => void;
  onDisruptStation: (station: StationList) => void;
  disrupting: boolean;
}

export function LiveMap({
  lines,
  stations,
  onStationClick,
  onTrainClick,
  showLabels,
  announcementsOn,
  onToggleLabels,
  onToggleAnnouncements,
  selectedStationCode,
  onSelectStation,
  onDisruptStation,
  disrupting,
}: LiveMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckRef = useRef<Deck | null>(null);
  const latestLayersRef = useRef<any[]>([null, null, null, null]);
  const { trains } = useSimulationStore();

  const resetView = useCallback(() => {
    mapRef.current?.flyTo({
      center: [INITIAL_VIEW.longitude, INITIAL_VIEW.latitude],
      zoom: INITIAL_VIEW.zoom,
      pitch: INITIAL_VIEW.pitch,
      bearing: INITIAL_VIEW.bearing,
      duration: 1000,
    });
  }, []);

  const flyToStation = useCallback((lat: number, lng: number) => {
    mapRef.current?.flyTo({
      center: [lng, lat],
      zoom: 16,
      pitch: 60,
      bearing: 0,
      duration: 1200,
    });
  }, []);

  const stationLayer = useMemo(
    () =>
      new ScatterplotLayer<StationList>({
        id: "stations",
        data: stations,
        getPosition: (d) => [d.longitude, d.latitude],
        getRadius: 120,
        getFillColor: [100, 150, 255, 180],
        getLineColor: [255, 255, 255, 200],
        lineWidthMinPixels: 1,
        stroked: true,
        pickable: true,
        onClick: (info) => {
          if (info.object) {
            const st = info.object as StationList;
            onStationClick(st.id);
            flyToStation(st.latitude, st.longitude);
            onSelectStation(st);
          }
        },
      }),
    [stations, onStationClick, flyToStation, onSelectStation],
  );

  const stationLabelLayer = useMemo(
    () =>
      new TextLayer<StationList>({
        id: "station-labels",
        data: showLabels ? stations : [],
        getPosition: (d) => [d.longitude, d.latitude],
        getText: (d) => d.name,
        getSize: 10,
        getColor: [255, 255, 255, 200],
        getTextAnchor: "start",
        getAlignmentBaseline: "bottom",
        billboard: true,
        sizeUnits: "meters",
        sizeScale: 1,
        fontFamily: "monospace",
      }),
    [stations, showLabels],
  );

  const trainLayer = useMemo(
    () =>
      new ScatterplotLayer<TrainPosition>({
        id: "trains",
        data: trains,
        getPosition: (d) => {
          const station = stations.find((s) => s.code === d.current_station);
          const next = stations.find((s) => s.code === d.next_station);
          if (station && next) {
            const ratio = d.position_m / 1000;
            return [
              station.longitude + (next.longitude - station.longitude) * 0.3,
              station.latitude + (next.latitude - station.latitude) * 0.3,
            ] as [number, number];
          }
          return station ? [station.longitude, station.latitude] : [77.2, 28.6];
        },
        getRadius: 180,
        getFillColor: (d) => getLineColor(d.line_code),
        getLineColor: [255, 255, 255, 220],
        lineWidthMinPixels: 1.5,
        stroked: true,
        pickable: true,
        onClick: (info) => {
          if (info.object) onTrainClick((info.object as TrainPosition).train_id);
        },
      }),
    [trains, stations, onTrainClick],
  );

  const trainLabelLayer = useMemo(
    () =>
      new TextLayer<TrainPosition>({
        id: "train-labels",
        data: trains,
        getPosition: (d) => {
          const station = stations.find((s) => s.code === d.current_station);
          const next = stations.find((s) => s.code === d.next_station);
          if (station && next) {
            return [
              station.longitude + (next.longitude - station.longitude) * 0.3 + 0.005,
              station.latitude + (next.latitude - station.latitude) * 0.3,
            ] as [number, number];
          }
          return station ? [station.longitude + 0.005, station.latitude] : [77.2, 28.6];
        },
        getText: (d) => d.train_id,
        getSize: 9,
        getColor: (d) => getLineColor(d.line_code),
        getTextAnchor: "start",
        billboard: true,
        sizeUnits: "meters",
        sizeScale: 1,
        fontFamily: "monospace",
      }),
    [trains, stations],
  );

  latestLayersRef.current = [stationLayer, trainLayer, stationLabelLayer, trainLabelLayer];

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
      center: [INITIAL_VIEW.longitude, INITIAL_VIEW.latitude],
      zoom: INITIAL_VIEW.zoom,
      pitch: INITIAL_VIEW.pitch,
      bearing: INITIAL_VIEW.bearing,
      attributionControl: false,
    });

    map.addControl(new maplibregl.NavigationControl(), "top-left");
    map.addControl(new maplibregl.ScaleControl(), "bottom-left");
    mapRef.current = map;

    let deck: Deck | null = null;

    map.on("load", () => {
      const container = map.getCanvasContainer();
      if (!container) return;
      deck = new Deck({
        parent: container as HTMLDivElement,
        width: "100%",
        height: "100%",
        initialViewState: INITIAL_VIEW,
        controller: false,
        layers: latestLayersRef.current,
        onViewStateChange: ({ viewState }) => {
          map.jumpTo({
            center: [viewState.longitude, viewState.latitude],
            zoom: viewState.zoom,
            bearing: viewState.bearing,
            pitch: viewState.pitch,
          });
        },
      });
      deckRef.current = deck;
    });

    return () => {
      if (deck) deck.finalize();
      map.remove();
      mapRef.current = null;
      deckRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (deckRef.current) {
      deckRef.current.setProps({
        layers: [stationLayer, trainLayer, stationLabelLayer, trainLabelLayer],
      });
    }
  }, [stationLayer, trainLayer, stationLabelLayer, trainLabelLayer]);

  return (
    <div className="relative h-full w-full">
      <MapControls
        showLabels={showLabels}
        onToggleLabels={onToggleLabels}
        onResetView={resetView}
        announcementsOn={announcementsOn}
        onToggleAnnouncements={onToggleAnnouncements}
        stations={stations}
        selectedStationCode={selectedStationCode}
        onFlyToStation={flyToStation}
        onSelectStation={onSelectStation}
        onDisruptStation={onDisruptStation}
        disrupting={disrupting}
      />
      <div ref={mapContainer} className="h-full w-full" />
    </div>
  );
}
