# Packaging Instructions for ProgressGhostCreator

These instructions will guide you through the process of packaging the ProgressGhostCreator application into a standalone Windows executable (.exe) file.

## Prerequisites

1. Ensure you have Python 3.8 or newer installed
2. Install PyInstaller: `pip install pyinstaller`
3. Install all required dependencies:
   ```
   pip install pandas pillow pyttsx3 pydub
   ```

## Steps to Create the Executable

1. Make sure all project files are in place:
   - All Python files (main.py, gui.py, textnow_bot.py, etc.)
   - Assets folder with branding images
   - Voicemail folder with sample greetings
   - ghost_names_usernames.csv with sample data

2. Run the build_exe.py script:
   ```
   python build_exe.py
   ```

3. The executable will be created in the `dist` folder as `ProgressGhostCreator.exe`

## Alternative Manual Method

If the build script doesn't work, you can manually create the executable with this command:

```
pyinstaller --clean --noconfirm --name=ProgressGhostCreator --onefile --windowed --add-data "assets;assets" --add-data "voicemail;voicemail" --add-data "ghost_names_usernames.csv;." --icon=assets/progress_logo.png main.py
```

## Testing the Executable

1. Navigate to the `dist` folder
2. Run `ProgressGhostCreator.exe`
3. Verify that:
   - The UI displays correctly with PB BETTING branding
   - You can enter a number of accounts to create
   - The Start/Pause/Stop buttons work
   - Sample accounts are created in demo mode

## Troubleshooting

If you encounter issues:

1. Missing resources: Make sure all paths are correct and resources are included in the PyInstaller command
2. Import errors: Check that all dependencies are installed
3. "Access denied" errors: Try running the executable as administrator

## Distribution

The final executable can be:
1. Uploaded to a website for download
2. Distributed via file sharing
3. Placed on a USB drive

## Notes

- The demo version simulates TextNow account creation without actually connecting to TextNow
- For production use with an actual phone, additional configuration will be needed
- The executable includes everything needed - no separate installation required