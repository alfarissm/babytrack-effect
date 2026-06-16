# BabyTrack Photo HUD

Tkinter desktop app: load one photo, find many visual blobs with OpenCV
(feature/contour regions, count 16–512), overlay configurable tracking
HUD/filter effects (30 styles), save as PNG. No YOLO, no model download.

Clone of the artkit.cc BabyTrack effect for a single static photo. The look is
"random but specific": many tracking boxes lock onto real image features, not
semantic objects.

## Setup

    python -m venv .venv
    .venv/Scripts/python -m pip install -r requirements.txt

## Run

    .venv/Scripts/python main.py

1. **Open Photo** — pick any detailed JPG/PNG.
2. Tracking boxes scatter across detected blobs.
3. **Blob mode** (count/size) and **Blob count** (16–512) control detection.
4. **Style** picks one of 30 HUD/filter overlays; stroke, color, label, font are configurable.
5. **Save PNG** writes the composite.

## Styles

- **HUD (14):** Basic, Cross, Label, Frame, L-Frame, X-Frame, Grid, Particle, Dash, Scope, Win2K, Label 2, Glow, Backdrop
- **Filter (16):** Invert, Fusion, Inv, Glitch, Thermal, Pixel, Tone, Blur, Dither, Zoom, X-Ray, Water, Mask, CRT, Edge, Blink

## Test

    .venv/Scripts/python -m pytest -v

Pure CPU OpenCV — runs instantly, GPU unused.
