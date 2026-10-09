"""Tests for the hand pointer, the 3-second click, and button mode.

No camera needed.
Run with:  python -m pytest -v
"""
from src.config import (COUNTDOWN_SECONDS, DWELL_SECONDS, PAPER, RESULT_SECONDS,
                        ROCK, SCISSORS, START_HOLD_SECONDS, UNKNOWN)
from src.game_controller import GameController, State
from src.game_rules import LOSE
from src.hand_pointer import (Button, DwellClicker, Pointer,
                              index_tip_normalized)
from src.renderer import buttons_for
from play_game import handle_action


def make_hand(x, y):
    points = [(0.5, 0.5, 0.0)] * 21
    points = list(points)
    points[8] = (x, y, 0.0)
    return points


BUTTONS = [Button("START", "START", 100, 100, 200, 80),
           Button("HISTORY", "HISTORY", 400, 100, 200, 80)]
ON_START = (150, 130)
ON_HISTORY = (450, 130)
NOWHERE = (900, 600)


# ---------------- fingertip and cursor ----------------
def test_fingertip_normalized_values():
    assert index_tip_normalized(make_hand(0.25, 0.75), 640, 480) == (0.25, 0.75)


def test_fingertip_pixel_values_are_converted():
    assert index_tip_normalized(make_hand(320, 240), 640, 480) == (0.5, 0.5)


def test_no_hand_gives_no_fingertip():
    assert index_tip_normalized(None, 640, 480) is None


def test_pointer_maps_to_screen_and_clamps():
    p = Pointer(1000, 600, margin=0.1, smoothing=1.0)
    assert p.update((0.5, 0.5)) == (500.0, 300.0)
    assert p.update((0.0, 1.0)) == (0.0, 600.0)      # edge is clamped
    assert p.update(None) is None


# ---------------- one-second click ----------------
def test_one_second_on_a_button_clicks_it():
    c = DwellClicker(DWELL_SECONDS)
    assert c.update(ON_START, BUTTONS, 0.0) is None
    assert c.update(ON_START, BUTTONS, 0.9) is None
    assert c.update(ON_START, BUTTONS, 1.1) == "START"


def test_progress_bar_value():
    c = DwellClicker(DWELL_SECONDS)
    c.update(ON_START, BUTTONS, 0.0)
    c.update(ON_START, BUTTONS, 0.5)
    assert c.progress("START", 0.5) == 0.5
    assert c.progress("HISTORY", 0.5) == 0.0


def test_leaving_the_button_cancels():
    c = DwellClicker(DWELL_SECONDS)
    c.update(ON_START, BUTTONS, 0.0)
    c.update(NOWHERE, BUTTONS, 2.0)
    c.update(ON_START, BUTTONS, 2.1)                  # starts again from 0
    assert c.update(ON_START, BUTTONS, 2.9) is None
    assert c.update(ON_START, BUTTONS, 3.2) == "START"


def test_moving_to_another_button_restarts():
    c = DwellClicker(DWELL_SECONDS)
    c.update(ON_START, BUTTONS, 0.0)
    c.update(ON_HISTORY, BUTTONS, 2.0)
    assert c.update(ON_HISTORY, BUTTONS, 2.9) is None
    assert c.update(ON_HISTORY, BUTTONS, 3.2) == "HISTORY"


def test_one_click_only_until_you_leave():
    c = DwellClicker(DWELL_SECONDS)
    c.update(ON_START, BUTTONS, 0.0)
    assert c.update(ON_START, BUTTONS, 1.1) == "START"
    assert c.update(ON_START, BUTTONS, 9.0) is None   # still on it: no repeat
    c.update(NOWHERE, BUTTONS, 9.5)
    c.update(ON_START, BUTTONS, 10.0)
    assert c.update(ON_START, BUTTONS, 11.1) == "START"


def test_hand_lost_cancels():
    c = DwellClicker(DWELL_SECONDS)
    c.update(ON_START, BUTTONS, 0.0)
    c.update(None, BUTTONS, 2.0)
    assert c.update(ON_START, BUTTONS, 2.9) is None


# ---------------- controller in "button mode" ----------------
class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, seconds):
        self.t += seconds


class FixedPlayer:
    def __init__(self, move):
        self.move = move

    def choose(self):
        return self.move


def button_mode_game():
    clock = FakeClock()
    game = GameController(computer_player=FixedPlayer(SCISSORS), clock=clock,
                          auto_next=False, hand_start=False)
    return game, clock


def test_open_hand_does_not_start_in_button_mode():
    game, clock = button_mode_game()
    for _ in range(10):
        game.update(PAPER)
    clock.advance(START_HOLD_SECONDS + 0.1)
    game.update(PAPER)
    assert game.state == State.HOME


def test_next_round_waits_for_result_timer_in_button_mode():
    game, clock = button_mode_game()
    game.start_game()
    game.start_round()
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)
    for _ in range(10):
        game.update(ROCK)
    assert game.state == State.RESULT
    clock.advance(RESULT_SECONDS * 3)
    game.update(UNKNOWN)
    assert game.state == State.RESULT                 # waits for the button
    assert game.start_round() is True                 # explicit controller action remains supported


def test_intermediate_result_offers_pause_and_exit():
    game, clock = button_mode_game()
    game.start_game()
    game.start_round()
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)
    for _ in range(10):
        game.update(ROCK)
    assert [button.name for button in buttons_for(game, "GAME")] == ["PAUSE", "EXIT"]


def test_round_controls_are_available_during_play():
    game, _ = button_mode_game()
    game.start_game()
    game.start_round()
    assert [button.name for button in buttons_for(game, "GAME")] == ["PAUSE", "EXIT"]


def test_paused_screen_offers_resume_and_exit():
    game, _ = button_mode_game()
    assert [button.name for button in buttons_for(game, "PAUSED")] == ["RESUME", "EXIT"]


def test_welcome_and_menu_screens_offer_expected_navigation():
    game, _ = button_mode_game()
    assert [button.name for button in buttons_for(game, "WELCOME")] == ["START"]
    assert [button.name for button in buttons_for(game, "HOME")] == [
        "START", "HELP", "SETTINGS", "HISTORY", "EXIT",
    ]
    assert [button.name for button in buttons_for(game, "HELP")] == ["BACK", "START"]


def test_settings_and_result_screens_offer_expected_controls():
    game, _ = button_mode_game()
    assert [button.name for button in buttons_for(game, "SETTINGS")] == [
        "SOUND_TOGGLE", "VOLUME_DOWN", "VOLUME_UP", "BACK",
    ]
    assert [button.name for button in buttons_for(game, "RESULT")] == [
        "AGAIN", "MAIN_MENU", "HISTORY", "EXIT",
    ]


def test_capture_screen_offers_mouse_move_buttons():
    game, clock = button_mode_game()
    game.start_game()
    game.start_round()
    clock.advance(COUNTDOWN_SECONDS + 0.1)
    game.update(UNKNOWN)
    assert [button.name for button in buttons_for(game, "GAME")] == [
        "MOVE_ROCK", "MOVE_PAPER", "MOVE_SCISSORS", "PAUSE", "EXIT",
    ]
    assert game.submit_move(PAPER) is True
    assert game.result == LOSE
    assert game.submit_move(ROCK) is False


class FakeAudio:
    def __init__(self):
        self.enabled = True
        self.volume = 0.8

    def set_enabled(self, enabled):
        self.enabled = enabled

    def set_volume(self, volume):
        self.volume = min(max(volume, 0.0), 1.0)


def test_welcome_start_leads_to_home_then_starts_a_match():
    game, _ = button_mode_game()
    audio = FakeAudio()
    assert handle_action("START", game, "WELCOME", audio, "HOME") == "HOME"
    assert game.state == State.HOME
    assert handle_action("START", game, "HOME", audio, "HOME") == "GAME"
    assert game.state == State.COUNTDOWN


def test_settings_actions_toggle_sound_and_clamp_volume():
    game, _ = button_mode_game()
    audio = FakeAudio()
    handle_action("SOUND_TOGGLE", game, "SETTINGS", audio, "HOME")
    assert audio.enabled is False
    handle_action("VOLUME_DOWN", game, "SETTINGS", audio, "HOME")
    assert abs(audio.volume - 0.7) < 1e-9