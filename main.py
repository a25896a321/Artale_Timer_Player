# -*- coding: utf-8 -*-
"""
Artale Timer Player  v1.0.1
Author  : oo_jump
Window  : Artale Timer Player_v1.0.1

Run as Administrator to enable global hotkeys.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import threading
import os
import sys
import json
import copy
import webbrowser
import ctypes
import ctypes.wintypes as wintypes

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from translations import TRANSLATIONS
from calculator import (
    BUTTON_NAMES,
    compute_tagged_results,
    compute_plain_results,
    compute_best5zones,
    minutes_to_str,
)

# ══════════════════════════════════════════════════════════════════════════════
# App metadata & paths
# ══════════════════════════════════════════════════════════════════════════════

VERSION    = "1.0.1"
APP_NAME   = f"Artale Timer Player_v{VERSION}"
AUTHOR     = "oo_jump"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SETTINGS_FILE = os.path.join(SCRIPT_DIR, "settings.json")
PNG_DIR       = os.path.join(SCRIPT_DIR, "png_type")
ICON_PATH     = os.path.join(PNG_DIR, "Artale_timer_player_ico.ico")

# ── Colour palette ─────────────────────────────────────────────────────────
BG_MAIN    = "#0f0f1a"
BG_FRAME   = "#161628"
BG_CARD    = "#1c1c30"
BG_BTN     = "#1e2a4a"
BG_BTN_HV  = "#2a3d6a"
BG_BTN_ACT = "#4a3080"
BG_PREVIEW = "#141428"
BG_RESULTS = "#0c0c1e"
BG_ENTRY   = "#1a1a30"
FG_TEXT    = "#dde2f0"
FG_HINT    = "#7080a0"
FG_ACCENT  = "#5bb8f5"
FG_SEL     = "#ffd040"
FG_RESULT  = "#7de88a"
FG_RESULT_H= "#5bb8f5"
FG_WHITE   = "#ffffff"
FG_MUTED   = "#505068"
BORDER     = "#2a2a48"

FONT_FAMILY = "Microsoft YaHei UI"
FONT_MAIN   = (FONT_FAMILY, 9)
FONT_HINT   = (FONT_FAMILY, 8)
FONT_BTN    = (FONT_FAMILY, 9, "bold")
FONT_TIME   = (FONT_FAMILY, 11, "bold")

# ── VK code tables ─────────────────────────────────────────────────────────
VK_CODE_MAP: dict = {
    'NumPad0': 0x60, 'NumPad1': 0x61, 'NumPad2': 0x62, 'NumPad3': 0x63,
    'NumPad4': 0x64, 'NumPad5': 0x65, 'NumPad6': 0x66, 'NumPad7': 0x67,
    'NumPad8': 0x68, 'NumPad9': 0x69, 'NumPad*': 0x6A, 'NumPad+': 0x6B,
    'NumPad-': 0x6D, 'NumPad.': 0x6E, 'NumPad/': 0x6F,
    **{f'F{n}': 0x6F + n for n in range(1, 13)},
    **{c: 0x40 + i for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ', 1)},
}
VK_NAME_MAP: dict = {v: k for k, v in VK_CODE_MAP.items()}

KEYSYM_VK: dict = {
    'KP_1': 0x61, 'KP_2': 0x62, 'KP_3': 0x63, 'KP_4': 0x64,
    'KP_5': 0x65, 'KP_6': 0x66, 'KP_7': 0x67, 'KP_8': 0x68,
    'KP_9': 0x69, 'KP_0': 0x60,
    'KP_Add': 0x6B, 'KP_Subtract': 0x6D,
    'KP_Decimal': 0x6E, 'KP_Multiply': 0x6A, 'KP_Divide': 0x6F,
    **{f'F{n}': 0x6F + n for n in range(1, 13)},
}

# ── Time button definitions ────────────────────────────────────────────────
TIME_BUTTONS = [
    ('btn_10min', '10分'), ('btn_30min', '30分'),
    ('btn_50min', '50分'), ('btn_1hr',   '1hr'),
    ('btn_2hr',  '2hr'),  ('btn_4hr',   '4hr'),
    ('btn_9hr',  '9hr'),  ('btn_x2',    'x2'),
]

SORT_ORDERS = ['base_desc', 'base_asc', 'result_desc', 'result_asc', 'best5zones']

# ── Default settings ────────────────────────────────────────────────────────
DEFAULT_SETTINGS: dict = {
    "language": "zh",
    "topmost": False,
    "sort_order": "base_desc",
    "opacity": 1.0,
    "hotkeys": {
        "10分": {"vk": 0x61, "name": "NumPad1"},
        "30分": {"vk": 0x63, "name": "NumPad3"},
        "50分": {"vk": 0x65, "name": "NumPad5"},
        "1hr":  {"vk": 0x66, "name": "NumPad6"},
        "2hr":  {"vk": 0x62, "name": "NumPad2"},
        "4hr":  {"vk": 0x64, "name": "NumPad4"},
        "9hr":  {"vk": 0x69, "name": "NumPad9"},
        "x2":   {"vk": 0x6B, "name": "NumPad+"},
        "clear":{"vk": 0x6E, "name": "NumPad."},
        "undo": {"vk": 0x6D, "name": "NumPad-"},
    },
    "interface": {
        # Preview
        "preview_fg":       "#ffd040",
        "preview_bg_on":    True,
        "preview_bg":       "#141428",
        # Float window
        "float_bg_on":      True,
        "float_bg":         "#0f0f1a",
        "float_x":          100,
        "float_y":          100,
        "float_opacity":    0.92,
        "show_float_sel":   True,       # show time buttons in float
        "float_font_size":  8,
        "float_fg":         "#7de88a",
        # Buttons (synced to float)
        "btn_color":        "#5bb8f5",
        "btn_bg_on":        True,
        "show_hotkeys":     True,
        "btn_icon_size":    36,
        "btn_spacing":      2,
        # Results display
        "results_font_size":    9,
        "results_fg":           "#7de88a",
        "results_show_number":  True,
        "results_show_estimate":True,
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# Utilities
# ══════════════════════════════════════════════════════════════════════════════

def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


# ══════════════════════════════════════════════════════════════════════════════
# Win32 global hotkey listener
# ══════════════════════════════════════════════════════════════════════════════

class Win32HotkeyListener:
    WM_HOTKEY = 0x0312
    WM_QUIT   = 0x0012

    def __init__(self, id_to_action: dict, callback):
        self._id_to_action = id_to_action
        self._callback     = callback
        self._thread: threading.Thread | None = None
        self._win32_tid: int = 0

    def start(self):
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if self._win32_tid:
            ctypes.windll.user32.PostThreadMessageW(
                self._win32_tid, self.WM_QUIT, 0, 0)

    def _run(self):
        self._win32_tid = ctypes.windll.kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        while True:
            bRet = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if bRet == 0 or bRet == -1:
                break
            if msg.message == self.WM_HOTKEY:
                action = self._id_to_action.get(msg.wParam)
                if action and self._callback:
                    self._callback(action)
        for hid in self._id_to_action:
            ctypes.windll.user32.UnregisterHotKey(None, hid)


def build_hotkey_listener(hotkeys_cfg: dict, callback):
    actions = {
        "10分": hotkeys_cfg["10分"]["vk"], "30分": hotkeys_cfg["30分"]["vk"],
        "50分": hotkeys_cfg["50分"]["vk"], "1hr":  hotkeys_cfg["1hr"]["vk"],
        "2hr":  hotkeys_cfg["2hr"]["vk"],  "4hr":  hotkeys_cfg["4hr"]["vk"],
        "9hr":  hotkeys_cfg["9hr"]["vk"],  "x2":   hotkeys_cfg["x2"]["vk"],
        "clear":hotkeys_cfg["clear"]["vk"],"undo": hotkeys_cfg["undo"]["vk"],
    }
    id_to_action = {}
    for i, (action, vk) in enumerate(actions.items(), start=1):
        if ctypes.windll.user32.RegisterHotKey(None, i, 0, vk):
            id_to_action[i] = action
        else:
            for j in range(1, i):
                ctypes.windll.user32.UnregisterHotKey(None, j)
            return None
    listener = Win32HotkeyListener(id_to_action, callback)
    listener.start()
    return listener


# ══════════════════════════════════════════════════════════════════════════════
# Main Application
# ══════════════════════════════════════════════════════════════════════════════

class ArtaleTimerPlayer:

    def __init__(self):
        # State
        self.selected: list[str] = []
        self.settings: dict = self._load_settings()
        self.lang: str     = self.settings["language"]
        self.is_topmost: bool = self.settings["topmost"]
        self._admin: bool  = is_admin()
        self._hk_listener  = None

        # Sub-window slots (single-instance)
        self._hotkey_win = None
        self._iface_win  = None
        self._float_win  = None

        # Float drag
        self._float_drag_x = self._float_drag_y = 0
        self._img_move: object = None
        self._img_gear: object = None

        # Build
        self.root = tk.Tk()
        self._setup_root()
        self._build_ui()

        if self._admin:
            self._start_global_hotkeys()
        else:
            self._bind_local_hotkeys()

        self._update_hint()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    # ── Translation ──────────────────────────────────────────────────────

    def t(self, key: str) -> str:
        return TRANSLATIONS.get(self.lang, TRANSLATIONS['zh']).get(key, key)

    # ── Settings ─────────────────────────────────────────────────────────

    def _load_settings(self) -> dict:
        s = copy.deepcopy(DEFAULT_SETTINGS)
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, encoding='utf-8') as f:
                    saved = json.load(f)
                for k, v in saved.items():
                    if isinstance(v, dict) and k in s and isinstance(s[k], dict):
                        s[k].update(v)
                    else:
                        s[k] = v
            except Exception:
                pass
        return s

    def _save_settings(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror(self.t('msg_error_title'), str(e))

    # ── Root window ───────────────────────────────────────────────────────

    def _setup_root(self):
        self.root.title(APP_NAME)
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)
        w, h = 490, 630
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.root.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        self.root.attributes('-topmost', self.is_topmost)
        self.root.attributes('-alpha', self.settings.get("opacity", 1.0))
        if os.path.exists(ICON_PATH):
            try:
                self.root.iconbitmap(ICON_PATH)
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════════════════
    # UI builders
    # ══════════════════════════════════════════════════════════════════════

    def _build_ui(self):
        self._build_hint_frame()
        self._build_top_frame()
        self._build_time_buttons_frame()
        self._build_preview_frame()
        self._build_results_frame()
        self._build_opacity_frame()

    # ── hint_frame ────────────────────────────────────────────────────────

    def _build_hint_frame(self):
        self.hint_frame = tk.Frame(self.root, bg=BG_FRAME, height=26)
        self.hint_frame.pack(fill=tk.X)
        self.hint_frame.pack_propagate(False)
        self.hint_label = tk.Label(
            self.hint_frame, text='', bg=BG_FRAME, fg=FG_HINT,
            font=FONT_HINT, anchor='w', padx=8)
        self.hint_label.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.topmost_indicator = tk.Label(
            self.hint_frame, text='', bg=BG_FRAME, fg=FG_ACCENT,
            font=FONT_HINT, padx=8)
        self.topmost_indicator.pack(side=tk.RIGHT)

    def _update_hint(self, status: str = 'ready'):
        top_txt = self.t('hint_topmost_on') if self.is_topmost else self.t('hint_topmost_off')
        self.topmost_indicator.config(
            text=top_txt, fg=FG_ACCENT if self.is_topmost else FG_MUTED)
        key = {
            'ready':      'hint_ready',
            'selecting':  'hint_selecting',
            'calculated': 'hint_calculated',
            'settings':   'hint_settings_open',
        }.get(status, 'hint_ready')
        self.hint_label.config(text=self.t(key))

    # ── top_frame ─────────────────────────────────────────────────────────

    def _build_top_frame(self):
        self.top_frame = tk.Frame(self.root, bg=BG_CARD, pady=4)
        self.top_frame.pack(fill=tk.X, pady=(1, 0))

        def _btn(text, cmd, w=7, fg=FG_TEXT):
            b = tk.Button(
                self.top_frame, text=text, command=cmd,
                bg=BG_BTN, fg=fg, activebackground=BG_BTN_HV,
                activeforeground=FG_TEXT, relief=tk.FLAT,
                font=FONT_BTN, width=w, cursor='hand2', padx=4, pady=3)
            b.pack(side=tk.LEFT, padx=2)
            return b

        self.topmost_btn  = _btn(self.t('btn_topmost_on'), self._toggle_topmost, w=7,
                                 fg=FG_ACCENT if self.is_topmost else FG_TEXT)
        self.hotkeys_btn  = _btn(self.t('btn_hotkeys'),   self._open_hotkey_settings, w=8)
        self.iface_btn    = _btn(self.t('btn_interface'),  self._open_interface_settings, w=9)
        self.sponsor_btn  = _btn(self.t('btn_sponsor'),   self._open_sponsor, w=7)
        self.lang_btn     = _btn(self.t('btn_lang'),      self._toggle_lang, w=5, fg=FG_ACCENT)
        self.float_btn    = _btn(self.t('btn_float'),     self._toggle_float, w=6)

    # ── Time buttons (4 cols × 2 rows) ───────────────────────────────────

    def _build_time_buttons_frame(self):
        if hasattr(self, '_time_btn_outer') and self._time_btn_outer.winfo_exists():
            self._time_btn_outer.destroy()

        outer = tk.Frame(self.root, bg=BG_MAIN, pady=6)
        outer.pack(fill=tk.X, padx=6)
        self._time_btn_outer = outer
        self.time_btn_widgets: dict[str, tk.Button] = {}

        iface   = self.settings["interface"]
        gap     = iface["btn_spacing"]
        btn_fg  = iface["btn_color"]
        btn_bg  = BG_BTN if iface["btn_bg_on"] else BG_MAIN

        for idx, (label_key, name) in enumerate(TIME_BUTTONS):
            col = idx % 4
            row = idx // 4
            text = self._time_btn_label(label_key, name)
            b = tk.Button(
                outer, text=text, width=7, height=2,
                bg=btn_bg, fg=btn_fg,
                activebackground=BG_BTN_HV, activeforeground=FG_TEXT,
                relief=tk.FLAT, font=FONT_BTN, cursor='hand2',
                command=lambda n=name: self._on_time_btn(n))
            b.grid(row=row, column=col, padx=gap, pady=gap, sticky='nsew')
            self.time_btn_widgets[name] = b

        for c in range(4):
            outer.columnconfigure(c, weight=1)

    def _time_btn_label(self, label_key: str, name: str) -> str:
        text = self.t(label_key)
        iface = self.settings["interface"]
        if iface.get("show_hotkeys", True):
            hk = self.settings["hotkeys"].get(name, {}).get("name", "")
            if hk:
                text += f"\n[{hk}]"
        return text

    # ── Preview frame ─────────────────────────────────────────────────────

    def _build_preview_frame(self):
        self.preview_lf = tk.LabelFrame(
            self.root, text=self.t('preview_title'),
            bg=BG_PREVIEW, fg=FG_ACCENT, font=FONT_HINT,
            relief=tk.FLAT, bd=1,
            highlightbackground=BORDER, highlightthickness=1)
        self.preview_lf.pack(fill=tk.X, padx=6, pady=(4, 2))

        iface    = self.settings["interface"]
        slot_bg  = iface["preview_bg"] if iface["preview_bg_on"] else BG_PREVIEW
        slot_fg  = iface["preview_fg"]

        self.preview_slots: list[tk.Button] = []
        for i in range(4):
            slot = tk.Button(
                self.preview_lf,
                text=self.t('preview_empty'),
                width=9, height=2,
                bg=slot_bg, fg=FG_MUTED,
                activebackground=BG_BTN_HV,
                relief=tk.FLAT, font=FONT_BTN, cursor='hand2',
                command=lambda idx=i: self._on_preview_click(idx))
            slot.pack(side=tk.LEFT, padx=4, pady=4, expand=True, fill=tk.X)
            self.preview_slots.append(slot)

    def _update_preview(self):
        iface   = self.settings["interface"]
        slot_bg = iface["preview_bg"] if iface["preview_bg_on"] else BG_PREVIEW
        slot_fg = iface["preview_fg"]
        for i, slot in enumerate(self.preview_slots):
            if i < len(self.selected):
                slot.config(text=self.selected[i], fg=slot_fg,
                            bg=slot_bg, font=FONT_TIME)
            else:
                slot.config(text=self.t('preview_empty'), fg=FG_MUTED,
                            bg=BG_PREVIEW, font=FONT_BTN)

    # ── Results frame ─────────────────────────────────────────────────────

    def _build_results_frame(self):
        rf = tk.Frame(self.root, bg=BG_MAIN)
        rf.pack(fill=tk.BOTH, expand=True, padx=6, pady=(2, 2))

        # Header row
        header = tk.Frame(rf, bg=BG_MAIN)
        header.pack(fill=tk.X)

        self.results_title_lbl = tk.Label(
            header, text=self.t('results_title'),
            bg=BG_MAIN, fg=FG_RESULT_H, font=FONT_BTN, anchor='w')
        self.results_title_lbl.pack(side=tk.LEFT, padx=4)

        self._sort_labels = [self.t(f'sort_{o}') for o in SORT_ORDERS]
        self.sort_var = tk.StringVar(value=self._sort_labels[
            SORT_ORDERS.index(self.settings["sort_order"])])

        self.sort_combo = ttk.Combobox(
            header, textvariable=self.sort_var,
            values=self._sort_labels, state='readonly',
            width=22, font=FONT_HINT)
        self.sort_combo.pack(side=tk.RIGHT, padx=4)
        self.sort_combo.bind('<<ComboboxSelected>>', self._on_sort_change)

        # Text + scrollbar
        txt_frame = tk.Frame(
            rf, bg=BG_RESULTS,
            highlightbackground=BORDER, highlightthickness=1)
        txt_frame.pack(fill=tk.BOTH, expand=True, pady=2)

        sb = tk.Scrollbar(txt_frame, orient=tk.VERTICAL, bg=BG_CARD)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        iface = self.settings["interface"]
        res_font_size = iface.get("results_font_size", 9)
        res_fg        = iface.get("results_fg", FG_RESULT)

        self.results_text = tk.Text(
            txt_frame,
            bg=BG_RESULTS, fg=res_fg,
            font=("Consolas", res_font_size),
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED, wrap=tk.NONE,
            yscrollcommand=sb.set,
            selectbackground=BG_BTN_HV,
            padx=8, pady=6)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.config(command=self.results_text.yview)

        self._configure_result_tags(res_fg)
        self._update_results()

    def _configure_result_tags(self, res_fg: str = FG_RESULT):
        iface = self.settings["interface"]
        float_fg = iface.get("float_fg", FG_RESULT)
        self.results_text.tag_configure('header',      foreground=FG_RESULT_H,
                                        font=("Consolas", iface.get("results_font_size", 9), "bold"))
        self.results_text.tag_configure('col_num',     foreground=FG_HINT)
        self.results_text.tag_configure('col_range',   foreground=FG_TEXT)
        self.results_text.tag_configure('col_action',  foreground=FG_WHITE)
        self.results_text.tag_configure('col_estimate',foreground=res_fg)
        self.results_text.tag_configure('muted',       foreground=FG_MUTED)
        self.results_text.tag_configure('newline',     foreground=res_fg)

    def _update_results(self):
        txt = self.results_text
        txt.config(state=tk.NORMAL)
        txt.delete('1.0', tk.END)

        iface        = self.settings["interface"]
        show_number  = iface.get("results_show_number",   True)
        show_estimate= iface.get("results_show_estimate", True)

        if not self.selected:
            txt.insert(tk.END, self.t('results_empty') + '\n', 'muted')
        else:
            order  = self.settings["sort_order"]
            tagged = compute_tagged_results(
                self.selected, order, self.lang, show_number, show_estimate)
            for text_part, tag in tagged:
                txt.insert(tk.END, text_part, tag)

        txt.config(state=tk.DISABLED)

        # Mirror to float
        if self._float_win and self._float_win.winfo_exists():
            self._float_update_results()

    # ── Opacity frame ─────────────────────────────────────────────────────

    def _build_opacity_frame(self):
        of = tk.Frame(self.root, bg=BG_MAIN, pady=2)
        of.pack(fill=tk.X, padx=6, pady=(0, 4))

        self.opacity_lbl = tk.Label(
            of, text=self.t('opacity_label'),
            bg=BG_MAIN, fg=FG_HINT, font=FONT_HINT)
        self.opacity_lbl.pack(side=tk.LEFT, padx=4)

        self.opacity_var = tk.DoubleVar(value=self.settings.get("opacity", 1.0))
        scale = tk.Scale(
            of, from_=0.2, to=1.0, resolution=0.05,
            orient=tk.HORIZONTAL, variable=self.opacity_var,
            bg=BG_MAIN, fg=FG_TEXT, troughcolor=BG_BTN,
            highlightthickness=0, showvalue=False, length=260,
            command=self._on_opacity_change)
        scale.pack(side=tk.LEFT, padx=4)

        self.opacity_pct = tk.Label(
            of, text=f"{int(self.opacity_var.get()*100)}%",
            bg=BG_MAIN, fg=FG_HINT, font=FONT_HINT, width=4)
        self.opacity_pct.pack(side=tk.LEFT)

    # ══════════════════════════════════════════════════════════════════════
    # Event handlers
    # ══════════════════════════════════════════════════════════════════════

    def _on_time_btn(self, name: str):
        """Add a button to selection (no hard cap at 4 for display, but max 4)."""
        if len(self.selected) < 4:
            self.selected.append(name)
        self._after_selection_change()

    def _on_preview_click(self, idx: int):
        """Remove the item at position idx from selection."""
        if idx < len(self.selected):
            self.selected.pop(idx)
            self._after_selection_change()

    def _action_undo(self):
        if self.selected:
            self.selected.pop()
            self._after_selection_change()

    def _action_clear(self):
        self.selected.clear()
        self._after_selection_change()

    def _after_selection_change(self):
        self._update_preview()
        if not self.selected:
            self._update_hint('ready')
        elif len(self.selected) < 4:
            self._update_hint('selecting')
        else:
            self._update_hint('calculated')
        self._update_results()
        if self._float_win and self._float_win.winfo_exists():
            self._float_update_preview()
            self._float_update_results()

    def _on_sort_change(self, event=None):
        try:
            idx = self._sort_labels.index(self.sort_var.get())
            self.settings["sort_order"] = SORT_ORDERS[idx]
        except ValueError:
            pass
        self._update_results()

    def _on_opacity_change(self, val=None):
        v = self.opacity_var.get()
        self.root.attributes('-alpha', v)
        self.settings["opacity"] = v
        self.opacity_pct.config(text=f"{int(v*100)}%")

    def _toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.settings["topmost"] = self.is_topmost
        self.root.attributes('-topmost', self.is_topmost)
        fg = FG_ACCENT if self.is_topmost else FG_TEXT
        self.topmost_btn.config(fg=fg)
        self._update_hint()
        self._save_settings()

    # ── Immediate language switch ─────────────────────────────────────────

    def _toggle_lang(self):
        self.lang = 'en' if self.lang == 'zh' else 'zh'
        self.settings["language"] = self.lang
        self._save_settings()
        self._refresh_all_text()

    def _refresh_all_text(self):
        """Update every UI label/button to the current language instantly."""
        self.root.title(APP_NAME)
        self._update_hint()

        # top_frame
        self.topmost_btn.config(text=self.t('btn_topmost_on'))
        self.hotkeys_btn.config(text=self.t('btn_hotkeys'))
        self.iface_btn.config(text=self.t('btn_interface'))
        self.sponsor_btn.config(text=self.t('btn_sponsor'))
        self.lang_btn.config(text=self.t('btn_lang'))
        self.float_btn.config(text=self.t('btn_float'))

        # preview_frame
        self.preview_lf.config(text=self.t('preview_title'))
        self._update_preview()

        # results
        self.results_title_lbl.config(text=self.t('results_title'))
        self._sort_labels = [self.t(f'sort_{o}') for o in SORT_ORDERS]
        cur_order = self.settings["sort_order"]
        self.sort_combo.config(values=self._sort_labels)
        self.sort_var.set(self._sort_labels[SORT_ORDERS.index(cur_order)])
        self._update_results()

        # opacity
        self.opacity_lbl.config(text=self.t('opacity_label'))

        # time buttons
        for (label_key, name) in TIME_BUTTONS:
            if name in self.time_btn_widgets:
                self.time_btn_widgets[name].config(
                    text=self._time_btn_label(label_key, name))

    # ── Hotkeys ───────────────────────────────────────────────────────────

    def _on_hotkey(self, action: str):
        if action in ('10分', '30分', '50分', '1hr', '2hr', '4hr', '9hr', 'x2'):
            self.root.after(0, lambda a=action: self._on_time_btn(a))
        elif action == 'undo':
            self.root.after(0, self._action_undo)
        elif action == 'clear':
            self.root.after(0, self._action_clear)

    def _start_global_hotkeys(self):
        try:
            self._hk_listener = build_hotkey_listener(
                self.settings["hotkeys"], self._on_hotkey)
        except Exception:
            self._bind_local_hotkeys()

    def _stop_global_hotkeys(self):
        if self._hk_listener:
            self._hk_listener.stop()
            self._hk_listener = None

    def _bind_local_hotkeys(self):
        for btn_name in DEFAULT_SETTINGS["hotkeys"]:
            vk   = self.settings["hotkeys"][btn_name]["vk"]
            ksym = VK_NAME_MAP.get(vk, "")
            if not ksym:
                continue
            tk_sym = (ksym.replace('NumPad', 'KP_')
                         .replace('KP_+', 'KP_Add')
                         .replace('KP_-', 'KP_Subtract')
                         .replace('KP_.', 'KP_Decimal'))
            try:
                self.root.bind(f'<{tk_sym}>',
                               lambda e, a=btn_name: self._on_hotkey(a))
            except Exception:
                pass

    # ══════════════════════════════════════════════════════════════════════
    # Hotkey settings window
    # ══════════════════════════════════════════════════════════════════════

    def _open_hotkey_settings(self):
        if self._hotkey_win and self._hotkey_win.winfo_exists():
            self._hotkey_win.lift(); return
        self._update_hint('settings')

        win = tk.Toplevel(self.root)
        self._hotkey_win = win
        win.title(self.t('hotkey_title'))
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)
        win.attributes('-topmost', True)
        self._set_icon(win)
        win.protocol("WM_DELETE_WINDOW",
                     lambda: self._close_sub(win, '_hotkey_win'))

        actions = [
            ('10分','hotkey_10min'),('30分','hotkey_30min'),
            ('50分','hotkey_50min'),('1hr', 'hotkey_1hr'),
            ('2hr', 'hotkey_2hr'), ('4hr', 'hotkey_4hr'),
            ('9hr', 'hotkey_9hr'), ('x2',  'hotkey_x2'),
            ('clear','hotkey_clear'),('undo','hotkey_undo'),
        ]
        fr = tk.Frame(win, bg=BG_MAIN, padx=16, pady=12)
        fr.pack(fill=tk.BOTH, expand=True)

        tk.Label(fr, text=self.t('hotkey_col_action'), bg=BG_MAIN, fg=FG_ACCENT,
                 font=FONT_BTN, width=12).grid(row=0, column=0, padx=4, pady=2)
        tk.Label(fr, text=self.t('hotkey_col_key'), bg=BG_MAIN, fg=FG_ACCENT,
                 font=FONT_BTN, width=16).grid(row=0, column=1, padx=4, pady=2)

        key_vars: dict[str, tk.StringVar] = {}
        key_btns: dict[str, tk.Button]   = {}
        capturing = {'active': None}

        def start_capture(action):
            if capturing['active']:
                return
            capturing['active'] = action
            key_btns[action].config(text=self.t('hotkey_listening'),
                                    fg=FG_ACCENT, bg=BG_BTN_ACT)
            win.focus_force()
            win.bind('<KeyPress>', on_keypress)

        def on_keypress(event):
            action = capturing['active']
            if not action:
                return
            vk   = KEYSYM_VK.get(event.keysym, event.keycode)
            name = VK_NAME_MAP.get(vk, event.keysym)
            key_vars[action].set(name)
            key_btns[action].config(text=name, fg=FG_TEXT, bg=BG_BTN)
            capturing['active'] = None
            win.unbind('<KeyPress>')

        for r, (action, label_key) in enumerate(actions, start=1):
            tk.Label(fr, text=self.t(label_key), bg=BG_MAIN, fg=FG_TEXT,
                     font=FONT_MAIN, width=12, anchor='w'
                     ).grid(row=r, column=0, padx=4, pady=3, sticky='w')
            v = tk.StringVar(value=self.settings["hotkeys"][action]["name"])
            key_vars[action] = v
            b = tk.Button(fr, textvariable=v, width=16,
                          bg=BG_BTN, fg=FG_TEXT, activebackground=BG_BTN_HV,
                          relief=tk.FLAT, font=FONT_MAIN, cursor='hand2',
                          command=lambda a=action: start_capture(a))
            b.grid(row=r, column=1, padx=4, pady=3)
            key_btns[action] = b

        bot = tk.Frame(fr, bg=BG_MAIN, pady=8)
        bot.grid(row=len(actions)+1, column=0, columnspan=2)

        def save_hotkeys():
            for action, var in key_vars.items():
                name = var.get()
                vk   = VK_CODE_MAP.get(name, 0)
                self.settings["hotkeys"][action] = {"vk": vk, "name": name}
            self._save_settings()
            self._stop_global_hotkeys()
            if self._admin:
                self._start_global_hotkeys()
            else:
                self._bind_local_hotkeys()
            messagebox.showinfo(self.t('hotkey_title'),
                                self.t('hotkey_saved_msg'), parent=win)

        def reset_hotkeys():
            for action, var in key_vars.items():
                dflt = DEFAULT_SETTINGS["hotkeys"][action]["name"]
                var.set(dflt)
                key_btns[action].config(text=dflt)

        self._bot_buttons(bot,
            (self.t('hotkey_save'),  save_hotkeys,  FG_ACCENT, '#000'),
            (self.t('hotkey_reset'), reset_hotkeys, BG_BTN, FG_TEXT),
            (self.t('hotkey_close'), lambda: self._close_sub(win, '_hotkey_win'),
             BG_BTN, FG_TEXT),
        )
        self._center_window(win)

    # ══════════════════════════════════════════════════════════════════════
    # Interface settings window
    # ══════════════════════════════════════════════════════════════════════

    def _open_interface_settings(self):
        if self._iface_win and self._iface_win.winfo_exists():
            self._iface_win.lift(); return
        self._update_hint('settings')

        win = tk.Toplevel(self.root)
        self._iface_win = win
        win.title(self.t('ui_title'))
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)
        win.attributes('-topmost', True)
        self._set_icon(win)
        win.protocol("WM_DELETE_WINDOW",
                     lambda: self._close_sub(win, '_iface_win'))

        nb  = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        iface = self.settings["interface"]
        tmp: dict = copy.deepcopy(iface)

        # ── helper builders ───────────────────────────────────────────
        def _fr(parent):
            f = tk.Frame(parent, bg=BG_MAIN, padx=12, pady=8)
            f.pack(fill=tk.BOTH, expand=True)
            return f

        def _lbl(parent, row, text_key, col=0, **kw):
            tk.Label(parent, text=self.t(text_key),
                     bg=BG_MAIN, fg=FG_TEXT, font=FONT_MAIN,
                     anchor='w', width=22, **kw
                     ).grid(row=row, column=col, sticky='w', padx=4, pady=4)

        def _color_row(parent, row, label_key, cfg_key):
            _lbl(parent, row, label_key)
            v = tk.StringVar(value=tmp.get(cfg_key, '#ffffff'))
            swatch = tk.Frame(parent, bg=tmp.get(cfg_key, '#ffffff'),
                              width=28, height=16, relief=tk.SOLID, bd=1)
            def pick(k=cfg_key, sv=v, sw=swatch):
                col = colorchooser.askcolor(color=sv.get(), parent=win)[1]
                if col:
                    sv.set(col)
                    tmp[k] = col
                    sw.config(bg=col)
            btn = tk.Button(parent, text=self.t('ui_choose_color'),
                            command=pick, bg=BG_BTN, fg=FG_TEXT,
                            relief=tk.FLAT, font=FONT_HINT, cursor='hand2', padx=6)
            frame = tk.Frame(parent, bg=BG_MAIN)
            frame.grid(row=row, column=1, sticky='w', padx=4, pady=4)
            swatch.pack(in_=frame, side=tk.LEFT, padx=(0, 4))
            btn.pack(in_=frame, side=tk.LEFT)

        def _check_row(parent, row, label_key, cfg_key, default=True):
            _lbl(parent, row, label_key)
            v = tk.BooleanVar(value=tmp.get(cfg_key, default))
            cb = tk.Checkbutton(parent, variable=v, bg=BG_MAIN, fg=FG_TEXT,
                                activebackground=BG_MAIN, selectcolor=BG_BTN,
                                font=FONT_MAIN,
                                command=lambda k=cfg_key, vv=v: tmp.update({k: vv.get()}))
            cb.grid(row=row, column=1, sticky='w', padx=4, pady=4)

        def _spin_row(parent, row, label_key, cfg_key, from_, to_):
            _lbl(parent, row, label_key)
            v = tk.StringVar(value=str(tmp.get(cfg_key, from_)))
            def update(k=cfg_key, sv=v):
                try: tmp[k] = int(sv.get())
                except ValueError: pass
            sb = tk.Spinbox(parent, from_=from_, to=to_, textvariable=v,
                            width=6, bg=BG_ENTRY, fg=FG_TEXT,
                            buttonbackground=BG_BTN, relief=tk.FLAT, font=FONT_MAIN,
                            command=update)
            sb.bind('<FocusOut>', lambda e: update())
            sb.grid(row=row, column=1, sticky='w', padx=4, pady=4)

        def _opacity_row(parent, row, label_key, cfg_key):
            _lbl(parent, row, label_key)
            ov = tk.DoubleVar(value=tmp.get(cfg_key, 0.9))
            sc = tk.Scale(parent, from_=0.2, to=1.0, resolution=0.05,
                          orient=tk.HORIZONTAL, variable=ov,
                          bg=BG_MAIN, fg=FG_TEXT, troughcolor=BG_BTN,
                          highlightthickness=0, length=110,
                          command=lambda v, k=cfg_key: tmp.update({k: float(v)}))
            sc.grid(row=row, column=1, sticky='w', padx=4, pady=4)

        # ── Tab: Preview ──────────────────────────────────────────────
        t_prev = tk.Frame(nb, bg=BG_MAIN)
        nb.add(t_prev, text=f"  {self.t('ui_tab_preview')}  ")
        f = _fr(t_prev)
        _color_row(f, 0, 'ui_preview_fg',   'preview_fg')
        _check_row(f, 1, 'ui_preview_bg_on','preview_bg_on')
        _color_row(f, 2, 'ui_preview_bg',   'preview_bg')

        # ── Tab: Float ────────────────────────────────────────────────
        t_float = tk.Frame(nb, bg=BG_MAIN)
        nb.add(t_float, text=f"  {self.t('ui_tab_float')}  ")
        f = _fr(t_float)
        _check_row(f, 0, 'ui_float_bg_on',   'float_bg_on')
        _color_row(f, 1, 'ui_float_bg',       'float_bg')
        _spin_row (f, 2, 'ui_float_x',        'float_x',  0, 3840)
        _spin_row (f, 3, 'ui_float_y',        'float_y',  0, 2160)
        _opacity_row(f, 4, 'ui_float_opacity','float_opacity')
        _check_row(f, 5, 'ui_show_float_sel', 'show_float_sel', True)
        _spin_row (f, 6, 'ui_float_font_size','float_font_size', 7, 20)
        _color_row(f, 7, 'ui_float_fg',       'float_fg')
        tk.Label(f, text=self.t('ui_preview_note'),
                 bg=BG_MAIN, fg=FG_HINT, font=FONT_HINT
                 ).grid(row=8, column=0, columnspan=2, pady=4)

        # ── Tab: Buttons ──────────────────────────────────────────────
        t_btn = tk.Frame(nb, bg=BG_MAIN)
        nb.add(t_btn, text=f"  {self.t('ui_tab_buttons')}  ")
        f = _fr(t_btn)
        _color_row(f, 0, 'ui_btn_color',  'btn_color')
        _check_row(f, 1, 'ui_btn_bg_on',  'btn_bg_on')
        _check_row(f, 2, 'ui_show_hotkeys','show_hotkeys')
        _spin_row (f, 3, 'ui_btn_size',   'btn_icon_size', 24, 80)
        _spin_row (f, 4, 'ui_btn_spacing','btn_spacing', 0, 20)

        # ── Tab: Results ──────────────────────────────────────────────
        t_res = tk.Frame(nb, bg=BG_MAIN)
        nb.add(t_res, text=f"  {self.t('ui_tab_results')}  ")
        f = _fr(t_res)
        _spin_row (f, 0, 'ui_results_font_size',    'results_font_size', 7, 20)
        _color_row(f, 1, 'ui_results_fg',            'results_fg')
        _check_row(f, 2, 'ui_results_show_number',   'results_show_number', True)
        _check_row(f, 3, 'ui_results_show_estimate', 'results_show_estimate', True)

        tk.Label(f, text=self.t('ui_sort_order'),
                 bg=BG_MAIN, fg=FG_TEXT, font=FONT_MAIN
                 ).grid(row=4, column=0, sticky='w', padx=4, pady=4)
        sort_labels2  = [self.t(f'sort_{o}') for o in SORT_ORDERS]
        sort_var2     = tk.StringVar(
            value=self.t(f'sort_{self.settings["sort_order"]}'))
        ttk.Combobox(f, textvariable=sort_var2, values=sort_labels2,
                     state='readonly', width=22, font=FONT_HINT
                     ).grid(row=4, column=1, sticky='w', padx=4, pady=4)

        # ── Bottom buttons ────────────────────────────────────────────
        bot = tk.Frame(win, bg=BG_MAIN, pady=8)
        bot.pack(fill=tk.X, padx=12)

        def save_iface():
            self.settings["interface"].update(tmp)
            try:
                idx2 = sort_labels2.index(sort_var2.get())
                self.settings["sort_order"] = SORT_ORDERS[idx2]
                self.sort_var.set(sort_labels2[idx2])
            except ValueError:
                pass
            self._save_settings()
            self._rebuild_time_buttons()
            self._update_preview()
            # Refresh result tags and text
            self._configure_result_tags(tmp.get("results_fg", FG_RESULT))
            rfs = tmp.get("results_font_size", 9)
            self.results_text.config(
                font=("Consolas", rfs),
                fg=tmp.get("results_fg", FG_RESULT))
            self._update_results()
            messagebox.showinfo(self.t('ui_title'), self.t('ui_saved_msg'), parent=win)

        def reset_iface():
            nonlocal tmp
            tmp = copy.deepcopy(DEFAULT_SETTINGS["interface"])

        self._bot_buttons(bot,
            (self.t('ui_save'),  save_iface, FG_ACCENT, '#000'),
            (self.t('ui_reset'), reset_iface, BG_BTN, FG_TEXT),
            (self.t('ui_close'), lambda: self._close_sub(win, '_iface_win'), BG_BTN, FG_TEXT),
        )
        self._center_window(win)

    def _rebuild_time_buttons(self):
        for w in list(self.time_btn_widgets.values()):
            try: w.destroy()
            except Exception: pass
        self.time_btn_widgets.clear()
        self._build_time_buttons_frame()

    # ══════════════════════════════════════════════════════════════════════
    # Sponsor window
    # ══════════════════════════════════════════════════════════════════════

    def _open_sponsor(self):
        win = tk.Toplevel(self.root)
        win.title(self.t('sponsor_title'))
        win.configure(bg=BG_MAIN)
        win.resizable(False, False)
        win.attributes('-topmost', True)
        self._set_icon(win)

        fr = tk.Frame(win, bg=BG_MAIN, padx=28, pady=20)
        fr.pack(fill=tk.BOTH, expand=True)
        tk.Label(fr, text=self.t('sponsor_msg'),
                 font=FONT_MAIN, bg=BG_MAIN, fg=FG_TEXT,
                 justify=tk.CENTER).pack(pady=(0, 12))
        tk.Button(
            fr, text=self.t('sponsor_youtube'),
            command=lambda: webbrowser.open("https://www.youtube.com/@oo_jump_game"),
            bg="#c0392b", fg="#ffffff", relief=tk.FLAT,
            padx=14, pady=7, font=FONT_BTN, cursor='hand2',
        ).pack(pady=4)
        tk.Button(
            fr, text=self.t('btn_close'), command=win.destroy,
            bg=BG_BTN, fg=FG_TEXT, relief=tk.FLAT,
            padx=12, pady=4, font=FONT_MAIN, cursor='hand2',
        ).pack(pady=(10, 0))
        self._center_window(win)

    # ══════════════════════════════════════════════════════════════════════
    # Floating window
    # ══════════════════════════════════════════════════════════════════════

    def _toggle_float(self):
        if self._float_win and self._float_win.winfo_exists():
            self._close_float()
        else:
            self._open_float()

    def _open_float(self):
        iface  = self.settings["interface"]
        bg     = iface["float_bg"] if iface["float_bg_on"] else BG_MAIN
        gap    = iface["btn_spacing"]
        f_size = iface.get("float_font_size", 8)
        f_fg   = iface.get("float_fg", FG_RESULT)
        show_sel = iface.get("show_float_sel", True)

        win = tk.Toplevel(self.root)
        self._float_win = win
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.attributes('-alpha', iface["float_opacity"])
        win.configure(bg=bg)
        win.geometry(f"+{iface.get('float_x', 100)}+{iface.get('float_y', 100)}")

        # ── Icon row (drag + gear + close) ────────────────────────────
        icon_row = tk.Frame(win, bg=bg)
        icon_row.pack(fill=tk.X, padx=2, pady=(2, 0))

        icon_sz = 20
        move_path = os.path.join(PNG_DIR, "Set_Arrow_keys.png")
        gear_path = os.path.join(PNG_DIR, "Set_gear.png")

        if PIL_AVAILABLE and os.path.exists(move_path):
            img = Image.open(move_path).resize((icon_sz, icon_sz), Image.LANCZOS)
            self._img_move = ImageTk.PhotoImage(img)
            move_lbl = tk.Label(icon_row, image=self._img_move, bg=bg, cursor='fleur')
        else:
            move_lbl = tk.Label(icon_row, text='✥', bg=bg, fg=FG_HINT,
                                font=("Arial", 13), cursor='fleur')
        move_lbl.pack(side=tk.LEFT, padx=(2, 1))
        move_lbl.bind('<ButtonPress-1>', self._float_drag_start)
        move_lbl.bind('<B1-Motion>',     self._float_drag_move)

        if PIL_AVAILABLE and os.path.exists(gear_path):
            img2 = Image.open(gear_path).resize((icon_sz, icon_sz), Image.LANCZOS)
            self._img_gear = ImageTk.PhotoImage(img2)
            gear_lbl = tk.Label(icon_row, image=self._img_gear, bg=bg, cursor='hand2')
        else:
            gear_lbl = tk.Label(icon_row, text='⚙', bg=bg, fg=FG_HINT,
                                font=("Arial", 12), cursor='hand2')
        gear_lbl.pack(side=tk.LEFT, padx=(0, 4))
        gear_lbl.bind('<Button-1>', lambda e: self._float_gear_click())

        close_lbl = tk.Label(icon_row, text='✕', bg=bg, fg=FG_MUTED,
                             font=("Arial", 10), cursor='hand2')
        close_lbl.pack(side=tk.RIGHT, padx=2)
        close_lbl.bind('<Button-1>', lambda e: self._close_float())

        # ── Preview slots (4) ─────────────────────────────────────────
        slot_fg = iface["preview_fg"]
        slot_bg = iface["preview_bg"] if iface["preview_bg_on"] else bg
        prev_row = tk.Frame(win, bg=bg)
        prev_row.pack(fill=tk.X, padx=2, pady=(0, 1))
        self._float_slots: list[tk.Label] = []
        for i in range(4):
            txt = (self.selected[i] if i < len(self.selected)
                   else self.t('preview_empty'))
            fg_now = slot_fg if i < len(self.selected) else FG_MUTED
            lbl = tk.Label(prev_row, text=txt, width=5, bg=slot_bg,
                           fg=fg_now, font=(FONT_FAMILY, f_size, "bold"),
                           relief=tk.FLAT, cursor='hand2')
            lbl.pack(side=tk.LEFT, padx=1, pady=1)
            lbl.bind('<Button-1>', lambda e, idx=i: self._on_preview_click(idx))
            self._float_slots.append(lbl)

        # ── Time buttons 4×2 (shown only if show_float_sel) ──────────
        if show_sel:
            btn_row = tk.Frame(win, bg=bg)
            btn_row.pack(padx=2, pady=(1, 1))
            btn_fg  = iface["btn_color"]
            btn_bg2 = BG_BTN if iface["btn_bg_on"] else bg
            self._float_btns: dict[str, tk.Button] = {}
            for idx, (label_key, name) in enumerate(TIME_BUTTONS):
                b = tk.Button(
                    btn_row, text=self.t(label_key), width=5,
                    bg=btn_bg2, fg=btn_fg,
                    activebackground=BG_BTN_HV, activeforeground=FG_TEXT,
                    relief=tk.FLAT, font=(FONT_FAMILY, f_size, "bold"),
                    cursor='hand2',
                    command=lambda n=name: self._on_time_btn(n))
                b.grid(row=idx // 4, column=idx % 4,
                       padx=gap, pady=gap, sticky='nsew')
                self._float_btns[name] = b
        else:
            self._float_btns = {}

        # ── Results section ────────────────────────────────────────────
        sep = tk.Frame(win, bg=BORDER, height=1)
        sep.pack(fill=tk.X, padx=4, pady=(2, 0))

        res_frame = tk.Frame(win, bg=bg)
        res_frame.pack(fill=tk.BOTH, expand=True, padx=2, pady=(0, 2))

        res_sb = tk.Scrollbar(res_frame, orient=tk.VERTICAL, bg=BG_CARD, width=8)
        res_sb.pack(side=tk.RIGHT, fill=tk.Y)

        self._float_res_txt = tk.Text(
            res_frame, bg=bg, fg=f_fg,
            font=("Consolas", f_size),
            relief=tk.FLAT, bd=0,
            state=tk.DISABLED, wrap=tk.NONE,
            yscrollcommand=res_sb.set,
            height=7, width=34,
            padx=4, pady=2)
        self._float_res_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        res_sb.config(command=self._float_res_txt.yview)

        self._float_res_txt.tag_configure('header',      foreground=FG_RESULT_H)
        self._float_res_txt.tag_configure('col_num',     foreground=FG_HINT)
        self._float_res_txt.tag_configure('col_range',   foreground=FG_TEXT)
        self._float_res_txt.tag_configure('col_action',  foreground=FG_WHITE)
        self._float_res_txt.tag_configure('col_estimate',foreground=f_fg)
        self._float_res_txt.tag_configure('muted',       foreground=FG_MUTED)
        self._float_res_txt.tag_configure('newline',     foreground=f_fg)

        self._float_update_results()

    def _close_float(self):
        if self._float_win and self._float_win.winfo_exists():
            try:
                self.settings["interface"]["float_x"] = self._float_win.winfo_x()
                self.settings["interface"]["float_y"] = self._float_win.winfo_y()
            except Exception:
                pass
            self._float_win.destroy()
        self._float_win = None

    def _float_drag_start(self, event):
        self._float_drag_x = event.x_root - self._float_win.winfo_x()
        self._float_drag_y = event.y_root - self._float_win.winfo_y()

    def _float_drag_move(self, event):
        x = event.x_root - self._float_drag_x
        y = event.y_root - self._float_drag_y
        self._float_win.geometry(f'+{x}+{y}')

    def _float_gear_click(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _float_update_preview(self):
        if not (self._float_win and self._float_win.winfo_exists()):
            return
        iface   = self.settings["interface"]
        slot_fg = iface["preview_fg"]
        slot_bg = iface["preview_bg"] if iface["preview_bg_on"] else \
                  (iface["float_bg"] if iface["float_bg_on"] else BG_MAIN)
        for i, lbl in enumerate(self._float_slots):
            if i < len(self.selected):
                lbl.config(text=self.selected[i], fg=slot_fg, bg=slot_bg)
            else:
                lbl.config(text=self.t('preview_empty'), fg=FG_MUTED, bg=slot_bg)

    def _float_update_results(self):
        if not (self._float_win and self._float_win.winfo_exists()):
            return
        if not hasattr(self, '_float_res_txt'):
            return
        iface        = self.settings["interface"]
        show_number  = iface.get("results_show_number",   True)
        show_estimate= iface.get("results_show_estimate", True)
        txt = self._float_res_txt
        txt.config(state=tk.NORMAL)
        txt.delete('1.0', tk.END)
        if not self.selected:
            txt.insert(tk.END, self.t('results_empty'), 'muted')
        else:
            order  = self.settings["sort_order"]
            tagged = compute_tagged_results(
                self.selected, order, self.lang, show_number, show_estimate)
            for text_part, tag in tagged:
                txt.insert(tk.END, text_part, tag)
        txt.config(state=tk.DISABLED)

    # ══════════════════════════════════════════════════════════════════════
    # Utilities
    # ══════════════════════════════════════════════════════════════════════

    def _bot_buttons(self, parent, *spec):
        """Add a row of (label, command, bg, fg) buttons."""
        for label, cmd, bg, fg in spec:
            tk.Button(parent, text=label, command=cmd,
                      bg=bg, fg=fg, relief=tk.FLAT, font=FONT_BTN,
                      cursor='hand2', padx=10, pady=4
                      ).pack(side=tk.LEFT, padx=4)

    def _close_sub(self, win, attr: str):
        try: win.destroy()
        except Exception: pass
        setattr(self, attr, None)
        self._update_hint()

    def _center_window(self, win: tk.Toplevel):
        win.update_idletasks()
        w, h = win.winfo_reqwidth(), win.winfo_reqheight()
        sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
        win.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _set_icon(self, win: tk.Toplevel):
        if os.path.exists(ICON_PATH):
            try: win.iconbitmap(ICON_PATH)
            except Exception: pass

    def _on_close(self):
        self._save_settings()
        self._stop_global_hotkeys()
        self._close_float()
        self.root.destroy()


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    ArtaleTimerPlayer()
