"""Score Manager - player / computer / draw counts and total rounds. (Phase 8)

It does not decide who wins. It only counts a result it is given.
"""
from src.game_rules import WIN, LOSE, DRAW


class ScoreManager:
    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.player_score = 0
        self.computer_score = 0
        self.draws = 0
        self.rounds = 0

    def record(self, result: str) -> None:
        """Add one finished round. result is WIN, LOSE or DRAW (player's view)."""
        if result == WIN:
            self.player_score += 1
        elif result == LOSE:
            self.computer_score += 1
        elif result == DRAW:
            self.draws += 1
        else:
            raise ValueError(f"Invalid result: {result!r}")
        self.rounds += 1