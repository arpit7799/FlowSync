"""Simulated camera stream generator for FlowSync edge AI."""

import cv2
import numpy as np


class CameraStreamSimulator:
    """Generates synthetic road frames with moving vehicles for camera pipeline testing."""

    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height

    def generate_synthetic_frame(
        self,
        vehicle_count: int = 3,
        include_emergency: bool = False,
    ) -> np.ndarray:
        """Create a simulated traffic camera view."""
        # Asphalt background
        frame = np.full((self.height, self.width, 3), 45, dtype=np.uint8)

        # Draw road lane markings
        lane_w = self.width // 3
        # Road borders
        cv2.line(frame, (50, 0), (50, self.height), (200, 200, 200), 3)
        cv2.line(frame, (self.width - 50, 0), (self.width - 50, self.height), (200, 200, 200), 3)

        # Dashed lane dividers
        for y in range(0, self.height, 40):
            cv2.line(frame, (lane_w, y), (lane_w, y + 20), (255, 255, 255), 2)
            cv2.line(frame, (lane_w * 2, y), (lane_w * 2, y + 20), (255, 255, 255), 2)

        # Stop line
        cv2.line(frame, (50, self.height - 80), (self.width - 50, self.height - 80), (255, 255, 255), 6)

        # Draw simulated vehicle blobs
        rng = np.random.default_rng(seed=42)
        lanes_x = [lane_w - 70, lane_w + 30, lane_w * 2 - 30]

        for i in range(min(vehicle_count, len(lanes_x))):
            vx = lanes_x[i]
            vy = 120 + (i * 90)
            vw, vh = 50, 80

            if i == 0 and include_emergency:
                # White body with red roof / cross
                cv2.rectangle(frame, (vx, vy), (vx + vw, vy + vh), (240, 240, 240), -1)
                cv2.rectangle(frame, (vx + 15, vy + 20), (vx + vw - 15, vy + vh - 20), (0, 0, 255), -1)
            else:
                # Regular vehicle
                color = (rng.integers(50, 230), rng.integers(50, 230), rng.integers(50, 230))
                cv2.rectangle(frame, (vx, vy), (vx + vw, vy + vh), (int(color[0]), int(color[1]), int(color[2])), -1)

            # Windshield
            cv2.rectangle(frame, (vx + 5, vy + 15), (vx + vw - 5, vy + 35), (30, 30, 30), -1)

        return frame
