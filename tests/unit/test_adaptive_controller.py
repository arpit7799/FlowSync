import pytest

from traffic_intelligence.adaptive_control.controller import (
    AdaptiveSignalController,
    ControllerConfig,
    TrafficDemand,
)


def test_higher_demand_selects_phase():
    controller = AdaptiveSignalController()

    decision = controller.decide(
        TrafficDemand(vehicles=10, queue=5),
        TrafficDemand(vehicles=2, queue=1),
        current_time=10,
    )

    assert decision.selected_phase == 0


def test_green_duration_stays_within_limits():
    controller = AdaptiveSignalController()

    decision = controller.decide(
        TrafficDemand(vehicles=100, queue=50),
        TrafficDemand(vehicles=0, queue=0),
        current_time=10,
    )

    assert 10 <= decision.green_duration <= 60


def test_balanced_demand_alternates_fairly():
    controller = AdaptiveSignalController()

    first = controller.decide(
        TrafficDemand(5, 2),
        TrafficDemand(5, 2),
        current_time=10,
    )

    controller.mark_served(first.selected_phase, 10)

    second = controller.decide(
        TrafficDemand(5, 2),
        TrafficDemand(5, 2),
        current_time=20,
    )

    assert first.selected_phase != second.selected_phase


def test_starvation_prevention_selects_overdue_phase():
    controller = AdaptiveSignalController()

    controller.mark_served(0, 0)

    decision = controller.decide(
        TrafficDemand(20, 10, waiting_time=10),
        TrafficDemand(1, 0, waiting_time=100),
        current_time=100,
    )

    assert decision.selected_phase == 2
    assert decision.reason == "starvation_prevention"


def test_negative_queue_is_rejected():
    controller = AdaptiveSignalController()

    with pytest.raises(ValueError):
        controller.decide(
            TrafficDemand(1, -1),
            TrafficDemand(1, 1),
            current_time=10,
        )


def test_invalid_configuration_is_rejected():
    with pytest.raises(ValueError):
        AdaptiveSignalController(
            ControllerConfig(min_green=60, max_green=10)
        )
