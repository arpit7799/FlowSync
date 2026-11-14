"""Edge AI Vehicle Detection and Emergency Classification."""

from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger("flowsync.edge_ai")

COCO_VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

EMERGENCY_CLASSES = {"ambulance", "police", "fire_truck", "emergency"}


@dataclass
class DetectedVehicle:
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    track_id: Optional[int] = None
    is_emergency: bool = False


class EdgeVehicleDetector:
    """YOLO/OpenCV-based vehicle detector with graceful CPU fallback."""

    def __init__(
        self,
        confidence_threshold: float = 0.45,
        iou_threshold: float = 0.50,
        model_path: Optional[str] = None,
        use_cpu_only: bool = True,
    ):
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        self.model_path = model_path
        self.use_cpu_only = use_cpu_only
        self._model = None
        self._backend = "cpu_fallback"

        self._initialize_model()

    def _initialize_model(self):
        """Attempt to load ultralytics YOLO model; fallback to OpenCV CPU simulator if unavailable."""
        if self.model_path:
            try:
                from ultralytics import YOLO
                self._model = YOLO(self.model_path)
                self._backend = "yolov8"
                logger.info("Loaded YOLO model from %s on %s", self.model_path, "CPU" if self.use_cpu_only else "GPU")
                return
            except Exception as exc:
                logger.warning("Could not load YOLO model (%s), using lightweight CPU fallback: %s", self.model_path, exc)

        self._backend = "cpu_fallback"
        logger.info("Using Edge AI CPU Fallback vehicle detector.")

    @property
    def backend(self) -> str:
        return self._backend

    def detect(self, frame: np.ndarray) -> List[DetectedVehicle]:
        """Run detection on a BGR image frame (H, W, 3)."""
        if frame is None or frame.size == 0:
            return []

        if self._model is not None and self._backend == "yolov8":
            return self._detect_yolo(frame)
        else:
            return self._detect_fallback(frame)

    def _detect_yolo(self, frame: np.ndarray) -> List[DetectedVehicle]:
        """Inference with YOLO model."""
        results = self._model(frame, conf=self.confidence_threshold, iou=self.iou_threshold, verbose=False)
        detections = []

        if not results:
            return []

        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [int(v) for v in box.xyxy[0].tolist()]

                # Only include vehicle classes
                cls_name = r.names.get(cls_id, "unknown")
                if cls_name in ("car", "motorcycle", "bus", "truck", "ambulance") or cls_id in COCO_VEHICLE_CLASSES:
                    is_emg = cls_name in EMERGENCY_CLASSES
                    detections.append(
                        DetectedVehicle(
                            class_id=cls_id,
                            class_name=cls_name,
                            confidence=round(conf, 3),
                            bbox=(xyxy[0], xyxy[1], xyxy[2], xyxy[3]),
                            is_emergency=is_emg,
                        )
                    )

        return detections

    def _detect_fallback(self, frame: np.ndarray) -> List[DetectedVehicle]:
        """Deterministic OpenCV/Numpy fallback detecting vehicle motion/blobs in frame."""
        import cv2

        detections = []
        h, w = frame.shape[:2]

        # Use image analysis (grayscale, blur, adaptive thresholding)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 15, 3
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        track_idx = 1
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Filter vehicle bounding boxes (e.g. 50x80 px = ~4000 area)
            if 1000 < area < (h * w * 0.4):
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / float(bh)

                if 0.3 <= aspect <= 3.5:
                    cls_name = "car"
                    if area > 4500:
                        cls_name = "bus" if aspect < 1.5 else "truck"

                    # Check for emergency markings (red pixel concentration in vehicle bbox)
                    roi = frame[y:y + bh, x:x + bw]
                    is_emg = False
                    if roi.size > 0:
                        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
                        mask1 = cv2.inRange(hsv, np.array([0, 100, 100]), np.array([10, 255, 255]))
                        mask2 = cv2.inRange(hsv, np.array([160, 100, 100]), np.array([179, 255, 255]))
                        red_pixels = cv2.countNonZero(mask1 + mask2)
                        if red_pixels > (area * 0.05):
                            is_emg = True
                            cls_name = "ambulance"

                    detections.append(
                        DetectedVehicle(
                            class_id=2 if not is_emg else 99,
                            class_name=cls_name,
                            confidence=round(min(0.95, 0.65 + (area / 15000.0)), 2),
                            bbox=(x, y, x + bw, y + bh),
                            track_id=track_idx,
                            is_emergency=is_emg,
                        )
                    )
                    track_idx += 1

        return detections

    def format_detection_event(
        self,
        camera_id: str,
        intersection_id: str,
        frame_id: int,
        detections: List[DetectedVehicle],
    ) -> Dict[str, Any]:
        """Format detection event according to FlowSync Communication Contracts."""
        return {
            "schema_version": "1.0",
            "event_type": "ai.detection",
            "timestamp": round(float(np.datetime64('now').astype('int64') / 1e6), 3),
            "camera_id": camera_id,
            "intersection_id": intersection_id,
            "frame_id": frame_id,
            "detections": [
                {
                    "class_name": d.class_name,
                    "confidence": d.confidence,
                    "bbox": list(d.bbox),
                    "track_id": d.track_id or idx + 1,
                    "is_emergency": d.is_emergency,
                }
                for idx, d in enumerate(detections)
            ],
            "vehicle_count": len(detections),
            "has_emergency": any(d.is_emergency for d in detections),
        }
