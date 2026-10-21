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


def test_available_indices_releases_each_probe(monkeypatch):
    captures = []

    class Capture:
        def __init__(self, index):
            self.index = index
            self.released = False

        def isOpened(self):
            return self.index in (0, 2)

        def release(self):
            self.released = True

    def video_capture(index, *_args):
        capture = Capture(index)
        captures.append(capture)
        return capture

    monkeypatch.setattr("src.camera.sys.platform", "linux")
    monkeypatch.setattr("src.camera.cv2.VideoCapture", video_capture)

    assert Camera.available_indices() == [0, 2]
    assert len(captures) == 4
    assert all(capture.released for capture in captures)


def test_available_indices_survives_probe_errors(monkeypatch):
    monkeypatch.setattr("src.camera.sys.platform", "linux")

    def video_capture(_index):
        raise RuntimeError("camera backend failed")

    monkeypatch.setattr("src.camera.cv2.VideoCapture", video_capture)

    assert Camera.available_indices() == []
