"""Game Controller - the state machine that runs the game. (Phase 6)

States:  HOME -> READY -> COUNTDOWN -> CAPTURE -> SCORE_UPDATE -> RESULT
HANDS-FREE: no keyboard is needed.
  - HOME / READY : hold an OPEN HAND steady for a moment -> a round starts.
  - RESULT       : the next round starts by itself after a few seconds.
  - GAME OVER    : hold an OPEN HAND again -> a new game starts.

This file does NOT draw anything and does NOT touch the camera.
Every frame it receives ONE raw gesture and decides what to do with it.
"""
import math
import time
from enum import Enum

from src.computer_player import ComputerPlayer
from src.config import (CAPTURE_TIMEOUT_SECONDS, COUNTDOWN_SECONDS, RESULT_SECONDS,
                        START_GESTURE, START_HOLD_SECONDS, TARGET_SCORE, UNKNOWN)
from src.game_rules import LOSE, determine_result, is_valid_move
from src.gesture_stabilizer import GestureStabilizer
from src.history import History
from src.score_manager import ScoreManager


class State(Enum):
    HOME = "HOME"
    READY = "READY"
    COUNTDOWN = "COUNTDOWN"
    CAPTURE = "CAPTURE"
    SCORE_UPDATE = "SCORE_UPDATE"
    RESULT = "RESULT"


class GameController:
    def __init__(self, computer_player=None, stabilizer=None, score=None,
                 history=None, clock=time.monotonic,
                 target_score=TARGET_SCORE,
                 auto_next=True, hand_start=True) -> None:
        # (the "is None" checks are on purpose: an empty History counts as False)
        self.computer = computer_player if computer_player is not None else ComputerPlayer()
        self.stabilizer = stabilizer if stabilizer is not None else GestureStabilizer()
        self.score = score if score is not None else ScoreManager()
        self.history = history if history is not None else History()
        self._clock = clock               # can be replaced in tests (fake time)
        self.target_score = target_score
        # auto_next : the next round starts by itself after RESULT
        # hand_start: an open hand starts a round (set both to False when the
        #             screen has clickable buttons instead)
        self.auto_next = auto_next
        self.hand_start = hand_start
        self.state = State.HOME
        self._phase_start = 0.0
        self._hold_start = None           # when the "open hand" started
        self._paused_at = None
        self._clear_round()

    # ---------- things the screen (UI) is allowed to read ----------
    @property
    def countdown_number(self) -> int:
        """3, 2, 1 during COUNTDOWN. 0 in every other state."""
        if self.state != State.COUNTDOWN:
            return 0
        now = self._paused_at if self.is_paused else self._clock()
        remaining = COUNTDOWN_SECONDS - (now - self._phase_start)
        return max(1, math.ceil(remaining))

    @property
    def hold_progress(self) -> float:
        """0.0 to 1.0: how long the open hand has been held (for a progress bar)."""
        if self._hold_start is None:
            return 0.0
        now = self._paused_at if self.is_paused else self._clock()
        return min(1.0, (now - self._hold_start) / START_HOLD_SECONDS)

    @property
    def next_round_seconds(self) -> int:
        """Seconds left before the next round starts by itself (RESULT only)."""
        if self.state != State.RESULT or self.is_game_over:
            return 0
        now = self._paused_at if self.is_paused else self._clock()
        left = RESULT_SECONDS - (now - self._phase_start)
        return max(1, math.ceil(left))

    @property
    def visible_computer_move(self):
        """Fairness rule: the computer's move is shown ONLY in RESULT."""
        return self.computer_move if self.state == State.RESULT else None

    @property
    def is_game_over(self) -> bool:
        if self.target_score is None:
            return False
        best = max(self.score.player_score, self.score.computer_score)
        return best >= self.target_score

    @property
    def is_paused(self) -> bool:
        return self._paused_at is not None

    # ---------- actions (called by the buttons) ----------
    def start_game(self) -> bool:
        """HOME -> READY."""
        if self.state != State.HOME:
            return False
        self.state = State.READY
        return True

    def start_round(self) -> bool:
        """READY or RESULT -> COUNTDOWN. Returns False if not allowed now."""
        if self.state not in (State.READY, State.RESULT) or self.is_game_over:
            return False
        self._clear_round()
        self._hold_start = None
        self.computer_move = self.computer.choose()   # chosen now, but HIDDEN
        self.state = State.COUNTDOWN
        self._phase_start = self._clock()
        return True

    def new_game(self) -> None:
        """Reset the match score and go back to READY, preserving session history."""
        self._reset_game()
        self.state = State.READY

    def return_home(self) -> None:
        """End the current match and return home without erasing session history."""
        self._reset_game()
        self.state = State.HOME

    def _reset_game(self) -> None:
        self.score.reset()
        self.stabilizer.reset()
        self._hold_start = None
        self._paused_at = None
        self._clear_round()

    def pause_game(self) -> bool:
        """Freeze the current game state and its timers."""
        if self.is_paused:
            return False
        self._paused_at = self._clock()
        return True

    def resume_game(self) -> bool:
        """Resume the game without counting paused time against its timers."""
        if not self.is_paused:
            return False
        paused_for = self._clock() - self._paused_at
        self._phase_start += paused_for
        if self._hold_start is not None:
            self._hold_start += paused_for
        self._paused_at = None
        return True

    def submit_move(self, move: str) -> bool:
        """Accept a manual move during CAPTURE, for mouse-controlled play."""
        if self.is_paused or self.state != State.CAPTURE or not is_valid_move(move):
            return False
        self._lock_move(move)
        return True

    # ---------- called ONCE per camera frame ----------
    def update(self, raw_gesture: str) -> None:
        if self.is_paused:
            return
        now = self._clock()

        if self.state == State.COUNTDOWN:
            # Gestures are ignored here. Only the clock matters.
            if now - self._phase_start >= COUNTDOWN_SECONDS:
                self.stabilizer.reset()      # forget anything shown before GO
                self.state = State.CAPTURE
                self._phase_start = now

        elif self.state == State.CAPTURE:
            stable = self.stabilizer.update(raw_gesture)
            if is_valid_move(stable):
                self._lock_move(stable)
            elif now - self._phase_start >= CAPTURE_TIMEOUT_SECONDS:
                self.message = "No clear gesture. AI wins this round."
                self._finish_round(UNKNOWN, LOSE)

        elif self.state in (State.HOME, State.READY):
            if self.hand_start and self._open_hand_held(raw_gesture, now):
                self._start_by_hand()

        elif self.state == State.RESULT:
            if now - self._phase_start >= RESULT_SECONDS:
                if not self.is_game_over:
                    if self.auto_next:
                        self.start_round()             # automatic next round
                elif self.hand_start and self._open_hand_held(raw_gesture, now):
                    self._start_by_hand()              # new game by hand

    # ---------- private helpers ----------
    def _open_hand_held(self, raw_gesture: str, now: float) -> bool:
        """True once an open hand has been held steady for START_HOLD_SECONDS."""
        stable = self.stabilizer.update(raw_gesture)
        if stable == START_GESTURE:
            if self._hold_start is None:
                self._hold_start = now
            return now - self._hold_start >= START_HOLD_SECONDS
        self._hold_start = None          # hand removed or changed: start over
        return False

    def _start_by_hand(self) -> None:
        """The player showed the open hand: begin a round (or a new game)."""
        if self.state == State.HOME:
            self.start_game()
        elif self.state == State.RESULT:       # game over -> new game
            self.new_game()
        self.start_round()

    def _clear_round(self) -> None:
        self.player_move = None
        self.computer_move = None
        self.result = None
        self.message = ""

    def _lock_move(self, move: str) -> None:
        """Lock the player's move and count the round EXACTLY ONCE."""
        self._finish_round(move, determine_result(move, self.computer_move))

    def _finish_round(self, player_move: str, result: str) -> None:
        """Record a completed round and show its result exactly once."""
        self.player_move = player_move
        self.result = result
        self.state = State.SCORE_UPDATE
        self.score.record(self.result)
        self.history.add(self.player_move, self.computer_move, self.result)
        self.stabilizer.reset()          # the move shown must not count again
        self._hold_start = None
        self._phase_start = self._clock()
        self.state = State.RESULT