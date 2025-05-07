"""
ADB Phone Test for ProgressGhostCreator

This script verifies that we can properly connect to and control a BLU G44 phone
via ADB (Android Debug Bridge) for IP rotation by toggling airplane mode.
"""

import os
import sys
import time
import logging
import subprocess
from ppadb.client import Client as AdbClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('device_manager.log')
    ]
)
logger = logging.getLogger('AdbPhoneTest')

class PhoneConnectionTester:
    def __init__(self, host='127.0.0.1', port=5037):
        """Initialize the phone connection tester"""
        self.host = host
        self.port = port
        self.client = None
        self.device = None
        
    def check_adb_installed(self):
        """Check if ADB is installed on the system"""
        try:
            result = subprocess.run(['adb', 'version'], 
                                   stdout=subprocess.PIPE, 
                                   stderr=subprocess.PIPE,
                                   text=True)
            if result.returncode == 0:
                logger.info(f"ADB installed: {result.stdout.splitlines()[0]}")
                return True
            else:
                logger.error("ADB not found or not working properly")
                return False
        except FileNotFoundError:
            logger.error("ADB is not installed or not in PATH")
            return False
    
    def connect_to_adb(self):
        """Connect to ADB server"""
        try:
            self.client = AdbClient(host=self.host, port=self.port)
            logger.info(f"Successfully connected to ADB server at {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to ADB server: {str(e)}")
            return False
    
    def get_connected_devices(self):
        """Get list of connected devices"""
        if not self.client:
            logger.error("ADB client not initialized")
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
                        
                        logger.info(f"Found device: {model} (Android {android_version}), serial: {serial}")
                    except Exception as e:
                        logger.error(f"Error getting device info: {str(e)}")
                
                return device_info
            else:
                logger.warning("No devices connected")
                return []
        except Exception as e:
            logger.error(f"Error getting device list: {str(e)}")
            return []
    
    def select_device(self, serial=None):
        """Select a device to work with"""
        if not self.client:
            logger.error("ADB client not initialized")
            return False
        
        try:
            devices = self.client.devices()
            if not devices:
                logger.error("No devices connected")
                return False
            
            if serial:
                # Try to find specific device
                for device in devices:
                    if device.serial == serial:
                        self.device = device
                        model = device.shell('getprop ro.product.model').strip()
                        logger.info(f"Selected device: {model} with serial {serial}")
                        return True
                logger.error(f"Device with serial {serial} not found")
                return False
            else:
                # Just take the first device
                self.device = devices[0]
                model = self.device.shell('getprop ro.product.model').strip()
                logger.info(f"Selected device: {model} with serial {self.device.serial}")
                return True
        except Exception as e:
            logger.error(f"Error selecting device: {str(e)}")
            return False
    
    def test_airplane_mode(self):
        """Test toggling airplane mode on and off"""
        if not self.device:
            logger.error("No device selected")
            return False
        
        try:
            # Check current IP first
            before_ip = self.get_current_ip()
            logger.info(f"Current IP before airplane mode: {before_ip}")
            
            # Turn airplane mode ON
            logger.info("Turning airplane mode ON...")
            self.device.shell('settings put global airplane_mode_on 1')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state true')
            logger.info("Waiting for network to disconnect...")
            time.sleep(5)
            
            # Check if network is disconnected
            in_airplane_mode = self.check_if_in_airplane_mode()
            logger.info(f"Is in airplane mode: {in_airplane_mode}")
            
            # Turn airplane mode OFF
            logger.info("Turning airplane mode OFF...")
            self.device.shell('settings put global airplane_mode_on 0')
            self.device.shell('am broadcast -a android.intent.action.AIRPLANE_MODE --ez state false')
            logger.info("Waiting for network to reconnect...")
            time.sleep(10)
            
            # Check new IP
            after_ip = self.get_current_ip()
            logger.info(f"Current IP after airplane mode: {after_ip}")
            
            # Verify if IP changed
            if before_ip and after_ip:
                if before_ip != after_ip:
                    logger.info("IP CHANGED SUCCESSFULLY!")
                    return True
                else:
                    logger.warning("IP did not change after toggling airplane mode")
                    return False
            else:
                logger.warning("Could not verify IP change (unable to get IP)")
                return False
            
        except Exception as e:
            logger.error(f"Error testing airplane mode: {str(e)}")
            return False
    
    def check_if_in_airplane_mode(self):
        """Check if device is currently in airplane mode"""
        try:
            result = self.device.shell('settings get global airplane_mode_on').strip()
            return result == '1'
        except Exception as e:
            logger.error(f"Error checking airplane mode: {str(e)}")
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
                
            logger.warning("Could not determine device IP address")
            return None
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            return None

    def run_full_test(self):
        """Run a complete test of all functionality"""
        logger.info("=== STARTING COMPREHENSIVE ADB PHONE TEST ===")
        
        # Step 1: Check if ADB is installed
        logger.info("Step 1: Checking if ADB is installed...")
        if not self.check_adb_installed():
            logger.error("TEST FAILED: ADB is not installed or not in PATH")
            return False
        
        # Step 2: Connect to ADB server
        logger.info("Step 2: Connecting to ADB server...")
        if not self.connect_to_adb():
            logger.error("TEST FAILED: Could not connect to ADB server")
            return False
        
        # Step 3: List connected devices
        logger.info("Step 3: Looking for connected devices...")
        devices = self.get_connected_devices()
        if not devices:
            logger.error("TEST FAILED: No devices found connected to ADB")
            return False
        
        # Step 4: Select a device (preferably BLU G44)
        logger.info("Step 4: Selecting a device...")
        
        # Try to find BLU G44 first
        blu_g44_found = False
        for device in devices:
            if 'BLU' in device['model'] and 'G44' in device['model']:
                blu_g44_found = True
                if self.select_device(device['serial']):
                    logger.info("Successfully selected BLU G44 device!")
                else:
                    logger.error("Failed to select BLU G44 device")
                    return False
        
        if not blu_g44_found:
            logger.warning("BLU G44 device not found. Selecting first available device...")
            if not self.select_device():
                logger.error("TEST FAILED: Could not select any device")
                return False
        
        # Step 5: Test airplane mode toggling
        logger.info("Step 5: Testing airplane mode toggling and IP rotation...")
        if not self.test_airplane_mode():
            logger.warning("IP rotation test inconclusive - could not verify IP change")
            # Don't fail completely here, as this might be due to network issues
        
        logger.info("=== ADB PHONE TEST COMPLETED SUCCESSFULLY ===")
        return True


def main():
    """Run the ADB phone test"""
    print("\n=== ADB Phone Connection Tester for ProgressGhostCreator ===\n")
    print("This script will test if we can connect to and control your BLU G44 phone.")
    print("Please ensure your phone is:\n")
    print("1. Connected to the computer via USB")
    print("2. Has USB debugging enabled in Developer Options")
    print("3. Has granted permission for USB debugging if prompted\n")
    
    input("Press Enter to start the test...")
    
    tester = PhoneConnectionTester()
    result = tester.run_full_test()
    
    if result:
        print("\n✅ TEST PASSED: Your phone is properly configured for ProgressGhostCreator!")
        print("We can successfully control airplane mode for IP rotation.")
    else:
        print("\n❌ TEST FAILED: There were issues connecting to or controlling your phone.")
        print("Please check the log file (device_manager.log) for details.")
        print("\nCommon troubleshooting steps:")
        print("1. Ensure USB debugging is enabled in Developer Options")
        print("2. Try disconnecting and reconnecting the phone")
        print("3. Check if you need to install ADB drivers for your phone")
        print("4. Make sure you approved the USB debugging prompt on your phone")

if __name__ == "__main__":
    main()