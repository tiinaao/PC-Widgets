import tkinter as tk
import sys
import subprocess
import json
from pathlib import Path

TASKS_FILE = Path(__file__).resolve().parent.parent.parent / "widgets/todo/tasks.txt"
CONFIG_FILE = Path(__file__).resolve().parent.parent.parent / "general/config.json"
SETTINGS_FILE = Path(__file__).resolve().parent.parent.parent / "general/settings.py"

BASE_WIDTH = 260
BASE_HEIGHT = 200
TITLE_FONT_BASE = 14
TASK_FONT_BASE = 11
SCALE_FACTOR = 0.25
ADD_BTN_ALPHA = 0.35  

def load_config():
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(data):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

class TodoWidget(tk.Tk):
    def __init__(self):
        super().__init__()
        self.config_data = load_config()
        self.pos_key = "todo_xy"
        self.alt_held = False
        self.shift_held = False
        self.resizing = False
        self.drag_x = 0
        self.drag_y = 0
        self.start_width = 0
        self.start_height = 0
        self.tasks = []

        self.configure_window()
        self.create_todo()
        self.load_tasks()
        self.bind_events()
        self.watch_config()

    def configure_window(self):
        self.overrideredirect(True)
        self.attributes("-alpha", 0.9)
        self.attributes("-toolwindow", True)
        self.bg_color = self.config_data.get("todo_bg", "#0b0a0c")
        self.text_color = self.config_data.get("todo_text", "#cccccc")
        self.configure(bg=self.bg_color)
        self.restore_position()

    def restore_position(self):
        pos = self.config_data.get(self.pos_key)
        if not pos or len(pos) != 2:
            x = (self.winfo_screenwidth() - BASE_WIDTH) // 2
            y = (self.winfo_screenheight() - BASE_HEIGHT) // 3
        else:
            x, y = pos
        self.geometry(f"{BASE_WIDTH}x{BASE_HEIGHT}+{x}+{y}")

    def save_position(self):
        self.config_data[self.pos_key] = [self.winfo_x(), self.winfo_y()]
        save_config(self.config_data)

    def darker(self, hex_color, alpha):
        hex_color = hex_color.lstrip("#")
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        r = int(r * (1 - alpha))
        g = int(g * (1 - alpha))
        b = int(b * (1 - alpha))
        return f"#{r:02x}{g:02x}{b:02x}"

    def apply_colors(self):
        self.bg_color = self.config_data.get("todo_bg", "#0b0a0c")
        self.text_color = self.config_data.get("todo_text", "#cccccc")
        btn_bg = self.darker(self.bg_color, ADD_BTN_ALPHA)

        self.configure(bg=self.bg_color)
        self.container.config(bg=self.bg_color)
        self.task_frame.config(bg=self.bg_color)
        self.title.config(bg=self.bg_color, fg=self.text_color)
        self.add_btn.config(bg=btn_bg, fg=self.text_color, activebackground=btn_bg, activeforeground=self.text_color)
        self.entry.config(bg=btn_bg, fg=self.text_color, insertbackground=self.text_color)

        for row in self.task_frame.winfo_children():
            row.config(bg=self.bg_color)
            for w in row.winfo_children():
                if isinstance(w, tk.Checkbutton):
                    w.config(bg=self.bg_color, fg=self.text_color, selectcolor=self.bg_color)
                else:
                    w.config(bg=self.bg_color, fg=self.text_color)

    def create_todo(self):
        self.container = tk.Frame(self, bg=self.bg_color)
        self.container.pack(fill="both", expand=True)

        self.title = tk.Label(
            self.container,
            text="To Do",
            font=("Consolas", TITLE_FONT_BASE, "bold"),
            fg=self.text_color,
            bg=self.bg_color,
            pady=6
        )
        self.title.pack(fill="x")

        self.task_frame = tk.Frame(self.container, bg=self.bg_color)
        self.task_frame.pack(fill="both", expand=True)

        btn_bg = self.darker(self.bg_color, ADD_BTN_ALPHA)
        self.add_btn = tk.Button(
            self.container,
            text="+ Add Task",
            command=self.show_entry,
            bg=btn_bg,
            fg=self.text_color,
            relief="flat",
            activebackground=btn_bg,
            activeforeground=self.text_color
        )
        self.add_btn.pack(fill="x", padx=5, pady=5)

        self.entry = tk.Entry(
            self.container,
            font=("Consolas", TASK_FONT_BASE),
            bg=btn_bg,
            fg=self.text_color,
            insertbackground=self.text_color,
            relief="flat"
        )
        self.entry.bind("<Return>", self.add_task)
        self.entry.bind("<Escape>", lambda e: self.hide_entry())

    def show_entry(self):
        self.add_btn.pack_forget()
        self.entry.pack(fill="x", padx=5, pady=5)
        self.entry.focus()

    def hide_entry(self):
        self.entry.delete(0, "end")
        self.entry.pack_forget()
        self.add_btn.pack(fill="x", padx=5, pady=5)

    def load_tasks(self):
        if not TASKS_FILE.exists():
            return
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            for t in f:
                t = t.strip()
                if t:
                    self.create_task(t)

    def save_tasks(self):
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            for t in self.tasks:
                f.write(t + "\n")

    def create_task(self, text):
        row = tk.Frame(self.task_frame, bg=self.bg_color)
        row.pack(fill="x", padx=5, pady=2)

        chk = tk.Checkbutton(
            row,
            command=lambda: self.remove_task(row, text),
            bg=self.bg_color,
            fg=self.text_color,
            activebackground=self.bg_color,
            selectcolor=self.bg_color
        )
        chk.pack(side="left")

        lbl = tk.Label(
            row,
            text=text,
            font=("Consolas", TASK_FONT_BASE),
            fg=self.text_color,
            bg=self.bg_color,
            anchor="w"
        )
        lbl.pack(side="left", fill="x", expand=True)

        self.tasks.append(text)
        self.update_size()

    def remove_task(self, row, text):
        if text in self.tasks:
            self.tasks.remove(text)
        row.destroy()
        self.save_tasks()
        self.update_size()

    def add_task(self, event=None):
        text = self.entry.get().strip()
        if text:
            self.create_task(text)
            self.save_tasks()
        self.hide_entry()

    def update_size(self):
        self.update_idletasks()
        h = self.container.winfo_reqheight()
        self.geometry(f"{self.winfo_width()}x{max(120, h)}")
        self.update_fonts(self.winfo_height())

    def update_fonts(self, height):
        scale = 1 + (height - BASE_HEIGHT) / BASE_HEIGHT * SCALE_FACTOR
        self.title.config(font=("Consolas", max(8, int(TITLE_FONT_BASE * scale)), "bold"))
        for row in self.task_frame.winfo_children():
            for w in row.winfo_children():
                if isinstance(w, (tk.Label, tk.Checkbutton)):
                    w.config(font=("Consolas", max(8, int(TASK_FONT_BASE * scale))))

    def watch_config(self):
        new_cfg = load_config()
        if new_cfg != self.config_data:
            self.config_data = new_cfg
            self.apply_colors()
        self.after(1000, self.watch_config)

    def bind_events(self):
        self.bind("<ButtonPress-1>", self.start_drag)
        self.bind("<B1-Motion>", self.do_drag)
        self.bind("<ButtonRelease-1>", self.stop_drag)
        self.bind("<Motion>", self.check_resize_area)
        self.bind("<space>", self.open_settings)
        self.bind_all("<Alt_L>", lambda e: self.set_alt(True))
        self.bind_all("<KeyRelease-Alt_L>", lambda e: self.set_alt(False))
        self.bind_all("<Shift_L>", lambda e: self.set_shift(True))
        self.bind_all("<KeyRelease-Shift_L>", lambda e: self.set_shift(False))
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
            w = max(200, self.start_width + dx)
            h = max(120, self.start_height + dy)
            self.geometry(f"{w}x{h}")
            self.update_fonts(h)

    def stop_drag(self, event):
        self.drag_x = self.drag_y = 0
        self.resizing = False
        self.save_position()

    def check_resize_area(self, event):
        w, h = self.winfo_width(), self.winfo_height()
        if self.shift_held and w - 15 <= event.x <= w and h - 15 <= event.y <= h:
            self.config(cursor="size_nw_se")
            self.resizing = True
        else:
            self.config(cursor="")
            self.resizing = False

    def open_settings(self, event=None):
        if SETTINGS_FILE.exists():
            subprocess.Popen([sys.executable, str(SETTINGS_FILE)])

if __name__ == "__main__":
    TodoWidget().mainloop()