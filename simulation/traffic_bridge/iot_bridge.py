"""SUMO to Virtual Hardware / IoT Bridge for FlowSync."""

from dataclasses import dataclass
import logging
import math
import time
from typing import Dict, List, Optional
import traci

from iot.mqtt.client import FlowSyncMQTTClient
from iot.mqtt.topics import (
    ALL_EMERGENCY,
    ALL_INTERSECTION_SIGNALS,
    get_sensors_topic,
    get_signals_topic,
    get_status_topic,
    parse_intersection_id,
)
from iot.mqtt.validator import validate_signal_command
from traffic_intelligence.emergency_priority.priority_manager import (
    EmergencyPriorityManager,
    PriorityStatus,
)

logger = logging.getLogger("flowsync.bridge")

INTERSECTION_MAPPING = {
    "J1": {"device_id": "esp32_j1_controller", "approach_edges": ["N_J1", "J2_J1", "J3_J1"]},
    "J2": {"device_id": "esp32_j2_controller", "approach_edges": ["J1_J2", "J4_J2", "S_J2"]},
    "J3": {"device_id": "esp32_j3_controller", "approach_edges": ["J1_J3", "J4_J3", "W_J3"]},
    "J4": {"device_id": "esp32_j4_controller", "approach_edges": ["J2_J4", "J3_J4", "E_J4"]},
}


def queue_to_ultrasonic_distance(queue_count: int) -> float:
    """Convert queue count into realistic simulated ultrasonic sensor distance (cm).
    
    A vehicle directly at stop line gives ~15-25 cm distance.
    As queue extends or clears, distance increases up to 400 cm (clear).
    """
    if queue_count <= 0:
        return 350.0 + (queue_count * 10.0)  # ~350cm = clear lane
    elif queue_count == 1:
        return 22.5
    elif queue_count == 2:
        return 18.0
    else:
        return 12.0


class SUMOIoTBridge:
    """Synchronizes SUMO simulation state with virtual IoT hardware via MQTT."""

    def __init__(
        self,
        mqtt_client: FlowSyncMQTTClient,
        emergency_manager: Optional[EmergencyPriorityManager] = None,
        sensor_publish_interval: float = 1.0,
    ):
        self.mqtt = mqtt_client
        self.emergency_manager = emergency_manager
        self.sensor_publish_interval = sensor_publish_interval
        self._last_sensor_publish = 0.0
        self._pending_commands: Dict[str, dict] = {}

    def setup_subscriptions(self):
        """Subscribe to incoming commands from virtual hardware and manual overrides."""
        self.mqtt.subscribe(ALL_INTERSECTION_SIGNALS, self._on_signal_command)
        self.mqtt.subscribe(ALL_EMERGENCY, self._on_emergency_event)
        logger.info("SUMO IoT Bridge registered MQTT subscriptions")

    def _on_signal_command(self, topic: str, payload: dict):
        """Receive signal command from ESP32 or external controller."""
        valid, err = validate_signal_command(payload)
        if not valid:
            logger.warning("Rejected invalid signal command from %s: %s", topic, err)
            return

        intersection_id = payload.get("intersection_id") or parse_intersection_id(topic)
        if intersection_id in INTERSECTION_MAPPING:
            self._pending_commands[intersection_id] = payload
            logger.debug("Queued signal command for %s: %s", intersection_id, payload)

    def _on_emergency_event(self, topic: str, payload: dict):
        """Receive emergency event from ESP32 push button or camera."""
        if not self.emergency_manager:
            return

        junction = payload.get("intersection_id", "J1")
        vtype = payload.get("vehicle_type", "ambulance")
        vid = payload.get("vehicle_id", f"emg_btn_{junction}")
        current_time = time.time()

        logger.info("Bridge received emergency event on %s for junction %s", topic, junction)
        self.emergency_manager.request_priority(
            vehicle_id=vid,
            vehicle_type=vtype,
            junction=junction,
            incoming_edge=INTERSECTION_MAPPING.get(junction, {}).get("approach_edges", ["N_J1"])[0],
            requested_phase=0,
            current_time=current_time,
        )

    def sync_sensors(self, sim_time: float):
        """Extract SUMO vehicle presence and publish virtual sensor telemetry."""
        if (sim_time - self._last_sensor_publish) < self.sensor_publish_interval:
            return
        self._last_sensor_publish = sim_time

        for jid, info in INTERSECTION_MAPPING.items():
            device_id = info["device_id"]
            total_queue = 0
            total_vehicles = 0

            for edge in info["approach_edges"]:
                try:
                    num_lanes = traci.edge.getLaneNumber(edge)
                    for lane_idx in range(num_lanes):
                        lane_id = f"{edge}_{lane_idx}"
                        total_queue += traci.lane.getLastStepHaltingNumber(lane_id)
                        total_vehicles += traci.lane.getLastStepVehicleNumber(lane_id)
                except traci.TraCIException:
                    continue

            distance_cm = queue_to_ultrasonic_distance(total_queue)
            vehicle_detected = total_vehicles > 0

            self.mqtt.publish_sensor_reading(
                intersection_id=jid,
                device_id=device_id,
                distance_cm=distance_cm,
                vehicle_detected=vehicle_detected,
                vehicle_count=total_vehicles,
                queue_length=total_queue,
            )

    def apply_pending_commands(self, runtimes: dict):
        """Validate and apply pending hardware commands safely to SUMO intersections."""
        if not self._pending_commands:
            return

        for jid, cmd in list(self._pending_commands.items()):
            runtime = runtimes.get(jid)
            if not runtime:
                continue

            # Check if command has a raw state string
            state = cmd.get("state")
            if state:
                # Must be 12 chars
                if len(state) == len(runtime.green_states[0]):
                    try:
                        traci.trafficlight.setRedYellowGreenState(jid, state)
                    except traci.TraCIException as exc:
                        logger.error("Failed to set state for %s: %s", jid, exc)

            # Check boolean red/yellow/green
            elif all(k in cmd for k in ("red", "yellow", "green")):
                # Map to valid program phase
                if cmd["green"]:
                    target_phase = cmd.get("phase", 0)
                    if target_phase in runtime.green_states:
                        try:
                            traci.trafficlight.setRedYellowGreenState(jid, runtime.green_states[target_phase])
                            runtime.current_phase = target_phase
                            runtime.mode = "green"
                        except traci.TraCIException as exc:
                            logger.error("Failed setting green phase for %s: %s", jid, exc)
                elif cmd["yellow"]:
                    curr = runtime.current_phase if runtime.current_phase is not None else 0
                    try:
                        traci.trafficlight.setRedYellowGreenState(jid, runtime.yellow_states[curr])
                        runtime.mode = "yellow"
                    except traci.TraCIException as exc:
                        logger.error("Failed setting yellow for %s: %s", jid, exc)
                elif cmd["red"]:
                    try:
                        traci.trafficlight.setRedYellowGreenState(jid, runtime.all_red_state)
                        runtime.mode = "all_red"
                    except traci.TraCIException as exc:
                        logger.error("Failed setting all-red for %s: %s", jid, exc)

        self._pending_commands.clear()
