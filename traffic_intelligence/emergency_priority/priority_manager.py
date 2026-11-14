"""Emergency vehicle priority management for FlowSync."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional
import uuid


class PriorityStatus(str, Enum):
    IDLE = "idle"
    REQUESTED = "requested"
    CLEARING_EXISTING = "clearing_existing"  # Transitioning via yellow/all-red
    ACTIVE = "active"                        # Green corridor active
    CLEARED = "cleared"
    CANCELLED = "cancelled"


@dataclass
class EmergencyEventRecord:
    event_id: str
    vehicle_id: str
    vehicle_type: str
    junction: str
    incoming_edge: str
    requested_phase: int
    request_time: float
    granted_time: Optional[float] = None
    cleared_time: Optional[float] = None
    response_time: Optional[float] = None
    status: PriorityStatus = PriorityStatus.REQUESTED
    notes: str = ""


@dataclass
class JunctionPriorityState:
    junction: str
    status: PriorityStatus = PriorityStatus.IDLE
    active_event_id: Optional[str] = None
    active_vehicle_id: Optional[str] = None
    target_phase: Optional[int] = None
    hold_until: float = 0.0
    preempted_from_phase: Optional[int] = None
    preempted_from_mode: Optional[str] = None


class EmergencyPriorityManager:
    """Coordinates emergency vehicle preemption and safe phase clearance."""

    def __init__(self, yellow_clearance: float = 3.0, all_red_clearance: float = 1.0, max_green_hold: float = 45.0):
        self.yellow_clearance = yellow_clearance
        self.all_red_clearance = all_red_clearance
        self.max_green_hold = max_green_hold

        self.junction_states: Dict[str, JunctionPriorityState] = {}
        self.event_history: List[EmergencyEventRecord] = []
        self._active_events: Dict[str, EmergencyEventRecord] = {}

    def get_junction_state(self, junction: str) -> JunctionPriorityState:
        if junction not in self.junction_states:
            self.junction_states[junction] = JunctionPriorityState(junction=junction)
        return self.junction_states[junction]

    def request_priority(
        self,
        vehicle_id: str,
        vehicle_type: str,
        junction: str,
        incoming_edge: str,
        requested_phase: int,
        current_time: float,
        current_phase: Optional[int] = None,
        current_mode: str = "green",
    ) -> Optional[EmergencyEventRecord]:
        """Request emergency green preemption at a junction.
        
        Guards against duplicate/repeated requests while one is active for the same vehicle.
        """
        state = self.get_junction_state(junction)

        # Idempotency / duplicate protection
        if state.status in (PriorityStatus.REQUESTED, PriorityStatus.CLEARING_EXISTING, PriorityStatus.ACTIVE):
            if state.active_vehicle_id == vehicle_id:
                # Existing request for same vehicle is already processing
                return self._active_events.get(state.active_event_id or "")

        event_id = f"emg_{junction}_{vehicle_id}_{int(current_time)}_{uuid.uuid4().hex[:6]}"
        event = EmergencyEventRecord(
            event_id=event_id,
            vehicle_id=vehicle_id,
            vehicle_type=vehicle_type,
            junction=junction,
            incoming_edge=incoming_edge,
            requested_phase=requested_phase,
            request_time=current_time,
            status=PriorityStatus.REQUESTED,
        )

        state.active_event_id = event_id
        state.active_vehicle_id = vehicle_id
        state.target_phase = requested_phase
        state.preempted_from_phase = current_phase
        state.preempted_from_mode = current_mode

        # If current phase is already requested green, we grant immediately
        if current_phase == requested_phase and current_mode == "green":
            state.status = PriorityStatus.ACTIVE
            event.status = PriorityStatus.ACTIVE
            event.granted_time = current_time
            event.response_time = 0.0
            state.hold_until = current_time + self.max_green_hold
        else:
            state.status = PriorityStatus.CLEARING_EXISTING
            event.status = PriorityStatus.CLEARING_EXISTING

        self._active_events[event_id] = event
        self.event_history.append(event)
        return event

    def on_phase_granted(self, junction: str, current_time: float):
        """Called when signal safely transitions to emergency green."""
        state = self.get_junction_state(junction)
        if state.status == PriorityStatus.CLEARING_EXISTING:
            state.status = PriorityStatus.ACTIVE
            state.hold_until = current_time + self.max_green_hold
            if state.active_event_id and state.active_event_id in self._active_events:
                event = self._active_events[state.active_event_id]
                event.status = PriorityStatus.ACTIVE
                event.granted_time = current_time
                event.response_time = round(current_time - event.request_time, 2)

    def clear_priority(self, junction: str, current_time: float, reason: str = "passed") -> Optional[EmergencyEventRecord]:
        """Release emergency priority and return junction to normal control."""
        state = self.get_junction_state(junction)
        if state.status == PriorityStatus.IDLE:
            return None

        event = None
        if state.active_event_id and state.active_event_id in self._active_events:
            event = self._active_events.pop(state.active_event_id)
            event.status = PriorityStatus.CLEARED
            event.cleared_time = current_time
            event.notes = f"Cleared: {reason}"

        state.status = PriorityStatus.IDLE
        state.active_event_id = None
        state.active_vehicle_id = None
        state.target_phase = None
        state.hold_until = 0.0
        return event

    def cancel_priority(self, junction: str, current_time: float, reason: str = "cancelled") -> Optional[EmergencyEventRecord]:
        """Manually cancel an active priority request."""
        state = self.get_junction_state(junction)
        if state.status == PriorityStatus.IDLE:
            return None

        event = None
        if state.active_event_id and state.active_event_id in self._active_events:
            event = self._active_events.pop(state.active_event_id)
            event.status = PriorityStatus.CANCELLED
            event.cleared_time = current_time
            event.notes = f"Cancelled: {reason}"

        state.status = PriorityStatus.IDLE
        state.active_event_id = None
        state.active_vehicle_id = None
        state.target_phase = None
        state.hold_until = 0.0
        return event

    def is_priority_active(self, junction: str) -> bool:
        state = self.get_junction_state(junction)
        return state.status in (PriorityStatus.REQUESTED, PriorityStatus.CLEARING_EXISTING, PriorityStatus.ACTIVE)

    def get_active_events(self) -> List[EmergencyEventRecord]:
        return list(self._active_events.values())

    def get_history(self) -> List[EmergencyEventRecord]:
        return list(self.event_history)
