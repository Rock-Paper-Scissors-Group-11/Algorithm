"""Play Rock Paper Scissors with your hand or mouse.

Point your INDEX FINGER at a button and keep it there for 1 second to select.
Mouse clicks and move buttons are also available.

Run with:  python main.py
"""
import time

import cv2
import numpy as np

from src.camera import Camera
from src.config import DWELL_SECONDS, FULLSCREEN, UNKNOWN
from src.audio import AudioManager
from src.game_controller import GameController, State
from src.gesture_classifier import classify
from src.hand_pointer import DwellClicker, Pointer, index_tip_normalized
from src.hand_tracker import HandTracker
from src.renderer import HEIGHT, PALE, WIDTH, Renderer, buttons_for

WINDOW = "Rock Paper Scissors"


def fit_scale(canvas_w: int, canvas_h: int, window_w: int, window_h: int):
    """Return scale, centered offsets, and image size, or None for zero sizes."""
    if min(canvas_w, canvas_h, window_w, window_h) <= 0:
        return None
    scale = min(window_w / canvas_w, window_h / canvas_h)
    image_w = max(1, round(canvas_w * scale))
    image_h = max(1, round(canvas_h * scale))
    offset_x = (window_w - image_w) // 2
    offset_y = (window_h - image_h) // 2
    return scale, offset_x, offset_y, image_w, image_h


def window_to_canvas(x, y, canvas_w: int, canvas_h: int,
                     window_w: int, window_h: int):
    """Map a window click to canvas coordinates, or None outside the image."""
    fitted = fit_scale(canvas_w, canvas_h, window_w, window_h)
    if fitted is None:
        return None
    _, offset_x, offset_y, image_w, image_h = fitted
    if not (offset_x <= x < offset_x + image_w
            and offset_y <= y < offset_y + image_h):
        return None
    canvas_x = int((x - offset_x) * canvas_w / image_w)
    canvas_y = int((y - offset_y) * canvas_h / image_h)
    return canvas_x, canvas_y


class SilentAudio:
    def __init__(self) -> None:
        self.enabled = False
        self.available = False
        self.volume = 0.0

    def play(self, name) -> None:
        pass

    def set_enabled(self, value) -> None:
        pass

    def set_volume(self, value) -> None:
        pass

    def close(self) -> None:
        pass


def handle_action(action, game, view, audio, history_return_view):
    """Do what the clicked button says. Returns the new view."""
    if action == "START" and view == "WELCOME":
        return "HOME"
    if action == "START" and view in ("HOME", "HELP"):
        game.start_game()
        game.start_round()
        return "GAME"
    if action == "AGAIN":
        game.new_game()
        game.start_round()
        return "GAME"
    if action.startswith("MOVE_"):
        game.submit_move(action.removeprefix("MOVE_"))
    if action == "HELP":
        return "HELP"
    if action == "SETTINGS":
        return "SETTINGS"
    if action == "SOUND_TOGGLE":
        audio.set_enabled(not audio.enabled)
    elif action == "VOLUME_DOWN":
        audio.set_volume(audio.volume - 0.1)
    elif action == "VOLUME_UP":
        audio.set_volume(audio.volume + 0.1)
    elif action == "CLEAR_HISTORY":
        game.history.clear()
    elif action == "MAIN_MENU":
        game.return_home()
        return "HOME"
    elif action == "EXIT" and view == "HOME":
        return "QUIT"
    elif action == "EXIT":
        game.return_home()
        return "HOME"
    elif action == "HISTORY":
        return "HISTORY"
    elif action == "BACK":
        if view == "HISTORY":
            return history_return_view
        return "HOME"
    elif action == "PAUSE":
        game.pause_game()
        return "PAUSED"
    elif action == "RESUME":
        game.resume_game()
        return "GAME"
    return view


def main() -> None:
    try:
        audio = AudioManager()
    except Exception:
        print("Sound unavailable")
        audio = SilentAudio()
    try:
        tracker = HandTracker()
    except Exception as error:
        print("Could not start the hand tracker; mouse controls remain available:", error)
        tracker = None

    camera = Camera()
    camera_available = camera.open()
    next_camera_retry = time.monotonic() + 2.0
    failed_camera_frames = 0
    if not camera_available:
        print("Could not open the webcam. The welcome and menu screens remain available.")

    game = GameController(auto_next=True, hand_start=False)
    renderer = Renderer()
    pointer = Pointer(WIDTH, HEIGHT)
    clicker = DwellClicker(DWELL_SECONDS)
    view = "WELCOME"
    history_return_view = "HOME"
    mouse_click = []
    last_game_state = game.state
    last_countdown = None

    def on_mouse(event, x, y, _flags, _param):
        if event == cv2.EVENT_LBUTTONDOWN:
            mouse_click.append((x, y))

    cv2.namedWindow(WINDOW, cv2.WINDOW_NORMAL)
    cv2.setMouseCallback(WINDOW, on_mouse)
    fullscreen = FULLSCREEN
    cv2.setWindowProperty(
        WINDOW, cv2.WND_PROP_FULLSCREEN,
        cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL,
    )
    print("Select Start Game to open the menu. Q = quit.")

    try:
        while view != "QUIT":
            now = time.monotonic()
            window_rect = cv2.getWindowImageRect(WINDOW)
            window_w, window_h = window_rect[2], window_rect[3]
            if camera_available:
                frame = camera.read()
                if frame is None:
                    failed_camera_frames += 1
                    if failed_camera_frames > 30:
                        camera.release()
                        camera_available = False
                        failed_camera_frames = 0
                        next_camera_retry = time.monotonic() + 2.0
                else:
                    failed_camera_frames = 0
            else:
                frame = None
                if now >= next_camera_retry:
                    camera_available = camera.open()
                    if not camera_available:
                        next_camera_retry = time.monotonic() + 2.0

            landmarks = tracker.detect(frame) if tracker is not None and frame is not None else None
            if tracker is not None and frame is not None:
                tracker.draw(frame, landmarks)
            raw = UNKNOWN if landmarks is None else classify(landmarks)
            if view != "PAUSED":
                game.update(raw)

            if frame is not None:
                frame_h, frame_w = frame.shape[:2]
                fingertip = index_tip_normalized(landmarks, frame_w, frame_h)
            else:
                fingertip = None
            cursor = pointer.update(fingertip)
            buttons = buttons_for(game, view)

            action = clicker.update(cursor, buttons, now)
            if mouse_click:
                window_point = mouse_click.pop()
                mouse_click.clear()
                point = window_to_canvas(
                    window_point[0], window_point[1], WIDTH, HEIGHT,
                    window_w, window_h,
                )
                if point is not None:
                    for button in buttons:
                        if button.contains(point):
                            action = button.name
            if action:
                if action == "HISTORY":
                    history_return_view = view
                view = handle_action(action, game, view, audio, history_return_view)
            if (view == "GAME" and game.state == State.RESULT
                    and game.is_game_over):
                view = "RESULT"

            if game.state == State.COUNTDOWN:
                countdown = game.countdown_number
                if last_countdown is None:
                    audio.play("countdown")
                last_countdown = countdown
            else:
                last_countdown = None
            if game.state == State.RESULT and last_game_state != State.RESULT:
                if game.is_game_over:
                    audio.play("match")
                else:
                    sound = {"WIN": "win", "LOSE": "lose", "DRAW": "draw"}[game.result]
                    audio.play(sound)
            last_game_state = game.state

            buttons = buttons_for(game, view)
            screen = renderer.draw(
                game, frame, raw, view, buttons, cursor, clicker, now,
                audio.enabled, audio.volume, camera_available, audio.available,
            )
            window_rect = cv2.getWindowImageRect(WINDOW)
            window_w, window_h = window_rect[2], window_rect[3]
            fitted = fit_scale(WIDTH, HEIGHT, window_w, window_h)
            if fitted is not None:
                _, offset_x, offset_y, image_w, image_h = fitted
                scaled = cv2.resize(
                    screen, (image_w, image_h), interpolation=cv2.INTER_LINEAR,
                )
                display = np.full(
                    (window_h, window_w, 3), PALE, dtype=np.uint8,
                )
                display[offset_y:offset_y + image_h,
                        offset_x:offset_x + image_w] = scaled
                cv2.imshow(WINDOW, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                break
            if key in (ord("f"), ord("F")):
                fullscreen = not fullscreen
                cv2.setWindowProperty(
                    WINDOW, cv2.WND_PROP_FULLSCREEN,
                    cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL,
                )
            if cv2.getWindowProperty(WINDOW, cv2.WND_PROP_VISIBLE) < 1:
                break
    finally:
        camera.release()
        if tracker is not None:
            tracker.close()
        audio.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()