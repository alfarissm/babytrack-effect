# BabyTrack Photo HUD — Design Spec

Date: 2026-06-16
Status: Draft (awaiting user review)

## Goal

A Python desktop app (Tkinter) that takes a **single static photo**, runs AI object
detection on it, and overlays BabyTrack-style "tracking HUD" graphics on each detected
object. Styles and parameters are configurable through a settings panel that mirrors the
artkit.cc/baby-track website. The composited image can be viewed on screen and saved as PNG.

This is a visual experiment, not a product. No video, no camera, no export to MP4/WebM,
no audio, no PRO/cloud features.

## Stack

- **Language:** Python 3.13 (verified present, tkinter present)
- **GUI:** Tkinter (stdlib)
- **Detection:** Ultralytics YOLO (`yolov8n.pt`, auto-downloaded ~6MB)
- **Image:** Pillow (PIL) for load, draw, filters, save; NumPy for pixel-level filters
- **Single file:** `babytrack.py`

Dependencies: `pip install ultralytics pillow numpy` (ultralytics pulls in torch).

## Data Flow

```
File dialog -> PIL.Image (keep pristine original copy)
   -> YOLO(img) -> detections: list of {x, y, w, h, label, conf}   (run once per photo, in a thread)
   -> Compositor redraw on any setting change:
        base = copy of original
        for each detection: apply active style via renderer(draw/img, box, opts)
   -> show on Tkinter Canvas (ImageTk.PhotoImage)
   -> Save PNG via save dialog
```

## Components (functions/classes in one file)

1. **Loader** — open file dialog, load into `PIL.Image`, store pristine `original`. Reject
   non-image files with a warning.
2. **Detector** — load YOLO model lazily; `detect(image)` returns the detection list. Runs on
   a background thread so the UI does not freeze; status label shows "loading YOLO…" /
   "detecting…". Detections cached until a new photo is loaded.
3. **Renderers** — one function per style, signature `render(base_img, draw, box, opts)`.
   - **Outline/HUD group** draw on an `ImageDraw.Draw` over the base.
   - **Filter group** operate on the pixel region inside the box (crop → transform → paste).
4. **Settings panel** — Tkinter widgets bound to an `opts` dict; any change triggers redraw.
5. **Compositor** — rebuild image from pristine original + all detections × active style.
6. **Exporter** — `image.save(path)` as PNG via `asksaveasfilename`.

## Styles (mirror website — all of them)

**Basic / HUD (14):** Basic, Cross, Label, Frame, L-Frame, X-Frame, Grid, Particle, Dash,
Scope, Win2K, Label 2, Glow, Backdrop

**Filter (16):** Invert, Fusion, Inv, Glitch, Thermal, Pixel, Tone, Blur, Dither, Zoom,
X-Ray, Water, Mask, CRT, Edge, Blink

Implementation notes for filters (operate on cropped box region):
- Invert/Inv: `ImageOps.invert`
- Thermal: grayscale → apply warm colormap (LUT/palette)
- Pixel: downscale then nearest-upscale
- Glitch: per-channel horizontal offset
- Tone: posterize / duotone
- Blur: `GaussianBlur`
- Dither: convert mode "1" (Floyd–Steinberg)
- Zoom: scale region content up, clip to box
- X-Ray: invert + edge-enhance
- Water: sine displacement via NumPy (approximate)
- Mask: solid fill
- CRT: horizontal scanlines + slight RGB split
- Edge: `FIND_EDGES`
- Blink: on a static photo = outline on/off toggle (no animation)

Note: "Blink"/animated effects are static here since input is one photo. Documented, not animated.

## Settings (panel controls)

- **Style** — Combobox (all 30 names)
- **Stroke width** — Scale (1–8 px)
- **Bounding size** — Same Size (fixed, e.g. 32–512) or follow detection box
- **Color mode** — single (colorchooser) / random / by-label
- **Label mode** — Random / real YOLO label / custom Entry
- **Label position** — center / top / bottom
- **Font size** — 10/12/16/18/20
- **Show score** — Checkbutton (append conf like `0.98`)

## Error Handling

- 0 detections → status "no objects detected, try another photo"; show plain photo.
- YOLO load/detect failure → status with the error message; app stays usable for reload.
- Non-image file → warning dialog.

## Out of Scope (YAGNI)

Video, webcam, MP4/WebM export, audio-reactive, connection/center-hub mode, multi-photo
batch, any PRO/cloud feature.

## Success Criteria

1. Load a JPG/PNG → YOLO detects objects → boxes appear.
2. Changing any setting redraws the overlay correctly without reloading the photo.
3. All 30 styles render without crashing (visual fidelity approximate to website).
4. Save produces a PNG matching the on-screen composite.
5. UI never hard-freezes during detection (threaded).
