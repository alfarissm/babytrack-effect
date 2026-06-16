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
    max_blob_pct: int = 50           # By Size: drop boxes wider/taller than this % of image
    # render params (changing these only re-composes)
    style: str = "Frame"
    box_shape: str = "rect"          # rect | ellipse | diamond | hexagon | triangle | random
    stroke: int = 2
    same_size: bool = False          # False: keep detection box size. True: force bounding_size
    color_mode: str = "single"       # single | random | by-label
    color: str = "#00ff66"           # used when color_mode == single
    label_mode: str = "generic"      # generic | random | custom
    label_custom: str = "TARGET"
    label_pos: str = "top"           # center | top | bottom
    font_size: int = 14
    show_score: bool = True
    # connection lines between blobs (drawn under the per-box style)
    connect: bool = False
    connect_mode: str = "hub"        # hub | nearest | mesh
    connect_curve: bool = False      # curved (bezier) instead of straight
    # in-box region effect, applied under the outline style (independent of style)
    region_fill: str = "none"        # see REGION_FX names in region_fx.py

DETECTION_PARAMS = {"blob_mode", "blob_count", "bounding_size", "min_blob_size", "max_blob_pct"}

REGION_FILLS = ["none", "gradient", "invert", "darken", "brighten", "tint", "pixelate", "scanline"]

BOX_SHAPES = ["rect", "ellipse", "diamond", "hexagon", "triangle", "random"]
