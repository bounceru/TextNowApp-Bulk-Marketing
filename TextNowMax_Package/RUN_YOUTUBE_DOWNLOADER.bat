@echo off
echo ============================================================
echo YouTube Video Downloader - Setup and Launch
echo ============================================================
echo.

echo Installing dependencies...
pip install PyQt5 pytube
echo.

echo Starting YouTube Downloader...
python youtube_downloader.py
echo.

pause