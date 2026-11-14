"""Unit tests for SUMO-to-IoT bridge logic."""

import pytest
from simulation.traffic_bridge.iot_bridge import (
    INTERSECTION_MAPPING,
    SUMOIoTBridge,
    queue_to_ultrasonic_distance,
)
from iot.mqtt.client import FlowSyncMQTTClient
from traffic_intelligence.emergency_priority.priority_manager import EmergencyPriorityManager


def test_queue_to_ultrasonic_distance_mapping():
    # Empty queue should indicate clear road (~350cm)
    assert queue_to_ultrasonic_distance(0) >= 300.0

    # 1 vehicle halted at stop line
    d1 = queue_to_ultrasonic_distance(1)
    assert 10.0 <= d1 <= 30.0

    # Multiple vehicles halted
    d2 = queue_to_ultrasonic_distance(2)
    d3 = queue_to_ultrasonic_distance(5)
    assert d3 <= d2 <= d1


def test_intersection_mapping_coverage():
    assert set(INTERSECTION_MAPPING.keys()) == {"J1", "J2", "J3", "J4"}
    for jid, info in INTERSECTION_MAPPING.items():
        assert "device_id" in info
        assert "approach_edges" in info
        assert len(info["approach_edges"]) > 0


def test_bridge_command_queueing():
    client = FlowSyncMQTTClient(client_id="dummy_bridge_test")
    bridge = SUMOIoTBridge(mqtt_client=client)

    # Simulate receiving a signal command
    bridge._on_signal_command("flowsync/intersection/J1/signals", {
        "schema_version": "1.0",
        "event_type": "signal.command",
        "timestamp": 100.0,
        "intersection_id": "J1",
        "red": False,
        "yellow": False,
        "green": True,
        "phase": 0,
    })

    assert "J1" in bridge._pending_commands
    assert bridge._pending_commands["J1"]["green"] is True


def test_bridge_rejects_malformed_command():
    client = FlowSyncMQTTClient(client_id="dummy_bridge_test")
    bridge = SUMOIoTBridge(mqtt_client=client)

    # Malformed command
    bridge._on_signal_command("flowsync/intersection/J1/signals", {
        "bad_key": "bad_value",
    })

    assert "J1" not in bridge._pending_commands


def test_bridge_emergency_event_dispatch():
    client = FlowSyncMQTTClient(client_id="dummy_bridge_test")
    em = EmergencyPriorityManager()
    bridge = SUMOIoTBridge(mqtt_client=client, emergency_manager=em)

    bridge._on_emergency_event("flowsync/emergency/detected", {
        "schema_version": "1.0",
        "event_type": "emergency.detected",
        "timestamp": 120.0,
        "intersection_id": "J1",
        "vehicle_id": "amb_iot_test",
        "vehicle_type": "ambulance",
    })

    assert em.is_priority_active("J1")
