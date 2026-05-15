import base64
import difflib
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path

import psutil
import pyautogui
import pyperclip
from groq import Groq
from PIL import ImageGrab

from config import GROQ_API_KEY

# Mouse corner pe jaane se emergency stop
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05  # Actions ke beech mini delay

# ─── APP MAP ─────────────────────────────────────────────────────────────────
APP_MAP = {
    # Browsers
    "chrome":           "chrome",
    "google chrome":    "chrome",
    "edge":             "msedge",
    "firefox":          "firefox",
    # Media
    "spotify":          "spotify",
    "vlc":              "vlc",
    "youtube":          "chrome --new-tab https://youtube.com",
    # Dev tools
    "vs code":          "code",
    "vscode":           "code",
    "visual studio code": "code",
    "terminal":         "wt",           # Windows Terminal
    "cmd":              "cmd",
    "powershell":       "powershell",
    # Productivity
    "notepad":          "notepad",
    "calculator":       "calc",
    "paint":            "mspaint",
    "word":             "winword",
    "excel":            "excel",
    "powerpoint":       "powerpnt",
    # System
    "file explorer":    "explorer",
    "explorer":         "explorer",
    "task manager":     "taskmgr",
    "control panel":    "control",
    "settings":         "ms-settings:",
    # Social
    "whatsapp":         "whatsapp",
    "telegram":         "telegram",
    "discord":          "discord",
    # Sites (Chrome mein khulenge)
    "instagram":        "chrome --new-tab https://instagram.com",
    "facebook":         "chrome --new-tab https://facebook.com",
    "github":           "chrome --new-tab https://github.com",
    "gmail":            "chrome --new-tab https://mail.google.com",
    "maps":             "chrome --new-tab https://maps.google.com",
    "chatgpt":          "chrome --new-tab https://chat.openai.com",
}

# Process names for killing (app_key → process name)
PROCESS_MAP = {
    "chrome":       ["chrome.exe"],
    "spotify":      ["spotify.exe"],
    "vs code":      ["code.exe"],
    "vscode":       ["code.exe"],
    "notepad":      ["notepad.exe"],
    "calculator":   ["calculatorapp.exe", "calc.exe"],
    "whatsapp":     ["whatsapp.exe"],
    "telegram":     ["telegram.exe"],
    "discord":      ["discord.exe"],
    "vlc":          ["vlc.exe"],
    "firefox":      ["firefox.exe"],
    "edge":         ["msedge.exe"],
    "paint":        ["mspaint.exe"],
}


# ─── HELPERS ─────────────────────────────────────────────────────────────────
def _resolve_app_key(app_name: str):
    """App name se best matching key nikalo."""
    key = (app_name or "").strip().lower()
    if not key:
        return None
    if key in APP_MAP:
        return key
    # Fuzzy match
    matches = difflib.get_close_matches(key, APP_MAP.keys(), n=1, cutoff=0.45)
    if matches:
        return matches[0]
    # Substring match
    for candidate in APP_MAP:
        if key in candidate or candidate in key:
            return candidate
    return None


# ─── OPEN APP ────────────────────────────────────────────────────────────────
def open_app(app_name: str) -> str:
    try:
        match = _resolve_app_key(app_name)
        if not match:
            return f"'{app_name}' app map mein nahi mila bhai. Available apps: {', '.join(list(APP_MAP.keys())[:10])}..."

        command = APP_MAP[match]

        # ms-settings jaise URI scheme handle karo
        if command.startswith("ms-"):
            subprocess.Popen(f"start {command}", shell=True)
        else:
            subprocess.Popen(command, shell=True)

        time.sleep(0.5)
        return f"'{match}' khul gaya bhai! 🚀"
    except Exception as e:
        return f"Arre bhai '{app_name}' kholne mein gadbad: {e}"


# ─── CLOSE APP ───────────────────────────────────────────────────────────────
def close_app(app_name: str) -> str:
    try:
        match = _resolve_app_key(app_name) or app_name.strip().lower()
        process_names = PROCESS_MAP.get(match, [f"{match}.exe", match])
        killed = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                proc_name = (proc.info.get("name") or "").lower()
                cmdline = " ".join(proc.info.get("cmdline") or []).lower()
                for pname in process_names:
                    if pname.lower() in proc_name or pname.lower() in cmdline:
                        proc.kill()
                        killed += 1
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        if killed == 0:
            return f"'{app_name}' ka koi running process nahi mila bhai."
        return f"'{app_name}' band kar diya bhai! ({killed} process kill kiye)"
    except Exception as e:
        return f"Arre bhai '{app_name}' band karne mein gadbad: {e}"


# ─── FOCUS / SWITCH WINDOW ───────────────────────────────────────────────────
def focus_window(app_name: str) -> str:
    """Running window ko foreground mein laao."""
    try:
        import pygetwindow as gw
        key = (app_name or "").lower()
        windows = gw.getAllTitles()
        matches = [w for w in windows if key in w.lower() and w.strip()]
        if not matches:
            return f"'{app_name}' ki koi open window nahi mili bhai."
        win = gw.getWindowsWithTitle(matches[0])[0]
        win.activate()
        time.sleep(0.3)
        return f"'{matches[0]}' window focus mein aa gaya bhai!"
    except Exception as e:
        return f"Window focus error: {e}"


# ─── SCREENSHOT ──────────────────────────────────────────────────────────────
def take_screenshot(region=None) -> str:
    """
    Screen ka screenshot lo.
    region: (x, y, width, height) ya None for full screen
    """
    try:
        root_dir = Path(__file__).resolve().parents[1]
        shots_dir = root_dir / "screenshots"
        shots_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        file_path = shots_dir / f"shot-{timestamp}.png"

        if region:
            x, y, w, h = region
            img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
        else:
            img = ImageGrab.grab()

        img.save(file_path)
        return str(file_path)
    except Exception as e:
        return f"Arre bhai screenshot mein gadbad: {e}"


# ─── SCREEN ANALYZE ──────────────────────────────────────────────────────────
def analyze_screen(question="Is screenshot mein kya dikh raha hai? Hinglish mein bata.") -> str:
    """Screenshot lo aur Groq vision se analyze karo."""
    try:
        shot_path = take_screenshot()
        if shot_path.startswith("Arre"):
            return shot_path
        if not GROQ_API_KEY:
            return "GROQ_API_KEY missing hai bhai."

        with open(shot_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")

        client = Groq(api_key=GROQ_API_KEY)
        result = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{encoded}"}}
                ]
            }],
            max_tokens=512,
            temperature=0.4,
        )
        return (result.choices[0].message.content or "Screen analysis blank aa gaya bhai.").strip()
    except Exception as e:
        return f"Screen analyze error: {e}"


# ─── KEYBOARD TYPE ───────────────────────────────────────────────────────────
def keyboard_type(text: str, press_enter=False) -> str:
    """Text type karo — clipboard paste method use karta hai special chars ke liye."""
    try:
        if not text:
            return "Type karne ke liye text de bhai."
        pyperclip.copy(str(text))
        time.sleep(0.1)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        if press_enter:
            pyautogui.press("enter")
        return f"Type kar diya bhai: '{text[:50]}{'...' if len(text) > 50 else ''}'"
    except Exception as e:
        return f"Type error: {e}"


def copy_to_clipboard(text: str) -> str:
    try:
        pyperclip.copy(text or "")
        return "Clipboard mein copy kar diya bhai."
    except Exception as e:
        return f"Arre bhai clipboard copy error: {e}"


def get_clipboard() -> str:
    try:
        content = pyperclip.paste()
        if not content:
            return "Clipboard abhi khali hai bhai."
        return f"Clipboard mein ye hai bhai: {content}"
    except Exception as e:
        return f"Arre bhai clipboard read error: {e}"


def get_system_info() -> str:
    try:
        cpu = psutil.cpu_percent(interval=0.5)
        vm = psutil.virtual_memory()
        battery = psutil.sensors_battery()
        battery_text = (
            f"{battery.percent}% {'(charging)' if battery.power_plugged else '(on battery)'}"
            if battery
            else "battery info available nahi hai"
        )
        return (
            f"System info bhai: CPU {cpu}%, RAM {vm.percent}% "
            f"({round(vm.used / (1024 ** 3), 1)}GB/{round(vm.total / (1024 ** 3), 1)}GB), "
            f"Battery {battery_text}."
        )
    except Exception as e:
        return f"Arre bhai system info nikalne mein error: {e}"


# ─── KEY PRESS ───────────────────────────────────────────────────────────────
def press_key(key: str) -> str:
    """
    Single ya combo key press karo.
    Examples: 'enter', 'ctrl+c', 'alt+tab', 'win+d'
    """
    try:
        key = key.strip().lower()
        if "+" in key:
            parts = [p.strip() for p in key.split("+")]
            pyautogui.hotkey(*parts)
        else:
            pyautogui.press(key)
        return f"Key '{key}' press kar diya bhai!"
    except Exception as e:
        return f"Key press error: {e}"


# ─── MOUSE CLICK ─────────────────────────────────────────────────────────────
def mouse_click(x=None, y=None, button="left", double=False) -> str:
    """Mouse click karo — coordinates ya current position pe."""
    try:
        if x is not None and y is not None:
            pyautogui.moveTo(x, y, duration=0.2)
        if double:
            pyautogui.doubleClick()
        else:
            pyautogui.click(button=button)
        pos = pyautogui.position()
        return f"{'Double c' if double else 'C'}lick kar diya bhai at ({pos.x}, {pos.y})!"
    except Exception as e:
        return f"Click error: {e}"


# ─── SCROLL ──────────────────────────────────────────────────────────────────
def scroll(direction="down", amount=3) -> str:
    """Page scroll karo."""
    try:
        clicks = amount if direction == "up" else -amount
        pyautogui.scroll(clicks)
        return f"Scroll {direction} kar diya bhai!"
    except Exception as e:
        return f"Scroll error: {e}"


# ─── VOLUME CONTROL ──────────────────────────────────────────────────────────
def volume_control(action: str) -> str:
    """Volume up/down/mute control."""
    try:
        action = (action or "").strip().lower()
        steps = 3

        if action in ("up", "badhao", "zyada"):
            for _ in range(steps):
                pyautogui.press("volumeup")
                time.sleep(0.05)
            return "Volume up kar diya bhai! 🔊"

        if action in ("down", "kam", "ghata"):
            for _ in range(steps):
                pyautogui.press("volumedown")
                time.sleep(0.05)
            return "Volume down kar diya bhai! 🔉"

        if action in ("mute", "band", "chup"):
            pyautogui.press("volumemute")
            return "Volume mute kar diya bhai! 🔇"

        if action in ("unmute", "chalu"):
            pyautogui.press("volumemute")
            return "Volume unmute kar diya bhai! 🔊"

        return f"Volume action '{action}' samajh nahi aaya bhai. 'up', 'down', ya 'mute' bol."
    except Exception as e:
        return f"Volume control error: {e}"


# ─── SYSTEM ACTIONS ──────────────────────────────────────────────────────────
def system_action(action: str) -> str:
    """Lock, sleep, restart, shutdown."""
    try:
        action = action.strip().lower()
        if action in ("lock", "lock karo"):
            subprocess.run("rundll32.exe user32.dll,LockWorkStation", shell=True)
            return "PC lock kar diya bhai!"
        if action in ("sleep", "so ja"):
            subprocess.run("rundll32.exe powrprof.dll,SetSuspendState 0,1,0", shell=True)
            return "PC sleep mein bhej diya bhai!"
        if action in ("restart", "reboot"):
            subprocess.run("shutdown /r /t 30", shell=True)
            return "PC 30 seconds mein restart hoga bhai!"
        if action in ("shutdown", "band karo"):
            subprocess.run("shutdown /s /t 30", shell=True)
            return "PC 30 seconds mein shutdown hoga bhai!"
        return f"System action '{action}' samajh nahi aaya bhai."
    except Exception as e:
        return f"System action error: {e}"


# ─── GET MOUSE POSITION ──────────────────────────────────────────────────────
def get_mouse_pos() -> str:
    pos = pyautogui.position()
    return f"Mouse abhi ({pos.x}, {pos.y}) pe hai bhai."


# ─── TEST ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print(take_screenshot())
    print(volume_control("up"))
    print(get_mouse_pos())
