"""REST API Endpoints for FlowSync."""

from datetime import datetime
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.traffic import (
    BaseResponse,
    BenchmarkComparisonResponse,
    DeviceStatusResponse,
    EmergencyEventResponse,
    EmergencyPriorityRequest,
    IntersectionResponse,
    SensorReadingCreate,
    SensorReadingResponse,
    SignalCommandRequest,
    SignalStateResponse,
    SimulationRunResponse,
    SimulationStartRequest,
)
from backend.app.services.traffic_service import TrafficService

router = APIRouter()


# ---------------------------------------------------------------------------
# Health & System
# ---------------------------------------------------------------------------
@router.get("/health", tags=["System"])
def get_system_health():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "FlowSync Backend API",
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# Intersections & Live State
# ---------------------------------------------------------------------------
@router.get("/intersections", response_model=List[IntersectionResponse], tags=["Intersections"])
def list_intersections(db: Session = Depends(get_db)):
    """List all 4 controlled traffic intersections (J1, J2, J3, J4)."""
    return TrafficService.get_all_intersections(db)


@router.get("/intersections/{intersection_id}", response_model=IntersectionResponse, tags=["Intersections"])
def get_intersection(intersection_id: str, db: Session = Depends(get_db)):
    """Get real-time details and signal phase for a specific intersection."""
    intersection = TrafficService.get_intersection_by_id(db, intersection_id)
    if not intersection:
        raise HTTPException(status_code=404, detail=f"Intersection '{intersection_id}' not found")
    return intersection


@router.get("/traffic/state", tags=["Traffic State"])
def get_current_traffic_state(db: Session = Depends(get_db)):
    """Aggregate real-time traffic state for the entire 2x2 grid."""
    intersections = TrafficService.get_all_intersections(db)
    total_vehicles = sum(i.vehicle_count for i in intersections)
    total_queue = sum(i.queue_length for i in intersections)

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "total_vehicles": total_vehicles,
        "total_queue": total_queue,
        "active_intersections": len(intersections),
        "intersections": [
            {
                "id": i.id,
                "name": i.name,
                "status": i.status,
                "mode": i.current_mode,
                "phase": i.current_phase,
                "state": i.current_state,
                "vehicles": i.vehicle_count,
                "queue": i.queue_length,
            }
            for i in intersections
        ],
    }


# ---------------------------------------------------------------------------
# Sensors Telemetry
# ---------------------------------------------------------------------------
@router.get("/sensors/telemetry", response_model=List[SensorReadingResponse], tags=["Sensors"])
def get_sensor_telemetry(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve recent ultrasonic / presence sensor readings."""
    return TrafficService.get_latest_sensor_readings(db, limit=limit)


@router.post("/sensors/telemetry", response_model=SensorReadingResponse, status_code=status.HTTP_201_CREATED, tags=["Sensors"])
def record_sensor_telemetry(
    reading: SensorReadingCreate,
    db: Session = Depends(get_db),
):
    """Ingest sensor reading from virtual hardware or simulation."""
    return TrafficService.record_sensor_reading(db, reading)


# ---------------------------------------------------------------------------
# Signal Control
# ---------------------------------------------------------------------------
@router.get("/signals/status", response_model=List[SignalStateResponse], tags=["Signals"])
def get_signal_statuses(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get history of signal phase transitions across intersections."""
    return TrafficService.get_latest_signal_states(db, limit=limit)


@router.post("/signals/command", response_model=BaseResponse, tags=["Signals"])
def send_signal_command(
    command: SignalCommandRequest,
    db: Session = Depends(get_db),
):
    """Manual or external override command for an intersection signal."""
    intersection = TrafficService.get_intersection_by_id(db, command.intersection_id)
    if not intersection:
        raise HTTPException(status_code=404, detail=f"Intersection '{command.intersection_id}' not found")

    mode = "green" if command.green else ("yellow" if command.yellow else "all_red")
    state_str = intersection.current_state  # fallback
    if command.green:
        state_str = "GGggrrrrGGGg" if command.phase == 0 else "rrrrGGGgGrrr"
    elif command.yellow:
        state_str = "yyyyrrrrGyyy"
    else:
        state_str = "rrrrrrrrrrrr"

    TrafficService.record_signal_state(
        db,
        jid=command.intersection_id,
        mode=mode,
        phase=command.phase,
        state=state_str,
        duration=command.duration,
        is_emergency=command.emergency_priority,
    )

    return BaseResponse(
        success=True,
        message=f"Signal command applied to {command.intersection_id} (mode={mode}, phase={command.phase})",
    )


# ---------------------------------------------------------------------------
# Emergency Priority
# ---------------------------------------------------------------------------
@router.get("/emergency/requests", response_model=List[EmergencyEventResponse], tags=["Emergency Priority"])
def list_emergency_events(
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List recent emergency vehicle priority requests and their statuses."""
    return TrafficService.get_emergency_events(db, limit=limit)


@router.post("/emergency/requests", response_model=EmergencyEventResponse, status_code=status.HTTP_201_CREATED, tags=["Emergency Priority"])
def create_emergency_priority_request(
    request: EmergencyPriorityRequest,
    db: Session = Depends(get_db),
):
    """Trigger emergency vehicle preemption at an intersection."""
    intersection = TrafficService.get_intersection_by_id(db, request.intersection_id)
    if not intersection:
        raise HTTPException(status_code=404, detail=f"Intersection '{request.intersection_id}' not found")

    event = TrafficService.create_emergency_request(db, request)
    return event


@router.post("/emergency/requests/{event_id}/cancel", response_model=BaseResponse, tags=["Emergency Priority"])
def cancel_emergency_priority_request(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Cancel an active emergency priority request."""
    updated = TrafficService.update_emergency_status(db, event_id=event_id, status="cancelled", notes="Manual cancellation via API")
    if not updated:
        raise HTTPException(status_code=404, detail=f"Emergency event '{event_id}' not found")

    return BaseResponse(
        success=True,
        message=f"Emergency priority event '{event_id}' cancelled.",
    )


# ---------------------------------------------------------------------------
# Benchmarks & Analytics
# ---------------------------------------------------------------------------
@router.get("/benchmarks", tags=["Analytics"])
def get_benchmark_comparison():
    """Get baseline (actuated) vs adaptive control benchmark metrics."""
    return TrafficService.get_benchmark_report()


# ---------------------------------------------------------------------------
# IoT Devices
# ---------------------------------------------------------------------------
@router.get("/devices", response_model=List[DeviceStatusResponse], tags=["IoT Devices"])
def list_devices(db: Session = Depends(get_db)):
    """List connected virtual ESP32 hardware devices."""
    return TrafficService.get_all_devices(db)
