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
