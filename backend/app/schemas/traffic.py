"""Pydantic schemas for FlowSync API requests and responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# Base API envelope
class BaseResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


# Intersection schemas
class IntersectionBase(BaseModel):
    id: str
    name: str
    location_x: float
    location_y: float
    num_lanes: int = 12
    status: str = "online"


class IntersectionResponse(IntersectionBase):
    current_phase: int = 0
    current_mode: str = "initial"
    current_state: str = "GGggrrrrGGGg"
    vehicle_count: int = 0
    queue_length: int = 0
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Sensor schemas
class SensorReadingCreate(BaseModel):
    intersection_id: str
    device_id: str
    distance_cm: float
    vehicle_detected: bool = False
    vehicle_count: int = 0
    queue_length: int = 0
    timestamp: float


class SensorReadingResponse(SensorReadingCreate):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Signal schemas
class SignalCommandRequest(BaseModel):
    intersection_id: str
    red: bool = False
    yellow: bool = False
    green: bool = True
    phase: int = 0
    duration: float = 25.0
    emergency_priority: bool = False


class SignalStateResponse(BaseModel):
    id: int
    intersection_id: str
    mode: str
    active_phase: int
    state: str
    is_emergency: bool
    duration: float
    timestamp: float

    model_config = ConfigDict(from_attributes=True)


# Emergency schemas
class EmergencyPriorityRequest(BaseModel):
    vehicle_id: str
    vehicle_type: str = "ambulance"
    intersection_id: str
    incoming_edge: Optional[str] = "N_J1"
    requested_phase: int = 0
    source: str = "api_manual"


class EmergencyEventResponse(BaseModel):
    id: int
    event_id: str
    vehicle_id: str
    vehicle_type: str
    junction_id: str
    incoming_edge: Optional[str] = None
    requested_phase: int
    request_time: float
    granted_time: Optional[float] = None
    cleared_time: Optional[float] = None
    response_time: Optional[float] = None
    status: str
    notes: Optional[str] = ""
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# Simulation & Benchmark schemas
class SimulationStartRequest(BaseModel):
    scenario: str = Field(default="low", description="low, medium, heavy, or emergency")
    controller_type: str = Field(default="adaptive", description="baseline or adaptive")


class SimulationRunResponse(BaseModel):
    id: int
    scenario: str
    controller_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    vehicles_inserted: int
    vehicles_arrived: int
    peak_queue: int
    status: str

    model_config = ConfigDict(from_attributes=True)


class BenchmarkComparisonResponse(BaseModel):
    scenario: str
    baseline: Dict[str, Any]
    adaptive: Dict[str, Any]
    comparison: Dict[str, Any]


# Device status schema
class DeviceStatusResponse(BaseModel):
    device_id: str
    intersection_id: str
    status: str
    uptime_seconds: float
    last_heartbeat: datetime
    ip_address: str

    model_config = ConfigDict(from_attributes=True)
