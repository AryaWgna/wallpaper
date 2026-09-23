"""
install.py — Daftarkan wallpaper switcher ke Windows Task Scheduler.

Membuat 6 trigger:
  1. Saat login (AtLogon)
  2. Saat bangun dari sleep/hibernate (EventTrigger)
  3. Jam 06:00 (morning)
  4. Jam 10:00 (day)
  5. Jam 17:00 (sunset)
  6. Jam 19:30 (night)

Jalankan: python install.py
Uninstall: python install.py --remove
"""

import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, "config.json")
TASK_NAME = "CustomWallpaperSwitch"


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def decimal_to_hm(t):
    """Konversi jam desimal ke (hour, minute). Contoh: 19.5 → (19, 30)"""
    h = int(t)
    m = int((t - h) * 60)
    return h, m


def find_python():
    """Cari path lengkap pythonw.exe agar jalan di background tanpa jendela console."""
    base_exe = sys.executable
    pythonw = base_exe.replace("python.exe", "pythonw.exe")
    if os.path.exists(pythonw):
        return pythonw
    return base_exe


def build_task_xml(config):
    """Buat XML untuk Task Scheduler."""
    python_exe = find_python()
    script_path = os.path.join(SCRIPT_DIR, "wallpaper_switch.py")

    schedule = config["schedule"]
    times = []
    for period_name in ["morning", "day", "sunset", "night"]:
        t = schedule.get(period_name)
        if t is not None:
            h, m = decimal_to_hm(t)
            times.append((h, m))

    ns = "http://schemas.microsoft.com/windows/2004/02/mit/task"
    ET.register_namespace("", ns)

    task = ET.Element("Task", {
        "version": "1.2",
        "xmlns": ns,
    })

    # Registration info
    reg = ET.SubElement(task, "RegistrationInfo")
    ET.SubElement(reg, "Description").text = (
        "Otomatis ganti wallpaper berdasarkan waktu (morning/day/sunset/night)"
    )

    # Triggers
    triggers = ET.SubElement(task, "Triggers")

    # Trigger: saat login
    logon_trigger = ET.SubElement(triggers, "LogonTrigger")
    ET.SubElement(logon_trigger, "Enabled").text = "true"
    ET.SubElement(logon_trigger, "Delay").text = "PT30S"

    # Trigger: saat bangun dari sleep/hibernate
    # Event ID 1 dari Power-Troubleshooter selalu muncul waktu resume
    event_trigger = ET.SubElement(triggers, "EventTrigger")
    ET.SubElement(event_trigger, "Enabled").text = "true"
    ET.SubElement(event_trigger, "Delay").text = "PT10S"
    subscription = ET.SubElement(event_trigger, "Subscription")
    subscription.text = (
        "<QueryList>"
        "<Query Id='0' Path='System'>"
        "<Select Path='System'>"
        "*[System[Provider[@Name='Microsoft-Windows-Power-Troubleshooter'] and EventID=1]]"
        "</Select>"
        "</Query>"
        "</QueryList>"
    )

    # Trigger: setiap jadwal
    for hour, minute in times:
        cal_trigger = ET.SubElement(triggers, "CalendarTrigger")
        ET.SubElement(cal_trigger, "StartBoundary").text = (
            f"2024-01-01T{hour:02d}:{minute:02d}:00"
        )
        ET.SubElement(cal_trigger, "Enabled").text = "true"

        schedule_by_day = ET.SubElement(cal_trigger, "ScheduleByDay")
        ET.SubElement(schedule_by_day, "DaysInterval").text = "1"

    # Principals
    principals = ET.SubElement(task, "Principals")
    principal = ET.SubElement(principals, "Principal", {"id": "Author"})
    ET.SubElement(principal, "LogonType").text = "InteractiveToken"
    ET.SubElement(principal, "RunLevel").text = "LeastPrivilege"

    # Settings
    settings = ET.SubElement(task, "Settings")
    ET.SubElement(settings, "MultipleInstancesPolicy").text = "IgnoreNew"
    ET.SubElement(settings, "DisallowStartIfOnBatteries").text = "false"
    ET.SubElement(settings, "StopIfGoingOnBatteries").text = "false"
    ET.SubElement(settings, "AllowHardTerminate").text = "true"
    ET.SubElement(settings, "StartWhenAvailable").text = "true"
    ET.SubElement(settings, "RunOnlyIfNetworkAvailable").text = "false"
    ET.SubElement(settings, "AllowStartOnDemand").text = "true"
    ET.SubElement(settings, "Enabled").text = "true"
    ET.SubElement(settings, "Hidden").text = "true"
    # Hapus ExecutionTimeLimit agar video loop tidak mati otomatis
    ET.SubElement(settings, "ExecutionTimeLimit").text = "PT0S"

    idle = ET.SubElement(settings, "IdleSettings")
    ET.SubElement(idle, "StopOnIdleEnd").text = "false"
    ET.SubElement(idle, "RestartOnIdle").text = "false"

    # Actions
    actions = ET.SubElement(task, "Actions", {"Context": "Author"})
    
    # Buat VBScript wrapper untuk menyembunyikan terminal 100%
    vbs_path = os.path.join(SCRIPT_DIR, "run_hidden.vbs")
    lively_script = os.path.join(SCRIPT_DIR, "lively_switch.py")
    lockscreen_script = os.path.join(SCRIPT_DIR, "wallpaper_switch.py")
    
    # VBScript syntax requires "" to escape quotes inside a string.
    # WshShell.Run """C:\python.exe"" ""C:\script.py""", 0, True
    vbs_content = (
        'Set WshShell = CreateObject("WScript.Shell")\n'
        'WshShell.Run """' + python_exe + '"" ""' + lively_script + '""", 0, True\n'
        'WshShell.Run """' + python_exe + '"" ""' + lockscreen_script + '"" --lockscreen-only", 0, True\n'
    )
    
    with open(vbs_path, "w", encoding="utf-8") as f:
        f.write(vbs_content)

    # Gunakan wscript.exe untuk mengeksekusi VBScript
    action1 = ET.SubElement(actions, "Exec")
    ET.SubElement(action1, "Command").text = "wscript.exe"
    ET.SubElement(action1, "Arguments").text = f'"{vbs_path}"'
    ET.SubElement(action1, "WorkingDirectory").text = SCRIPT_DIR

    return task


def install_task(config):
    """Daftarkan task ke Windows Task Scheduler."""
    task_xml = build_task_xml(config)

    xml_path = os.path.join(SCRIPT_DIR, "task_schedule.xml")
    tree = ET.ElementTree(task_xml)
    ET.indent(tree, space="  ")
    tree.write(xml_path, encoding="UTF-16", xml_declaration=True)

    # Hapus task lama kalau ada
    subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True,
    )

    # Buat task baru
    result = subprocess.run(
        ["schtasks", "/create", "/tn", TASK_NAME, "/xml", xml_path],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' berhasil didaftarkan!")
        print()
        print("Jadwal:")
        schedule = config["schedule"]
        for period_name in ["morning", "day", "sunset", "night"]:
            t = schedule.get(period_name, 0)
            h, m = decimal_to_hm(t)
            print(f"  {period_name:8s} : {h:02d}:{m:02d}")
        print(f"  {'login':8s} : saat login")
        print()
        print(f"Untuk menghapus:  schtasks /delete /tn \"{TASK_NAME}\" /f")
    else:
        print(f"[ERROR] Gagal mendaftarkan task")
        print(result.stderr)
        sys.exit(1)


def remove_task():
    """Hapus task dari Task Scheduler."""
    result = subprocess.run(
        ["schtasks", "/delete", "/tn", TASK_NAME, "/f"],
        capture_output=True, text=True,
    )

    if result.returncode == 0:
        print(f"[OK] Task '{TASK_NAME}' berhasil dihapus")
    else:
        print(f"[INFO] Task '{TASK_NAME}' tidak ditemukan atau sudah dihapus")


def main():
    if "--remove" in sys.argv or "--uninstall" in sys.argv:
        remove_task()
        return

    config = load_config()
    install_task(config)


if __name__ == "__main__":
    main()
