from PIL import Image
from babytrack.geometry import Box
from babytrack.options import Opts, STYLES_HUD, STYLES_FILTER
from babytrack.renderers import RENDERERS, apply_style

def _blank():
    return Image.new("RGB", (200, 200), (0, 0, 0))

def _box():
    return Box(40, 40, 80, 80, "person", 0.9)

def test_all_hud_styles_registered():
    for name in STYLES_HUD:
        assert name in RENDERERS

def test_hud_render_changes_pixels():
    img = _blank()
    apply_style(img, _box(), Opts(style="Frame", color="#00ff66"))
    assert img.getextrema() != ((0, 0), (0, 0), (0, 0))

def test_basic_draws_rectangle_edge():
    img = _blank()
    apply_style(img, _box(), Opts(style="Basic", color="#ffffff", stroke=2))
    assert img.getpixel((40, 41)) != (0, 0, 0)

def test_all_filter_styles_registered():
    for name in STYLES_FILTER:
        assert name in RENDERERS

def test_filter_changes_region_pixels():
    img = Image.new("RGB", (200, 200), (10, 120, 200))
    apply_style(img, Box(40, 40, 80, 80, "car", 0.8), Opts(style="Invert"))
    assert img.getpixel((80, 80)) != (10, 120, 200)

import pytest
from babytrack.options import ALL_STYLES

@pytest.mark.parametrize("style", ALL_STYLES)
def test_every_style_renders_without_crashing(style):
    img = Image.new("RGB", (200, 200), (60, 60, 60))
    apply_style(img, _box(), Opts(style=style))

