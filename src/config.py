"""All adjustable settings live here, so nobody hard-codes numbers elsewhere."""

# Camera
CAMERA_INDEX = 0
FRAME_WIDTH = 640
FRAME_HEIGHT = 480
MIRROR_VIEW = True

# Hand tracking
MAX_HANDS = 1
DETECTION_CONFIDENCE = 0.7
TRACKING_CONFIDENCE = 0.6

# Stabilizer
STABILITY_FRAMES = 10
STABILITY_REQUIRED = 7

# Game
COUNTDOWN_SECONDS = 3.0
RESULT_SECONDS = 3.0
TARGET_SCORE = 3

# Valid moves
ROCK = "ROCK"
PAPER = "PAPER"
SCISSORS = "SCISSORS"
UNKNOWN = "UNKNOWN"

# Start gesture
START_GESTURE = PAPER
START_HOLD_SECONDS = 3.0

# Gesture classifier
FINGER_EXTENDED_RATIO = 1.15

# Gesture stabilizer
STABILIZER_WINDOW = 10
STABILIZER_MIN_VOTES = 7

# Game controller
CAPTURE_TIMEOUT_SECONDS = 5.0
HISTORY_SIZE = 10

# Click with the hand (the screen buttons)
DWELL_SECONDS = 1.0