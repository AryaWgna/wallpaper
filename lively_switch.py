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
    import shutil
    
    # 1. Coba App Execution Alias (Jika sudah diaktifkan di Settings -> App execution aliases)
    if shutil.which("lively.exe"):
        return shutil.which("lively.exe")
    elif shutil.which("lively"):
        return shutil.which("lively")

    # 2. Coba dari proses yang sedang berjalan via PowerShell (fully hidden)
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

    # 3. Fallback: cari langsung di WindowsApps (Bisa menyebabkan PermissionError)
    base_path = r"C:\Program Files\WindowsApps"
    search_pattern = os.path.join(
        base_path, "12030rocksdanister.LivelyWallpaper_*", "Build", "Lively.exe"
    )
    matches = glob.glob(search_pattern)
    if matches:
        return matches[0]

    return None


def _get_lively_aumid():
    """Cari AUMID (Application User Model ID) Lively dari AppX package."""
    try:
        proc = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
                "-Command",
                "(Get-AppxPackage | Where-Object { $_.Name -match 'LivelyWallpaper' } | "
                "ForEach-Object { $_.PackageFamilyName + '!App' } | Select-Object -First 1)",
            ],
            capture_output=True, text=True, check=True,
            **_hidden_subprocess_args(),
        )
        aumid = proc.stdout.strip()
        if aumid:
            return aumid
    except Exception:
        pass
    return None


def _activate_via_com(aumid, cli_args):
    """Jalankan Lively MS Store via COM ApplicationActivationManager (hidden)."""
    ps_script = f'''
Add-Type -TypeDefinition @"
using System;
using System.Runtime.InteropServices;

public class AppActivator {{
    [DllImport("ole32.dll")]
    static extern int CoCreateInstance(
        [In] ref Guid rclsid, IntPtr pUnkOuter, uint dwClsContext,
        [In] ref Guid riid,
        [MarshalAs(UnmanagedType.Interface)] out IApplicationActivationManager ppv);

    [ComImport, Guid("2e941141-7f97-4756-ba1d-9decde894a3d"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
    public interface IApplicationActivationManager {{
        int ActivateApplication(
            [MarshalAs(UnmanagedType.LPWStr)] string appUserModelId,
            [MarshalAs(UnmanagedType.LPWStr)] string arguments,
            uint options, out uint processId);
    }}

    public static uint Activate(string aumid, string args) {{
        Guid clsid = new Guid("45BA127D-10A8-46EA-8AB7-56EA9078943C");
        Guid iid = new Guid("2e941141-7f97-4756-ba1d-9decde894a3d");
        IApplicationActivationManager mgr;
        int hr = CoCreateInstance(ref clsid, IntPtr.Zero, 0x1, ref iid, out mgr);
        if (hr != 0) throw new Exception("CoCreateInstance failed: 0x" + hr.ToString("X"));
        uint pid;
        mgr.ActivateApplication(aumid, args, 0, out pid);
        return pid;
    }}
}}
"@
[AppActivator]::Activate("{aumid}", '{cli_args}')
'''
    proc = subprocess.run(
        [
            "powershell", "-NoProfile", "-NonInteractive",
            "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass",
            "-Command", ps_script,
        ],
        capture_output=True, text=True,
        **_hidden_subprocess_args(),
    )
    return proc.returncode == 0


def set_lively_wallpaper(video_path):
    """Set wallpaper via Lively CLI tanpa window."""
    lively_exe = get_lively_exe()

    # 1. Coba langsung via subprocess (works untuk non-Store install)
    if lively_exe:
        try:
            subprocess.run(
                [lively_exe, "setwp", "--file", video_path],
                capture_output=True, check=True,
                **_hidden_subprocess_args(),
            )
            return True
        except PermissionError:
            pass  # MS Store version — lanjut ke fallback COM
        except Exception:
            pass

    # 2. Fallback: COM ApplicationActivationManager (untuk MS Store / AppX)
    aumid = _get_lively_aumid()
    if aumid:
        abs_path = os.path.abspath(video_path)
        cli_args = f'setwp --file "{abs_path}"'
        if _activate_via_com(aumid, cli_args):
            return True

    return False


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
