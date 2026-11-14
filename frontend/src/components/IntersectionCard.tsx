"use client";

import React from "react";
import { Intersection } from "@/lib/api";
import { AlertTriangle, Car, Clock } from "lucide-react";

interface IntersectionCardProps {
  intersection: Intersection;
  onDispatchEmergency?: (jid: string) => void;
}

export const IntersectionCard: React.FC<IntersectionCardProps> = ({
  intersection,
  onDispatchEmergency,
}) => {
  const mode = (intersection?.current_mode || intersection?.mode || "initial").toLowerCase();
  const phase = intersection?.current_phase ?? intersection?.phase ?? 0;
  const state = intersection?.current_state || intersection?.state || "GGggrrrrGGGg";
  const vehicleCount = intersection?.vehicle_count ?? intersection?.vehicles ?? 0;
  const queueLength = intersection?.queue_length ?? intersection?.queue ?? 0;

  const isEmergency = typeof mode === "string" && mode.includes("emergency");
  const isYellow = mode === "yellow" || mode === "emergency_yellow";
  const isAllRed = mode === "all_red" || mode === "emergency_all_red";
  const isGreen = mode === "green" || mode === "emergency_green";

  return (
    <div
      className={`rounded-xl border p-5 transition-all shadow-lg ${
        isEmergency
          ? "border-red-500/80 bg-red-950/20 shadow-red-500/10"
          : "border-slate-800 bg-slate-900/60 hover:border-slate-700"
      }`}
    >
      {/* Top title and mode badge */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-mono text-sm font-bold px-2 py-0.5 rounded bg-slate-800 text-cyan-400 border border-slate-700">
              {intersection.id}
            </span>
            <h3 className="font-semibold text-white text-base">{intersection.name}</h3>
          </div>
          <p className="text-xs text-slate-400 mt-1">12-Link Controlled TLS</p>
        </div>

        <span
          className={`text-xs font-semibold px-2.5 py-1 rounded-full uppercase tracking-wider ${
            isEmergency
              ? "bg-red-500/20 text-red-400 border border-red-500/50 animate-pulse"
              : isGreen
              ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"
              : isYellow
              ? "bg-amber-500/20 text-amber-400 border border-amber-500/30"
              : "bg-rose-500/20 text-rose-400 border border-rose-500/30"
          }`}
        >
          {mode.replace("_", " ")}
        </span>
      </div>

      {/* Traffic Signal Visualizer & Info */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 bg-slate-950/50 rounded-lg p-4 border border-slate-800/80 mb-4">
        {/* Virtual 3-LED Traffic Light Housing */}
        <div className="flex flex-col items-center justify-center p-2 rounded-lg bg-slate-900 border border-slate-800 w-20 mx-auto">
          {/* RED LED */}
          <div
            className={`w-5 h-5 rounded-full my-1 transition-all duration-300 ${
              isAllRed || (!isGreen && !isYellow)
                ? "bg-red-500 shadow-md shadow-red-500/80 ring-2 ring-red-400/50"
                : "bg-red-950/40 opacity-30"
            }`}
          />
          {/* YELLOW LED */}
          <div
            className={`w-5 h-5 rounded-full my-1 transition-all duration-300 ${
              isYellow
                ? "bg-yellow-400 shadow-md shadow-yellow-400/80 ring-2 ring-yellow-300/50"
                : "bg-yellow-950/40 opacity-30"
            }`}
          />
          {/* GREEN LED */}
          <div
            className={`w-5 h-5 rounded-full my-1 transition-all duration-300 ${
              isGreen
                ? "bg-emerald-400 shadow-md shadow-emerald-400/80 ring-2 ring-emerald-300/50"
                : "bg-emerald-950/40 opacity-30"
            }`}
          />
        </div>

        {/* Phase details */}
        <div className="col-span-2 flex flex-col justify-center space-y-2 text-xs">
          <div>
            <span className="text-slate-400">Active Phase:</span>
            <div className="font-semibold text-slate-200 mt-0.5">
              {phase === 0 ? "Phase 0 (North-South / Primary)" : "Phase 2 (Cross / Secondary)"}
            </div>
          </div>

          <div>
            <span className="text-slate-400">Signal State:</span>
            <div className="font-mono text-cyan-300 tracking-wider bg-slate-900 px-2 py-1 rounded border border-slate-800 text-xs">
              {state}
            </div>
          </div>
        </div>
      </div>

      {/* Traffic Measurements */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Car className="h-3.5 w-3.5 text-cyan-400" />
            <span>Vehicles Present</span>
          </div>
          <div className="text-xl font-bold font-mono text-white">
            {vehicleCount}
          </div>
        </div>

        <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-2.5">
          <div className="flex items-center gap-1.5 text-slate-400 text-xs mb-1">
            <Clock className="h-3.5 w-3.5 text-amber-400" />
            <span>Queue Length</span>
          </div>
          <div className="text-xl font-bold font-mono text-amber-400">
            {queueLength}
          </div>
        </div>
      </div>

      {/* Action / Priority Button */}
      {onDispatchEmergency && (
        <button
          onClick={() => onDispatchEmergency(intersection.id)}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-red-600/20 hover:bg-red-600/30 text-red-300 border border-red-500/40 text-xs font-semibold transition"
        >
          <AlertTriangle className="h-3.5 w-3.5 text-red-400" />
          Request Emergency Green Priority
        </button>
      )}
    </div>
  );
};
