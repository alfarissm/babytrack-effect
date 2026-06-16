from babytrack.renderers import apply_style
from babytrack.connections import draw_connections
from babytrack.options import Opts

def compose(original, boxes, opts: Opts):
    img = original.convert("RGB").copy()
    draw_connections(img, boxes, opts)  # under the per-box styles
    for box in boxes:
        apply_style(img, box, opts)
    return img
