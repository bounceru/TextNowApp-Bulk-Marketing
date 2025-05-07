# TextNow Max Creator - Build Instructions

This document guides you through building the TextNow Max Creator into a Windows executable (.exe) file that you can run on any Windows computer.

## Prerequisites

1. **Install Python 3.8 or newer**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **Install Required Packages**
   Open Command Prompt (cmd) as Administrator and run:
   ```
   pip install pyinstaller
   pip install flask pandas pillow playwright pyttsx3 pydub pygame reportlab svglib
   python -m playwright install
   ```

## Building the Executable

1. **Create a folder** for the project, for example: `C:\TextNowMax`

2. **Copy all project files** to this folder, making sure to include:
   - All Python (.py) files
   - assets folder with images
   - static folder (if any)
   - ghost_accounts.db (the database file)
   - ghost_names_usernames.csv (the names file)

3. **Open Command Prompt** and navigate to your project folder:
   ```
   cd C:\TextNowMax
   ```

4. **Run PyInstaller** to create the executable:
   ```
   pyinstaller --name=TextNowMaxCreator --onefile --windowed --icon=assets/progress_logo.png --add-data="assets;assets" --add-data="static;static" --add-data="voicemail;voicemail" --add-data="ghost_accounts.db;." --add-data="ghost_names_usernames.csv;." fixed_clickable_original.py
   ```

5. **Find your executable** in the `dist` folder as `TextNowMaxCreator.exe`

## Making a Portable Version

To create a portable version that can be run from a USB drive:

1. Create a folder on your USB drive, e.g., `TextNowMaxPortable`

2. Copy the following to this folder:
   - `TextNowMaxCreator.exe` from the `dist` folder
   - README.md, FEATURES.md, INSTALLATION.md, USAGE_GUIDE.md

3. Create the following empty folders in the portable directory:
   - data
   - logs
   - config

4. Create a batch file named `Run_TextNowMax.bat` with the following content:
   ```batch
   @echo off
   echo ============================================================
   echo TextNow Max Creator - Portable Edition
   echo ============================================================
   echo.
   echo Starting TextNow Max Creator...
   echo.
   echo The application will open in your web browser.
   echo Press CTRL+C to stop the application.
   echo.

   start TextNowMaxCreator.exe
   ```

5. Double-click the batch file to run the application.

## Setting Up the Phone Connection

After building and running the executable:

1. Connect your BLU G44 phone to your computer via USB
2. Enable Developer Mode on the phone:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times until it says "You are now a developer"
3. Enable USB Debugging:
   - Go to Settings > System > Developer Options
   - Turn on "USB Debugging"
4. In the TextNow Max Creator app, go to the "Device Manager" section
5. Click "Connect to Device" to establish the connection
6. Test the IP rotation by clicking "Refresh IP"

## Troubleshooting

- **Missing Dependencies**: If the executable fails to start, you may need to install additional dependencies or rebuild with the `--collect-all` option for specific modules.
- **ADB Not Found**: Make sure Android Debug Bridge (ADB) is installed and in your PATH. You can download it from the Android SDK Platform Tools.
- **Database Issues**: If you encounter database errors, make sure your ghost_accounts.db file is properly included in the build.