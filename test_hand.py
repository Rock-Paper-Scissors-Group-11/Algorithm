"""Phase 3 + 4 + 5 test: hand tracking, gesture recognition AND stabilizing.

Big text   = STABLE gesture (after majority voting)  <- the game will use this
Small text = RAW gesture (straight from the classifier, can flicker)
Press 'q' to quit.

Run with:  python test_hand.py
"""
import cv2

from src.camera import Camera
from src.config import UNKNOWN
from src.gesture_classifier import classify, get_finger_states
from src.gesture_stabilizer import GestureStabilizer
from src.hand_tracker import HandTracker


def main() -> None:
    try:
        tracker = HandTracker()
    except Exception as error:
        print("Could not start the hand tracker:", error)
        print("If the model download failed, check your internet connection.")
        return

    camera = Camera()
    if not camera.open():
        print("Could not open the webcam.")
        tracker.close()
        return

    stabilizer = GestureStabilizer()

    print("Show your hand to the camera. Press 'q' to quit.")
    try:
        while True:
            frame = camera.read()
            if frame is None:
                continue

            landmarks = tracker.detect(frame)
            tracker.draw(frame, landmarks)

            if landmarks is None:
                raw = UNKNOWN
                cv2.putText(frame, "Show your hand", (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 2)
            else:
                raw = classify(landmarks)

            # No hand counts as UNKNOWN, so old votes slowly fade away
            stable = stabilizer.update(raw)

            if landmarks is not None:
                color = (0, 0, 255) if stable == UNKNOWN else (0, 255, 0)
                cv2.putText(frame, stable, (10, 45),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.4, color, 3)
                cv2.putText(frame, "raw: " + raw, (10, 75),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

                states = get_finger_states(landmarks)
                debug = "  ".join(f"{name[0].upper()}:{int(is_open)}"
                                  for name, is_open in states.items())
                cv2.putText(frame, debug, (10, 100),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            cv2.imshow("Gesture Test (q = quit)", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()