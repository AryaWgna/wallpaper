"""
video_wallpaper.py - Live video wallpaper untuk Windows.
"""
import ctypes
import ctypes.wintypes
import datetime
import json
import os
import subprocess
import sys
import time
import signal

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
PID_FILE = os.path.join(SCRIPT_DIR, "video_wallpaper.pid")

user32 = ctypes.windll.user32
FindWindowW = user32.FindWindowW
FindWindowExW = user32.FindWindowExW
SendMessageTimeoutW = user32.SendMessageTimeoutW
EnumWindows = user32.EnumWindows
GetSystemMetrics = user32.GetSystemMetrics

SMTO_NORMAL = 0x0000
SM_CXSCREEN = 0
SM_CYSCREEN = 1

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
    night_start = schedule.get("night", 19.5)
    
    if morning_start <= t < day_start: return "morning"
    elif day_start <= t < sunset_start: return "day"
    elif sunset_start <= t < night_start: return "sunset"
    else: return "night"

def find_workerw():
    progman = FindWindowW("Progman", None)
    if not progman:
        return None

    result = ctypes.wintypes.DWORD(0)
    for wparam, lparam in [(0xD, 0x1), (0xD, 0), (0, 0)]:
        SendMessageTimeoutW(progman, 0x052C, wparam, lparam, SMTO_NORMAL, 1000, ctypes.byref(result))
        time.sleep(0.3)

    workerw = None
    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
    def enum_callback(hwnd, lparam):
        nonlocal workerw
        shell_view = FindWindowExW(hwnd, None, "SHELLDLL_DefView", None)
        if shell_view:
            workerw = FindWindowExW(None, hwnd, "WorkerW", None)
        return True

    EnumWindows(enum_callback, 0)
    
    if not workerw:
        workerw = progman
    else:
        ctypes.windll.user32.ShowWindow(workerw, 5) # SW_SHOW
        
    return workerw

def play_video_on_desktop(video_path, workerw_hwnd, mpv_exe="mpv"):
    screen_w = GetSystemMetrics(SM_CXSCREEN)
    screen_h = GetSystemMetrics(SM_CYSCREEN)

    CREATE_NO_WINDOW = 0x08000000
    
    cmd = [
        mpv_exe,
        "--wid=" + str(workerw_hwnd),
        "--loop-file=inf",
        "--no-audio",
        "--no-osc",
        "--no-osd-bar",
        "--no-input-default-bindings",
        "--panscan=1.0",
        f"--geometry={screen_w}x{screen_h}+0+0",
        "--hwdec=auto",
        "--vo=gpu", # Fallback to stable gpu vo
        video_path,
    ]

    log_out = open(os.path.join(SCRIPT_DIR, "mpv_debug.log"), "w")
    return subprocess.Popen(
        cmd, 
        stdout=log_out, 
        stderr=log_out,
        creationflags=CREATE_NO_WINDOW
    )

def kill_existing():
    if not os.path.exists(PID_FILE): return
    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())
        subprocess.run(["taskkill", "/F", "/PID", str(pid), "/T"], capture_output=True, creationflags=0x08000000)
    except:
        pass
    try: os.remove(PID_FILE)
    except: pass
    
    subprocess.run(["taskkill", "/F", "/IM", "mpv.exe"], capture_output=True, creationflags=0x08000000)

def save_pid(pid):
    with open(PID_FILE, "w") as f:
        f.write(str(pid))

def main():
    log_file = open(os.path.join(SCRIPT_DIR, "video_debug.log"), "w")
    def log(msg): log_file.write(msg + "\n"); log_file.flush()

    try:
        if "--stop" in sys.argv or "--kill" in sys.argv:
            kill_existing()
            return

        config = load_config()
        period = get_time_period(config)
        video_file = config["videos"].get(period)
        video_path = os.path.join(SCRIPT_DIR, video_file)

        kill_existing()
        
        mpv_exe = "mpv"
        import shutil
        if not shutil.which("mpv"):
            possible_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\mpv.exe"),
                os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\shinchiro.mpv_Microsoft.Winget.Source_8wekyb3d8bbwe\mpv\mpv.exe"),
                r"C:\Program Files\MPV Player\mpv.exe",
                r"C:\Program Files\mpv\mpv.exe"
            ]
            for p in possible_paths:
                if os.path.exists(p):
                    mpv_exe = p
                    break

        workerw = find_workerw()
        if not workerw:
            log("[ERROR] Tidak bisa menemukan WorkerW window")
            sys.exit(1)
        
        log(f"WorkerW found: {workerw}. Starting MPV: {mpv_exe}")
        proc = play_video_on_desktop(video_path, workerw, mpv_exe)
        save_pid(proc.pid)
        log(f"MPV started with PID: {proc.pid}")

        current_period = period

        def cleanup(signum=None, frame=None):
            proc.terminate()
            kill_existing()
            sys.exit(0)

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        while True:
            ret = proc.poll()
            if ret is not None:
                log(f"[WARN] MPV exited unexpectedly with code {ret}")
                break
            time.sleep(15)
            new_period = get_time_period(config)
            if new_period != current_period:
                proc.terminate()
                proc.wait(timeout=5)
                current_period = new_period
                new_video = config["videos"].get(new_period)
                new_path = os.path.join(SCRIPT_DIR, new_video)
                if os.path.isfile(new_path):
                    log(f"Switching video to {new_path}")
                    proc = play_video_on_desktop(new_path, workerw, mpv_exe)
                    save_pid(proc.pid)
    except Exception as e:
        import traceback
        log(traceback.format_exc())
    finally:
        log_file.close()

if __name__ == "__main__":
    main()
