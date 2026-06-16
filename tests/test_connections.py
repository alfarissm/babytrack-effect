from PIL import Image
from babytrack.geometry import Box
from babytrack.options import Opts
from babytrack.connections import draw_connections

def _boxes():
    return [
        Box(10, 10, 20, 20, "OBJ", 1.0),
        Box(100, 20, 20, 20, "OBJ", 1.0),
        Box(60, 120, 20, 20, "OBJ", 1.0),
        Box(150, 150, 20, 20, "OBJ", 1.0),
    ]

def _blank():
    return Image.new("RGB", (200, 200), (0, 0, 0))

def test_hub_draws_lines():
    img = _blank()
    draw_connections(img, _boxes(), Opts(connect=True, connect_mode="hub", color="#ffffff"))
    assert img.getextrema() != ((0, 0), (0, 0), (0, 0))

def test_nearest_draws_lines():
    img = _blank()
    draw_connections(img, _boxes(), Opts(connect=True, connect_mode="nearest", color="#ffffff"))
    assert img.getextrema() != ((0, 0), (0, 0), (0, 0))

def test_mesh_draws_more_than_hub():
    hub = _blank()
    mesh = _blank()
    draw_connections(hub, _boxes(), Opts(connect=True, connect_mode="hub", color="#ffffff"))
    draw_connections(mesh, _boxes(), Opts(connect=True, connect_mode="mesh", color="#ffffff"))
    lit = lambda im: sum(1 for b in im.tobytes() if b)
    assert lit(mesh) > lit(hub)

def test_fewer_than_two_boxes_no_crash():
    img = _blank()
    draw_connections(img, [Box(5, 5, 10, 10, "OBJ", 1.0)], Opts(connect=True, connect_mode="mesh"))
    draw_connections(img, [], Opts(connect=True, connect_mode="hub"))
    assert img.getextrema() == ((0, 0), (0, 0), (0, 0))
