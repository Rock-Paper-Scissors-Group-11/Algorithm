"""Hand Pointer - use the index fingertip like a mouse, click by waiting.

Move your index fingertip over a button and KEEP it there for DWELL_SECONDS
(3 s). A progress bar fills on the button. When it is full = click.

This file does NOT draw anything and does NOT open the camera.
"""
from src.config import DWELL_SECONDS

INDEX_TIP = 8


def index_tip_normalized(landmarks, frame_width, frame_height):
    """Return the fingertip as (x, y) between 0 and 1, or None if no hand.

    Works if the tracker gives 0-1 values OR pixel values.
    """
    if landmarks is None or len(landmarks) != 21:
        return None
    x, y = landmarks[INDEX_TIP][0], landmarks[INDEX_TIP][1]
    if x > 1.5 or y > 1.5:                      # pixels -> 0..1
        x, y = x / frame_width, y / frame_height
    return (min(max(x, 0.0), 1.0), min(max(y, 0.0), 1.0))


class Pointer:
    """Turns the fingertip into a smooth cursor on the game screen."""

    def __init__(self, width, height, margin=0.12, smoothing=0.45) -> None:
        self.width = width
        self.height = height
        self.margin = margin          # the camera edges are hard to reach
        self.smoothing = smoothing    # 1.0 = no smoothing, smaller = smoother
        self._pos = None

    def update(self, normalized):
        """Give (x, y) from index_tip_normalized (or None). Get screen (x, y)."""
        if normalized is None:
            self._pos = None
            return None
        span = 1.0 - 2 * self.margin
        nx = min(max((normalized[0] - self.margin) / span, 0.0), 1.0)
        ny = min(max((normalized[1] - self.margin) / span, 0.0), 1.0)
        target = (nx * self.width, ny * self.height)
        if self._pos is None:
            self._pos = target
        else:
            self._pos = (self._pos[0] + self.smoothing * (target[0] - self._pos[0]),
                         self._pos[1] + self.smoothing * (target[1] - self._pos[1]))
        return self._pos


class Button:
    def __init__(self, name, label, x, y, w, h) -> None:
        self.name = name        # what the program uses, e.g. "START"
        self.label = label      # what the player reads
        self.x, self.y, self.w, self.h = x, y, w, h

    def contains(self, point) -> bool:
        return (point is not None
                and self.x <= point[0] <= self.x + self.w
                and self.y <= point[1] <= self.y + self.h)


class DwellClicker:
    """Counts how long the cursor stays on one button."""

    def __init__(self, dwell_seconds: float = DWELL_SECONDS) -> None:
        self.dwell = dwell_seconds
        self._target = None       # button name being held now
        self._start = 0.0
        self._locked = None       # just clicked: leave the button before again

    def update(self, point, buttons, now):
        """Call once per frame. Returns the clicked button's name, or None."""
        hit = None
        for button in buttons:
            if button.contains(point):
                hit = button.name
                break

        if hit != self._locked:
            self._locked = None
        if hit is None or hit == self._locked:
            self._target = None
            return None

        if hit != self._target:
            self._target = hit
            self._start = now
        if now - self._start >= self.dwell:
            self._locked = hit
            self._target = None
            return hit
        return None

    def progress(self, button_name, now) -> float:
        """0.0 to 1.0 for the progress bar of one button."""
        if button_name != self._target:
            return 0.0
        return min(1.0, (now - self._start) / self.dwell)