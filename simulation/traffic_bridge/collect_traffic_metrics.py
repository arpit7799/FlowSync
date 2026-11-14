from pathlib import Path
import csv
import json
import traci

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "simulation/sumo/config"
NETWORK_FILE = ROOT / "simulation/sumo/network/flowsync.net.xml"
RESULTS_DIR = ROOT / "data/results"

SIMULATIONS = ["low", "medium", "heavy"]

INCOMING = {
    "J1": ["N_J1", "J2_J1", "J3_J1"],
    "J2": ["J1_J2", "J4_J2", "S_J2"],
    "J3": ["J1_J3", "J4_J3", "W_J3"],
    "J4": ["J2_J4", "J3_J4", "E_J4"],
}


def get_incoming_lanes():
    import xml.etree.ElementTree as ET

    root = ET.parse(NETWORK_FILE).getroot()
    edge_lanes = {}

    for edge in root.findall("edge"):
        edge_id = edge.get("id")
        if edge_id and edge_id in {
            edge_id
            for incoming in INCOMING.values()
            for edge_id in incoming
        }:
            edge_lanes[edge_id] = [
                lane.get("id") for lane in edge.findall("lane")
            ]

    return {
        junction: [
            lane
            for edge in edges
            for lane in edge_lanes.get(edge, [])
        ]
        for junction, edges in INCOMING.items()
    }


def collect_scenario(scenario):
    config = CONFIG_DIR / f"{scenario}.sumocfg"
    output = RESULTS_DIR / f"{scenario}_traffic_metrics.csv"
    incoming_lanes = get_incoming_lanes()

    rows = []
    total_departed = 0
    total_arrived = 0
    tripinfo_path = RESULTS_DIR / f"{scenario}_tripinfo.xml"
    traci.start([
        "sumo", "-c", str(config), "--no-step-log", "true",
        "--tripinfo-output", str(tripinfo_path),
    ])

    try:
        while traci.simulation.getMinExpectedNumber() > 0:
            traci.simulationStep()
            total_departed += traci.simulation.getDepartedNumber()
            total_arrived += traci.simulation.getArrivedNumber()

            for junction, lanes in incoming_lanes.items():
                counts = [
                    traci.lane.getLastStepVehicleNumber(lane)
                    for lane in lanes
                ]

                vehicles = sum(counts)
                queue = sum(
                    traci.lane.getLastStepHaltingNumber(lane)
                    for lane in lanes
                )

                occupancy = (
                    sum(traci.lane.getLastStepOccupancy(lane) for lane in lanes)
                    / len(lanes)
                    if lanes else 0
                )

                speeds = [
                    traci.lane.getLastStepMeanSpeed(lane)
                    for lane, count in zip(lanes, counts)
                    if count > 0
                ]

                rows.append({
                    "time": traci.simulation.getTime(),
                    "scenario": scenario,
                    "intersection": junction,
                    "vehicles": vehicles,
                    "queue_length": queue,
                    "occupancy_percent": round(occupancy, 3),
                    "average_speed_mps": round(
                        sum(speeds) / len(speeds), 3
                    ) if speeds else 0,
                    "signal_phase": traci.trafficlight.getPhase(junction),
                })

        summary = {
            "scenario": scenario,
            "vehicles_inserted": total_departed,
            "vehicles_arrived": total_arrived,
            "vehicles_remaining": traci.simulation.getMinExpectedNumber(),
            "peak_intersection_queue": max(
                (row["queue_length"] for row in rows), default=0
            ),
            "average_intersection_queue": round(
                sum(row["queue_length"] for row in rows) / len(rows), 3
            ) if rows else 0,
        }

    finally:
        traci.close()

    with output.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    summary_path = RESULTS_DIR / f"{scenario}_summary.json"
    summary_path.write_text(json.dumps(summary, indent=4))

    print(f"\n{scenario.upper()} SCENARIO")
    print(json.dumps(summary, indent=4))
    print("Metrics saved:", output)


if __name__ == "__main__":
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    for scenario in SIMULATIONS:
        collect_scenario(scenario)
