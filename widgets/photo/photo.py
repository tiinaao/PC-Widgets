import tkinter as tk
import sys
import random
import json
from pathlib import Path
from PIL import Image, ImageTk
import subprocess

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "general/config.json"
SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "general/settings.py"
IMAGE_FOLDER = Path(__file__).resolve().parent.parent.parent / "widgets/photo/image"

TARGET_SIZE = 250
MIN_SIZE = 100
MAX_SIZE = 800
RESIZE_MARGIN = 15

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_random_image():
    if not IMAGE_FOLDER.exists():
        return None
    images = [p for p in IMAGE_FOLDER.iterdir() if p.suffix.lower() in (".jpg", ".png")]
    return random.choice(images) if images else None

class PhotoWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.pos_key = "photo_xy"
        self.alt_held = False
        self.shift_held = False
        self.resizing = False
        self.drag_x = 0
        self.drag_y = 0
        self.start_width = 0
        self.start_height = 0
        self.original_image = None
        self.photo_image = None

        self.configure_window()
        self.create_photo()
        self.bind_events()

    def configure_window(self):
        self.overrideredirect(True)
        self.attributes("-toolwindow", True)
        self.configure(bg="black")
        self.restore_position()

    def restore_position(self):
        pos = self.config_data.get(self.pos_key)

        if pos and len(pos) == 2:
            self.geometry(f"{TARGET_SIZE}x{TARGET_SIZE}+{pos[0]}+{pos[1]}")
        else:
            self.center_window()

    def save_position(self):
        self.config_data[self.pos_key] = [self.winfo_x(), self.winfo_y()]
        save_config(self.config_data)

    def center_window(self):
        x = (self.winfo_screenwidth() - TARGET_SIZE) // 2
        y = (self.winfo_screenheight() - TARGET_SIZE) // 3
        self.geometry(f"{TARGET_SIZE}x{TARGET_SIZE}+{x}+{y}")

    def create_photo(self):
        self.label = tk.Label(self, bg="black", borderwidth=0, highlightthickness=0)
        self.label.pack(expand=True, fill="both")
        self.load_photo()

    def load_photo(self):
        path = get_random_image()
        if not path:
            return

        self.original_image = Image.open(path).convert("RGBA")
        self.resize_image(TARGET_SIZE, TARGET_SIZE)

    def resize_image(self, w, h):
        w = max(MIN_SIZE, min(MAX_SIZE, w))
        h = max(MIN_SIZE, min(MAX_SIZE, h))

        img = self.original_image.copy()
        img.thumbnail((w, h), Image.LANCZOS)

        self.photo_image = ImageTk.PhotoImage(img)
        self.label.config(image=self.photo_image)
        self.geometry(f"{img.width}x{img.height}")

    def bind_events(self):
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind_all("<Alt_L>", lambda e: self.set_alt(True))
        self.bind_all("<KeyRelease-Alt_L>", lambda e: self.set_alt(False))
        self.bind_all("<Shift_L>", lambda e: self.set_shift(True))
        self.bind_all("<KeyRelease-Shift_L>", lambda e: self.set_shift(False))
        self.bind("<Motion>", self.check_resize_area)
        self.bind("<space>", self.open_settings)
        self.bind("<Button-3>", lambda e: self.quit())

    def set_alt(self, state):
        self.alt_held = state

    def set_shift(self, state):
        self.shift_held = state

    def start_drag(self, event):
        if self.alt_held:
            self.drag_x = event.x
            self.drag_y = event.y
        elif self.resizing:
            self.start_width = self.winfo_width()
            self.start_height = self.winfo_height()
            self.drag_x = event.x_root
            self.drag_y = event.y_root

    def do_drag(self, event):
        if self.alt_held:
            self.geometry(f"+{self.winfo_x() + event.x - self.drag_x}+{self.winfo_y() + event.y - self.drag_y}")
        elif self.resizing:
            w = self.start_width + (event.x_root - self.drag_x)
            h = self.start_height + (event.y_root - self.drag_y)
            self.resize_image(w, h)

    def stop_drag(self, event):
        self.drag_x = self.drag_y = 0
        self.resizing = False
        self.save_position()

    def check_resize_area(self, event):
        w, h = self.winfo_width(), self.winfo_height()
        if self.shift_held and event.x >= w - RESIZE_MARGIN and event.y >= h - RESIZE_MARGIN:
            self.config(cursor="size_nw_se")
            self.resizing = True
        else:
            self.config(cursor="")
            self.resizing = False

    def open_settings(self, event=None):
        if SETTINGS_FILE.exists():
            subprocess.Popen([sys.executable, str(SETTINGS_FILE)])

if __name__ == "__main__":
    PhotoWidget().mainloop()