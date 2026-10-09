"""Draw the desktop game's welcome, menu, game, and information screens."""
import math
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from src.config import PAPER, ROCK, SCISSORS
from src.game_controller import State
from src.game_rules import DRAW, LOSE, WIN
from src.hand_pointer import Button

WIDTH, HEIGHT = 1100, 700
FONT = cv2.FONT_HERSHEY_DUPLEX
ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = ROOT / "assets" / "fonts" / "SpaceGrotesk-Variable.ttf"
_TEXT_QUEUE = None

# Colors are BGR (OpenCV order). The original yellow and purple are retained.
YELLOW = (77, 216, 255)
PURPLE = (224, 59, 108)
PINK = (156, 122, 240)
ORANGE = (77, 169, 255)
GREEN = (89, 199, 52)
RED = (90, 90, 255)
GRAY = (130, 130, 130)
DARK = (40, 40, 40)
WHITE = (255, 255, 255)
PALE = (249, 249, 252)
RESULT_COLORS = {WIN: GREEN, LOSE: RED, DRAW: (0, 190, 240)}
BUTTON_COLORS = {
    "START": GREEN, "AGAIN": GREEN, "HELP": PURPLE, "SETTINGS": PURPLE,
    "SOUND_TOGGLE": GREEN, "VOLUME_DOWN": GRAY, "VOLUME_UP": GRAY,
    "HISTORY": PURPLE, "CLEAR_HISTORY": ORANGE, "BACK": GRAY,
    "MAIN_MENU": PURPLE, "EXIT": RED, "PAUSE": ORANGE, "RESUME": GREEN,
    "MOVE_ROCK": GREEN, "MOVE_PAPER": PURPLE, "MOVE_SCISSORS": ORANGE,
}
BUTTON_LABELS = {
    "START": "START GAME", "AGAIN": "PLAY AGAIN",
    "HELP": "HOW TO PLAY",
    "SETTINGS": "SETTINGS", "SOUND_TOGGLE": "SOUND: ON",
    "VOLUME_DOWN": "VOLUME -", "VOLUME_UP": "VOLUME +",
    "HISTORY": "HISTORY", "CLEAR_HISTORY": "CLEAR HISTORY", "BACK": "BACK",
    "MAIN_MENU": "MAIN MENU", "EXIT": "EXIT", "PAUSE": "PAUSE",
    "RESUME": "RESUME",
    "MOVE_ROCK": "ROCK", "MOVE_PAPER": "PAPER", "MOVE_SCISSORS": "SCISSORS",
}

LEFT_X, RIGHT_X, CARD_W = 30, 640, 430
CARD_Y, HEADER_H = 110, 50
CAM_H = 322


@lru_cache(maxsize=24)
def _font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size)


def text_center(img, text, cx, cy, scale, color, thickness=2):
    if _TEXT_QUEUE is not None:
        _TEXT_QUEUE.append((str(text), cx, cy, scale, color, thickness))
        return
    (w, h), _ = cv2.getTextSize(str(text), FONT, scale, thickness)
    cv2.putText(img, str(text), (int(cx - w / 2), int(cy + h / 2)), FONT,
                scale, color, thickness, cv2.LINE_AA)


def _render_text(img, commands):
    image = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(image)
    for text, cx, cy, scale, color, thickness in commands:
        size = max(13, round(scale * 28))
        rgb = (int(color[2]), int(color[1]), int(color[0]))
        draw.text((int(cx), int(cy)), text, font=_font(size), fill=rgb,
                  anchor="mm", stroke_width=max(0, round(thickness / 3)),
                  stroke_fill=rgb)
    return cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)


def rounded_rect(img, x, y, w, h, r, color, thickness=-1):
    x, y, w, h, r = (int(v) for v in (x, y, w, h, r))
    if thickness < 0:
        cv2.rectangle(img, (x + r, y), (x + w - r, y + h), color, -1)
        cv2.rectangle(img, (x, y + r), (x + w, y + h - r), color, -1)
        for cx, cy in ((x + r, y + r), (x + w - r, y + r),
                       (x + r, y + h - r), (x + w - r, y + h - r)):
            cv2.circle(img, (cx, cy), r, color, -1, cv2.LINE_AA)
        return
    cv2.line(img, (x + r, y), (x + w - r, y), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + r, y + h), (x + w - r, y + h), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x, y + r), (x, y + h - r), color, thickness, cv2.LINE_AA)
    cv2.line(img, (x + w, y + r), (x + w, y + h - r), color, thickness, cv2.LINE_AA)
    for (cx, cy), start in (((x + r, y + r), 180), ((x + w - r, y + r), 270),
                            ((x + w - r, y + h - r), 0), ((x + r, y + h - r), 90)):
        cv2.ellipse(img, (cx, cy), (r, r), 0, start, start + 90,
                    color, thickness, cv2.LINE_AA)


def finger(img, p1, p2, width, color, thickness):
    (x1, y1), (x2, y2) = p1, p2
    length = math.hypot(x2 - x1, y2 - y1) or 1.0
    nx, ny = -(y2 - y1) / length * width / 2, (x2 - x1) / length * width / 2
    points = np.array([(x1 + nx, y1 + ny), (x2 + nx, y2 + ny),
                       (x2 - nx, y2 - ny), (x1 - nx, y1 - ny)], np.int32)
    cv2.polylines(img, [points], True, color, thickness, cv2.LINE_AA)


def draw_hand_icon(img, move, cx, cy, s, color=WHITE, t=5):
    if move == ROCK:
        rounded_rect(img, cx - 0.5 * s, cy - 0.35 * s, s, 0.9 * s,
                     0.22 * s, color, t)
        for dx in (-0.25, 0.0, 0.25):
            cv2.line(img, (int(cx + dx * s), int(cy - 0.35 * s)),
                     (int(cx + dx * s), int(cy + 0.05 * s)), color, t, cv2.LINE_AA)
        rounded_rect(img, cx - 0.38 * s, cy + 0.12 * s, 0.7 * s, 0.28 * s,
                     0.14 * s, color, t)
    elif move == PAPER:
        rounded_rect(img, cx - 0.45 * s, cy + 0.05 * s, 0.9 * s, 0.6 * s,
                     0.2 * s, color, t)
        for i, height in enumerate((0.75, 0.95, 0.9, 0.7)):
            fx = cx - 0.34 * s + i * 0.227 * s
            finger(img, (fx, cy + 0.15 * s), (fx, cy + 0.15 * s - height * s),
                   0.19 * s, color, t)
        finger(img, (cx - 0.4 * s, cy + 0.4 * s),
               (cx - 0.78 * s, cy - 0.05 * s), 0.19 * s, color, t)
    elif move == SCISSORS:
        rounded_rect(img, cx - 0.45 * s, cy + 0.1 * s, 0.9 * s, 0.55 * s,
                     0.2 * s, color, t)
        finger(img, (cx - 0.12 * s, cy + 0.2 * s),
               (cx - 0.38 * s, cy - 0.7 * s), 0.19 * s, color, t)
        finger(img, (cx + 0.12 * s, cy + 0.2 * s),
               (cx + 0.38 * s, cy - 0.7 * s), 0.19 * s, color, t)
        for dx in (0.2, 0.38):
            cv2.circle(img, (int(cx + dx * s), int(cy + 0.3 * s)),
                       int(0.1 * s), color, t, cv2.LINE_AA)
    else:
        text_center(img, "?", cx, cy, s / 28, color, 8)


def make_background():
    bg = np.full((HEIGHT, WIDTH, 3), PALE, np.uint8)
    for x in range(-HEIGHT, WIDTH, 52):
        cv2.line(bg, (x, HEIGHT), (x + HEIGHT, 0), (242, 242, 246), 10)
    cv2.rectangle(bg, (0, 0), (WIDTH, 82), YELLOW, -1)
    cv2.line(bg, (0, 82), (WIDTH, 82), (35, 31, 28), 4)
    return bg


def buttons_for(game, view):
    """Return the clickable controls visible on the selected screen."""
    specs = {
        "WELCOME": [("START", 410, 565, 280, 66)],
        "HOME": [
            ("START", 165, 505, 230, 62), ("HELP", 435, 505, 230, 62),
            ("SETTINGS", 705, 505, 230, 62), ("HISTORY", 300, 580, 230, 58),
            ("EXIT", 570, 580, 230, 58),
        ],
        "HELP": [("BACK", 300, 580, 220, 60), ("START", 580, 580, 220, 60)],
        "SETTINGS": [
            ("SOUND_TOGGLE", 235, 500, 260, 60),
            ("VOLUME_DOWN", 520, 500, 150, 60),
            ("VOLUME_UP", 690, 500, 150, 60),
            ("BACK", 440, 580, 220, 58),
        ],
        "HISTORY": [
            ("BACK", 300, 580, 220, 60),
            ("CLEAR_HISTORY", 580, 580, 220, 60),
        ],
        "RESULT": [
            ("AGAIN", 150, 575, 220, 62), ("MAIN_MENU", 390, 575, 220, 62),
            ("HISTORY", 630, 575, 190, 62), ("EXIT", 840, 575, 150, 62),
        ],
        "PAUSED": [("RESUME", 300, 575, 220, 62), ("EXIT", 580, 575, 220, 62)],
    }
    if view == "GAME":
        if game.state == State.CAPTURE:
            names = ["MOVE_ROCK", "MOVE_PAPER", "MOVE_SCISSORS", "PAUSE", "EXIT"]
        else:
            names = ["PAUSE", "EXIT"]
        if len(names) == 5:
            specs["GAME"] = [(name, 68 + index * 198, 575, 178, 62)
                             for index, name in enumerate(names)]
        else:
            specs["GAME"] = [(name, 300 + index * 270, 575, 230, 62)
                             for index, name in enumerate(names)]
    return [Button(name, BUTTON_LABELS[name], x, y, w, h)
            for name, x, y, w, h in specs.get(view, [])]


class Renderer:
    def __init__(self) -> None:
        self._background = make_background()

    def draw(self, game, frame, raw_gesture, view, buttons, cursor, clicker, now,
             audio_enabled=True, volume=0.8, camera_available=True,
             audio_available=True):
        global _TEXT_QUEUE
        canvas = self._background.copy()
        _TEXT_QUEUE = []
        try:
            self._draw_header(canvas, view, camera_available, audio_enabled)
            if view == "WELCOME":
                self._draw_welcome(canvas)
            elif view == "HOME":
                self._draw_home(canvas, game)
            elif view == "HELP":
                self._draw_help(canvas)
            elif view == "SETTINGS":
                self._draw_settings(canvas, audio_enabled, volume, audio_available)
            elif view == "HISTORY":
                self._draw_history(canvas, game)
            elif view == "RESULT":
                self._draw_result(canvas, game)
            else:
                self._draw_cards(canvas, game, frame, raw_gesture)
                self._draw_center_box(canvas, game)
                self._draw_caption(canvas, game)
                if view == "PAUSED":
                    self._draw_paused_overlay(canvas)
            self._draw_buttons(canvas, buttons, clicker, now, audio_enabled,
                               audio_available)
            self._draw_footer(canvas, buttons, cursor, camera_available)
            self._draw_cursor(canvas, buttons, cursor, clicker, now)
            return _render_text(canvas, _TEXT_QUEUE)
        finally:
            _TEXT_QUEUE = None

    def _draw_header(self, canvas, view, camera_available, audio_enabled):
        titles = {
            "WELCOME": "HANDPLAY  •  ROCK PAPER SCISSORS",
            "HOME": "HANDPLAY  •  ROCK PAPER SCISSORS",
            "HELP": "HOW TO PLAY", "SETTINGS": "SETTINGS",
            "HISTORY": "MATCH HISTORY", "RESULT": "MATCH COMPLETE",
            "GAME": "ROCK  •  PAPER  •  SCISSORS", "PAUSED": "GAME PAUSED",
        }
        text_center(canvas, titles.get(view, "HANDPLAY"), WIDTH / 2, 40,
                    1.3 if view in ("WELCOME", "HOME", "GAME") else 1.15,
                    (20, 24, 30), 2)
        status = "CAMERA READY" if camera_available else "CAMERA OFF  •  MOUSE READY"
        status_color = GREEN if camera_available else (65, 65, 180)
        if view not in ("GAME", "PAUSED", "RESULT"):
            rounded_rect(canvas, 28, 99, 210, 34, 14, WHITE)
            cv2.circle(canvas, (46, 116), 5, status_color, -1, cv2.LINE_AA)
            text_center(canvas, status, 140, 116, 0.42, DARK, 1)
            rounded_rect(canvas, 924, 99, 148, 34, 14, WHITE)
            cv2.circle(canvas, (943, 116), 5, GREEN if audio_enabled else GRAY,
                       -1, cv2.LINE_AA)
            text_center(canvas, "SOUND ON" if audio_enabled else "SOUND OFF",
                        1004, 116, 0.48, DARK, 1)

    def _draw_welcome(self, canvas):
        rounded_rect(canvas, 180, 165, 740, 340, 28, (220, 218, 199))
        rounded_rect(canvas, 180, 157, 740, 340, 28, WHITE)
        rounded_rect(canvas, 180, 157, 740, 15, 8, PURPLE)
        cv2.circle(canvas, (550, 265), 66, PINK, -1, cv2.LINE_AA)
        draw_hand_icon(canvas, PAPER, 550, 267, 60, WHITE, 5)
        text_center(canvas, "WELCOME TO HANDPLAY", 550, 365, 1.2, DARK, 2)
        text_center(canvas, "Rock, paper, scissors — now played with your hand.",
                    550, 410, 0.62, GRAY, 1)
        text_center(canvas, "Show a gesture to your camera, or use your mouse.",
                    550, 446, 0.54, GRAY, 1)

    def _draw_home(self, canvas, game):
        rounded_rect(canvas, 110, 165, 880, 305, 26, (220, 218, 199))
        rounded_rect(canvas, 110, 157, 880, 305, 26, WHITE)
        rounded_rect(canvas, 110, 157, 880, 12, 6, PURPLE)
        text_center(canvas, "MAKE YOUR MOVE", 400, 225, 1.5, DARK, 2)
        text_center(canvas, "Play with your hand. Beat the computer.", 400, 275,
                    0.72, GRAY, 1)
        text_center(canvas, "First to 3 wins takes the match.", 400, 312,
                    0.62, GRAY, 1)
        for index, move in enumerate((ROCK, PAPER, SCISSORS)):
            cx = 290 + index * 110
            rounded_rect(canvas, cx - 42, 355, 84, 74, 18, PALE)
            draw_hand_icon(canvas, move, cx, 392, 37, PURPLE, 3)
            text_center(canvas, move, cx, 449, 0.42, DARK, 1)
        rounded_rect(canvas, 705, 208, 205, 195, 25, (246, 245, 255))
        cv2.circle(canvas, (807, 276), 42, YELLOW, -1, cv2.LINE_AA)
        draw_hand_icon(canvas, PAPER, 807, 278, 39, DARK, 3)
        text_center(canvas, "YOUR HAND", 807, 350, 0.65, DARK, 1)
        text_center(canvas, f"Rounds recorded: {len(game.history)}",
                    550, 485, 0.58, PURPLE, 1)

    def _draw_help(self, canvas):
        text_center(canvas, "THREE GESTURES. CLASSIC RULES.", 550, 165,
                    1.05, DARK, 2)
        text_center(canvas, "Make a clear pose and show one hand to the camera.",
                    550, 205, 0.58, GRAY, 1)
        cards = [
            (ROCK, "Close your hand", "Rock beats scissors"),
            (PAPER, "Open your hand", "Paper beats rock"),
            (SCISSORS, "Raise two fingers", "Scissors beat paper"),
        ]
        for index, (move, gesture, beats) in enumerate(cards):
            x = 68 + index * 324
            rounded_rect(canvas, x, 245, 290, 250, 22, WHITE)
            rounded_rect(canvas, x, 245, 290, 48, 16, PURPLE)
            text_center(canvas, move, x + 145, 270, 0.8, WHITE, 2)
            cv2.circle(canvas, (x + 145, 365), 48, PINK, -1, cv2.LINE_AA)
            draw_hand_icon(canvas, move, x + 145, 365, 44, WHITE, 4)
            text_center(canvas, gesture, x + 145, 438, 0.6, DARK, 1)
            text_center(canvas, beats, x + 145, 470, 0.49, GRAY, 1)
        rounded_rect(canvas, 145, 515, 810, 42, 16, (244, 243, 255))
        text_center(canvas, "Wait for the countdown, then hold your gesture still "
                             "until the round is recorded.", 550, 536,
                    0.5, PURPLE, 1)

    def _draw_settings(self, canvas, audio_enabled, volume, audio_available):
        rounded_rect(canvas, 250, 170, 600, 285, 24, (220, 218, 199))
        rounded_rect(canvas, 250, 162, 600, 285, 24, WHITE)
        rounded_rect(canvas, 250, 162, 600, 10, 5, PURPLE)
        text_center(canvas, "SOUND EFFECTS", 550, 220, 0.95, DARK, 2)
        text_center(canvas, "Round results and countdown feedback",
                    550, 257, 0.56, GRAY, 1)
        rounded_rect(canvas, 333, 288, 434, 54, 18,
                     (229, 249, 239) if audio_enabled else (241, 241, 244))
        cv2.circle(canvas, (366, 315), 11, GREEN if audio_enabled else GRAY,
                   -1, cv2.LINE_AA)
        text_center(canvas, "SOUND IS ON" if audio_enabled else "SOUND IS OFF",
                    540, 315, 0.7, DARK, 2)
        text_center(canvas, f"VOLUME  {round(volume * 100)}%", 550, 378,
                    0.72, PURPLE, 2)
        cv2.rectangle(canvas, (366, 407), (734, 415), (223, 222, 230), -1)
        cv2.rectangle(canvas, (366, 407),
                      (366 + round(368 * volume), 415), PURPLE, -1)
        for tick in range(0, 101, 10):
            x = 366 + round(368 * tick / 100)
            cv2.circle(canvas, (x, 411), 4 if tick % 20 == 0 else 2,
                       YELLOW if tick <= round(volume * 100) else GRAY,
                       -1, cv2.LINE_AA)
        description = ("Use the buttons below to adjust sound and volume."
                       if audio_available else
                       "No audio device is available. Check your Windows playback device.")
        text_center(canvas, description, 550, 440, 0.43, GRAY, 1)

    def _card(self, canvas, x, title, score, badge_color):
        cv2.rectangle(canvas, (x, CARD_Y),
                      (x + CARD_W, CARD_Y + HEADER_H + CAM_H), WHITE, -1)
        cv2.rectangle(canvas, (x, CARD_Y),
                      (x + CARD_W, CARD_Y + HEADER_H), PURPLE, -1)
        cv2.rectangle(canvas, (x, CARD_Y),
                      (x + CARD_W, CARD_Y + HEADER_H + CAM_H), PURPLE, 5)
        text_center(canvas, title, x + CARD_W / 2 - 40, CARD_Y + HEADER_H / 2,
                    0.9, WHITE, 2)
        rounded_rect(canvas, x + CARD_W - 94, CARD_Y + 6, 84, HEADER_H - 12,
                     10, badge_color)
        text_center(canvas, str(score), x + CARD_W - 52, CARD_Y + HEADER_H / 2,
                    0.9, WHITE, 2)
        return CARD_Y + HEADER_H

    def _draw_cards(self, canvas, game, frame, raw_gesture):
        scores = game.score
        top = self._card(canvas, LEFT_X, "COMPUTER", scores.computer_score, RED)
        cx, cy = LEFT_X + CARD_W // 2, top + CAM_H // 2 - 8
        cv2.circle(canvas, (cx, cy), 112, PINK, -1, cv2.LINE_AA)
        draw_hand_icon(canvas, game.visible_computer_move, cx, cy + 8, 110)
        text_center(canvas, game.visible_computer_move or "HIDDEN",
                    cx, top + CAM_H - 16, 0.65, GRAY, 1)

        top = self._card(canvas, RIGHT_X, "PLAYER", scores.player_score, GREEN)
        if frame is not None:
            camera = cv2.resize(frame, (CARD_W, CAM_H))
            canvas[top:top + CAM_H, RIGHT_X:RIGHT_X + CARD_W] = camera
        else:
            canvas[top:top + CAM_H, RIGHT_X:RIGHT_X + CARD_W] = (48, 48, 58)
            text_center(canvas, "CAMERA NOT AVAILABLE", RIGHT_X + CARD_W / 2,
                        top + CAM_H / 2 - 12, 0.65, WHITE, 1)
            text_center(canvas, "Use the mouse to play", RIGHT_X + CARD_W / 2,
                        top + CAM_H / 2 + 28, 0.48, (205, 205, 205), 1)
        if game.state == State.RESULT and game.player_move:
            text = "YOU: " + game.player_move
        elif game.state == State.CAPTURE:
            text = "SEEING: " + raw_gesture
        else:
            text = ""
        if text and frame is not None:
            cv2.rectangle(canvas, (RIGHT_X, top + CAM_H - 36),
                          (RIGHT_X + CARD_W, top + CAM_H), DARK, -1)
            text_center(canvas, text, RIGHT_X + CARD_W / 2,
                        top + CAM_H - 18, 0.58, WHITE, 1)
        cv2.rectangle(canvas, (RIGHT_X, CARD_Y),
                      (RIGHT_X + CARD_W, CARD_Y + HEADER_H + CAM_H), PURPLE, 5)
        for y in range(CARD_Y, CARD_Y + HEADER_H + CAM_H, 22):
            cv2.line(canvas, (550, y), (550, y + 11), GRAY, 3)

    def _draw_center_box(self, canvas, game):
        color, label, scale = ORANGE, "VS", 1.1
        if game.state == State.COUNTDOWN:
            label, scale = str(game.countdown_number), 1.8
        elif game.state == State.CAPTURE:
            label, scale = "GO!", 1.4
        elif game.state == State.RESULT and game.result:
            color, label = RESULT_COLORS[game.result], game.result
        rounded_rect(canvas, 480, 262, 140, 74, 16, WHITE)
        rounded_rect(canvas, 480, 257, 140, 74, 16, color)
        text_center(canvas, label, 550, 294, scale, WHITE, 3)

    def _draw_caption(self, canvas, game):
        score = game.score
        caption, color = "", DARK
        if game.state == State.HOME:
            caption = "Choose START GAME from the menu"
        elif game.state == State.READY:
            caption = game.message or "Get ready for your first round"
        elif game.state == State.COUNTDOWN:
            caption = "Get ready... do not show your hand yet"
        elif game.state == State.CAPTURE:
            caption = "Show ROCK, PAPER, or SCISSORS!"
        elif game.state == State.RESULT:
            if game.is_game_over:
                won = score.player_score > score.computer_score
                caption = "YOU WON THE MATCH!" if won else "COMPUTER WON THE MATCH"
                color = GREEN if won else RED
            else:
                caption = {WIN: "You win this round!", LOSE: "AI wins this round",
                           DRAW: "It is a draw"}[game.result]
                color = RESULT_COLORS[game.result]
        text_center(canvas, caption, WIDTH / 2, 514, 0.9, color, 2)
        goal = f"First to {game.target_score}" if game.target_score else "Free play"
        text_center(canvas, f"{goal}  |  Draws {score.draws}  |  Rounds {score.rounds}",
                    WIDTH / 2, 545, 0.52, GRAY, 1)

    def _draw_result(self, canvas, game):
        score = game.score
        won = score.player_score > score.computer_score
        rounded_rect(canvas, 255, 155, 590, 390, 28, (220, 218, 199))
        rounded_rect(canvas, 255, 147, 590, 390, 28, WHITE)
        rounded_rect(canvas, 255, 147, 590, 12, 6, PURPLE)
        cv2.circle(canvas, (550, 222), 43, YELLOW, -1, cv2.LINE_AA)
        draw_hand_icon(canvas, PAPER, 550, 222, 40, DARK, 3)
        title = "YOU WON!" if won else "COMPUTER WINS"
        text_center(canvas, title, 550, 298, 1.25, GREEN if won else RED, 2)
        text_center(canvas, "FINAL SCORE", 550, 340, 0.55, GRAY, 1)
        rounded_rect(canvas, 380, 365, 340, 70, 18, (246, 245, 255))
        text_center(canvas, f"YOU   {score.player_score}     -     "
                            f"{score.computer_score}   AI", 550, 400,
                    0.85, PURPLE, 2)
        text_center(canvas, f"Rounds played {score.rounds}    "
                            f"Draws {score.draws}", 550, 473,
                    0.56, DARK, 1)
        text_center(canvas, "Play again or return to the main menu.",
                    550, 510, 0.48, GRAY, 1)

    def _draw_history(self, canvas, game):
        x, y, w, h = 110, 155, 880, 395
        rounded_rect(canvas, x, y + 5, w, h, 20, (220, 218, 199))
        rounded_rect(canvas, x, y, w, h, 20, WHITE)
        rounded_rect(canvas, x, y, w, 52, 18, PURPLE)
        text_center(canvas, "HISTORY - RECENT ROUNDS", WIDTH / 2, y + 27,
                    0.88, WHITE, 2)
        columns = (x + 90, x + 310, x + 530, x + 750)
        for cx, name in zip(columns, ("ROUND", "YOU", "COMPUTER", "RESULT")):
            text_center(canvas, name, cx, y + 84, 0.57, GRAY, 1)
        cv2.line(canvas, (x + 20, y + 103), (x + w - 20, y + 103),
                 (200, 200, 200), 2)
        rounds = game.history.recent()
        if not rounds:
            text_center(canvas, "No rounds yet", WIDTH / 2, y + 226,
                        0.9, GRAY, 2)
            text_center(canvas, "Play a match and your results will appear here.",
                        WIDTH / 2, y + 270, 0.52, GRAY, 1)
        for index, item in enumerate(rounds[:10]):
            row_y = y + 132 + index * 25
            values = (str(len(rounds) - index), item["player"],
                      item["computer"], item["result"])
            for column, (cx, value) in enumerate(zip(columns, values)):
                color = RESULT_COLORS[item["result"]] if column == 3 else DARK
                text_center(canvas, value, cx, row_y, 0.5, color,
                            2 if column == 3 else 1)
        counts = {
            WIN: sum(item["result"] == WIN for item in rounds),
            LOSE: sum(item["result"] == LOSE for item in rounds),
            DRAW: sum(item["result"] == DRAW for item in rounds),
        }
        text_center(canvas, f"Recent {len(rounds)}  •  Wins {counts[WIN]}  "
                            f"Losses {counts[LOSE]}  Draws {counts[DRAW]}",
                    WIDTH / 2, y + h - 20, 0.55, PURPLE, 1)

    def _draw_paused_overlay(self, canvas):
        overlay = canvas.copy()
        cv2.rectangle(overlay, (0, 82), (WIDTH, HEIGHT), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.58, canvas, 0.42, 0, canvas)
        text_center(canvas, "GAME PAUSED", WIDTH / 2, 310, 1.6, WHITE, 4)
        text_center(canvas, "Take a break, then select RESUME",
                    WIDTH / 2, 365, 0.75, WHITE, 2)

    def _draw_buttons(self, canvas, buttons, clicker, now, audio_enabled,
                      audio_available):
        for button in buttons:
            color = BUTTON_COLORS[button.name]
            rounded_rect(canvas, button.x, button.y + 5, button.w, button.h,
                         16, (160, 160, 160))
            rounded_rect(canvas, button.x, button.y, button.w, button.h, 16, color)
            rounded_rect(canvas, button.x, button.y, button.w, button.h, 16,
                         WHITE, 2)
            label = button.label
            if button.name == "SOUND_TOGGLE":
                label = ("SOUND: ON" if audio_enabled else "SOUND: OFF") \
                    if audio_available else "NO AUDIO DEVICE"
            text_center(canvas, label, button.x + button.w / 2,
                        button.y + button.h / 2 - 2, 0.65, WHITE, 2)
            if button.name == "START":
                bx, by, bw, bh = (int(button.x + 25), int(button.y + button.h - 15),
                                  int(button.w - 50), 7)
                cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), DARK, 1)
                fill = int(bw * clicker.progress(button.name, now))
                if fill > 0:
                    cv2.rectangle(canvas, (bx, by), (bx + fill, by + bh), WHITE, -1)

    def _draw_footer(self, canvas, buttons, cursor, camera_available):
        if cursor is None:
            text, color = ("Camera unavailable - click with your mouse"
                           if not camera_available else
                           "Point at a button and hold for 1 second to select"), (0, 120, 220)
        elif buttons:
            text, color = "Hold your index finger on a button for 1 second", GRAY
        else:
            text, color = "", GRAY
        text_center(canvas, text, WIDTH / 2, 676, 0.48, color, 1)

    def _draw_cursor(self, canvas, buttons, cursor, clicker, now):
        if cursor is None or not buttons:
            return
        pos = (int(cursor[0]), int(cursor[1]))
        cv2.circle(canvas, pos, 11, (255, 120, 0), -1, cv2.LINE_AA)
        cv2.circle(canvas, pos, 11, WHITE, 2, cv2.LINE_AA)
        for button in buttons:
            progress = clicker.progress(button.name, now)
            if progress > 0:
                cv2.ellipse(canvas, pos, (22, 22), 0, -90,
                            -90 + 360 * progress, (0, 200, 255), 4, cv2.LINE_AA)
