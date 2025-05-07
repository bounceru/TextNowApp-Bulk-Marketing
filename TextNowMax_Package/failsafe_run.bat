@echo off
color 0A
title ProgressGhostCreator Server - FAILSAFE MODE

echo ============================================================
echo  PROGRESS GHOST CREATOR - FAILSAFE LAUNCHER
echo ============================================================
echo.
echo This launcher will keep the window open even if errors occur.
echo.

echo Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or newer and try again.
    echo.
    echo Visit: https://www.python.org/downloads/
    echo.
    echo Press any key to exit...
    pause > nul
    goto end
)

echo.
echo Checking required packages...
echo.
echo Attempting to install Flask and Pillow...
pip install flask pillow
echo.

echo Press any key to start the application...
pause > nul
echo.

echo ============================================================
echo  STARTING SERVER - DO NOT CLOSE THIS WINDOW
echo ============================================================
echo.
echo If the application crashes, you'll see error messages here.
echo The window will remain open so you can read any errors.
echo.

:: Try to start the server with error handling
echo Starting server...
python app_preview_fixed.py

echo.
echo ============================================================
echo.
if %ERRORLEVEL% NEQ 0 (
    echo APPLICATION ERROR DETECTED!
    echo.
    echo The Python application encountered an error.
    echo Please check the error messages above.
    echo.
) else (
    echo Server has stopped normally.
)

:end
echo.
echo Press any key to exit...
pause > nul