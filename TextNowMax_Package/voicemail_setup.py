"""
Automated Voicemail Setup for ProgressGhostCreator

This module handles the automatic assignment and setup of custom voicemail greetings
for TextNow accounts using Android emulation and audio injection.
"""

import os
import time
import random
import logging
import sqlite3
import threading
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from audio_manager import AudioManager
from emulator_controller import EmulatorController

class VoicemailSetupManager:
    def __init__(self, 
                db_path: str = 'ghost_accounts.db', 
                voicemail_folder: str = 'voicemail',
                custom_voicemail_folder: Optional[str] = None,
                avd_name: Optional[str] = None,
                max_retry_attempts: int = 3,
                max_parallel_emulators: int = 1):
        """Initialize the voicemail setup manager
        
        Args:
            db_path: Path to the database
            voicemail_folder: Path to the default voicemail folder
            custom_voicemail_folder: Path to custom voicemail files
            avd_name: Android Virtual Device name to use
            max_retry_attempts: Maximum number of retry attempts per account
            max_parallel_emulators: Maximum number of parallel emulators to run
        """
        self.db_path = db_path
        self.voicemail_folder = voicemail_folder
        self.custom_voicemail_folder = custom_voicemail_folder
        self.avd_name = avd_name
        self.max_retry_attempts = max_retry_attempts
        self.max_parallel_emulators = max_parallel_emulators
        
        # Initialize audio manager
        self.audio_manager = AudioManager(
            voicemail_folder=voicemail_folder,
            custom_voicemail_folder=custom_voicemail_folder,
            db_path=db_path
        )
        
        # Database connection
        self.conn = None
        self._connect_db()
        
        # Active emulators
        self.active_emulators: Dict[int, EmulatorController] = {}
        
        # Setup status tracking
        self.setup_running = False
        self.setup_thread = None
        self.accounts_to_setup: List[Dict[str, Any]] = []
        self.accounts_in_progress: Dict[int, Dict[str, Any]] = {}
        self.accounts_completed: List[int] = []
        self.accounts_failed: Dict[int, str] = {}
        
        # Locks for thread safety
        self.emulator_lock = threading.Lock()
        self.db_lock = threading.Lock()
        
    def _connect_db(self):
        """Connect to the database"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            # Create necessary tables if they don't exist
            cursor = self.conn.cursor()
            
            # Table to track voicemail setup status
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS account_voicemail (
                    account_id INTEGER PRIMARY KEY,
                    voicemail_id TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    setup_time TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    last_error TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts(id),
                    FOREIGN KEY (voicemail_id) REFERENCES voicemail_usage(voicemail_id)
                )
            ''')
            
            self.conn.commit()
            logging.info("Connected to database")
            
        except Exception as e:
            logging.error(f"Error connecting to database: {e}")
            self.conn = None
    
    def import_custom_voicemails(self, folder_path: Optional[str] = None) -> int:
        """Import custom voicemails from a folder
        
        Args:
            folder_path: Path to the folder containing voicemail files
            
        Returns:
            Number of new voicemails imported
        """
        if folder_path:
            self.custom_voicemail_folder = folder_path
            self.audio_manager.custom_voicemail_folder = folder_path
            
        return self.audio_manager.import_custom_voicemails(self.custom_voicemail_folder)
    
    def get_accounts_needing_voicemail(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get accounts that need voicemail setup
        
        Args:
            limit: Maximum number of accounts to return
            
        Returns:
            List of account dictionaries
        """
        if not self.conn:
            logging.error("Database connection not available")
            return []
            
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                
                # Find accounts that:
                # 1. Don't have a voicemail record, or
                # 2. Have a 'pending' or 'failed' status
                cursor.execute('''
                    SELECT a.id, a.phone_number, a.username, a.password, a.email, a.status,
                           COALESCE(av.status, 'pending') as voicemail_status,
                           COALESCE(av.retry_count, 0) as retry_count,
                           COALESCE(av.last_error, '') as last_error
                    FROM accounts a
                    LEFT JOIN account_voicemail av ON a.id = av.account_id
                    WHERE a.status = 'active' AND
                          (av.status IS NULL OR av.status IN ('pending', 'failed'))
                    ORDER BY COALESCE(av.retry_count, 0) ASC, a.id ASC
                    LIMIT ?
                ''', (limit,))
                
                accounts = [dict(row) for row in cursor.fetchall()]
                return accounts
                
        except Exception as e:
            logging.error(f"Error getting accounts needing voicemail: {e}")
            return []
    
    def start_voicemail_setup(self, account_ids: Optional[List[int]] = None, max_accounts: Optional[int] = None):
        """Start the voicemail setup process
        
        Args:
            account_ids: Specific account IDs to set up (None for all pending accounts)
            max_accounts: Maximum number of accounts to process
        """
        if self.setup_running:
            logging.warning("Voicemail setup already running")
            return False
            
        try:
            # Get accounts to process
            if account_ids:
                accounts = []
                for account_id in account_ids:
                    # Get the account details
                    cursor = self.conn.cursor()
                    cursor.execute('''
                        SELECT a.id, a.phone_number, a.username, a.password, a.email, a.status,
                               COALESCE(av.status, 'pending') as voicemail_status,
                               COALESCE(av.retry_count, 0) as retry_count,
                               COALESCE(av.last_error, '') as last_error
                        FROM accounts a
                        LEFT JOIN account_voicemail av ON a.id = av.account_id
                        WHERE a.id = ?
                    ''', (account_id,))
                    
                    account = cursor.fetchone()
                    if account:
                        accounts.append(dict(account))
            else:
                accounts = self.get_accounts_needing_voicemail(limit=max_accounts or 1000)
                
            if not accounts:
                logging.info("No accounts need voicemail setup")
                return False
                
            # Set up process tracking
            self.accounts_to_setup = accounts
            self.accounts_in_progress = {}
            self.accounts_completed = []
            self.accounts_failed = {}
            self.setup_running = True
            
            # Start the setup thread
            self.setup_thread = threading.Thread(target=self._voicemail_setup_worker)
            self.setup_thread.daemon = True
            self.setup_thread.start()
            
            logging.info(f"Started voicemail setup for {len(accounts)} accounts")
            return True
            
        except Exception as e:
            logging.error(f"Error starting voicemail setup: {e}")
            self.setup_running = False
            return False
    
    def stop_voicemail_setup(self, wait: bool = True) -> bool:
        """Stop the voicemail setup process
        
        Args:
            wait: Whether to wait for current operations to complete
            
        Returns:
            Success boolean
        """
        if not self.setup_running:
            return True
            
        logging.info("Stopping voicemail setup process")
        self.setup_running = False
        
        # Wait for the thread to finish if requested
        if wait and self.setup_thread and self.setup_thread.is_alive():
            self.setup_thread.join(timeout=60)
            
        # Clean up any active emulators
        for port, emulator in list(self.active_emulators.items()):
            try:
                emulator.stop_emulator()
            except:
                pass
                
        self.active_emulators = {}
        
        return True
    
    def get_setup_status(self) -> Dict[str, Any]:
        """Get the current status of the voicemail setup process
        
        Returns:
            Dictionary with status information
        """
        return {
            "running": self.setup_running,
            "total": len(self.accounts_to_setup) + len(self.accounts_in_progress) + len(self.accounts_completed) + len(self.accounts_failed),
            "pending": len(self.accounts_to_setup),
            "in_progress": len(self.accounts_in_progress),
            "completed": len(self.accounts_completed),
            "failed": len(self.accounts_failed),
            "active_emulators": len(self.active_emulators)
        }
    
    def _voicemail_setup_worker(self):
        """Worker thread to process voicemail setup"""
        logging.info("Voicemail setup worker thread started")
        
        try:
            # Process accounts until none are left or we're stopped
            while self.setup_running and (self.accounts_to_setup or self.accounts_in_progress):
                # Check if we can start more emulators
                with self.emulator_lock:
                    available_slots = self.max_parallel_emulators - len(self.active_emulators)
                    
                # Start new setups if possible
                for _ in range(min(available_slots, len(self.accounts_to_setup))):
                    if not self.setup_running:
                        break
                        
                    if self.accounts_to_setup:
                        account = self.accounts_to_setup.pop(0)
                        setup_thread = threading.Thread(
                            target=self._setup_account_voicemail,
                            args=(account,)
                        )
                        setup_thread.daemon = True
                        setup_thread.start()
                    
                # Small delay before checking again
                time.sleep(1)
                
            logging.info("Voicemail setup worker thread completed")
            
        except Exception as e:
            logging.error(f"Error in voicemail setup worker: {e}")
            
        finally:
            self.setup_running = False
    
    def _setup_account_voicemail(self, account: Dict[str, Any]):
        """Set up voicemail for a specific account
        
        Args:
            account: Account dictionary with details
        """
        account_id = account['id']
        
        # Mark account as in progress
        self.accounts_in_progress[account_id] = account
        
        # Update database status
        self._update_account_status(account_id, 'in_progress')
        
        try:
            # Get a voicemail file for this account
            voicemail_path = self.audio_manager.get_random_voicemail()
            if not voicemail_path:
                raise Exception("No voicemail files available")
                
            # Store voicemail assignment
            voicemail_id = self._assign_voicemail_to_account(account_id, voicemail_path)
            
            # Start an emulator
            emulator = self._get_emulator()
            if not emulator:
                raise Exception("Could not start emulator")
                
            port = emulator.emulator_port
            
            try:
                # Set up the voicemail on TextNow
                success = self._setup_textnow_voicemail(emulator, account, voicemail_path)
                
                if success:
                    # Mark as completed
                    self._update_account_status(account_id, 'completed')
                    logging.info(f"Voicemail setup completed for account {account_id}")
                    self.accounts_completed.append(account_id)
                else:
                    # Mark as failed
                    retry_count = account.get('retry_count', 0) + 1
                    error_msg = "Voicemail setup failed"
                    self._update_account_status(account_id, 'failed', error_msg, retry_count)
                    self.accounts_failed[account_id] = error_msg
                    logging.error(f"Voicemail setup failed for account {account_id}")
                    
            finally:
                # Release the emulator
                self._release_emulator(port)
                
        except Exception as e:
            # Update failure status
            retry_count = account.get('retry_count', 0) + 1
            error_msg = str(e)
            self._update_account_status(account_id, 'failed', error_msg, retry_count)
            self.accounts_failed[account_id] = error_msg
            logging.error(f"Error setting up voicemail for account {account_id}: {e}")
            
        finally:
            # Remove from in-progress list
            if account_id in self.accounts_in_progress:
                del self.accounts_in_progress[account_id]
    
    def _assign_voicemail_to_account(self, account_id: int, voicemail_path: str) -> Optional[str]:
        """Assign a voicemail to an account and record in database
        
        Args:
            account_id: Account ID
            voicemail_path: Path to the voicemail file
            
        Returns:
            Voicemail ID if successful, None otherwise
        """
        try:
            # Use audio manager to track the assignment
            self.audio_manager.assign_voicemail_to_account(account_id, voicemail_path)
            
            # Get the voicemail ID from the path
            filename = os.path.basename(voicemail_path)
            
            with self.db_lock:
                cursor = self.conn.cursor()
                # Check if the voicemail is in the database
                cursor.execute(
                    "SELECT voicemail_id FROM voicemail_usage WHERE filename = ?",
                    (filename,)
                )
                result = cursor.fetchone()
                
                if result:
                    voicemail_id = result[0]
                    
                    # Update the account_voicemail table
                    cursor.execute('''
                        INSERT OR REPLACE INTO account_voicemail
                        (account_id, voicemail_id, status)
                        VALUES (?, ?, 'assigned')
                    ''', (account_id, voicemail_id))
                    
                    self.conn.commit()
                    return voicemail_id
                
            return None
            
        except Exception as e:
            logging.error(f"Error assigning voicemail to account {account_id}: {e}")
            return None
    
    def _update_account_status(self, account_id: int, status: str, error: str = None, retry_count: int = None):
        """Update account voicemail setup status in the database
        
        Args:
            account_id: Account ID
            status: Status string ('pending', 'in_progress', 'completed', 'failed')
            error: Error message if status is 'failed'
            retry_count: Update retry count if provided
        """
        if not self.conn:
            return
            
        try:
            with self.db_lock:
                cursor = self.conn.cursor()
                
                # Check if record exists
                cursor.execute(
                    "SELECT 1 FROM account_voicemail WHERE account_id = ?",
                    (account_id,)
                )
                exists = cursor.fetchone() is not None
                
                if exists:
                    # Prepare update based on provided parameters
                    update_sql = "UPDATE account_voicemail SET status = ?"
                    params = [status]
                    
                    if status == 'completed' or status == 'in_progress':
                        update_sql += ", setup_time = ?"
                        params.append(datetime.now().isoformat())
                        
                    if error is not None:
                        update_sql += ", last_error = ?"
                        params.append(error)
                        
                    if retry_count is not None:
                        update_sql += ", retry_count = ?"
                        params.append(retry_count)
                        
                    update_sql += " WHERE account_id = ?"
                    params.append(account_id)
                    
                    cursor.execute(update_sql, params)
                    
                else:
                    # Create new record
                    insert_sql = '''
                        INSERT INTO account_voicemail
                        (account_id, status, setup_time, retry_count, last_error)
                        VALUES (?, ?, ?, ?, ?)
                    '''
                    cursor.execute(
                        insert_sql, 
                        (
                            account_id, 
                            status, 
                            datetime.now().isoformat() if status == 'completed' or status == 'in_progress' else None,
                            retry_count or 0,
                            error or None
                        )
                    )
                
                self.conn.commit()
                
        except Exception as e:
            logging.error(f"Error updating account status: {e}")
    
    def _get_emulator(self) -> Optional[EmulatorController]:
        """Get an available emulator or start a new one
        
        Returns:
            EmulatorController instance if successful, None otherwise
        """
        with self.emulator_lock:
            # Check if we've reached the maximum number of emulators
            if len(self.active_emulators) >= self.max_parallel_emulators:
                logging.warning("Maximum number of emulators reached")
                return None
                
            # Start a new emulator
            emulator = EmulatorController(avd_name=self.avd_name)
            
            # Find an available port
            port = None
            for i in range(10):
                test_port = 5554 + (i * 2)
                if test_port not in self.active_emulators:
                    port = test_port
                    break
                    
            if port is None:
                logging.error("No available ports for emulator")
                return None
                
            # Start the emulator
            success = emulator.start_emulator(port=port, enable_audio=True)
            
            if not success:
                logging.error(f"Failed to start emulator on port {port}")
                return None
                
            # Store in active emulators
            self.active_emulators[port] = emulator
            logging.info(f"Started emulator on port {port}")
            
            return emulator
    
    def _release_emulator(self, port: int):
        """Release an emulator
        
        Args:
            port: Emulator port
        """
        with self.emulator_lock:
            if port in self.active_emulators:
                emulator = self.active_emulators[port]
                
                try:
                    # Stop the emulator
                    emulator.stop_emulator()
                except Exception as e:
                    logging.error(f"Error stopping emulator on port {port}: {e}")
                    
                # Remove from active emulators
                del self.active_emulators[port]
                logging.info(f"Released emulator on port {port}")
    
    def _setup_textnow_voicemail(self, emulator: EmulatorController, account: Dict[str, Any], voicemail_path: str) -> bool:
        """Set up TextNow voicemail using the emulator
        
        Args:
            emulator: EmulatorController instance
            account: Account dictionary
            voicemail_path: Path to the voicemail file
            
        Returns:
            Success boolean
        """
        try:
            username = account['username']
            password = account['password']
            
            # Install TextNow app if needed
            # In a real implementation, you would have the APK file available
            # For this demo, we'll skip this step
            
            # Launch TextNow app
            textnow_package = "com.enflick.android.TextNow"
            emulator.launch_app(textnow_package)
            
            # Wait for app to load
            time.sleep(5)
            
            # Check if already logged in, if not, login
            if not self._check_logged_in(emulator):
                login_success = self._login_to_textnow(emulator, username, password)
                if not login_success:
                    raise Exception("Failed to log in to TextNow")
                    
                # Wait for login to complete
                time.sleep(5)
            
            # Navigate to settings
            self._navigate_to_settings(emulator)
            
            # Navigate to voicemail settings
            self._navigate_to_voicemail_settings(emulator)
            
            # Set up the voicemail
            return self._set_voicemail_greeting(emulator, voicemail_path)
            
        except Exception as e:
            logging.error(f"Error setting up TextNow voicemail: {e}")
            return False
            
    def _check_logged_in(self, emulator: EmulatorController) -> bool:
        """Check if already logged in to TextNow
        
        Args:
            emulator: EmulatorController instance
            
        Returns:
            True if logged in, False otherwise
        """
        # Take a screenshot and check for login elements
        # This would require image recognition in a real implementation
        # For this demo, we'll assume not logged in
        return False
        
    def _login_to_textnow(self, emulator: EmulatorController, username: str, password: str) -> bool:
        """Log in to TextNow
        
        Args:
            emulator: EmulatorController instance
            username: TextNow username
            password: TextNow password
            
        Returns:
            Success boolean
        """
        try:
            # In a real implementation, you would:
            # 1. Navigate to the login screen
            # 2. Enter username and password
            # 3. Tap login button
            # 4. Verify login success
            
            # For this demo, we'll simulate the process
            
            # Tap on login button (simulate coordinates)
            emulator.tap(250, 500)
            time.sleep(2)
            
            # Enter username
            emulator.input_text(username)
            time.sleep(1)
            
            # Tap on password field
            emulator.tap(250, 600)
            time.sleep(1)
            
            # Enter password
            emulator.input_text(password)
            time.sleep(1)
            
            # Tap login button
            emulator.tap(250, 700)
            time.sleep(5)
            
            # Check for login success
            # In a real implementation, you would verify login success
            
            return True
            
        except Exception as e:
            logging.error(f"Error logging in to TextNow: {e}")
            return False
            
    def _navigate_to_settings(self, emulator: EmulatorController) -> bool:
        """Navigate to TextNow settings
        
        Args:
            emulator: EmulatorController instance
            
        Returns:
            Success boolean
        """
        try:
            # In a real implementation, you would:
            # 1. Tap on profile/menu button
            # 2. Tap on settings option
            
            # For this demo, we'll simulate tapping on specific coordinates
            
            # Tap on menu button (simulate coordinates)
            emulator.tap(50, 50)
            time.sleep(2)
            
            # Tap on settings option
            emulator.tap(150, 300)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to settings: {e}")
            return False
            
    def _navigate_to_voicemail_settings(self, emulator: EmulatorController) -> bool:
        """Navigate to voicemail settings
        
        Args:
            emulator: EmulatorController instance
            
        Returns:
            Success boolean
        """
        try:
            # In a real implementation, you would:
            # 1. Scroll to find voicemail settings
            # 2. Tap on voicemail settings option
            
            # For this demo, we'll simulate the process
            
            # Scroll down to find voicemail settings
            emulator.swipe(250, 700, 250, 300, 500)
            time.sleep(1)
            
            # Tap on voicemail settings
            emulator.tap(250, 500)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to voicemail settings: {e}")
            return False
            
    def _set_voicemail_greeting(self, emulator: EmulatorController, voicemail_path: str) -> bool:
        """Set the voicemail greeting
        
        Args:
            emulator: EmulatorController instance
            voicemail_path: Path to the voicemail file
            
        Returns:
            Success boolean
        """
        try:
            # In a real implementation, you would:
            # 1. Tap on "Record new greeting" button
            # 2. When the recording screen appears, inject the audio
            # 3. Tap on save/confirm button
            
            # For this demo, we'll simulate the process
            
            # Tap on record new greeting button
            emulator.tap(250, 400)
            time.sleep(2)
            
            # Wait for recording screen
            time.sleep(2)
            
            # Inject audio
            emulator.inject_audio(voicemail_path)
            
            # Wait for audio to play
            time.sleep(10)  # This should be adjusted based on audio length
            
            # Tap save button
            emulator.tap(250, 600)
            time.sleep(2)
            
            return True
            
        except Exception as e:
            logging.error(f"Error setting voicemail greeting: {e}")
            return False

# Singleton instance
_voicemail_manager = None

def get_voicemail_manager(**kwargs):
    """Get the singleton voicemail manager instance"""
    global _voicemail_manager
    if _voicemail_manager is None:
        _voicemail_manager = VoicemailSetupManager(**kwargs)
    return _voicemail_manager