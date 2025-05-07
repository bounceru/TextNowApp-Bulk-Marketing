import os
import sys
import shutil
from pathlib import Path

def main():
    """Build the .exe file using PyInstaller"""
    print("Building ProgressGhostCreator.exe...")
    
    # Create directories for PyInstaller
    os.makedirs("build", exist_ok=True)
    os.makedirs("dist", exist_ok=True)
    
    # Create folders that should be included in the distribution
    for folder in ["assets", "logs", "voicemail"]:
        os.makedirs(folder, exist_ok=True)
    
    # Copy resources
    if os.path.exists("attached_assets/progress_background.jpg"):
        shutil.copy("attached_assets/progress_background.jpg", "assets/")
    if os.path.exists("attached_assets/progress_logo.png"):
        shutil.copy("attached_assets/progress_logo.png", "assets/")
    
    # Generate default ghost names if not exist
    if not os.path.exists("ghost_names_usernames.csv"):
        from data_manager import DataManager
        dm = DataManager()
        dm._create_sample_names_csv()
    
    # Build command for PyInstaller
    # Create platform-specific command
    if sys.platform.startswith('win'):
        # Windows uses semicolons for path separators in PyInstaller
        cmd = (
            f"pyinstaller --clean --noconfirm "
            f"--name=ProgressGhostCreator "
            f"--onefile "  # Single file executable
            f"--windowed "  # GUI application, no console
            f"--add-data \"assets;assets\" "
            f"--add-data \"voicemail;voicemail\" "
            f"--add-data \"ghost_names_usernames.csv;.\" "
            f"--icon=assets/progress_logo.png "
            f"main.py"
        )
    else:
        # Linux/Mac uses colons for path separators
        cmd = (
            f"pyinstaller --clean --noconfirm "
            f"--name=ProgressGhostCreator "
            f"--onefile "  # Single file executable
            f"--windowed "  # GUI application, no console
            f"--add-data 'assets{os.pathsep}assets' "
            f"--add-data 'voicemail{os.pathsep}voicemail' "
            f"--add-data 'ghost_names_usernames.csv{os.pathsep}.' "
            f"--icon=assets/progress_logo.png "
            f"main.py"
        )
    
    # Run PyInstaller
    print(f"Running: {cmd}")
    os.system(cmd)
    
    # Report result
    exe_path = os.path.join("dist", "ProgressGhostCreator.exe")
    if os.path.exists(exe_path):
        size_mb = os.path.getsize(exe_path) / (1024 * 1024)
        print(f"Build successful! Executable size: {size_mb:.2f} MB")
        print(f"Executable saved to: {os.path.abspath(exe_path)}")
    else:
        print("Build failed. Check the logs for errors.")

if __name__ == "__main__":
    main()