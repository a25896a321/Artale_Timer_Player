# -*- coding: utf-8 -*-
"""
Artale Timer Player — Windows VK Hotkey System
Reference: New_Countdown_Timer/vk_hotkey.py (oo_jump)

Uses GetAsyncKeyState polling to detect global key presses
without requiring Administrator / RegisterHotKey.
"""

import ctypes
import threading
import time

# ── Windows VK Code table (code → name) ────────────────────────────────────
VK_CODES: dict = {
    # Function keys
    0x70: "F1",  0x71: "F2",  0x72: "F3",  0x73: "F4",
    0x74: "F5",  0x75: "F6",  0x76: "F7",  0x77: "F8",
    0x78: "F9",  0x79: "F10", 0x7A: "F11", 0x7B: "F12",

    # Main keyboard digits
    0x30: "0", 0x31: "1", 0x32: "2", 0x33: "3", 0x34: "4",
    0x35: "5", 0x36: "6", 0x37: "7", 0x38: "8", 0x39: "9",

    # Letters
    0x41: "A", 0x42: "B", 0x43: "C", 0x44: "D", 0x45: "E",
    0x46: "F", 0x47: "G", 0x48: "H", 0x49: "I", 0x4A: "J",
    0x4B: "K", 0x4C: "L", 0x4D: "M", 0x4E: "N", 0x4F: "O",
    0x50: "P", 0x51: "Q", 0x52: "R", 0x53: "S", 0x54: "T",
    0x55: "U", 0x56: "V", 0x57: "W", 0x58: "X", 0x59: "Y",
    0x5A: "Z",

    # NumPad digits (distinct VK codes from main keyboard)
    0x60: "NumPad0", 0x61: "NumPad1", 0x62: "NumPad2", 0x63: "NumPad3",
    0x64: "NumPad4", 0x65: "NumPad5", 0x66: "NumPad6", 0x67: "NumPad7",
    0x68: "NumPad8", 0x69: "NumPad9",

    # NumPad operators
    0x6A: "NumPad*",
    0x6B: "NumPad+",
    0x6D: "NumPad-",
    0x6E: "NumPad.",
    0x6F: "NumPad/",

    # Main keyboard punctuation
    0xBA: ";",  0xBB: "=",  0xBC: ",",  0xBD: "-",
    0xBE: ".",  0xBF: "/",  0xC0: "`",
    0xDB: "[",  0xDC: "\\", 0xDD: "]",  0xDE: "'",

    # Control keys
    0x08: "Backspace", 0x09: "Tab",  0x0D: "Enter",
    0x10: "Shift",     0x11: "Ctrl", 0x12: "Alt",
    0x1B: "Escape",    0x20: "Space",

    # Navigation
    0x21: "PageUp", 0x22: "PageDown", 0x23: "End",    0x24: "Home",
    0x25: "Left",   0x26: "Up",       0x27: "Right",  0x28: "Down",
    0x2D: "Insert", 0x2E: "Delete",

    # Toggle keys
    0x90: "NumLock", 0x91: "ScrollLock",
}

# Reverse mapping: name → code
VK_NAME_TO_CODE: dict = {v: k for k, v in VK_CODES.items()}


def get_vk_display_name(vk_name: str) -> str:
    """Return a compact user-facing label for a VK name."""
    if not vk_name:
        return ""
    if vk_name.startswith("NumPad"):
        return "Num" + vk_name[6:]
    return vk_name


def get_vk_code_from_name(vk_name: str) -> int:
    return VK_NAME_TO_CODE.get(vk_name, 0)


def get_vk_name_from_code(vk_code: int) -> str:
    return VK_CODES.get(vk_code, "")


# ── Global hotkey listener (polling) ────────────────────────────────────────

class VKHotkeyListener:
    """
    Background-thread hotkey listener using GetAsyncKeyState.

    Works for all users (no Administrator / RegisterHotKey needed).
    Calls callback(vk_code: int, vk_name: str) on every key-down event.
    """

    POLL_INTERVAL = 0.015  # seconds between polls (~67 Hz)

    def __init__(self, callback):
        self.callback = callback
        self.running  = False
        self.thread   = None
        try:
            self.user32 = ctypes.windll.user32
            self.GetAsyncKeyState = self.user32.GetAsyncKeyState
            self.GetAsyncKeyState.argtypes = [ctypes.c_int]
            self.GetAsyncKeyState.restype  = ctypes.c_short
        except Exception as e:
            print(f"[VKHotkeyListener] init failed: {e}")
            self.user32 = None

    def start(self) -> bool:
        if not self.user32:
            return False
        if self.running:
            return True
        self.running = True
        self.thread  = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None

    def is_running(self) -> bool:
        return self.running

    def _loop(self):
        pressed = set()
        while self.running:
            try:
                for vk_code, vk_name in VK_CODES.items():
                    state = self.GetAsyncKeyState(vk_code)
                    if state & 0x8000:
                        if vk_code not in pressed:
                            pressed.add(vk_code)
                            try:
                                self.callback(vk_code, vk_name)
                            except Exception as e:
                                print(f"[VKHotkeyListener] callback error: {e}")
                    else:
                        pressed.discard(vk_code)
                time.sleep(self.POLL_INTERVAL)
            except Exception as e:
                print(f"[VKHotkeyListener] loop error: {e}")
                time.sleep(0.1)


# ── One-shot key capture (for hotkey assignment dialogs) ─────────────────────

class VKCaptureSingleKey:
    """
    Captures exactly one key press (for hotkey assignment UI).
    Waits 300 ms for any currently-held keys to release, then
    fires callback(vk_code, vk_name) on the first new key down.
    """

    POLL_INTERVAL = 0.01

    def __init__(self, callback):
        self.callback = callback
        self.running  = False
        self.thread   = None
        try:
            self.user32 = ctypes.windll.user32
            self.GetAsyncKeyState = self.user32.GetAsyncKeyState
            self.GetAsyncKeyState.argtypes = [ctypes.c_int]
            self.GetAsyncKeyState.restype  = ctypes.c_short
        except Exception:
            self.user32 = None

    def start_capture(self) -> bool:
        if not self.user32:
            return False
        self.running = True
        self.thread  = threading.Thread(target=self._capture, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        self.running = False

    def _capture(self):
        # Brief delay so the button-click key-up doesn't trigger immediately
        time.sleep(0.3)
        while self.running:
            try:
                for vk_code, vk_name in VK_CODES.items():
                    state = self.GetAsyncKeyState(vk_code)
                    if state & 0x8001:   # newly pressed
                        self.running = False
                        try:
                            self.callback(vk_code, vk_name)
                        except Exception as e:
                            print(f"[VKCaptureSingleKey] callback error: {e}")
                        return
                time.sleep(self.POLL_INTERVAL)
            except Exception as e:
                print(f"[VKCaptureSingleKey] capture error: {e}")
                time.sleep(0.1)
