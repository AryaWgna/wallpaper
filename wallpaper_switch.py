"""
wallpaper_switch.py - Ganti wallpaper Windows berdasarkan waktu.

Mengambil satu frame dari video yang sesuai dengan waktu sekarang,
lalu set sebagai wallpaper desktop DAN lock screen.

Jadwal default:
    06:00 - 10:00  morning
    10:00 - 17:00  day
    17:00 - 19:30  sunset
    19:30 - 06:00  night
"""

import ctypes
import datetime
import json
import os
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _no_window_kwargs():
    """Kwargs untuk subprocess agar tidak muncul jendela sama sekali."""
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 0  # SW_HIDE
    return {"creationflags": 0x08000000, "startupinfo": si}

CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
FRAMES_DIR = os.path.join(SCRIPT_DIR, "frames")

# Windows constants untuk SystemParametersInfoW
SPI_SETDESKWALLPAPER = 0x0014
SPIF_UPDATEINIFILE = 0x01
SPIF_SENDWININICHANGE = 0x02

# Wallpaper style registry values
WALLPAPER_STYLES = {
    "center":  ("0", "0"),
    "tile":    ("0", "1"),
    "stretch": ("2", "0"),
    "fit":     ("6", "0"),
    "fill":    ("10", "0"),
    "span":    ("22", "0"),
}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_time_period(config):
    """Tentukan periode waktu berdasarkan jam sekarang."""
    now = datetime.datetime.now()
    t = now.hour + now.minute / 60

    schedule = config["schedule"]
    morning_start = schedule.get("morning", 6.0)
    day_start = schedule.get("day", 10.0)
    sunset_start = schedule.get("sunset", 17.0)
    night_start = schedule.get("night", 19.5)

    if morning_start <= t < day_start:
        return "morning"
    elif day_start <= t < sunset_start:
        return "day"
    elif sunset_start <= t < night_start:
        return "sunset"
    else:
        return "night"


def extract_frame(video_path, output_path, position=0.5):
    """
    Ambil satu frame dari video menggunakan ffmpeg.
    position: posisi dalam video (0.0 = awal, 1.0 = akhir)
    """
    # Dapatkan durasi video
    probe_cmd = [
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "csv=p=0",
        video_path,
    ]

    try:
        result = subprocess.run(probe_cmd, capture_output=True, text=True, check=True, **_no_window_kwargs())
        duration = float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError, FileNotFoundError):
        # Fallback: ambil frame di detik ke-1
        duration = 2.0

    timestamp = duration * position

    extract_cmd = [
        "ffmpeg", "-y",
        "-ss", f"{timestamp:.2f}",
        "-i", video_path,
        "-frames:v", "1",
        "-q:v", "2",
        output_path,
    ]

    subprocess.run(extract_cmd, capture_output=True, check=True, **_no_window_kwargs())


def set_wallpaper_style(style_name):
    """Set wallpaper display style via registry."""
    import winreg

    style, tile = WALLPAPER_STYLES.get(style_name, ("10", "0"))

    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER,
        r"Control Panel\Desktop",
        0,
        winreg.KEY_SET_VALUE,
    )
    winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, style)
    winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, tile)
    winreg.CloseKey(key)


def set_wallpaper(image_path):
    """Set gambar sebagai wallpaper desktop Windows."""
    abs_path = os.path.abspath(image_path)

    result = ctypes.windll.user32.SystemParametersInfoW(
        SPI_SETDESKWALLPAPER,
        0,
        abs_path,
        SPIF_UPDATEINIFILE | SPIF_SENDWININICHANGE,
    )

    if not result:
        print(f"[ERROR] Gagal set desktop wallpaper: {abs_path}")
        sys.exit(1)


def set_lockscreen(image_path):
    """Set gambar sebagai lock screen Windows via PowerShell WinRT API."""
    abs_path = os.path.abspath(image_path).replace("\\", "\\\\")

    ps_script = f'''
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
    $_.Name -eq 'AsTask' -and
    $_.GetParameters().Count -eq 1 -and
    $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
}})[0]

Function Await($WinRtTask, $ResultType) {{
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    $netTask.Result
}}

[Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType=WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType=WindowsRuntime] | Out-Null

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync("{abs_path}")) ([Windows.Storage.StorageFile])
Await ([Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file)) ([Windows.Foundation.IPropertyValue])
'''

    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
        capture_output=True, text=True, **_no_window_kwargs()
    )

    if result.returncode != 0:
        # Fallback: coba via registry (butuh path gambar yang valid)
        print(f"  [WARN] Lock screen via WinRT gagal, coba registry...")
        try:
            import winreg
            key = winreg.CreateKeyEx(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\PersonalizationCSP",
                0,
                winreg.KEY_SET_VALUE | winreg.KEY_WRITE,
            )
            abs_real = os.path.abspath(image_path)
            winreg.SetValueEx(key, "LockScreenImagePath", 0, winreg.REG_SZ, abs_real)
            winreg.SetValueEx(key, "LockScreenImageUrl", 0, winreg.REG_SZ, abs_real)
            winreg.SetValueEx(key, "LockScreenImageStatus", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            print("  Lock   : Lock screen diganti via registry!")
        except PermissionError:
            print("  [WARN] Lock screen butuh akses admin untuk fallback registry")
        except Exception as e:
            print(f"  [WARN] Lock screen gagal: {e}")
    else:
        print("  Lock   : Lock screen berhasil diganti!")


def main():
    config = load_config()
    period = get_time_period(config)

    video_file = config["videos"].get(period)
    if not video_file:
        print(f"[ERROR] Tidak ada video untuk periode '{period}' di config.json")
        sys.exit(1)

    video_path = os.path.join(SCRIPT_DIR, video_file)
    if not os.path.isfile(video_path):
        print(f"[ERROR] Video tidak ditemukan: {video_path}")
        print("        Taruh video di folder 'videos/' atau update config.json")
        sys.exit(1)

    os.makedirs(FRAMES_DIR, exist_ok=True)

    frame_path = os.path.join(FRAMES_DIR, f"{period}.jpg")
    frame_position = config.get("frame_position", 0.5)

    print(f"[{datetime.datetime.now().strftime('%H:%M')}] Periode: {period}")
    print(f"  Video  : {video_file}")
    print(f"  Frame  : {frame_path}")

    extract_frame(video_path, frame_path, frame_position)

    if "--lockscreen-only" not in sys.argv:
        style = config.get("wallpaper_style", "fill")
        set_wallpaper_style(style)
        set_wallpaper(frame_path)
        print("  Desktop: Wallpaper berhasil diganti!")
    else:
        print("  Desktop: Skip desktop wallpaper (--lockscreen-only)")

    set_lockscreen(frame_path)


if __name__ == "__main__":
    main()
