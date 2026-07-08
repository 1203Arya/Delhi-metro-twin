"use client";

import { useEffect, useRef, useCallback } from "react";
import { useSimulationStore } from "@/stores/simulation";
import type { WSMessage } from "@/types/api";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || "/api/v1";

export function useWebSocket(lineCode?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { setTrains, setMetrics, setTick, setState, setSimStats, setServiceMeta } = useSimulationStore();

  const connect = useCallback(() => {
    const path = lineCode ? `/ws/simulation/${lineCode}` : "/ws/simulation";
    const url = `${WS_BASE}${path}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg: WSMessage = JSON.parse(event.data);
        if (msg.type === "position_update") {
          setTrains(msg.trains);
          setMetrics(msg.metrics);
          setTick(msg.tick, msg.time_s);
          setSimStats(msg.completed_passengers, msg.active_incidents, msg.passengers);
          setState({
            running: msg.running,
            paused: msg.paused,
            time_s: msg.time_s,
            trains: msg.total_trains ?? msg.trains.length,
            active_trains: msg.active_trains,
            depot_trains: msg.depot_trains,
            passengers: msg.passengers,
            completed_passengers: msg.completed_passengers,
            active_incidents: msg.active_incidents,
            service_period: msg.service_period,
            ist_time: msg.ist_time,
            service_start: "",
            service_end: "",
          });
          setServiceMeta(msg.ist_time, msg.service_period, msg.depot_trains);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      reconnectTimeout.current = setTimeout(connect, 2000);
    };

    ws.onerror = () => {
      ws.close();
    };
  }, [lineCode, setTrains, setMetrics, setTick, setState, setServiceMeta]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
