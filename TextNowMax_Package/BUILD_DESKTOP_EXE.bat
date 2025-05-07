@echo off
echo ============================================================
echo TextNow Max Creator - Building Desktop Executable
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
pip install pyinstaller pyqt5 pillow pygame
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install required packages
    pause
    exit /b 1
)

echo.
echo Starting build process - this may take a few minutes...
echo.

REM Create a directory for assets if it doesn't exist
if not exist assets mkdir assets

REM Create a directory for the database if it doesn't exist
if not exist data mkdir data

REM Create a one-file executable
pyinstaller --noconfirm --onefile --windowed --icon="assets/progress_logo.png" --name="TextNowMax" ^
  --add-data="assets;assets/" ^
  --add-data="data;data/" ^
  desktop_app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed!
    echo.
    echo Common causes:
    echo - Missing dependencies
    echo - File permissions issues
    echo - Antivirus blocking PyInstaller
    echo.
    echo Try running this batch file as Administrator
    pause
    exit /b 1
)

echo.
echo ============================================================
echo Build completed successfully!
echo.
echo The executable file is located at:
echo %CD%\dist\TextNowMax.exe
echo.
echo You can copy this file along with the following folders:
echo - assets
echo - data
echo.
echo ============================================================
echo.

echo Would you like to run the application now? (Y/N)
set /p choice="Choice: "
if /i "%choice%"=="Y" (
    echo.
    echo Starting TextNow Max Creator...
    start dist\TextNowMax.exe
)

pause