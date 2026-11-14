"""SQLAlchemy models for FlowSync traffic management."""

from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Intersection(Base):
    __tablename__ = "intersections"

    id = Column(String(10), primary_key=True)  # J1, J2, J3, J4
    name = Column(String(100), nullable=False)
    location_x = Column(Float, default=0.0)
    location_y = Column(Float, default=0.0)
    num_lanes = Column(Integer, default=12)
    status = Column(String(20), default="online")  # online, offline, degraded
    current_phase = Column(Integer, default=0)
    current_mode = Column(String(20), default="initial")
    current_state = Column(String(30), default="GGggrrrrGGGg")
    vehicle_count = Column(Integer, default=0)
    queue_length = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sensor_readings = relationship("SensorReading", back_populates="intersection", cascade="all, delete-orphan")
    signal_states = relationship("SignalState", back_populates="intersection", cascade="all, delete-orphan")
    emergency_events = relationship("EmergencyEvent", back_populates="intersection", cascade="all, delete-orphan")


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    intersection_id = Column(String(10), ForeignKey("intersections.id"), nullable=False, index=True)
    device_id = Column(String(50), nullable=False)
    distance_cm = Column(Float, nullable=False)
    vehicle_detected = Column(Boolean, default=False)
    vehicle_count = Column(Integer, default=0)
    queue_length = Column(Integer, default=0)

    intersection = relationship("Intersection", back_populates="sensor_readings")


class SignalState(Base):
    __tablename__ = "signal_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    intersection_id = Column(String(10), ForeignKey("intersections.id"), nullable=False, index=True)
    mode = Column(String(30), nullable=False)  # green, yellow, all_red, emergency_green
    active_phase = Column(Integer, default=0)
    state = Column(String(30), nullable=False)  # 12-char RYG state
    is_emergency = Column(Boolean, default=False)
    duration = Column(Float, default=0.0)

    intersection = relationship("Intersection", back_populates="signal_states")


class EmergencyEvent(Base):
    __tablename__ = "emergency_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    vehicle_id = Column(String(50), nullable=False, index=True)
    vehicle_type = Column(String(30), default="ambulance")
    junction_id = Column(String(10), ForeignKey("intersections.id"), nullable=False, index=True)
    incoming_edge = Column(String(30), nullable=True)
    requested_phase = Column(Integer, default=0)
    request_time = Column(Float, nullable=False)
    granted_time = Column(Float, nullable=True)
    cleared_time = Column(Float, nullable=True)
    response_time = Column(Float, nullable=True)
    status = Column(String(30), default="requested", index=True)  # requested, clearing_existing, active, cleared, cancelled
    notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)

    intersection = relationship("Intersection", back_populates="emergency_events")


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(String(30), nullable=False)  # low, medium, heavy, emergency
    controller_type = Column(String(30), default="adaptive")  # baseline, adaptive
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    vehicles_inserted = Column(Integer, default=0)
    vehicles_arrived = Column(Integer, default=0)
    peak_queue = Column(Integer, default=0)
    status = Column(String(20), default="running")  # running, completed, failed

    benchmarks = relationship("BenchmarkMetric", back_populates="run", cascade="all, delete-orphan")


class BenchmarkMetric(Base):
    __tablename__ = "benchmark_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=True)
    scenario = Column(String(30), nullable=False)
    mode = Column(String(30), nullable=False)  # baseline, adaptive
    total_vehicles = Column(Integer, default=0)
    avg_waiting_time = Column(Float, default=0.0)
    avg_time_loss = Column(Float, default=0.0)
    avg_duration = Column(Float, default=0.0)
    peak_queue = Column(Integer, default=0)
    avg_queue = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("SimulationRun", back_populates="benchmarks")


class DeviceStatus(Base):
    __tablename__ = "device_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    device_id = Column(String(50), unique=True, nullable=False, index=True)
    intersection_id = Column(String(10), nullable=False)
    status = Column(String(20), default="online")
    uptime_seconds = Column(Float, default=0.0)
    last_heartbeat = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    ip_address = Column(String(50), default="127.0.0.1")
