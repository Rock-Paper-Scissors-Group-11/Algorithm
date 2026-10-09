"""Phase 2 test: show the live webcam. Press 'q' to quit.

Run with:  python preview_camera.py
"""
import time

import cv2

from src.camera import Camera


def main() -> None:
    camera = Camera()
    if not camera.open():
        print("Could not open the webcam.")
        print("- Is another app (Zoom, Teams, browser) using the camera?")
        print("- Try changing CAMERA_INDEX to 1 in src/config.py")
        return

    print("Camera is on. Press 'q' in the video window to quit.")
    last_time = time.time()
    failed_frames = 0

    try:
        while True:
            frame = camera.read()
            if frame is None:
                failed_frames += 1
                if failed_frames > 30:
                    print("Camera stopped sending frames. Closing.")
                    break
                continue
            failed_frames = 0

            # Calculate FPS (frames per second)
            now = time.time()
            fps = 1.0 / max(now - last_time, 1e-6)
            last_time = now

            cv2.putText(frame, f"FPS: {fps:.0f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            cv2.imshow("Rock Paper Scissors - Camera Test (q = quit)", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        camera.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()