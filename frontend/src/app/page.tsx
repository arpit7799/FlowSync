"use client";

import React, { useEffect, useState } from "react";
import {
  BenchmarkReport,
  DeviceStatus,
  EmergencyEvent,
  Intersection,
  SensorReading,
  WS_URL,
  cancelEmergencyRequest,
  createEmergencyRequest,
  fetchBenchmarkReport,
  fetchDevices,
  fetchEmergencyEvents,
  fetchIntersections,
  fetchSensors,
  fetchTrafficState,
} from "@/lib/api";
import { Header } from "@/components/Header";
import { OverviewGrid } from "@/components/OverviewGrid";
import { EmergencyTracker } from "@/components/EmergencyTracker";
import { LiveSensors } from "@/components/LiveSensors";
import { DeviceStatusPanel } from "@/components/DeviceStatusPanel";
import { BenchmarkModal } from "@/components/BenchmarkModal";
import { TrafficCanvasSimulation } from "@/components/TrafficCanvasSimulation";
import { VirtualHardwareTwin } from "@/components/VirtualHardwareTwin";
import { Car, Cpu, LayoutGrid } from "lucide-react";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<"simulation" | "hardware" | "telemetry">("simulation");
  const [intersections, setIntersections] = useState<Intersection[]>([]);
  const [sensors, setSensors] = useState<SensorReading[]>([]);
  const [emergencyEvents, setEmergencyEvents] = useState<EmergencyEvent[]>([]);
  const [devices, setDevices] = useState<DeviceStatus[]>([]);
  const [benchmarkReport, setBenchmarkReport] = useState<BenchmarkReport | null>(null);

  const [wsConnected, setWsConnected] = useState(false);
  const [isBenchmarkOpen, setIsBenchmarkOpen] = useState(false);

  // Initial data load
  useEffect(() => {
    async function loadInitialData() {
      const [initIntersections, initSensors, initEmergency, initDevices, initBenchmark] =
        await Promise.all([
          fetchIntersections(),
          fetchSensors(),
          fetchEmergencyEvents(),
          fetchDevices(),
          fetchBenchmarkReport(),
        ]);

      if (initIntersections.length > 0) setIntersections(initIntersections);
      setSensors(initSensors);
      setEmergencyEvents(initEmergency);
      setDevices(initDevices);
      setBenchmarkReport(initBenchmark);
    }

    loadInitialData();
  }, []);

  // WebSocket Live Updates Connection with Auto-reconnect & Polling Fallback
  useEffect(() => {
    let ws: WebSocket | null = null;
    let reconnectTimer: NodeJS.Timeout | null = null;
    let pollInterval: NodeJS.Timeout | null = null;

    const connectWebSocket = () => {
      try {
        ws = new WebSocket(WS_URL);

        ws.onopen = () => {
          setWsConnected(true);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.event_type === "traffic.live_update" && Array.isArray(data.intersections)) {
              setIntersections(data.intersections);
            }
          } catch (err) {
            console.error("WS parse error:", err);
          }
        };

        ws.onclose = () => {
          setWsConnected(false);
          reconnectTimer = setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = () => {
          ws?.close();
        };
      } catch (err) {
        setWsConnected(false);
        reconnectTimer = setTimeout(connectWebSocket, 5000);
      }
    };

    connectWebSocket();

    // Secondary Polling for sensors & emergency state every 2s
    pollInterval = setInterval(async () => {
      const [sensorData, emgData] = await Promise.all([
        fetchSensors(),
        fetchEmergencyEvents(),
      ]);
      setSensors(sensorData);
      setEmergencyEvents(emgData);

      // If WS is not connected, also poll traffic state
      if (!wsConnected) {
        const state = await fetchTrafficState();
        if (state && state.intersections) {
          setIntersections(state.intersections);
        }
      }
    }, 2000);

    return () => {
      if (ws) ws.close();
      if (reconnectTimer) clearTimeout(reconnectTimer);
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [wsConnected]);

  // Actions
  const handleDispatchEmergency = async (junctionId: string, vehicleId: string = "ambulance_01") => {
    await createEmergencyRequest({
      vehicle_id: vehicleId,
      intersection_id: junctionId,
      vehicle_type: "ambulance",
      requested_phase: 0,
    });
    const refreshed = await fetchEmergencyEvents();
    setEmergencyEvents(refreshed);
  };

  const handleCancelEmergency = async (eventId: string) => {
    await cancelEmergencyRequest(eventId);
    const refreshed = await fetchEmergencyEvents();
    setEmergencyEvents(refreshed);
  };

  const totalVehicles = intersections.reduce((sum, i) => sum + (i.vehicle_count || (i as any).vehicles || 0), 0);
  const totalQueue = intersections.reduce((sum, i) => sum + (i.queue_length || (i as any).queue || 0), 0);
  const isEmergencyActive = intersections.some((i) => {
    const m = (i?.current_mode || (i as any)?.mode || "").toLowerCase();
    return m.includes("emergency");
  });

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      <Header
        wsConnected={wsConnected}
        totalVehicles={totalVehicles}
        totalQueue={totalQueue}
        emergencyActive={isEmergencyActive}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-800 pb-3">
          <button
            onClick={() => setActiveTab("simulation")}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition ${
              activeTab === "simulation"
                ? "bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20"
                : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            <Car className="h-4 w-4" />
            Live 2D Traffic & Car Simulation (Canvas)
          </button>

          <button
            onClick={() => setActiveTab("hardware")}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition ${
              activeTab === "hardware"
                ? "bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20"
                : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            <Cpu className="h-4 w-4" />
            Virtual IoT Hardware Twin (ESP32 & Sensors)
          </button>

          <button
            onClick={() => setActiveTab("telemetry")}
            className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition ${
              activeTab === "telemetry"
                ? "bg-cyan-500 text-slate-950 shadow-lg shadow-cyan-500/20"
                : "bg-slate-900 text-slate-400 hover:text-white border border-slate-800"
            }`}
          >
            <LayoutGrid className="h-4 w-4" />
            Multi-Junction Telemetry & Grid Cards
          </button>
        </div>

        {/* Tab 1: Interactive 2D Canvas Traffic Simulation */}
        {activeTab === "simulation" && (
          <div className="space-y-6">
            <TrafficCanvasSimulation />

            {/* Quick Live Emergency Tracker alongside */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <EmergencyTracker
                events={emergencyEvents}
                onTriggerEmergency={handleDispatchEmergency}
                onCancelEmergency={handleCancelEmergency}
              />

              <LiveSensors sensors={sensors} />
            </div>
          </div>
        )}

        {/* Tab 2: Virtual IoT Hardware & Circuit Twin */}
        {activeTab === "hardware" && (
          <div className="space-y-6">
            <VirtualHardwareTwin
              currentRed={intersections.find((i) => i.id === "J1")?.current_mode?.includes("red") || false}
              currentYellow={intersections.find((i) => i.id === "J1")?.current_mode?.includes("yellow") || false}
              currentGreen={intersections.find((i) => i.id === "J1")?.current_mode?.includes("green") || true}
              distanceCm={sensors.find((s) => s.intersection_id === "J1")?.distance_cm || 24.5}
              onPressEmergencyBtn={() => handleDispatchEmergency("J1", "ambulance_iot_btn")}
            />

            <DeviceStatusPanel
              devices={devices}
              onOpenBenchmark={() => setIsBenchmarkOpen(true)}
            />
          </div>
        )}

        {/* Tab 3: Detailed Telemetry, Grid Cards & Controller Analytics */}
        {activeTab === "telemetry" && (
          <div className="space-y-6">
            <OverviewGrid
              intersections={intersections}
              onDispatchEmergency={(jid) => handleDispatchEmergency(jid)}
            />

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <EmergencyTracker
                events={emergencyEvents}
                onTriggerEmergency={handleDispatchEmergency}
                onCancelEmergency={handleCancelEmergency}
              />

              <LiveSensors sensors={sensors} />
            </div>

            <DeviceStatusPanel
              devices={devices}
              onOpenBenchmark={() => setIsBenchmarkOpen(true)}
            />
          </div>
        )}
      </main>

      <footer className="border-t border-slate-900 bg-slate-950 py-4 px-6 text-center text-xs text-slate-500">
        FlowSync Traffic Intelligence Platform • Edge AI, MQTT & Wokwi Simulation
      </footer>

      {/* Benchmark Modal */}
      <BenchmarkModal
        isOpen={isBenchmarkOpen}
        onClose={() => setIsBenchmarkOpen(false)}
        report={benchmarkReport}
      />
    </div>
  );
}
