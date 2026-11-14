"""Generate a benchmark comparison report between baseline and adaptive control."""

import csv
import json
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "data/results"
SCENARIOS = ("low", "medium", "heavy")


def parse_tripinfo(path: Path) -> dict:
    """Parse SUMO tripinfo XML and compute aggregate metrics."""
    tree = ET.parse(path)
    trips = tree.getroot().findall("tripinfo")

    if not trips:
        return {
            "total_vehicles": 0,
            "avg_waiting_time": 0,
            "avg_duration": 0,
            "avg_time_loss": 0,
            "total_time_loss": 0,
        }

    waiting_times = []
    durations = []
    time_losses = []

    for trip in trips:
        waiting_times.append(float(trip.get("waitingTime", 0)))
        durations.append(float(trip.get("duration", 0)))
        time_losses.append(float(trip.get("timeLoss", 0)))

    return {
        "total_vehicles": len(trips),
        "avg_waiting_time": round(sum(waiting_times) / len(waiting_times), 2),
        "avg_duration": round(sum(durations) / len(durations), 2),
        "avg_time_loss": round(sum(time_losses) / len(time_losses), 2),
        "total_time_loss": round(sum(time_losses), 2),
        "max_waiting_time": round(max(waiting_times), 2),
    }


def parse_metrics_csv(path: Path) -> dict:
    """Parse per-step metrics CSV and compute queue statistics."""
    rows = list(csv.DictReader(path.open()))

    if not rows:
        return {"avg_queue": 0, "peak_queue": 0, "records": 0}

    queue_key = "queue_length" if "queue_length" in rows[0] else None
    if queue_key is None:
        # Adaptive metrics use phase_0_queue and phase_2_queue
        queues = [
            max(int(r.get("phase_0_queue", 0)), int(r.get("phase_2_queue", 0)))
            for r in rows
        ]
    else:
        queues = [int(r[queue_key]) for r in rows]

    return {
        "avg_queue": round(sum(queues) / len(queues), 3),
        "peak_queue": max(queues),
        "records": len(rows),
    }


def generate_report():
    report = {"generated_at": "benchmark_comparison", "scenarios": {}}

    for scenario in SCENARIOS:
        baseline_tripinfo = RESULTS_DIR / f"{scenario}_tripinfo.xml"
        adaptive_tripinfo = RESULTS_DIR / f"{scenario}_adaptive_tripinfo.xml"
        baseline_metrics = RESULTS_DIR / f"{scenario}_traffic_metrics.csv"
        adaptive_metrics = RESULTS_DIR / f"{scenario}_adaptive_metrics.csv"
        baseline_summary = RESULTS_DIR / f"{scenario}_summary.json"

        entry = {"baseline": {}, "adaptive": {}}

        # Baseline summary
        if baseline_summary.exists():
            entry["baseline"]["summary"] = json.loads(
                baseline_summary.read_text()
            )

        # Tripinfo comparison
        if baseline_tripinfo.exists():
            entry["baseline"]["tripinfo"] = parse_tripinfo(baseline_tripinfo)
        if adaptive_tripinfo.exists():
            entry["adaptive"]["tripinfo"] = parse_tripinfo(adaptive_tripinfo)

        # Metrics comparison
        if baseline_metrics.exists():
            entry["baseline"]["queue_stats"] = parse_metrics_csv(
                baseline_metrics
            )
        if adaptive_metrics.exists():
            entry["adaptive"]["queue_stats"] = parse_metrics_csv(
                adaptive_metrics
            )

        # Comparison
        if "tripinfo" in entry["baseline"] and "tripinfo" in entry["adaptive"]:
            b = entry["baseline"]["tripinfo"]
            a = entry["adaptive"]["tripinfo"]
            entry["comparison"] = {
                "waiting_time_change_pct": round(
                    ((a["avg_waiting_time"] - b["avg_waiting_time"])
                     / max(b["avg_waiting_time"], 0.01)) * 100, 1
                ),
                "time_loss_change_pct": round(
                    ((a["avg_time_loss"] - b["avg_time_loss"])
                     / max(b["avg_time_loss"], 0.01)) * 100, 1
                ),
                "duration_change_pct": round(
                    ((a["avg_duration"] - b["avg_duration"])
                     / max(b["avg_duration"], 0.01)) * 100, 1
                ),
            }

        report["scenarios"][scenario] = entry

    return report


def main():
    report = generate_report()

    output = RESULTS_DIR / "benchmark_report.json"
    output.write_text(json.dumps(report, indent=4))
    print(f"Benchmark report: {output}")

    # Print summary table
    print("\n" + "=" * 72)
    print("FLOWSYNC BENCHMARK COMPARISON: Baseline (Actuated) vs Adaptive")
    print("=" * 72)

    for scenario in SCENARIOS:
        entry = report["scenarios"][scenario]
        print(f"\n--- {scenario.upper()} SCENARIO ---")

        for mode in ("baseline", "adaptive"):
            data = entry.get(mode, {})
            ti = data.get("tripinfo", {})
            qs = data.get("queue_stats", {})
            print(f"  {mode.capitalize()}:")
            print(f"    Vehicles:         {ti.get('total_vehicles', 'N/A')}")
            print(f"    Avg Waiting Time: {ti.get('avg_waiting_time', 'N/A')}s")
            print(f"    Avg Time Loss:    {ti.get('avg_time_loss', 'N/A')}s")
            print(f"    Avg Duration:     {ti.get('avg_duration', 'N/A')}s")
            print(f"    Peak Queue:       {qs.get('peak_queue', 'N/A')}")
            print(f"    Avg Queue:        {qs.get('avg_queue', 'N/A')}")

        comp = entry.get("comparison", {})
        if comp:
            print(f"  Change (adaptive vs baseline):")
            for key, val in comp.items():
                direction = "+" if val > 0 else ""
                print(f"    {key}: {direction}{val}%")


if __name__ == "__main__":
    main()
