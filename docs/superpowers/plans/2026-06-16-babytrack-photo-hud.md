# BabyTrack Photo HUD Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Tkinter desktop app that loads one photo, finds many visual blobs (OpenCV feature/contour regions, count 16–512), and overlays configurable BabyTrack-style tracking HUD/filter effects on each blob, viewable on screen and savable as PNG.

**Architecture:** Pure logic (blob detector, geometry, color, renderers, compositor, export) lives in small testable modules under `babytrack/`. The Tkinter GUI (`app.py`) is a thin shell that binds widgets to an `Opts` dataclass, runs OpenCV blob detection, and calls the compositor. Detection is pure CPU OpenCV (fast, no model), re-run only when a detection param changes. Renderers are small functions keyed by style name in a registry, so the settings panel just lists registry keys.

**Tech Stack:** Python 3.13, Tkinter (stdlib), OpenCV (`opencv-python`), Pillow, NumPy, pytest. No YOLO/torch — detection is OpenCV feature/contour blobs with user-controlled count (16–512), mirroring BabyTrack.

> **Note on file structure:** The spec proposed a single `babytrack.py`. This plan splits into focused modules instead — 30 renderers plus GUI is too large for one file to test or hold in context. Same app, better boundaries.

---

## File Structure

```
babytrack-hud/
  requirements.txt
  babytrack/
    __init__.py
    geometry.py      # Box dataclass
    options.py       # Opts dataclass (all settings + defaults)
    colors.py        # resolve_color() for single/random/by-label modes
    blobs.py         # detect_blobs(image, opts) -> list[Box]  (OpenCV)
    renderers.py     # registry of HUD + filter render functions
    compositor.py    # compose(original, boxes, opts) -> PIL.Image
    export.py        # save_png(image, path)
    app.py           # Tkinter GUI (manual-tested)
  tests/
    test_geometry.py
    test_colors.py
    test_blobs.py
    test_renderers.py
    test_compositor.py
    test_export.py
  main.py            # entry: python main.py -> launches app
```

---

## Task 1: Project scaffold

**Files:**
- Create: `requirements.txt`
- Create: `babytrack/__init__.py`
- Create: `main.py`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create requirements.txt**

```
opencv-python>=4.9
pillow>=10.0
numpy>=1.26
pytest>=8.0
```

- [ ] **Step 2: Create empty package markers**

`babytrack/__init__.py`:
```python
```
`tests/__init__.py`:
```python
```

- [ ] **Step 3: Create main.py entry point**

```python
from babytrack.app import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Create and activate virtualenv, install deps**

Run:
```bash
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
```
Expected: installs succeed (opencv-python ~40MB; no torch, no model download).

- [ ] **Step 5: Commit**

```bash
git add requirements.txt babytrack/__init__.py main.py tests/__init__.py
git commit -m "chore: scaffold babytrack package"
```

---

## Task 2: Box geometry

**Files:**
- Create: `babytrack/geometry.py`
- Test: `tests/test_geometry.py`

- [ ] **Step 1: Write the failing test**

```python
from babytrack.geometry import Box

def test_box_corners_and_center():
    b = Box(x=10, y=20, w=100, h=50, label="person", conf=0.97)
    assert b.x2 == 110
    assert b.y2 == 70
    assert b.center == (60, 45)

def test_box_resized_keeps_center():
    b = Box(x=0, y=0, w=100, h=100, label="cat", conf=0.5)
    r = b.resized(50)  # force 50x50 box, same center
    assert (r.w, r.h) == (50, 50)
    assert r.center == b.center
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_geometry.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.geometry`

- [ ] **Step 3: Write minimal implementation**

```python
from dataclasses import dataclass

@dataclass
class Box:
    x: int
    y: int
    w: int
    h: int
    label: str
    conf: float

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def resized(self, size: int) -> "Box":
        cx, cy = self.center
        return Box(cx - size // 2, cy - size // 2, size, size, self.label, self.conf)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_geometry.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/geometry.py tests/test_geometry.py
git commit -m "feat: add Box geometry"
```

---

## Task 3: Options dataclass

**Files:**
- Create: `babytrack/options.py`

- [ ] **Step 1: Write implementation (no test — pure defaults container)**

```python
from dataclasses import dataclass

STYLES_HUD = [
    "Basic", "Cross", "Label", "Frame", "L-Frame", "X-Frame", "Grid",
    "Particle", "Dash", "Scope", "Win2K", "Label 2", "Glow", "Backdrop",
]
STYLES_FILTER = [
    "Invert", "Fusion", "Inv", "Glitch", "Thermal", "Pixel", "Tone", "Blur",
    "Dither", "Zoom", "X-Ray", "Water", "Mask", "CRT", "Edge", "Blink",
]
ALL_STYLES = STYLES_HUD + STYLES_FILTER

@dataclass
class Opts:
    # detection params (changing these re-runs blob detection)
    blob_mode: str = "count"         # count | size
    blob_count: int = 128            # 16..512
    bounding_size: int = 48          # box side for By Count
    min_blob_size: int = 16          # min contour size for By Size
    # render params (changing these only re-composes)
    style: str = "Frame"
    stroke: int = 2
    same_size: bool = False          # False: keep detection box size (By Count=fixed, By Size=contour). True: force bounding_size
    color_mode: str = "single"       # single | random | by-label
    color: str = "#00ff66"           # used when color_mode == single
    label_mode: str = "generic"      # generic | random | custom
    label_custom: str = "TARGET"
    label_pos: str = "top"           # center | top | bottom
    font_size: int = 14
    show_score: bool = True

DETECTION_PARAMS = {"blob_mode", "blob_count", "bounding_size", "min_blob_size"}
```

- [ ] **Step 2: Sanity import check**

Run: `.venv/Scripts/python -c "from babytrack.options import Opts, ALL_STYLES; print(len(ALL_STYLES))"`
Expected: prints `30`

- [ ] **Step 3: Commit**

```bash
git add babytrack/options.py
git commit -m "feat: add Opts settings dataclass"
```

---

## Task 4: Color resolution

**Files:**
- Create: `babytrack/colors.py`
- Test: `tests/test_colors.py`

- [ ] **Step 1: Write the failing test**

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_colors.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.colors`

- [ ] **Step 3: Write minimal implementation**

```python
import hashlib
import random
from babytrack.options import Opts

def _hex_from_int(n: int) -> str:
    return "#{:06x}".format(n & 0xFFFFFF)

def resolve_color(opts: Opts, label: str) -> str:
    if opts.color_mode == "single":
        return opts.color
    if opts.color_mode == "by-label":
        h = hashlib.md5(label.encode()).hexdigest()
        return "#" + h[:6]
    return _hex_from_int(random.randint(0, 0xFFFFFF))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_colors.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/colors.py tests/test_colors.py
git commit -m "feat: add color resolution by mode"
```

---

## Task 5: Blob detector (OpenCV)

**Files:**
- Create: `babytrack/blobs.py`
- Test: `tests/test_blobs.py`

`detect_blobs(pil_image, opts)` returns `list[Box]`. Two modes mirror the website:
**By Count** (Shi-Tomasi corners → N fixed-size boxes) and **By Size** (Canny → contours →
boxes by extent). Tests use a synthetic image with known high-contrast features.

- [ ] **Step 1: Write the failing test**

```python
import numpy as np
from PIL import Image
from babytrack.blobs import detect_blobs
from babytrack.options import Opts

def _dotted_image():
    # black image with several bright squares => strong corner features
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    for (cx, cy) in [(30, 30), (80, 50), (150, 60), (40, 150), (160, 160)]:
        arr[cy-5:cy+5, cx-5:cx+5] = 255
    return Image.fromarray(arr)

def test_by_count_respects_max_and_box_size():
    img = _dotted_image()
    boxes = detect_blobs(img, Opts(blob_mode="count", blob_count=16, bounding_size=20))
    assert 1 <= len(boxes) <= 16
    assert all(b.w == 20 and b.h == 20 for b in boxes)
    assert all(0.0 <= b.conf <= 1.0 for b in boxes)

def test_by_size_returns_contour_boxes():
    img = _dotted_image()
    boxes = detect_blobs(img, Opts(blob_mode="size", min_blob_size=4, blob_count=50))
    assert len(boxes) >= 1
    # contour boxes vary in extent, not all identical fixed size
    assert all(b.w >= 4 and b.h >= 4 for b in boxes)

def test_empty_image_returns_no_boxes():
    blank = Image.new("RGB", (100, 100), (0, 0, 0))
    boxes = detect_blobs(blank, Opts(blob_mode="count", blob_count=32))
    assert boxes == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_blobs.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.blobs`

- [ ] **Step 3: Write minimal implementation**

```python
import cv2
import numpy as np
from babytrack.geometry import Box
from babytrack.options import Opts

def _gray(pil_image):
    arr = np.asarray(pil_image.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)

def _detect_by_count(gray, opts: Opts) -> list[Box]:
    n = max(16, min(512, opts.blob_count))
    pts = cv2.goodFeaturesToTrack(gray, maxCorners=n, qualityLevel=0.01, minDistance=8)
    if pts is None:
        return []
    size = max(4, opts.bounding_size)
    half = size // 2
    boxes = []
    for i, p in enumerate(pts):
        px, py = p.ravel()
        boxes.append(Box(int(px) - half, int(py) - half, size, size, "OBJ", 1.0))
    return boxes

def _detect_by_size(gray, opts: Opts) -> list[Box]:
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w >= opts.min_blob_size and h >= opts.min_blob_size:
            rects.append((w * h, x, y, w, h))
    rects.sort(reverse=True)
    rects = rects[: max(16, min(512, opts.blob_count))]
    if not rects:
        return []
    max_area = rects[0][0] or 1
    return [Box(x, y, w, h, "OBJ", round(area / max_area, 3)) for area, x, y, w, h in rects]

def detect_blobs(pil_image, opts: Opts) -> list[Box]:
    gray = _gray(pil_image)
    if opts.blob_mode == "size":
        return _detect_by_size(gray, opts)
    return _detect_by_count(gray, opts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_blobs.py -v`
Expected: PASS (3 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/blobs.py tests/test_blobs.py
git commit -m "feat: add OpenCV blob detector (by-count and by-size)"
```

---

## Task 6: Renderer registry + HUD renderers

**Files:**
- Create: `babytrack/renderers.py`
- Test: `tests/test_renderers.py`

Each HUD renderer signature: `render(img: PIL.Image, box: Box, opts: Opts) -> None`
(draws in place via `ImageDraw`). Registry maps style name -> function.

- [ ] **Step 1: Write the failing test**

```python
from PIL import Image
from babytrack.geometry import Box
from babytrack.options import Opts, STYLES_HUD
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
    # at least one pixel is no longer black
    assert img.getextrema() != ((0, 0), (0, 0), (0, 0))

def test_basic_draws_rectangle_edge():
    img = _blank()
    apply_style(img, _box(), Opts(style="Basic", color="#ffffff", stroke=2))
    # top-left corner of box should have a non-black pixel near (40,40)
    assert img.getpixel((40, 41)) != (0, 0, 0)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_renderers.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.renderers`

- [ ] **Step 3: Write minimal implementation**

```python
from PIL import ImageDraw, ImageFont
from babytrack.geometry import Box
from babytrack.options import Opts
from babytrack.colors import resolve_color

RENDERERS = {}

def register(name):
    def deco(fn):
        RENDERERS[name] = fn
        return fn
    return deco

def _font(size):
    try:
        return ImageFont.truetype("consola.ttf", size)
    except OSError:
        return ImageFont.load_default()

def _effective_box(box: Box, opts: Opts) -> Box:
    return box.resized(opts.bounding_size) if opts.same_size else box

def _label_text(box: Box, opts: Opts) -> str:
    if opts.label_mode == "custom":
        base = opts.label_custom
    elif opts.label_mode == "random":
        base = box.label.upper()
    else:
        base = box.label.upper()
    if opts.show_score:
        base = f"{base} {box.conf:.2f}"
    return base

def _draw_label(draw, box: Box, opts: Opts, color):
    text = _label_text(box, opts)
    f = _font(opts.font_size)
    if opts.label_pos == "top":
        xy = (box.x, max(0, box.y - opts.font_size - 2))
    elif opts.label_pos == "bottom":
        xy = (box.x, box.y2 + 2)
    else:
        cx, cy = box.center
        xy = (cx - opts.font_size * 2, cy)
    draw.text(xy, text, fill=color, font=f)

@register("Basic")
def _r_basic(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)

@register("Frame")
def _r_frame(img, box, opts):
    _r_basic(img, box, opts)
    draw = ImageDraw.Draw(img)
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    _draw_label(draw, box, opts, c)

@register("Cross")
def _r_cross(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    cx, cy = box.center
    draw.line([box.x, cy, box.x2, cy], fill=c, width=opts.stroke)
    draw.line([cx, box.y, cx, box.y2], fill=c, width=opts.stroke)

@register("Label")
def _r_label(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    _draw_label(ImageDraw.Draw(img), box, opts, c)

def _corner_marks(draw, box, c, stroke, frac=0.25):
    ln = int(min(box.w, box.h) * frac)
    pts = [
        [(box.x, box.y), (box.x + ln, box.y)], [(box.x, box.y), (box.x, box.y + ln)],
        [(box.x2, box.y), (box.x2 - ln, box.y)], [(box.x2, box.y), (box.x2, box.y + ln)],
        [(box.x, box.y2), (box.x + ln, box.y2)], [(box.x, box.y2), (box.x, box.y2 - ln)],
        [(box.x2, box.y2), (box.x2 - ln, box.y2)], [(box.x2, box.y2), (box.x2, box.y2 - ln)],
    ]
    for a, b in pts:
        draw.line([a, b], fill=c, width=stroke)

@register("L-Frame")
def _r_lframe(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    _corner_marks(ImageDraw.Draw(img), box, c, opts.stroke)

@register("X-Frame")
def _r_xframe(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    _corner_marks(draw, box, c, opts.stroke, frac=0.18)
    draw.line([box.x, box.y, box.x2, box.y2], fill=c, width=1)
    draw.line([box.x2, box.y, box.x, box.y2], fill=c, width=1)

@register("Grid")
def _r_grid(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    draw.rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)
    step = max(8, min(box.w, box.h) // 4)
    for gx in range(box.x + step, box.x2, step):
        draw.line([gx, box.y, gx, box.y2], fill=c, width=1)
    for gy in range(box.y + step, box.y2, step):
        draw.line([box.x, gy, box.x2, gy], fill=c, width=1)

@register("Particle")
def _r_particle(img, box, opts):
    import random
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    for _ in range(30):
        px = random.randint(box.x, box.x2)
        py = random.randint(box.y, box.y2)
        draw.ellipse([px, py, px + 2, py + 2], fill=c)

@register("Dash")
def _r_dash(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    dash = 8
    for x in range(box.x, box.x2, dash * 2):
        draw.line([x, box.y, min(x + dash, box.x2), box.y], fill=c, width=opts.stroke)
        draw.line([x, box.y2, min(x + dash, box.x2), box.y2], fill=c, width=opts.stroke)
    for y in range(box.y, box.y2, dash * 2):
        draw.line([box.x, y, box.x, min(y + dash, box.y2)], fill=c, width=opts.stroke)
        draw.line([box.x2, y, box.x2, min(y + dash, box.y2)], fill=c, width=opts.stroke)

@register("Scope")
def _r_scope(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    cx, cy = box.center
    r = min(box.w, box.h) // 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=opts.stroke)
    draw.line([cx - r, cy, cx + r, cy], fill=c, width=1)
    draw.line([cx, cy - r, cx, cy + r], fill=c, width=1)

@register("Win2K")
def _r_win2k(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    draw.rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)
    bar_h = opts.font_size + 4
    draw.rectangle([box.x, box.y, box.x2, box.y + bar_h], fill=c)
    draw.text((box.x + 3, box.y + 2), _label_text(box, opts), fill="#000000", font=_font(opts.font_size))

@register("Label 2")
def _r_label2(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    draw = ImageDraw.Draw(img)
    text = _label_text(box, opts)
    f = _font(opts.font_size)
    tb = draw.textbbox((0, 0), text, font=f)
    w = tb[2] - tb[0] + 8
    h = tb[3] - tb[1] + 6
    draw.rectangle([box.x, box.y - h, box.x + w, box.y], fill=c)
    draw.text((box.x + 4, box.y - h + 2), text, fill="#000000", font=f)
    draw.rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)

@register("Glow")
def _r_glow(img, box, opts):
    from PIL import Image, ImageFilter
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke + 2)
    blurred = layer.filter(ImageFilter.GaussianBlur(4))
    img.paste(blurred, (0, 0), blurred)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)

@register("Backdrop")
def _r_backdrop(img, box, opts):
    from PIL import Image
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    fill = tuple(int(c[i:i+2], 16) for i in (1, 3, 5)) + (80,)
    od.rectangle([box.x, box.y, box.x2, box.y2], fill=fill)
    img.paste(overlay, (0, 0), overlay)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2], outline=c, width=opts.stroke)

def apply_style(img, box: Box, opts: Opts) -> None:
    fn = RENDERERS.get(opts.style)
    if fn is None:
        raise KeyError(f"unknown style {opts.style}")
    fn(img, box, opts)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_renderers.py -v`
Expected: PASS (3 passed). Note: `test_all_hud_styles_registered` passes only after Task 7 if any HUD name is still missing — all 14 HUD names are registered in this task, so it passes now.

- [ ] **Step 5: Commit**

```bash
git add babytrack/renderers.py tests/test_renderers.py
git commit -m "feat: add renderer registry and 14 HUD styles"
```

---

## Task 7: Filter renderers

**Files:**
- Modify: `babytrack/renderers.py`
- Test: `tests/test_renderers.py` (extend)

Each filter renderer crops the box region, transforms pixels, pastes back, then
optionally outlines. Signature identical to HUD renderers.

- [ ] **Step 1: Write the failing test (append to tests/test_renderers.py)**

```python
from babytrack.options import STYLES_FILTER

def test_all_filter_styles_registered():
    for name in STYLES_FILTER:
        assert name in RENDERERS

def test_filter_changes_region_pixels():
    img = Image.new("RGB", (200, 200), (10, 120, 200))
    apply_style(img, Box(40, 40, 80, 80, "car", 0.8), Opts(style="Invert"))
    # inside box should differ from original blue after invert
    assert img.getpixel((80, 80)) != (10, 120, 200)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_renderers.py -k filter -v`
Expected: FAIL — filter styles not registered yet.

- [ ] **Step 3: Add filter implementations to renderers.py**

Add near the top:
```python
import numpy as np
from PIL import ImageOps, ImageFilter
```

Add helper + renderers (append before `apply_style`):
```python
def _region(img, box):
    x = max(0, box.x); y = max(0, box.y)
    x2 = min(img.width, box.x2); y2 = min(img.height, box.y2)
    return (x, y, x2, y2)

def _process_region(img, box, fn):
    bbox = _region(img, box)
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return
    crop = img.crop(bbox)
    img.paste(fn(crop), bbox)

@register("Invert")
def _f_invert(img, box, opts):
    box = _effective_box(box, opts)
    _process_region(img, box, lambda c: ImageOps.invert(c.convert("RGB")))

@register("Inv")
def _f_inv(img, box, opts):
    _f_invert(img, box, opts)
    box = _effective_box(box, opts)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2],
                                  outline=resolve_color(opts, box.label), width=opts.stroke)

@register("Fusion")
def _f_fusion(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    rgb = tuple(int(c[i:i+2], 16) for i in (1, 3, 5))
    def fn(crop):
        from PIL import Image
        tint = Image.new("RGB", crop.size, rgb)
        return Image.blend(crop.convert("RGB"), tint, 0.4)
    _process_region(img, box, fn)

@register("Glitch")
def _f_glitch(img, box, opts):
    box = _effective_box(box, opts)
    def fn(crop):
        from PIL import Image
        r, g, b = crop.convert("RGB").split()
        r = ImageOps.offset(r, 4, 0)
        b = ImageOps.offset(b, -4, 0)
        return Image.merge("RGB", (r, g, b))
    _process_region(img, box, fn)

@register("Thermal")
def _f_thermal(img, box, opts):
    def fn(crop):
        g = crop.convert("L")
        lut = []
        for ch, (a, bb) in zip("rgb", [(0, 255), (0, 100), (255, 0)]):
            lut += [int(a + (bb - a) * i / 255) for i in range(256)]
        return g.convert("RGB").point(lut)
    _process_region(img, box, fn)

@register("Pixel")
def _f_pixel(img, box, opts):
    def fn(crop):
        small = crop.resize((max(1, crop.width // 10), max(1, crop.height // 10)))
        return small.resize(crop.size, 0)  # NEAREST
    _process_region(img, box, fn)

@register("Tone")
def _f_tone(img, box, opts):
    _process_region(img, box, lambda c: ImageOps.posterize(c.convert("RGB"), 2))

@register("Blur")
def _f_blur(img, box, opts):
    _process_region(img, box, lambda c: c.filter(ImageFilter.GaussianBlur(6)))

@register("Dither")
def _f_dither(img, box, opts):
    _process_region(img, box, lambda c: c.convert("1").convert("RGB"))

@register("Zoom")
def _f_zoom(img, box, opts):
    def fn(crop):
        big = crop.resize((int(crop.width * 1.5), int(crop.height * 1.5)))
        left = (big.width - crop.width) // 2
        top = (big.height - crop.height) // 2
        return big.crop((left, top, left + crop.width, top + crop.height))
    _process_region(img, box, fn)

@register("X-Ray")
def _f_xray(img, box, opts):
    def fn(crop):
        inv = ImageOps.invert(crop.convert("RGB"))
        return inv.filter(ImageFilter.EDGE_ENHANCE_MORE)
    _process_region(img, box, fn)

@register("Water")
def _f_water(img, box, opts):
    def fn(crop):
        arr = np.asarray(crop.convert("RGB"))
        h, w = arr.shape[:2]
        out = np.zeros_like(arr)
        for y in range(h):
            shift = int(6 * np.sin(y / 8.0))
            out[y] = np.roll(arr[y], shift, axis=0)
        from PIL import Image
        return Image.fromarray(out)
    _process_region(img, box, fn)

@register("Mask")
def _f_mask(img, box, opts):
    box = _effective_box(box, opts)
    c = resolve_color(opts, box.label)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2], fill=c)

@register("CRT")
def _f_crt(img, box, opts):
    def fn(crop):
        c = crop.convert("RGB").copy()
        d = ImageDraw.Draw(c)
        for y in range(0, c.height, 3):
            d.line([0, y, c.width, y], fill=(0, 0, 0))
        return c
    _process_region(img, box, fn)

@register("Edge")
def _f_edge(img, box, opts):
    _process_region(img, box, lambda c: c.convert("RGB").filter(ImageFilter.FIND_EDGES))

@register("Blink")
def _f_blink(img, box, opts):
    # static photo: render as a bright outline (no animation possible on one frame)
    box = _effective_box(box, opts)
    ImageDraw.Draw(img).rectangle([box.x, box.y, box.x2, box.y2],
                                  outline=resolve_color(opts, box.label), width=opts.stroke + 1)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_renderers.py -v`
Expected: PASS (5 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/renderers.py tests/test_renderers.py
git commit -m "feat: add 16 filter styles"
```

---

## Task 8: Compositor

**Files:**
- Create: `babytrack/compositor.py`
- Test: `tests/test_compositor.py`

- [ ] **Step 1: Write the failing test**

```python
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
    assert list(out.getdata()) == list(original.getdata())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_compositor.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.compositor`

- [ ] **Step 3: Write minimal implementation**

```python
from babytrack.renderers import apply_style
from babytrack.options import Opts

def compose(original, boxes, opts: Opts):
    img = original.convert("RGB").copy()
    for box in boxes:
        apply_style(img, box, opts)
    return img
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_compositor.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/compositor.py tests/test_compositor.py
git commit -m "feat: add compositor"
```

---

## Task 9: PNG export

**Files:**
- Create: `babytrack/export.py`
- Test: `tests/test_export.py`

- [ ] **Step 1: Write the failing test**

```python
from PIL import Image
from babytrack.export import save_png

def test_save_png_writes_file(tmp_path):
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    out = tmp_path / "out.png"
    save_png(img, str(out))
    assert out.exists()
    reopened = Image.open(out)
    assert reopened.format == "PNG"
    assert reopened.size == (10, 10)

def test_save_png_appends_extension(tmp_path):
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    out = tmp_path / "noext"
    path = save_png(img, str(out))
    assert path.endswith(".png")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/Scripts/python -m pytest tests/test_export.py -v`
Expected: FAIL with `ModuleNotFoundError: babytrack.export`

- [ ] **Step 3: Write minimal implementation**

```python
def save_png(image, path: str) -> str:
    if not path.lower().endswith(".png"):
        path = path + ".png"
    image.convert("RGB").save(path, "PNG")
    return path
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv/Scripts/python -m pytest tests/test_export.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add babytrack/export.py tests/test_export.py
git commit -m "feat: add PNG export"
```

---

## Task 10: Tkinter GUI app

**Files:**
- Create: `babytrack/app.py`

GUI is manually tested (no automated UI test). It binds widgets to an `Opts` instance,
loads a photo, runs OpenCV blob detection (cheap, synchronous), and redraws the canvas.
Detection params (blob mode/count/size) re-detect; render params only recompose.

- [ ] **Step 1: Write the app**

```python
import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk

from babytrack.options import Opts, ALL_STYLES, DETECTION_PARAMS
from babytrack.blobs import detect_blobs
from babytrack.compositor import compose
from babytrack.export import save_png

class App:
    def __init__(self, root):
        self.root = root
        root.title("BabyTrack Photo HUD")
        self.opts = Opts()
        self.original = None      # PIL.Image
        self.boxes = []
        self.preview = None       # ImageTk ref

        self._build_layout()

    def _build_layout(self):
        self.canvas = tk.Canvas(self.root, width=720, height=540, bg="#111")
        self.canvas.grid(row=0, column=0, rowspan=24, padx=8, pady=8)

        panel = ttk.Frame(self.root)
        panel.grid(row=0, column=1, sticky="n", padx=8, pady=8)
        r = 0

        ttk.Button(panel, text="Open Photo", command=self.open_photo).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
        ttk.Button(panel, text="Save PNG", command=self.save).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1

        self.status = ttk.Label(panel, text="open a photo to start")
        self.status.grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Label(panel, text="Blob mode").grid(row=r, column=0, sticky="w")
        self.bmode_var = tk.StringVar(value=self.opts.blob_mode)
        cb0 = ttk.Combobox(panel, textvariable=self.bmode_var, values=["count", "size"], state="readonly", width=14)
        cb0.grid(row=r, column=1, sticky="ew"); cb0.bind("<<ComboboxSelected>>", lambda e: self._set("blob_mode", self.bmode_var.get())); r += 1

        r = self._scale(panel, r, "Blob count", "blob_count", 16, 512)
        r = self._scale(panel, r, "Bound size", "bounding_size", 16, 256)
        r = self._scale(panel, r, "Min blob size", "min_blob_size", 4, 128)

        ttk.Label(panel, text="Style").grid(row=r, column=0, sticky="w")
        self.style_var = tk.StringVar(value=self.opts.style)
        cb = ttk.Combobox(panel, textvariable=self.style_var, values=ALL_STYLES, state="readonly", width=14)
        cb.grid(row=r, column=1, sticky="ew"); cb.bind("<<ComboboxSelected>>", lambda e: self._set("style", self.style_var.get())); r += 1

        r = self._scale(panel, r, "Stroke", "stroke", 1, 8)
        r = self._scale(panel, r, "Font size", "font_size", 10, 28)

        self.same_var = tk.BooleanVar(value=self.opts.same_size)
        ttk.Checkbutton(panel, text="Force same size", variable=self.same_var,
                        command=lambda: self._set("same_size", self.same_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        self.score_var = tk.BooleanVar(value=self.opts.show_score)
        ttk.Checkbutton(panel, text="Show score", variable=self.score_var,
                        command=lambda: self._set("show_score", self.score_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Label(panel, text="Color mode").grid(row=r, column=0, sticky="w")
        self.cmode_var = tk.StringVar(value=self.opts.color_mode)
        cb2 = ttk.Combobox(panel, textvariable=self.cmode_var, values=["single", "random", "by-label"], state="readonly", width=14)
        cb2.grid(row=r, column=1, sticky="ew"); cb2.bind("<<ComboboxSelected>>", lambda e: self._set("color_mode", self.cmode_var.get())); r += 1

        ttk.Button(panel, text="Pick color", command=self.pick_color).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1

        ttk.Label(panel, text="Label mode").grid(row=r, column=0, sticky="w")
        self.lmode_var = tk.StringVar(value=self.opts.label_mode)
        cb3 = ttk.Combobox(panel, textvariable=self.lmode_var, values=["generic", "random", "custom"], state="readonly", width=14)
        cb3.grid(row=r, column=1, sticky="ew"); cb3.bind("<<ComboboxSelected>>", lambda e: self._set("label_mode", self.lmode_var.get())); r += 1

        ttk.Label(panel, text="Custom label").grid(row=r, column=0, sticky="w")
        self.lcustom_var = tk.StringVar(value=self.opts.label_custom)
        e = ttk.Entry(panel, textvariable=self.lcustom_var, width=16)
        e.grid(row=r, column=1, sticky="ew"); e.bind("<KeyRelease>", lambda ev: self._set("label_custom", self.lcustom_var.get())); r += 1

        ttk.Label(panel, text="Label pos").grid(row=r, column=0, sticky="w")
        self.lpos_var = tk.StringVar(value=self.opts.label_pos)
        cb4 = ttk.Combobox(panel, textvariable=self.lpos_var, values=["center", "top", "bottom"], state="readonly", width=14)
        cb4.grid(row=r, column=1, sticky="ew"); cb4.bind("<<ComboboxSelected>>", lambda e: self._set("label_pos", self.lpos_var.get())); r += 1

    def _scale(self, panel, r, text, attr, lo, hi):
        ttk.Label(panel, text=text).grid(row=r, column=0, sticky="w")
        s = ttk.Scale(panel, from_=lo, to=hi, command=lambda v, a=attr: self._set(a, int(float(v))))
        s.set(getattr(self.opts, attr))
        s.grid(row=r, column=1, sticky="ew")
        return r + 1

    def _set(self, attr, value):
        setattr(self.opts, attr, value)
        if attr in DETECTION_PARAMS:
            self.detect()
        else:
            self.redraw()

    def open_photo(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if not path:
            return
        try:
            self.original = Image.open(path).convert("RGB")
        except Exception as ex:
            messagebox.showwarning("Bad file", f"Not an image: {ex}")
            return
        self.detect()

    def detect(self):
        if self.original is None:
            return
        try:
            self.boxes = detect_blobs(self.original, self.opts)
        except Exception as ex:
            self.status.config(text=f"detect error: {ex}")
            return
        if self.boxes:
            self.status.config(text=f"{len(self.boxes)} blob(s)")
        else:
            self.status.config(text="no blobs — lower min size / raise count")
        self.redraw()

    def redraw(self):
        if self.original is None:
            return
        composed = compose(self.original, self.boxes, self.opts)
        disp = composed.copy()
        disp.thumbnail((720, 540))
        self.preview = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(360, 270, image=self.preview)

    def pick_color(self):
        c = colorchooser.askcolor(color=self.opts.color)
        if c and c[1]:
            self.opts.color = c[1]
            self.opts.color_mode = "single"
            self.cmode_var.set("single")
            self.redraw()

    def save(self):
        if self.original is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        composed = compose(self.original, self.boxes, self.opts)
        save_png(composed, path)
        self.status.config(text=f"saved {path}")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
```

- [ ] **Step 2: Manual smoke test — launch app**

Run: `.venv/Scripts/python main.py`
Expected: window opens with a dark canvas and a settings panel. No crash.

- [ ] **Step 3: Manual test — detect + blob count + style switching**

1. Click "Open Photo", choose any detailed JPG.
2. Status shows "N blob(s)"; many tracking boxes scatter across features.
3. Drag "Blob count" up/down — number of boxes changes (16–512).
4. Switch "Blob mode" Count↔Size — placement/sizing changes.
5. Change Style through several values — overlay updates each time (no re-detect).
6. Change Stroke/Color — overlay updates.
7. Click "Save PNG", choose a path → file is written and opens correctly.

- [ ] **Step 4: Commit**

```bash
git add babytrack/app.py
git commit -m "feat: add Tkinter GUI app"
```

---

## Task 11: Full test run + README

**Files:**
- Create: `README.md`

- [ ] **Step 1: Run the whole test suite**

Run: `.venv/Scripts/python -m pytest -v`
Expected: all tests pass.

- [ ] **Step 2: Write README**

```markdown
# BabyTrack Photo HUD

Tkinter desktop app: load one photo, find many visual blobs with OpenCV
(feature/contour regions, count 16–512), overlay configurable tracking
HUD/filter effects (30 styles), save as PNG. No YOLO, no model download.

## Setup
    python -m venv .venv
    .venv/Scripts/python -m pip install -r requirements.txt

## Run
    .venv/Scripts/python main.py

## Test
    .venv/Scripts/python -m pytest -v

Pure CPU OpenCV — runs instantly, GPU unused.
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: add README"
```

---

## Self-Review Notes

- **Spec coverage:** loader (Task 10 open_photo), blob detector by-count & by-size (Task 5), blob-count control (Task 10 scale + DETECTION_PARAMS re-detect), all 30 styles (Tasks 6–7), settings panel (Task 10), compositor (Task 8), exporter (Task 9), error handling (Task 10 messagebox + status). All covered.
- **Type consistency:** `Box(x,y,w,h,label,conf)`, `detect_blobs(pil_image, opts)`, `apply_style(img, box, opts)`, `compose(original, boxes, opts)`, `save_png(image, path)`, `resolve_color(opts, label)`, `DETECTION_PARAMS` used consistently across tasks.
- **Out of scope honored:** no video/camera/mp4/audio/PRO/YOLO.
```
