import os
import sys
import logging
from pathlib import Path
import tkinter as tk
from gui import ProgressGhostGUI
from textnow_bot import TextNowBot
from data_manager import DataManager
from device_manager import DeviceManager
from utils import setup_logger

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def main():
    # Setup logging
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    setup_logger(log_dir / "app.log")
    
    # Initialize app components
    data_manager = DataManager()
    device_manager = DeviceManager()
    bot = TextNowBot(data_manager, device_manager)
    
    # Start GUI
    root = tk.Tk()
    app = ProgressGhostGUI(root, bot, data_manager)
    root.mainloop()

if __name__ == "__main__":
    main()
