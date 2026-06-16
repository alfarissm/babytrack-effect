from babytrack.renderers import apply_style
from babytrack.options import Opts

def compose(original, boxes, opts: Opts):
    img = original.convert("RGB").copy()
    for box in boxes:
        apply_style(img, box, opts)
    return img
