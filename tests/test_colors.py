from babytrack.colors import resolve_color
from babytrack.options import Opts

def test_single_color_is_fixed():
    o = Opts(color_mode="single", color="#ff0000")
    assert resolve_color(o, "person") == "#ff0000"

def test_by_label_is_stable_per_label():
    o = Opts(color_mode="by-label")
    assert resolve_color(o, "person") == resolve_color(o, "person")
    assert resolve_color(o, "person") != resolve_color(o, "car")

def test_random_is_valid_hex():
    o = Opts(color_mode="random")
    c = resolve_color(o, "person")
    assert c.startswith("#") and len(c) == 7
