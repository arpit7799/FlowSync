"""Unit tests for MQTT module: topics, validation, and client."""

import pytest
from iot.mqtt.client import FlowSyncMQTTClient
from iot.mqtt.topics import (
    ALL_EMERGENCY,
    ALL_INTERSECTION_SENSORS,
    ALL_INTERSECTION_SIGNALS,
    ALL_INTERSECTION_STATUS,
    EMERGENCY_DETECTED,
    EMERGENCY_PRIORITY,
    SYSTEM_HEALTH,
    get_sensors_topic,
    get_signals_topic,
    get_status_topic,
    parse_intersection_id,
)
from iot.mqtt.validator import (
    validate_base_message,
    validate_device_status,
    validate_emergency_event,
    validate_sensor_reading,
    validate_signal_command,
)


def test_topic_formatting():
    assert get_sensors_topic("J1") == "flowsync/intersection/J1/sensors"
    assert get_signals_topic("J2") == "flowsync/intersection/J2/signals"
    assert get_status_topic("J3") == "flowsync/intersection/J3/status"


def test_parse_intersection_id():
    assert parse_intersection_id("flowsync/intersection/J1/sensors") == "J1"
    assert parse_intersection_id("flowsync/intersection/J4/signals") == "J4"
    assert parse_intersection_id("flowsync/emergency/detected") is None
    assert parse_intersection_id("invalid/topic") is None


def test_validate_base_message_valid():
    valid, err = validate_base_message({
        "schema_version": "1.0",
        "event_type": "sensor.reading",
        "timestamp": 123456.0,
    })
    assert valid
    assert err is None


def test_validate_base_message_invalid_schema():
    valid, err = validate_base_message({
        "schema_version": "2.0",
        "event_type": "sensor.reading",
        "timestamp": 123456.0,
    })
    assert not valid
    assert "Unsupported schema_version" in err


def test_validate_base_message_missing_event():
    valid, err = validate_base_message({
        "schema_version": "1.0",
        "timestamp": 123456.0,
    })
    assert not valid
    assert "Missing 'event_type'" in err


def test_validate_sensor_reading_valid():
    valid, err = validate_sensor_reading({
        "schema_version": "1.0",
        "event_type": "sensor.reading",
        "timestamp": 123456.0,
        "intersection_id": "J1",
        "device_id": "esp32_j1",
        "distance_cm": 24.5,
        "vehicle_detected": True,
    })
    assert valid
    assert err is None


def test_validate_sensor_reading_invalid_junction():
    valid, err = validate_sensor_reading({
        "schema_version": "1.0",
        "event_type": "sensor.reading",
        "timestamp": 123456.0,
        "intersection_id": "J99",
        "device_id": "esp32_j1",
        "distance_cm": 24.5,
    })
    assert not valid
    assert "Invalid or missing 'intersection_id'" in err


def test_validate_sensor_reading_missing_device():
    valid, err = validate_sensor_reading({
        "schema_version": "1.0",
        "event_type": "sensor.reading",
        "timestamp": 123456.0,
        "intersection_id": "J1",
        "distance_cm": 24.5,
    })
    assert not valid
    assert "Missing 'device_id'" in err


def test_validate_signal_command_valid():
    valid, err = validate_signal_command({
        "schema_version": "1.0",
        "event_type": "signal.command",
        "timestamp": 123456.0,
        "intersection_id": "J2",
        "red": False,
        "yellow": False,
        "green": True,
        "phase": 0,
    })
    assert valid
    assert err is None


def test_validate_signal_command_missing_state():
    valid, err = validate_signal_command({
        "schema_version": "1.0",
        "event_type": "signal.command",
        "timestamp": 123456.0,
        "intersection_id": "J2",
    })
    assert not valid
    assert "Command must specify" in err


def test_validate_emergency_event_valid():
    valid, err = validate_emergency_event({
        "schema_version": "1.0",
        "event_type": "emergency.detected",
        "timestamp": 123456.0,
        "vehicle_id": "ambulance_01",
        "vehicle_type": "ambulance",
        "intersection_id": "J1",
    })
    assert valid
    assert err is None


def test_validate_emergency_event_missing_vehicle():
    valid, err = validate_emergency_event({
        "schema_version": "1.0",
        "event_type": "emergency.detected",
        "timestamp": 123456.0,
        "intersection_id": "J1",
    })
    assert not valid
    assert "Missing 'vehicle_id'" in err


def test_validate_device_status_valid():
    valid, err = validate_device_status({
        "schema_version": "1.0",
        "event_type": "device.status",
        "timestamp": 123456.0,
        "intersection_id": "J3",
        "device_id": "esp32_j3",
        "status": "online",
    })
    assert valid
    assert err is None


def test_mqtt_client_initialization():
    client = FlowSyncMQTTClient(client_id="test_unit_client", broker_host="127.0.0.1", broker_port=1883)
    assert client.client_id == "test_unit_client"
    assert not client.is_connected


def test_mqtt_client_subscribe_registration():
    client = FlowSyncMQTTClient(client_id="test_sub_client")
    calls = []

    def dummy_callback(topic, data):
        calls.append(data)

    client.subscribe("flowsync/intersection/+/sensors", dummy_callback)
    assert "flowsync/intersection/+/sensors" in client._subscribers
    assert len(client._subscribers["flowsync/intersection/+/sensors"]) == 1


def test_publish_rejection_for_bad_payload():
    client = FlowSyncMQTTClient(client_id="test_pub_client")
    # Payload missing schema_version, event_type, etc.
    res = client.publish("some/topic", {"bad": "data"})
    assert res is False
