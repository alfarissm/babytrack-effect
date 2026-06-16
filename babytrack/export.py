def save_png(image, path: str) -> str:
    if not path.lower().endswith(".png"):
        path = path + ".png"
    image.convert("RGB").save(path, "PNG")
    return path
