"use client";

import { useEffect, useRef, useMemo, useCallback } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import { Deck } from "@deck.gl/core";
import { ScatterplotLayer, LineLayer, TextLayer } from "@deck.gl/layers";
import { useSimulationStore } from "@/stores/simulation";
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
}

export function LiveMap({ lines, stations, onStationClick, onTrainClick }: LiveMapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckRef = useRef<Deck | null>(null);
  const { trains } = useSimulationStore();

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
          if (info.object) onStationClick((info.object as StationList).id);
        },
      }),
    [stations, onStationClick],
  );

  const stationLabelLayer = useMemo(
    () =>
      new TextLayer<StationList>({
        id: "station-labels",
        data: stations,
        getPosition: (d) => [d.longitude, d.latitude],
        getText: (d) => d.code,
        getSize: 10,
        getColor: [255, 255, 255, 200],
        getTextAnchor: "start",
        getAlignmentBaseline: "bottom",
        billboard: true,
        sizeUnits: "meters",
        sizeScale: 1,
        fontFamily: "monospace",
      }),
    [stations],
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

    const deck = new Deck({
      canvas: undefined,
      width: "100%",
      height: "100%",
      initialViewState: INITIAL_VIEW,
      controller: false,
      layers: [],
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

    map.on("load", () => {
      const container = map.getCanvasContainer();
      if (container) deck.setProps({ parent: container as HTMLDivElement });
    });

    return () => {
      deck.finalize();
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

  return <div ref={mapContainer} className="h-full w-full" />;
}
