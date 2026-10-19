"""Tests for score counting and reset behavior."""
import pytest

from src.game_rules import DRAW, LOSE, WIN
from src.score_manager import ScoreManager


@pytest.mark.parametrize(
    ("result", "expected_scores"),
    [
        (WIN, (1, 0, 0)),
        (LOSE, (0, 1, 0)),
        (DRAW, (0, 0, 1)),
    ],
)
def test_record_counts_result(result, expected_scores):
    score = ScoreManager()

    score.record(result)

    assert (score.player_score, score.computer_score, score.draws) == expected_scores
    assert score.rounds == 1


def test_rounds_counts_every_recorded_result():
    score = ScoreManager()

    for result in (WIN, LOSE, DRAW, WIN):
        score.record(result)

    assert score.rounds == 4


def test_reset_clears_scores_and_rounds():
    score = ScoreManager()
    score.record(WIN)
    score.record(LOSE)
    score.record(DRAW)

    score.reset()

    assert score.player_score == 0
    assert score.computer_score == 0
    assert score.draws == 0
    assert score.rounds == 0


def test_record_rejects_invalid_result():
    score = ScoreManager()

    with pytest.raises(ValueError):
        score.record("INVALID")

    assert score.rounds == 0
