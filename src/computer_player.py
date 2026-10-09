"""Computer Player - random move, hidden until RESULT. (Phase 7)

It only picks a move. Hiding it from the screen is the Game Controller's job.
"""
import random

from src.game_rules import VALID_MOVES


class ComputerPlayer:
    def __init__(self, rng=None) -> None:
        # rng can be replaced in tests so the "random" choice is predictable
        self._rng = rng if rng is not None else random.Random()

    def choose(self) -> str:
        """Return ROCK, PAPER or SCISSORS, each with equal chance."""
        return self._rng.choice(VALID_MOVES)