import numpy as np
from PIL import Image
from babytrack.blobs import detect_blobs
from babytrack.options import Opts

def _dotted_image():
    # black image with several bright squares => strong corner features
    arr = np.zeros((200, 200, 3), dtype=np.uint8)
    for (cx, cy) in [(30, 30), (80, 50), (150, 60), (40, 150), (160, 160)]:
        arr[cy-5:cy+5, cx-5:cx+5] = 255
    return Image.fromarray(arr)

def test_by_count_respects_max_and_box_size():
    img = _dotted_image()
    boxes = detect_blobs(img, Opts(blob_mode="count", blob_count=16, bounding_size=20))
    assert 1 <= len(boxes) <= 16
    assert all(b.w == 20 and b.h == 20 for b in boxes)
    assert all(0.0 <= b.conf <= 1.0 for b in boxes)

def test_by_size_returns_contour_boxes():
    img = _dotted_image()
    boxes = detect_blobs(img, Opts(blob_mode="size", min_blob_size=4, blob_count=50))
    assert len(boxes) >= 1
    # contour boxes vary in extent, not all identical fixed size
    assert all(b.w >= 4 and b.h >= 4 for b in boxes)

def test_empty_image_returns_no_boxes():
    blank = Image.new("RGB", (100, 100), (0, 0, 0))
    boxes = detect_blobs(blank, Opts(blob_mode="count", blob_count=32))
    assert boxes == []
