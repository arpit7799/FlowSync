"""MQTT topic constants and parsing utilities for FlowSync."""

from typing import Optional

# Root namespace
ROOT = "flowsync"

# Topic templates
INTERSECTION_SENSORS_TEMPLATE = f"{ROOT}/intersection/{{id}}/sensors"
INTERSECTION_SIGNALS_TEMPLATE = f"{ROOT}/intersection/{{id}}/signals"
INTERSECTION_STATUS_TEMPLATE  = f"{ROOT}/intersection/{{id}}/status"

# System-wide topics
EMERGENCY_DETECTED = f"{ROOT}/emergency/detected"
EMERGENCY_PRIORITY = f"{ROOT}/emergency/priority"
SYSTEM_HEALTH      = f"{ROOT}/system/health"

# Wildcard topics for listeners
ALL_INTERSECTION_SENSORS = f"{ROOT}/intersection/+/sensors"
ALL_INTERSECTION_SIGNALS = f"{ROOT}/intersection/+/signals"
ALL_INTERSECTION_STATUS  = f"{ROOT}/intersection/+/status"
ALL_EMERGENCY            = f"{ROOT}/emergency/#"


def get_sensors_topic(intersection_id: str) -> str:
    """Get topic for publishing/subscribing to intersection sensor readings."""
    return INTERSECTION_SENSORS_TEMPLATE.format(id=intersection_id)


def get_signals_topic(intersection_id: str) -> str:
    """Get topic for publishing/subscribing to intersection traffic signal commands."""
    return INTERSECTION_SIGNALS_TEMPLATE.format(id=intersection_id)


def get_status_topic(intersection_id: str) -> str:
    """Get topic for publishing/subscribing to intersection device status."""
    return INTERSECTION_STATUS_TEMPLATE.format(id=intersection_id)


def parse_intersection_id(topic: str) -> Optional[str]:
    """Extract intersection ID from topic string (e.g. 'flowsync/intersection/J1/sensors' -> 'J1')."""
    parts = topic.split("/")
    if len(parts) >= 4 and parts[0] == ROOT and parts[1] == "intersection":
        return parts[2]
    return None
