import os
import subprocess
import json
import datetime
import glob
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")


def _hidden_subprocess_args():
    """Kwargs untuk subprocess agar tidak muncul jendela sama sekali."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": si,
        "stdin": subprocess.DEVNULL,
    }


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_time_period(config):
    now = datetime.datetime.now()
    t = now.hour + now.minute / 60
    schedule = config["schedule"]
    morning_start = schedule.get("morning", 6.0)
    day_start = schedule.get("day", 10.0)
    sunset_start = schedule.get("sunset", 17.0)
    night_start = schedule.get("night", 19.0)

    if morning_start <= t < day_start: return "morning"
    elif day_start <= t < sunset_start: return "day"
    elif sunset_start <= t < night_start: return "sunset"
    else: return "night"


def get_lively_exe():
    """Cari Lively.exe tanpa memunculkan window."""
    # Coba dari proses yang sedang berjalan via PowerShell (fully hidden)
    try:
        proc = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
                "-Command",
                "(Get-Process lively -ErrorAction SilentlyContinue | "
                "Select-Object -ExpandProperty Path | Select-Object -First 1)",
            ],
            capture_output=True, text=True, check=True,
            **_hidden_subprocess_args(),
        )
        path = proc.stdout.strip()
        if path and os.path.exists(path):
            return path
    except Exception:
        pass

    # Fallback: cari langsung di WindowsApps
    base_path = r"C:\Program Files\WindowsApps"
    search_pattern = os.path.join(
        base_path, "12030rocksdanister.LivelyWallpaper_*", "Build", "Lively.exe"
    )
    matches = glob.glob(search_pattern)
    if matches:
        return matches[0]

    return None


def set_lively_wallpaper(video_path):
    """Set wallpaper via Lively CLI tanpa window."""
    lively_exe = get_lively_exe()
    if not lively_exe:
        return False

    subprocess.run(
        [lively_exe, "setwp", "--file", video_path],
        capture_output=True,
        **_hidden_subprocess_args(),
    )
    return True


def main():
    config = load_config()
    current_period = get_time_period(config)
    video_file = config["videos"].get(current_period)
    video_path = os.path.join(SCRIPT_DIR, video_file)

    if not os.path.isfile(video_path):
        return

    set_lively_wallpaper(video_path)
    
    # Bersihkan file sampah thumbnail {GUID}.png yang kadang dibuat oleh Lively
    for f in glob.glob(os.path.join(SCRIPT_DIR, "{*}.png")):
        try:
            os.remove(f)
        except Exception:
            pass

if __name__ == "__main__":
    main()
