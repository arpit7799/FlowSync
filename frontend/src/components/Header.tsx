"use client";

import React from "react";
import { Activity, Radio, ShieldAlert } from "lucide-react";

interface HeaderProps {
  wsConnected: boolean;
  totalVehicles: number;
  totalQueue: number;
  emergencyActive: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  wsConnected,
  totalVehicles,
  totalQueue,
  emergencyActive,
}) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50 px-6 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Radio className="h-5 w-5 text-white animate-pulse" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-tight text-white flex items-center gap-2">
              FlowSync
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800">
                Edge AI & IoT
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Adaptive Traffic Signal & Emergency Priority System
            </p>
          </div>
        </div>

        {/* Live Metrics Header Badges */}
        <div className="flex items-center gap-3 text-sm">
          {emergencyActive && (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-red-950/80 border border-red-500/50 text-red-300 font-semibold text-xs animate-pulse">
              <ShieldAlert className="h-4 w-4 text-red-400" />
              EMERGENCY CORRIDOR ACTIVE
            </div>
          )}

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2">
            <span className="text-xs text-slate-400 uppercase tracking-wider">Vehicles:</span>
            <span className="font-bold text-white font-mono">{totalVehicles}</span>
          </div>

          <div className="bg-slate-800/80 border border-slate-700/60 rounded-lg px-3 py-1.5 flex items-center gap-2">
            <span className="text-xs text-slate-400 uppercase tracking-wider">Queue:</span>
            <span className="font-bold text-amber-400 font-mono">{totalQueue}</span>
          </div>

          {/* Connection status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700/60 text-xs font-medium">
            <span
              className={`h-2.5 w-2.5 rounded-full ${
                wsConnected ? "bg-emerald-400 animate-ping" : "bg-amber-400"
              }`}
            />
            <span className={wsConnected ? "text-emerald-400" : "text-amber-400"}>
              {wsConnected ? "WebSocket Live" : "Polling Active"}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
