import tkinter as tk
from time import strftime
import sys
import json
import subprocess
from pathlib import Path

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "general/config.json"
SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "general/settings.py"

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class ClockWidget(tk.Tk):
    BASE_WIDTH = 220
    BASE_HEIGHT = 80
    BASE_TIME_FONT = 24
    BASE_DATE_FONT = 10
    SCALE_FACTOR = 0.3

    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.pos_key = "clock_xy"
        self.alt_held = False
        self.shift_held = False
        self.drag_x = 0
        self.drag_y = 0
        self.resizing = False
        self.start_width = 0
        self.start_height = 0

        self.configure_window()
        self.create_clock()
        self.update_clock()
        self.watch_config()
        self.bind_events()

    def configure_window(self):
        self.overrideredirect(True)
        self.attributes("-alpha", 0.85)
        self.attributes("-toolwindow", True)
        self.configure(bg=self.config_data.get("clock_bg", "#0b0a0c"))
        self.restore_position()

    def restore_position(self):
        pos = self.config_data.get(self.pos_key)
        self.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}+{pos[0]}+{pos[1]}")

    def save_position(self):
        self.config_data[self.pos_key] = [self.winfo_x(), self.winfo_y()]
        save_config(self.config_data)

    def create_clock(self):
        self.clock_label = tk.Label(
            self,
            fg=self.config_data.get("clock_time", "#51ae95"),
            bg=self.config_data.get("clock_bg", "#0b0a0c"),
        )
        self.date_label = tk.Label(
            self,
            fg=self.config_data.get("clock_date", "#afe9dc"),
            bg=self.config_data.get("clock_bg", "#0b0a0c"),
        )
        self.clock_label.place(relx=0.5, rely=0.3, anchor="center")
        self.date_label.place(relx=0.5, rely=0.7, anchor="center")

    def update_clock(self):
        self.clock_label.config(text=strftime("%H:%M"))
        self.date_label.config(text=strftime("%A, %b %d"))

        h = self.winfo_height()
        scale = 1 + (h - self.BASE_HEIGHT) / self.BASE_HEIGHT * self.SCALE_FACTOR

        self.clock_label.config(
            font=("Consolas", max(8, int(self.BASE_TIME_FONT * scale)), "bold")
        )
        self.date_label.config(
            font=("Consolas", max(6, int(self.BASE_DATE_FONT * scale)))
        )

        self.after(1000, self.update_clock)

    def watch_config(self):
        new_config = load_config()
        if new_config != self.config_data:
            self.config_data = new_config
            self.apply_colors()
        self.after(1000, self.watch_config)

    def apply_colors(self):
        bg = self.config_data.get("clock_bg", "#0b0a0c")
        self.configure(bg=bg)
        self.clock_label.config(
            fg=self.config_data.get("clock_time", "#51ae95"), bg=bg
        )
        self.date_label.config(
            fg=self.config_data.get("clock_date", "#afe9dc"), bg=bg
        )

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
        w, h = self.winfo_width(), self.winfo_height()

        if self.shift_held and w - 15 <= event.x <= w and h - 15 <= event.y <= h:
            self.resizing = True
            self.start_width = w
            self.start_height = h
            self.drag_x = event.x_root
            self.drag_y = event.y_root
        elif self.alt_held:
            self.drag_x = event.x
            self.drag_y = event.y

    def do_drag(self, event):
        if self.alt_held:
            x = self.winfo_x() + event.x - self.drag_x
            y = self.winfo_y() + event.y - self.drag_y
            self.geometry(f"+{x}+{y}")
        elif self.resizing:
            dx = event.x_root - self.drag_x
            dy = event.y_root - self.drag_y
            self.geometry(
                f"{max(100, self.start_width + dx)}x{max(50, self.start_height + dy)}"
            )

    def stop_drag(self, event):
        self.drag_x = self.drag_y = 0
        self.resizing = False
        self.save_position()

    def check_resize_area(self, event):
        if self.shift_held:
            w, h = self.winfo_width(), self.winfo_height()
            if w - 15 <= event.x <= w and h - 15 <= event.y <= h:
                self.config(cursor="size_nw_se")
                self.resizing = True
            else:
                self.config(cursor="")
                self.resizing = False
        else:
            self.config(cursor="")
            self.resizing = False

    def open_settings(self, event=None):
        if SETTINGS_FILE.exists():
            subprocess.Popen([sys.executable, str(SETTINGS_FILE)])

if __name__ == "__main__":
    ClockWidget().mainloop()