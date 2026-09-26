export type UserRole = "CIVILIAN" | "OFFICER" | "RESPONSE_TEAM";

export interface UserPublic {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface IncidentTimelineEvent {
  status: string;
  note: string;
  actor_name: string;
  actor_role: UserRole;
  timestamp: string;
}

export interface IncidentReport {
  id: string;
  reporter_id: string;
  reporter_name: string;
  title: string;
  category: string;
  severity: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  description: string;
  location_name: string;
  latitude: number;
  longitude: number;
  contact: string;
  photo_name: string;
  status: "NEW" | "ACKNOWLEDGED" | "TEAM_ASSIGNED" | "TEAM_ACCEPTED" | "EN_ROUTE" | "RESOLVED";
  assigned_team_ids: string[];
  primary_team_id: string | null;
  assignment_deadline: string | null;
  team_acknowledged_at: string | null;
  created_at: string;
  updated_at: string;
  timeline: IncidentTimelineEvent[];
}

export interface IncidentReportPayload {
  title: string;
  category: string;
  severity: IncidentReport["severity"];
  description: string;
  location_name: string;
  latitude: number;
  longitude: number;
  contact: string;
  photo_name: string;
}

export interface ResponseTeam {
  id: string;
  user_id: string;
  name: string;
  capabilities: string[];
  latitude: number;
  longitude: number;
  status: "AVAILABLE" | "BUSY" | "OFF_DUTY";
  active_incidents: number;
}

export interface TeamRecommendation {
  team: ResponseTeam;
  score: number;
  distance_km: number;
  capability_match: boolean;
  reasoning: string[];
}

export interface IncidentMessage {
  id: string;
  report_id: string;
  sender_id: string;
  sender_name: string;
  sender_role: UserRole;
  message: string;
  created_at: string;
}

export interface Incident {
  id: string;
  category: string;
  title: string;
  zone_id: string;
  zone_name: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "Dispatched" | "Resolved" | "Monitoring" | "Investigating";
  occurred_at: string;
  dispatch_unit: string;
  resolution_minutes: number;
  description: string;
  latitude: number;
  longitude: number;
}

export interface CampusZone {
  id: string;
  name: string;
  incidents: number;
  risk_level: "CRITICAL" | "HIGH" | "MODERATE" | "LOW";
  is_highest_risk: boolean;
  latitude: number;
  longitude: number;
  scope: "KIIT" | "Bhubaneswar";
  area_note: string;
  peak_hours: string;
  category_breakdown: Record<string, number>;
}

export interface IncidentDashboard {
  incidents: Incident[];
  zones: CampusZone[];
  total_incidents: number;
  filtered_incidents: number;
  high_risk_zone_id: string;
  generated_at: string;
}

export interface GeoPoint {
  latitude: number;
  longitude: number;
}

export interface GeofenceStats {
  incident_count: number;
  risk_score: number;
  average_response_minutes: number;
  category_breakdown: Record<string, number>;
}

export interface Geofence {
  id: string;
  name: string;
  points: GeoPoint[];
  patrol_owner: string;
  risk_threshold: "LOW" | "MODERATE" | "HIGH" | "CRITICAL";
  notes: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  stats: GeofenceStats;
}

export interface GeofencePayload {
  name: string;
  points: GeoPoint[];
  patrol_owner: string;
  risk_threshold: Geofence["risk_threshold"];
  notes: string;
}

export const CATEGORY_OPTIONS = [
  "all",
  "Traffic Accident",
  "Medical Emergency",
  "Campus Disturbance",
  "Asset Theft",
  "Fire Hazard",
  "CCTV/Network Glitch",
] as const;

export const FALLBACK_ZONES: CampusZone[] = [
  { id: "zone-1", name: "KIIT Square Junction", incidents: 42, risk_level: "CRITICAL", is_highest_risk: true, latitude: 20.3533, longitude: 85.8188, scope: "KIIT", area_note: "The primary KIIT hotspot, driven by evening pedestrian and two-wheeler conflict.", peak_hours: "17:00–20:00", category_breakdown: { "Traffic Accident": 21, "Medical Emergency": 8 } },
  { id: "zone-3", name: "KIMS Hospital & Medical Gate", incidents: 29, risk_level: "HIGH", is_highest_risk: false, latitude: 20.3498, longitude: 85.8175, scope: "KIIT", area_note: "Medical response corridor with frequent vehicle movement.", peak_hours: "08:00–11:00", category_breakdown: { "Medical Emergency": 14, "Traffic Accident": 8 } },
  { id: "zone-7", name: "Patia & Infocity Junction", incidents: 31, risk_level: "HIGH", is_highest_risk: false, latitude: 20.3585, longitude: 85.8115, scope: "Bhubaneswar", area_note: "Dense commuter corridor serving Infocity and north Bhubaneswar.", peak_hours: "08:30–10:30", category_breakdown: { "Traffic Accident": 17, "Medical Emergency": 5 } },
  { id: "zone-8", name: "Jayadev Vihar Overbridge", incidents: 38, risk_level: "CRITICAL", is_highest_risk: false, latitude: 20.3021, longitude: 85.8239, scope: "Bhubaneswar", area_note: "High-speed interchange with recurring peak-hour traffic incidents.", peak_hours: "18:00–21:00", category_breakdown: { "Traffic Accident": 25, "Medical Emergency": 7 } },
  { id: "zone-9", name: "Master Canteen & Station Area", incidents: 29, risk_level: "HIGH", is_highest_risk: false, latitude: 20.2667, longitude: 85.8436, scope: "Bhubaneswar", area_note: "Transit-heavy zone around the railway station.", peak_hours: "17:00–22:00", category_breakdown: { "Traffic Accident": 12, "Asset Theft": 8 } },
  { id: "zone-10", name: "Rasulgarh Square / NH16", incidents: 40, risk_level: "CRITICAL", is_highest_risk: false, latitude: 20.3051, longitude: 85.8672, scope: "Bhubaneswar", area_note: "Major NH16 junction with high commercial traffic volume.", peak_hours: "08:00–11:00", category_breakdown: { "Traffic Accident": 24, "Medical Emergency": 7 } },
];