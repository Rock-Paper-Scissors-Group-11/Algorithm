"""Gesture Stabilizer - removes flickering from the classifier.

The classifier looks at ONE frame at a time, so its answer can jump
(PAPER, PAPER, UNKNOWN, PAPER, ROCK...). The stabilizer remembers the
last few answers and only accepts a gesture that appears often enough
(majority voting).

This file knows NOTHING about the game. It only cleans up the gesture.
"""
from collections import Counter, deque

from src.config import UNKNOWN, STABILIZER_WINDOW, STABILIZER_MIN_VOTES


class GestureStabilizer:
    def __init__(self, window: int = STABILIZER_WINDOW,
                 min_votes: int = STABILIZER_MIN_VOTES) -> None:
        self.min_votes = min_votes
        # deque with maxlen: when full, the oldest item is dropped automatically
        self.history = deque(maxlen=window)

    def update(self, gesture: str) -> str:
        """Give the newest raw gesture, get back the stable gesture."""
        self.history.append(gesture)

        # Count only real gestures (UNKNOWN is "no answer", not a vote)
        votes = Counter(g for g in self.history if g != UNKNOWN)
        if not votes:
            return UNKNOWN

        best_gesture, best_count = votes.most_common(1)[0]
        if best_count >= self.min_votes:
            return best_gesture
        return UNKNOWN

    def reset(self) -> None:
        """Forget everything (use this at the start of a new round)."""
        self.history.clear()
