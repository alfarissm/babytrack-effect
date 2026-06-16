from babytrack.geometry import Box

def test_box_corners_and_center():
    b = Box(x=10, y=20, w=100, h=50, label="person", conf=0.97)
    assert b.x2 == 110
    assert b.y2 == 70
    assert b.center == (60, 45)

def test_box_resized_keeps_center():
    b = Box(x=0, y=0, w=100, h=100, label="cat", conf=0.5)
    r = b.resized(50)  # force 50x50 box, same center
    assert (r.w, r.h) == (50, 50)
    assert r.center == b.center
