from babytrack.renderers import apply_style
from babytrack.connections import draw_connections
from babytrack.region_fx import apply_region_fx
from babytrack.options import Opts

def compose(original, boxes, opts: Opts):
    img = original.convert("RGB").copy()
    draw_connections(img, boxes, opts)      # under everything
    for box in boxes:
        apply_region_fx(img, box, opts)     # in-box effect, under the outline
    for box in boxes:
        apply_style(img, box, opts)         # outline/HUD style on top
    return img
