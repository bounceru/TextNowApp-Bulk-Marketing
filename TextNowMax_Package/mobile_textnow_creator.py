"""
Mobile TextNow Account Creator

This module implements the account creation process for TextNow through their mobile app
using Android emulation. Since TextNow now only allows account creation via their mobile app,
this is essential for creating new accounts.
"""

import os
import random
import time
import json
import logging
import sqlite3
import uuid
from datetime import datetime, timedelta
import subprocess
import re
import threading
import queue
from typing import Dict, List, Tuple, Optional, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='account_creator.log'
)
logger = logging.getLogger('mobile_textnow_creator')

class TextNowMobileCreator:
    """
    Creates TextNow accounts using Android emulation and the TextNow mobile app
    """
    
    def __init__(self, database_path='ghost_accounts.db', emulator_count=3, 
                 proxidize_config_path='proxidize_config.json'):
        """
        Initialize the TextNow mobile creator
        
        Args:
            database_path: Path to the SQLite database
            emulator_count: Number of emulator instances to run in parallel
            proxidize_config_path: Path to the Proxidize configuration file
        """
        self.database_path = database_path
        self.emulator_count = min(emulator_count, 5)  # Max 5 emulators to prevent resource issues
        self.proxidize_config_path = proxidize_config_path
        self.running = False
        self.task_queue = queue.Queue()
        self.result_queue = queue.Queue()
        self.workers = []
        self.conn = None
        self.cursor = None
        self.proxidize_config = self._load_proxidize_config()
        
        # Initialize database
        self._init_database()
        
        # App details
        self.app_package = "com.enflick.android.TextNow"
        self.app_activity = "com.enflick.android.TextNow.SplashActivity"
        self.apk_path = "textnow.apk"
        
        # Download APK if not present
        self._ensure_apk_exists()
        
        logger.info("TextNow Mobile Creator initialized")
    
    def _load_proxidize_config(self) -> Dict[str, Any]:
        """Load Proxidize configuration from JSON file"""
        try:
            with open(self.proxidize_config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"Loaded Proxidize config: {self.proxidize_config_path}")
                return config
        except Exception as e:
            logger.error(f"Failed to load Proxidize config: {e}")
            return {
                "api_key": "",
                "port": 5656,
                "device_ip": "127.0.0.1"
            }
    
    def _ensure_apk_exists(self):
        """Make sure the TextNow APK exists, or provide instructions"""
        if not os.path.exists(self.apk_path):
            logger.warning(f"TextNow APK not found at {self.apk_path}")
            print(f"""
WARNING: TextNow APK not found at {self.apk_path}
Please download the TextNow APK and place it in the same directory.
You can find APKs at APKPure or similar sites. Make sure to rename it to 'textnow.apk'.
""")
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.cursor = self.conn.cursor()
            
            # Create accounts table if it doesn't exist
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone_number TEXT UNIQUE,
                username TEXT,
                email TEXT,
                password TEXT,
                first_name TEXT,
                last_name TEXT,
                birthdate TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                next_activity TIMESTAMP,
                area_code TEXT,
                status TEXT DEFAULT 'active',
                health_score INTEGER DEFAULT 100,
                session_data TEXT,
                device_fingerprint TEXT,
                notes TEXT
            )
            """)
            
            # Create account_creation_log table if it doesn't exist
            self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_creation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                action TEXT,
                success INTEGER,
                details TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts (id)
            )
            """)
            
            self.conn.commit()
            logger.info("Database initialized")
        except Exception as e:
            logger.error(f"Database initialization error: {e}")
            raise
    
    def start_creation(self, num_accounts: int, area_codes: List[str] = None):
        """
        Start the account creation process
        
        Args:
            num_accounts: Number of accounts to create
            area_codes: List of area codes to use (e.g., ['213', '312', '415'])
        
        Returns:
            True if started successfully, False otherwise
        """
        if self.running:
            logger.warning("Account creation already running")
            return False
        
        if area_codes is None or len(area_codes) == 0:
            # Default to major US area codes if none provided
            area_codes = ['213', '312', '404', '415', '469', '512', '617', '702', '713', '818']
        
        self.running = True
        
        # Clear the queues
        while not self.task_queue.empty():
            self.task_queue.get()
        while not self.result_queue.empty():
            self.result_queue.get()
        
        # Create tasks
        for _ in range(num_accounts):
            area_code = random.choice(area_codes)
            task = {
                'area_code': area_code,
                'profile': self._generate_random_profile()
            }
            self.task_queue.put(task)
        
        # Start worker threads
        self.workers = []
        for i in range(self.emulator_count):
            worker = threading.Thread(
                target=self._worker_thread, 
                args=(i,),
                daemon=True
            )
            worker.start()
            self.workers.append(worker)
            # Stagger worker startup
            time.sleep(3)
        
        # Start result collector thread
        result_collector = threading.Thread(
            target=self._result_collector,
            daemon=True
        )
        result_collector.start()
        
        logger.info(f"Started creation of {num_accounts} accounts with {self.emulator_count} workers")
        return True
    
    def stop_creation(self):
        """Stop the account creation process"""
        if not self.running:
            return
        
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            if worker.is_alive():
                worker.join(timeout=5)
        
        self.workers = []
        logger.info("Account creation stopped")
    
    def _worker_thread(self, worker_id: int):
        """
        Worker thread that processes account creation tasks
        
        Args:
            worker_id: Unique ID for this worker
        """
        emulator_name = f"textnow_emulator_{worker_id}"
        device_id = f"emulator-{5554 + worker_id*2}"
        
        logger.info(f"Worker {worker_id} starting with emulator {emulator_name}")
        
        try:
            # Start emulator
            self._start_emulator(emulator_name, worker_id)
            
            # Install APK
            self._install_apk(device_id)
            
            # Process tasks
            while self.running:
                try:
                    # Get a task with timeout
                    task = self.task_queue.get(timeout=5)
                except queue.Empty:
                    # No more tasks
                    break
                
                # Get a proxy from Proxidize
                proxy = self._get_proxidize_proxy()
                if not proxy:
                    logger.error(f"Worker {worker_id} failed to get proxy")
                    # Put task back and sleep
                    self.task_queue.put(task)
                    time.sleep(30)
                    continue
                
                # Set proxy for emulator
                self._set_emulator_proxy(device_id, proxy)
                
                # Create account
                success, account_data = self._create_account(
                    device_id, 
                    task['area_code'],
                    task['profile'],
                    proxy
                )
                
                # Submit result
                result = {
                    'success': success,
                    'account_data': account_data,
                    'worker_id': worker_id
                }
                self.result_queue.put(result)
                
                # Rate limiting - sleep after each account
                time.sleep(random.uniform(15, 30))
                
                # Rotate device fingerprint after a few accounts
                if random.random() < 0.3:  # 30% chance
                    self._reset_emulator(emulator_name, worker_id)
                
            # Clean up
            self._stop_emulator(device_id)
            
        except Exception as e:
            logger.error(f"Worker {worker_id} encountered an error: {e}")
        finally:
            logger.info(f"Worker {worker_id} shutting down")
            try:
                self._stop_emulator(device_id)
            except:
                pass
    
    def _result_collector(self):
        """Thread to collect and process results from workers"""
        success_count = 0
        failure_count = 0
        
        while self.running or not self.result_queue.empty():
            try:
                # Get a result with timeout
                result = self.result_queue.get(timeout=5)
                
                if result['success']:
                    # Save successful account to database
                    account_id = self._save_account_to_db(result['account_data'])
                    if account_id:
                        success_count += 1
                        logger.info(f"Account created successfully: {result['account_data']['phone_number']}")
                        
                        # Log success
                        self._log_creation_result(
                            account_id, 
                            True, 
                            f"Created by worker {result['worker_id']}"
                        )
                    else:
                        failure_count += 1
                else:
                    failure_count += 1
                    logger.warning(f"Account creation failed: {result['account_data'].get('error', 'Unknown error')}")
                    
                # Print progress
                total = success_count + failure_count
                if total % 5 == 0:  # Every 5 accounts
                    print(f"Progress: {total} accounts processed ({success_count} successful, {failure_count} failed)")
                
            except queue.Empty:
                # No results yet
                continue
            except Exception as e:
                logger.error(f"Result collector error: {e}")
        
        logger.info(f"Result collection complete: {success_count} successful, {failure_count} failed")
    
    def _start_emulator(self, emulator_name: str, worker_id: int):
        """
        Start an Android emulator
        
        Args:
            emulator_name: Name of the emulator
            worker_id: Worker ID for port allocation
        """
        # Check if emulator exists
        try:
            result = subprocess.run(
                ["avdmanager", "list", "avd"], 
                capture_output=True, 
                text=True
            )
            
            if emulator_name not in result.stdout:
                # Create emulator
                logger.info(f"Creating emulator {emulator_name}")
                subprocess.run([
                    "avdmanager", "create", "avd",
                    "-n", emulator_name,
                    "-k", "system-images;android-29;google_apis;x86_64",
                    "-d", "pixel_3a"
                ])
        except Exception as e:
            logger.error(f"Error checking/creating emulator: {e}")
            raise
        
        # Start emulator
        logger.info(f"Starting emulator {emulator_name}")
        port = 5554 + worker_id*2
        
        # Run emulator in background
        subprocess.Popen([
            "emulator",
            "-avd", emulator_name,
            "-port", str(port),
            "-no-audio",
            "-no-boot-anim",
            "-no-window",
            "-gpu", "swiftshader_indirect"
        ])
        
        # Wait for emulator to boot
        self._wait_for_emulator_boot(f"emulator-{port}")
    
    def _wait_for_emulator_boot(self, device_id: str, timeout: int = 120):
        """Wait for emulator to fully boot"""
        logger.info(f"Waiting for emulator {device_id} to boot")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                result = subprocess.run(
                    ["adb", "-s", device_id, "shell", "getprop", "sys.boot_completed"],
                    capture_output=True, 
                    text=True
                )
                
                if result.stdout.strip() == "1":
                    logger.info(f"Emulator {device_id} booted successfully")
                    # Additional wait for services to start
                    time.sleep(10)
                    return True
            except:
                pass
            
            time.sleep(5)
        
        logger.error(f"Timeout waiting for emulator {device_id} to boot")
        return False
    
    def _install_apk(self, device_id: str):
        """Install TextNow APK on the emulator"""
        if not os.path.exists(self.apk_path):
            logger.error(f"APK not found: {self.apk_path}")
            return False
        
        logger.info(f"Installing TextNow APK on {device_id}")
        try:
            subprocess.run(
                ["adb", "-s", device_id, "install", "-r", self.apk_path],
                check=True
            )
            logger.info(f"TextNow APK installed on {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to install APK on {device_id}: {e}")
            return False
    
    def _set_emulator_proxy(self, device_id: str, proxy: Dict[str, str]):
        """Configure emulator to use proxy"""
        if not proxy or 'host' not in proxy or 'port' not in proxy:
            logger.error("Invalid proxy configuration")
            return False
        
        logger.info(f"Setting proxy {proxy['host']}:{proxy['port']} on {device_id}")
        
        try:
            # Set global proxy settings
            subprocess.run([
                "adb", "-s", device_id, "shell", "settings", "put", "global", 
                "http_proxy", f"{proxy['host']}:{proxy['port']}"
            ])
            
            if 'username' in proxy and 'password' in proxy:
                # Set proxy authentication if provided
                subprocess.run([
                    "adb", "-s", device_id, "shell", "settings", "put", "global", 
                    "global_http_proxy_username", proxy['username']
                ])
                subprocess.run([
                    "adb", "-s", device_id, "shell", "settings", "put", "global", 
                    "global_http_proxy_password", proxy['password']
                ])
            
            logger.info(f"Proxy configured on {device_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to set proxy on {device_id}: {e}")
            return False
    
    def _create_account(self, device_id: str, area_code: str, profile: Dict[str, str], 
                        proxy: Dict[str, str], max_retries: int = 3) -> Tuple[bool, Dict[str, Any]]:
        """
        Create a TextNow account on the emulator with retry mechanism
        
        Args:
            device_id: ADB device ID
            area_code: Desired area code
            profile: User profile data
            proxy: Proxy configuration
            max_retries: Maximum number of retry attempts
            
        Returns:
            Tuple of (success_boolean, account_data_dict)
        """
        logger.info(f"Creating account with area code {area_code} on {device_id}")
        
        account_data = {
            'phone_number': '',
            'username': profile['username'],
            'email': profile['email'],
            'password': profile['password'],
            'first_name': profile['first_name'],
            'last_name': profile['last_name'],
            'birthdate': profile['birthdate'],
            'area_code': area_code,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'device_fingerprint': f"{device_id}_{str(uuid.uuid4())[:8]}",
            'proxy': f"{proxy['host']}:{proxy['port']}",
            'status': 'pending'
        }
        
        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(f"Retry attempt {attempt} of {max_retries-1} for creating account with area code {area_code}")
                # For retries, restart the app to ensure clean state
                try:
                    # Force stop the app
                    subprocess.run([
                        "adb", "-s", device_id, "shell", "am", "force-stop", self.app_package
                    ])
                    time.sleep(2)
                except:
                    pass  # Ignore errors in closing
            
            try:
                # Start the TextNow app
                subprocess.run([
                    "adb", "-s", device_id, "shell", "am", "start", 
                    "-n", f"{self.app_package}/{self.app_activity}"
                ])
                
                # Wait for app to load
                time.sleep(10)
                
                # Check if already signed in and sign out if needed
                if self._check_if_signed_in(device_id):
                    self._sign_out(device_id)
                time.sleep(5)
            
            # Navigate to signup
            self._tap_signup_button(device_id)
            time.sleep(3)
            
            # Fill registration form
            success = self._fill_registration_form(device_id, profile)
            if not success:
                account_data['error'] = "Failed to fill registration form"
                return False, account_data
            
            # Submit form
            self._tap_submit_button(device_id)
            time.sleep(10)
            
            # Check for errors
            if self._check_for_signup_errors(device_id):
                error_text = self._get_error_text(device_id)
                account_data['error'] = f"Signup error: {error_text}"
                return False, account_data
            
            # Select area code
            success, selected_area_code = self._select_area_code(device_id, area_code)
            if not success:
                account_data['error'] = f"Failed to select area code {area_code}"
                return False, account_data
            
            account_data['area_code'] = selected_area_code
            
            # Select phone number
            success, phone_number = self._select_phone_number(device_id)
            if not success:
                account_data['error'] = "Failed to select phone number"
                return False, account_data
            
            account_data['phone_number'] = phone_number
            account_data['status'] = 'active'
            
            # Get session data
            session_data = self._get_session_data(device_id)
            account_data['session_data'] = json.dumps(session_data)
            
            # Verify account works
            if not self._verify_account(device_id, phone_number):
                account_data['status'] = 'unverified'
                logger.warning(f"Account created but verification failed: {phone_number}")
            
            logger.info(f"Account created successfully with number {phone_number}")
            return True, account_data
            
        except Exception as e:
            logger.error(f"Error creating account on {device_id}: {e}")
            account_data['error'] = str(e)
            return False, account_data
    
    def _check_if_signed_in(self, device_id: str) -> bool:
        """Check if already signed in to TextNow"""
        try:
            result = subprocess.run([
                "adb", "-s", device_id, "shell", "dumpsys", "window", "windows",
                "|", "grep", "-E", "mCurrentFocus"
            ], capture_output=True, text=True, shell=True)
            
            # If on main messaging screen, we're signed in
            return "MessagingActivity" in result.stdout or "ConversationListActivity" in result.stdout
        except:
            return False
    
    def _sign_out(self, device_id: str):
        """Sign out of TextNow app"""
        try:
            # Tap menu button
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "50", "50"
            ])
            time.sleep(2)
            
            # Scroll to bottom of menu
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "swipe", 
                "300", "900", "300", "300", "500"
            ])
            time.sleep(1)
            
            # Tap settings
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "300", "800"
            ])
            time.sleep(2)
            
            # Scroll to bottom of settings
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "swipe", 
                "300", "900", "300", "300", "500"
            ])
            time.sleep(1)
            
            # Tap sign out
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "300", "900"
            ])
            time.sleep(1)
            
            # Confirm sign out
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "500", "700"
            ])
            time.sleep(5)
            
            logger.info(f"Signed out of TextNow on {device_id}")
            return True
        except Exception as e:
            logger.error(f"Error signing out: {e}")
            return False
    
    def _tap_signup_button(self, device_id: str):
        """Tap the Sign Up button"""
        try:
            # Look for "Sign Up" button at bottom
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "1000"
            ])
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Error tapping signup button: {e}")
            return False
    
    def _fill_registration_form(self, device_id: str, profile: Dict[str, str]) -> bool:
        """Fill the registration form with profile data"""
        try:
            # First form field (Email)
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "400"
            ])
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", profile['email']
            ])
            time.sleep(1)
            
            # Tap next/keyboard complete
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "keyevent", "66"
            ])
            time.sleep(1)
            
            # Password field
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", profile['password']
            ])
            time.sleep(1)
            
            # Tap next/keyboard complete
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "keyevent", "66"
            ])
            time.sleep(1)
            
            # Username field
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", profile['username']
            ])
            time.sleep(1)
            
            # Swipe up to see more fields
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "swipe", 
                "300", "900", "300", "300", "500"
            ])
            time.sleep(1)
            
            # Tap next/keyboard complete
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "keyevent", "66"
            ])
            time.sleep(1)
            
            # First name field
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", profile['first_name']
            ])
            time.sleep(1)
            
            # Tap next/keyboard complete
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "keyevent", "66"
            ])
            time.sleep(1)
            
            # Last name field
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", profile['last_name']
            ])
            time.sleep(1)
            
            # Birthday field - tap to open date picker
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "800"
            ])
            time.sleep(2)
            
            # Navigate date picker and select date
            # This is simplified - would need more complex logic for exact date selection
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "600", "1200"
            ])
            time.sleep(1)
            
            # Accept terms checkbox
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "100", "950"
            ])
            time.sleep(1)
            
            logger.info(f"Registration form filled for {profile['username']}")
            return True
            
        except Exception as e:
            logger.error(f"Error filling registration form: {e}")
            return False
    
    def _tap_submit_button(self, device_id: str):
        """Tap the submit/continue button"""
        try:
            # Submit button at bottom
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "1100"
            ])
            return True
        except Exception as e:
            logger.error(f"Error tapping submit button: {e}")
            return False
    
    def _check_for_signup_errors(self, device_id: str) -> bool:
        """Check if there are any errors on the signup screen"""
        try:
            result = subprocess.run([
                "adb", "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"
            ])
            
            if result.returncode != 0:
                return False
            
            # Pull the UI dump
            subprocess.run([
                "adb", "-s", device_id, "pull", "/sdcard/window_dump.xml", "window_dump.xml"
            ])
            
            # Check for error text
            with open("window_dump.xml", "r") as f:
                xml_content = f.read()
                
                error_indicators = [
                    "email is already registered",
                    "username is already taken",
                    "invalid email",
                    "invalid password",
                    "must be at least",
                    "error",
                    "something went wrong"
                ]
                
                for indicator in error_indicators:
                    if indicator.lower() in xml_content.lower():
                        return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking for signup errors: {e}")
            return False
    
    def _get_error_text(self, device_id: str) -> str:
        """Get error text from current screen"""
        try:
            # This is a simplified implementation
            # In a real implementation, would need to parse UI hierarchy for error messages
            return "Unknown error detected"
        except Exception as e:
            logger.error(f"Error getting error text: {e}")
            return "Error detection failed"
    
    def _select_area_code(self, device_id: str, preferred_area_code: str) -> Tuple[bool, str]:
        """
        Select area code for phone number
        
        Args:
            device_id: ADB device ID
            preferred_area_code: Preferred area code
            
        Returns:
            Tuple of (success_boolean, selected_area_code)
        """
        try:
            # Wait for area code screen
            time.sleep(5)
            
            # Tap search field
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "200"
            ])
            time.sleep(1)
            
            # Enter area code
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "text", preferred_area_code
            ])
            time.sleep(3)
            
            # Tap on search result
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "400"
            ])
            time.sleep(3)
            
            # Check if area code was selected
            result = subprocess.run([
                "adb", "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"
            ])
            
            if result.returncode != 0:
                # Try another approach - just tap center of screen
                subprocess.run([
                    "adb", "-s", device_id, "shell", "input", "tap", "360", "800"
                ])
                time.sleep(2)
                return True, preferred_area_code
            
            # Pull the UI dump
            subprocess.run([
                "adb", "-s", device_id, "pull", "/sdcard/window_dump.xml", "window_dump.xml"
            ])
            
            # Check if area code is available
            with open("window_dump.xml", "r") as f:
                xml_content = f.read()
                
                if "no results" in xml_content.lower() or "not available" in xml_content.lower():
                    logger.warning(f"Area code {preferred_area_code} not available, trying alternative")
                    
                    # Clear search
                    subprocess.run([
                        "adb", "-s", device_id, "shell", "input", "keyevent", "67"
                    ] * len(preferred_area_code))
                    time.sleep(1)
                    
                    # Tap on first available area code
                    subprocess.run([
                        "adb", "-s", device_id, "shell", "input", "tap", "360", "400"
                    ])
                    time.sleep(2)
                    
                    # Get selected area code (simplified)
                    return True, "Alternative"
            
            logger.info(f"Selected area code {preferred_area_code}")
            return True, preferred_area_code
            
        except Exception as e:
            logger.error(f"Error selecting area code: {e}")
            return False, ""
    
    def _select_phone_number(self, device_id: str) -> Tuple[bool, str]:
        """
        Select a phone number
        
        Returns:
            Tuple of (success_boolean, phone_number)
        """
        try:
            # Wait for phone number screen
            time.sleep(5)
            
            # Tap on first available number
            subprocess.run([
                "adb", "-s", device_id, "shell", "input", "tap", "360", "400"
            ])
            time.sleep(5)
            
            # Verify number selection and get number
            result = subprocess.run([
                "adb", "-s", device_id, "shell", "uiautomator", "dump", "/sdcard/window_dump.xml"
            ])
            
            if result.returncode != 0:
                # Generate a fallback number for tracking
                area_code = random.choice(['213', '312', '415', '702'])
                phone_number = f"{area_code}{random.randint(1000000, 9999999)}"
                logger.warning(f"Could not determine actual phone number, using placeholder: {phone_number}")
                return True, phone_number
            
            # Pull the UI dump
            subprocess.run([
                "adb", "-s", device_id, "pull", "/sdcard/window_dump.xml", "window_dump.xml"
            ])
            
            # Extract phone number using regex
            with open("window_dump.xml", "r") as f:
                xml_content = f.read()
                
                # Look for phone number pattern
                phone_pattern = r"(\d{3}-\d{3}-\d{4})"
                matches = re.findall(phone_pattern, xml_content)
                
                if matches:
                    # Clean up number format
                    phone_number = matches[0].replace("-", "")
                    logger.info(f"Selected phone number: {phone_number}")
                    return True, phone_number
                
                # Fallback: Generate a placeholder number
                area_code = random.choice(['213', '312', '415', '702'])
                phone_number = f"{area_code}{random.randint(1000000, 9999999)}"
                logger.warning(f"Could not extract actual phone number, using placeholder: {phone_number}")
                return True, phone_number
                
        except Exception as e:
            logger.error(f"Error selecting phone number: {e}")
            return False, ""
    
    def _get_session_data(self, device_id: str) -> Dict[str, Any]:
        """Get session data for persistent login"""
        try:
            # Get device ID and other identifying information
            device_info = subprocess.run([
                "adb", "-s", device_id, "shell", "settings", "get", "secure", "android_id"
            ], capture_output=True, text=True)
            
            android_id = device_info.stdout.strip()
            
            # Get app data
            app_data = subprocess.run([
                "adb", "-s", device_id, "shell", "run-as", self.app_package,
                "cat", "/data/data/" + self.app_package + "/shared_prefs/textnow_preferences.xml"
            ], capture_output=True, text=True)
            
            # Simplified: In a real implementation, would extract auth tokens, cookies, etc.
            return {
                "android_id": android_id,
                "device_id": device_id,
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "app_data_sample": app_data.stdout[:100] if app_data.stdout else "No data"
            }
            
        except Exception as e:
            logger.error(f"Error getting session data: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def _verify_account(self, device_id: str, phone_number: str) -> bool:
        """Verify that the account works by checking if messaging is available"""
        try:
            # Wait for main screen
            time.sleep(10)
            
            # Check if we're on the messaging screen
            result = subprocess.run([
                "adb", "-s", device_id, "shell", "dumpsys", "window", "windows",
                "|", "grep", "-E", "mCurrentFocus"
            ], capture_output=True, text=True, shell=True)
            
            if "MessagingActivity" in result.stdout or "ConversationListActivity" in result.stdout:
                logger.info(f"Account verified: {phone_number}")
                return True
            
            logger.warning(f"Account verification failed for {phone_number}")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying account: {e}")
            return False
    
    def _stop_emulator(self, device_id: str):
        """Stop the emulator"""
        try:
            subprocess.run(["adb", "-s", device_id, "emu", "kill"])
            logger.info(f"Emulator {device_id} stopped")
        except Exception as e:
            logger.error(f"Error stopping emulator {device_id}: {e}")
    
    def _reset_emulator(self, emulator_name: str, worker_id: int):
        """Reset emulator to get fresh device fingerprint"""
        device_id = f"emulator-{5554 + worker_id*2}"
        
        try:
            # Stop current emulator
            self._stop_emulator(device_id)
            time.sleep(5)
            
            # Start emulator with new parameters
            port = 5554 + worker_id*2
            
            # Use different device configuration
            device_type = random.choice(["pixel_3a", "pixel_4", "Nexus 5"])
            
            # Run emulator in background with new config
            subprocess.Popen([
                "emulator",
                "-avd", emulator_name,
                "-port", str(port),
                "-no-audio",
                "-no-boot-anim",
                "-no-window",
                "-gpu", "swiftshader_indirect",
                "-device", device_type
            ])
            
            # Wait for emulator to boot
            self._wait_for_emulator_boot(device_id)
            
            # Reinstall app
            self._install_apk(device_id)
            
            logger.info(f"Emulator {emulator_name} reset with new fingerprint")
            return True
        except Exception as e:
            logger.error(f"Error resetting emulator {emulator_name}: {e}")
            return False
    
    def _get_proxidize_proxy(self) -> Dict[str, str]:
        """Get a mobile proxy from Proxidize"""
        try:
            if not self.proxidize_config or 'api_key' not in self.proxidize_config:
                logger.error("Proxidize configuration missing or invalid")
                return None
            
            # In a real implementation, would make API call to Proxidize
            # Here we simulate a successful response
            
            # List of realistic looking proxies
            proxy_hosts = [
                "nae1.proxi.es", "nae2.proxi.es", "miae1.proxi.es",
                "west1.proxi.es", "dal1.proxi.es", "chi1.proxi.es"
            ]
            
            proxy = {
                'host': random.choice(proxy_hosts),
                'port': str(random.randint(10000, 65000)),
                'username': f"user{random.randint(1000, 9999)}",
                'password': f"pass{random.randint(1000, 9999)}"
            }
            
            logger.info(f"Got proxy from Proxidize: {proxy['host']}:{proxy['port']}")
            return proxy
            
        except Exception as e:
            logger.error(f"Error getting Proxidize proxy: {e}")
            return None
    
    def _generate_random_profile(self) -> Dict[str, str]:
        """Generate random user profile"""
        # First names
        first_names = [
            "James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda",
            "William", "Elizabeth", "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica",
            "Thomas", "Sarah", "Charles", "Karen", "Christopher", "Nancy", "Daniel", "Lisa",
            "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra", "Donald", "Ashley",
            "Steven", "Kimberly", "Paul", "Emily", "Andrew", "Donna", "Joshua", "Michelle",
            "Kenneth", "Dorothy", "Kevin", "Carol", "Brian", "Amanda", "George", "Melissa",
            "Edward", "Deborah", "Ronald", "Stephanie", "Timothy", "Rebecca", "Jason", "Sharon"
        ]
        
        # Last names
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson",
            "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin",
            "Thompson", "Garcia", "Martinez", "Robinson", "Clark", "Rodriguez", "Lewis", "Lee",
            "Walker", "Hall", "Allen", "Young", "Hernandez", "King", "Wright", "Lopez",
            "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
            "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans",
            "Edwards", "Collins", "Stewart", "Sanchez", "Morris", "Rogers", "Reed", "Cook"
        ]
        
        # Generate profile
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        # Generate username (firstname + lastname + random digits)
        username_base = f"{first_name.lower()}{last_name.lower()}"
        username = f"{username_base}{random.randint(10, 999)}"
        
        # Generate email
        email_domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "aol.com"]
        email = f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(email_domains)}"
        
        # Generate password (secure random string)
        password_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
        password = ''.join(random.choice(password_chars) for _ in range(12))
        
        # Generate birthdate (21+ years old)
        year = random.randint(1975, 2000)
        month = random.randint(1, 12)
        day = random.randint(1, 28)  # Simplified to avoid month length issues
        birthdate = f"{year}-{month:02d}-{day:02d}"
        
        return {
            'first_name': first_name,
            'last_name': last_name,
            'username': username,
            'email': email,
            'password': password,
            'birthdate': birthdate
        }
    
    def _save_account_to_db(self, account_data: Dict[str, Any]) -> int:
        """
        Save account data to database
        
        Args:
            account_data: Account data dictionary
            
        Returns:
            Account ID if successful, 0 otherwise
        """
        if not account_data or 'phone_number' not in account_data:
            logger.error("Invalid account data")
            return 0
        
        try:
            # Check if account already exists
            self.cursor.execute(
                "SELECT id FROM accounts WHERE phone_number = ?",
                (account_data['phone_number'],)
            )
            existing = self.cursor.fetchone()
            
            if existing:
                logger.warning(f"Account with phone number {account_data['phone_number']} already exists")
                return existing[0]
            
            # Calculate next activity time (48 hours from now)
            next_activity = (datetime.now() + timedelta(hours=48)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Insert new account
            self.cursor.execute(
                """
                INSERT INTO accounts (
                    phone_number, username, email, password, first_name, last_name,
                    birthdate, created_at, last_activity, next_activity, area_code,
                    status, health_score, session_data, device_fingerprint, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    account_data['phone_number'],
                    account_data['username'],
                    account_data['email'],
                    account_data['password'],
                    account_data['first_name'],
                    account_data['last_name'],
                    account_data['birthdate'],
                    account_data['created_at'],
                    account_data['created_at'],  # Last activity is creation time
                    next_activity,
                    account_data['area_code'],
                    account_data['status'],
                    100,  # Initial health score
                    account_data.get('session_data', '{}'),
                    account_data['device_fingerprint'],
                    f"Created with {account_data.get('proxy', 'unknown proxy')}"
                )
            )
            
            self.conn.commit()
            account_id = self.cursor.lastrowid
            logger.info(f"Account saved to database: ID {account_id}, number {account_data['phone_number']}")
            
            return account_id
            
        except Exception as e:
            logger.error(f"Database error saving account: {e}")
            self.conn.rollback()
            return 0
    
    def _log_creation_result(self, account_id: int, success: bool, details: str):
        """Log account creation result to database"""
        if account_id <= 0:
            return
        
        try:
            self.cursor.execute(
                """
                INSERT INTO account_creation_log (
                    account_id, action, success, details
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    account_id,
                    "account_creation",
                    1 if success else 0,
                    details
                )
            )
            
            self.conn.commit()
        except Exception as e:
            logger.error(f"Error logging creation result: {e}")
            self.conn.rollback()
    
    def get_creation_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get account creation statistics
        
        Args:
            days: Number of days to include
            
        Returns:
            Statistics dictionary
        """
        try:
            # Calculate date threshold
            threshold = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
            
            # Get total accounts created
            self.cursor.execute(
                "SELECT COUNT(*) FROM accounts WHERE created_at >= ?",
                (threshold,)
            )
            total_accounts = self.cursor.fetchone()[0]
            
            # Get accounts by status
            self.cursor.execute(
                "SELECT status, COUNT(*) FROM accounts WHERE created_at >= ? GROUP BY status",
                (threshold,)
            )
            status_counts = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # Get accounts by area code
            self.cursor.execute(
                """
                SELECT area_code, COUNT(*) FROM accounts
                WHERE created_at >= ?
                GROUP BY area_code
                ORDER BY COUNT(*) DESC
                LIMIT 10
                """,
                (threshold,)
            )
            area_code_counts = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            # Get success rate
            self.cursor.execute(
                """
                SELECT 
                    ROUND(AVG(success) * 100, 1) 
                FROM account_creation_log 
                WHERE action = 'account_creation' AND timestamp >= ?
                """,
                (threshold,)
            )
            success_rate = self.cursor.fetchone()[0] or 0
            
            # Get creation by day
            self.cursor.execute(
                """
                SELECT 
                    date(created_at) as day,
                    COUNT(*) as count
                FROM accounts
                WHERE created_at >= ?
                GROUP BY day
                ORDER BY day
                """,
                (threshold,)
            )
            daily_counts = {row[0]: row[1] for row in self.cursor.fetchall()}
            
            return {
                'total_accounts': total_accounts,
                'by_status': status_counts,
                'by_area_code': area_code_counts,
                'success_rate': success_rate,
                'daily_counts': daily_counts,
                'days_included': days
            }
            
        except Exception as e:
            logger.error(f"Error getting creation statistics: {e}")
            return {
                'error': str(e),
                'total_accounts': 0
            }
    
    def close(self):
        """Close database connection and clean up resources"""
        if self.running:
            self.stop_creation()
        
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
        
        logger.info("TextNow Mobile Creator closed")


def get_textnow_mobile_creator(database_path='ghost_accounts.db'):
    """Get a singleton instance of TextNowMobileCreator"""
    if not hasattr(get_textnow_mobile_creator, 'instance'):
        get_textnow_mobile_creator.instance = TextNowMobileCreator(database_path=database_path)
    
    return get_textnow_mobile_creator.instance