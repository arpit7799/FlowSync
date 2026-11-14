"""Traffic management business logic and database persistence service."""

import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from backend.app.models.traffic import (
    BenchmarkMetric,
    DeviceStatus,
    EmergencyEvent,
    Intersection,
    SensorReading,
    SignalState,
    SimulationRun,
)
from backend.app.schemas.traffic import EmergencyPriorityRequest, SensorReadingCreate

ROOT_DIR = Path(__file__).resolve().parents[3]
BENCHMARK_REPORT_PATH = ROOT_DIR / "data/results/benchmark_report.json"


class TrafficService:
    """Service handling traffic telemetry, intersection statuses, and persistence."""

    @staticmethod
    def get_all_intersections(db: Session) -> List[Intersection]:
        return db.query(Intersection).all()

    @staticmethod
    def get_intersection_by_id(db: Session, jid: str) -> Optional[Intersection]:
        return db.query(Intersection).filter(Intersection.id == jid).first()

    @staticmethod
    def update_intersection_state(
        db: Session,
        jid: str,
        mode: str,
        phase: int,
        state: str,
        vehicle_count: int,
        queue_length: int,
    ) -> Optional[Intersection]:
        intersection = db.query(Intersection).filter(Intersection.id == jid).first()
        if not intersection:
            return None

        intersection.current_mode = mode
        intersection.current_phase = phase
        intersection.current_state = state
        intersection.vehicle_count = vehicle_count
        intersection.queue_length = queue_length
        db.commit()
        db.refresh(intersection)
        return intersection

    @staticmethod
    def record_sensor_reading(db: Session, reading_in: SensorReadingCreate) -> SensorReading:
        reading = SensorReading(
            timestamp=reading_in.timestamp,
            intersection_id=reading_in.intersection_id,
            device_id=reading_in.device_id,
            distance_cm=reading_in.distance_cm,
            vehicle_detected=reading_in.vehicle_detected,
            vehicle_count=reading_in.vehicle_count,
            queue_length=reading_in.queue_length,
        )
        db.add(reading)

        # Update intersection stats
        intersection = db.query(Intersection).filter(Intersection.id == reading_in.intersection_id).first()
        if intersection:
            intersection.vehicle_count = reading_in.vehicle_count
            intersection.queue_length = reading_in.queue_length

        db.commit()
        db.refresh(reading)
        return reading

    @staticmethod
    def get_latest_sensor_readings(db: Session, limit: int = 50) -> List[SensorReading]:
        return db.query(SensorReading).order_by(SensorReading.id.desc()).limit(limit).all()

    @staticmethod
    def record_signal_state(
        db: Session,
        jid: str,
        mode: str,
        phase: int,
        state: str,
        duration: float,
        is_emergency: bool = False,
    ) -> SignalState:
        sig = SignalState(
            timestamp=time.time(),
            intersection_id=jid,
            mode=mode,
            active_phase=phase,
            state=state,
            duration=duration,
            is_emergency=is_emergency,
        )
        db.add(sig)

        # Update intersection current state
        intersection = db.query(Intersection).filter(Intersection.id == jid).first()
        if intersection:
            intersection.current_mode = mode
            intersection.current_phase = phase
            intersection.current_state = state

        db.commit()
        db.refresh(sig)
        return sig

    @staticmethod
    def get_latest_signal_states(db: Session, limit: int = 20) -> List[SignalState]:
        return db.query(SignalState).order_by(SignalState.id.desc()).limit(limit).all()

    @staticmethod
    def create_emergency_request(db: Session, req: EmergencyPriorityRequest) -> EmergencyEvent:
        event_id = f"emg_{req.intersection_id}_{req.vehicle_id}_{int(time.time())}"
        ev = EmergencyEvent(
            event_id=event_id,
            vehicle_id=req.vehicle_id,
            vehicle_type=req.vehicle_type,
            junction_id=req.intersection_id,
            incoming_edge=req.incoming_edge,
            requested_phase=req.requested_phase,
            request_time=time.time(),
            status="requested",
            notes=f"Source: {req.source}",
        )
        db.add(ev)
        db.commit()
        db.refresh(ev)
        return ev

    @staticmethod
    def get_emergency_events(db: Session, limit: int = 50) -> List[EmergencyEvent]:
        return db.query(EmergencyEvent).order_by(EmergencyEvent.id.desc()).limit(limit).all()

    @staticmethod
    def update_emergency_status(
        db: Session,
        event_id: str,
        status: str,
        granted_time: Optional[float] = None,
        cleared_time: Optional[float] = None,
        notes: str = "",
    ) -> Optional[EmergencyEvent]:
        ev = db.query(EmergencyEvent).filter(EmergencyEvent.event_id == event_id).first()
        if not ev:
            return None

        ev.status = status
        if granted_time is not None:
            ev.granted_time = granted_time
            ev.response_time = round(granted_time - ev.request_time, 2)
        if cleared_time is not None:
            ev.cleared_time = cleared_time
        if notes:
            ev.notes = f"{ev.notes}; {notes}".strip("; ")

        db.commit()
        db.refresh(ev)
        return ev

    @staticmethod
    def get_benchmark_report() -> Dict[str, Any]:
        """Read benchmark results from generated report file or produce defaults."""
        if BENCHMARK_REPORT_PATH.exists():
            try:
                return json.loads(BENCHMARK_REPORT_PATH.read_text())
            except Exception:
                pass

        return {
            "generated_at": "default",
            "scenarios": {
                "low": {"baseline": {"vehicles": 50, "avg_waiting_time": 2.5}, "adaptive": {"vehicles": 50, "avg_waiting_time": 9.0}},
                "medium": {"baseline": {"vehicles": 150, "avg_waiting_time": 3.73}, "adaptive": {"vehicles": 150, "avg_waiting_time": 26.75}},
                "heavy": {"baseline": {"vehicles": 300, "avg_waiting_time": 3.63}, "adaptive": {"vehicles": 300, "avg_waiting_time": 34.17}},
            },
        }

    @staticmethod
    def record_device_heartbeat(
        db: Session,
        device_id: str,
        intersection_id: str,
        status: str = "online",
        uptime_seconds: float = 0.0,
        ip_address: str = "127.0.0.1",
    ) -> DeviceStatus:
        dev = db.query(DeviceStatus).filter(DeviceStatus.device_id == device_id).first()
        if not dev:
            dev = DeviceStatus(
                device_id=device_id,
                intersection_id=intersection_id,
                status=status,
                uptime_seconds=uptime_seconds,
                ip_address=ip_address,
            )
            db.add(dev)
        else:
            dev.status = status
            dev.uptime_seconds = uptime_seconds
            dev.ip_address = ip_address

        db.commit()
        db.refresh(dev)
        return dev

    @staticmethod
    def get_all_devices(db: Session) -> List[DeviceStatus]:
        return db.query(DeviceStatus).all()
