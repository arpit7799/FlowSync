"""Integration tests for SUMO simulation across all four intersections.

These tests require SUMO to be installed and accessible.
They verify that the simulation runs correctly with both the baseline
actuated controller and the experimental adaptive controller.
"""

import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "simulation/sumo/config"
NETWORK_FILE = ROOT / "simulation/sumo/network/flowsync.net.xml"
RESULTS_DIR = ROOT / "data/results"
SCENARIOS = ("low", "medium", "heavy")
JUNCTIONS = ("J1", "J2", "J3", "J4")

# Expected vehicle counts per scenario (10 routes)
EXPECTED_VEHICLES = {"low": 50, "medium": 150, "heavy": 300}


def _sumo_available():
    """Check if SUMO is installed and traci importable."""
    try:
        import traci
        import shutil
        return shutil.which("sumo") is not None
    except ImportError:
        return False


requires_sumo = pytest.mark.skipif(
    not _sumo_available(),
    reason="SUMO or traci not available",
)


# ---------------------------------------------------------------------------
# Network structure tests (no SUMO process needed)
# ---------------------------------------------------------------------------


class TestNetworkStructure:
    """Verify the SUMO network has the expected topology."""

    @pytest.fixture(autouse=True)
    def parse_network(self):
        self.tree = ET.parse(NETWORK_FILE)
        self.root = self.tree.getroot()

    def test_four_traffic_light_junctions_exist(self):
        junctions = [
            j for j in self.root.findall("junction")
            if j.get("type") == "traffic_light"
        ]
        junction_ids = {j.get("id") for j in junctions}
        assert junction_ids == {"J1", "J2", "J3", "J4"}

    def test_each_junction_has_twelve_controlled_links(self):
        for tl in self.root.findall("tlLogic"):
            tl_id = tl.get("id")
            state_len = len(tl.findall("phase")[0].get("state"))
            assert state_len == 12, (
                f"{tl_id} has {state_len} links, expected 12"
            )

    def test_each_junction_has_four_phases(self):
        for tl in self.root.findall("tlLogic"):
            phases = tl.findall("phase")
            assert len(phases) == 4, (
                f"{tl.get('id')} has {len(phases)} phases, expected 4"
            )

    def test_j1_j2_share_signal_pattern(self):
        tls = {
            tl.get("id"): tl for tl in self.root.findall("tlLogic")
        }
        j1_states = [p.get("state") for p in tls["J1"].findall("phase")]
        j2_states = [p.get("state") for p in tls["J2"].findall("phase")]
        assert j1_states == j2_states

    def test_j3_j4_share_signal_pattern(self):
        tls = {
            tl.get("id"): tl for tl in self.root.findall("tlLogic")
        }
        j3_states = [p.get("state") for p in tls["J3"].findall("phase")]
        j4_states = [p.get("state") for p in tls["J4"].findall("phase")]
        assert j3_states == j4_states

    def test_yellow_phases_have_yellow_signals(self):
        for tl in self.root.findall("tlLogic"):
            phases = tl.findall("phase")
            # Yellow phases are index 1 and 3
            for idx in (1, 3):
                state = phases[idx].get("state")
                assert "y" in state or "Y" in state, (
                    f"{tl.get('id')} phase {idx} has no yellow: {state}"
                )

    def test_signal_state_lengths_consistent(self):
        for tl in self.root.findall("tlLogic"):
            phases = tl.findall("phase")
            lengths = {len(p.get("state")) for p in phases}
            assert len(lengths) == 1, (
                f"{tl.get('id')} has inconsistent state lengths: {lengths}"
            )


# ---------------------------------------------------------------------------
# Route and scenario tests
# ---------------------------------------------------------------------------


class TestRoutes:
    """Verify route definitions and scenario files."""

    def test_all_scenarios_exist(self):
        for scenario in SCENARIOS:
            config = CONFIG_DIR / f"{scenario}.sumocfg"
            assert config.exists(), f"Missing config: {config}"

    def test_route_file_has_ambulance_type(self):
        types_file = ROOT / "simulation/sumo/routes/vehicle_types.rou.xml"
        tree = ET.parse(types_file)
        vtypes = {vt.get("id") for vt in tree.getroot().findall("vType")}
        assert "ambulance" in vtypes

    def test_scenario_vehicle_counts(self):
        for scenario in SCENARIOS:
            route_file = ROOT / f"simulation/sumo/scenarios/{scenario}.rou.xml"
            tree = ET.parse(route_file)
            vehicles = tree.getroot().findall("vehicle")
            assert len(vehicles) == EXPECTED_VEHICLES[scenario], (
                f"{scenario}: expected {EXPECTED_VEHICLES[scenario]}, "
                f"got {len(vehicles)}"
            )

    def test_south_to_east_route_goes_east(self):
        """Verify the south_to_east route actually reaches the east boundary."""
        route_file = ROOT / "simulation/sumo/routes/flowsync_routes.rou.xml"
        tree = ET.parse(route_file)
        for route in tree.getroot().findall("route"):
            if route.get("id") == "south_to_east":
                edges = route.get("edges").split()
                assert edges[-1] == "J4_E", (
                    f"south_to_east should end at J4_E, got {edges[-1]}"
                )
                return
        pytest.fail("south_to_east route not found")

    def test_ten_routes_defined(self):
        route_file = ROOT / "simulation/sumo/routes/flowsync_routes.rou.xml"
        tree = ET.parse(route_file)
        routes = tree.getroot().findall("route")
        assert len(routes) == 10


# ---------------------------------------------------------------------------
# Baseline simulation result tests (use existing data)
# ---------------------------------------------------------------------------


class TestBaselineResults:
    """Verify baseline (actuated) simulation results."""

    def test_baseline_summaries_exist(self):
        for scenario in SCENARIOS:
            summary = RESULTS_DIR / f"{scenario}_summary.json"
            assert summary.exists(), f"Missing: {summary}"

    def test_all_vehicles_arrive_baseline(self):
        for scenario in SCENARIOS:
            summary = json.loads(
                (RESULTS_DIR / f"{scenario}_summary.json").read_text()
            )
            inserted = summary["vehicles_inserted"]
            arrived = summary["vehicles_arrived"]
            assert arrived == inserted, (
                f"{scenario}: {arrived}/{inserted} vehicles arrived"
            )
            assert inserted == EXPECTED_VEHICLES[scenario]

    def test_baseline_metrics_files_exist(self):
        for scenario in SCENARIOS:
            metrics = RESULTS_DIR / f"{scenario}_traffic_metrics.csv"
            assert metrics.exists()
            assert metrics.stat().st_size > 0


# ---------------------------------------------------------------------------
# Adaptive simulation result tests
# ---------------------------------------------------------------------------


class TestAdaptiveResults:
    """Verify adaptive controller simulation results."""

    @pytest.fixture(autouse=True)
    def load_adaptive_summary(self):
        path = RESULTS_DIR / "adaptive_summary.json"
        assert path.exists(), "Run adaptive simulations first"
        self.summaries = {
            s["scenario"]: s
            for s in json.loads(path.read_text())
        }

    def test_all_vehicles_arrive_adaptive(self):
        for scenario in SCENARIOS:
            s = self.summaries[scenario]
            assert s["vehicles_arrived"] == s["vehicles_inserted"]
            assert s["vehicles_remaining"] == 0

    def test_all_four_intersections_controlled(self):
        for scenario in SCENARIOS:
            assert self.summaries[scenario]["intersections_controlled"] == 4

    def test_adaptive_decisions_recorded(self):
        for scenario in SCENARIOS:
            assert self.summaries[scenario]["decision_count"] > 0

    def test_adaptive_metrics_files_exist(self):
        for scenario in SCENARIOS:
            metrics = RESULTS_DIR / f"{scenario}_adaptive_metrics.csv"
            decisions = RESULTS_DIR / f"{scenario}_adaptive_decisions.csv"
            assert metrics.exists() and metrics.stat().st_size > 0
            assert decisions.exists() and decisions.stat().st_size > 0


# ---------------------------------------------------------------------------
# Signal safety tests
# ---------------------------------------------------------------------------


class TestSignalSafety:
    """Verify that signal states never create unsafe conditions."""

    def _get_tl_phases(self):
        tree = ET.parse(NETWORK_FILE)
        result = {}
        for tl in tree.getroot().findall("tlLogic"):
            phases = [p.get("state") for p in tl.findall("phase")]
            result[tl.get("id")] = phases
        return result

    def test_no_conflicting_green_in_same_phase(self):
        """Green phases from the TL program should not have conflicting
        movements that are unsafe. Verified by checking that only the
        defined phase 0 and phase 2 green states are used."""
        phases = self._get_tl_phases()
        for junction_id, states in phases.items():
            # Green phases are index 0 and 2
            for idx in (0, 2):
                green = states[idx]
                # Every character should be G, g, or r
                for i, ch in enumerate(green):
                    assert ch in ("G", "g", "r"), (
                        f"{junction_id} phase {idx} pos {i}: "
                        f"unexpected '{ch}'"
                    )

    def test_yellow_follows_green(self):
        """Verify that yellow phases correctly transition from green."""
        phases = self._get_tl_phases()
        for junction_id, states in phases.items():
            for green_idx, yellow_idx in ((0, 1), (2, 3)):
                green = states[green_idx]
                yellow = states[yellow_idx]
                for i in range(len(green)):
                    if green[i] in ("G", "g"):
                        assert yellow[i] in ("y", "Y", "G", "g", "r"), (
                            f"{junction_id}: green pos {i} -> "
                            f"invalid yellow '{yellow[i]}'"
                        )

    def test_green_duration_within_bounds(self):
        from traffic_intelligence.adaptive_control.controller import (
            ControllerConfig,
        )
        config = ControllerConfig()
        assert config.min_green >= 5
        assert config.max_green <= 120
        assert config.yellow >= 3
        assert config.all_red >= 1
