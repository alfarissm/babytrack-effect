from PIL import Image, ImageOps, ImageEnhance, ImageDraw
from babytrack.renderers import _resolve_shape, _shape_mask

REGION_FX = {}

def register(name):
    def deco(fn):
        REGION_FX[name] = fn
        return fn
    return deco

def _rgb(hexc):
    return tuple(int(hexc[i:i+2], 16) for i in (1, 3, 5))

def _region(img, box):
    x = max(0, box.x); y = max(0, box.y)
    x2 = min(img.width, box.x2); y2 = min(img.height, box.y2)
    return (x, y, x2, y2)

def _paste_shaped(img, box, bbox, processed, opts):
    shape = _resolve_shape(opts, box)
    if shape == "rect":
        img.paste(processed, bbox)
    else:
        img.paste(processed, bbox, _shape_mask(processed.size, box, bbox, shape))

def _process(img, box, fn, opts):
    bbox = _region(img, box)
    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return
    crop = img.crop(bbox).convert("RGB")
    _paste_shaped(img, box, bbox, fn(crop), opts)

@register("invert")
def _invert(img, box, opts):
    _process(img, box, lambda c: ImageOps.invert(c), opts)

@register("darken")
def _darken(img, box, opts):
    _process(img, box, lambda c: ImageEnhance.Brightness(c).enhance(0.4), opts)

@register("brighten")
def _brighten(img, box, opts):
    _process(img, box, lambda c: ImageEnhance.Brightness(c).enhance(1.7), opts)

@register("tint")
def _tint(img, box, opts):
    rgb = _rgb(opts.color)
    def fn(c):
        tint = Image.new("RGB", c.size, rgb)
        return Image.blend(c, tint, 0.5)
    _process(img, box, fn, opts)

@register("pixelate")
def _pixelate(img, box, opts):
    def fn(c):
        small = c.resize((max(1, c.width // 12), max(1, c.height // 12)))
        return small.resize(c.size, Image.NEAREST)
    _process(img, box, fn, opts)

@register("scanline")
def _scanline(img, box, opts):
    def fn(c):
        out = c.copy()
        d = ImageDraw.Draw(out)
        for y in range(0, out.height, 3):
            d.line([0, y, out.width, y], fill=(0, 0, 0))
        return out
    _process(img, box, fn, opts)

@register("gradient")
def _gradient(img, box, opts):
    # vertical gradient of opts.color, opaque at top -> transparent at bottom, over the region
    bbox = _region(img, box)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    if w <= 0 or h <= 0:
        return
    rgb = _rgb(opts.color)
    grad = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = grad.load()
    for yy in range(h):
        a = int(180 * (1 - yy / max(1, h - 1)))
        for xx in range(w):
            px[xx, yy] = (rgb[0], rgb[1], rgb[2], a)
    base = img.crop(bbox).convert("RGBA")
    base.alpha_composite(grad)
    _paste_shaped(img, box, bbox, base.convert("RGB"), opts)

def apply_region_fx(img, box, opts) -> None:
    fn = REGION_FX.get(opts.region_fill)
    if fn is None:   # "none" or unknown
        return
    fn(img, box, opts)
