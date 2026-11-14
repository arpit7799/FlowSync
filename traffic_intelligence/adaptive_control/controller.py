from dataclasses import dataclass
from typing import Literal


Movement = Literal[0, 2]


@dataclass(frozen=True)
class ControllerConfig:
    min_green: int = 10
    max_green: int = 60
    yellow: int = 3
    all_red: int = 1
    max_starvation: int = 90

    vehicle_weight: float = 1.0
    queue_weight: float = 3.0
    waiting_weight: float = 0.15

    demand_reference: float = 12.0
    hysteresis: float = 1.15


@dataclass(frozen=True)
class TrafficDemand:
    vehicles: int
    queue: int
    waiting_time: float = 0.0


@dataclass(frozen=True)
class SignalDecision:
    selected_phase: Movement
    green_duration: int
    phase_0_score: float
    phase_2_score: float
    reason: str


class AdaptiveSignalController:
    """Queue-aware adaptive controller for two compatible green phases."""

    def __init__(self, config: ControllerConfig | None = None):
        self.config = config or ControllerConfig()

        if self.config.min_green <= 0:
            raise ValueError("Minimum green must be positive.")

        if self.config.max_green < self.config.min_green:
            raise ValueError("Maximum green cannot be below minimum green.")

        if self.config.yellow < 0 or self.config.all_red < 0:
            raise ValueError("Clearance durations cannot be negative.")

        if self.config.max_starvation <= 0:
            raise ValueError("Maximum starvation must be positive.")

        if self.config.demand_reference <= 0:
            raise ValueError("Demand reference must be positive.")

        self.last_served = {0: 0.0, 2: 0.0}

    def calculate_score(self, demand: TrafficDemand) -> float:
        if demand.vehicles < 0 or demand.queue < 0:
            raise ValueError("Traffic counts cannot be negative.")

        if demand.waiting_time < 0:
            raise ValueError("Waiting time cannot be negative.")

        return (
            self.config.vehicle_weight * demand.vehicles
            + self.config.queue_weight * demand.queue
            + self.config.waiting_weight * demand.waiting_time
        )

    def decide(
        self,
        phase_0: TrafficDemand,
        phase_2: TrafficDemand,
        current_time: float,
    ) -> SignalDecision:

        score_0 = self.calculate_score(phase_0)
        score_2 = self.calculate_score(phase_2)

        demands = {0: phase_0, 2: phase_2}
        scores = {0: score_0, 2: score_2}

        starvation = {
            phase: current_time - self.last_served[phase]
            for phase in (0, 2)
        }

        starved = [
            phase
            for phase in (0, 2)
            if starvation[phase] >= self.config.max_starvation
        ]

        if starved:
            selected = max(
                starved,
                key=lambda phase: (
                    demands[phase].waiting_time,
                    starvation[phase],
                    scores[phase],
                ),
            )
            reason = "starvation_prevention"

        else:
            if score_0 > score_2 * self.config.hysteresis:
                selected = 0
                reason = "higher_phase_0_demand"
            elif score_2 > score_0 * self.config.hysteresis:
                selected = 2
                reason = "higher_phase_2_demand"
            else:
                selected = (
                    0 if self.last_served[0] <= self.last_served[2] else 2
                )
                reason = "balanced_demand_fairness"

        selected_score = scores[selected]

        demand_ratio = min(
            1.0,
            selected_score / self.config.demand_reference,
        )

        green = round(
            self.config.min_green
            + demand_ratio
            * (self.config.max_green - self.config.min_green)
        )

        green = max(
            self.config.min_green,
            min(self.config.max_green, green),
        )

        return SignalDecision(
            selected_phase=selected,
            green_duration=green,
            phase_0_score=round(score_0, 2),
            phase_2_score=round(score_2, 2),
            reason=reason,
        )

    def mark_served(self, phase: Movement, current_time: float) -> None:
        if phase not in (0, 2):
            raise ValueError("Only green phases 0 and 2 can be served.")

        self.last_served[phase] = current_time
