# BabyTrack Effect — project guide

Personal desktop app: load one photo, detect many visual blobs (OpenCV), overlay tracking
HUD/filter effects, export PNG. Classical computer vision, NOT AI. Public docs stay
personal — no third-party/company references.

## Run / test (Windows)

Always use the venv Python (system Python lacks opencv/pillow-heif):

```
.venv\Scripts\python.exe main.py          # launch GUI
.venv\Scripts\python.exe -m pytest         # 68 tests
```

Note: run pytest/git via PowerShell here — the Git Bash tool hits a cygwin `fork`
resource error intermittently on this machine.

## Architecture

```
babytrack/
  geometry.py     Box dataclass (x,y,w,h,label,conf; .x2 .y2 .center .resized)
  options.py      Opts dataclass + ALL_STYLES, REGION_FILLS, BOX_SHAPES, DETECTION_PARAMS
  blobs.py        detect_blobs(img, opts) -> list[Box]; modes: count (goodFeaturesToTrack), size (Canny+contours)
  colors.py       resolve_color(opts, label): single | random | by-label
  renderers.py    RENDERERS registry; apply_style(img, box, opts); 30 styles; box-shape helpers; region masking
  connections.py  draw_connections(img, boxes, opts): hub | nearest | mesh, straight/curved (bezier)
  region_fx.py    apply_region_fx(img, box, opts): gradient/invert/darken/brighten/tint/pixelate/scanline
  compositor.py   compose(original, boxes, opts): connections -> region fx -> outline styles
  export.py       save_png(image, path)
  app.py          Tkinter GUI; main()
main.py           entry
tests/            pytest, one file per module
docs/superpowers/ design spec + implementation plan
docs/img/preview.png  README screenshot
```

## Key decisions

- Detection is blob/feature based, not object/face detection. Many boxes (16-512) lock onto
  high-contrast features = the "random but specific" look. No YOLO/torch (rejected: too heavy,
  wrong look).
- Settings split: DETECTION_PARAMS (blob_mode, blob_count, bounding_size, min_blob_size,
  max_blob_pct) re-run detection; everything else just re-composes.
- Box shapes (rect/ellipse/diamond/hexagon/triangle/random pool) apply to outline styles AND
  mask filters AND region fills (via `_shape_mask` / `_resolve_shape` in renderers.py).
- Output is full-res lossless PNG; the on-screen canvas is a downscaled preview only.

## Conventions

- TDD: write test, see it fail, implement, see it pass, commit. One commit per logical change.
- Adding a style: register in renderers.py RENDERERS; add name to options.py lists; the
  30-style smoke test covers "renders without crashing".
- Commit style: `feat:` / `fix:` / `docs:` / `chore:`.

## Git

Private repo `alfarissm/babytrack-effect`, branch `master`. Push: `git push origin master`.

## Backlog

- Face/person detection as a new `blob_mode`. Preferred: OpenCV Haar Cascade (built in,
  `cv2.data.haarcascades`, no download, classical). Alternatives: OpenCV DNN face, YOLO person.
- Optional: connection rate/density control for mesh at high blob counts.
