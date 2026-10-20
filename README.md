# HandPlay

HandPlay is a desktop Rock Paper Scissors game that uses OpenCV and MediaPipe to read hand gestures from a webcam, with on-screen and mouse controls available for playing.

## Requirements

- Python 3.11
- A webcam for gesture controls
- OpenCV, MediaPipe, NumPy, and Pillow (listed in `requirements.txt`)
- pytest to run the automated tests

## Installation

From the project root, install the project requirements:

```sh
pip install -r requirements.txt
```

## How to play

Run `python main.py` from the project root. Select **Start Game** using the mouse or hold the hand cursor over a button for 1 second. Each round has a 3-second countdown; show a move during capture or select a move button. The first player to win 3 rounds wins the match; draws are recorded but do not increase either player's score.

## Gestures

- **Rock:** no recognized fingers extended.
- **Paper:** three or four recognized fingers extended.
- **Scissors:** index and middle fingers extended, with ring finger and pinky folded.

See the [gesture guide](docs/gesture-guide.md) for classifier details and tips.

## Project structure

- `main.py`, `play_game.py` — desktop game entry point and interface.
- `src/` — camera, hand tracking, gesture processing, game state, scoring, and rendering modules.
- `tests/` — automated tests.
- `scripts/` — optional camera and hand-tracking diagnostic scripts.
- `docs/` — architecture, state, gesture, and measurement documentation.
- `index.html`, `app.js`, `styles.css` — browser version.

## Design documentation

- [Architecture](docs/architecture.md)
- [Game state diagram](docs/state-diagram.md)

## Tests and camera measurements

Run the automated tests with:

```sh
python -m pytest
```

To measure gesture accuracy and average FPS under your lighting, run:

```sh
python -m scripts.measure_accuracy
```

The script asks for the lighting condition, then records 20 trials each for Rock, Paper, and Scissors. It prints the actual run results and creates (or appends to) `docs/measured_results.md`; it does not estimate camera accuracy or FPS.

## Known limitations

- Desktop sound uses the Windows Media Control Interface and is available on Windows only.
- When multiple hands are detected, the game uses the hand with the largest normalized bounding box as its primary hand.
- Lighting, hand distance, and visibility can affect gesture recognition.

## Browser version

The browser version uses `index.html`, `app.js`, and `styles.css`. Start its local server with `python start_web.py`.
