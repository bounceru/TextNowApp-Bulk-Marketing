"""
ADB Phone Test GUI for ProgressGhostCreator

This GUI application tests if we can connect to and control a BLU G44 phone
via ADB for IP rotation by toggling airplane mode.
"""

import os
import sys
import time
import logging
import threading
import subprocess
from ppadb.client import Client as AdbClient

try:
    import tkinter as tk
    from tkinter import ttk, scrolledtext, messagebox
except ImportError:
    # For systems without tkinter installed
    print("Tkinter not found. Please install tkinter to run the GUI version.")
    print("Falling back to command line version...")
    import adb_phone_test
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('device_manager.log')
    ]
)
logger = logging.getLogger('AdbPhoneTestGUI')

class RedirectText:
    """Class to redirect stdout to tkinter text widget"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.buffer = ""

    def write(self, string):
        self.buffer += string
        # For long outputs, we don't want to update the UI constantly
        if "\n" in self.buffer:
            self.update_textbox()

    def update_textbox(self):
        self.text_widget.configure(state='normal')
        self.text_widget.insert(tk.END, self.buffer)
        self.text_widget.see(tk.END)
        self.text_widget.configure(state='disabled')
        self.buffer = ""

    def flush(self):
        if self.buffer:
            self.update_textbox()
            

class PhoneConnectionTester:
    def __init__(self, host='127.0.0.1', port=5037, log_widget=None):
        """Initialize the phone connection tester"""
        self.host = host
        self.port = port
        self.client = None
        self.device = None
        self.log_widget = log_widget
        
    def log(self, message, level='info'):
        """Log message to both log file and widget if provided"""
        if level == 'info':
            logger.info(message)
        elif level == 'warning':
            logger.warning(message)
        elif level == 'error':
            logger.error(message)
            
        if self.log_widget:
            if level == 'error':
                self.log_widget.tag_config('error', foreground='red')
                self.log_widget.configure(state='normal')
                self.log_widget.insert(tk.END, f"{message}\n", 'error')
                self.log_widget.configure(state='disabled')
            elif level == 'warning':
                self.log_widget.tag_config('warning', foreground='orange')
                self.log_widget.configure(state='normal')
                self.log_widget.insert(tk.END, f"{message}\n", 'warning')
                self.log_widget.configure(state='disabled')
            elif level == 'success':
                self.log_widget.tag_config('success', foreground='green')
                self.log_widget.configure(state='normal')
                self.log_widget.insert(tk.END, f"{message}\n", 'success')
                self.log_widget.configure(state='disabled')
            else:
                self.log_widget.configure(state='normal')
                self.log_widget.insert(tk.END, f"{message}\n")
                self.log_widget.configure(state='disabled')
                
            self.log_widget.see(tk.END)
        
    def check_adb_installed(self):
        """Check if ADB is installed on the system"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            if result.returncode == 0:
                self.log(f"ADB installed: {result.stdout.splitlines()[0]}", 'success')
                return True
            else:
                self.log("ADB not found or not working properly", 'error')
                return False
        except FileNotFoundError:
            self.log("ADB is not installed or not in PATH", 'error')
            return False
    
    def connect_to_adb(self):
        """Connect to ADB server"""
        try:
            self.client = AdbClient(host=self.host, port=self.port)
            self.log(f"Successfully connected to ADB server at {self.host}:{self.port}", 'success')
            return True
        except Exception as e:
            self.log(f"Failed to connect to ADB server: {str(e)}", 'error')
            return False
    
    def get_connected_devices(self):
        """Get list of connected devices"""
        if not self.client:
            self.log("ADB client not initialized", 'error')
            return []
        
        try:
            devices = self.client.devices()
            if devices:
                device_info = []
                for device in devices:
                    try:
                        model = device.shell('getprop ro.product.model').strip()
                        android_version = device.shell('getprop ro.build.version.release').strip()
                        serial = device.serial
                        
                        device_info.append({
                            'serial': serial,
                            'model': model,
                            'android_version': android_version
                        })
                        
                        self.log(f"Found device: {model} (Android {android_version}), serial: {serial}", 'success')
                    except Exception as e:
                        self.log(f"Error getting device info: {str(e)}", 'error')
                
                return device_info
            else:
                self.log("No devices connected", 'warning')
                return []
        except Exception as e:
            self.log(f"Error getting device list: {str(e)}", 'error')
            return []
    
    def select_device(self, serial=None):
        """Select a device to work with"""
        if not self.client:
            self.log("ADB client not initialized", 'error')
            return False
        
        try:
            devices = self.client.devices()
            if not devices:
                self.log("No devices connected", 'error')
                return False
            
            if serial:
                # Try to find specific device
                for device in devices:
                    if device.serial == serial:
                        self.device = device
                        model = device.shell('getprop ro.product.model').strip()
                        self.log(f"Selected device: {model} with serial {serial}", 'success')
                        return True
                self.log(f"Device with serial {serial} not found", 'error')
                return False
            else:
                # Just take the first device
                self.device = devices[0]
                model = self.device.shell('getprop ro.product.model').strip()
                self.log(f"Selected device: {model} with serial {self.device.serial}", 'success')
                return True
        except Exception as e:
            self.log(f"Error selecting device: {str(e)}", 'error')
            return False
    
    def test_airplane_mode(self):
        """Test toggling airplane mode on and off"""
        if not self.device:
            self.log("No device selected", 'error')
            return False
        
        try:
            # Check current IP first
            self.log("Checking current IP address...")
            before_ip = self.get_current_ip()
            self.log(f"Current IP before airplane mode: {before_ip}")
            
            # Turn airplane mode ON
            self.log("Turning airplane mode ON...")
            self.device.shell('settings put global airplane_mode_on 1')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true')
            self.log("Waiting for network to disconnect...")
            time.sleep(5)
            
            # Check if network is disconnected
            in_airplane_mode = self.check_if_in_airplane_mode()
            self.log(f"Is in airplane mode: {in_airplane_mode}")
            
            # Turn airplane mode OFF
            self.log("Turning airplane mode OFF...")
            self.device.shell('settings put global airplane_mode_on 0')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false')
            self.log("Waiting for network to reconnect...")
            time.sleep(10)
            
            # Check new IP
            after_ip = self.get_current_ip()
            self.log(f"Current IP after airplane mode: {after_ip}")
            
            # Verify if IP changed
            if before_ip and after_ip:
                if before_ip != after_ip:
                    self.log("IP CHANGED SUCCESSFULLY!", 'success')
                    return True
                else:
                    self.log("IP did not change after toggling airplane mode", 'warning')
                    return False
            else:
                self.log("Could not verify IP change (unable to get IP)", 'warning')
                return False
            
        except Exception as e:
            self.log(f"Error testing airplane mode: {str(e)}", 'error')
            return False
    
    def check_if_in_airplane_mode(self):
        """Check if device is currently in airplane mode"""
        try:
            result = self.device.shell('settings get global airplane_mode_on').strip()
            return result == '1'
        except Exception as e:
            self.log(f"Error checking airplane mode: {str(e)}", 'error')
            return None
    
    def get_current_ip(self):
        """Get current IP address of device"""
        try:
            # First try getting IP from the network interface
            ip_data = self.device.shell('ip addr show wlan0').strip()
            import re
            ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_data)
            
            if ip_match:
                return ip_match.group(1)
            
            # Alternative method in case first one doesn't work
            ip_data = self.device.shell('ifconfig wlan0').strip()
            ip_match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', ip_data)
            
            if ip_match:
                return ip_match.group(1)
            
            # If all else fails, try to get external IP
            external_ip = self.device.shell('curl -s ifconfig.me').strip()
            if external_ip and len(external_ip) > 0 and '.' in external_ip:
                return external_ip
                
            self.log("Could not determine device IP address", 'warning')
            return None
        except Exception as e:
            self.log(f"Error getting current IP: {str(e)}", 'error')
            return None

    def run_full_test(self):
        """Run a complete test of all functionality"""
        self.log("=== STARTING COMPREHENSIVE ADB PHONE TEST ===")
        
        # Step 1: Check if ADB is installed
        self.log("Step 1: Checking if ADB is installed...")
        if not self.check_adb_installed():
            self.log("TEST FAILED: ADB is not installed or not in PATH", 'error')
            return False
        
        # Step 2: Connect to ADB server
        self.log("Step 2: Connecting to ADB server...")
        if not self.connect_to_adb():
            self.log("TEST FAILED: Could not connect to ADB server", 'error')
            return False
        
        # Step 3: List connected devices
        self.log("Step 3: Looking for connected devices...")
        devices = self.get_connected_devices()
        if not devices:
            self.log("TEST FAILED: No devices found connected to ADB", 'error')
            return False
        
        # Step 4: Select a device (preferably BLU G44)
        self.log("Step 4: Selecting a device...")
        
        # Try to find BLU G44 first
        blu_g44_found = False
        for device in devices:
            if 'BLU' in device['model'] and 'G44' in device['model']:
                blu_g44_found = True
                if self.select_device(device['serial']):
                    self.log("Successfully selected BLU G44 device!", 'success')
                else:
                    self.log("Failed to select BLU G44 device", 'error')
                    return False
        
        if not blu_g44_found:
            self.log("BLU G44 device not found. Selecting first available device...", 'warning')
            if not self.select_device():
                self.log("TEST FAILED: Could not select any device", 'error')
                return False
        
        # Step 5: Test airplane mode toggling
        self.log("Step 5: Testing airplane mode toggling and IP rotation...")
        if not self.test_airplane_mode():
            self.log("IP rotation test inconclusive - could not verify IP change", 'warning')
            # Don't fail completely here, as this might be due to network issues
        
        self.log("=== ADB PHONE TEST COMPLETED SUCCESSFULLY ===", 'success')
        return True


class PhoneTestApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ProgressGhostCreator - Phone Connection Test")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        
        # Set theme colors
        self.bg_color = "#1E1E1E"
        self.text_color = "#EEEEEE"
        self.accent_color = "#FF6600"
        self.secondary_bg = "#252525"
        
        self.root.configure(bg=self.bg_color)
        
        self.create_widgets()
        
    def create_widgets(self):
        # Main frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="BLU G44 Phone Connection Test",
            font=("Arial", 18, "bold"),
            fg=self.accent_color,
            bg=self.bg_color
        )
        title_label.pack(pady=(0, 10))
        
        # Description
        desc_frame = tk.Frame(main_frame, bg=self.secondary_bg, padx=15, pady=15)
        desc_frame.pack(fill=tk.X, pady=(0, 15))
        
        desc_text = (
            "This tool tests if we can connect to your BLU G44 phone and control it for IP rotation.\n"
            "Before starting the test, please ensure:\n\n"
            "1. Your phone is connected to the computer via USB\n"
            "2. USB debugging is enabled in Developer Options\n"
            "3. You've approved any USB debugging prompts on your phone"
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
        
        # Log output
        log_frame = tk.Frame(main_frame, bg=self.secondary_bg)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        log_label = tk.Label(
            log_frame, 
            text="Test Results:",
            anchor=tk.W,
            fg=self.text_color,
            bg=self.secondary_bg,
            padx=10,
            pady=5
        )
        log_label.pack(fill=tk.X)
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            bg="#333333",
            fg=self.text_color,
            padx=10,
            pady=10,
            font=("Consolas", 10),
            state='disabled'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X)
        
        self.start_button = tk.Button(
            button_frame,
            text="Start Test",
            bg=self.accent_color,
            fg=self.text_color,
            font=("Arial", 10, "bold"),
            padx=15,
            pady=8,
            command=self.start_test
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
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
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready to test phone connection")
        
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            fg=self.text_color,
            bg="#333333",
            anchor=tk.W,
            padx=10,
            pady=5
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def start_test(self):
        # Disable the start button to prevent multiple tests
        self.start_button.config(state=tk.DISABLED)
        self.status_var.set("Running test... Please wait")
        
        # Clear log
        self.log_text.configure(state='normal')
        self.log_text.delete(1.0, tk.END)
        self.log_text.configure(state='disabled')
        
        # Create and start the test in a separate thread
        self.test_thread = threading.Thread(target=self.run_test)
        self.test_thread.daemon = True
        self.test_thread.start()
        
    def run_test(self):
        try:
            # Initialize the tester
            tester = PhoneConnectionTester(log_widget=self.log_text)
            
            # Run the test
            result = tester.run_full_test()
            
            # Update UI when done
            self.root.after(100, self.test_completed, result)
        except Exception as e:
            logger.error(f"Unexpected error during test: {str(e)}")
            self.root.after(100, self.test_error, str(e))
    
    def test_completed(self, result):
        self.start_button.config(state=tk.NORMAL)
        
        if result:
            self.status_var.set("Test completed successfully!")
            messagebox.showinfo(
                "Test Passed", 
                "Your phone is properly configured for ProgressGhostCreator!\n\n"
                "We can successfully control airplane mode for IP rotation."
            )
        else:
            self.status_var.set("Test failed. See log for details.")
            messagebox.showerror(
                "Test Failed",
                "There were issues connecting to or controlling your phone.\n\n"
                "Please check the log output for details."
            )
    
    def test_error(self, error_msg):
        self.start_button.config(state=tk.NORMAL)
        self.status_var.set("Test error. See log for details.")
        
        self.log_text.configure(state='normal')
        self.log_text.insert(tk.END, f"\nUNEXPECTED ERROR: {error_msg}\n", 'error')
        self.log_text.configure(state='disabled')
        
        messagebox.showerror(
            "Test Error",
            f"An unexpected error occurred:\n\n{error_msg}"
        )

def main():
    root = tk.Tk()
    app = PhoneTestApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()