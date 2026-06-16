import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()  # lets PIL open .heic / .heif (iPhone photos)
    _HEIC = " *.heic *.heif"
except ImportError:
    _HEIC = ""

from babytrack.options import Opts, ALL_STYLES, DETECTION_PARAMS, REGION_FILLS
from babytrack.blobs import detect_blobs
from babytrack.compositor import compose
from babytrack.export import save_png

class App:
    def __init__(self, root):
        self.root = root
        root.title("BabyTrack Photo HUD")
        self.opts = Opts()
        self.original = None      # PIL.Image
        self.boxes = []
        self.preview = None       # ImageTk ref
        self._fullscreen = False

        self._build_layout()

        # window: maximized, resizable, F11 fullscreen, Esc exit
        root.rowconfigure(0, weight=1)
        root.columnconfigure(0, weight=1)
        try:
            root.state("zoomed")           # Windows: maximize
        except tk.TclError:
            root.attributes("-zoomed", True)  # Linux fallback
        root.bind("<F11>", self._toggle_fullscreen)
        root.bind("<Escape>", lambda e: self._set_fullscreen(False))
        self.canvas.bind("<Configure>", lambda e: self.redraw())

    def _toggle_fullscreen(self, _=None):
        self._set_fullscreen(not self._fullscreen)

    def _set_fullscreen(self, on):
        self._fullscreen = on
        self.root.attributes("-fullscreen", on)

    def _build_layout(self):
        self.canvas = tk.Canvas(self.root, width=720, height=540, bg="#111", highlightthickness=0)
        self.canvas.grid(row=0, column=0, rowspan=40, sticky="nsew", padx=8, pady=8)

        panel = ttk.Frame(self.root)
        panel.grid(row=0, column=1, sticky="n", padx=8, pady=8)
        r = 0

        ttk.Button(panel, text="Open Photo", command=self.open_photo).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1
        ttk.Button(panel, text="Save PNG", command=self.save).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1

        self.status = ttk.Label(panel, text="open a photo to start")
        self.status.grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Label(panel, text="Blob mode").grid(row=r, column=0, sticky="w")
        self.bmode_var = tk.StringVar(value=self.opts.blob_mode)
        cb0 = ttk.Combobox(panel, textvariable=self.bmode_var, values=["count", "size"], state="readonly", width=14)
        cb0.grid(row=r, column=1, sticky="ew"); cb0.bind("<<ComboboxSelected>>", lambda e: self._set("blob_mode", self.bmode_var.get())); r += 1

        r = self._scale(panel, r, "Blob count", "blob_count", 16, 512)
        r = self._scale(panel, r, "Bound size", "bounding_size", 16, 256)
        r = self._scale(panel, r, "Min blob size", "min_blob_size", 4, 128)

        ttk.Label(panel, text="Style").grid(row=r, column=0, sticky="w")
        self.style_var = tk.StringVar(value=self.opts.style)
        cb = ttk.Combobox(panel, textvariable=self.style_var, values=ALL_STYLES, state="readonly", width=14)
        cb.grid(row=r, column=1, sticky="ew"); cb.bind("<<ComboboxSelected>>", lambda e: self._set("style", self.style_var.get())); r += 1

        r = self._scale(panel, r, "Stroke (thickness)", "stroke", 1, 30)
        r = self._scale(panel, r, "Font size", "font_size", 10, 28)

        self.same_var = tk.BooleanVar(value=self.opts.same_size)
        ttk.Checkbutton(panel, text="Force same size", variable=self.same_var,
                        command=lambda: self._set("same_size", self.same_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        self.score_var = tk.BooleanVar(value=self.opts.show_score)
        ttk.Checkbutton(panel, text="Show score", variable=self.score_var,
                        command=lambda: self._set("show_score", self.score_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        self.connect_var = tk.BooleanVar(value=self.opts.connect)
        ttk.Checkbutton(panel, text="Connect blobs", variable=self.connect_var,
                        command=lambda: self._set("connect", self.connect_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Label(panel, text="Connect mode").grid(row=r, column=0, sticky="w")
        self.conmode_var = tk.StringVar(value=self.opts.connect_mode)
        cb5 = ttk.Combobox(panel, textvariable=self.conmode_var, values=["hub", "nearest", "mesh"], state="readonly", width=14)
        cb5.grid(row=r, column=1, sticky="ew"); cb5.bind("<<ComboboxSelected>>", lambda e: self._set("connect_mode", self.conmode_var.get())); r += 1

        self.curve_var = tk.BooleanVar(value=self.opts.connect_curve)
        ttk.Checkbutton(panel, text="Curved connect", variable=self.curve_var,
                        command=lambda: self._set("connect_curve", self.curve_var.get())).grid(row=r, column=0, columnspan=2, sticky="w"); r += 1

        ttk.Label(panel, text="Region fill").grid(row=r, column=0, sticky="w")
        self.region_var = tk.StringVar(value=self.opts.region_fill)
        cb6 = ttk.Combobox(panel, textvariable=self.region_var, values=REGION_FILLS, state="readonly", width=14)
        cb6.grid(row=r, column=1, sticky="ew"); cb6.bind("<<ComboboxSelected>>", lambda e: self._set("region_fill", self.region_var.get())); r += 1

        ttk.Label(panel, text="Color mode").grid(row=r, column=0, sticky="w")
        self.cmode_var = tk.StringVar(value=self.opts.color_mode)
        cb2 = ttk.Combobox(panel, textvariable=self.cmode_var, values=["single", "random", "by-label"], state="readonly", width=14)
        cb2.grid(row=r, column=1, sticky="ew"); cb2.bind("<<ComboboxSelected>>", lambda e: self._set("color_mode", self.cmode_var.get())); r += 1

        ttk.Button(panel, text="Pick color", command=self.pick_color).grid(row=r, column=0, columnspan=2, sticky="ew"); r += 1

        ttk.Label(panel, text="Label mode").grid(row=r, column=0, sticky="w")
        self.lmode_var = tk.StringVar(value=self.opts.label_mode)
        cb3 = ttk.Combobox(panel, textvariable=self.lmode_var, values=["generic", "random", "custom"], state="readonly", width=14)
        cb3.grid(row=r, column=1, sticky="ew"); cb3.bind("<<ComboboxSelected>>", lambda e: self._set("label_mode", self.lmode_var.get())); r += 1

        ttk.Label(panel, text="Custom label").grid(row=r, column=0, sticky="w")
        self.lcustom_var = tk.StringVar(value=self.opts.label_custom)
        e = ttk.Entry(panel, textvariable=self.lcustom_var, width=16)
        e.grid(row=r, column=1, sticky="ew"); e.bind("<KeyRelease>", lambda ev: self._set("label_custom", self.lcustom_var.get())); r += 1

        ttk.Label(panel, text="Label pos").grid(row=r, column=0, sticky="w")
        self.lpos_var = tk.StringVar(value=self.opts.label_pos)
        cb4 = ttk.Combobox(panel, textvariable=self.lpos_var, values=["center", "top", "bottom"], state="readonly", width=14)
        cb4.grid(row=r, column=1, sticky="ew"); cb4.bind("<<ComboboxSelected>>", lambda e: self._set("label_pos", self.lpos_var.get())); r += 1

    def _scale(self, panel, r, text, attr, lo, hi):
        ttk.Label(panel, text=text).grid(row=r, column=0, sticky="w")
        s = ttk.Scale(panel, from_=lo, to=hi, command=lambda v, a=attr: self._set(a, int(float(v))))
        s.set(getattr(self.opts, attr))
        s.grid(row=r, column=1, sticky="ew")
        return r + 1

    def _set(self, attr, value):
        setattr(self.opts, attr, value)
        if attr in DETECTION_PARAMS:
            self.detect()
        else:
            self.redraw()

    def open_photo(self):
        filetypes = [
            ("Images", "*.jpg *.jpeg *.png *.bmp *.webp" + _HEIC),
            ("HEIC/HEIF", "*.heic *.heif"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if not path:
            return
        try:
            img = Image.open(path)
            img.load()
            self.original = img.convert("RGB")
        except Exception as ex:
            hint = ""
            if path.lower().endswith((".heic", ".heif")) and not _HEIC:
                hint = "\n\npillow-heif not active. Run with the venv python:\n.venv\\Scripts\\python.exe main.py"
            messagebox.showwarning("Cannot open", f"{type(ex).__name__}: {ex}{hint}")
            return
        self.detect()

    def detect(self):
        if self.original is None:
            return
        try:
            self.boxes = detect_blobs(self.original, self.opts)
        except Exception as ex:
            self.status.config(text=f"detect error: {ex}")
            return
        if self.boxes:
            self.status.config(text=f"{len(self.boxes)} blob(s)")
        else:
            self.status.config(text="no blobs - lower min size / raise count")
        self.redraw()

    def redraw(self):
        if self.original is None:
            return
        cw = max(1, self.canvas.winfo_width())
        ch = max(1, self.canvas.winfo_height())
        composed = compose(self.original, self.boxes, self.opts)
        disp = composed.copy()
        disp.thumbnail((cw, ch))
        self.preview = ImageTk.PhotoImage(disp)
        self.canvas.delete("all")
        self.canvas.create_image(cw // 2, ch // 2, image=self.preview)

    def pick_color(self):
        c = colorchooser.askcolor(color=self.opts.color)
        if c and c[1]:
            self.opts.color = c[1]
            self.opts.color_mode = "single"
            self.cmode_var.set("single")
            self.redraw()

    def save(self):
        if self.original is None:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if not path:
            return
        composed = compose(self.original, self.boxes, self.opts)
        save_png(composed, path)
        self.status.config(text=f"saved {path}")

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()
