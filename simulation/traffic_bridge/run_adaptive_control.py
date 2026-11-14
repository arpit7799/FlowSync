from pathlib import Path
import json

from traffic_intelligence.adaptive_control.sumo_adapter import (
    run_adaptive_simulation,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "simulation/sumo/config"
RESULTS_DIR = ROOT / "data/results"

SCENARIOS = ("low", "medium", "heavy")


def main():
    summaries = []

    for scenario in SCENARIOS:
        config = CONFIG_DIR / f"{scenario}.sumocfg"

        summary = run_adaptive_simulation(
            config_path=config,
            scenario=scenario,
            results_dir=RESULTS_DIR,
        )

        summaries.append(summary)

    summary_path = RESULTS_DIR / "adaptive_summary.json"
    summary_path.write_text(
        json.dumps(summaries, indent=4)
    )

    print("\nAll adaptive simulations completed.")
    print("Summary:", summary_path)


if __name__ == "__main__":
    main()
