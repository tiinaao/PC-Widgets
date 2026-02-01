import tkinter as tk
from tkinter import ttk, colorchooser, filedialog
import subprocess
import sys
import json
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
WIDGETS_DIR = SCRIPT_DIR.parent / "widgets"
CONFIG_FILE = SCRIPT_DIR / "config.json"
WIDGETS = ["clock", "text", "media", "todo", "button"] 

config_data = {}
if CONFIG_FILE.exists():
    with open(CONFIG_FILE, "r") as f:
        config_data = json.load(f)

def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(config_data, f, indent=4)

def get_widget_path(widget):
    return (WIDGETS_DIR / widget / f"{widget}.py").resolve()

class SettingsApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Widget Settings")
        self.root.geometry("450x550")
        self.root.configure(bg="#1e1e1e")

        self.widget_vars = {}
        self.running_widgets = {}

        self.setup_style()
        self.create_navigation()
        self.create_widgets_tab()
        self.create_customize_tab()

        self.show_frame("widgets")
        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self.root.mainloop()

    def setup_style(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#e6e6e6", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 13, "bold"))
        style.configure("TButton", font=("Segoe UI", 10), padding=6)
        style.configure("TCheckbutton", background="#1e1e1e", foreground="#e6e6e6")
        style.map("TButton",
                  background=[("active", "#3a3a3a"), ("pressed", "#505050")],
                  foreground=[("active", "#ffffff"), ("pressed", "#ffffff")])
        style.map("TCheckbutton",
                  background=[("active", "#2e2e2e")],
                  foreground=[("active", "#ffffff")])

    def create_navigation(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", pady=8)
        ttk.Button(top_frame, text="Widgets", command=lambda: self.show_frame("widgets")).pack(side="left", padx=10)
        ttk.Button(top_frame, text="Customize", command=lambda: self.show_frame("customize")).pack(side="left")

    def show_frame(self, name):
        for f in [self.widgets_frame, self.customize_frame]:
            f.pack_forget()
        if name == "widgets":
            self.widgets_frame.pack(fill="both", expand=True)
        else:
            self.customize_frame.pack(fill="both", expand=True)

    def create_widgets_tab(self):
        self.widgets_frame = ttk.Frame(self.root)
        ttk.Label(self.widgets_frame, text="Enabled Widgets", style="Header.TLabel").pack(pady=15)

        for w in WIDGETS + ["photo"]:  
            var = tk.IntVar()
            var.set(config_data.get(f"{w}_on", 0))
            self.widget_vars[w] = var
            cb = ttk.Checkbutton(self.widgets_frame, text=w.capitalize(), variable=var,
                                 command=lambda w=w: self.toggle_widget(w))
            cb.pack(anchor="w", padx=40, pady=4)

        ttk.Button(self.widgets_frame, text="Save Changes", command=self.save_widget_settings).pack(pady=10)

    def toggle_widget(self, widget):
        if self.widget_vars[widget].get() == 1:
            config_data[f"{widget}_on"] = 1
            if widget not in self.running_widgets:
                path = get_widget_path(widget)
                self.running_widgets[widget] = subprocess.Popen([sys.executable, str(path)], cwd=path.parent)
        else:
            config_data[f"{widget}_on"] = 0
            if widget in self.running_widgets:
                self.running_widgets[widget].terminate()
                del self.running_widgets[widget]

    def save_widget_settings(self):
        for w, var in self.widget_vars.items():
            config_data[f"{w}_on"] = var.get()
        save_config()

    def create_customize_tab(self):
        self.customize_frame = ttk.Frame(self.root)
        ttk.Label(self.customize_frame, text="Customization", style="Header.TLabel").pack(pady=15)

        self.customize_var = tk.StringVar()
        self.customize_var.set("clock")
        ttk.OptionMenu(self.customize_frame, self.customize_var, "clock", *WIDGETS,
                       command=self.show_customization_options).pack(pady=5)

        self.options_frame = ttk.Frame(self.customize_frame)
        self.options_frame.pack(pady=10)

        ttk.Button(self.customize_frame, text="Save Customization", command=self.save_customization).pack(pady=15)
        self.show_customization_options("clock")

    def show_customization_options(self, widget):
        for c in self.options_frame.winfo_children():
            c.destroy()

        ttk.Label(self.options_frame, text=f"{widget.capitalize()} Settings", style="Header.TLabel").pack(pady=5)

        def add_color_option(label, key):
            frame = ttk.Frame(self.options_frame)
            frame.pack(pady=5)
            ttk.Label(frame, text=label, width=15).pack(side="left")
            var = tk.StringVar()
            var.set(config_data.get(key, "black"))
            setattr(self, key + "_var", var)
            ttk.Entry(frame, textvariable=var, width=12).pack(side="left", padx=5)

            def pick_color():
                color = colorchooser.askcolor(var.get())[1]
                if color:
                    var.set(color)

            ttk.Button(frame, text="Pick", width=6, command=pick_color).pack(side="left", padx=5)

        if widget == "clock":
            add_color_option("Time Color", "clock_time")
            add_color_option("Date Color", "clock_date")
            add_color_option("Background", "clock_bg")
        elif widget == "text":
            add_color_option("Text Color", "text_text")
            add_color_option("Background", "text_bg")
            frame = ttk.Frame(self.options_frame)
            frame.pack(pady=5)
            ttk.Label(frame, text="Text Content", width=15).pack(side="left")
            self.text_c_var = tk.StringVar()
            self.text_c_var.set(config_data.get("text_c", "Example text"))
            ttk.Entry(frame, textvariable=self.text_c_var, width=25).pack(side="left", padx=5)
        elif widget == "media":
            add_color_option("Title Color", "media_text_t")
            add_color_option("Artist Color", "media_text_a")
            add_color_option("Background", "media_bg")
        elif widget == "todo":
            add_color_option("Text Color", "todo_text")
            add_color_option("Background", "todo_bg")
        elif widget == "button":
            add_color_option("Text Color", "button_text")
            add_color_option("Background", "button_bg")
            frame = ttk.Frame(self.options_frame)
            frame.pack(pady=5)
            ttk.Label(frame, text="App to Launch", width=15).pack(side="left")
            self.button_c_var = tk.StringVar()
            self.button_c_var.set(config_data.get("button_c", "notepad.exe"))
            ttk.Entry(frame, textvariable=self.button_c_var, width=25).pack(side="left", padx=5)
            ttk.Button(frame, text="Browse", command=self.pick_button_app).pack(side="left", padx=5)

    def pick_button_app(self):
        file = filedialog.askopenfilename(title="Select Executable",
                                          filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
        if file:
            self.button_c_var.set(file)

    def save_customization(self):
        keys = ["clock_time", "clock_date", "clock_bg",
                "text_text", "text_bg",
                "media_text_t", "media_text_a", "media_bg",
                "todo_text", "todo_bg",
                "button_text", "button_bg"]
        for key in keys:
            var = getattr(self, key + "_var", None)
            if var:
                config_data[key] = var.get()
        if hasattr(self, "text_c_var"):
            config_data["text_c"] = self.text_c_var.get()
        if hasattr(self, "button_c_var"):
            config_data["button_c"] = self.button_c_var.get()
        save_config()

if __name__ == "__main__": 
    SettingsApp().mainloop()