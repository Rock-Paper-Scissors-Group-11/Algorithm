"""Tests for the gesture stabilizer (Phase 5).

No camera needed: we feed fake sequences of gestures.
Run with:  python -m pytest -v
"""
from src.config import ROCK, PAPER, UNKNOWN
from src.gesture_stabilizer import GestureStabilizer


def feed(stabilizer, gestures):
    """Send many gestures in order and return the LAST answer."""
    result = UNKNOWN
    for g in gestures:
        result = stabilizer.update(g)
    return result


def test_one_frame_is_not_enough():
    assert feed(GestureStabilizer(), [ROCK]) == UNKNOWN


def test_steady_gesture_is_accepted():
    assert feed(GestureStabilizer(), [ROCK] * 10) == ROCK


def test_small_noise_is_ignored():
    # 8 PAPER + 2 UNKNOWN mixed in -> still PAPER
    frames = [PAPER] * 4 + [UNKNOWN] + [PAPER] * 3 + [UNKNOWN] + [PAPER]
    assert feed(GestureStabilizer(), frames) == PAPER


def test_flickering_is_unknown():
    frames = [ROCK, PAPER] * 5   # 5 vs 5, nobody reaches 7
    assert feed(GestureStabilizer(), frames) == UNKNOWN


def test_switching_gesture_needs_enough_frames():
    s = GestureStabilizer()
    feed(s, [ROCK] * 10)
    # after 6 PAPER frames: 4 ROCK + 6 PAPER -> not sure yet
    assert feed(s, [PAPER] * 6) == UNKNOWN
    # the 7th PAPER frame makes 3 ROCK + 7 PAPER -> accepted
    assert s.update(PAPER) == PAPER


def test_reset_forgets_history():
    s = GestureStabilizer()
    feed(s, [ROCK] * 10)
    s.reset()
    assert s.update(ROCK) == UNKNOWN