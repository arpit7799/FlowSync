from dataclasses import dataclass, field
from pathlib import Path
import csv
from typing import Optional

import traci

from .controller import (
    AdaptiveSignalController,
    TrafficDemand,
)
from traffic_intelligence.emergency_priority.priority_manager import (
    EmergencyPriorityManager,
    PriorityStatus,
)
from traffic_intelligence.emergency_priority.detector import (
    EmergencyVehicleDetector,
)


@dataclass
class IntersectionRuntime:
    junction: str
    controller: AdaptiveSignalController
    green_states: dict
    yellow_states: dict
    all_red_state: str
    phase_links: dict
    shared_links: list[int] = field(default_factory=list)

    mode: str = "initial"
    current_phase: int | None = None
    transition_at: float = 0.0
    current_decision: object | None = None


def green_indices(state: str) -> list[int]:
    return [
        index
        for index, character in enumerate(state)
        if character in ("G", "g")
    ]


def partition_phase_indices(green_states: dict) -> tuple[dict, list[int]]:
    """Separate exclusive phase signals from signals shared by both phases."""
    phase_0 = set(green_indices(green_states[0]))
    phase_2 = set(green_indices(green_states[2]))

    shared = sorted(phase_0 & phase_2)

    exclusive = {
        0: sorted(phase_0 - set(shared)),
        2: sorted(phase_2 - set(shared)),
    }

    return exclusive, shared


def build_intersection(junction: str) -> IntersectionRuntime:
    programs = traci.trafficlight.getAllProgramLogics(junction)

    if not programs:
        raise RuntimeError(f"No signal program found for {junction}")

    program = next(
        (p for p in programs if p.programID == "0"),
        programs[0],
    )
    phases = program.phases

    if len(phases) < 4:
        raise RuntimeError(f"{junction} requires four signal phases")

    green_states = {0: phases[0].state, 2: phases[2].state}
    yellow_states = {0: phases[1].state, 2: phases[3].state}

    for phase in (0, 2):
        green = green_states[phase]
        yellow = yellow_states[phase]

        if len(green) != len(yellow):
            raise RuntimeError(f"{junction}: green/yellow length mismatch")

        if not any(character in ("y", "Y") for character in yellow):
            raise RuntimeError(
                f"{junction}: yellow phase contains no yellow signal"
            )

    controlled_links = traci.trafficlight.getControlledLinks(junction)

    for state in green_states.values():
        if len(state) != len(controlled_links):
            raise RuntimeError(
                f"{junction}: signal state/link count mismatch"
            )

    phase_links, shared_links = partition_phase_indices(green_states)

    return IntersectionRuntime(
        junction=junction,
        controller=AdaptiveSignalController(),
        green_states=green_states,
        yellow_states=yellow_states,
        all_red_state="r" * len(green_states[0]),
        phase_links=phase_links,
        shared_links=shared_links,
    )

def get_phase_demand(
    runtime: IntersectionRuntime,
    phase: int,
) -> TrafficDemand:
    """
    Estimate phase demand using unique vehicles and their next route edge.
    A vehicle is counted once per phase, even if multiple signal links
    connect its incoming lane to the same outgoing edge.
    """

    links = traci.trafficlight.getControlledLinks(runtime.junction)
    relevant_vehicles = set()

    for signal_index in runtime.phase_links[phase]:
        for connection in links[signal_index]:
            incoming_lane, outgoing_lane, _ = connection
            outgoing_edge = traci.lane.getEdgeID(outgoing_lane)

            for vehicle_id in traci.lane.getLastStepVehicleIDs(
                incoming_lane
            ):
                route = traci.vehicle.getRoute(vehicle_id)
                route_index = traci.vehicle.getRouteIndex(vehicle_id)

                if route_index < 0 or route_index + 1 >= len(route):
                    continue

                if route[route_index + 1] == outgoing_edge:
                    relevant_vehicles.add(vehicle_id)

    queue = 0
    maximum_wait = 0.0

    for vehicle_id in relevant_vehicles:
        if traci.vehicle.getSpeed(vehicle_id) <= 0.1:
            queue += 1

        maximum_wait = max(
            maximum_wait,
            traci.vehicle.getWaitingTime(vehicle_id),
        )

    return TrafficDemand(
        vehicles=len(relevant_vehicles),
        queue=queue,
        waiting_time=maximum_wait,
    )

def get_both_demands(runtime):
    return (
        get_phase_demand(runtime, 0),
        get_phase_demand(runtime, 2),
    )


def apply_green(runtime, phase, decision, current_time, decision_log):
    traci.trafficlight.setRedYellowGreenState(
        runtime.junction,
        runtime.green_states[phase],
    )

    runtime.mode = "green"
    runtime.current_phase = phase
    runtime.current_decision = decision
    runtime.transition_at = current_time + decision.green_duration

    runtime.controller.mark_served(phase, current_time)

    decision_log.append({
        "time": current_time,
        "intersection": runtime.junction,
        "selected_phase": phase,
        "green_duration": decision.green_duration,
        "phase_0_score": decision.phase_0_score,
        "phase_2_score": decision.phase_2_score,
        "reason": decision.reason,
    })


def update_intersection(
    runtime,
    current_time,
    decision_log,
    emergency_manager: Optional[EmergencyPriorityManager] = None,
):
    # Check if an emergency preemption is active for this intersection
    if emergency_manager is not None and emergency_manager.is_priority_active(runtime.junction):
        state = emergency_manager.get_junction_state(runtime.junction)
        target = state.target_phase

        if state.status == PriorityStatus.CLEARING_EXISTING:
            if runtime.mode == "green":
                if runtime.current_phase == target:
                    # Current green is already the requested green!
                    emergency_manager.on_phase_granted(runtime.junction, current_time)
                    runtime.mode = "emergency_green"
                    runtime.transition_at = current_time + 1.0
                    return
                else:
                    # Must safely clear conflicting green through yellow
                    traci.trafficlight.setRedYellowGreenState(
                        runtime.junction,
                        runtime.yellow_states[runtime.current_phase],
                    )
                    runtime.mode = "emergency_yellow"
                    runtime.transition_at = (
                        current_time + runtime.controller.config.yellow
                    )
                    return

            elif runtime.mode == "emergency_yellow":
                if current_time >= runtime.transition_at:
                    traci.trafficlight.setRedYellowGreenState(
                        runtime.junction,
                        runtime.all_red_state,
                    )
                    runtime.mode = "emergency_all_red"
                    runtime.transition_at = (
                        current_time + runtime.controller.config.all_red
                    )
                return

            elif runtime.mode in ("all_red", "emergency_all_red", "initial"):
                if current_time >= runtime.transition_at:
                    traci.trafficlight.setRedYellowGreenState(
                        runtime.junction,
                        runtime.green_states[target],
                    )
                    runtime.mode = "emergency_green"
                    runtime.current_phase = target
                    runtime.transition_at = current_time + 1.0
                    emergency_manager.on_phase_granted(runtime.junction, current_time)

                    decision_log.append({
                        "time": current_time,
                        "intersection": runtime.junction,
                        "selected_phase": target,
                        "green_duration": -1,
                        "phase_0_score": 999.0 if target == 0 else 0.0,
                        "phase_2_score": 999.0 if target == 2 else 0.0,
                        "reason": "emergency_priority_granted",
                    })
                return

        elif state.status == PriorityStatus.ACTIVE:
            # Active emergency green corridor
            if current_time >= state.hold_until:
                # Max hold exceeded, transition safely out
                emergency_manager.clear_priority(runtime.junction, current_time, reason="timeout")
                traci.trafficlight.setRedYellowGreenState(
                    runtime.junction,
                    runtime.yellow_states[runtime.current_phase],
                )
                runtime.mode = "yellow"
                runtime.transition_at = (
                    current_time + runtime.controller.config.yellow
                )
            else:
                # Maintain green corridor
                runtime.transition_at = current_time + 1.0
            return

    # Normal operation
    if current_time < runtime.transition_at:
        return

    if runtime.mode in ("initial", "all_red", "emergency_all_red"):
        demand_0, demand_2 = get_both_demands(runtime)

        decision = runtime.controller.decide(
            demand_0,
            demand_2,
            current_time,
        )

        apply_green(
            runtime,
            decision.selected_phase,
            decision,
            current_time,
            decision_log,
        )

    elif runtime.mode in ("green", "emergency_green"):
        phase = runtime.current_phase

        traci.trafficlight.setRedYellowGreenState(
            runtime.junction,
            runtime.yellow_states[phase],
        )

        runtime.mode = "yellow"
        runtime.transition_at = (
            current_time + runtime.controller.config.yellow
        )

    elif runtime.mode in ("yellow", "emergency_yellow"):
        traci.trafficlight.setRedYellowGreenState(
            runtime.junction,
            runtime.all_red_state,
        )

        runtime.mode = "all_red"
        runtime.transition_at = (
            current_time + runtime.controller.config.all_red
        )


def collect_live_metrics(runtime, scenario, current_time):
    demand_0, demand_2 = get_both_demands(runtime)

    return {
        "time": current_time,
        "scenario": scenario,
        "intersection": runtime.junction,
        "signal_mode": runtime.mode,
        "active_phase": (
            runtime.current_phase
            if runtime.current_phase is not None
            else -1
        ),
        "phase_0_vehicles": demand_0.vehicles,
        "phase_0_queue": demand_0.queue,
        "phase_2_vehicles": demand_2.vehicles,
        "phase_2_queue": demand_2.queue,
        "phase_0_waiting": demand_0.waiting_time,
        "phase_2_waiting": demand_2.waiting_time,
    }


def run_adaptive_simulation(
    config_path: Path,
    scenario: str,
    results_dir: Path,
    enable_emergency_priority: bool = True,
):
    results_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = results_dir / f"{scenario}_adaptive_metrics.csv"
    decisions_path = results_dir / f"{scenario}_adaptive_decisions.csv"
    emergency_events_path = results_dir / f"{scenario}_emergency_events.json"

    metrics = []
    decisions = []

    total_departed = 0
    total_arrived = 0

    emergency_detector = EmergencyVehicleDetector() if enable_emergency_priority else None
    emergency_manager = EmergencyPriorityManager() if enable_emergency_priority else None

    tripinfo_path = results_dir / f"{scenario}_adaptive_tripinfo.xml"

    traci.start([
        "sumo",
        "-c", str(config_path),
        "--no-step-log", "true",
        "--tripinfo-output", str(tripinfo_path),
    ])

    try:
        junctions = traci.trafficlight.getIDList()

        runtimes = {
            junction: build_intersection(junction)
            for junction in junctions
        }

        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()

            current_time = traci.simulation.getTime()

            total_departed += traci.simulation.getDepartedNumber()
            total_arrived += traci.simulation.getArrivedNumber()

            # Handle emergency vehicle detection and priority requests
            if emergency_detector and emergency_manager:
                tracked_evs = emergency_detector.scan_for_emergency_vehicles(runtimes)

                for ev in tracked_evs:
                    if ev.target_junction and ev.required_phase is not None:
                        if ev.distance_to_stopline_m <= 250.0:
                            emergency_manager.request_priority(
                                vehicle_id=ev.vehicle_id,
                                vehicle_type=ev.vehicle_type,
                                junction=ev.target_junction,
                                incoming_edge=ev.current_edge,
                                requested_phase=ev.required_phase,
                                current_time=current_time,
                                current_phase=runtimes[ev.target_junction].current_phase,
                                current_mode=runtimes[ev.target_junction].mode,
                            )

                # Check if any active emergency vehicle has cleared the junction
                for j_id, j_state in list(emergency_manager.junction_states.items()):
                    if j_state.status == PriorityStatus.ACTIVE and j_state.active_vehicle_id:
                        vid = j_state.active_vehicle_id
                        still_approaching = any(
                            ev.vehicle_id == vid and ev.target_junction == j_id
                            for ev in tracked_evs
                        )
                        if not still_approaching:
                            cleared_ev = emergency_manager.clear_priority(
                                j_id, current_time, reason="vehicle_passed"
                            )
                            if cleared_ev:
                                rt = runtimes[j_id]
                                traci.trafficlight.setRedYellowGreenState(
                                    rt.junction,
                                    rt.yellow_states[rt.current_phase],
                                )
                                rt.mode = "yellow"
                                rt.transition_at = current_time + rt.controller.config.yellow

            for runtime in runtimes.values():
                update_intersection(
                    runtime,
                    current_time,
                    decisions,
                    emergency_manager,
                )

                metrics.append(
                    collect_live_metrics(
                        runtime,
                        scenario,
                        current_time,
                    )
                )

    finally:
        traci.close()

    if not metrics:
        raise RuntimeError(f"No telemetry collected for {scenario}")

    with metrics_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=metrics[0].keys(),
        )
        writer.writeheader()
        writer.writerows(metrics)

    with decisions_path.open("w", newline="") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=decisions[0].keys(),
        )
        writer.writeheader()
        writer.writerows(decisions)

    if emergency_manager and emergency_manager.event_history:
        import json
        ev_data = [
            {
                "event_id": ev.event_id,
                "vehicle_id": ev.vehicle_id,
                "vehicle_type": ev.vehicle_type,
                "junction": ev.junction,
                "incoming_edge": ev.incoming_edge,
                "requested_phase": ev.requested_phase,
                "request_time": ev.request_time,
                "granted_time": ev.granted_time,
                "cleared_time": ev.cleared_time,
                "response_time": ev.response_time,
                "status": ev.status.value,
                "notes": ev.notes,
            }
            for ev in emergency_manager.event_history
        ]
        emergency_events_path.write_text(json.dumps(ev_data, indent=4))

    summary = {
        "scenario": scenario,
        "vehicles_inserted": total_departed,
        "vehicles_arrived": total_arrived,
        "vehicles_remaining": total_departed - total_arrived,
        "intersections_controlled": len(runtimes),
        "decision_count": len(decisions),
        "metrics_records": len(metrics),
        "adaptive_peak_queue": max(
            max(row["phase_0_queue"], row["phase_2_queue"])
            for row in metrics
        ),
    }

    print(f"\n{scenario.upper()} ADAPTIVE RESULTS")
    for key, value in summary.items():
        print(f"{key}: {value}")

    print("Metrics:", metrics_path)
    print("Decisions:", decisions_path)

    return summary
