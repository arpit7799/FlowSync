"use client";

import React from "react";
import { Intersection } from "@/lib/api";
import { IntersectionCard } from "./IntersectionCard";

interface OverviewGridProps {
  intersections: Intersection[];
  onDispatchEmergency: (jid: string) => void;
}

export const OverviewGrid: React.FC<OverviewGridProps> = ({
  intersections,
  onDispatchEmergency,
}) => {
  // Sort or map to grid positions: J1 (top-left), J2 (top-right), J3 (bottom-left), J4 (bottom-right)
  const jMap = new Map(intersections.map((i) => [i.id, i]));
  const gridOrder = ["J1", "J2", "J3", "J4"];

  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold text-white">4-Intersection Grid Network</h2>
          <p className="text-xs text-slate-400">
            Real-time multi-junction traffic signal control and emergency corridor coordination
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {gridOrder.map((jid) => {
          const item = jMap.get(jid) || {
            id: jid,
            name: `Junction ${jid}`,
            status: "online",
            current_phase: 0,
            current_mode: "initial",
            current_state: "GGggrrrrGGGg",
            vehicle_count: 0,
            queue_length: 0,
            location_x: 0,
            location_y: 0,
          };

          return (
            <IntersectionCard
              key={jid}
              intersection={item}
              onDispatchEmergency={onDispatchEmergency}
            />
          );
        })}
      </div>
    </section>
  );
};
