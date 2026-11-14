"""Unit tests for Edge AI detector and synthetic camera stream."""

import numpy as np
import pytest
from edge_ai.camera.stream_simulator import CameraStreamSimulator
from edge_ai.detection.vehicle_detector import DetectedVehicle, EdgeVehicleDetector


def test_camera_stream_simulator():
    sim = CameraStreamSimulator(width=320, height=240)
    frame = sim.generate_synthetic_frame(vehicle_count=2, include_emergency=True)

    assert frame is not None
    assert frame.shape == (240, 320, 3)
    assert frame.dtype == np.uint8


def test_edge_vehicle_detector_cpu_fallback():
    detector = EdgeVehicleDetector(confidence_threshold=0.30)
    assert detector.backend == "cpu_fallback"

    sim = CameraStreamSimulator(width=640, height=480)
    frame = sim.generate_synthetic_frame(vehicle_count=3)

    detections = detector.detect(frame)
    assert isinstance(detections, list)
    # Fallback blob detection should find vehicle contours
    assert len(detections) >= 1
    assert detections[0].class_name in ("car", "bus", "truck")
    assert 0.0 <= detections[0].confidence <= 1.0


def test_edge_vehicle_detector_empty_frame():
    detector = EdgeVehicleDetector()
    detections = detector.detect(None)
    assert detections == []

    empty_frame = np.zeros((0, 0, 3), dtype=np.uint8)
    assert detector.detect(empty_frame) == []


def test_format_detection_event():
    detector = EdgeVehicleDetector()
    sample_detections = [
        DetectedVehicle(class_id=2, class_name="car", confidence=0.88, bbox=(10, 20, 60, 90)),
        DetectedVehicle(class_id=99, class_name="ambulance", confidence=0.95, bbox=(100, 120, 150, 190), is_emergency=True),
    ]

    event = detector.format_detection_event(
        camera_id="cam_J1_north",
        intersection_id="J1",
        frame_id=101,
        detections=sample_detections,
    )

    assert event["schema_version"] == "1.0"
    assert event["event_type"] == "ai.detection"
    assert event["intersection_id"] == "J1"
    assert event["vehicle_count"] == 2
    assert event["has_emergency"] is True
    assert len(event["detections"]) == 2
