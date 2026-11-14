"use client";

import React, { useState } from "react";
import { EmergencyEvent } from "@/lib/api";
import { AlertCircle, CheckCircle2, ShieldAlert, XCircle } from "lucide-react";

interface EmergencyTrackerProps {
  events: EmergencyEvent[];
  onTriggerEmergency: (junction: string, vehicleId: string) => Promise<void>;
  onCancelEmergency: (eventId: string) => Promise<void>;
}

export const EmergencyTracker: React.FC<EmergencyTrackerProps> = ({
  events,
  onTriggerEmergency,
  onCancelEmergency,
}) => {
  const [targetJunction, setTargetJunction] = useState("J1");
  const [vehicleId, setVehicleId] = useState("ambulance_01");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      await onTriggerEmergency(targetJunction, vehicleId);
    } finally {
      setIsSubmitting(false);
    }
  };

  const activeEvents = events.filter((e) =>
    ["requested", "clearing_existing", "active"].includes(e.status)
  );

  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg space-y-5">
      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
        <div>
          <h3 className="font-bold text-white flex items-center gap-2">
            <ShieldAlert className="h-4 w-4 text-red-400" />
            Emergency Vehicle Priority Dispatcher
          </h3>
          <p className="text-xs text-slate-400">
            Coordinates green corridor clearance for ambulances across the 4-junction grid
          </p>
        </div>
      </div>

      {/* Manual Dispatch Form */}
      <form onSubmit={handleSubmit} className="grid grid-cols-1 md:grid-cols-4 gap-3 bg-slate-950/40 p-3 rounded-lg border border-slate-800/80">
        <div>
          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
            Vehicle ID
          </label>
          <input
            type="text"
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
            required
          />
        </div>

        <div>
          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
            Target Junction
          </label>
          <select
            value={targetJunction}
            onChange={(e) => setTargetJunction(e.target.value)}
            className="w-full bg-slate-900 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500 font-mono"
          >
            <option value="J1">J1 (North-West)</option>
            <option value="J2">J2 (North-East)</option>
            <option value="J3">J3 (South-West)</option>
            <option value="J4">J4 (South-East)</option>
          </select>
        </div>

        <div>
          <label className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
            Vehicle Type
          </label>
          <input
            type="text"
            disabled
            value="Ambulance (Code Red)"
            className="w-full bg-slate-900/50 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-400 font-mono"
          />
        </div>

        <div className="flex items-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 px-3 rounded bg-red-600 hover:bg-red-500 text-white font-bold text-xs transition shadow-md shadow-red-600/20 disabled:opacity-50"
          >
            {isSubmitting ? "Dispatching..." : "Dispatch Priority"}
          </button>
        </div>
      </form>

      {/* Active Corridors */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          Active Emergency Corridors ({activeEvents.length})
        </h4>

        {activeEvents.length === 0 ? (
          <div className="text-center py-4 text-xs text-slate-500 bg-slate-950/20 rounded border border-slate-800/40">
            No active emergency preemption requests. Normal adaptive signal cycle operating.
          </div>
        ) : (
          <div className="space-y-2">
            {activeEvents.map((ev) => (
              <div
                key={ev.event_id}
                className="flex items-center justify-between p-3 rounded-lg bg-red-950/30 border border-red-500/40"
              >
                <div className="flex items-center gap-3">
                  <div className="h-8 w-8 rounded-full bg-red-500/20 border border-red-500/40 flex items-center justify-center animate-pulse">
                    <ShieldAlert className="h-4 w-4 text-red-400" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-white text-xs font-mono">{ev.vehicle_id}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded bg-red-900/50 text-red-300 border border-red-700 uppercase">
                        {ev.status}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Intersection <span className="text-white font-semibold">{ev.junction_id}</span> • Phase {ev.requested_phase}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => onCancelEmergency(ev.event_id)}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-700 transition"
                >
                  Cancel
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Event History */}
      <div>
        <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2">
          Emergency Response History
        </h4>
        <div className="max-h-48 overflow-y-auto space-y-1.5 pr-1">
          {events.slice(0, 5).map((ev) => (
            <div
              key={ev.event_id}
              className="flex items-center justify-between p-2 rounded bg-slate-950/40 border border-slate-800 text-xs"
            >
              <div className="flex items-center gap-2">
                {ev.status === "cleared" ? (
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                ) : ev.status === "cancelled" ? (
                  <XCircle className="h-3.5 w-3.5 text-slate-500" />
                ) : (
                  <AlertCircle className="h-3.5 w-3.5 text-red-400 animate-pulse" />
                )}
                <span className="font-mono font-semibold text-slate-200">{ev.vehicle_id}</span>
                <span className="text-slate-400">@ {ev.junction_id}</span>
              </div>

              <div className="flex items-center gap-3 font-mono text-[11px]">
                {ev.response_time !== null && ev.response_time !== undefined && (
                  <span className="text-cyan-400">Response: {ev.response_time}s</span>
                )}
                <span className="capitalize text-slate-400">{ev.status}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
