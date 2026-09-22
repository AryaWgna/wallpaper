# Day/Night Video Wallpaper

Automatic time-based wallpaper switcher for Windows 10/11. Swaps desktop wallpaper and lock screen image according to a configurable daily schedule (morning, day, sunset, night).

Optionally plays looping video directly on the desktop behind icons using MPV.

*Baca dalam [Bahasa Indonesia](README.id.md).*

## How it works

Four time periods are defined in `config.json`. At each transition, the active script either:

1. **Static mode** (`wallpaper_switch.py`) — extracts a single frame from the matching video via FFmpeg, sets it as the desktop wallpaper and lock screen.
2. **Live mode** (`video_wallpaper.py`) — embeds MPV into the WorkerW desktop window and loops the video. Monitors for period changes and swaps the video automatically.
3. **Lively mode** (`lively_switch.py`) — delegates to [Lively Wallpaper](https://www.rocksdanister.com/lively/) if installed.

`install.py` registers a Windows Task Scheduler entry so everything runs at login and at each scheduled transition. No manual intervention needed after setup.

## Requirements

- Python 3.8+
- FFmpeg (for frame extraction)
- MPV (only for live video mode)

```
winget install Gyan.FFmpeg
winget install shinchiro.mpv
```

## Setup

Clone the repo and drop your video files into `videos/`:

```
git clone <repo-url>
cd wallpaper
```

The videos folder expects one file per period. Names are configured in `config.json` — defaults:

```
videos/
  morning.mp4
  day.mp4
  sunset.mp4
  night.mp4
```

Short loops (10-30s) work best. If your source files aren't H.264 MP4, run `convert_videos.bat` first.

## Configuration

Edit `config.json`:

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

Schedule values are decimal hours (`19.5` = 19:30). `frame_position` controls where in the video the static frame is grabbed (0.0 = start, 1.0 = end). `wallpaper_style` accepts `center`, `tile`, `stretch`, `fit`, `fill`, or `span`.

## Usage

Test manually:

```
python wallpaper_switch.py
python video_wallpaper.py
```

Register to Task Scheduler for automatic switching:

```
python install.py
```

This creates triggers at login, 06:00, 10:00, 17:00, and 19:30. The scheduled task runs silently in the background via a generated VBScript wrapper.

To remove:

```
python install.py --remove
```

## File overview

| File | Purpose |
|------|---------|
| `config.json` | Schedule times, video paths, display settings |
| `wallpaper_switch.py` | Static wallpaper + lock screen switcher |
| `video_wallpaper.py` | Live video wallpaper via MPV on WorkerW |
| `lively_switch.py` | Lively Wallpaper integration |
| `install.py` | Task Scheduler registration |
| `convert_videos.bat` | Batch convert videos to H.264 MP4 |
| `dump_windows.py` | Debug helper — dumps WorkerW/Progman window tree |

## Troubleshooting

**Wallpaper not changing** — run `python wallpaper_switch.py` directly and check the output.

**FFmpeg/MPV not found** — make sure they're on your PATH. Restart your terminal after installing.

**Lock screen not updating** — the WinRT API method works without admin. The registry fallback requires elevation.

**Live video flickers or doesn't appear** — the WorkerW trick depends on the shell state. Restarting Explorer usually fixes it.

## License

MIT
