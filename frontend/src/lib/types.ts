// TypeScript interfaces matching backend API schemas

export interface BatterySummary {
  id: number;
  aadhaar_id: string | null;
  external_ref: string;
  oem: string;
  chemistry: string;
  rated_capacity_kwh: number;
  status: string;
  soh_pct: number | null;
  rul_years: number | null;
  grade: string | null;
  confidence: string | null;
  site_name: string | null;
}

export interface BatteryListResponse {
  items: BatterySummary[];
  total: number;
  page: number;
}

export interface TelemetryDetail {
  cycle_count: number;
  capacity_now_kwh: number | null;
  capacity_fade_pct: number | null;
  avg_temp_c: number | null;
  max_temp_c: number | null;
  thermal_stress_hours: number | null;
  internal_resistance_mohm: number | null;
  ir_growth_pct: number | null;
  voltage_stability: number | null;
  coulombic_efficiency: number | null;
}

export interface AssessmentDetail {
  soh_pct: number;
  rul_years: number;
  rul_range: [number, number];
  grade: string;
  confidence: string;
  reasons: string[];
  explanation_json: Array<{ feature: string; label: string; value: number; weight: number }>;
}

export interface DeploymentDetail {
  site_id: number;
  site_name: string;
  site_type: string;
  score: number;
  distance_km: number | null;
  reasons: string[];
  energy_unlocked_mwh: number;
  carbon_saved_kg: number;
  from: [number, number] | null;
  to: [number, number] | null;
  reasoning_json: unknown[];
}

export interface BatteryDetail {
  id: number;
  aadhaar_id: string | null;
  external_ref: string;
  oem: string;
  model: string | null;
  chemistry: string;
  form_factor: string;
  rated_capacity_kwh: number;
  nominal_voltage: number | null;
  manufacture_date: string | null;
  source_city: string | null;
  source_state: string | null;
  lat: number | null;
  lng: number | null;
  status: string;
  created_at: string;
  telemetry: TelemetryDetail | null;
  assessment: AssessmentDetail | null;
  deployment: DeploymentDetail | null;
}

export interface AadhaarPassport {
  aadhaar_id: string;
  decoded: {
    country: string;
    manufacturer: string;
    chemistry: string;
    voltage: string;
    capacity_kwh: number;
    manufactured: string;
    serial: string;
  };
  qr_payload: string;
  static: Record<string, unknown>;
  dynamic: Record<string, unknown>;
  timeline: Array<{ event: string; timestamp: string; payload?: unknown }>;
  life_story: string;
  impact: Record<string, unknown>;
}

export interface Site {
  id: number;
  name: string;
  site_type: string;
  state: string | null;
  lat: number;
  lng: number;
  demand_kwh: number;
  remaining_kwh: number;
  min_grade: string;
  assigned_count: number;
}

export interface ImpactSummary {
  mwh_unlocked: number;
  carbon_saved_tonnes: number;
  diverted_from_recycling: number;
  recycled_responsibly: number;
  processed: number;
  total: number;
  by_grade: Record<string, number>;
  by_site_type: Record<string, number>;
}

export interface DashboardStats {
  total_batteries: number;
  processed: number;
  active_deployments: number;
  recycled: number;
  avg_soh_pct: number;
  mwh_unlocked: number;
  carbon_saved_tonnes: number;
  by_grade: Record<string, number>;
  by_status: Record<string, number>;
  recent_batteries: Array<{
    id: number;
    aadhaar_id: string | null;
    external_ref: string;
    oem: string;
    status: string;
    grade: string | null;
    soh_pct: number | null;
  }>;
}

export interface DeploymentItem {
  id: number;
  battery_id: number;
  aadhaar_id: string | null;
  external_ref: string;
  oem: string;
  chemistry: string;
  rated_capacity_kwh: number;
  grade: string | null;
  soh_pct: number | null;
  confidence: string | null;
  site_id: number;
  site_name: string;
  site_type: string;
  site_state: string | null;
  score: number;
  distance_km: number | null;
  energy_unlocked_mwh: number;
  carbon_saved_kg: number;
  deployment_status: string;
  created_at: string;
  from_coords: [number, number] | null;
  to_coords: [number, number] | null;
}

export interface FleetAnalytics {
  total_batteries: number;
  total_with_telemetry: number;
  averages: {
    cycle_count: number;
    capacity_fade_pct: number;
    avg_temp_c: number;
    max_temp_c: number;
    internal_resistance_mohm: number;
    ir_growth_pct: number;
    coulombic_efficiency: number;
    voltage_stability: number;
    total_thermal_stress_hours: number;
  };
  soh_distribution: Record<string, number>;
  cycle_distribution: Record<string, number>;
  by_chemistry: Record<string, number>;
  by_oem: Record<string, number>;
}

export interface ChatResponse {
  response: string;
  intent: string;
  suggestions: string[];
}

export interface JobStatus {
  job_id: string;
  status: string;
  processed: number;
  total: number;
  recent_events: unknown[];
}

export interface WSEvent {
  type: 'assessment' | 'deployment' | 'impact' | 'progress';
  payload: Record<string, unknown>;
}
