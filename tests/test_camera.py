"""Tests for camera read failures."""
from src.camera import Camera


class RaisingCapture:
    def isOpened(self):
        return True

    def read(self):
        raise RuntimeError("camera backend failed")


def test_read_returns_none_when_capture_raises():
    camera = Camera()
    camera.cap = RaisingCapture()

    assert camera.read() is None
