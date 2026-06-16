from PIL import Image
from babytrack.geometry import Box
from babytrack.options import Opts, REGION_FILLS
from babytrack.region_fx import REGION_FX, apply_region_fx

def _img():
    return Image.new("RGB", (200, 200), (120, 120, 120))

def _box():
    return Box(40, 40, 80, 80, "OBJ", 1.0)

def test_all_region_fills_registered_except_none():
    for name in REGION_FILLS:
        if name == "none":
            continue
        assert name in REGION_FX

def test_none_is_noop():
    img = _img()
    before = img.tobytes()
    apply_region_fx(img, _box(), Opts(region_fill="none"))
    assert img.tobytes() == before

def test_invert_changes_region_only():
    img = _img()
    apply_region_fx(img, _box(), Opts(region_fill="invert"))
    assert img.getpixel((80, 80)) != (120, 120, 120)   # inside box changed
    assert img.getpixel((5, 5)) == (120, 120, 120)      # outside untouched

def test_every_region_fill_runs():
    for name in REGION_FILLS:
        img = _img()
        apply_region_fx(img, _box(), Opts(region_fill=name, color="#3366ff"))

def test_region_fill_follows_shape():
    import numpy as np
    base = np.random.default_rng(1).integers(0, 255, (200, 200, 3), dtype=np.uint8)
    img = Image.fromarray(base.copy())
    corner = img.getpixel((42, 42))
    apply_region_fx(img, _box(), Opts(region_fill="invert", box_shape="ellipse"))
    assert img.getpixel((42, 42)) == corner        # outside ellipse untouched
    assert img.getpixel((80, 80)) != corner        # inside changed
