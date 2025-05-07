@echo off
echo ============================================================
echo TextNow Max - Phone Verification Tool
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python 3.8 or higher and try again.
    echo.
    pause
    exit /b 1
)

REM Check for required dependencies
echo Checking for required dependencies...
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Tkinter is not installed. This is required for the GUI.
    echo Please install Python with Tkinter included and try again.
    echo.
    pause
    exit /b 1
)

REM Create necessary directory
if not exist logs mkdir logs

echo.
echo ============================================================
echo Starting Phone Verification Tool...
echo ============================================================
echo.
echo This tool will help you verify if your Android phone is 
echo properly connected and can perform IP rotation.
echo.
echo Please ensure:
echo   1. Android phone is connected via USB
echo   2. USB debugging is enabled on the phone
echo   3. You have confirmed any permission dialogs on the phone
echo.

REM Run the phone verification tool
python phone_verification.py

echo.
echo Phone Verification Tool has been closed.
echo.
pause