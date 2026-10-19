"""Tests for choosing the primary detected hand."""
from src.hand_tracker import select_primary_hand


def test_select_primary_hand_returns_largest_bounding_box():
    small_hand = [(0.1, 0.1, 0.0), (0.3, 0.2, 0.0)]
    large_hand = [(0.4, 0.4, 0.0), (0.9, 0.8, 0.0)]

    assert select_primary_hand([small_hand, large_hand]) == large_hand
