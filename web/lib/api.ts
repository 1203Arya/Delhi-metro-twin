import type {
  ApproachingTrainsResponse,
  HealthResponse,
  TokenResponse,
  LoginRequest,
  LineList,
  LineDetail,
  LineWithStations,
  StationList,
  StationDetail,
  TrackSegmentList,
  TrainClassList,
  DepotList,
  SimulationState,
  SimulationConfig,
  TrainPositionsResponse,
  PaginatedResponse,
} from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

async function request<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init?.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const res = await fetch(`${BASE}${path}`, { ...init, headers });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request<HealthResponse>("/health"),

  auth: {
    login: (body: LoginRequest) =>
      request<TokenResponse>("/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),
  },

  lines: {
    list: (skip = 0, limit = 100) =>
      request<LineList[]>(`/lines?skip=${skip}&limit=${limit}`),
    get: (code: string) => request<LineDetail>(`/lines/${code}`),
    stations: (code: string) =>
      request<LineWithStations>(`/lines/${code}/stations`),
  },

  stations: {
    list: (line_code?: string, skip = 0, limit = 100) => {
      const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
      if (line_code) params.set("line_code", line_code);
      return request<PaginatedResponse<StationList>>(`/stations?${params}`);
    },
    get: (id: string) => request<StationDetail>(`/stations/${id}`),
  },

  tracks: {
    list: (line_code?: string, skip = 0, limit = 100) => {
      const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
      if (line_code) params.set("line_code", line_code);
      return request<PaginatedResponse<TrackSegmentList>>(`/tracks?${params}`);
    },
  },

  trainClasses: {
    list: () => request<TrainClassList[]>("/trains/classes"),
  },

  depots: {
    list: (line_code?: string, skip = 0, limit = 100) => {
      const params = new URLSearchParams({ skip: String(skip), limit: String(limit) });
      if (line_code) params.set("line_code", line_code);
      return request<PaginatedResponse<DepotList>>(`/depots?${params}`);
    },
  },

  simulation: {
    start: (config?: SimulationConfig) =>
      request<{ message: string }>("/simulation/start", {
        method: "POST",
        body: config ? JSON.stringify(config) : undefined,
      }),
    stop: () =>
      request<{ message: string }>("/simulation/stop", { method: "POST" }),
    pause: () =>
      request<{ message: string }>("/simulation/pause", { method: "POST" }),
    resume: () =>
      request<{ message: string }>("/simulation/resume", { method: "POST" }),
    state: () => request<SimulationState>("/simulation/state"),
    snapshots: () => request<Record<string, unknown>[]>("/simulation/snapshots"),
    disrupt: (station_code: string, line_code: string, duration_s = 300) =>
      request<{ message: string }>("/simulation/disrupt", {
        method: "POST",
        body: JSON.stringify({ station_code, line_code, duration_s }),
      }),
    approachingTrains: (code: string) =>
      request<ApproachingTrainsResponse>(`/simulation/station/${code}/approaching`),
    trainPositions: () =>
      request<TrainPositionsResponse>("/simulation/trains/positions"),
  },
};
