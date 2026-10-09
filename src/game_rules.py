"""Rule Engine - decides WIN, LOSE or DRAW. (Phase 1)"""
"""Rule Engine - decides WIN, LOSE or DRAW.

This file knows NOTHING about the camera or the screen.
It only answers one question: given two moves, who wins?
"""
from src.config import ROCK, PAPER, SCISSORS

# Possible results (from the PLAYER's point of view)
WIN = "WIN"
LOSE = "LOSE"
DRAW = "DRAW"

VALID_MOVES = (ROCK, PAPER, SCISSORS)

# Each key beats the value:  Rock beats Scissors, Paper beats Rock, ...
BEATS = {
    ROCK: SCISSORS,
    PAPER: ROCK,
    SCISSORS: PAPER,
}


def is_valid_move(move) -> bool:
    """True only for ROCK, PAPER or SCISSORS (UNKNOWN or None are NOT valid)."""
    return move in VALID_MOVES


def determine_result(player_move: str, computer_move: str) -> str:
    """Compare the two moves and return WIN, LOSE or DRAW for the player.

    Raises ValueError if either move is invalid. This protects the game:
    an UNKNOWN gesture can never produce a result.
    """
    if not is_valid_move(player_move):
        raise ValueError(f"Invalid player move: {player_move!r}")
    if not is_valid_move(computer_move):
        raise ValueError(f"Invalid computer move: {computer_move!r}")

    if player_move == computer_move:
        return DRAW
    if BEATS[player_move] == computer_move:
        return WIN
    return LOSE