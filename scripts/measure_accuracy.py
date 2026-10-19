"""Measure gesture recognition accuracy and average FPS with a webcam."""
import time
from pathlib import Path

import cv2

from src.camera import Camera
from src.config import FRAME_HEIGHT, FRAME_WIDTH, PAPER, ROCK, SCISSORS
from src.gesture_classifier import classify
from src.hand_tracker import HandTracker

TARGETS = (ROCK, PAPER, SCISSORS)
LIGHTING_CONDITIONS = ("bright", "normal", "dim")
RESULTS_PATH = Path(__file__).resolve().parent.parent / "docs" / "measured_results.md"


def ask_lighting_condition() -> str:
    while True:
        lighting = input("Lighting condition (bright / normal / dim): ").strip().lower()
        if lighting in LIGHTING_CONDITIONS:
            return lighting
        print("Please enter bright, normal, or dim.")


def format_results(lighting, results, fps, interrupted) -> str:
    lines = [
        f"Lighting condition: **{lighting}**",
        "",
        "| Gesture | Correct / 20 | Trials completed | FPS |",
        "| --- | ---: | ---: | ---: |",
    ]
    for gesture in TARGETS:
        result = results[gesture]
        lines.append(
            f"| {gesture.title()} | {result['correct']} / 20 "
            f"| {result['trials']} | {fps:.2f} |"
        )
    if interrupted:
        lines.extend(("", "Measurement was interrupted before all trials finished."))
    return "\n".join(lines)


def append_results(report: str) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with RESULTS_PATH.open("a", encoding="utf-8") as results_file:
        if results_file.tell() == 0:
            results_file.write("# Measured camera results\n\n")
        else:
            results_file.write("\n\n")
        results_file.write(report)
        results_file.write("\n")


def main() -> None:
    lighting = ask_lighting_condition()
    camera = Camera()
    tracker = None
    try:
        if not camera.open():
            print("No camera found. Connect a webcam and try again.")
            return

        tracker = HandTracker()
        results = {
            target: {"correct": 0, "trials": 0}
            for target in TARGETS
        }
        processed_frames = 0
        interrupted = False
        started_at = time.monotonic()

        print("Press SPACE to record each trial. Press Q to quit.")
        cv2.namedWindow("HandPlay Accuracy Measurement")

        for target in TARGETS:
            while results[target]["trials"] < 20:
                frame = camera.read()
                if frame is None:
                    print("Camera connection lost. Measurement stopped safely.")
                    interrupted = True
                    break

                processed_frames += 1
                landmarks = tracker.detect(frame)
                tracker.draw(frame, landmarks)
                detected = classify(landmarks)
                trial_number = results[target]["trials"] + 1

                cv2.putText(
                    frame, f"Target: {target}", (12, 34),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2,
                )
                cv2.putText(
                    frame, f"Trial: {trial_number}/20", (12, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2,
                )
                cv2.putText(
                    frame, f"Detected: {detected}", (12, 106),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
                )
                cv2.putText(
                    frame, "SPACE: record   Q: quit", (12, 142),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2,
                )
                cv2.imshow("HandPlay Accuracy Measurement", frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    interrupted = True
                    break
                if key == ord(" "):
                    results[target]["trials"] += 1
                    if detected == target:
                        results[target]["correct"] += 1

            if interrupted:
                break

        elapsed = time.monotonic() - started_at
        fps = processed_frames / elapsed if elapsed > 0 else 0.0
        report = format_results(lighting, results, fps, interrupted)
        print("\n" + report)
        append_results(report)
        print(f"\nResults appended to {RESULTS_PATH}")
    finally:
        try:
            camera.release()
        finally:
            try:
                if tracker is not None:
                    tracker.close()
            finally:
                cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
