export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
export const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000/ws/live";

export interface Intersection {
  id: string;
  name: string;
  status: string;
  current_phase?: number;
  phase?: number;
  current_mode?: string;
  mode?: string;
  current_state?: string;
  state?: string;
  vehicle_count?: number;
  vehicles?: number;
  queue_length?: number;
  queue?: number;
  location_x?: number;
  location_y?: number;
}

export interface SensorReading {
  id: number;
  intersection_id: string;
  device_id: string;
  distance_cm: number;
  vehicle_detected: boolean;
  vehicle_count: number;
  queue_length: number;
  timestamp: number;
  created_at: string;
}

export interface EmergencyEvent {
  id: number;
  event_id: string;
  vehicle_id: string;
  vehicle_type: string;
  junction_id: string;
  incoming_edge?: string;
  requested_phase: number;
  request_time: number;
  granted_time?: number;
  cleared_time?: number;
  response_time?: number;
  status: string;
  notes?: string;
}

export interface BenchmarkReport {
  generated_at: string;
  scenarios: {
    [key: string]: {
      baseline?: {
        tripinfo?: {
          total_vehicles: number;
          avg_waiting_time: number;
          avg_time_loss: number;
          avg_duration: number;
        };
        queue_stats?: {
          peak_queue: number;
          avg_queue: number;
        };
      };
      adaptive?: {
        tripinfo?: {
          total_vehicles: number;
          avg_waiting_time: number;
          avg_time_loss: number;
          avg_duration: number;
        };
        queue_stats?: {
          peak_queue: number;
          avg_queue: number;
        };
      };
      comparison?: {
        waiting_time_change_pct: number;
        time_loss_change_pct: number;
        duration_change_pct: number;
      };
    };
  };
}

export interface DeviceStatus {
  device_id: string;
  intersection_id: string;
  status: string;
  uptime_seconds: number;
  last_heartbeat: string;
  ip_address: string;
}

export async function fetchTrafficState() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/traffic/state`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch state");
    return await res.json();
  } catch (err) {
    console.error("Traffic state fetch error:", err);
    return null;
  }
}

export async function fetchIntersections(): Promise<Intersection[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/intersections`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch intersections");
    return await res.json();
  } catch (err) {
    console.error("Intersections fetch error:", err);
    return [];
  }
}

export async function fetchSensors(): Promise<SensorReading[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/sensors/telemetry?limit=20`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch sensors");
    return await res.json();
  } catch (err) {
    console.error("Sensors fetch error:", err);
    return [];
  }
}

export async function fetchEmergencyEvents(): Promise<EmergencyEvent[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/emergency/requests?limit=20`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch emergency events");
    return await res.json();
  } catch (err) {
    console.error("Emergency fetch error:", err);
    return [];
  }
}

export async function createEmergencyRequest(data: {
  vehicle_id: string;
  intersection_id: string;
  vehicle_type?: string;
  incoming_edge?: string;
  requested_phase?: number;
}) {
  const res = await fetch(`${API_BASE}/api/v1/emergency/requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ...data, source: "dashboard_ui" }),
  });
  return await res.json();
}

export async function cancelEmergencyRequest(eventId: string) {
  const res = await fetch(`${API_BASE}/api/v1/emergency/requests/${eventId}/cancel`, {
    method: "POST",
  });
  return await res.json();
}

export async function fetchBenchmarkReport(): Promise<BenchmarkReport | null> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/benchmarks`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch benchmark");
    return await res.json();
  } catch (err) {
    console.error("Benchmark fetch error:", err);
    return null;
  }
}

export async function fetchDevices(): Promise<DeviceStatus[]> {
  try {
    const res = await fetch(`${API_BASE}/api/v1/devices`, { cache: "no-store" });
    if (!res.ok) throw new Error("Failed to fetch devices");
    return await res.json();
  } catch (err) {
    console.error("Devices fetch error:", err);
    return [];
  }
}
