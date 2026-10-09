"""Tests for the gesture classifier (Phase 4).

We build FAKE hands (21 points) so the tests do not need a camera.
Run with:  python -m pytest -v
"""
from src.config import ROCK, PAPER, SCISSORS, UNKNOWN
from src.gesture_classifier import classify, get_finger_states

# (middle joint index, tip index, x position) for index, middle, ring, pinky
_FINGER_POINTS = [(6, 8, 0.40), (10, 12, 0.47), (14, 16, 0.54), (18, 20, 0.61)]


def make_hand(index=False, middle=False, ring=False, pinky=False):
    """Make a fake hand. True = finger extended, False = folded."""
    points = [(0.5, 0.9, 0.0)] * 21          # wrist at the bottom
    points = list(points)
    for (joint, tip, x), extended in zip(_FINGER_POINTS,
                                         [index, middle, ring, pinky]):
        points[joint] = (x, 0.70, 0.0)                      # middle joint
        points[tip] = (x, 0.40 if extended else 0.78, 0.0)  # far or near
    return points


def test_rock():
    assert classify(make_hand()) == ROCK


def test_paper_all_fingers():
    assert classify(make_hand(True, True, True, True)) == PAPER


def test_paper_three_fingers():
    assert classify(make_hand(True, True, True, False)) == PAPER


def test_scissors():
    assert classify(make_hand(index=True, middle=True)) == SCISSORS


def test_one_finger_is_unknown():
    assert classify(make_hand(index=True)) == UNKNOWN


def test_strange_two_fingers_is_unknown():
    assert classify(make_hand(index=True, pinky=True)) == UNKNOWN


def test_no_hand_is_unknown():
    assert classify(None) == UNKNOWN


def test_wrong_number_of_points_is_unknown():
    assert classify([(0.5, 0.5, 0.0)] * 5) == UNKNOWN


def test_finger_states():
    states = get_finger_states(make_hand(index=True, ring=True))
    assert states == {"index": True, "middle": False, "ring": True, "pinky": False}
