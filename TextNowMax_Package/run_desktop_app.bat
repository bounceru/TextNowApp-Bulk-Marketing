@echo off
echo ============================================================
echo TextNow Max Creator - Desktop Application
echo ============================================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking for required packages...
python -m pip install --upgrade pip
pip install pyqt5 pillow pygame

echo.
echo ============================================================
echo Starting TextNow Max Creator Desktop Application...
echo ============================================================
echo.

REM Run the desktop application
python desktop_app.py

echo.
echo Application closed.
echo.
pause