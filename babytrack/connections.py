from PIL import ImageDraw
from babytrack.colors import resolve_color

def _centers(boxes):
    return [b.center for b in boxes]

def _segment(draw, a, b, color, width, curve):
    if not curve:
        draw.line([a, b], fill=color, width=width)
        return
    # quadratic bezier: control point offset perpendicular to the midpoint
    mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2
    dx, dy = b[0] - a[0], b[1] - a[1]
    cx, cy = mx - dy * 0.25, my + dx * 0.25
    pts = []
    steps = 18
    for i in range(steps + 1):
        t = i / steps
        u = 1 - t
        x = u * u * a[0] + 2 * u * t * cx + t * t * b[0]
        y = u * u * a[1] + 2 * u * t * cy + t * t * b[1]
        pts.append((x, y))
    draw.line(pts, fill=color, width=width, joint="curve")

def draw_connections(img, boxes, opts) -> None:
    if not opts.connect or len(boxes) < 2:
        return
    draw = ImageDraw.Draw(img)
    c = resolve_color(opts, "LINE")
    w = opts.stroke
    curve = getattr(opts, "connect_curve", False)
    pts = _centers(boxes)

    if opts.connect_mode == "hub":
        hx = sum(p[0] for p in pts) // len(pts)
        hy = sum(p[1] for p in pts) // len(pts)
        for p in pts:
            _segment(draw, p, (hx, hy), c, w, curve)
        return

    if opts.connect_mode == "mesh":
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                _segment(draw, pts[i], pts[j], c, w, curve)
        return

    # nearest: connect each point to its closest other point
    for i, a in enumerate(pts):
        best = None
        best_d = None
        for j, b in enumerate(pts):
            if i == j:
                continue
            d = (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if best_d is None or d < best_d:
                best_d, best = d, b
        if best is not None:
            _segment(draw, a, best, c, w, curve)
