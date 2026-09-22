@echo off
REM convert_videos.bat — Konversi video ke format H.264 MP4 yang kompatibel dengan Windows
REM Pastikan FFmpeg sudah terinstall (winget install Gyan.FFmpeg)

echo ============================================
echo   Konversi Video untuk Day/Night Wallpaper
echo ============================================
echo.

if not exist "videos" (
    mkdir videos
    echo Folder 'videos' dibuat. Taruh video sumber di sana.
    echo Lalu jalankan ulang script ini.
    pause
    exit /b
)

echo Mencari video di folder videos\...
echo.

for %%f in (videos\*.mp4 videos\*.mkv videos\*.avi videos\*.webm videos\*.mov) do (
    echo Mengkonversi: %%f
    ffmpeg -y -i "%%f" -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -an -movflags +faststart "videos\%%~nf_converted.mp4"
    echo.
)

echo ============================================
echo   Selesai!
echo.
echo   File hasil konversi ada di folder videos\
echo   dengan suffix _converted.mp4
echo.
echo   Rename file sesuai kebutuhan:
echo     morning.mp4, day.mp4, sunset.mp4, night.mp4
echo ============================================

pause
