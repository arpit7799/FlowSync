"use client";

import React from "react";
import { SensorReading } from "@/lib/api";
import { Gauge, Radio, Wifi } from "lucide-react";

interface LiveSensorsProps {
  sensors: SensorReading[];
}

export const LiveSensors: React.FC<LiveSensorsProps> = ({ sensors }) => {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-white flex items-center gap-2">
            <Radio className="h-4 w-4 text-cyan-400" />
            Live IoT Sensor Telemetry
          </h3>
          <p className="text-xs text-slate-400">
            Simulated HC-SR04 ultrasonic distance sensors on virtual ESP32 nodes
          </p>
        </div>
        <span className="text-xs bg-slate-800 px-2.5 py-1 rounded-full text-slate-300 font-mono">
          QoS 0 Telemetry
        </span>
      </div>

      {sensors.length === 0 ? (
        <div className="text-center py-8 text-xs text-slate-500">
          Waiting for incoming sensor telemetry...
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-300">
            <thead className="bg-slate-950/60 text-slate-400 uppercase tracking-wider text-[10px]">
              <tr>
                <th className="py-2.5 px-3 rounded-l">Junction</th>
                <th className="py-2.5 px-3">Device Node</th>
                <th className="py-2.5 px-3">Distance</th>
                <th className="py-2.5 px-3">Presence</th>
                <th className="py-2.5 px-3">Queue</th>
                <th className="py-2.5 px-3 rounded-r">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {sensors.slice(0, 8).map((s) => (
                <tr key={s.id} className="hover:bg-slate-800/30 transition">
                  <td className="py-2 px-3 font-bold text-cyan-400">{s.intersection_id}</td>
                  <td className="py-2 px-3 text-slate-400">{s.device_id}</td>
                  <td className="py-2 px-3">
                    <span className="text-white font-semibold">{s.distance_cm.toFixed(1)}</span>
                    <span className="text-slate-500 text-[10px] ml-1">cm</span>
                  </td>
                  <td className="py-2 px-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold ${
                        s.vehicle_detected
                          ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                          : "bg-slate-800 text-slate-400"
                      }`}
                    >
                      {s.vehicle_detected ? "DETECTED" : "CLEAR"}
                    </span>
                  </td>
                  <td className="py-2 px-3 text-amber-400 font-semibold">{s.queue_length} veh</td>
                  <td className="py-2 px-3 text-slate-400 text-[10px]">
                    {new Date(s.created_at).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
