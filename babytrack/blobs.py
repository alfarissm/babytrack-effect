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
    for p in pts:
        px, py = p.ravel()
        boxes.append(Box(int(px) - half, int(py) - half, size, size, "OBJ", 1.0))
    return boxes

def _detect_by_size(gray, opts: Opts) -> list[Box]:
    H, W = gray.shape[:2]
    max_w = W * max(1, min(100, opts.max_blob_pct)) / 100.0
    max_h = H * max(1, min(100, opts.max_blob_pct)) / 100.0
    edges = cv2.Canny(gray, 50, 150)
    edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    rects = []
    for c in contours:
        x, y, w, h = cv2.boundingRect(c)
        if w >= opts.min_blob_size and h >= opts.min_blob_size and w <= max_w and h <= max_h:
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
