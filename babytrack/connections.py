from PIL import ImageDraw
from babytrack.colors import resolve_color

def _centers(boxes):
    return [b.center for b in boxes]

def draw_connections(img, boxes, opts) -> None:
    if not opts.connect or len(boxes) < 2:
        return
    draw = ImageDraw.Draw(img)
    c = resolve_color(opts, "LINE")
    w = opts.stroke
    pts = _centers(boxes)

    if opts.connect_mode == "hub":
        hx = sum(p[0] for p in pts) // len(pts)
        hy = sum(p[1] for p in pts) // len(pts)
        for p in pts:
            draw.line([p, (hx, hy)], fill=c, width=w)
        return

    if opts.connect_mode == "mesh":
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                draw.line([pts[i], pts[j]], fill=c, width=w)
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
            draw.line([a, best], fill=c, width=w)
