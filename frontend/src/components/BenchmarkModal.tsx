"use client";

import React from "react";
import { BenchmarkReport } from "@/lib/api";
import { BarChart3, TrendingUp, X } from "lucide-react";

interface BenchmarkModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: BenchmarkReport | null;
}

export const BenchmarkModal: React.FC<BenchmarkModalProps> = ({
  isOpen,
  onClose,
  report,
}) => {
  if (!isOpen) return null;

  const scenarios = report?.scenarios ? Object.keys(report.scenarios) : ["low", "medium", "heavy"];

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 shadow-2xl text-slate-100 space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center">
              <BarChart3 className="h-5 w-5 text-cyan-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white">
                Empirical Benchmark Comparison
              </h2>
              <p className="text-xs text-slate-400">
                SUMO Actuated Baseline vs Experimental Adaptive Signal Controller
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-white transition"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Note on honest findings per project rules */}
        <div className="p-4 rounded-xl bg-amber-950/30 border border-amber-600/40 text-amber-200 text-xs leading-relaxed">
          <strong className="font-semibold block mb-1">Academic Project Evaluation Note:</strong>
          In accordance with project integrity standards, results are reported from actual SUMO TraCI
          simulations. SUMO&apos;s mature gap-out actuated controller provides a robust baseline. The
          experimental adaptive controller prioritizes queue balancing and starvation prevention, making
          it subject to higher waiting times under balanced demand patterns.
        </div>

        {/* Comparison Tables per Scenario */}
        <div className="space-y-6">
          {scenarios.map((sc) => {
            const data = report?.scenarios?.[sc];
            const baseTi = data?.baseline?.tripinfo;
            const adaptTi = data?.adaptive?.tripinfo;
            const baseQs = data?.baseline?.queue_stats;
            const adaptQs = data?.adaptive?.queue_stats;
            const comp = data?.comparison;

            return (
              <div key={sc} className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
                <div className="flex items-center justify-between mb-3 border-b border-slate-800/80 pb-2">
                  <h3 className="font-bold text-white uppercase text-sm tracking-wider flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" />
                    {sc} Traffic Demand
                  </h3>
                  <span className="text-xs font-mono text-slate-400">
                    {baseTi?.total_vehicles || 0} Vehicles Evaluated
                  </span>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-900 text-slate-400 font-mono text-[11px]">
                      <tr>
                        <th className="py-2 px-3">Metric</th>
                        <th className="py-2 px-3">Baseline (Actuated)</th>
                        <th className="py-2 px-3">Adaptive (Experimental)</th>
                        <th className="py-2 px-3">Delta</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 font-mono text-slate-200">
                      <tr>
                        <td className="py-2 px-3 text-slate-400 font-sans">Avg Waiting Time</td>
                        <td className="py-2 px-3">{baseTi?.avg_waiting_time ?? "N/A"} s</td>
                        <td className="py-2 px-3">{adaptTi?.avg_waiting_time ?? "N/A"} s</td>
                        <td className="py-2 px-3 font-semibold text-amber-400">
                          {comp ? `+${comp.waiting_time_change_pct}%` : "—"}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-slate-400 font-sans">Avg Time Loss</td>
                        <td className="py-2 px-3">{baseTi?.avg_time_loss ?? "N/A"} s</td>
                        <td className="py-2 px-3">{adaptTi?.avg_time_loss ?? "N/A"} s</td>
                        <td className="py-2 px-3 font-semibold text-amber-400">
                          {comp ? `+${comp.time_loss_change_pct}%` : "—"}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-slate-400 font-sans">Trip Duration</td>
                        <td className="py-2 px-3">{baseTi?.avg_duration ?? "N/A"} s</td>
                        <td className="py-2 px-3">{adaptTi?.avg_duration ?? "N/A"} s</td>
                        <td className="py-2 px-3 font-semibold text-slate-300">
                          {comp ? `+${comp.duration_change_pct}%` : "—"}
                        </td>
                      </tr>
                      <tr>
                        <td className="py-2 px-3 text-slate-400 font-sans">Peak Intersection Queue</td>
                        <td className="py-2 px-3">{baseQs?.peak_queue ?? "N/A"} veh</td>
                        <td className="py-2 px-3">{adaptQs?.peak_queue ?? "N/A"} veh</td>
                        <td className="py-2 px-3 text-slate-400">—</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            );
          })}
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs transition"
          >
            Close Report
          </button>
        </div>
      </div>
    </div>
  );
};
