"""Play Rock Paper Scissors with your hand or mouse.

Point your INDEX FINGER at a button and keep it there for 1 second to select.
Mouse clicks and move buttons are also available.

Run with:  python play_game.py
"""
import time

import cv2

from src.camera import Camera
from src.config import DWELL_SECONDS, UNKNOWN
from src.audio import AudioManager
from src.game_controller import GameController, State
from src.gesture_classifier import classify
from src.hand_pointer import DwellClicker, Pointer, index_tip_normalized
from src.hand_tracker import HandTracker
from src.renderer import HEIGHT, WIDTH, Renderer, buttons_for

WINDOW = "Rock Paper Scissors"


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
    audio = AudioManager()
    try:
        tracker = HandTracker()
    except Exception as error:
        print("Could not start the hand tracker; mouse controls remain available:", error)
        tracker = None

    camera = Camera()
    camera_available = camera.open()
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

    cv2.namedWindow(WINDOW)
    cv2.setMouseCallback(WINDOW, on_mouse)
    print("Select Start Game to open the menu. Q = quit.")

    try:
        while view != "QUIT":
            frame = camera.read() if camera_available else None
            landmarks = tracker.detect(frame) if tracker is not None and frame is not None else None
            if tracker is not None and frame is not None:
                tracker.draw(frame, landmarks)
            raw = UNKNOWN if landmarks is None else classify(landmarks)
            if view != "PAUSED":
                game.update(raw)

            now = time.monotonic()
            if frame is not None:
                frame_h, frame_w = frame.shape[:2]
                fingertip = index_tip_normalized(landmarks, frame_w, frame_h)
            else:
                fingertip = None
            cursor = pointer.update(fingertip)
            buttons = buttons_for(game, view)

            action = clicker.update(cursor, buttons, now)
            if mouse_click:
                point = mouse_click.pop()
                mouse_click.clear()
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
            cv2.imshow(WINDOW, screen)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
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