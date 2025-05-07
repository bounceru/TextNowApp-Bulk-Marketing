"""
Run the TextNow Max Creator desktop application in VNC mode.
This script ensures compatibility when running in a development environment
without a local display, like Replit.
"""

import os
import sys
import subprocess
import time

def check_python_installed():
    """Check if Python is installed"""
    try:
        subprocess.run(["python", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except FileNotFoundError:
        return False

def check_pyqt_installed():
    """Check if PyQt5 is installed"""
    try:
        import PyQt5
        return True
    except ImportError:
        return False

def install_dependencies():
    """Install required dependencies"""
    print("Installing required dependencies...")
    subprocess.run([sys.executable, "-m", "pip", "install", "PyQt5"], check=True)

def create_assets_folder():
    """Create the assets folder if it doesn't exist"""
    if not os.path.exists("assets"):
        os.makedirs("assets", exist_ok=True)
        print("Created assets folder")

def main():
    """Main function"""
    print("============================================================")
    print("TextNow Max Creator - Desktop Application (VNC Mode)")
    print("============================================================")
    
    # Check Python installation
    if not check_python_installed():
        print("ERROR: Python is not installed or not in PATH")
        sys.exit(1)
    
    # Check PyQt5 installation
    if not check_pyqt_installed():
        try:
            install_dependencies()
        except subprocess.CalledProcessError:
            print("ERROR: Failed to install PyQt5")
            sys.exit(1)
    
    # Create necessary folders
    create_assets_folder()
    
    # Set environment variables for VNC
    os.environ["QT_QPA_PLATFORM"] = "vnc"
    
    # Run the desktop application
    print("\nStarting TextNow Max Creator desktop application in VNC mode...")
    print("This may take a moment to initialize...")
    
    try:
        # Import and run the desktop_app module
        import desktop_app
        desktop_app.main()
    except ImportError:
        print("ERROR: Could not import desktop_app.py")
        print("Make sure desktop_app.py is in the current directory")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: An error occurred while running the desktop application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()