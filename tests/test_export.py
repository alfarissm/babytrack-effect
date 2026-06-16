from PIL import Image
from babytrack.export import save_png

def test_save_png_writes_file(tmp_path):
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    out = tmp_path / "out.png"
    save_png(img, str(out))
    assert out.exists()
    reopened = Image.open(out)
    assert reopened.format == "PNG"
    assert reopened.size == (10, 10)

def test_save_png_appends_extension(tmp_path):
    img = Image.new("RGB", (10, 10), (1, 2, 3))
    out = tmp_path / "noext"
    path = save_png(img, str(out))
    assert path.endswith(".png")
