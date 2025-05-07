"""
Phone Verification for TextNow Max

This module provides a simple interface to verify if an Android phone is properly
connected via ADB and can perform IP rotation by toggling airplane mode.
Works with any Android phone, not just the BLU G44.
"""

import os
import time
import logging
import sys
import subprocess
import re
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Optional, Dict, List, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('phone_verification.log')
    ]
)
logger = logging.getLogger('PhoneVerifier')

class PhoneVerifier:
    """Class to verify Android phone connection and functionality"""
    
    def __init__(self, adb_path=None):
        """Initialize the phone verifier with optional ADB path"""
        self.adb_path = adb_path or self._find_adb_path()
        self.current_device = None
        self.device_info = {}
    
    def _find_adb_path(self):
        """Find ADB path automatically"""
        # Check environment variable
        if 'ADB_PATH' in os.environ:
            return os.environ['ADB_PATH']
        
        # Check common locations
        possible_paths = [
            os.path.join(os.getcwd(), 'platform-tools', 'adb'),
            os.path.join(os.getcwd(), 'platform-tools', 'adb.exe'),
            'adb',  # If in PATH
            'adb.exe'
        ]
        
        for path in possible_paths:
            try:
                # Check if the path is valid
                result = subprocess.run(
                    [path, 'version'], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logger.info(f"Found ADB at: {path}")
                    return path
            except (subprocess.SubprocessError, FileNotFoundError):
                continue
        
        logger.warning("Could not find ADB path automatically")
        return 'adb'  # Default fallback
    
    def check_adb_installed(self):
        """Check if ADB is installed and working"""
        try:
            result = subprocess.run(
                [self.adb_path, 'version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version = result.stdout.splitlines()[0]
                logger.info(f"ADB is installed: {version}")
                return True, version
            else:
                logger.error(f"ADB error: {result.stderr}")
                return False, result.stderr
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error checking ADB: {str(e)}")
            if isinstance(e, FileNotFoundError):
                return False, "ADB not found. Please install Android SDK Platform Tools."
            return False, str(e)
    
    def start_adb_server(self):
        """Start the ADB server"""
        try:
            result = subprocess.run(
                [self.adb_path, 'start-server'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info("ADB server started")
                return True, "ADB server started successfully"
            else:
                logger.error(f"Failed to start ADB server: {result.stderr}")
                return False, result.stderr
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error starting ADB server: {str(e)}")
            return False, str(e)
    
    def find_connected_devices(self):
        """Find all connected Android devices"""
        try:
            result = subprocess.run(
                [self.adb_path, 'devices'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"ADB error: {result.stderr}")
                return []
            
            # Parse the output to get device list
            devices = []
            for line in result.stdout.splitlines()[1:]:  # Skip the first line (header)
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2 and parts[1] == 'device':
                        devices.append(parts[0])
            
            if devices:
                logger.info(f"Found {len(devices)} connected devices: {', '.join(devices)}")
            else:
                logger.warning("No connected devices found")
                
            return devices
        except subprocess.SubprocessError as e:
            logger.error(f"Error finding devices: {str(e)}")
            return []
    
    def get_device_info(self, device_serial):
        """Get detailed information about a device"""
        if not device_serial:
            return {}
        
        device_info = {
            'serial': device_serial,
            'model': None,
            'manufacturer': None,
            'android_version': None,
            'sdk_version': None,
            'ip_address': None,
            'battery_level': None,
            'screen_resolution': None,
            'product_name': None
        }
        
        # Define the properties to retrieve
        properties = {
            'model': 'ro.product.model',
            'manufacturer': 'ro.product.manufacturer',
            'android_version': 'ro.build.version.release',
            'sdk_version': 'ro.build.version.sdk',
            'product_name': 'ro.product.name'
        }
        
        try:
            # Get each property
            for key, prop in properties.items():
                result = subprocess.run(
                    [self.adb_path, '-s', device_serial, 'shell', 'getprop', prop], 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, 
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    device_info[key] = result.stdout.strip()
            
            # Get IP address
            device_info['ip_address'] = self.get_device_ip(device_serial)
            
            # Get battery level
            battery_info = self.execute_adb_command(
                device_serial, ['shell', 'dumpsys', 'battery'], timeout=5
            )
            if battery_info:
                level_match = re.search(r'level:\s*(\d+)', battery_info)
                if level_match:
                    device_info['battery_level'] = level_match.group(1) + '%'
            
            # Get screen resolution
            display_info = self.execute_adb_command(
                device_serial, ['shell', 'wm', 'size'], timeout=5
            )
            if display_info:
                size_match = re.search(r'Physical size:\s*(\d+x\d+)', display_info)
                if size_match:
                    device_info['screen_resolution'] = size_match.group(1)
                else:
                    # Try alternative method
                    size_match = re.search(r'Override size:\s*(\d+x\d+)', display_info)
                    if size_match:
                        device_info['screen_resolution'] = size_match.group(1)
            
            logger.info(f"Retrieved device info for {device_serial}: {device_info}")
            return device_info
            
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return device_info
    
    def execute_adb_command(self, device_serial, command, timeout=30):
        """Execute an ADB command on a specific device"""
        try:
            # Prepare the full command
            full_command = [self.adb_path, '-s', device_serial] + command
            
            # Run the command
            result = subprocess.run(
                full_command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=timeout
            )
            
            if result.returncode != 0:
                logger.error(f"ADB command error: {result.stderr}")
                return None
            
            return result.stdout.strip()
        except subprocess.SubprocessError as e:
            logger.error(f"Error executing ADB command: {str(e)}")
            return None
    
    def get_device_ip(self, device_serial):
        """Get the current IP address of the device"""
        try:
            # Method 1: Try using ip addr show
            ip_data = self.execute_adb_command(device_serial, ['shell', 'ip', 'addr', 'show', 'wlan0'])
            if ip_data:
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_data)
                if ip_match:
                    return ip_match.group(1)
            
            # Method 2: Try using ifconfig
            ip_data = self.execute_adb_command(device_serial, ['shell', 'ifconfig', 'wlan0'])
            if ip_data:
                ip_match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', ip_data)
                if ip_match:
                    return ip_match.group(1)
            
            # Method 3: Try getting the external IP
            try:
                # First check if we have curl
                curl_version = self.execute_adb_command(device_serial, ['shell', 'curl', '--version'])
                if curl_version:
                    external_ip = self.execute_adb_command(device_serial, ['shell', 'curl', '-s', 'ifconfig.me'])
                    if external_ip and len(external_ip) > 0 and '.' in external_ip:
                        return external_ip
            except:
                logger.warning("Could not use curl to get external IP")
            
            # Method 4: Try using a different network interface
            interfaces = ['rmnet0', 'rmnet_data0', 'eth0']
            for interface in interfaces:
                ip_data = self.execute_adb_command(device_serial, ['shell', 'ip', 'addr', 'show', interface])
                if ip_data:
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_data)
                    if ip_match:
                        return ip_match.group(1)
            
            logger.warning("Could not determine device IP address")
            return None
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            return None
    
    def check_airplane_mode(self, device_serial):
        """Check if airplane mode is enabled on the device"""
        try:
            result = self.execute_adb_command(
                device_serial, ['shell', 'settings', 'get', 'global', 'airplane_mode_on']
            )
            
            if result is None:
                return None
            
            is_enabled = result.strip() == '1'
            logger.info(f"Airplane mode is {'enabled' if is_enabled else 'disabled'}")
            return is_enabled
        except Exception as e:
            logger.error(f"Error checking airplane mode: {str(e)}")
            return None
    
    def toggle_airplane_mode(self, device_serial, enable=True):
        """Toggle airplane mode on the device"""
        try:
            # Save current IP before toggling
            old_ip = self.get_device_ip(device_serial)
            
            # First, check the current state
            current_state = self.execute_adb_command(
                device_serial, ['shell', 'settings', 'get', 'global', 'airplane_mode_on']
            )
            
            # If current state matches what we want, no need to toggle
            if (current_state == '1' and enable) or (current_state == '0' and not enable):
                logger.info(f"Airplane mode is already {'ON' if enable else 'OFF'}")
                return True, f"Airplane mode is already {'ON' if enable else 'OFF'}"
            
            logger.info(f"Toggling airplane mode {'ON' if enable else 'OFF'}")
            
            # Set the new state
            new_state = '1' if enable else '0'
            self.execute_adb_command(
                device_serial, ['shell', 'settings', 'put', 'global', 'airplane_mode_on', new_state]
            )
            
            # Broadcast the change so the device takes action
            self.execute_adb_command(
                device_serial, 
                ['shell', 'am', 'broadcast', '-a', 'android.intent.action.AIRPLANE_MODE', 
                 '--ez', 'state', 'true' if enable else 'false']
            )
            
            # Wait for the change to take effect
            time.sleep(2)
            
            # Verify the change
            updated_state = self.execute_adb_command(
                device_serial, ['shell', 'settings', 'get', 'global', 'airplane_mode_on']
            )
            success = updated_state == new_state
            
            if not success:
                logger.error(f"Failed to toggle airplane mode: Current state is {updated_state}")
                return False, f"Failed to toggle airplane mode: Current state is {updated_state}"
            
            # If disabling airplane mode, wait for network to reconnect
            if not enable:
                result = "Airplane mode turned OFF. "
                logger.info("Waiting for network to reconnect...")
                time.sleep(5)  # Give it time to reconnect
                
                # Get the new IP
                new_ip = self.get_device_ip(device_serial)
                
                if new_ip:
                    logger.info(f"Network reconnected with IP: {new_ip}")
                    result += f"Network reconnected with IP: {new_ip}"
                    
                    if old_ip and old_ip != new_ip:
                        logger.info(f"IP changed from {old_ip} to {new_ip}")
                        result += f"\nIP successfully rotated from {old_ip} to {new_ip}"
                    elif old_ip:
                        logger.warning(f"IP did not change: {old_ip}")
                        result += f"\nWarning: IP did not change from {old_ip}"
                else:
                    logger.warning("Network did not reconnect or IP could not be determined")
                    result += "Warning: Network did not reconnect or IP could not be determined"
            else:
                result = "Airplane mode turned ON."
            
            return True, result
            
        except Exception as e:
            logger.error(f"Error toggling airplane mode: {str(e)}")
            return False, f"Error: {str(e)}"
    
    def test_airplane_mode_toggle(self, device_serial):
        """Test toggling airplane mode on and off"""
        results = {
            'initial_state': None,
            'enable_success': False,
            'disable_success': False,
            'initial_ip': None,
            'final_ip': None,
            'ip_changed': False,
            'airplane_mode_working': False
        }
        
        try:
            # Get initial state
            initial_state = self.check_airplane_mode(device_serial)
            results['initial_state'] = initial_state
            
            # Get initial IP
            initial_ip = self.get_device_ip(device_serial)
            results['initial_ip'] = initial_ip
            
            # Turn airplane mode ON
            logger.info("Testing: Turning airplane mode ON")
            enable_success, enable_message = self.toggle_airplane_mode(device_serial, enable=True)
            results['enable_success'] = enable_success
            
            if not enable_success:
                logger.error("Failed to enable airplane mode")
                results['airplane_mode_working'] = False
                return results
            
            # Wait a bit
            time.sleep(3)
            
            # Turn airplane mode OFF
            logger.info("Testing: Turning airplane mode OFF")
            disable_success, disable_message = self.toggle_airplane_mode(device_serial, enable=False)
            results['disable_success'] = disable_success
            
            if not disable_success:
                logger.error("Failed to disable airplane mode")
                results['airplane_mode_working'] = False
                return results
            
            # Wait for network to reconnect
            time.sleep(5)
            
            # Get final IP
            final_ip = self.get_device_ip(device_serial)
            results['final_ip'] = final_ip
            
            # Check if IP changed
            if initial_ip and final_ip:
                results['ip_changed'] = initial_ip != final_ip
                
            # Overall success
            results['airplane_mode_working'] = enable_success and disable_success
            
            # If everything went well but IP didn't change, still consider it a success
            # as some providers might not change IP with this method
            if results['airplane_mode_working'] and not results['ip_changed']:
                logger.warning("Airplane mode toggle worked but IP did not change")
            
            # Restore original state if needed
            if initial_state is not None and initial_state != self.check_airplane_mode(device_serial):
                self.toggle_airplane_mode(device_serial, enable=initial_state)
            
            return results
            
        except Exception as e:
            logger.error(f"Error testing airplane mode toggle: {str(e)}")
            results['airplane_mode_working'] = False
            return results
    
    def run_full_verification(self, device_serial=None):
        """Run a complete verification of the phone setup"""
        results = {}
        
        # Step 1: Check if ADB is installed
        logger.info("Step 1: Checking ADB installation")
        adb_success, adb_message = self.check_adb_installed()
        results['adb_installed'] = adb_success
        results['adb_message'] = adb_message
        
        if not adb_success:
            logger.error("ADB is not installed or not working. Verification failed.")
            results['overall_success'] = False
            return results
        
        # Step 2: Start ADB server
        logger.info("Step 2: Starting ADB server")
        server_success, server_message = self.start_adb_server()
        results['adb_server_started'] = server_success
        results['adb_server_message'] = server_message
        
        # Step 3: Find connected devices
        logger.info("Step 3: Finding connected devices")
        devices = self.find_connected_devices()
        results['devices_found'] = len(devices)
        results['device_list'] = devices
        
        if not devices:
            logger.error("No devices found. Verification failed.")
            results['overall_success'] = False
            return results
        
        # If no specific device is specified, use the first one
        if device_serial is None:
            device_serial = devices[0]
        
        results['selected_device'] = device_serial
        
        # Step 4: Get device info
        logger.info(f"Step 4: Getting device info for {device_serial}")
        device_info = self.get_device_info(device_serial)
        results['device_info'] = device_info
        
        # Step 5: Check airplane mode
        logger.info("Step 5: Checking airplane mode")
        airplane_mode = self.check_airplane_mode(device_serial)
        results['airplane_mode_status'] = airplane_mode
        
        # Step 6: Test airplane mode toggle
        logger.info("Step 6: Testing airplane mode toggle")
        toggle_results = self.test_airplane_mode_toggle(device_serial)
        results.update(toggle_results)
        
        # Overall success
        results['overall_success'] = (
            adb_success and 
            server_success and 
            len(devices) > 0 and 
            toggle_results['airplane_mode_working']
        )
        
        # Record result message
        if results['overall_success']:
            if toggle_results['ip_changed']:
                results['message'] = "Phone verification successful! Device is properly connected and IP rotation is working correctly."
            else:
                results['message'] = "Phone verification partially successful. Device is connected and airplane mode toggle works, but IP did not change during test. This might be due to carrier policies."
        else:
            results['message'] = "Phone verification failed. Please check the detailed results for specific issues."
        
        return results

class PhoneVerificationGUI:
    """GUI for phone verification tool"""
    
    def __init__(self, master):
        """Initialize the GUI"""
        self.master = master
        self.master.title("TextNow Max - Phone Verification Tool")
        self.master.geometry("800x600")
        self.master.resizable(True, True)
        
        # Set icon if available
        try:
            self.master.iconbitmap('app_icon.ico')
        except:
            pass
        
        self.verifier = PhoneVerifier()
        self.device_dropdown = None
        self.devices = []
        self.verification_running = False
        
        self.create_widgets()
        
        # Automatically check ADB installation on startup
        self.check_adb_installation()
    
    def create_widgets(self):
        """Create GUI widgets"""
        # Create main frame
        main_frame = ttk.Frame(self.master, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title label
        title_label = ttk.Label(main_frame, text="Android Phone Verification Tool", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        # Subtitle label
        subtitle_label = ttk.Label(main_frame, text="Verify your Android phone setup for IP rotation")
        subtitle_label.pack(pady=5)
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.pack(fill=tk.X, pady=10)
        
        # ADB status
        adb_frame = ttk.Frame(status_frame)
        adb_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(adb_frame, text="ADB Installation:").pack(side=tk.LEFT, padx=5)
        self.adb_status_label = ttk.Label(adb_frame, text="Checking...", foreground="gray")
        self.adb_status_label.pack(side=tk.LEFT, padx=5)
        
        # Check ADB button
        self.check_adb_button = ttk.Button(adb_frame, text="Check Again", command=self.check_adb_installation)
        self.check_adb_button.pack(side=tk.RIGHT, padx=5)
        
        # Device selection frame
        device_frame = ttk.LabelFrame(main_frame, text="Device Selection", padding="10")
        device_frame.pack(fill=tk.X, pady=10)
        
        # Device dropdown
        ttk.Label(device_frame, text="Select Device:").pack(side=tk.LEFT, padx=5)
        
        self.device_var = tk.StringVar()
        self.device_dropdown = ttk.Combobox(device_frame, textvariable=self.device_var, state="readonly", width=30)
        self.device_dropdown.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Refresh devices button
        self.refresh_button = ttk.Button(device_frame, text="Refresh Devices", command=self.refresh_devices)
        self.refresh_button.pack(side=tk.RIGHT, padx=5)
        
        # Device info frame
        self.device_info_frame = ttk.LabelFrame(main_frame, text="Device Information", padding="10")
        self.device_info_frame.pack(fill=tk.X, pady=10)
        
        # Device info content (will be populated when a device is selected)
        self.device_info_content = ttk.Frame(self.device_info_frame)
        self.device_info_content.pack(fill=tk.X, expand=True)
        
        # Placeholder for device info
        ttk.Label(self.device_info_content, text="Select a device to view its information").pack(pady=10)
        
        # Action buttons frame
        action_frame = ttk.Frame(main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        
        # Verification button
        self.verify_button = ttk.Button(
            action_frame, 
            text="Run Full Verification", 
            command=self.run_verification,
            style="Accent.TButton"
        )
        self.verify_button.pack(side=tk.LEFT, padx=5)
        
        # IP test button
        self.ip_test_button = ttk.Button(
            action_frame,
            text="Test IP Rotation",
            command=self.test_ip_rotation
        )
        self.ip_test_button.pack(side=tk.LEFT, padx=5)
        
        # Get device info button
        self.info_button = ttk.Button(
            action_frame, 
            text="Get Device Info", 
            command=self.refresh_device_info
        )
        self.info_button.pack(side=tk.LEFT, padx=5)
        
        # Close button
        self.close_button = ttk.Button(
            action_frame, 
            text="Close", 
            command=self.master.destroy
        )
        self.close_button.pack(side=tk.RIGHT, padx=5)
        
        # Log frame
        log_frame = ttk.LabelFrame(main_frame, text="Verification Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Log text widget
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)
        
        # Add initial log entry
        self.add_log("Phone Verification Tool started. Please select a device to verify.")
        
        # Setup device selection callback
        self.device_dropdown.bind("<<ComboboxSelected>>", self.on_device_selected)
        
        # Initial device refresh
        self.refresh_devices()
    
    def check_adb_installation(self):
        """Check if ADB is installed and update status"""
        self.adb_status_label.config(text="Checking...", foreground="gray")
        self.master.update_idletasks()
        
        success, message = self.verifier.check_adb_installed()
        
        if success:
            self.adb_status_label.config(text=f"Installed ({message})", foreground="green")
            self.add_log(f"ADB is installed: {message}")
        else:
            self.adb_status_label.config(text=f"Not installed: {message}", foreground="red")
            self.add_log(f"ADB is not installed: {message}")
            messagebox.showerror(
                "ADB Not Found", 
                "Android Debug Bridge (ADB) is not installed or not in PATH.\n\n"
                "Please install Android SDK Platform Tools and add it to your PATH, "
                "or place the ADB executable in the same folder as this application."
            )
    
    def refresh_devices(self):
        """Refresh the device list"""
        # Start ADB server first
        self.verifier.start_adb_server()
        
        # Get devices
        self.devices = self.verifier.find_connected_devices()
        
        # Update dropdown
        if not self.devices:
            self.device_dropdown['values'] = ["No devices found"]
            self.device_dropdown.current(0)
            self.device_var.set("No devices found")
            self.add_log("No devices found. Please connect an Android device via USB and enable USB debugging.")
            self.verify_button.config(state=tk.DISABLED)
            self.ip_test_button.config(state=tk.DISABLED)
            self.info_button.config(state=tk.DISABLED)
        else:
            self.device_dropdown['values'] = self.devices
            self.device_dropdown.current(0)
            self.add_log(f"Found {len(self.devices)} connected device(s): {', '.join(self.devices)}")
            self.verify_button.config(state=tk.NORMAL)
            self.ip_test_button.config(state=tk.NORMAL)
            self.info_button.config(state=tk.NORMAL)
            # Automatically select the first device and get its info
            self.on_device_selected(None)
    
    def on_device_selected(self, event):
        """Handle device selection"""
        selected = self.device_var.get()
        
        # Check if a valid device is selected
        if selected and selected != "No devices found":
            self.add_log(f"Selected device: {selected}")
            self.refresh_device_info()
    
    def refresh_device_info(self):
        """Refresh device information"""
        selected = self.device_var.get()
        
        # Check if a valid device is selected
        if not selected or selected == "No devices found":
            return
        
        # Clear current info
        for widget in self.device_info_content.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = ttk.Label(self.device_info_content, text="Loading device information...")
        loading_label.pack(pady=10)
        self.master.update_idletasks()
        
        # Get device info
        device_info = self.verifier.get_device_info(selected)
        
        # Remove loading message
        loading_label.destroy()
        
        # Create grid for device info
        info_grid = ttk.Frame(self.device_info_content)
        info_grid.pack(fill=tk.X, expand=True, pady=5)
        
        # Add device info to grid
        row = 0
        for key, value in device_info.items():
            if key != 'serial' and value is not None:  # Skip serial (already shown) and None values
                # Format key for display
                display_key = key.replace('_', ' ').title()
                
                # Create label for key
                key_label = ttk.Label(info_grid, text=f"{display_key}:", width=20, anchor=tk.W)
                key_label.grid(row=row, column=0, sticky=tk.W, padx=5, pady=2)
                
                # Create label for value
                value_label = ttk.Label(info_grid, text=str(value), anchor=tk.W)
                value_label.grid(row=row, column=1, sticky=tk.W, padx=5, pady=2)
                
                row += 1
        
        # Add message if no info is available
        if row == 0:
            ttk.Label(info_grid, text="No device information available").grid(row=0, column=0, columnspan=2, pady=10)
        
        # Check airplane mode
        airplane_frame = ttk.Frame(self.device_info_content)
        airplane_frame.pack(fill=tk.X, pady=10)
        
        airplane_mode = self.verifier.check_airplane_mode(selected)
        
        ttk.Label(airplane_frame, text="Airplane Mode:").pack(side=tk.LEFT, padx=5)
        
        if airplane_mode is None:
            status_text = "Unknown"
            status_color = "gray"
        elif airplane_mode:
            status_text = "ON"
            status_color = "red"
        else:
            status_text = "OFF"
            status_color = "green"
        
        status_label = ttk.Label(airplane_frame, text=status_text, foreground=status_color)
        status_label.pack(side=tk.LEFT, padx=5)
        
        # Add buttons to toggle airplane mode
        ttk.Button(
            airplane_frame, 
            text="Turn ON", 
            command=lambda: self.toggle_airplane_mode(True)
        ).pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(
            airplane_frame, 
            text="Turn OFF", 
            command=lambda: self.toggle_airplane_mode(False)
        ).pack(side=tk.RIGHT, padx=5)
        
        self.add_log(f"Retrieved information for device: {selected}")
    
    def toggle_airplane_mode(self, enable):
        """Toggle airplane mode on the selected device"""
        selected = self.device_var.get()
        
        # Check if a valid device is selected
        if not selected or selected == "No devices found":
            return
        
        # Show status
        self.add_log(f"Toggling airplane mode {'ON' if enable else 'OFF'} for device: {selected}")
        
        # Disable buttons during toggle
        self.verify_button.config(state=tk.DISABLED)
        self.ip_test_button.config(state=tk.DISABLED)
        self.info_button.config(state=tk.DISABLED)
        self.master.update_idletasks()
        
        # Toggle airplane mode
        success, message = self.verifier.toggle_airplane_mode(selected, enable)
        
        # Log result
        if success:
            self.add_log(f"Airplane mode toggle successful: {message}")
        else:
            self.add_log(f"Airplane mode toggle failed: {message}")
            messagebox.showerror("Airplane Mode Toggle Failed", message)
        
        # Re-enable buttons
        self.verify_button.config(state=tk.NORMAL)
        self.ip_test_button.config(state=tk.NORMAL)
        self.info_button.config(state=tk.NORMAL)
        
        # Refresh device info
        self.refresh_device_info()
    
    def test_ip_rotation(self):
        """Test IP rotation by toggling airplane mode"""
        selected = self.device_var.get()
        
        # Check if a valid device is selected
        if not selected or selected == "No devices found":
            return
        
        # Confirm with user
        if not messagebox.askyesno(
            "Test IP Rotation", 
            "This will toggle airplane mode ON and then OFF to test IP rotation. "
            "Your device will temporarily disconnect from the network.\n\n"
            "Do you want to continue?"
        ):
            return
        
        # Show status
        self.add_log(f"Testing IP rotation for device: {selected}")
        
        # Disable buttons during test
        self.verify_button.config(state=tk.DISABLED)
        self.ip_test_button.config(state=tk.DISABLED)
        self.info_button.config(state=tk.DISABLED)
        self.master.update_idletasks()
        
        # Start test in a separate thread
        threading.Thread(target=self._run_ip_rotation_test, args=(selected,), daemon=True).start()
    
    def _run_ip_rotation_test(self, device_serial):
        """Run IP rotation test in a separate thread"""
        try:
            # Get initial IP
            self.add_log("Getting initial IP address...")
            initial_ip = self.verifier.get_device_ip(device_serial)
            
            if initial_ip is None:
                self.add_log("Could not determine initial IP address. Test failed.")
                messagebox.showerror(
                    "IP Rotation Test Failed", 
                    "Could not determine initial IP address. Make sure your device is connected to the network."
                )
                self._enable_buttons()
                return
            
            self.add_log(f"Initial IP address: {initial_ip}")
            
            # Turn airplane mode ON
            self.add_log("Turning airplane mode ON...")
            success, message = self.verifier.toggle_airplane_mode(device_serial, True)
            
            if not success:
                self.add_log(f"Failed to turn airplane mode ON: {message}")
                messagebox.showerror("IP Rotation Test Failed", f"Failed to turn airplane mode ON: {message}")
                self._enable_buttons()
                return
            
            self.add_log("Airplane mode turned ON successfully")
            time.sleep(3)  # Wait a bit
            
            # Turn airplane mode OFF
            self.add_log("Turning airplane mode OFF...")
            success, message = self.verifier.toggle_airplane_mode(device_serial, False)
            
            if not success:
                self.add_log(f"Failed to turn airplane mode OFF: {message}")
                messagebox.showerror("IP Rotation Test Failed", f"Failed to turn airplane mode OFF: {message}")
                self._enable_buttons()
                return
            
            self.add_log("Airplane mode turned OFF successfully")
            self.add_log("Waiting for network to reconnect...")
            time.sleep(5)  # Wait for network to reconnect
            
            # Get new IP
            self.add_log("Getting new IP address...")
            new_ip = self.verifier.get_device_ip(device_serial)
            
            if new_ip is None:
                self.add_log("Could not determine new IP address. Test failed.")
                messagebox.showerror(
                    "IP Rotation Test Failed", 
                    "Could not determine new IP address after turning airplane mode OFF."
                )
                self._enable_buttons()
                return
            
            self.add_log(f"New IP address: {new_ip}")
            
            # Check if IP changed
            if initial_ip == new_ip:
                self.add_log("IP address did not change. This might be due to carrier policies.")
                messagebox.showwarning(
                    "IP Rotation Test", 
                    f"IP address did not change after toggling airplane mode:\n"
                    f"Initial IP: {initial_ip}\n"
                    f"New IP: {new_ip}\n\n"
                    f"This might be due to carrier policies or the way your network is configured. "
                    f"Some carriers don't assign a new IP when reconnecting."
                )
            else:
                self.add_log(f"IP address changed successfully from {initial_ip} to {new_ip}")
                messagebox.showinfo(
                    "IP Rotation Test Successful", 
                    f"IP address changed successfully:\n"
                    f"Initial IP: {initial_ip}\n"
                    f"New IP: {new_ip}"
                )
        
        except Exception as e:
            self.add_log(f"Error during IP rotation test: {str(e)}")
            messagebox.showerror("IP Rotation Test Error", f"An error occurred: {str(e)}")
        
        finally:
            # Re-enable buttons
            self._enable_buttons()
            
            # Refresh device info
            self.refresh_device_info()
    
    def run_verification(self):
        """Run the full verification process"""
        selected = self.device_var.get()
        
        # Check if a valid device is selected
        if not selected or selected == "No devices found":
            return
        
        # Confirm with user
        if not messagebox.askyesno(
            "Run Verification", 
            "This will run a full verification of your phone setup, including testing airplane mode toggle "
            "and IP rotation. Your device will temporarily disconnect from the network.\n\n"
            "Do you want to continue?"
        ):
            return
        
        # Show status
        self.add_log("\n--- Starting full verification ---")
        self.add_log(f"Verifying device: {selected}")
        
        # Clear log except the last few lines
        log_text = self.log_text.get("1.0", tk.END)
        log_lines = log_text.split('\n')
        if len(log_lines) > 30:
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert(tk.END, '\n'.join(log_lines[-30:]) + '\n')
            self.log_text.config(state=tk.DISABLED)
            self.log_text.see(tk.END)
        
        # Disable buttons during verification
        self.verify_button.config(state=tk.DISABLED)
        self.ip_test_button.config(state=tk.DISABLED)
        self.info_button.config(state=tk.DISABLED)
        self.master.update_idletasks()
        
        # Start verification in a separate thread
        self.verification_running = True
        threading.Thread(target=self._run_verification_thread, args=(selected,), daemon=True).start()
    
    def _run_verification_thread(self, device_serial):
        """Run verification in a separate thread"""
        try:
            # Run verification
            self.add_log("Running verification...")
            results = self.verifier.run_full_verification(device_serial)
            
            # Display results
            self.add_log("\n--- Verification Results ---")
            
            # ADB installation
            self.add_log(f"ADB Installation: {'✓ Installed' if results['adb_installed'] else '✗ Not installed'}")
            self.add_log(f"  {results['adb_message']}")
            
            # Connected devices
            self.add_log(f"Connected Devices: {'✓ ' + str(results['devices_found']) + ' found' if results['devices_found'] > 0 else '✗ None found'}")
            if results['devices_found'] > 0:
                self.add_log(f"  Selected device: {results['selected_device']}")
            
            # Device info
            if 'device_info' in results and results['device_info']:
                info = results['device_info']
                self.add_log(f"Device Information:")
                self.add_log(f"  Model: {info.get('model', 'Unknown')}")
                self.add_log(f"  Manufacturer: {info.get('manufacturer', 'Unknown')}")
                self.add_log(f"  Android Version: {info.get('android_version', 'Unknown')}")
                self.add_log(f"  IP Address: {info.get('ip_address', 'Unknown')}")
            
            # Airplane mode
            if 'airplane_mode_status' in results:
                status = results['airplane_mode_status']
                self.add_log(f"Initial Airplane Mode: {'ON' if status else 'OFF' if status is not None else 'Unknown'}")
            
            # Airplane mode toggle
            self.add_log(f"Airplane Mode Toggle: {'✓ Working' if results['airplane_mode_working'] else '✗ Not working'}")
            if results['airplane_mode_working']:
                self.add_log(f"  Enable success: {'✓ Yes' if results['enable_success'] else '✗ No'}")
                self.add_log(f"  Disable success: {'✓ Yes' if results['disable_success'] else '✗ No'}")
            
            # IP rotation
            if 'initial_ip' in results and 'final_ip' in results:
                self.add_log(f"IP Rotation:")
                self.add_log(f"  Initial IP: {results['initial_ip'] or 'Unknown'}")
                self.add_log(f"  Final IP: {results['final_ip'] or 'Unknown'}")
                self.add_log(f"  IP Changed: {'✓ Yes' if results['ip_changed'] else '✗ No'}")
            
            # Overall result
            self.add_log(f"\nOverall Result: {'✓ Success' if results['overall_success'] else '✗ Failed'}")
            self.add_log(f"Message: {results['message']}")
            
            # Show message box with results
            if results['overall_success']:
                messagebox.showinfo(
                    "Verification Successful", 
                    results['message'] + "\n\nYour phone setup is ready for use with TextNow Max."
                )
            else:
                messagebox.showerror(
                    "Verification Failed", 
                    results['message'] + "\n\nPlease check the verification log for details."
                )
        
        except Exception as e:
            self.add_log(f"Error during verification: {str(e)}")
            messagebox.showerror("Verification Error", f"An error occurred: {str(e)}")
        
        finally:
            # Re-enable buttons
            self._enable_buttons()
            
            # Refresh device info
            self.refresh_device_info()
            
            self.verification_running = False
    
    def _enable_buttons(self):
        """Re-enable buttons on the main thread"""
        self.master.after(0, lambda: self.verify_button.config(state=tk.NORMAL))
        self.master.after(0, lambda: self.ip_test_button.config(state=tk.NORMAL))
        self.master.after(0, lambda: self.info_button.config(state=tk.NORMAL))
    
    def add_log(self, message):
        """Add a message to the log text widget"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state=tk.DISABLED)
        self.log_text.see(tk.END)
        self.master.update_idletasks()

def main():
    """Main function to run the phone verification tool"""
    root = tk.Tk()
    PhoneVerificationGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()