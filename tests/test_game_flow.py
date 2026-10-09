"""Tests for Phases 6-8: game controller, computer player, score, history.

No camera needed: we use a FAKE clock and a FAKE computer player.
Run with:  python -m pytest -v
"""
from src.computer_player import ComputerPlayer
from src.config import (CAPTURE_TIMEOUT_SECONDS, COUNTDOWN_SECONDS, RESULT_SECONDS,
                        PAPER, ROCK, SCISSORS, UNKNOWN)
from src.game_controller import GameController, State
from src.game_rules import DRAW, LOSE, VALID_MOVES, WIN
from src.history import History
from src.score_manager import ScoreManager
import pytest


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class FixedPlayer:
    """A computer that always plays the same move."""
    def __init__(self, move):
        self.move = move

    def choose(self):
        return self.move


def make(computer_move=SCISSORS, target_score=None):
    clock = FakeClock()
    game = GameController(computer_player=FixedPlayer(computer_move),
                          clock=clock, target_score=target_score)
    return game, clock


def go_to_capture(game, clock):
    game.start_game()
    game.start_round()
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)                 # countdown finished -> CAPTURE
    assert game.state == State.CAPTURE


def show(game, gesture, frames=10):
    for _ in range(frames):
        game.update(gesture)


# ---------------- state machine ----------------
def test_starts_at_home():
    game, _ = make()
    assert game.state == State.HOME


def test_start_game_goes_to_ready():
    game, _ = make()
    assert game.start_game() is True
    assert game.state == State.READY


def test_cannot_start_round_from_home():
    game, _ = make()
    assert game.start_round() is False
    assert game.state == State.HOME


def test_start_round_begins_countdown():
    game, _ = make()
    game.start_game()
    assert game.start_round() is True
    assert game.state == State.COUNTDOWN
    assert game.countdown_number == COUNTDOWN_SECONDS


def test_countdown_ignores_gestures():
    game, _ = make()
    game.start_game()
    game.start_round()
    show(game, ROCK, 30)                 # time does not move
    assert game.state == State.COUNTDOWN
    assert game.player_move is None


def test_countdown_becomes_capture_after_time():
    game, clock = make()
    game.start_game()
    game.start_round()
    clock.advance(COUNTDOWN_SECONDS - 0.1)
    game.update(UNKNOWN)
    assert game.state == State.COUNTDOWN
    clock.advance(0.2)
    game.update(UNKNOWN)
    assert game.state == State.CAPTURE


def test_gesture_before_go_does_not_count():
    game, clock = make()
    game.start_game()
    game.start_round()
    show(game, ROCK, 30)                 # shown DURING the countdown
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)                 # -> CAPTURE
    show(game, ROCK, 6)                  # 6 frames after GO: not enough yet
    assert game.state == State.CAPTURE
    game.update(ROCK)                    # 7th frame: locked
    assert game.state == State.RESULT


# ---------------- results and score ----------------
def test_player_wins():
    game, clock = make(computer_move=SCISSORS)
    go_to_capture(game, clock)
    show(game, ROCK)
    assert game.state == State.RESULT
    assert game.result == WIN
    assert game.score.player_score == 1


def test_player_loses():
    game, clock = make(computer_move=PAPER)
    go_to_capture(game, clock)
    show(game, ROCK)
    assert game.result == LOSE
    assert game.score.computer_score == 1


def test_draw():
    game, clock = make(computer_move=ROCK)
    go_to_capture(game, clock)
    show(game, ROCK)
    assert game.result == DRAW
    assert game.score.draws == 1


def test_score_counted_only_once():
    game, clock = make()
    go_to_capture(game, clock)
    show(game, ROCK)
    show(game, ROCK, 50)                 # many more frames in RESULT
    assert game.score.rounds == 1
    assert len(game.history) == 1


def test_computer_move_hidden_until_result():
    game, clock = make(computer_move=PAPER)
    game.start_game()
    game.start_round()
    assert game.visible_computer_move is None      # COUNTDOWN
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)
    assert game.visible_computer_move is None      # CAPTURE
    show(game, ROCK)
    assert game.visible_computer_move == PAPER     # RESULT


def test_unclear_gesture_counts_as_ai_win():
    game, clock = make()
    go_to_capture(game, clock)
    clock.advance(CAPTURE_TIMEOUT_SECONDS + 0.1)
    game.update(UNKNOWN)
    assert game.state == State.RESULT
    assert game.result == LOSE
    assert game.player_move == UNKNOWN
    assert game.score.computer_score == 1
    assert game.score.rounds == 1
    assert game.history.recent()[0]["player"] == UNKNOWN


def test_next_round_after_result():
    game, clock = make()
    go_to_capture(game, clock)
    show(game, ROCK)
    assert game.start_round() is True
    assert game.state == State.COUNTDOWN
    assert game.player_move is None and game.result is None


def test_next_round_starts_automatically_after_result():
    game, clock = make()
    go_to_capture(game, clock)
    show(game, ROCK)
    clock.advance(RESULT_SECONDS + 0.1)
    game.update(UNKNOWN)
    assert game.state == State.COUNTDOWN
    assert game.score.rounds == 1


def test_new_game_resets_match_but_keeps_session_history():
    game, clock = make()
    go_to_capture(game, clock)
    show(game, ROCK)
    game.new_game()
    assert game.state == State.READY
    assert game.score.rounds == 0
    assert len(game.history) == 1


def test_return_home_resets_match_and_keeps_history():
    game, clock = make()
    go_to_capture(game, clock)
    show(game, ROCK)
    assert game.score.rounds == 1
    assert len(game.history) == 1
    game.pause_game()

    game.return_home()

    assert game.state == State.HOME
    assert game.is_paused is False
    assert game.score.rounds == 0
    assert len(game.history) == 1
    assert game.player_move is None
    assert game.computer_move is None


def test_pausing_freezes_countdown_and_resume_preserves_remaining_time():
    game, clock = make()
    game.start_game()
    game.start_round()
    clock.advance(1)
    assert game.pause_game() is True
    clock.advance(COUNTDOWN_SECONDS * 2)
    game.update(UNKNOWN)
    assert game.state == State.COUNTDOWN
    assert game.countdown_number == COUNTDOWN_SECONDS - 1
    assert game.resume_game() is True
    clock.advance(COUNTDOWN_SECONDS - 1)
    game.update(UNKNOWN)
    assert game.state == State.CAPTURE


def test_game_cannot_be_paused_or_resumed_twice():
    game, _ = make()
    assert game.resume_game() is False
    assert game.pause_game() is True
    assert game.pause_game() is False
    assert game.resume_game() is True
    assert game.resume_game() is False


def test_game_over_at_target_score():
    game, clock = make(computer_move=SCISSORS, target_score=1)
    go_to_capture(game, clock)
    show(game, ROCK)                     # player wins 1-0
    assert game.is_game_over is True
    assert game.start_round() is False


def test_first_to_three_wins_ends_game():
    game, clock = make(computer_move=SCISSORS, target_score=3)
    for _ in range(3):
        if game.state == State.HOME:
            game.start_game()
        assert game.start_round() is True
        clock.advance(COUNTDOWN_SECONDS + 0.1)
        game.update(UNKNOWN)
        show(game, ROCK)
    assert game.score.player_score == 3
    assert game.is_game_over is True
    assert game.start_round() is False


# ---------------- small modules ----------------
def test_score_manager_counts():
    s = ScoreManager()
    for result in (WIN, WIN, LOSE, DRAW):
        s.record(result)
    assert (s.player_score, s.computer_score, s.draws, s.rounds) == (2, 1, 1, 4)


def test_score_manager_rejects_bad_result():
    with pytest.raises(ValueError):
        ScoreManager().record("MAYBE")


def test_history_newest_first_and_limited():
    h = History(max_rounds=2)
    h.add(ROCK, PAPER, LOSE)
    h.add(PAPER, PAPER, DRAW)
    h.add(SCISSORS, PAPER, WIN)          # pushes the oldest one out
    assert len(h) == 2
    assert h.recent()[0]["result"] == WIN


def test_computer_player_only_valid_moves():
    c = ComputerPlayer()
    assert all(c.choose() in VALID_MOVES for _ in range(100))
