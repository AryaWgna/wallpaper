# 🌅 Day/Night Video Wallpaper for Windows

Automatically switch your Windows desktop wallpaper based on the time of day — morning, day, sunset, and night.

![Windows 10/11](https://img.shields.io/badge/Windows-10%2F11-blue?logo=windows)
![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-yellow?logo=python)

## ✨ Features

- **Time-based wallpaper switching** — 4 periods: morning, day, sunset, night
- **Static mode** — Extracts a frame from video and sets it as wallpaper + lock screen
- **Live video mode** — Plays video directly on your desktop behind icons (using MPV)
- **Lively Wallpaper integration** — Works with [Lively Wallpaper](https://www.rocksdanister.com/lively/) app
- **Auto-scheduling** — Registers to Windows Task Scheduler for seamless automation
- **Lock screen support** — Also changes the lock screen to match the time period
- **Zero UI** — Runs completely in the background, no console windows

## 📁 Project Structure

```
wallpaper/
├── config.json            # Schedule and video configuration
├── video_wallpaper.py     # Live video wallpaper engine (MPV-based)
├── wallpaper_switch.py    # Static wallpaper + lock screen switcher
├── lively_switch.py       # Lively Wallpaper integration
├── install.py             # Task Scheduler auto-installer
├── convert_videos.bat     # Video format converter (to H.264 MP4)
├── dump_windows.py        # Debug utility for desktop window hierarchy
├── videos/                # Your video files go here (not tracked by git)
│   ├── morning.mp4
│   ├── day.mp4
│   ├── sunset.mp4
│   └── night.mp4
└── frames/                # Auto-generated extracted frames
```

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** — [Download](https://www.python.org/downloads/)
- **FFmpeg** — Required for frame extraction

  ```bash
  # via winget
  winget install Gyan.FFmpeg

  # or via Chocolatey
  choco install ffmpeg
  ```

- **MPV** *(optional, for live video mode)* — [Download](https://mpv.io/)

  ```bash
  winget install shinchiro.mpv
  ```

### 1. Clone and prepare videos

```bash
git clone https://github.com/YOUR_USERNAME/wallpaper.git
cd wallpaper
```

Place your 4 video files in the `videos/` folder. You can use any short looping videos (10-30 seconds recommended).

### 2. Configure schedule

Edit `config.json` to set your time schedule and video paths:

```json
{
    "schedule": {
        "morning": 6.0,
        "day": 10.0,
        "sunset": 17.0,
        "night": 19.5
    },
    "videos": {
        "morning": "videos/morning.mp4",
        "day": "videos/day.mp4",
        "sunset": "videos/sunset.mp4",
        "night": "videos/night.mp4"
    },
    "frame_position": 0.5,
    "wallpaper_style": "fill"
}
```

> **Note:** Schedule uses decimal hours. For example, `19.5` = 19:30 (7:30 PM).

### 3. Test it

```bash
# Static wallpaper mode
python wallpaper_switch.py

# Live video mode (plays video behind desktop icons)
python video_wallpaper.py
```

### 4. Auto-schedule

Register the wallpaper switcher to run automatically at login and at each time transition:

```bash
python install.py
```

This creates a Windows Task Scheduler entry with triggers at:
- 🔑 User login
- 🌄 06:00 — Morning
- ☀️ 10:00 — Day
- 🌇 17:00 — Sunset
- 🌙 19:30 — Night

### 5. (Optional) Convert videos

If your videos are not in H.264 MP4 format:

```bash
convert_videos.bat
```

## 🔧 Configuration

### Schedule

| Period    | Default Time | Description         |
|-----------|-------------|---------------------|
| `morning` | 06:00       | Sunrise / early day |
| `day`     | 10:00       | Bright daylight     |
| `sunset`  | 17:00       | Golden hour         |
| `night`   | 19:30       | After dark          |

### Wallpaper Style

The `wallpaper_style` option supports: `center`, `tile`, `stretch`, `fit`, `fill` (default), `span`.

## ❌ Uninstall

Remove the scheduled task:

```bash
python install.py --remove
# or manually:
schtasks /delete /tn "CustomWallpaperSwitch" /f
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Wallpaper doesn't change | Run `python wallpaper_switch.py` manually to check for errors |
| "FFmpeg not found" | Make sure FFmpeg is in your PATH, restart terminal after install |
| Video won't play | Convert with `convert_videos.bat` to ensure H.264 MP4 format |
| Live video mode flickers | Try different `--vo` options in `video_wallpaper.py` |
| Lock screen not updating | May require admin privileges for registry fallback |

## 📝 License

This project is open source and available under the [MIT License](LICENSE).
