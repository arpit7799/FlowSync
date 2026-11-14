"""JSON message schema validation for FlowSync MQTT messages."""

from typing import Any, Dict, Optional, Tuple

VALID_EVENT_TYPES = {
    "sensor.reading",
    "signal.command",
    "signal.status",
    "emergency.detected",
    "emergency.priority",
    "emergency.cleared",
    "device.status",
    "system.health",
}

VALID_INTERSECTIONS = {"J1", "J2", "J3", "J4"}


def validate_base_message(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate common base envelope for all FlowSync MQTT messages."""
    if not isinstance(payload, dict):
        return False, "Payload must be a JSON object"

    if "schema_version" not in payload:
        return False, "Missing 'schema_version'"

    if payload.get("schema_version") != "1.0":
        return False, f"Unsupported schema_version: {payload.get('schema_version')}"

    if "event_type" not in payload:
        return False, "Missing 'event_type'"

    if payload.get("event_type") not in VALID_EVENT_TYPES:
        return False, f"Invalid event_type: {payload.get('event_type')}"

    if "timestamp" not in payload:
        return False, "Missing 'timestamp'"

    return True, None


def validate_sensor_reading(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate sensor telemetry payload."""
    valid, err = validate_base_message(payload)
    if not valid:
        return False, err

    if payload.get("event_type") != "sensor.reading":
        return False, "Expected event_type 'sensor.reading'"

    jid = payload.get("intersection_id")
    if not jid or jid not in VALID_INTERSECTIONS:
        return False, f"Invalid or missing 'intersection_id': {jid}"

    if not payload.get("device_id"):
        return False, "Missing 'device_id'"

    if "distance_cm" not in payload and "vehicle_count" not in payload:
        return False, "Payload must contain 'distance_cm' or 'vehicle_count'"

    return True, None


def validate_signal_command(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate traffic signal control command."""
    valid, err = validate_base_message(payload)
    if not valid:
        return False, err

    if payload.get("event_type") not in ("signal.command", "traffic.signal.command"):
        return False, "Expected event_type 'signal.command'"

    jid = payload.get("intersection_id")
    if not jid or jid not in VALID_INTERSECTIONS:
        return False, f"Invalid or missing 'intersection_id': {jid}"

    # Must have either boolean states (red/yellow/green) or phase index/state
    has_bools = all(k in payload for k in ("red", "yellow", "green"))
    has_phase = "phase" in payload or "phase_id" in payload or "state" in payload

    if not (has_bools or has_phase):
        return False, "Command must specify red/yellow/green booleans or phase"

    return True, None


def validate_emergency_event(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate emergency vehicle priority event."""
    valid, err = validate_base_message(payload)
    if not valid:
        return False, err

    if not payload.get("event_type", "").startswith("emergency."):
        return False, "Expected an emergency.* event_type"

    if "vehicle_id" not in payload and "source" not in payload:
        return False, "Missing 'vehicle_id' or 'source'"

    if payload.get("intersection_id") and payload["intersection_id"] not in VALID_INTERSECTIONS:
        return False, f"Invalid 'intersection_id': {payload.get('intersection_id')}"

    return True, None


def validate_device_status(payload: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """Validate IoT device heartbeat / health status message."""
    valid, err = validate_base_message(payload)
    if not valid:
        return False, err

    if payload.get("event_type") not in ("device.status", "system.health"):
        return False, "Expected 'device.status' or 'system.health'"

    if not payload.get("device_id") and not payload.get("source"):
        return False, "Missing 'device_id' or 'source'"

    return True, None
