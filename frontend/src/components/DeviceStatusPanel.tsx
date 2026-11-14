"use client";

import React from "react";
import { DeviceStatus } from "@/lib/api";
import { Cpu, Server, Wifi } from "lucide-react";

interface DeviceStatusPanelProps {
  devices: DeviceStatus[];
  onOpenBenchmark: () => void;
}

export const DeviceStatusPanel: React.FC<DeviceStatusPanelProps> = ({
  devices,
  onOpenBenchmark,
}) => {
  const defaultNodes = [
    { device_id: "esp32_j1_controller", intersection_id: "J1", status: "online", uptime_seconds: 1420 },
    { device_id: "esp32_j2_controller", intersection_id: "J2", status: "online", uptime_seconds: 1420 },
    { device_id: "esp32_j3_controller", intersection_id: "J3", status: "online", uptime_seconds: 1420 },
    { device_id: "esp32_j4_controller", intersection_id: "J4", status: "online", uptime_seconds: 1420 },
  ];

  const displayList = devices.length > 0 ? devices : defaultNodes;

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="font-bold text-white flex items-center gap-2">
            <Cpu className="h-4 w-4 text-cyan-400" />
            IoT Edge Controllers & Broker
          </h3>
          <p className="text-xs text-slate-400">
            Wokwi Virtual Hardware Status & MQTT Mosquitto Connectivity
          </p>
        </div>

        <button
          onClick={onOpenBenchmark}
          className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/40 text-xs font-semibold transition"
        >
          View Benchmark Report
        </button>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {displayList.map((dev) => (
          <div
            key={dev.device_id}
            className="p-3 rounded-lg bg-slate-950/40 border border-slate-800/80 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs font-bold text-white">
                {dev.intersection_id}
              </span>
              <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                {dev.status}
              </span>
            </div>

            <div className="text-[11px] text-slate-400 font-mono truncate">
              {dev.device_id}
            </div>

            <div className="text-[10px] text-slate-500 mt-2">
              Uptime: {Math.floor(dev.uptime_seconds)}s
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
