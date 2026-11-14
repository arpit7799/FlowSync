"""FlowSync MQTT Client with auto-reconnection, validation, and callback routing."""

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional
import paho.mqtt.client as mqtt

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
)
from .validator import (
    validate_base_message,
    validate_emergency_event,
    validate_sensor_reading,
    validate_signal_command,
)

logger = logging.getLogger("flowsync.mqtt")


class FlowSyncMQTTClient:
    """Production-grade MQTT client for FlowSync traffic management."""

    def __init__(
        self,
        client_id: str = "flowsync_client",
        broker_host: str = "localhost",
        broker_port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        keepalive: int = 60,
    ):
        self.client_id = client_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.keepalive = keepalive

        self._connected = False
        self._lock = threading.Lock()
        self._subscribers: Dict[str, List[Callable[[str, Dict[str, Any]], None]]] = {}

        # Initialize paho MQTT client
        # Support callback api version if available
        try:
            self._client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                client_id=self.client_id,
            )
        except (AttributeError, TypeError):
            self._client = mqtt.Client(client_id=self.client_id)

        if self.username and self.password:
            self._client.username_pw_set(self.username, self.password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        # Reconnect with exponential backoff: 1s min, 30s max
        self._client.reconnect_delay_set(min_delay=1, max_delay=30)

    @property
    def is_connected(self) -> bool:
        return self._connected

    def connect(self, timeout: float = 3.0) -> bool:
        """Connect to MQTT broker and start background network thread."""
        try:
            logger.info("Connecting to MQTT broker at %s:%d...", self.broker_host, self.broker_port)
            self._client.connect(self.broker_host, self.broker_port, self.keepalive)
            self._client.loop_start()

            # Wait for connection flag with timeout
            start = time.time()
            while not self._connected and (time.time() - start) < timeout:
                time.sleep(0.05)

            if self._connected:
                logger.info("MQTT client '%s' connected successfully.", self.client_id)
                return True
            else:
                logger.warning("MQTT connection pending/degraded for '%s' (running asynchronously).", self.client_id)
                return False
        except Exception as exc:
            logger.error("Failed to connect to MQTT broker (%s:%d): %s", self.broker_host, self.broker_port, exc)
            return False

    def disconnect(self):
        """Disconnect and stop background loop."""
        try:
            self._client.loop_stop()
            self._client.disconnect()
            self._connected = False
            logger.info("MQTT client '%s' disconnected.", self.client_id)
        except Exception as exc:
            logger.error("Error during MQTT disconnect: %s", exc)

    def subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None], qos: int = 1):
        """Register callback and subscribe to topic."""
        with self._lock:
            if topic not in self._subscribers:
                self._subscribers[topic] = []
            self._subscribers[topic].append(callback)

        if self._connected:
            self._client.subscribe(topic, qos=qos)
            logger.debug("Subscribed to MQTT topic '%s' (qos=%d)", topic, qos)

    def publish(
        self,
        topic: str,
        payload: Dict[str, Any],
        qos: int = 0,
        retain: bool = False,
    ) -> bool:
        """Publish JSON payload to topic with validation."""
        valid, err = validate_base_message(payload)
        if not valid:
            logger.warning("MQTT publish rejected invalid payload for topic %s: %s", topic, err)
            return False

        try:
            json_str = json.dumps(payload)
            info = self._client.publish(topic, json_str, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as exc:
            logger.error("MQTT publish error on topic %s: %s", topic, exc)
            return False

    # Convenience publication helpers
    def publish_sensor_reading(
        self,
        intersection_id: str,
        device_id: str,
        distance_cm: float,
        vehicle_detected: bool,
        vehicle_count: int = 0,
        queue_length: int = 0,
    ) -> bool:
        topic = get_sensors_topic(intersection_id)
        payload = {
            "schema_version": "1.0",
            "event_type": "sensor.reading",
            "timestamp": time.time(),
            "intersection_id": intersection_id,
            "device_id": device_id,
            "distance_cm": round(distance_cm, 1),
            "vehicle_detected": vehicle_detected,
            "vehicle_count": vehicle_count,
            "queue_length": queue_length,
        }
        return self.publish(topic, payload, qos=0)

    def publish_signal_command(
        self,
        intersection_id: str,
        red: bool,
        yellow: bool,
        green: bool,
        phase_index: int,
        duration: float,
        emergency_priority: bool = False,
    ) -> bool:
        topic = get_signals_topic(intersection_id)
        payload = {
            "schema_version": "1.0",
            "event_type": "signal.command",
            "timestamp": time.time(),
            "intersection_id": intersection_id,
            "red": red,
            "yellow": yellow,
            "green": green,
            "phase": phase_index,
            "duration": round(duration, 1),
            "emergency_priority": emergency_priority,
        }
        return self.publish(topic, payload, qos=1)

    def publish_emergency_detected(
        self,
        intersection_id: str,
        vehicle_id: str,
        vehicle_type: str = "ambulance",
        source: str = "sumo_detector",
        corridor: Optional[str] = None,
    ) -> bool:
        payload = {
            "schema_version": "1.0",
            "event_type": "emergency.detected",
            "timestamp": time.time(),
            "intersection_id": intersection_id,
            "vehicle_id": vehicle_id,
            "vehicle_type": vehicle_type,
            "source": source,
            "corridor": corridor or "active_route",
        }
        return self.publish(EMERGENCY_DETECTED, payload, qos=1)

    def publish_device_status(
        self,
        intersection_id: str,
        device_id: str,
        status: str = "online",
        uptime_seconds: float = 0.0,
    ) -> bool:
        topic = get_status_topic(intersection_id)
        payload = {
            "schema_version": "1.0",
            "event_type": "device.status",
            "timestamp": time.time(),
            "intersection_id": intersection_id,
            "device_id": device_id,
            "status": status,
            "uptime_seconds": round(uptime_seconds, 1),
        }
        return self.publish(topic, payload, qos=1, retain=True)

    def publish_system_health(self, components_status: Dict[str, str]) -> bool:
        payload = {
            "schema_version": "1.0",
            "event_type": "system.health",
            "timestamp": time.time(),
            "source": "flowsync_core",
            "components": components_status,
        }
        return self.publish(SYSTEM_HEALTH, payload, qos=1, retain=True)

    # Internal MQTT Callbacks
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        rc_code = rc.value if hasattr(rc, "value") else rc
        if rc_code == 0:
            self._connected = True
            logger.info("Connected to MQTT Broker!")

            # Re-subscribe to all registered topics
            with self._lock:
                for topic in self._subscribers.keys():
                    client.subscribe(topic, qos=1)
        else:
            self._connected = False
            logger.warning("MQTT connection rejected with code %s", rc_code)

    def _on_disconnect(self, client, userdata, rc, properties=None):
        self._connected = False
        logger.warning("Disconnected from MQTT broker (rc=%s). Auto-reconnecting...", rc)

    def _on_message(self, client, userdata, msg):
        try:
            raw_payload = msg.payload.decode("utf-8")
            data = json.loads(raw_payload)
        except Exception as exc:
            logger.error("Failed to decode MQTT message on '%s': %s", msg.topic, exc)
            return

        # Deliver to matched subscribers
        with self._lock:
            for pattern, callbacks in self._subscribers.items():
                if mqtt.topic_matches_sub(pattern, msg.topic):
                    for cb in callbacks:
                        try:
                            cb(msg.topic, data)
                        except Exception as cb_err:
                            logger.error("Error in MQTT callback for %s: %s", msg.topic, cb_err)
