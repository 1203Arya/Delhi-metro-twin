"use client";

import { useEffect, useRef, useCallback } from "react";
import { useSimulationStore } from "@/stores/simulation";
import type { WSMessage } from "@/types/api";

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/api/v1";

export function useWebSocket(lineCode?: string) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const { setTrains, setMetrics, setTick } = useSimulationStore();

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
  }, [lineCode, setTrains, setMetrics, setTick]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimeout.current);
      wsRef.current?.close();
    };
  }, [connect]);
}
