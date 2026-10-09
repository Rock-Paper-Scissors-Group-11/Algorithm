"""Round History - stores recent rounds. (Phase 8)"""
from collections import deque

from src.config import HISTORY_SIZE


class History:
    def __init__(self, max_rounds: int = HISTORY_SIZE) -> None:
        # deque with maxlen: the oldest round is dropped automatically
        self._rounds = deque(maxlen=max_rounds)

    def add(self, player_move: str, computer_move: str, result: str) -> None:
        self._rounds.append({
            "player": player_move,
            "computer": computer_move,
            "result": result,
        })

    def recent(self) -> list:
        """Newest round first."""
        return list(reversed(self._rounds))

    def clear(self) -> None:
        self._rounds.clear()

    def __len__(self) -> int:
        return len(self._rounds)