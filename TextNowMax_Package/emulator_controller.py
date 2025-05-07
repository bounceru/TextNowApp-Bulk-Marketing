"""
Android Emulator Controller for ProgressGhostCreator

This module provides functionality to automate Android emulators for scaling
operations beyond a single physical mobile device.
"""

import os
import time
import random
import logging
import json
import subprocess
import platform
import re
import threading
from datetime import datetime

class EmulatorController:
    def __init__(self, emulator_path=None, avd_name=None, adb_path=None):
        """Initialize the emulator controller
        
        Args:
            emulator_path (str): Path to the emulator executable
            avd_name (str): Name of the Android Virtual Device to use
            adb_path (str): Path to the ADB executable
        """
        self.emulator_path = emulator_path or self._find_emulator_path()
        self.avd_name = avd_name
        self.adb_path = adb_path or self._find_adb_path()
        self.emulator_process = None
        self.running = False
        self.emulator_port = None
        self.installed_apps = []
        self.audio_injection_active = False
        self.audio_injection_thread = None
        
    def _find_emulator_path(self):
        """Find the path to the emulator executable"""
        system = platform.system()
        
        # Common locations
        if system == "Windows":
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'emulator', 'emulator.exe'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'emulator', 'emulator.exe'),
                r"C:\Android\SDK\emulator\emulator.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\emulator\emulator.exe"
            ]
        elif system == "Darwin":  # macOS
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'emulator/emulator'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'emulator/emulator'),
                "/Users/$USER/Library/Android/sdk/emulator/emulator",
                "/Applications/Android Studio.app/Contents/sdk/emulator/emulator"
            ]
        else:  # Linux
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'emulator/emulator'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'emulator/emulator'),
                "/home/$USER/Android/Sdk/emulator/emulator",
                "/opt/android-sdk/emulator/emulator"
            ]
            
        # Try each path
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
                
        # If not found, assume it's in PATH
        return "emulator"
        
    def _find_adb_path(self):
        """Find the path to the adb executable"""
        system = platform.system()
        
        # Common locations
        if system == "Windows":
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'platform-tools', 'adb.exe'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'platform-tools', 'adb.exe'),
                r"C:\Android\SDK\platform-tools\adb.exe",
                r"C:\Users\%USERNAME%\AppData\Local\Android\Sdk\platform-tools\adb.exe"
            ]
        elif system == "Darwin":  # macOS
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'platform-tools/adb'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'platform-tools/adb'),
                "/Users/$USER/Library/Android/sdk/platform-tools/adb",
                "/Applications/Android Studio.app/Contents/sdk/platform-tools/adb"
            ]
        else:  # Linux
            common_paths = [
                os.path.join(os.environ.get('ANDROID_HOME', ''), 'platform-tools/adb'),
                os.path.join(os.environ.get('ANDROID_SDK_ROOT', ''), 'platform-tools/adb'),
                "/home/$USER/Android/Sdk/platform-tools/adb",
                "/opt/android-sdk/platform-tools/adb"
            ]
            
        # Try each path
        for path in common_paths:
            expanded_path = os.path.expandvars(path)
            if os.path.exists(expanded_path):
                return expanded_path
                
        # If not found, assume it's in PATH
        return "adb"
        
    def list_avds(self):
        """List available Android Virtual Devices"""
        try:
            cmd = f"{self.emulator_path} -list-avds"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error listing AVDs: {result.stderr}")
                return []
                
            avds = result.stdout.strip().split('\n')
            return [avd for avd in avds if avd]
            
        except Exception as e:
            logging.error(f"Error listing AVDs: {e}")
            return []
            
    def create_avd(self, name, device="pixel_4", system_image="system-images;android-30;google_apis;x86_64"):
        """Create a new Android Virtual Device"""
        try:
            # Check if AVD already exists
            if name in self.list_avds():
                logging.info(f"AVD '{name}' already exists")
                return True
                
            # Find the Android SDK tools
            sdk_tools = os.path.dirname(os.path.dirname(self.emulator_path))
            avdmanager = os.path.join(sdk_tools, "tools", "bin", "avdmanager")
            
            if platform.system() == "Windows":
                avdmanager += ".bat"
                
            if not os.path.exists(avdmanager):
                logging.error(f"avdmanager not found at {avdmanager}")
                return False
                
            # Create the AVD
            cmd = f'"{avdmanager}" create avd -n "{name}" -k "{system_image}" -d "{device}" --force'
            
            logging.info(f"Creating AVD with command: {cmd}")
            
            # The process might wait for confirmation, so we use a more complex approach
            process = subprocess.Popen(
                cmd,
                shell=True,
                text=True,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit and then send "yes" to any prompts
            time.sleep(2)
            process.stdin.write("yes\n")
            process.stdin.flush()
            
            # Wait for completion
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logging.error(f"Error creating AVD: {stderr}")
                return False
                
            logging.info(f"Created AVD '{name}': {stdout}")
            return True
            
        except Exception as e:
            logging.error(f"Error creating AVD: {e}")
            return False
            
    def start_emulator(self, avd_name=None, port=None, no_window=False, proxy=None, wait_boot=True, enable_audio=True):
        """Start an Android emulator
        
        Args:
            avd_name (str): Name of the AVD to start
            port (int): Port to use for the emulator
            no_window (bool): Whether to run without a window (headless)
            proxy (str): Proxy settings in format "http://host:port"
            wait_boot (bool): Whether to wait for the emulator to fully boot
            enable_audio (bool): Whether to enable audio for the emulator
            
        Returns:
            bool: Whether the emulator was started successfully
        """
        if self.running:
            logging.warning("Emulator already running")
            return True
            
        avd = avd_name or self.avd_name
        if not avd:
            avds = self.list_avds()
            if not avds:
                logging.error("No AVDs found")
                return False
            avd = avds[0]
            
        # Assign a port if not provided
        if not port:
            port = 5554 + (random.randint(0, 10) * 2)  # Emulator uses port and port+1
            
        self.emulator_port = port
        
        # Build the command
        cmd = [self.emulator_path, "-avd", avd, "-port", str(port)]
        
        if no_window:
            cmd.append("-no-window")
            
        if proxy:
            cmd.extend(["-http-proxy", proxy])
            
        # Add performance improvements
        cmd.extend([
            "-no-boot-anim",
            "-no-snapshot",
            "-gpu", "swiftshader_indirect"
        ])
        
        # Disable audio if not needed
        if not enable_audio:
            cmd.append("-no-audio")
        
        try:
            logging.info(f"Starting emulator with command: {' '.join(cmd)}")
            
            # Start the emulator process
            self.emulator_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            self.running = True
            
            # Start a thread to monitor the output
            def monitor_output():
                for line in self.emulator_process.stdout:
                    logging.debug(f"Emulator: {line.strip()}")
                    
            threading.Thread(target=monitor_output, daemon=True).start()
            
            if wait_boot:
                return self.wait_for_boot()
            
            return True
            
        except Exception as e:
            logging.error(f"Error starting emulator: {e}")
            return False
            
    def wait_for_boot(self, timeout=300):
        """Wait for the emulator to boot completely
        
        Args:
            timeout (int): Maximum time to wait in seconds
            
        Returns:
            bool: Whether the emulator booted successfully
        """
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            start_time = time.time()
            booted = False
            
            logging.info("Waiting for emulator to boot...")
            
            while (time.time() - start_time) < timeout:
                # Check if boot is complete
                cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell getprop sys.boot_completed"
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                
                if result.returncode == 0 and result.stdout.strip() == "1":
                    logging.info("Emulator booted successfully")
                    booted = True
                    break
                
                # Small delay before checking again
                time.sleep(2)
                
            if not booted:
                logging.error(f"Emulator boot timed out after {timeout} seconds")
                return False
                
            # Wait a bit more for the system to stabilize
            time.sleep(10)
            
            return True
            
        except Exception as e:
            logging.error(f"Error waiting for emulator boot: {e}")
            return False
            
    def stop_emulator(self):
        """Stop the emulator"""
        if not self.running:
            return True
            
        try:
            # Try graceful shutdown first
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} emu kill"
            subprocess.run(cmd, shell=True, check=False)
            
            # Give it some time to shut down
            time.sleep(5)
            
            # Check if it's still running
            if self.emulator_process and self.emulator_process.poll() is None:
                # Force terminate
                self.emulator_process.terminate()
                self.emulator_process.wait(timeout=10)
                
            self.running = False
            self.emulator_process = None
            return True
            
        except Exception as e:
            logging.error(f"Error stopping emulator: {e}")
            return False
            
    def install_app(self, apk_path):
        """Install an app on the emulator
        
        Args:
            apk_path (str): Path to the APK file
            
        Returns:
            bool: Whether the app was installed successfully
        """
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            if not os.path.exists(apk_path):
                logging.error(f"APK not found: {apk_path}")
                return False
                
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} install -r \"{apk_path}\""
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error installing app: {result.stderr}")
                return False
                
            # Try to get the package name
            package_name = self._get_package_name(apk_path)
            if package_name:
                self.installed_apps.append(package_name)
                
            logging.info(f"Installed app: {os.path.basename(apk_path)}")
            return True
            
        except Exception as e:
            logging.error(f"Error installing app: {e}")
            return False
            
    def _get_package_name(self, apk_path):
        """Get the package name from an APK file"""
        try:
            # Using aapt (Android Asset Packaging Tool)
            aapt_path = self._find_aapt_path()
            if not aapt_path:
                return None
                
            cmd = f'"{aapt_path}" dump badging "{apk_path}" | findstr package:\ name'
            if platform.system() != "Windows":
                cmd = cmd.replace("findstr", "grep")
                
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode == 0:
                # Extract package name using regex
                match = re.search(r"package: name='([^']+)'", result.stdout)
                if match:
                    return match.group(1)
                    
            return None
            
        except Exception as e:
            logging.error(f"Error getting package name: {e}")
            return None
            
    def _find_aapt_path(self):
        """Find the path to the aapt executable"""
        system = platform.system()
        sdk_root = os.environ.get('ANDROID_SDK_ROOT') or os.environ.get('ANDROID_HOME')
        
        # Build tools directories, sorted by version
        build_tools_dir = os.path.join(sdk_root, "build-tools") if sdk_root else None
        
        if build_tools_dir and os.path.exists(build_tools_dir):
            # Get all version directories
            versions = [d for d in os.listdir(build_tools_dir) if os.path.isdir(os.path.join(build_tools_dir, d))]
            
            # Sort versions in descending order
            versions.sort(reverse=True)
            
            # Find aapt in the latest version
            for version in versions:
                aapt = os.path.join(build_tools_dir, version, "aapt")
                if system == "Windows":
                    aapt += ".exe"
                    
                if os.path.exists(aapt):
                    return aapt
                    
        # Try a direct PATH lookup
        try:
            if system == "Windows":
                result = subprocess.run("where aapt", shell=True, text=True, capture_output=True)
            else:
                result = subprocess.run("which aapt", shell=True, text=True, capture_output=True)
                
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
                
        except:
            pass
            
        return None
            
    def launch_app(self, package_name):
        """Launch an app on the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Get the main activity
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell pm dump {package_name} | grep -A 1 MAIN"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error finding main activity: {result.stderr}")
                # Try a simpler approach
                cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell monkey -p {package_name} -c android.intent.category.LAUNCHER 1"
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                
                return result.returncode == 0
                
            # Parse the output to find the activity name
            match = re.search(r"([a-zA-Z0-9\.]+/[a-zA-Z0-9\.]+)", result.stdout)
            if not match:
                logging.error("Could not find main activity")
                return False
                
            activity = match.group(1)
            
            # Launch the app
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell am start -n {activity}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error launching app: {result.stderr}")
                return False
                
            logging.info(f"Launched app: {package_name}")
            return True
            
        except Exception as e:
            logging.error(f"Error launching app: {e}")
            return False
            
    def inject_audio(self, audio_file_path, duration=None, stop_after=True):
        """Inject audio from a file to the emulator's microphone
        
        This function sends audio from a file to the emulator's microphone input,
        making it appear as if someone is speaking into the mic.
        
        Args:
            audio_file_path (str): Path to the audio file (MP3, WAV)
            duration (int): Duration in seconds to play the audio (None for full file)
            stop_after (bool): Whether to stop audio injection after playback
            
        Returns:
            bool: Whether the audio injection was started successfully
        """
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Check if the file exists
            if not os.path.exists(audio_file_path):
                logging.error(f"Audio file not found: {audio_file_path}")
                return False
                
            # Stop any existing audio injection
            self.stop_audio_injection()
            
            # Prepare the audio file
            # Use the emulator console to set up audio injection
            console_cmd = f"auth {self.emulator_port}"
            telnet_cmd = ["telnet", "localhost", str(self.emulator_port)]
            
            # Set up a new process to send audio to the emulator
            self.audio_injection_active = True
            
            def audio_injection_thread():
                try:
                    # Connect to the emulator console
                    telnet_process = subprocess.Popen(
                        telnet_cmd,
                        stdin=subprocess.PIPE,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Wait for telnet connection
                    time.sleep(1)
                    
                    # Authenticate
                    telnet_process.stdin.write(console_cmd + "\n")
                    telnet_process.stdin.flush()
                    time.sleep(0.5)
                    
                    # Set up audio injection
                    telnet_process.stdin.write(f"mic start {audio_file_path}\n")
                    telnet_process.stdin.flush()
                    
                    logging.info(f"Started audio injection from: {audio_file_path}")
                    
                    # If duration is specified, wait that long
                    if duration:
                        start_time = time.time()
                        while time.time() - start_time < duration and self.audio_injection_active:
                            time.sleep(0.5)
                    else:
                        # Otherwise, just wait until stopped
                        while self.audio_injection_active:
                            time.sleep(0.5)
                    
                    # Stop audio injection if requested
                    if stop_after:
                        telnet_process.stdin.write("mic stop\n")
                        telnet_process.stdin.flush()
                        logging.info("Stopped audio injection")
                    
                    # Close telnet connection
                    telnet_process.stdin.write("quit\n")
                    telnet_process.stdin.flush()
                    telnet_process.terminate()
                    
                except Exception as e:
                    logging.error(f"Error in audio injection thread: {e}")
                finally:
                    self.audio_injection_active = False
            
            # Start the audio injection thread
            self.audio_injection_thread = threading.Thread(target=audio_injection_thread)
            self.audio_injection_thread.daemon = True
            self.audio_injection_thread.start()
            
            # Small delay to ensure thread has started
            time.sleep(1)
            return self.audio_injection_active
            
        except Exception as e:
            logging.error(f"Error injecting audio: {e}")
            self.audio_injection_active = False
            return False
    
    def stop_audio_injection(self):
        """Stop any active audio injection"""
        if self.audio_injection_active:
            self.audio_injection_active = False
            
            # Wait for the thread to finish
            if self.audio_injection_thread and self.audio_injection_thread.is_alive():
                self.audio_injection_thread.join(timeout=5)
            
            # Additional cleanup using telnet
            try:
                telnet_cmd = ["telnet", "localhost", str(self.emulator_port)]
                console_cmd = f"auth {self.emulator_port}"
                
                telnet_process = subprocess.Popen(
                    telnet_cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for connection
                time.sleep(1)
                
                # Authenticate
                telnet_process.stdin.write(console_cmd + "\n")
                telnet_process.stdin.flush()
                time.sleep(0.5)
                
                # Stop mic
                telnet_process.stdin.write("mic stop\n")
                telnet_process.stdin.flush()
                
                # Close connection
                telnet_process.stdin.write("quit\n")
                telnet_process.stdin.flush()
                telnet_process.terminate()
                
                logging.info("Stopped audio injection")
                return True
                
            except Exception as e:
                logging.error(f"Error stopping audio injection: {e}")
                return False
        
        return True
        
    def toggle_airplane_mode(self):
        """Toggle airplane mode on the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Get current airplane mode state
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell settings get global airplane_mode_on"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error getting airplane mode state: {result.stderr}")
                return False
                
            # Toggle the state
            current_state = result.stdout.strip()
            new_state = "0" if current_state == "1" else "1"
            
            # Set the new state
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell settings put global airplane_mode_on {new_state}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error setting airplane mode: {result.stderr}")
                return False
                
            # Broadcast the change
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell am broadcast -a android.intent.action.AIRPLANE_MODE --ez state {new_state == '1'}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error broadcasting airplane mode change: {result.stderr}")
                return False
                
            logging.info(f"Airplane mode {'enabled' if new_state == '1' else 'disabled'}")
            return True
            
        except Exception as e:
            logging.error(f"Error toggling airplane mode: {e}")
            return False
            
    def take_screenshot(self, output_path=None):
        """Take a screenshot of the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Generate output path if not provided
            if not output_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = "screenshots"
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"emulator_{timestamp}.png")
                
            # Take screenshot on device
            tmp_path = f"/sdcard/screenshot_{random.randint(1000, 9999)}.png"
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell screencap -p {tmp_path}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error taking screenshot: {result.stderr}")
                return False
                
            # Pull the screenshot to the computer
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} pull {tmp_path} \"{output_path}\""
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error pulling screenshot: {result.stderr}")
                return False
                
            # Clean up the temporary file
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell rm {tmp_path}"
            subprocess.run(cmd, shell=True, check=False)
            
            logging.info(f"Screenshot saved to {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Error taking screenshot: {e}")
            return False
            
    def input_text(self, text):
        """Input text on the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Escape special characters
            text = text.replace(' ', '%s')
            text = text.replace("'", "\\'")
            text = text.replace('"', '\\"')
            
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell input text '{text}'"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error inputting text: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error inputting text: {e}")
            return False
            
    def tap(self, x, y):
        """Tap on the screen at the specified coordinates"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell input tap {x} {y}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error tapping screen: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error tapping screen: {e}")
            return False
            
    def swipe(self, x1, y1, x2, y2, duration=300):
        """Swipe on the screen from (x1,y1) to (x2,y2) with the specified duration"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell input swipe {x1} {y1} {x2} {y2} {duration}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error swiping screen: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error swiping screen: {e}")
            return False
            
    def press_key(self, key):
        """Press a key on the emulator
        
        Args:
            key (str): Key code, e.g., "KEYCODE_HOME", "KEYCODE_BACK"
        """
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell input keyevent {key.replace('KEYCODE_', '')}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error pressing key: {result.stderr}")
                return False
                
            return True
            
        except Exception as e:
            logging.error(f"Error pressing key: {e}")
            return False
            
    def get_ip_address(self):
        """Get the IP address of the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return None
            
        try:
            # Try multiple commands to get the IP
            commands = [
                "shell ip route | awk '{print $9}'",
                "shell ifconfig | grep 'inet addr'",
                "shell netcfg | grep 'wlan0'"
            ]
            
            for cmd_suffix in commands:
                cmd = f"{self.adb_path} -s emulator-{self.emulator_port} {cmd_suffix}"
                result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
                
                if result.returncode == 0 and result.stdout.strip():
                    # Extract IP address using regex
                    match = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', result.stdout)
                    if match:
                        return match.group(1)
                        
            # If all methods fail, use the emulator's default gateway
            return "10.0.2.15"  # Default IP for the emulator
            
        except Exception as e:
            logging.error(f"Error getting IP address: {e}")
            return None
            
    def execute_shell_command(self, command):
        """Execute a shell command on the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return None
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell {command}"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error executing shell command: {result.stderr}")
                return None
                
            return result.stdout.strip()
            
        except Exception as e:
            logging.error(f"Error executing shell command: {e}")
            return None
            
    def push_file(self, local_path, device_path):
        """Push a file to the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} push \"{local_path}\" \"{device_path}\""
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error pushing file: {result.stderr}")
                return False
                
            logging.info(f"Pushed file to {device_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error pushing file: {e}")
            return False
            
    def pull_file(self, device_path, local_path):
        """Pull a file from the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} pull \"{device_path}\" \"{local_path}\""
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error pulling file: {result.stderr}")
                return False
                
            logging.info(f"Pulled file to {local_path}")
            return True
            
        except Exception as e:
            logging.error(f"Error pulling file: {e}")
            return False
            
    def set_location(self, latitude, longitude):
        """Set the GPS location of the emulator"""
        if not self.running:
            logging.error("Emulator not running")
            return False
            
        try:
            # Using the geo fix command through the emulator console
            cmd = f"echo \"geo fix {longitude} {latitude}\" | {self.adb_path} -s emulator-{self.emulator_port} emu"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            
            if result.returncode != 0:
                logging.error(f"Error setting location: {result.stderr}")
                return False
                
            logging.info(f"Set location to {latitude}, {longitude}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting location: {e}")
            return False
            
    def get_device_info(self):
        """Get information about the emulator device"""
        if not self.running:
            logging.error("Emulator not running")
            return None
            
        try:
            info = {}
            
            # Get device model
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell getprop ro.product.model"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                info['model'] = result.stdout.strip()
                
            # Get Android version
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell getprop ro.build.version.release"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                info['android_version'] = result.stdout.strip()
                
            # Get screen resolution
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell wm size"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                match = re.search(r'(\d+)x(\d+)', result.stdout)
                if match:
                    info['screen_width'] = match.group(1)
                    info['screen_height'] = match.group(2)
                    
            # Get device ID
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell settings get secure android_id"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                info['device_id'] = result.stdout.strip()
                
            # Get IP address
            info['ip_address'] = self.get_ip_address()
            
            # Get installed packages
            cmd = f"{self.adb_path} -s emulator-{self.emulator_port} shell pm list packages -3"
            result = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            if result.returncode == 0:
                packages = result.stdout.strip().split('\n')
                info['installed_packages'] = [p.replace('package:', '').strip() for p in packages if p.strip()]
                
            return info
            
        except Exception as e:
            logging.error(f"Error getting device info: {e}")
            return None


class EmulatorPool:
    def __init__(self, max_emulators=5):
        """Initialize an emulator pool
        
        Args:
            max_emulators (int): Maximum number of emulators to run simultaneously
        """
        self.max_emulators = max_emulators
        self.emulators = []
        self.avd_names = []
        self.emulator_lock = threading.Lock()
        
    def initialize_pool(self, avd_names=None):
        """Initialize the emulator pool with the specified AVD names"""
        if avd_names:
            self.avd_names = avd_names
            
        if not self.avd_names:
            # Try to find available AVDs
            controller = EmulatorController()
            avds = controller.list_avds()
            
            if avds:
                self.avd_names = avds
                
        if not self.avd_names:
            logging.error("No AVDs specified or found")
            return False
            
        logging.info(f"Initialized emulator pool with AVDs: {self.avd_names}")
        return True
        
    def start_emulator(self, avd_name=None):
        """Start an emulator from the pool
        
        Args:
            avd_name (str): Specific AVD to start, or None to use round-robin
            
        Returns:
            EmulatorController: The started emulator controller, or None if failed
        """
        with self.emulator_lock:
            # Check if we've reached the maximum number of emulators
            if len(self.emulators) >= self.max_emulators:
                logging.warning(f"Maximum number of emulators ({self.max_emulators}) already running")
                return None
                
            # Determine which AVD to use
            if not avd_name:
                if not self.avd_names:
                    logging.error("No AVDs available")
                    return None
                    
                # Use round-robin
                avd_name = self.avd_names[len(self.emulators) % len(self.avd_names)]
                
            # Determine port (each emulator uses a pair of consecutive ports)
            base_port = 5554
            used_ports = [e.emulator_port for e in self.emulators if e.emulator_port]
            
            port = base_port
            while port in used_ports or port + 1 in used_ports:
                port += 2
                if port > 5584:  # Maximum is usually 5584
                    logging.error("No available ports for emulator")
                    return None
                    
            # Start the emulator
            controller = EmulatorController()
            success = controller.start_emulator(avd_name=avd_name, port=port)
            
            if success:
                self.emulators.append(controller)
                logging.info(f"Started emulator {avd_name} on port {port}")
                return controller
            else:
                logging.error(f"Failed to start emulator {avd_name}")
                return None
                
    def get_running_emulators(self):
        """Get a list of running emulators"""
        return self.emulators
        
    def get_available_emulator(self):
        """Get an available emulator from the pool, starting one if needed"""
        with self.emulator_lock:
            if not self.emulators:
                return self.start_emulator()
                
            # Return the least recently used emulator
            return self.emulators[0]
            
    def stop_emulator(self, controller):
        """Stop an emulator and remove it from the pool"""
        with self.emulator_lock:
            if controller in self.emulators:
                controller.stop_emulator()
                self.emulators.remove(controller)
                logging.info("Stopped emulator")
                return True
            else:
                logging.warning("Emulator not in pool")
                return False
                
    def stop_all_emulators(self):
        """Stop all emulators in the pool"""
        with self.emulator_lock:
            for controller in self.emulators[:]:
                controller.stop_emulator()
                self.emulators.remove(controller)
                
            logging.info("Stopped all emulators")
            return True


def get_emulator_pool(max_emulators=5):
    """Get the emulator pool singleton instance"""
    return EmulatorPool(max_emulators)


if __name__ == "__main__":
    # Test the emulator controller
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    controller = EmulatorController()
    
    # List available AVDs
    avds = controller.list_avds()
    print(f"Available AVDs: {avds}")
    
    if avds:
        # Start an emulator
        print("Starting emulator...")
        controller.start_emulator(avd_name=avds[0])
        
        # Get device info
        info = controller.get_device_info()
        print(f"Device info: {json.dumps(info, indent=2)}")
        
        # Take a screenshot
        screenshot_path = controller.take_screenshot()
        print(f"Screenshot saved to: {screenshot_path}")
        
        # Stop the emulator
        print("Stopping emulator...")
        controller.stop_emulator()
    else:
        print("No AVDs found. Please create one first.")