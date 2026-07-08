"use client";

import { useEffect, useRef, useMemo } from "react";
import { Deck } from "@deck.gl/core";
import {
  ScatterplotLayer,
  LineLayer,
  PolygonLayer,
  TextLayer,
} from "@deck.gl/layers";
import { useQuery } from "@tanstack/react-query";
import { useSimulationStore } from "@/stores/simulation";
import { api } from "@/lib/api";
import type { StationList, TrackSegmentList, LineWithStations } from "@/types/api";

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

function bearing(
  lat1: number,
  lng1: number,
  lat2: number,
  lng2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const toDeg = (r: number) => (r * 180) / Math.PI;
  const dLng = toRad(lng2 - lng1);
  const y = Math.sin(dLng) * Math.cos(toRad(lat2));
  const x =
    Math.cos(toRad(lat1)) * Math.sin(toRad(lat2)) -
    Math.sin(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.cos(dLng);
  return (toDeg(Math.atan2(y, x)) + 360) % 360;
}

function offsetMeters(
  lat: number,
  lng: number,
  dx: number,
  dy: number,
): [number, number] {
  const dLat = dy / 111320;
  const dLng = dx / (111320 * Math.cos((lat * Math.PI) / 180));
  return [lng + dLng, lat + dLat];
}

const HALF_PLATFORM_LENGTH = 100;
const HALF_PLATFORM_WIDTH = 7;

interface StationViewProps {
  station: StationList;
  allStations: StationList[];
  tracks: TrackSegmentList[];
  onBack: () => void;
}

export function StationView({
  station,
  allStations,
  tracks,
  onBack,
}: StationViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const deckRef = useRef<Deck | null>(null);
  const { trains } = useSimulationStore();

  const { data: lineData } = useQuery({
    queryKey: ["line-stations", station.line_code],
    queryFn: () => api.lines.stations(station.line_code),
  });

  const approachingTrains = useMemo(
    () => trains.filter((t) =>
      t.next_station === station.code && t.line_code === station.line_code
    ),
    [trains, station.code, station.line_code],
  );

  const lineStations = useMemo(() => lineData?.stations || [], [lineData]);
  const lineStationCodes = useMemo(() => {
    return lineStations
      .sort((a, b) => a.sequence - b.sequence)
      .map((s) => s.code);
  }, [lineStations]);

  const lineStationNames = useMemo(() => {
    const map: Record<string, string> = {};
    for (const s of lineStations) {
      map[s.code] = s.name;
    }
    return map;
  }, [lineStations]);

  const upTerminusName = lineStations.length > 0 ? lineStations[lineStations.length - 1]?.name || "" : "";
  const downTerminusName = lineStations.length > 0 ? lineStations[0]?.name || "" : "";

  const departureBoard = useMemo(() => {
    const stationIdx = lineStationCodes.indexOf(station.code);
    const headingToward = (t: typeof approachingTrains[number]) => {
      const curIdx = lineStationCodes.indexOf(t.current_station);
      if (curIdx < 0) return true;
      return t.direction === "up" ? curIdx < stationIdx : curIdx > stationIdx;
    };
    const sorted = [...approachingTrains]
      .filter((t) => t.status !== "completed" && headingToward(t))
      .sort((a, b) => {
        const idxA = lineStationCodes.indexOf(a.current_station);
        const idxB = lineStationCodes.indexOf(b.current_station);
        return (
          Math.abs(idxA - stationIdx) - Math.abs(idxB - stationIdx)
        );
      })
      .slice(0, 8);

    return sorted.map((t) => {
      const idx = lineStationCodes.indexOf(t.current_station);
      const seqDiff = Math.abs(idx - stationIdx);
      const platform = t.direction === "up" ? 1 : 2;
      const destination =
        t.direction === "up" ? upTerminusName : downTerminusName;
      const eta =
        t.doors_open || t.speed_kmh < 0.5
          ? "At platform"
          : seqDiff <= 1
            ? "~1 min"
            : seqDiff <= 2
              ? "~2 min"
              : seqDiff <= 3
                ? "~3 min"
                : seqDiff <= 5
                  ? "~5 min"
                  : ">5 min";

      return {
        trainId: t.train_id,
        platform,
        destination,
        lineCode: t.line_code,
        eta,
        status: t.status,
      };
    });
  }, [approachingTrains, lineStationCodes, station.code, upTerminusName, downTerminusName]);

  const platformBearing = useMemo(() => {
    const sorted = allStations
      .filter((s) => s.line_code === station.line_code)
      .sort((a, b) => a.sequence - b.sequence);
    const idx = sorted.findIndex((s) => s.id === station.id);
    if (idx < 0) return 0;
    const prev = idx > 0 ? sorted[idx - 1] : null;
    const next = idx < sorted.length - 1 ? sorted[idx + 1] : null;
    if (prev && next) {
      const b1 = bearing(
        prev.latitude,
        prev.longitude,
        station.latitude,
        station.longitude,
      );
      const b2 = bearing(
        station.latitude,
        station.longitude,
        next.latitude,
        next.longitude,
      );
      return (b1 + b2) / 2;
    }
    if (prev)
      return bearing(
        prev.latitude,
        prev.longitude,
        station.latitude,
        station.longitude,
      );
    if (next)
      return bearing(
        station.latitude,
        station.longitude,
        next.latitude,
        next.longitude,
      );
    return 0;
  }, [station, allStations]);

  const approaches = useMemo(() => {
    const stId = station.id;
    return tracks
      .filter((t) => t.from_station_id === stId || t.to_station_id === stId)
      .map((t) => {
        if (t.to_station_id === stId) {
          return {
            bearing: t.heading_in_deg,
            line_code: t.line_code,
            direction: t.direction,
          };
        }
        return {
          bearing: (t.heading_out_deg + 180) % 360,
          line_code: t.line_code,
          direction: `reverse_${t.direction}`,
        };
      });
  }, [station, tracks]);

  const platformCorners = useMemo(() => {
    const rad = (platformBearing * Math.PI) / 180;
    const alongX = Math.sin(rad) * HALF_PLATFORM_LENGTH;
    const alongY = Math.cos(rad) * HALF_PLATFORM_LENGTH;
    const perpX = Math.cos(rad) * HALF_PLATFORM_WIDTH;
    const perpY = -Math.sin(rad) * HALF_PLATFORM_WIDTH;
    return [
      offsetMeters(station.latitude, station.longitude, alongX + perpX, alongY + perpY),
      offsetMeters(station.latitude, station.longitude, alongX - perpX, alongY - perpY),
      offsetMeters(station.latitude, station.longitude, -alongX - perpX, -alongY - perpY),
      offsetMeters(station.latitude, station.longitude, -alongX + perpX, -alongY + perpY),
    ];
  }, [station, platformBearing]);

  const passengerPositions = useMemo(() => {
    const count = 30 + Math.floor(Math.random() * 20);
    const positions: [number, number][] = [];
    for (let i = 0; i < count; i++) {
      const along = (Math.random() - 0.5) * 2 * HALF_PLATFORM_LENGTH * 0.8;
      const across = (Math.random() - 0.5) * 2 * HALF_PLATFORM_WIDTH * 0.6;
      const rad = (platformBearing * Math.PI) / 180;
      const dx = Math.sin(rad) * along + Math.cos(rad) * across;
      const dy = Math.cos(rad) * along - Math.sin(rad) * across;
      positions.push(offsetMeters(station.latitude, station.longitude, dx, dy));
    }
    return positions;
  }, [station, platformBearing]);

  const approachBeams = useMemo(() => {
    return approaches.map((a) => {
      const rad = (a.bearing * Math.PI) / 180;
      const distDeg =
        400 /
        (111320 * Math.cos((station.latitude * Math.PI) / 180));
      return {
        source: [
          station.longitude - Math.sin(rad) * distDeg,
          station.latitude -
            (Math.cos(rad) * 400) / 111320,
        ] as [number, number],
        target: [station.longitude, station.latitude] as [number, number],
        line_code: a.line_code,
      };
    });
  }, [approaches, station]);

  const platformLayer = useMemo(
    () =>
      new PolygonLayer({
        id: "platform",
        data: [{ polygon: platformCorners }],
        getPolygon: (d) => d.polygon,
        getFillColor: [180, 190, 200, 220],
        getLineColor: [255, 255, 255, 200],
        lineWidthMinPixels: 2,
        extruded: true,
        getElevation: 0.5,
      }),
    [platformCorners],
  );

  const passengerLayer = useMemo(
    () =>
      new ScatterplotLayer({
        id: "passengers",
        data: passengerPositions,
        getPosition: (d) => d,
        getRadius: 1.8,
        getFillColor: [255, 220, 80, 200],
        radiusUnits: "meters",
        radiusMinPixels: 2,
      }),
    [passengerPositions],
  );

  const approachLayer = useMemo(
    () =>
      new LineLayer({
        id: "approach-beams",
        data: approachBeams,
        getSourcePosition: (d) => d.source,
        getTargetPosition: (d) => d.target,
        getColor: (d) => getLineColor(d.line_code),
        getWidth: 3,
        widthUnits: "pixels",
      }),
    [approachBeams],
  );

  const platformLabelLayer = useMemo(
    () =>
      new TextLayer({
        id: "platform-label",
        data: [
          { pos: offsetMeters(station.latitude, station.longitude, 0, -HALF_PLATFORM_WIDTH - 15), text: `Platform ${station.name}` },
        ],
        getPosition: (d) => d.pos,
        getText: (d) => d.text,
        getSize: 14,
        getColor: [255, 255, 255, 200],
        billboard: true,
        fontFamily: "monospace",
      }),
    [station],
  );

  useEffect(() => {
    if (!containerRef.current || deckRef.current) return;

    const deck = new Deck({
      parent: containerRef.current,
      width: "100%",
      height: "100%",
      initialViewState: {
        longitude: station.longitude,
        latitude: station.latitude,
        zoom: 17,
        pitch: 65,
        bearing: platformBearing - 30,
      },
      controller: true,
      layers: [
        platformLayer,
        passengerLayer,
        approachLayer,
        platformLabelLayer,
      ],
    });
    deckRef.current = deck;

    return () => {
      deck.finalize();
      deckRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (deckRef.current) {
      deckRef.current.setProps({
        layers: [
          platformLayer,
          passengerLayer,
          approachLayer,
          platformLabelLayer,
        ],
      });
    }
  }, [platformLayer, passengerLayer, approachLayer, platformLabelLayer]);

  return (
    <div className="relative h-full w-full bg-[#0a0a0f]">
      <div ref={containerRef} className="h-full w-full" />

      <button
        onClick={onBack}
        className="absolute left-4 top-4 z-30 rounded-lg border border-surface-600 bg-black/70 px-4 py-2 text-sm font-medium text-white backdrop-blur-sm hover:bg-black/90"
      >
        ← Network
      </button>

      <div className="absolute right-4 top-4 z-30 w-96 rounded-lg border border-white/10 bg-black/85 p-4 text-white shadow-2xl backdrop-blur-md">
        <div className="mb-3 flex items-center justify-between border-b border-yellow-400/60 pb-2">
          <div>
            <span className="text-lg font-bold tracking-wider">
              {station.name}
            </span>
            <span className="ml-2 rounded bg-yellow-400/20 px-2 py-0.5 font-mono text-xs text-yellow-400">
              {station.code}
            </span>
          </div>
          <span className="text-xs text-gray-400">
            {station.line_code} Line · Platform {station.platforms}
          </span>
        </div>

        <div className="mb-1 grid grid-cols-4 gap-2 text-[10px] font-semibold uppercase tracking-widest text-yellow-400">
          <span>Platform</span>
          <span>Destination</span>
          <span>Type</span>
          <span className="text-right">Arrival</span>
        </div>

        {departureBoard.length === 0 ? (
          <div className="flex items-center justify-center py-8 text-sm text-gray-500">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-yellow-400" />
              No approaching trains
            </div>
          </div>
        ) : (
          <div className="space-y-0.5">
            {departureBoard.map((row) => (
              <div
                key={row.trainId}
                className="grid grid-cols-4 gap-2 border-t border-gray-800/50 py-1.5 text-sm"
              >
                <span className="font-mono text-yellow-400">
                  {row.platform}
                </span>
                <span className="truncate text-white">
                  {row.destination || `${row.lineCode} Line`}
                </span>
                <span
                  className="truncate font-mono text-xs"
                  style={{
                    color: `rgba(${getLineColor(row.lineCode).join(",")})`,
                  }}
                >
                  {row.lineCode}
                </span>
                <span className="text-right font-mono text-xs text-green-400">
                  {row.eta}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="absolute bottom-4 right-4 z-30 text-[10px] text-gray-600">
        Station View · {approachingTrains.length} train{approachingTrains.length !== 1 ? "s" : ""} approaching
      </div>
    </div>
  );
}
