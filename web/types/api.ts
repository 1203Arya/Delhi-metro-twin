export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export interface LineList {
  id: string;
  code: string;
  name: string;
  number: number;
  color_hex: string;
  corridor: string;
  opened_year: number;
  operator: string;
  gauge_mm: number;
  electrification: string;
  signalling_system: string;
  total_length_km: number;
  station_count: number;
}

export interface LineDetail extends LineList {
  created_at: string;
  updated_at: string;
}

export interface StationBase {
  id: string;
  code: string;
  name: string;
  line_code: string;
  sequence: number;
  latitude: number;
  longitude: number;
  is_terminus: boolean;
  has_junction: boolean;
  structure: string;
}

export interface StationList extends StationBase {
  platforms: number;
  opened_year: number;
}

export interface StationDetail extends StationBase {
  platforms: number;
  opened_year: number;
  created_at: string;
  updated_at: string;
  coordinate_confidence: string;
}

export interface LineWithStations extends LineDetail {
  stations: StationBase[];
}

export interface TrackSegmentList {
  id: string;
  line_code: string;
  from_station_id: string;
  to_station_id: string;
  direction: string;
  segment_index: number;
  length_m: number;
  heading_in_deg: number;
  heading_out_deg: number;
  max_curve_radius_m: number | null;
  speed_limit_kmh: number;
  gradient_pct: number | null;
  is_curve: boolean;
}

export interface TrainClassList {
  id: string;
  name: string;
  max_speed_kmh: number;
  acceleration_ms2: number;
  deceleration_ms2: number;
  length_m: number;
  capacity_seated: number;
  capacity_standing: number;
}

export interface DepotList {
  id: string;
  line_code: string;
  name: string;
  latitude: number;
  longitude: number;
  area_m2: number;
  capacity_stabling: number;
  coordinate_confidence: string;
}

export interface SimulationState {
  running: boolean;
  paused: boolean;
  time_s: number;
  trains: number;
  active_trains: number;
  depot_trains: number;
  passengers: number;
  completed_passengers: number;
  active_incidents: number;
  service_period: string;
  ist_time: string;
  service_start: string;
  service_end: string;
}

export interface SimulationConfig {
  duration_s?: number;
  dt_s?: number;
  seed?: number;
  n_passengers?: number;
  headway_target_s?: number;
  snapshot_interval_s?: number;
}

export interface TrainPosition {
  train_id: string;
  line_code: string;
  line_name?: string;
  direction: string;
  direction_destination?: string;
  status: string;
  speed_kmh: number;
  speed_mps: number;
  position_m: number;
  current_station: string;       // station code (internal)
  current_station_name?: string; // human-readable name for display
  next_station: string;          // station code (internal)
  next_station_name?: string;    // human-readable name for display
  distance_to_next_m?: number;
  eta_s?: number;
  is_at_platform?: boolean;
  occupancy: number;
  doors_open: boolean;
  block_id: string;
}

export interface SimulationMetrics {
  avg_headway_s: number;
  avg_dwell_s: number;
  avg_journey_time_s: number;
  avg_speed_mps: number;
  total_energy_wh: number;
}

export interface ApproachInfo {
  bearing: number;
  line_code: string;
  direction: string;
}

export interface StationApproachData {
  id: string;
  code: string;
  name: string;
  line_code: string;
  latitude: number;
  longitude: number;
  platforms: number;
  has_junction: boolean;
}

export interface ApproachingTrainsResponse {
  station_code: string;
  station: StationApproachData;
  trains: TrainPosition[];
  approaches: ApproachInfo[];
}

export interface TrainDebugPosition {
  train_id: string;
  line_code: string;
  line_name: string;
  direction: string;
  direction_destination: string;
  status: string;
  speed_kmh: number;
  occupancy: number;
  current_station: string;       // Full human-readable name
  current_station_code: string;  // Internal code (supplementary)
  next_station: string;          // Full human-readable name
  next_station_code: string;     // Internal code (supplementary)
  distance_to_next_m: number;
  eta_s: number;
  is_at_platform: boolean;
  doors_open: boolean;
}

export interface LineStationSummary {
  station_name: string;  // Full human-readable name
  station_code: string;  // Internal code (supplementary)
  at_platform: number;
  approaching: number;
}

export interface LineTrainGroup {
  line_code: string;
  line_name: string;
  terminal_up: string;
  terminal_down: string;
  total_trains: number;
  active_trains: TrainDebugPosition[];
  station_summary: LineStationSummary[];
}

export interface TrainPositionsResponse {
  generated_at_s: number;
  ist_time: string;
  service_period: string;
  lines: LineTrainGroup[];
  total_trains: number;
  total_active: number;
}

export interface WSMessage {
  type: string;
  tick: number;
  time_s: number;
  ist_time: string;
  service_period: string;
  running: boolean;
  paused: boolean;
  trains: TrainPosition[];
  metrics: SimulationMetrics;
  completed_passengers: number;
  active_incidents: number;
  passengers: number;
  depot_trains: number;
  active_trains: number;
  total_trains?: number;
}
