"""Edge AI package for FlowSync."""

from .camera.stream_simulator import CameraStreamSimulator
from .detection.vehicle_detector import EdgeVehicleDetector, DetectedVehicle

__all__ = [
    "CameraStreamSimulator",
    "EdgeVehicleDetector",
    "DetectedVehicle",
]
