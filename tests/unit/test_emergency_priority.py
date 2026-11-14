"""Unit tests for emergency priority module."""

import pytest
from traffic_intelligence.emergency_priority.priority_manager import (
    EmergencyPriorityManager,
    PriorityStatus,
)


def test_priority_request_lifecycle():
    pm = EmergencyPriorityManager(yellow_clearance=3.0, all_red_clearance=1.0)

    # 1. Request priority when current phase is conflicting
    event = pm.request_priority(
        vehicle_id="amb_01",
        vehicle_type="ambulance",
        junction="J1",
        incoming_edge="N_J1",
        requested_phase=0,
        current_time=10.0,
        current_phase=2,
        current_mode="green",
    )

    assert event is not None
    assert event.vehicle_id == "amb_01"
    assert event.junction == "J1"
    assert event.requested_phase == 0
    assert event.status == PriorityStatus.CLEARING_EXISTING
    assert pm.is_priority_active("J1")

    # 2. Transition completed, green phase granted
    pm.on_phase_granted("J1", current_time=14.0)
    assert event.status == PriorityStatus.ACTIVE
    assert event.granted_time == 14.0
    assert event.response_time == 4.0  # 14.0 - 10.0

    # 3. Vehicle passes, clear priority
    cleared = pm.clear_priority("J1", current_time=25.0, reason="vehicle_passed")
    assert cleared is not None
    assert cleared.status == PriorityStatus.CLEARED
    assert cleared.cleared_time == 25.0
    assert not pm.is_priority_active("J1")


def test_immediate_grant_when_phase_already_green():
    pm = EmergencyPriorityManager()

    event = pm.request_priority(
        vehicle_id="amb_02",
        vehicle_type="ambulance",
        junction="J2",
        incoming_edge="J1_J2",
        requested_phase=0,
        current_time=50.0,
        current_phase=0,
        current_mode="green",
    )

    assert event.status == PriorityStatus.ACTIVE
    assert event.granted_time == 50.0
    assert event.response_time == 0.0
    assert pm.is_priority_active("J2")


def test_repeated_request_protection():
    pm = EmergencyPriorityManager()

    event1 = pm.request_priority(
        vehicle_id="amb_03",
        vehicle_type="ambulance",
        junction="J3",
        incoming_edge="W_J3",
        requested_phase=2,
        current_time=100.0,
        current_phase=0,
        current_mode="green",
    )

    # Duplicate call for the same vehicle
    event2 = pm.request_priority(
        vehicle_id="amb_03",
        vehicle_type="ambulance",
        junction="J3",
        incoming_edge="W_J3",
        requested_phase=2,
        current_time=101.0,
        current_phase=0,
        current_mode="yellow",
    )

    assert event1.event_id == event2.event_id
    assert len(pm.event_history) == 1  # No duplicate record created


def test_manual_cancellation():
    pm = EmergencyPriorityManager()

    event = pm.request_priority(
        vehicle_id="amb_04",
        vehicle_type="ambulance",
        junction="J4",
        incoming_edge="E_J4",
        requested_phase=0,
        current_time=200.0,
    )

    cancelled = pm.cancel_priority("J4", current_time=205.0, reason="diverted")
    assert cancelled is not None
    assert cancelled.status == PriorityStatus.CANCELLED
    assert not pm.is_priority_active("J4")


def test_clearance_intervals_configured():
    pm = EmergencyPriorityManager(yellow_clearance=4.0, all_red_clearance=2.0)
    assert pm.yellow_clearance == 4.0
    assert pm.all_red_clearance == 2.0


def test_multiple_junction_coordination():
    pm = EmergencyPriorityManager()

    # Ambulance moving along corridor N_J1 -> J1_J2 -> J2_S
    ev1 = pm.request_priority("amb_corridor", "ambulance", "J1", "N_J1", 0, 10.0, 2, "green")
    ev2 = pm.request_priority("amb_corridor", "ambulance", "J2", "J1_J2", 0, 15.0, 2, "green")

    assert pm.is_priority_active("J1")
    assert pm.is_priority_active("J2")

    pm.clear_priority("J1", 20.0)
    assert not pm.is_priority_active("J1")
    assert pm.is_priority_active("J2")

    pm.clear_priority("J2", 30.0)
    assert not pm.is_priority_active("J2")
