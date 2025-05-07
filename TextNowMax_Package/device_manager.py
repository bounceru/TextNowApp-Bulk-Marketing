"""
Device Manager for TextNow Max Creator

This module handles communication with Android devices, including:
- Connecting to any Android phone via ADB
- Toggling airplane mode for IP rotation
- Getting the current IP address
- Monitoring device status
- Supporting a wide range of Android devices (not just BLU G44)
"""

import os
import time
import logging
import subprocess
import re
import signal
import threading
import queue
import json
from typing import Optional, Dict, List, Tuple, Any
from contextlib import contextmanager

# Import database for logging
from database_schema import get_database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('device_manager.log')
    ]
)
logger = logging.getLogger('DeviceManager')

class DeviceManager:
    """Class to handle device management for IP rotation"""
    
    def __init__(self, adb_path=None, device_serial=None):
        """Initialize the device manager with optional ADB path and device serial number"""
        self.adb_path = adb_path or self._find_adb_path()
        self.device_serial = device_serial
        self.should_stop = threading.Event()
        self.command_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.monitoring_thread = None
        self.current_ip = None
        self.database = get_database()
        
        # Check if ADB is available
        if not self._check_adb_available():
            logger.error("ADB is not available. Please make sure it's installed and in PATH.")
        
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
        
        # Get from database settings if available
        try:
            db_adb_path = self.database.get_setting_value('device', 'adb_path')
            if db_adb_path:
                return db_adb_path
        except:
            pass
            
        logger.warning("Could not find ADB path automatically")
        return 'adb'  # Default fallback
    
    def _check_adb_available(self):
        """Check if ADB is available and working"""
        try:
            result = subprocess.run(
                [self.adb_path, 'version'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                logger.info(f"ADB is available: {result.stdout.splitlines()[0]}")
                return True
            else:
                logger.error(f"ADB error: {result.stderr}")
                return False
        except (subprocess.SubprocessError, FileNotFoundError) as e:
            logger.error(f"Error checking ADB: {str(e)}")
            return False
    
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
    
    def select_device(self, device_serial=None):
        """Select a device to work with, either by serial or automatically"""
        if device_serial:
            self.device_serial = device_serial
            logger.info(f"Selected device: {device_serial}")
            return device_serial
        
        # Find connected devices
        devices = self.find_connected_devices()
        if not devices:
            logger.error("No devices connected")
            return None
        
        # Use any Android device, but log the model for information
        self.device_serial = devices[0]
        model = self.get_device_model(self.device_serial)
        
        if model:
            logger.info(f"Selected device: {self.device_serial} (Model: {model})")
        else:
            logger.info(f"Selected device: {self.device_serial} (Model unknown)")
            
        return self.device_serial
    
    def get_device_model(self, device_serial=None):
        """Get the model of the device"""
        serial = device_serial or self.device_serial
        if not serial:
            logger.error("No device selected")
            return None
        
        try:
            # Run ADB command to get device model
            result = subprocess.run(
                [self.adb_path, '-s', serial, 'shell', 'getprop', 'ro.product.model'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                logger.error(f"ADB error: {result.stderr}")
                return None
            
            model = result.stdout.strip()
            logger.info(f"Device model: {model}")
            return model
        except subprocess.SubprocessError as e:
            logger.error(f"Error getting device model: {str(e)}")
            return None
    
    def execute_adb_command(self, command, timeout=30):
        """Execute an ADB command on the selected device"""
        if not self.device_serial:
            logger.error("No device selected")
            return None
        
        try:
            # Prepare the full command
            full_command = [self.adb_path, '-s', self.device_serial] + command
            
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
    
    def toggle_airplane_mode(self, enable=True):
        """Toggle airplane mode on the device"""
        if not self.device_serial:
            logger.error("No device selected")
            return False
        
        try:
            # Save current IP before toggling
            old_ip = self.get_current_ip()
            
            # Time how long the operation takes
            start_time = time.time()
            
            # First, check the current state
            current_state = self.execute_adb_command(['shell', 'settings', 'get', 'global', 'airplane_mode_on'])
            
            # If current state matches what we want, no need to toggle
            if (current_state == '1' and enable) or (current_state == '0' and not enable):
                logger.info(f"Airplane mode is already {'ON' if enable else 'OFF'}")
                return True
            
            logger.info(f"Toggling airplane mode {'ON' if enable else 'OFF'}")
            
            # Set the new state
            new_state = '1' if enable else '0'
            self.execute_adb_command(['shell', 'settings', 'put', 'global', 'airplane_mode_on', new_state])
            
            # Broadcast the change so the device takes action
            self.execute_adb_command([
                'shell', 'am', 'broadcast', 
                '-a', 'android.intent.action.AIRPLANE_MODE', 
                '--ez', 'state', 'true' if enable else 'false'
            ])
            
            # Wait for the change to take effect
            time.sleep(2)
            
            # Verify the change
            updated_state = self.execute_adb_command(['shell', 'settings', 'get', 'global', 'airplane_mode_on'])
            success = updated_state == new_state
            
            if not success:
                logger.error(f"Failed to toggle airplane mode: Current state is {updated_state}")
                return False
            
            # If disabling airplane mode, wait for network to reconnect
            if not enable:
                logger.info("Waiting for network to reconnect...")
                time.sleep(8)  # Give it time to reconnect
                
                # Get the new IP
                new_ip = self.get_current_ip()
                self.current_ip = new_ip
                
                # Calculate duration
                duration = int(time.time() - start_time)
                
                # Log the IP rotation in the database
                self.database.log_ip_rotation(
                    old_ip=old_ip,
                    new_ip=new_ip,
                    success=new_ip is not None,
                    duration=duration,
                    device_id=self.device_serial,
                    notes=f"Airplane mode toggle: {current_state} -> {updated_state}"
                )
                
                logger.info(f"IP rotation complete. Old IP: {old_ip}, New IP: {new_ip}, Duration: {duration}s")
            
            return True
        except Exception as e:
            logger.error(f"Error toggling airplane mode: {str(e)}")
            return False
    
    def get_current_ip(self):
        """Get the current IP address of the device"""
        if not self.device_serial:
            logger.error("No device selected")
            return None
        
        try:
            # Method 1: Try using ip addr show
            ip_data = self.execute_adb_command(['shell', 'ip', 'addr', 'show', 'wlan0'])
            if ip_data:
                ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_data)
                if ip_match:
                    return ip_match.group(1)
            
            # Method 2: Try using ifconfig
            ip_data = self.execute_adb_command(['shell', 'ifconfig', 'wlan0'])
            if ip_data:
                ip_match = re.search(r'inet addr:(\d+\.\d+\.\d+\.\d+)', ip_data)
                if ip_match:
                    return ip_match.group(1)
            
            # Method 3: Try getting the external IP
            try:
                # First check if we have curl
                curl_version = self.execute_adb_command(['shell', 'curl', '--version'])
                if curl_version:
                    external_ip = self.execute_adb_command(['shell', 'curl', '-s', 'ifconfig.me'])
                    if external_ip and len(external_ip) > 0 and '.' in external_ip:
                        return external_ip
            except:
                logger.warning("Could not use curl to get external IP")
            
            # Method 4: Try using a different network interface
            interfaces = ['rmnet0', 'rmnet_data0', 'eth0']
            for interface in interfaces:
                ip_data = self.execute_adb_command(['shell', 'ip', 'addr', 'show', interface])
                if ip_data:
                    ip_match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)', ip_data)
                    if ip_match:
                        return ip_match.group(1)
            
            logger.warning("Could not determine device IP address")
            return None
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            return None
    
    def rotate_ip(self):
        """Rotate the IP address by toggling airplane mode"""
        if not self.device_serial:
            logger.error("No device selected")
            return False
        
        try:
            # Enable airplane mode
            logger.info("Enabling airplane mode")
            if not self.toggle_airplane_mode(enable=True):
                logger.error("Failed to enable airplane mode")
                return False
            
            # Wait a few seconds
            time.sleep(5)
            
            # Disable airplane mode to get a new IP
            logger.info("Disabling airplane mode to get new IP")
            if not self.toggle_airplane_mode(enable=False):
                logger.error("Failed to disable airplane mode")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error rotating IP: {str(e)}")
            return False
    
    def start_monitoring(self):
        """Start a background thread to monitor the device"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        self.should_stop.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        logger.info("Device monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.info("Stopping device monitoring...")
            self.should_stop.set()
            self.monitoring_thread.join(timeout=10)
            logger.info("Device monitoring stopped")
    
    def _monitoring_loop(self):
        """Background loop to monitor the device and process commands"""
        logger.info("Device monitoring loop started")
        
        check_interval = 30  # Check device every 30 seconds
        last_check_time = 0
        
        while not self.should_stop.is_set():
            try:
                # Process any commands in the queue
                try:
                    command, args, kwargs = self.command_queue.get(block=False)
                    try:
                        result = command(*args, **kwargs)
                        self.response_queue.put((True, result))
                    except Exception as e:
                        logger.error(f"Error executing command {command.__name__}: {str(e)}")
                        self.response_queue.put((False, str(e)))
                    finally:
                        self.command_queue.task_done()
                except queue.Empty:
                    pass
                
                # Check device status periodically
                current_time = time.time()
                if current_time - last_check_time >= check_interval:
                    self._check_device_status()
                    last_check_time = current_time
                
                # Don't hog the CPU
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(5)  # Wait a bit longer if there's an error
    
    def _check_device_status(self):
        """Check the status of the device"""
        try:
            # Check if device is still connected
            devices = self.find_connected_devices()
            if not devices or self.device_serial not in devices:
                logger.warning(f"Device {self.device_serial} is no longer connected")
                # Log the error in the database
                self.database.log_error(
                    error_type="device_disconnect",
                    component="device_manager",
                    details=f"Device {self.device_serial} disconnected",
                    account_id=None
                )
                return False
            
            # Get current IP
            current_ip = self.get_current_ip()
            if current_ip != self.current_ip:
                if self.current_ip is not None:
                    logger.info(f"IP address changed: {self.current_ip} -> {current_ip}")
                self.current_ip = current_ip
            
            # Check battery level
            battery_level = self._get_battery_level()
            if battery_level is not None and battery_level < 20:
                logger.warning(f"Low battery level: {battery_level}%")
                
            return True
        except Exception as e:
            logger.error(f"Error checking device status: {str(e)}")
            return False
    
    def _get_battery_level(self):
        """Get the battery level of the device"""
        try:
            battery_info = self.execute_adb_command(['shell', 'dumpsys', 'battery'])
            if battery_info:
                level_match = re.search(r'level:\s*(\d+)', battery_info)
                if level_match:
                    return int(level_match.group(1))
            return None
        except Exception as e:
            logger.error(f"Error getting battery level: {str(e)}")
            return None
    
    def execute_command_async(self, command, *args, **kwargs):
        """Execute a command asynchronously by passing it to the monitoring thread"""
        if not self.monitoring_thread or not self.monitoring_thread.is_alive():
            logger.error("Monitoring thread is not running")
            return None
        
        self.command_queue.put((command, args, kwargs))
        try:
            success, result = self.response_queue.get(timeout=60)
            if success:
                return result
            else:
                logger.error(f"Command failed: {result}")
                return None
        except queue.Empty:
            logger.error("Timeout waiting for command response")
            return None
    
    def check_connection(self):
        """Check if the device is connected and responding"""
        if not self.device_serial:
            logger.error("No device selected")
            return False
        
        try:
            # Try to execute a simple command
            result = self.execute_adb_command(['shell', 'echo', 'hello'])
            return result == 'hello'
        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False
    
    def restart_adb_server(self):
        """Restart the ADB server"""
        try:
            # Kill server
            logger.info("Killing ADB server")
            subprocess.run(
                [self.adb_path, 'kill-server'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=10
            )
            
            time.sleep(2)
            
            # Start server
            logger.info("Starting ADB server")
            subprocess.run(
                [self.adb_path, 'start-server'], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=10
            )
            
            time.sleep(3)
            
            # Check if devices are connected
            devices = self.find_connected_devices()
            return len(devices) > 0
        except subprocess.SubprocessError as e:
            logger.error(f"Error restarting ADB server: {str(e)}")
            return False
    
    def get_device_info(self):
        """Get detailed information about the device"""
        if not self.device_serial:
            logger.error("No device selected")
            return {}
        
        try:
            info = {}
            
            # Get basic device info
            info['serial'] = self.device_serial
            info['model'] = self.get_device_model()
            info['ip_address'] = self.get_current_ip()
            
            # Get Android version
            android_version = self.execute_adb_command(['shell', 'getprop', 'ro.build.version.release'])
            info['android_version'] = android_version
            
            # Get device name
            device_name = self.execute_adb_command(['shell', 'getprop', 'ro.product.name'])
            info['device_name'] = device_name
            
            # Get manufacturer
            manufacturer = self.execute_adb_command(['shell', 'getprop', 'ro.product.manufacturer'])
            info['manufacturer'] = manufacturer
            
            # Get more device details
            info['sdk_version'] = self.execute_adb_command(['shell', 'getprop', 'ro.build.version.sdk'])
            info['product_model'] = self.execute_adb_command(['shell', 'getprop', 'ro.product.model'])
            info['build_id'] = self.execute_adb_command(['shell', 'getprop', 'ro.build.id'])
            
            # Get network details
            info['wifi_mac'] = self.execute_adb_command(['shell', 'cat', '/sys/class/net/wlan0/address'])
            
            # Get airplane mode status
            airplane_mode = self.execute_adb_command(['shell', 'settings', 'get', 'global', 'airplane_mode_on'])
            info['airplane_mode'] = (airplane_mode == '1')
            
            # Get battery info
            battery_info = self.execute_adb_command(['shell', 'dumpsys', 'battery'])
            if battery_info:
                battery_level_match = re.search(r'level:\s*(\d+)', battery_info)
                if battery_level_match:
                    info['battery_level'] = int(battery_level_match.group(1))
                
                battery_status_match = re.search(r'status:\s*(\d+)', battery_info)
                if battery_status_match:
                    status_code = int(battery_status_match.group(1))
                    # Convert status code to string
                    status_map = {
                        1: 'unknown',
                        2: 'charging',
                        3: 'discharging',
                        4: 'not charging',
                        5: 'full'
                    }
                    info['battery_status'] = status_map.get(status_code, 'unknown')
            
            # Get airplane mode status
            airplane_mode = self.execute_adb_command(['shell', 'settings', 'get', 'global', 'airplane_mode_on'])
            info['airplane_mode'] = airplane_mode == '1'
            
            return info
        except Exception as e:
            logger.error(f"Error getting device info: {str(e)}")
            return {'error': str(e)}
    
    def install_app(self, apk_path):
        """Install an app on the device"""
        if not os.path.exists(apk_path):
            logger.error(f"APK file not found: {apk_path}")
            return False
        
        try:
            logger.info(f"Installing app from {apk_path}")
            result = self.execute_adb_command(['install', '-r', apk_path], timeout=120)
            
            if result and 'Success' in result:
                logger.info("App installed successfully")
                return True
            else:
                logger.error(f"Failed to install app: {result}")
                return False
        except Exception as e:
            logger.error(f"Error installing app: {str(e)}")
            return False
    
    def uninstall_app(self, package_name):
        """Uninstall an app from the device"""
        try:
            logger.info(f"Uninstalling app {package_name}")
            result = self.execute_adb_command(['uninstall', package_name])
            
            if result and 'Success' in result:
                logger.info("App uninstalled successfully")
                return True
            else:
                logger.error(f"Failed to uninstall app: {result}")
                return False
        except Exception as e:
            logger.error(f"Error uninstalling app: {str(e)}")
            return False
    
    def launch_app(self, package_name, activity=None):
        """Launch an app on the device"""
        try:
            if activity:
                logger.info(f"Launching activity {activity} in app {package_name}")
                result = self.execute_adb_command([
                    'shell', 'am', 'start', 
                    '-n', f"{package_name}/{activity}"
                ])
            else:
                logger.info(f"Launching app {package_name}")
                result = self.execute_adb_command([
                    'shell', 'monkey', '-p', package_name, 
                    '-c', 'android.intent.category.LAUNCHER', '1'
                ])
            
            return result is not None
        except Exception as e:
            logger.error(f"Error launching app: {str(e)}")
            return False
    
    def take_screenshot(self, output_path):
        """Take a screenshot of the device"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # First take screenshot on device
            temp_path = '/sdcard/screenshot.png'
            self.execute_adb_command(['shell', 'screencap', '-p', temp_path])
            
            # Pull the file to the computer
            logger.info(f"Taking screenshot and saving to {output_path}")
            result = subprocess.run(
                [self.adb_path, '-s', self.device_serial, 'pull', temp_path, output_path],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=30
            )
            
            # Clean up the file on the device
            self.execute_adb_command(['shell', 'rm', temp_path])
            
            if result.returncode != 0:
                logger.error(f"Failed to take screenshot: {result.stderr}")
                return False
                
            return os.path.exists(output_path)
        except Exception as e:
            logger.error(f"Error taking screenshot: {str(e)}")
            return False
    
    def push_file(self, local_path, device_path):
        """Push a file to the device"""
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return False
        
        try:
            logger.info(f"Pushing file {local_path} to {device_path}")
            result = subprocess.run(
                [self.adb_path, '-s', self.device_serial, 'push', local_path, device_path],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to push file: {result.stderr}")
                return False
                
            return 'pushed' in result.stdout.lower()
        except Exception as e:
            logger.error(f"Error pushing file: {str(e)}")
            return False
    
    def pull_file(self, device_path, local_path):
        """Pull a file from the device"""
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            logger.info(f"Pulling file {device_path} to {local_path}")
            result = subprocess.run(
                [self.adb_path, '-s', self.device_serial, 'pull', device_path, local_path],
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE, 
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to pull file: {result.stderr}")
                return False
                
            return os.path.exists(local_path)
        except Exception as e:
            logger.error(f"Error pulling file: {str(e)}")
            return False
    
    def reboot_device(self):
        """Reboot the device"""
        try:
            logger.info("Rebooting device")
            self.execute_adb_command(['reboot'])
            
            # Wait for device to disconnect
            time.sleep(5)
            
            # Wait for device to come back online
            logger.info("Waiting for device to come back online...")
            for _ in range(60):  # Wait up to 5 minutes
                time.sleep(5)
                devices = self.find_connected_devices()
                if self.device_serial in devices:
                    logger.info("Device is back online")
                    
                    # Wait a bit more for it to fully boot
                    time.sleep(10)
                    return True
            
            logger.error("Device did not come back online after reboot")
            return False
        except Exception as e:
            logger.error(f"Error rebooting device: {str(e)}")
            return False

# Singleton instance for global access
_device_manager_instance = None

def get_device_manager(adb_path=None, device_serial=None):
    """Get the singleton instance of DeviceManager"""
    global _device_manager_instance
    if _device_manager_instance is None:
        _device_manager_instance = DeviceManager(adb_path=adb_path, device_serial=device_serial)
    return _device_manager_instance

# Example usage
if __name__ == "__main__":
    # Initialize device manager
    manager = DeviceManager()
    
    # Find connected devices
    devices = manager.find_connected_devices()
    if not devices:
        print("No devices connected. Please connect a device and try again.")
        exit(1)
    
    # Select the first device
    manager.select_device(devices[0])
    
    # Get device info
    info = manager.get_device_info()
    print("Device Info:")
    for key, value in info.items():
        print(f"  {key}: {value}")
    
    # Test IP rotation
    print("\nTesting IP rotation...")
    old_ip = manager.get_current_ip()
    print(f"Current IP: {old_ip}")
    
    print("Enabling airplane mode...")
    manager.toggle_airplane_mode(enable=True)
    time.sleep(5)
    
    print("Disabling airplane mode...")
    manager.toggle_airplane_mode(enable=False)
    
    new_ip = manager.get_current_ip()
    print(f"New IP: {new_ip}")
    
    if old_ip != new_ip:
        print("IP rotation successful!")
    else:
        print("IP rotation failed or IP did not change.")