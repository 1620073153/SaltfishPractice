import tkinter as tk
from tkinter import ttk, messagebox
import time
import math
import json
import os
from datetime import datetime
import platform

# Try to import plyer for notifications
try:
    from plyer import notification
    HAS_NOTIFICATION = True
except ImportError:
    HAS_NOTIFICATION = False

# Try to import winsound for sound on Windows
if platform.system() == "Windows":
    import winsound
    HAS_SOUND = True
else:
    HAS_SOUND = False


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pomodoro_config.json")

DEFAULT_CONFIG = {
    "work_time": 25 * 60,
    "short_break": 5 * 60,
    "long_break": 15 * 60,
    "long_break_interval": 4,
    "sound_enabled": True,
    "notification_enabled": True,
    "volume": 0.7,
    "always_on_top": True,
    "theme": "default",
}

THEMES = {
    "default": {
        "bg": "#2B2B2B",
        "fg": "#FFFFFF",
        "accent": "#E74C3C",
        "accent2": "#2ECC71",
        "accent3": "#3498DB",
        "card_bg": "#363636",
        "button_bg": "#404040",
        "button_hover": "#505050",
        "progress_bg": "#444444",
        "text_secondary": "#AAAAAA",
        "input_bg": "#404040",
        "input_fg": "#FFFFFF",
        "input_border": "#555555",
    },
    "light": {
        "bg": "#F5F5F5",
        "fg": "#333333",
        "accent": "#E74C3C",
        "accent2": "#27AE60",
        "accent3": "#2980B9",
        "card_bg": "#FFFFFF",
        "button_bg": "#E0E0E0",
        "button_hover": "#D0D0D0",
        "progress_bg": "#DDDDDD",
        "text_secondary": "#777777",
        "input_bg": "#FFFFFF",
        "input_fg": "#333333",
        "input_border": "#CCCCCC",
    },
    "tokyo-night": {
        "bg": "#1A1B26",
        "fg": "#A9B1D6",
        "accent": "#F7768E",
        "accent2": "#9ECE6A",
        "accent3": "#7AA2F7",
        "card_bg": "#24283B",
        "button_bg": "#1F2335",
        "button_hover": "#2F3345",
        "progress_bg": "#2F3548",
        "text_secondary": "#565F89",
        "input_bg": "#1F2335",
        "input_fg": "#A9B1D6",
        "input_border": "#2F3548",
    },
}


class PomodoroTimer:
    def __init__(self, root):
        self.root = root
        self.config = self.load_config()
        self.theme = THEMES[self.config.get("theme", "default")]

        self.root.title("番茄钟 - Pomodoro Timer")
        self.root.configure(bg=self.theme["bg"])

        self.set_window_size()

        if self.config.get("always_on_top", True):
            self.root.attributes("-topmost", True)

        self.state = "idle"  # idle, running, paused
        self.mode = "work"   # work, short_break, long_break
        self.time_remaining = self.config["work_time"]
        self.total_time = self.config["work_time"]
        self.completed_pomodoros = 0
        self.current_set = 0
        self.start_time = None
        self.after_id = None
        self.is_flashing = False

        self.create_widgets()
        self.apply_theme()
        self.update_display()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def set_window_size(self):
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        win_w, win_h = 420, 620
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.root.geometry(f"{win_w}x{win_h}+{x}+{y}")
        self.root.resizable(False, False)
        self.root.minsize(400, 580)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                merged = DEFAULT_CONFIG.copy()
                merged.update(user_config)
                return merged
            except Exception:
                pass
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def create_widgets(self):
        # === Title ===
        self.title_label = tk.Label(
            self.root, text="🍅 番茄钟", font=("Segoe UI", 22, "bold"),
            bg=self.theme["bg"], fg=self.theme["fg"]
        )
        self.title_label.pack(pady=(20, 5))

        self.subtitle_label = tk.Label(
            self.root, text="Pomodoro Timer", font=("Segoe UI", 10),
            bg=self.theme["bg"], fg=self.theme["text_secondary"]
        )
        self.subtitle_label.pack(pady=(0, 15))

        # === Mode Selector ===
        self.mode_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.mode_frame.pack(pady=5)

        self.mode_btn_work = tk.Button(
            self.mode_frame, text="专注", font=("Segoe UI", 11, "bold"),
            width=8, relief="flat", cursor="hand2",
            command=lambda: self.switch_mode("work")
        )
        self.mode_btn_work.pack(side=tk.LEFT, padx=3)

        self.mode_btn_short = tk.Button(
            self.mode_frame, text="短休息", font=("Segoe UI", 11, "bold"),
            width=8, relief="flat", cursor="hand2",
            command=lambda: self.switch_mode("short_break")
        )
        self.mode_btn_short.pack(side=tk.LEFT, padx=3)

        self.mode_btn_long = tk.Button(
            self.mode_frame, text="长休息", font=("Segoe UI", 11, "bold"),
            width=8, relief="flat", cursor="hand2",
            command=lambda: self.switch_mode("long_break")
        )
        self.mode_btn_long.pack(side=tk.LEFT, padx=3)

        # === Canvas for circular progress ===
        self.canvas_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.canvas_frame.pack(pady=10)

        self.canvas_size = 280
        self.canvas = tk.Canvas(
            self.canvas_frame, width=self.canvas_size, height=self.canvas_size,
            bg=self.theme["bg"], highlightthickness=0
        )
        self.canvas.pack()

        self.center_x = self.canvas_size // 2
        self.center_y = self.canvas_size // 2
        self.radius = 115
        self.progress_width = 12

        # Progress arc background
        self.canvas.create_oval(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            outline=self.theme["progress_bg"], width=self.progress_width
        )
        self.progress_arc = self.canvas.create_arc(
            self.center_x - self.radius, self.center_y - self.radius,
            self.center_x + self.radius, self.center_y + self.radius,
            start=90, extent=0,
            outline="", width=self.progress_width,
            style="arc"
        )

        # Timer text
        self.timer_label = tk.Label(
            self.canvas_frame, text="25:00", font=("Segoe UI", 52, "bold"),
            bg=self.theme["bg"], fg=self.theme["fg"]
        )
        self.timer_label.place(relx=0.5, rely=0.5, anchor="center",
                               in_=self.canvas)

        # Mode indicator text
        self.mode_text = tk.Label(
            self.canvas_frame, text="准备开始", font=("Segoe UI", 12),
            bg=self.theme["bg"], fg=self.theme["text_secondary"]
        )
        self.mode_text.place(relx=0.5, rely=0.62, anchor="center",
                             in_=self.canvas)

        # === Controls ===
        self.control_frame = tk.Frame(self.root, bg=self.theme["bg"])
        self.control_frame.pack(pady=15)

        self.start_btn = tk.Button(
            self.control_frame, text="▶ 开始", font=("Segoe UI", 13, "bold"),
            width=10, height=1, relief="flat", cursor="hand2",
            command=self.toggle_start
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.reset_btn = tk.Button(
            self.control_frame, text="↺ 重置", font=("Segoe UI", 11),
            width=8, relief="flat", cursor="hand2",
            command=self.reset_timer, state="disabled"
        )
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        self.skip_btn = tk.Button(
            self.control_frame, text="⏭ 跳过", font=("Segoe UI", 11),
            width=8, relief="flat", cursor="hand2",
            command=self.skip_session, state="disabled"
        )
        self.skip_btn.pack(side=tk.LEFT, padx=5)

        # === Stats ===
        self.stats_frame = tk.Frame(self.root, bg=self.theme["card_bg"],
                                    highlightbackground=self.theme.get("input_border", "#555555"),
                                    highlightthickness=1)
        self.stats_frame.pack(pady=10, padx=30, fill=tk.X)

        stats_inner = tk.Frame(self.stats_frame, bg=self.theme["card_bg"])
        stats_inner.pack(pady=10, padx=15)

        # Row 1
        row1 = tk.Frame(stats_inner, bg=self.theme["card_bg"])
        row1.pack(fill=tk.X)

        col1 = tk.Frame(row1, bg=self.theme["card_bg"])
        col1.pack(side=tk.LEFT, expand=True)

        tk.Label(col1, text="今日完成", font=("Segoe UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack()

        self.today_label = tk.Label(col1, text="0 个", font=("Segoe UI", 16, "bold"),
                                    bg=self.theme["card_bg"], fg=self.theme["accent2"])
        self.today_label.pack()

        col2 = tk.Frame(row1, bg=self.theme["card_bg"])
        col2.pack(side=tk.LEFT, expand=True)

        tk.Label(col2, text="当前连续", font=("Segoe UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack()

        self.streak_label = tk.Label(col2, text="0", font=("Segoe UI", 16, "bold"),
                                     bg=self.theme["card_bg"], fg=self.theme["accent3"])
        self.streak_label.pack()

        # Row 2
        row2 = tk.Frame(stats_inner, bg=self.theme["card_bg"])
        row2.pack(fill=tk.X, pady=(8, 0))

        col3 = tk.Frame(row2, bg=self.theme["card_bg"])
        col3.pack(side=tk.LEFT, expand=True)

        tk.Label(col3, text="总专注时长", font=("Segoe UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack()

        self.total_time_label = tk.Label(col3, text="0 分钟", font=("Segoe UI", 14, "bold"),
                                         bg=self.theme["card_bg"], fg=self.theme["fg"])
        self.total_time_label.pack()

        col4 = tk.Frame(row2, bg=self.theme["card_bg"])
        col4.pack(side=tk.LEFT, expand=True)

        tk.Label(col4, text="番茄目标", font=("Segoe UI", 9),
                 bg=self.theme["card_bg"], fg=self.theme["text_secondary"]).pack()

        self.goal_label = tk.Label(col4, text=f"0/{self.config['long_break_interval']}",
                                   font=("Segoe UI", 14, "bold"),
                                   bg=self.theme["card_bg"], fg=self.theme["accent"])
        self.goal_label.pack()

        # === Settings Button ===
        self.settings_btn = tk.Button(
            self.root, text="⚙ 设置", font=("Segoe UI", 10),
            bg=self.theme["button_bg"], fg=self.theme["text_secondary"],
            relief="flat", cursor="hand2", command=self.open_settings
        )
        self.settings_btn.pack(pady=(5, 15))

    def apply_theme(self):
        self.root.configure(bg=self.theme["bg"])
        self.title_label.configure(bg=self.theme["bg"], fg=self.theme["fg"])
        self.subtitle_label.configure(bg=self.theme["bg"], fg=self.theme["text_secondary"])
        self.mode_frame.configure(bg=self.theme["bg"])
        self.canvas_frame.configure(bg=self.theme["bg"])
        self.canvas.configure(bg=self.theme["bg"])
        self.timer_label.configure(bg=self.theme["bg"], fg=self.theme["fg"])
        self.mode_text.configure(bg=self.theme["bg"], fg=self.theme["text_secondary"])
        self.control_frame.configure(bg=self.theme["bg"])
        self.stats_frame.configure(bg=self.theme["card_bg"])
        self.settings_btn.configure(bg=self.theme["button_bg"], fg=self.theme["text_secondary"])
        self.update_mode_buttons()

    def update_mode_buttons(self):
        mode_map = {
            "work": self.mode_btn_work,
            "short_break": self.mode_btn_short,
            "long_break": self.mode_btn_long,
        }
        for mode, btn in mode_map.items():
            is_active = mode == self.mode
            if is_active:
                accent = self.theme["accent"] if mode == "work" else self.theme["accent2"]
                btn.configure(
                    bg=accent, fg="#FFFFFF",
                    activebackground=accent, activeforeground="#FFFFFF"
                )
            else:
                btn.configure(
                    bg=self.theme["button_bg"], fg=self.theme["text_secondary"],
                    activebackground=self.theme["button_hover"],
                    activeforeground=self.theme["fg"]
                )

    def update_display(self):
        minutes = self.time_remaining // 60
        seconds = self.time_remaining % 60
        self.timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        progress = 1 - (self.time_remaining / self.total_time) if self.total_time > 0 else 0
        extent = progress * 360

        self.canvas.itemconfig(self.progress_arc, extent=extent)

        if self.mode == "work":
            self.progress_color = self.theme["accent"]
            status_text = {
                "idle": "准备开始专注",
                "running": "正在专注中...",
                "paused": "已暂停",
            }.get(self.state, "")
        elif self.mode == "short_break":
            self.progress_color = self.theme["accent2"]
            status_text = {
                "idle": "准备短休息",
                "running": "休息中...",
                "paused": "已暂停",
            }.get(self.state, "")
        else:
            self.progress_color = self.theme["accent3"]
            status_text = {
                "idle": "准备长休息",
                "running": "休息中...",
                "paused": "已暂停",
            }.get(self.state, "")

        self.canvas.itemconfig(self.progress_arc, outline=self.progress_color)
        self.mode_text.configure(text=status_text)

    def toggle_start(self):
        if self.state == "idle" or self.state == "paused":
            self.start_timer()
        elif self.state == "running":
            self.pause_timer()

    def start_timer(self):
        self.state = "running"
        self.start_btn.configure(text="⏸ 暂停")
        self.reset_btn.configure(state="normal")
        self.skip_btn.configure(state="normal")
        self.start_time = time.time()
        self.tick()

    def pause_timer(self):
        self.state = "paused"
        self.start_btn.configure(text="▶ 继续")
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.update_display()

    def reset_timer(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.state = "idle"
        self.is_flashing = False
        self.set_mode_time()
        self.start_btn.configure(text="▶ 开始")
        self.reset_btn.configure(state="disabled")
        self.skip_btn.configure(state="disabled")
        self.update_display()

    def skip_session(self):
        if self.state == "idle":
            return
        if self.state == "running" or self.state == "paused":
            if self.after_id:
                self.root.after_cancel(self.after_id)
                self.after_id = None
            self.state = "idle"
            self.is_flashing = False
            self.handle_completion(skipped=True)

    def switch_mode(self, mode):
        if self.state == "running":
            return
        if self.after_id:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        self.mode = mode
        self.state = "idle"
        self.is_flashing = False
        self.set_mode_time()
        self.start_btn.configure(text="▶ 开始")
        self.reset_btn.configure(state="disabled")
        self.skip_btn.configure(state="disabled")
        self.update_mode_buttons()
        self.update_display()

    def set_mode_time(self):
        if self.mode == "work":
            self.time_remaining = self.config["work_time"]
        elif self.mode == "short_break":
            self.time_remaining = self.config["short_break"]
        else:
            self.time_remaining = self.config["long_break"]
        self.total_time = self.time_remaining

    def tick(self):
        if self.state != "running":
            return

        elapsed = time.time() - self.start_time
        self.time_remaining = max(0, self.total_time - int(elapsed))

        self.update_display()

        if self.time_remaining <= 0:
            self.handle_completion()
            return

        self.after_id = self.root.after(200, self.tick)

    def handle_completion(self, skipped=False):
        self.state = "idle"
        self.is_flashing = False
        self.start_btn.configure(text="▶ 开始")
        self.reset_btn.configure(state="disabled")
        self.skip_btn.configure(state="disabled")

        if self.mode == "work" and not skipped:
            self.completed_pomodoros += 1
            self.current_set += 1

            self.play_alert()
            self.show_notification("🎉 专注完成！", f"已完成 {self.completed_pomodoros} 个番茄钟")
            self.flash_window()

            if self.current_set % self.config["long_break_interval"] == 0:
                self.mode = "long_break"
            else:
                self.mode = "short_break"

            self.set_mode_time()
            self.update_stats()
        elif self.mode == "work" and skipped:
            self.set_mode_time()
        else:
            self.play_alert()
            self.show_notification(
                "☕ 休息结束！",
                "该开始新的专注了"
            )
            self.flash_window()
            self.mode = "work"
            self.set_mode_time()

        self.update_mode_buttons()
        self.update_display()

    def play_alert(self):
        if not self.config.get("sound_enabled", True):
            return

        if HAS_SOUND:
            try:
                frequency = 800
                duration = 300
                for _ in range(3):
                    winsound.Beep(frequency, duration)
                    time.sleep(0.1)
            except Exception:
                pass

    def flash_window(self):
        if self.is_flashing:
            return
        self.is_flashing = True
        self.flash_count = 0
        self.do_flash()

    def do_flash(self):
        if not self.is_flashing or self.flash_count >= 6:
            self.is_flashing = False
            try:
                self.root.attributes("-topmost", self.config.get("always_on_top", True))
                self.root.lift()
            except Exception:
                pass
            return

        try:
            current = self.root.attributes("-topmost")
            self.root.attributes("-topmost", not current)
        except Exception:
            pass

        self.flash_count += 1
        self.root.after(400, self.do_flash)

    def show_notification(self, title, message):
        if not self.config.get("notification_enabled", True):
            return
        if HAS_NOTIFICATION:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="番茄钟",
                    timeout=5
                )
            except Exception:
                pass

    def update_stats(self):
        self.today_label.configure(text=f"{self.completed_pomodoros} 个")

        self.goal_label.configure(
            text=f"{self.current_set % self.config['long_break_interval']}/{self.config['long_break_interval']}"
        )

        total_minutes = self.completed_pomodoros * (self.config["work_time"] // 60)
        self.total_time_label.configure(text=f"{total_minutes} 分钟")

    def open_settings(self):
        SettingsDialog(self)

    def on_close(self):
        if self.state == "running":
            result = messagebox.askyesno(
                "确认退出",
                "计时器正在运行，确定要退出吗？"
            )
            if not result:
                return
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.save_config()
        self.root.destroy()


class SettingsDialog:
    def __init__(self, app):
        self.app = app
        self.dialog = tk.Toplevel(app.root)
        self.dialog.title("设置")
        self.dialog.configure(bg=app.theme["bg"])
        self.dialog.transient(app.root)
        self.dialog.grab_set()

        w, h = 380, 420
        x = app.root.winfo_x() + (app.root.winfo_width() - w) // 2
        y = app.root.winfo_y() + (app.root.winfo_height() - h) // 2
        self.dialog.geometry(f"{w}x{h}+{x}+{y}")
        self.dialog.resizable(False, False)

        self.create_widgets()

    def create_widgets(self):
        app = self.app
        t = app.theme

        main = tk.Frame(self.dialog, bg=t["bg"])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        tk.Label(main, text="⏱ 时间设置", font=("Segoe UI", 14, "bold"),
                 bg=t["bg"], fg=t["fg"]).pack(anchor="w")

        # Time settings
        time_frame = tk.Frame(main, bg=t["bg"])
        time_frame.pack(fill=tk.X, pady=10)

        fields = [
            ("专注时间 (分钟)", "work_time", 25),
            ("短休息 (分钟)", "short_break", 5),
            ("长休息 (分钟)", "long_break", 15),
            ("长休息间隔 (番茄数)", "long_break_interval", 4),
        ]

        self.entries = {}
        for label_text, key, default in fields:
            row = tk.Frame(time_frame, bg=t["bg"])
            row.pack(fill=tk.X, pady=4)

            tk.Label(row, text=label_text, font=("Segoe UI", 10),
                     bg=t["bg"], fg=t["text_secondary"]).pack(side=tk.LEFT)

            entry = tk.Spinbox(
                row, from_=1, to=120, width=6,
                font=("Segoe UI", 11),
                bg=t["input_bg"], fg=t["input_fg"],
                relief="flat", justify="center",
                bd=0, highlightthickness=1,
                highlightbackground=t["input_border"],
                highlightcolor=t["accent"]
            )
            value = app.config.get(key, default)
            if key == "long_break_interval":
                entry.configure(from_=1, to=20)
            elif key == "long_break":
                entry.configure(from_=1, to=60)
            entry.delete(0, tk.END)
            entry.insert(0, str(value))
            entry.pack(side=tk.RIGHT)
            self.entries[key] = entry

        # Separator
        tk.Frame(main, bg=t["input_border"], height=1).pack(fill=tk.X, pady=10)

        # Theme selector
        tk.Label(main, text="🎨 主题", font=("Segoe UI", 10, "bold"),
                 bg=t["bg"], fg=t["fg"]).pack(anchor="w", pady=(0, 5))

        theme_frame = tk.Frame(main, bg=t["bg"])
        theme_frame.pack(fill=tk.X)

        self.theme_var = tk.StringVar(value=app.config.get("theme", "default"))
        for theme_name, theme_label in [("default", "暗色"), ("light", "亮色"), ("tokyo-night", "东京之夜")]:
            rb = tk.Radiobutton(
                theme_frame, text=theme_label, variable=self.theme_var,
                value=theme_name, font=("Segoe UI", 10),
                bg=t["bg"], fg=t["fg"], selectcolor=t["bg"],
                activebackground=t["bg"], activeforeground=t["fg"]
            )
            rb.pack(side=tk.LEFT, padx=(0, 12))

        # Options
        tk.Frame(main, bg=t["input_border"], height=1).pack(fill=tk.X, pady=10)

        tk.Label(main, text="🔔 通知", font=("Segoe UI", 10, "bold"),
                 bg=t["bg"], fg=t["fg"]).pack(anchor="w", pady=(0, 5))

        self.sound_var = tk.BooleanVar(value=app.config.get("sound_enabled", True))
        tk.Checkbutton(main, text="声音提醒", variable=self.sound_var,
                       font=("Segoe UI", 10), bg=t["bg"], fg=t["fg"],
                       selectcolor=t["bg"], activebackground=t["bg"],
                       activeforeground=t["fg"]).pack(anchor="w")

        self.notif_var = tk.BooleanVar(value=app.config.get("notification_enabled", True))
        tk.Checkbutton(main, text="桌面通知", variable=self.notif_var,
                       font=("Segoe UI", 10), bg=t["bg"], fg=t["fg"],
                       selectcolor=t["bg"], activebackground=t["bg"],
                       activeforeground=t["fg"]).pack(anchor="w")

        self.ontop_var = tk.BooleanVar(value=app.config.get("always_on_top", True))
        tk.Checkbutton(main, text="窗口置顶", variable=self.ontop_var,
                       font=("Segoe UI", 10), bg=t["bg"], fg=t["fg"],
                       selectcolor=t["bg"], activebackground=t["bg"],
                       activeforeground=t["fg"]).pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(main, bg=t["bg"])
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        tk.Button(
            btn_frame, text="保存", font=("Segoe UI", 11, "bold"),
            bg=t["accent"], fg="#FFFFFF", relief="flat",
            cursor="hand2", command=self.save_settings
        ).pack(side=tk.RIGHT, padx=(5, 0))

        tk.Button(
            btn_frame, text="取消", font=("Segoe UI", 11),
            bg=t["button_bg"], fg=t["fg"], relief="flat",
            cursor="hand2", command=self.dialog.destroy
        ).pack(side=tk.RIGHT, padx=(0, 5))

    def save_settings(self):
        app = self.app
        try:
            app.config["work_time"] = int(self.entries["work_time"].get()) * 60
            app.config["short_break"] = int(self.entries["short_break"].get()) * 60
            app.config["long_break"] = int(self.entries["long_break"].get()) * 60
            app.config["long_break_interval"] = int(self.entries["long_break_interval"].get())
            app.config["sound_enabled"] = self.sound_var.get()
            app.config["notification_enabled"] = self.notif_var.get()
            app.config["always_on_top"] = self.ontop_var.get()

            new_theme = self.theme_var.get()
            if new_theme != app.config.get("theme"):
                app.config["theme"] = new_theme
                app.theme = THEMES[new_theme]
                app.apply_theme()

            app.root.attributes("-topmost", app.config["always_on_top"])
            app.set_mode_time()
            app.update_display()
            app.save_config()
            self.dialog.destroy()
        except ValueError:
            messagebox.showerror("输入错误", "请输入有效的数字")


if __name__ == "__main__":
    root = tk.Tk()
    app = PomodoroTimer(root)
    root.mainloop()
