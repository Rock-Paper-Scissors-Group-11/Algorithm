# HandRPS — Rock, Paper, Scissors

A responsive, static website for playing rock-paper-scissors against the computer. Play with a webcam and hand gestures, or use the on-screen move buttons.

## Play locally

Open a terminal in the project folder and run:

```powershell
python start_web.py
```

This starts a local web server and opens the game in your browser at <http://localhost:8000>. Keep the terminal open while you play. Camera access requires a secure page: `localhost` is allowed for local play; deployed sites must use HTTPS. Select **Start camera match** and allow camera access, or select **Play with buttons** to play without a camera.

The static website consists of `index.html`, `styles.css`, and `app.js`. It does not require a Python web server in production.

## Deploy

Deploy the project root as a static site using GitHub Pages, Netlify, or another static host. Configure the site to serve `index.html` and ensure the published URL uses HTTPS so browsers can grant camera access.

Camera play loads its hand-landmark model from `assets/models/hand_landmarker.task`. Hand detection runs locally in the browser; the video is not uploaded or saved. The MediaPipe browser runtime is loaded from jsDelivr, so camera play requires an internet connection the first time. Sounds, illustrations, icons, and fonts are stored locally in `assets/`. Match history is stored in the browser's local storage and can be exported as CSV from **Match history**.

## Features

- First to three round wins takes the match; draws do not score.
- Camera play recognizes rock, paper, and scissors; unclear or missing gestures lose the round after the capture timer.
- Automatic rounds, score and countdown display, and optional sound effects.
- Manual play when the camera is unavailable.
- Local match history, match statistics, CSV export, and responsive play/history/help pages.

## Local assets

- `assets/sounds/` contains the countdown, round-result, and match sound effects.
- `assets/icons/` and `assets/images/` contain the game's move icons, app icons, and camera illustration.
- `assets/fonts/` contains the DM Sans and Space Grotesk variable fonts and their SIL Open Font License files.
- `assets/models/hand_landmarker.task` is the hand-tracking model used by both game versions.

The website's fonts, artwork, sounds, and model load from the project itself. Camera hand tracking still loads the MediaPipe browser runtime from jsDelivr, so that feature needs an internet connection.

## Python desktop version

The original OpenCV desktop app remains available separately:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe play_game.py
```

The desktop app opens on a welcome screen with mouse and one-second hand-dwell
controls for the home menu, how-to guide, settings, and recent-round history.
During play, it keeps the camera gesture controls, pause and match-result
screens. Sound effects and their volume can be adjusted in Settings. The
desktop sound player uses Windows Media Control Interface; if Windows has no
available audio output, the game reports that and keeps the rest of the menus
usable.

## Project structure

- `index.html`, `styles.css`, `app.js` — deployable browser game.
- `start_web.py` — local launcher; uses only Python's standard library.
- `src/` — Python game rules, camera, hand tracking, and desktop game.
- `tests/` — Python unit tests.
