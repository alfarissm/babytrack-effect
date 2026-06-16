# BabyTrack Photo HUD — Design Spec

Date: 2026-06-16
Status: Draft (awaiting user review) — rev 2 (blob detection)

## Goal

A Python desktop app (Tkinter) that takes a **single static photo**, finds many visual
"blobs" (feature/contrast regions) in it, and overlays BabyTrack-style tracking HUD/filter
graphics on each blob. The number of boxes is user-controlled (16–512), so the result has
the signature BabyTrack "random-but-specific" scatter of tracking boxes. Styles and
parameters are configurable through a settings panel. The
composited image can be viewed on screen and saved as PNG.

This is a visual experiment, not a product. No video, no camera, no MP4/WebM export, no
audio, no PRO/cloud features.

## Key decision: blob detection, NOT object detection

The real BabyTrack does not classify objects ("person", "car"). Its controls expose
**Blob Count (By Size / By Count, 16–512)** and **Bounding Size** — it locks many tracking
boxes onto visual features, not semantic objects. We mirror that with OpenCV. This is why
the look is "random but specific": boxes attach to real image features (edges, corners,
contrast), and there are many of them. No model training, no dataset, no class list.

## Stack

- **Language:** Python 3.13 (verified present, tkinter present)
- **GUI:** Tkinter (stdlib)
- **Detection:** OpenCV (`opencv-python`) — pure CV, CPU, no model download
- **Image:** Pillow (PIL) for draw/filters/save; NumPy for pixel-level filters
- **Modules:** small package under `babytrack/` (see plan), not one file

Dependencies: `pip install opencv-python pillow numpy pytest`. No torch, no YOLO.

### Hardware

Target machine: RTX 3050 (4GB VRAM), 16GB RAM. Irrelevant now — detection is pure CPU
OpenCV, runs in well under 100ms per photo. GPU unused. Install footprint is small
(opencv-python ~40MB) vs the previous ~2.5GB torch build.

## Blob detection (two modes, mirror the website)

Input: the loaded photo as a grayscale OpenCV array.

- **By Count** (`blob_mode = "count"`): `cv2.goodFeaturesToTrack(gray, maxCorners=N, qualityLevel, minDistance)`
  returns up to N strongest feature points (N = `blob_count`, 16–512). Each point becomes a
  box of side `bounding_size` centered on it. Feature strength → `conf`. This is the primary
  "many scattered boxes" look.
- **By Size** (`blob_mode = "size"`): Canny edges → `cv2.findContours` → bounding rect per
  contour, filtered by `min_blob_size`. Boxes follow real blob extents. Sorted largest-first,
  capped at `blob_count`.

Both return `list[Box]` with a generic label (default `"OBJ"`, or an index) and `conf` in 0..1.

## Data Flow

```
File dialog -> PIL.Image (keep pristine original)
   -> detect_blobs(original, opts) -> list[Box]   (re-run when a DETECTION param changes)
   -> compose(original, boxes, opts):
        base = copy of original
        for each box: apply active style via renderer(img, box, opts)
   -> show on Tkinter Canvas (ImageTk.PhotoImage)
   -> Save PNG via save dialog
```

**Detection params** (changing them re-runs detect_blobs): blob_mode, blob_count,
bounding_size, min_blob_size.
**Render params** (changing them only re-composes): style, stroke, color*, label*, font_size,
show_score. Detection is fast enough that re-running on every change is also acceptable; the
app re-detects only when a detection param changes to avoid box positions jumping unnecessarily.

## Components

1. **Loader** (`app.py`) — file dialog → `PIL.Image` (RGB), store pristine `original`;
   reject non-image with a warning.
2. **Blob detector** (`blobs.py`) — `detect_blobs(pil_image, opts) -> list[Box]`, two modes
   above. Pure function; cheap; no threading required but the call is wrapped so the UI stays
   responsive.
3. **Renderers** (`renderers.py`) — one function per style, `render(img, box, opts)`, kept in
   a name→function registry. HUD group draws outlines/labels; filter group transforms the
   pixel region inside the box.
4. **Settings panel** (`app.py`) — Tkinter widgets bound to an `Opts` dataclass; detection
   params re-detect+recompose, render params recompose.
5. **Compositor** (`compositor.py`) — `compose(original, boxes, opts)` returns a new image.
6. **Exporter** (`export.py`) — `save_png(image, path)`.

## Styles (mirror website — all of them)

**Basic / HUD (14):** Basic, Cross, Label, Frame, L-Frame, X-Frame, Grid, Particle, Dash,
Scope, Win2K, Label 2, Glow, Backdrop

**Filter (16):** Invert, Fusion, Inv, Glitch, Thermal, Pixel, Tone, Blur, Dither, Zoom,
X-Ray, Water, Mask, CRT, Edge, Blink

Filter notes (operate on cropped box region): Invert/Inv `ImageOps.invert`; Thermal grayscale
→ warm LUT; Pixel downscale+nearest-upscale; Glitch per-channel offset; Tone posterize; Blur
GaussianBlur; Dither mode "1"; Zoom scale region; X-Ray invert+edge-enhance; Water sine
displacement (NumPy); Mask solid fill; CRT scanlines; Edge FIND_EDGES; Blink bright outline
(static — one frame, no animation).

## Settings (panel controls)

- **Style** — Combobox (all 30 names)
- **Blob mode** — Combobox: By Count / By Size
- **Blob count** — Scale 16–512
- **Bounding size** — Scale 16–256 (box side in By Count; min size filter influence)
- **Min blob size** — Scale 4–128 (By Size filter)
- **Stroke width** — Scale 1–8 px
- **Color mode** — single (colorchooser) / random / by-label
- **Label mode** — generic ("OBJ"+index) / random / custom Entry
- **Label position** — center / top / bottom
- **Font size** — Scale 10–28
- **Show score** — Checkbutton (append conf like `0.98`)

## Error Handling

- 0 blobs found → status "no blobs found, lower min size / raise count"; show plain photo.
- Non-image file → warning dialog.
- Blob count clamped to 16–512.

## Out of Scope (YAGNI)

Video, webcam, MP4/WebM export, audio-reactive, connection/center-hub mode, multi-photo
batch, semantic object detection / YOLO, any PRO/cloud feature.

## Success Criteria

1. Load a JPG/PNG → blobs detected → many tracking boxes appear (scatter look).
2. Blob count slider changes the number of boxes (16–512).
3. Switching blob mode (Count/Size) changes box placement/sizing accordingly.
4. Changing a render setting updates the overlay without re-detecting.
5. All 30 styles render without crashing (approximate to website).
6. Save produces a PNG matching the on-screen composite.
