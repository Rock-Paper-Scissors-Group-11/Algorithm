"""Tests for fitting the game canvas into the desktop window."""
from play_game import fit_scale, window_to_canvas


def test_fit_scale_preserves_matching_aspect_ratio():
    assert fit_scale(1100, 700, 2200, 1400) == (2.0, 0, 0, 2200, 1400)


def test_fit_scale_centers_canvas_in_a_wider_window():
    assert fit_scale(1100, 700, 1600, 900) == (
        900 / 700, 93, 0, 1414, 900,
    )


def test_fit_scale_centers_canvas_in_a_taller_window():
    assert fit_scale(1100, 700, 1100, 1000) == (1.0, 0, 150, 1100, 700)


def test_fit_scale_handles_minimized_window():
    assert fit_scale(1100, 700, 0, 0) is None


def test_window_click_maps_to_canvas_coordinates():
    assert window_to_canvas(800, 450, 1100, 700, 1600, 900) == (550, 350)


def test_window_click_in_letterbox_is_ignored():
    assert window_to_canvas(20, 450, 1100, 700, 1600, 900) is None
