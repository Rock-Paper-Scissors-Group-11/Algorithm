"""Tests for test_rules (written in a later phase)."""
"""Tests for the rule engine (Phase 1).

Run with:  python -m pytest -v
"""
import pytest

from src.config import ROCK, PAPER, SCISSORS, UNKNOWN
from src.game_rules import determine_result, is_valid_move, WIN, LOSE, DRAW


# ---- Win tests: player wins ----
def test_rock_beats_scissors():
    assert determine_result(ROCK, SCISSORS) == WIN


def test_paper_beats_rock():
    assert determine_result(PAPER, ROCK) == WIN


def test_scissors_beats_paper():
    assert determine_result(SCISSORS, PAPER) == WIN


# ---- Lose tests: computer wins ----
def test_rock_loses_to_paper():
    assert determine_result(ROCK, PAPER) == LOSE


def test_paper_loses_to_scissors():
    assert determine_result(PAPER, SCISSORS) == LOSE


def test_scissors_loses_to_rock():
    assert determine_result(SCISSORS, ROCK) == LOSE


# ---- Draw tests: same move ----
@pytest.mark.parametrize("move", [ROCK, PAPER, SCISSORS])
def test_same_move_is_draw(move):
    assert determine_result(move, move) == DRAW


# ---- Invalid input must never give a result ----
def test_unknown_gesture_is_rejected():
    with pytest.raises(ValueError):
        determine_result(UNKNOWN, ROCK)


def test_none_is_rejected():
    with pytest.raises(ValueError):
        determine_result(ROCK, None)


def test_is_valid_move():
    assert is_valid_move(ROCK)
    assert is_valid_move(PAPER)
    assert is_valid_move(SCISSORS)
    assert not is_valid_move(UNKNOWN)
    assert not is_valid_move("LIZARD")
