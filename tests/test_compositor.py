from PIL import Image
from babytrack.geometry import Box
from babytrack.options import Opts
from babytrack.compositor import compose

def test_compose_does_not_mutate_original():
    original = Image.new("RGB", (200, 200), (0, 0, 0))
    boxes = [Box(40, 40, 80, 80, "person", 0.9)]
    out = compose(original, boxes, Opts(style="Basic", color="#ffffff"))
    assert original.getextrema() == ((0, 0), (0, 0), (0, 0))  # untouched
    assert out.getextrema() != ((0, 0), (0, 0), (0, 0))       # has drawing

def test_compose_with_no_boxes_returns_copy():
    original = Image.new("RGB", (50, 50), (5, 5, 5))
    out = compose(original, [], Opts())
    assert out is not original
    assert out.tobytes() == original.convert("RGB").tobytes()
