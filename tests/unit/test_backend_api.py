"""Unit & integration tests for FastAPI backend routes and database operations."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.models.traffic import Intersection

# Use an in-memory SQLite database with StaticPool for test isolation
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_test_database():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    # Seed default intersections
    default_intersections = [
        Intersection(id="J1", name="Junction 1", location_x=500.0, location_y=500.0, num_lanes=12, status="online"),
        Intersection(id="J2", name="Junction 2", location_x=1000.0, location_y=500.0, num_lanes=12, status="online"),
        Intersection(id="J3", name="Junction 3", location_x=500.0, location_y=0.0, num_lanes=12, status="online"),
        Intersection(id="J4", name="Junction 4", location_x=1000.0, location_y=0.0, num_lanes=12, status="online"),
    ]
    db.add_all(default_intersections)
    db.commit()
    db.close()

    yield

    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def test_health_check():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_list_intersections():
    response = client.get("/api/v1/intersections")
    assert response.status_code == 200
    intersections = response.json()
    assert len(intersections) == 4
    j_ids = {i["id"] for i in intersections}
    assert j_ids == {"J1", "J2", "J3", "J4"}


def test_get_single_intersection():
    response = client.get("/api/v1/intersections/J1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "J1"
    assert data["name"] == "Junction 1"


def test_get_nonexistent_intersection():
    response = client.get("/api/v1/intersections/UNKNOWN")
    assert response.status_code == 404


def test_current_traffic_state():
    response = client.get("/api/v1/traffic/state")
    assert response.status_code == 200
    data = response.json()
    assert "total_vehicles" in data
    assert "total_queue" in data
    assert len(data["intersections"]) == 4


def test_sensor_telemetry_flow():
    # 1. Post sensor reading
    payload = {
        "intersection_id": "J1",
        "device_id": "esp32_j1_controller",
        "distance_cm": 25.4,
        "vehicle_detected": True,
        "vehicle_count": 3,
        "queue_length": 2,
        "timestamp": 123456.7,
    }
    post_res = client.post("/api/v1/sensors/telemetry", json=payload)
    assert post_res.status_code == 201
    created = post_res.json()
    assert created["intersection_id"] == "J1"
    assert created["vehicle_count"] == 3

    # 2. Get sensor readings
    get_res = client.get("/api/v1/sensors/telemetry?limit=10")
    assert get_res.status_code == 200
    readings = get_res.json()
    assert len(readings) >= 1
    assert readings[0]["device_id"] == "esp32_j1_controller"


def test_signal_command_and_status():
    cmd = {
        "intersection_id": "J2",
        "red": False,
        "yellow": False,
        "green": True,
        "phase": 0,
        "duration": 30.0,
        "emergency_priority": False,
    }
    cmd_res = client.post("/api/v1/signals/command", json=cmd)
    assert cmd_res.status_code == 200
    assert cmd_res.json()["success"] is True

    status_res = client.get("/api/v1/signals/status")
    assert status_res.status_code == 200
    states = status_res.json()
    assert len(states) >= 1
    assert states[0]["intersection_id"] == "J2"
    assert states[0]["mode"] == "green"


def test_emergency_priority_flow():
    # 1. Create emergency priority request
    req = {
        "vehicle_id": "amb_999",
        "vehicle_type": "ambulance",
        "intersection_id": "J3",
        "incoming_edge": "W_J3",
        "requested_phase": 2,
        "source": "api_test",
    }
    post_res = client.post("/api/v1/emergency/requests", json=req)
    assert post_res.status_code == 201
    event = post_res.json()
    assert event["vehicle_id"] == "amb_999"
    assert event["junction_id"] == "J3"
    assert event["status"] == "requested"

    event_id = event["event_id"]

    # 2. List emergency events
    list_res = client.get("/api/v1/emergency/requests")
    assert list_res.status_code == 200
    events = list_res.json()
    assert any(e["event_id"] == event_id for e in events)

    # 3. Cancel emergency request
    cancel_res = client.post(f"/api/v1/emergency/requests/{event_id}/cancel")
    assert cancel_res.status_code == 200
    assert cancel_res.json()["success"] is True


def test_benchmarks_endpoint():
    response = client.get("/api/v1/benchmarks")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
