import tkinter as tk
import sys
import threading
import asyncio
import json
import subprocess
from pathlib import Path
from winsdk.windows.media.control import (
    GlobalSystemMediaTransportControlsSessionManager as MediaManager
)

CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "general/config.json"
SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "general/settings.py"
REFRESH_INTERVAL = 1

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class MediaWidget(tk.Tk):
    BASE_WIDTH = 200
    BASE_HEIGHT = 80
    BASE_TITLE_FONT = 14
    BASE_ARTIST_FONT = 10
    BASE_BTN_SIZE = 15
    SCALE_FACTOR = 0.25
    LEFT_PADDING = 10

    def __init__(self):
        super().__init__()
        self.pos_key = "media_xy"
        self.alt_held = False
        self.shift_held = False
        self.drag_x = 0
        self.drag_y = 0
        self.resizing = False
        self.start_width = 0
        self.start_height = 0
        self.config_data = load_config()

        self.configure_window()
        self.create_media()
        self.bind_events()
        self.start_media_loop()
        self.watch_config()

    def configure_window(self):
        bg = self.config_data.get("media_bg", "#0b0a0c")
        self.overrideredirect(True)
        self.attributes("-alpha", 0.9)
        self.attributes("-toolwindow", True)
        self.configure(bg=bg)
        self.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}+300+300")
        pos = self.config_data.get(self.pos_key)
        if pos:
            self.geometry(f"{self.BASE_WIDTH}x{self.BASE_HEIGHT}+{pos[0]}+{pos[1]}")

    def save_position(self):
        self.config_data[self.pos_key] = [self.winfo_x(), self.winfo_y()]
        save_config(self.config_data)

    def create_media(self):
        self.bg_color = self.config_data.get("media_bg", "#0b0a0c")
        self.text_title = self.config_data.get("media_text_t", "#cccccc")
        self.text_artist = self.config_data.get("media_text_a", "#aaaaaa")

        self.container = tk.Frame(self, bg=self.bg_color)
        self.container.pack(fill="both", expand=True, padx=5, pady=5)

        self.play_btn = tk.Label(
            self.container,
            text="⏯",
            bg=self.bg_color,  
            fg="white",
            font=("Consolas", self.BASE_BTN_SIZE, "bold"),
            width=3
        )
        self.play_btn.place(x=self.LEFT_PADDING, rely=0.5, anchor="w")
        self.play_btn.bind("<Button-1>", lambda e: self.toggle_play())

        self.info_frame = tk.Frame(self.container, bg=self.bg_color)
        self.info_frame.place(x=self.LEFT_PADDING + 45, rely=0.5, anchor="w")

        self.title_label = tk.Label(
            self.info_frame,
            text="None",
            fg=self.text_title,
            bg=self.bg_color,
            font=("Consolas", self.BASE_TITLE_FONT, "bold"),
            anchor="w"
        )
        self.title_label.pack(fill="x")

        self.artist_label = tk.Label(
            self.info_frame,
            text="Unknown",
            fg=self.text_artist,
            bg=self.bg_color,
            font=("Consolas", self.BASE_ARTIST_FONT),
            anchor="w"
        )
        self.artist_label.pack(fill="x")

    def start_media_loop(self):
        def loop():
            asyncio.set_event_loop(asyncio.new_event_loop())
            loop = asyncio.get_event_loop()
            async def task():
                manager = await MediaManager.request_async()
                while True:
                    session = manager.get_current_session()
                    if session:
                        info = await session.try_get_media_properties_async()
                        title = info.title or "None"
                        artist = info.artist or "Unknown"
                    else:
                        title, artist = "None", "Unknown"
                    self.after(0, self.update_labels, title, artist)
                    await asyncio.sleep(REFRESH_INTERVAL)
            loop.run_until_complete(task())
        threading.Thread(target=loop, daemon=True).start()

    def update_labels(self, title, artist):
        self.title_label.config(text=title)
        self.artist_label.config(text=artist)

    def toggle_play(self):
        async def play():
            manager = await MediaManager.request_async()
            session = manager.get_current_session()
            if session:
                await session.try_toggle_play_pause_async()
        asyncio.run(play())

    def watch_config(self):
        def update():
            new_config = load_config()
            if new_config != self.config_data:
                self.config_data = new_config
                self.apply_colors()
            self.after(1000, update)
        update()

    def apply_colors(self):
        self.bg_color = self.config_data.get("media_bg", "#0b0a0c")
        self.text_title = self.config_data.get("media_text_t", "#cccccc")
        self.text_artist = self.config_data.get("media_text_a", "#aaaaaa")

        self.configure(bg=self.bg_color)
        self.container.config(bg=self.bg_color)
        self.info_frame.config(bg=self.bg_color)
        self.title_label.config(bg=self.bg_color, fg=self.text_title)
        self.artist_label.config(bg=self.bg_color, fg=self.text_artist)
        self.play_btn.config(bg=self.bg_color)  

    def bind_events(self):
        self.container.bind("<ButtonPress-1>", self.start_drag)
        self.container.bind("<B1-Motion>", self.do_drag)
        self.container.bind("<ButtonRelease-1>", self.stop_drag)
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
        if self.shift_held and self.is_resize_zone(event):
            self.resizing = True
            self.start_width = self.winfo_width()
            self.start_height = self.winfo_height()
            self.drag_x = event.x_root
            self.drag_y = event.y_root
        elif self.alt_held:
            self.drag_x = event.x
            self.drag_y = event.y

    def do_drag(self, event):
        if self.alt_held and not self.resizing:
            x = self.winfo_x() + event.x - self.drag_x
            y = self.winfo_y() + event.y - self.drag_y
            self.geometry(f"+{x}+{y}")
        elif self.resizing:
            dx = event.x_root - self.drag_x
            dy = event.y_root - self.drag_y
            w = max(100, self.start_width + dx)
            h = max(50, self.start_height + dy)
            self.geometry(f"{w}x{h}")

    def stop_drag(self, event):
        self.drag_x = self.drag_y = 0
        self.resizing = False
        self.save_position()

    def is_resize_zone(self, event):
        w, h = self.winfo_width(), self.winfo_height()
        return w - 15 <= event.x <= w and h - 15 <= event.y <= h

    def check_resize_area(self, event):
        if self.shift_held and self.is_resize_zone(event):
            self.config(cursor="size_nw_se")
        else:
            self.config(cursor="")

    def open_settings(self, event=None):
        if SETTINGS_FILE.exists():
            subprocess.Popen([sys.executable, str(SETTINGS_FILE)])

if __name__ == "__main__":
    MediaWidget().mainloop()