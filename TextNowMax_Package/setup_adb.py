"""
ADB Setup Utility for ProgressGhostCreator

This script checks if ADB is installed, and if not, downloads and sets it up.
"""

import os
import sys
import zipfile
import platform
import subprocess
import urllib.request
import tkinter as tk
from tkinter import ttk, messagebox

# ADB download URLs
ADB_DOWNLOAD_URLS = {
    'windows': 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip',
    'darwin': 'https://dl.google.com/android/repository/platform-tools-latest-darwin.zip',
    'linux': 'https://dl.google.com/android/repository/platform-tools-latest-linux.zip'
}

def check_adb_installed():
    """Check if ADB is installed and accessible via PATH"""
    try:
        result = subprocess.run(['adb', 'version'], 
                            stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE,
                            text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def setup_adb_cli():
    """Set up ADB from the command line"""
    print("\n=== ADB Setup Utility for ProgressGhostCreator ===\n")
    
    if check_adb_installed():
        print("✅ ADB is already installed and accessible!")
        return True
    
    print("ADB (Android Debug Bridge) is not installed or not in PATH.")
    print("This tool is required to communicate with your BLU G44 phone.")
    
    choice = input("\nWould you like to download and set up ADB now? (y/n): ").strip().lower()
    if choice != 'y':
        print("\nSetup canceled. ADB is required for phone control functionality.")
        return False
    
    # Determine OS
    system = platform.system().lower()
    if system not in ADB_DOWNLOAD_URLS:
        print(f"❌ Unsupported operating system: {platform.system()}")
        return False
    
    print(f"\nDownloading ADB for {platform.system()}...")
    download_url = ADB_DOWNLOAD_URLS[system]
    
    try:
        # Create temp directory
        os.makedirs("temp", exist_ok=True)
        zip_path = os.path.join("temp", "platform-tools.zip")
        
        # Download ADB
        urllib.request.urlretrieve(download_url, zip_path)
        print("Download complete.")
        
        # Extract to a local directory
        print("Extracting ADB tools...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
        
        # Add to PATH temporarily
        platform_tools_path = os.path.abspath("platform-tools")
        if system == 'windows':
            os.environ["PATH"] += ";" + platform_tools_path
        else:
            os.environ["PATH"] += ":" + platform_tools_path
        
        # Test if it works
        if check_adb_installed():
            print("\n✅ ADB installed successfully!")
            
            # Provide instructions for permanent PATH setting
            print("\nTo make ADB permanently available, you should add it to your PATH:")
            if system == 'windows':
                print(f"1. Add this directory to your PATH environment variable:")
                print(f"   {platform_tools_path}")
                print("2. Or move the platform-tools folder to a location already in PATH")
            else:
                print(f"1. Add the following line to your ~/.bashrc or ~/.bash_profile:")
                print(f"   export PATH=\"$PATH:{platform_tools_path}\"")
                print("2. Then restart your terminal or run 'source ~/.bashrc'")
            
            return True
        else:
            print("❌ ADB installation failed. Please install ADB manually.")
            return False
        
    except Exception as e:
        print(f"❌ Error during setup: {str(e)}")
        return False


class AdbSetupApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB Setup for ProgressGhostCreator")
        self.root.geometry("600x450")
        self.root.minsize(600, 450)
        
        # Set theme colors
        self.bg_color = "#1E1E1E"
        self.text_color = "#EEEEEE"
        self.accent_color = "#FF6600"
        self.secondary_bg = "#252525"
        
        self.root.configure(bg=self.bg_color)
        
        self.platform_tools_path = None
        self.create_widgets()
        self.check_adb()
        
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="ADB Setup Utility",
            font=("Arial", 18, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_frame = tk.Frame(main_frame, bg=self.secondary_bg, padx=15, pady=15)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        desc_text = (
            "ADB (Android Debug Bridge) is required to communicate with your BLU G44 phone.\n"
            "This utility will check if ADB is installed and help you set it up if needed."
        )
        
        desc_label = tk.Label(
            desc_frame,
            text=desc_text,
            justify=tk.LEFT,
            fg=self.text_color,
            bg=self.secondary_bg,
            padx=10,
            pady=10
        )
        desc_label.pack(anchor=tk.W)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg=self.secondary_bg, padx=15, pady=15)
        status_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = tk.Label(
            status_frame,
            text="Checking for ADB...",
            justify=tk.LEFT,
            fg=self.text_color,
            bg=self.secondary_bg,
            padx=10,
            pady=10
        )
        self.status_label.pack(anchor=tk.W)
        
        # Log frame
        log_frame = tk.Frame(main_frame, bg=self.secondary_bg)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        log_label = tk.Label(
            log_frame, 
            text="Setup Log:",
            anchor=tk.W,
            fg=self.text_color,
            bg=self.secondary_bg,
            padx=10,
            pady=5
        )
        log_label.pack(fill=tk.X)
        
        self.log_text = tk.Text(
            log_frame,
            bg="#333333",
            fg=self.text_color,
            padx=10,
            pady=10,
            font=("Consolas", 10),
            height=10,
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            main_frame, 
            orient="horizontal",
            length=400, 
            mode="determinate",
            variable=self.progress_var
        )
        self.progress.pack(fill=tk.X, pady=(0, 10))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X)
        
        self.setup_button = tk.Button(
            button_frame,
            text="Install ADB",
            bg=self.accent_color,
            fg=self.text_color,
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            command=self.setup_adb,
            state=tk.DISABLED
        )
        self.setup_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.test_button = tk.Button(
            button_frame,
            text="Test Phone Connection",
            bg=self.accent_color,
            fg=self.text_color,
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            command=self.test_phone_connection,
            state=tk.DISABLED
        )
        self.test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.exit_button = tk.Button(
            button_frame,
            text="Exit",
            bg="#555555",
            fg=self.text_color,
            font=("Arial", 10),
            padx=15,
            pady=8,
            command=self.root.destroy
        )
        self.exit_button.pack(side=tk.LEFT)
        
    def log(self, message):
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state='disabled')
        self.root.update()
        
    def check_adb(self):
        if check_adb_installed():
            self.status_label.config(
                text="✅ ADB is already installed and accessible!",
                fg="#4CAF50"  # Green
            )
            self.test_button.config(state=tk.NORMAL)
            self.log("ADB is already installed and accessible.")
            self.log("You can now test the phone connection.")
        else:
            self.status_label.config(
                text="❌ ADB is not installed or not in PATH",
                fg="#F44336"  # Red
            )
            self.setup_button.config(state=tk.NORMAL)
            self.log("ADB (Android Debug Bridge) is not installed or not in PATH.")
            self.log("Click 'Install ADB' to download and set it up.")
    
    def setup_adb(self):
        self.setup_button.config(state=tk.DISABLED)
        self.test_button.config(state=tk.DISABLED)
        self.exit_button.config(state=tk.DISABLED)
        
        # Determine OS
        system = platform.system().lower()
        if system not in ADB_DOWNLOAD_URLS:
            messagebox.showerror(
                "Unsupported OS", 
                f"Unsupported operating system: {platform.system()}"
            )
            self.exit_button.config(state=tk.NORMAL)
            return
        
        try:
            # Create temp directory
            os.makedirs("temp", exist_ok=True)
            zip_path = os.path.join("temp", "platform-tools.zip")
            
            # Download ADB
            self.log(f"Downloading ADB for {platform.system()}...")
            self.status_label.config(text="Downloading ADB...")
            
            def progress_callback(blocks, block_size, total_size):
                percentage = min(100, int(100 * blocks * block_size / total_size))
                self.progress_var.set(percentage)
                self.root.update()
            
            urllib.request.urlretrieve(
                ADB_DOWNLOAD_URLS[system], 
                zip_path,
                progress_callback
            )
            
            self.log("Download complete.")
            
            # Extract to a local directory
            self.log("Extracting ADB tools...")
            self.status_label.config(text="Extracting ADB tools...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(".")
            
            # Add to PATH temporarily
            self.platform_tools_path = os.path.abspath("platform-tools")
            if system == 'windows':
                os.environ["PATH"] += ";" + self.platform_tools_path
            else:
                os.environ["PATH"] += ":" + self.platform_tools_path
            
            # Test if it works
            if check_adb_installed():
                self.log("\n✅ ADB installed successfully!")
                self.status_label.config(
                    text="✅ ADB installed successfully!",
                    fg="#4CAF50"  # Green
                )
                
                # Provide instructions for permanent PATH setting
                self.log("\nTo make ADB permanently available, you should add it to your PATH:")
                if system == 'windows':
                    self.log(f"1. Add this directory to your PATH environment variable:")
                    self.log(f"   {self.platform_tools_path}")
                    self.log("2. Or move the platform-tools folder to a location already in PATH")
                else:
                    self.log(f"1. Add the following line to your ~/.bashrc or ~/.bash_profile:")
                    self.log(f"   export PATH=\"$PATH:{self.platform_tools_path}\"")
                    self.log("2. Then restart your terminal or run 'source ~/.bashrc'")
                
                # Enable test button
                self.test_button.config(state=tk.NORMAL)
                self.exit_button.config(state=tk.NORMAL)
                
                messagebox.showinfo(
                    "Success",
                    "ADB installed successfully! You can now test the phone connection."
                )
            else:
                self.log("❌ ADB installation failed. Please install ADB manually.")
                self.status_label.config(
                    text="❌ ADB installation failed",
                    fg="#F44336"  # Red
                )
                self.setup_button.config(state=tk.NORMAL)
                self.exit_button.config(state=tk.NORMAL)
                
                messagebox.showerror(
                    "Installation Failed",
                    "ADB installation failed. Please install ADB manually."
                )
            
        except Exception as e:
            self.log(f"❌ Error during setup: {str(e)}")
            self.status_label.config(
                text=f"❌ Error during setup",
                fg="#F44336"  # Red
            )
            self.setup_button.config(state=tk.NORMAL)
            self.exit_button.config(state=tk.NORMAL)
            
            messagebox.showerror(
                "Setup Error",
                f"Error during setup: {str(e)}"
            )
    
    def test_phone_connection(self):
        # Launch the phone test application
        self.root.destroy()
        os.system("python adb_phone_test_gui.py")


def main():
    # Check if we should use GUI or CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        setup_adb_cli()
    else:
        try:
            root = tk.Tk()
            app = AdbSetupApp(root)
            root.mainloop()
        except Exception as e:
            print(f"Error starting GUI: {str(e)}")
            print("Falling back to command line interface...")
            setup_adb_cli()

if __name__ == "__main__":
    main()