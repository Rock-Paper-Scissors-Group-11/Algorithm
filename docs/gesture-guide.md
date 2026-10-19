# Gesture guide

The desktop classifier examines four fingers: index, middle, ring, and pinky. For each finger, it divides the wrist-to-tip distance by the wrist-to-middle-joint distance. The finger is considered extended only when that ratio is greater than `FINGER_EXTENDED_RATIO` (currently `1.15` in `src/config.py`).

- **Rock:** keep all four recognized fingers folded.
- **Paper:** extend three or four recognized fingers.
- **Scissors:** extend the index and middle fingers while keeping the ring finger and pinky folded.
- **Unknown:** no hand is visible, landmarks are invalid, or the finger combination does not match one of those rules (for example, only one finger extended).

The thumb is not part of the classifier's four-finger count. If more than one hand is detected, HandPlay uses the hand with the largest normalized bounding-box area.

## Tips

- Keep your hand fully inside the camera view and far enough from the camera that all landmarks can be seen.
- Use even, bright lighting; shadows, backlighting, and dim rooms can make landmarks harder to detect.
- Show one hand at a time for the most predictable control.
- Hold the gesture steady so the stabilizer can recognize it across multiple frames.
