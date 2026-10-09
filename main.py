"""Entry point of the game.

For now (Phase 0) this only checks that the environment is ready.
Later it will start the real game.
"""
import sys


def check_environment() -> bool:
    """Try to import every library we need and print its version."""
    print(f"Python version: {sys.version.split()[0]}")
    if sys.version_info < (3, 11):
        print("[WARN] Python 3.11 or newer is recommended.")

    libraries = ["cv2", "mediapipe", "numpy", "pytest"]
    all_ok = True
    for name in libraries:
        try:
            module = __import__(name)
            version = getattr(module, "__version__", "unknown")
            print(f"[OK]   {name} ({version})")
        except ImportError:
            print(f"[FAIL] {name} is NOT installed -> run: pip install -r requirements.txt")
            all_ok = False
    return all_ok


def main() -> None:
    print("=== Rock Paper Scissors - Environment Check ===")
    if check_environment():
        print("\nEverything is ready. You can start Phase 1!")
    else:
        print("\nSome libraries are missing. Fix them first, then run again.")


if __name__ == "__main__":
    main()
