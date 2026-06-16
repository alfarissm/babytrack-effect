import numpy as np
from PIL import ImageDraw, ImageFont, ImageOps, ImageFilter, ImageChops
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

_SHAPE_CHOICES = ["rect", "ellipse", "diamond", "hexagon", "triangle"]

def _resolve_shape(opts: Opts, box: Box) -> str:
    shape = getattr(opts, "box_shape", "rect")
    if shape == "random":
        pool = [s for s in getattr(opts, "random_shapes", None) or _SHAPE_CHOICES if s in _SHAPE_CHOICES]
        if not pool:
            pool = _SHAPE_CHOICES
        # deterministic per box position so redraws stay stable
        return pool[(box.x * 31 + box.y * 17 + box.w) % len(pool)]
    return shape

def _poly_points(box: Box, shape: str):
    cx, cy = box.center
    if shape == "diamond":
        return [(cx, box.y), (box.x2, cy), (cx, box.y2), (box.x, cy)]
    if shape == "triangle":
        return [(cx, box.y), (box.x2, box.y2), (box.x, box.y2)]
    if shape == "hexagon":
        qx = box.w // 4
        return [(box.x + qx, box.y), (box.x2 - qx, box.y), (box.x2, cy),
                (box.x2 - qx, box.y2), (box.x + qx, box.y2), (box.x, cy)]
    return [(box.x, box.y), (box.x2, box.y), (box.x2, box.y2), (box.x, box.y2)]

def _shape_outline(draw, box: Box, opts: Opts, color, width):
    shape = _resolve_shape(opts, box)
    if shape == "rect":
        draw.rectangle([box.x, box.y, box.x2, box.y2], outline=color, width=width)
    elif shape == "ellipse":
        draw.ellipse([box.x, box.y, box.x2, box.y2], outline=color, width=width)
    else:
        draw.polygon(_poly_points(box, shape), outline=color, width=width)

def _shape_fill(draw, box: Box, opts: Opts, color):
    shape = _resolve_shape(opts, box)
    if shape == "rect":
        draw.rectangle([box.x, box.y, box.x2, box.y2], fill=color)
    elif shape == "ellipse":
        draw.ellipse([box.x, box.y, box.x2, box.y2], fill=color)
    else:
        draw.polygon(_poly_points(box, shape), fill=color)

def _label_text(box: Box, opts: Opts) -> str:
    if opts.label_mode == "custom":
        base = opts.label_custom
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
    _shape_outline(ImageDraw.Draw(img), box, opts, c, opts.stroke)

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
    _shape_outline(draw, box, opts, c, opts.stroke)
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
    _shape_outline(draw, box, opts, c, opts.stroke)
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
    _shape_outline(draw, box, opts, c, opts.stroke)

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
    _shape_outline(ImageDraw.Draw(img), box, opts, c, opts.stroke)

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
    _shape_outline(ImageDraw.Draw(img), box, opts, resolve_color(opts, box.label), opts.stroke)

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
        r = ImageChops.offset(r, 4, 0)
        b = ImageChops.offset(b, -4, 0)
        return Image.merge("RGB", (r, g, b))
    _process_region(img, box, fn)

@register("Thermal")
def _f_thermal(img, box, opts):
    def fn(crop):
        g = crop.convert("L")
        lut = []
        for a, bb in [(0, 255), (0, 100), (255, 0)]:
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
    _shape_fill(ImageDraw.Draw(img), box, opts, c)

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
    _shape_outline(ImageDraw.Draw(img), box, opts, resolve_color(opts, box.label), opts.stroke + 1)

def apply_style(img, box: Box, opts: Opts) -> None:
    fn = RENDERERS.get(opts.style)
    if fn is None:
        raise KeyError(f"unknown style {opts.style}")
    fn(img, box, opts)
