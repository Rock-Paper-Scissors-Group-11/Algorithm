"""Hand Tracker - finds the 21 hand landmarks with MediaPipe. (Phase 3)"""
"""Hand Tracker - finds the 21 hand landmarks using MediaPipe (Tasks API).

Note: new MediaPipe versions removed the old `mp.solutions` code, so we use
the newer `HandLandmarker`. It needs a small model file (hand_landmarker.task)
which is downloaded automatically the first time (needs internet once).
"""
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

from src import config

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)
MODEL_PATH = str(Path(__file__).resolve().parent.parent / "assets" / "models" / "hand_landmarker.task")

# Which landmark points are connected by lines (the "skeleton" of the hand)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),            # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),            # index finger
    (5, 9), (9, 10), (10, 11), (11, 12),       # middle finger
    (9, 13), (13, 14), (14, 15), (15, 16),     # ring finger
    (13, 17), (17, 18), (18, 19), (19, 20),    # little finger
    (0, 17),                                   # palm edge
]


def ensure_model(path: str = MODEL_PATH) -> str:
    """Download the model file if we do not have it yet."""
    model_path = Path(path)
    if model_path.exists():
        return path
    model_path.parent.mkdir(parents=True, exist_ok=True)
    print("Downloading hand model (one time only, ~8 MB)...")
    urllib.request.urlretrieve(MODEL_URL, model_path)
    print("Download finished.")
    return path


class HandTracker:
    def __init__(self):
        model_path = ensure_model()
        options = vision.HandLandmarkerOptions(
            base_options=mp_python.BaseOptions(model_asset_path=model_path),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.MAX_HANDS,
            min_hand_detection_confidence=config.DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.DETECTION_CONFIDENCE,
            min_tracking_confidence=config.TRACKING_CONFIDENCE,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp = -1

    def detect(self, frame_bgr):
        """Find the hand in one camera frame.

        Returns a list of 21 (x, y, z) points (values between 0 and 1,
        x/y relative to the image size), or None if no hand is visible.
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)  # MediaPipe wants RGB
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        # Timestamps must always increase in VIDEO mode
        timestamp = int(time.monotonic() * 1000)
        if timestamp <= self._last_timestamp:
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp

        result = self.landmarker.detect_for_video(mp_image, timestamp)
        if not result.hand_landmarks:
            return None
        return [(p.x, p.y, p.z) for p in result.hand_landmarks[0]]

    @staticmethod
    def draw(frame_bgr, landmarks) -> None:
        """Draw the hand skeleton (lines + red dots) on the frame."""
        if landmarks is None:
            return
        height, width = frame_bgr.shape[:2]
        points = [(int(x * width), int(y * height)) for x, y, _ in landmarks]
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame_bgr, points[a], points[b], (255, 255, 255), 2)
        for point in points:
            cv2.circle(frame_bgr, point, 5, (0, 0, 255), -1)

    def close(self) -> None:
        self.landmarker.close()
