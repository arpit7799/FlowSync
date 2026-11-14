"""MQTT communication package for FlowSync."""

from .client import FlowSyncMQTTClient
from .topics import (
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
from .validator import (
    validate_base_message,
    validate_device_status,
    validate_emergency_event,
    validate_sensor_reading,
    validate_signal_command,
)

__all__ = [
    "FlowSyncMQTTClient",
    "get_sensors_topic",
    "get_signals_topic",
    "get_status_topic",
    "parse_intersection_id",
    "EMERGENCY_DETECTED",
    "EMERGENCY_PRIORITY",
    "SYSTEM_HEALTH",
    "ALL_INTERSECTION_SENSORS",
    "ALL_INTERSECTION_SIGNALS",
    "ALL_INTERSECTION_STATUS",
    "ALL_EMERGENCY",
    "validate_base_message",
    "validate_sensor_reading",
    "validate_signal_command",
    "validate_emergency_event",
    "validate_device_status",
]
