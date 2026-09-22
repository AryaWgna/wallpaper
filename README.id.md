# Day/Night Video Wallpaper

Wallpaper switcher otomatis berbasis waktu untuk Windows 10/11. Mengganti wallpaper desktop dan lock screen sesuai jadwal harian yang bisa dikonfigurasi (pagi, siang, sunset, malam).

Opsional: bisa memutar video looping langsung di desktop di belakang ikon menggunakan MPV.

*Read this in [English](README.md).*

## Cara kerja

Empat periode waktu didefinisikan di `config.json`. Setiap transisi, script yang aktif akan:

1. **Mode static** (`wallpaper_switch.py`) — mengambil satu frame dari video yang sesuai via FFmpeg, lalu di-set sebagai wallpaper desktop dan lock screen.
2. **Mode live** (`video_wallpaper.py`) — menanamkan MPV ke window WorkerW desktop dan loop video. Otomatis mendeteksi pergantian periode dan menukar video.
3. **Mode Lively** (`lively_switch.py`) — mendelegasikan ke [Lively Wallpaper](https://www.rocksdanister.com/lively/) kalau terinstall.

`install.py` mendaftarkan entry di Windows Task Scheduler supaya semuanya jalan saat login dan di setiap transisi jadwal. Tidak perlu intervensi manual setelah setup.

## Kebutuhan

- Python 3.8+
- FFmpeg (untuk ekstraksi frame)
- MPV (hanya untuk mode live video)

```
winget install Gyan.FFmpeg
winget install shinchiro.mpv
```

## Setup

Clone repo lalu taruh file video ke `videos/`:

```
git clone <repo-url>
cd wallpaper
```

Folder videos butuh satu file per periode. Nama file dikonfigurasi di `config.json` — default:

```
videos/
  morning.mp4
  day.mp4
  sunset.mp4
  night.mp4
```

Video pendek loop (10-30 detik) paling cocok. Kalau file sumber belum H.264 MP4, jalankan `convert_videos.bat` dulu.

## Konfigurasi

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

Nilai jadwal dalam jam desimal (`19.5` = 19:30). `frame_position` mengatur posisi frame yang diambil dari video (0.0 = awal, 1.0 = akhir). `wallpaper_style` menerima `center`, `tile`, `stretch`, `fit`, `fill`, atau `span`.

## Penggunaan

Test manual:

```
python wallpaper_switch.py
python video_wallpaper.py
```

Daftarkan ke Task Scheduler untuk switching otomatis:

```
python install.py
```

Ini membuat trigger saat login, 06:00, 10:00, 17:00, dan 19:30. Task berjalan diam-diam di background lewat VBScript wrapper yang di-generate.

Untuk menghapus:

```
python install.py --remove
```

## Daftar file

| File | Fungsi |
|------|--------|
| `config.json` | Jadwal, path video, pengaturan tampilan |
| `wallpaper_switch.py` | Switcher wallpaper static + lock screen |
| `video_wallpaper.py` | Live video wallpaper via MPV di WorkerW |
| `lively_switch.py` | Integrasi Lively Wallpaper |
| `install.py` | Registrasi Task Scheduler |
| `convert_videos.bat` | Batch convert video ke H.264 MP4 |
| `dump_windows.py` | Debug helper — dump tree window WorkerW/Progman |

## Troubleshooting

**Wallpaper tidak berubah** — jalankan `python wallpaper_switch.py` langsung dan cek output-nya.

**FFmpeg/MPV not found** — pastikan sudah ada di PATH. Restart terminal setelah install.

**Lock screen tidak update** — metode WinRT API jalan tanpa admin. Fallback via registry butuh elevasi.

**Video live berkedip atau tidak muncul** — trik WorkerW tergantung state shell. Restart Explorer biasanya memperbaiki ini.

## Lisensi

MIT
