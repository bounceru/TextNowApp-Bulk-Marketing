# Windows Build Instructions for ProgressGhostCreator

These instructions will guide you through building the ProgressGhostCreator.exe file on your Windows computer.

## Prerequisites

1. Install Python 3.8 or newer from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"

2. Open Command Prompt (cmd) and install required packages:
   ```
   pip install pandas pillow pyttsx3 pydub pyinstaller
   ```

## Building the Executable

1. Extract the ProgressGhostCreator.zip file to a folder

2. Open Command Prompt and navigate to the extracted folder:
   ```
   cd path\to\ProgressGhostCreator
   ```

3. Run the build script:
   ```
   python build_exe.py
   ```

4. After the build completes (it may take a few minutes), you'll find the executable at:
   ```
   dist\ProgressGhostCreator.exe
   ```

## Troubleshooting

If you encounter issues:

1. Make sure all dependencies are installed:
   ```
   pip install -r package_requirements.txt
   ```

2. If PyInstaller has problems, try running it directly:
   ```
   pyinstaller --clean --noconfirm --name=ProgressGhostCreator --onefile --windowed --add-data "assets;assets" --add-data "voicemail;voicemail" --add-data "ghost_names_usernames.csv;." --icon=assets/progress_logo.png main.py
   ```

3. For any errors related to missing modules, install them with pip:
   ```
   pip install module_name
   ```

## Testing the Executable

1. Navigate to the `dist` folder
2. Double-click `ProgressGhostCreator.exe` to run it
3. Verify that:
   - The UI displays with PB BETTING branding
   - You can enter account numbers and start the process
   - It successfully simulates creating TextNow accounts

## Distribution

After confirming the executable works correctly:

1. Upload the .exe file to your website for distribution
2. Your users can simply download and run it - no installation required

## Need Help?

If you encounter any issues building the executable, please contact support@pbbetting.com for assistance.