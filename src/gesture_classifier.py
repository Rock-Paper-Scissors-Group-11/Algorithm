"""Gesture Classifier - returns ROCK, PAPER, SCISSORS or UNKNOWN.

This file knows NOTHING about the game (score, computer, rounds).
It only looks at the 21 hand points and answers: "what gesture is this?"
"""
import math

from src.config import ROCK, PAPER, SCISSORS, UNKNOWN, FINGER_EXTENDED_RATIO

WRIST = 0

# For each finger: (middle joint index, fingertip index) in the 21 landmarks
FINGERS = {
    "index": (6, 8),
    "middle": (10, 12),
    "ring": (14, 16),
    "pinky": (18, 20),
}


def _distance(a, b) -> float:
    """Straight-line distance between two points (using x and y only)."""
    return math.hypot(a[0] - b[0], a[1] - b[1])


def get_finger_states(landmarks) -> dict:
    """Tell which of the 4 fingers are extended (True) or folded (False).

    Idea: if a finger is straight, its tip is FAR from the wrist.
    If it is folded, the tip comes back close to the palm.
    We compare the tip's distance with the middle joint's distance, so it
    still works when the hand is tilted or rotated.
    """
    wrist = landmarks[WRIST]
    states = {}
    for name, (joint, tip) in FINGERS.items():
        joint_distance = _distance(wrist, landmarks[joint])
        tip_distance = _distance(wrist, landmarks[tip])
        ratio = tip_distance / joint_distance if joint_distance > 0 else 0
        states[name] = ratio > FINGER_EXTENDED_RATIO
    return states


def classify(landmarks) -> str:
    """Return ROCK, PAPER, SCISSORS or UNKNOWN for one hand."""
    if landmarks is None or len(landmarks) != 21:
        return UNKNOWN

    s = get_finger_states(landmarks)
    extended_count = sum(s.values())

    # Scissors: index + middle up, ring + pinky folded
    if s["index"] and s["middle"] and not s["ring"] and not s["pinky"]:
        return SCISSORS
    # Paper: (almost) all four fingers open
    if extended_count >= 3:
        return PAPER
    # Rock: all four fingers folded
    if extended_count == 0:
        return ROCK
    # Anything else (e.g. only one finger up) is unclear
    return UNKNOWN