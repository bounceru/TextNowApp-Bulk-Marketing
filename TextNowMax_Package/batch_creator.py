"""
Batch Account Creator for ProgressGhostCreator

This module handles the creation of multiple TextNow accounts in a batch process,
with proper error handling, resume capabilities, and progress tracking.
"""

import os
import time
import random
import logging
import json
import threading
import queue
import traceback
from datetime import datetime

# Local imports
from textnow_bot import TextNowBot
from device_manager import DeviceManager
from fingerprint_manager import FingerprintManager
from data_manager import DataManager
from account_health import get_account_health_monitor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("batch_creator.log"),
        logging.StreamHandler()
    ]
)

class BatchCreator:
    def __init__(self, database_path='ghost_accounts.db', resume_file='batch_resume.json'):
        """Initialize the batch creator"""
        self.database_path = database_path
        self.resume_file = resume_file
        self.device_manager = DeviceManager()
        self.fingerprint_manager = FingerprintManager(database_path)
        self.data_manager = DataManager()
        self.health_monitor = get_account_health_monitor()
        
        # Batch processing state
        self.is_running = False
        self.is_paused = False
        self.current_batch = None
        self.created_count = 0
        self.failed_count = 0
        self.total_count = 0
        self.start_time = None
        self.accounts_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.worker_threads = []
        
        # Worker count (parallel account creation)
        self.worker_count = 1  # Default is 1, as we typically want sequential IP rotation
        
        # Event callbacks
        self.on_progress = None
        self.on_complete = None
        self.on_error = None
    
    def start_batch(self, count, area_codes=None, worker_count=1):
        """Start a new batch creation process"""
        if self.is_running:
            logging.warning("Batch creation is already running")
            return False
        
        # Setup batch parameters
        self.total_count = count
        self.worker_count = worker_count
        self.is_running = True
        self.is_paused = False
        self.created_count = 0
        self.failed_count = 0
        self.start_time = datetime.now()
        
        # Check for resume data
        resume_data = self._load_resume_data()
        if resume_data and 'batch_id' in resume_data:
            # Resume previous batch
            self.current_batch = resume_data['batch_id']
            self.created_count = resume_data.get('created_count', 0)
            self.failed_count = resume_data.get('failed_count', 0)
            self.start_time = datetime.fromisoformat(resume_data.get('start_time', datetime.now().isoformat()))
            logging.info(f"Resuming batch {self.current_batch}: Created: {self.created_count}, Failed: {self.failed_count}")
        else:
            # Create a new batch ID
            self.current_batch = f"batch_{int(time.time())}"
            logging.info(f"Starting new batch {self.current_batch} to create {count} accounts")
            
            # Save initial resume data
            self._save_resume_data()
        
        # Prepare area codes
        if not area_codes:
            # Default area codes
            area_codes = ['201', '240', '301', '302', '303', '304', '305', '308', '309']
        
        # Queue up the accounts to create
        remaining = count - (self.created_count + self.failed_count)
        for i in range(remaining):
            # Pick a random area code for each account
            area_code = random.choice(area_codes)
            self.accounts_queue.put({
                'index': i + self.created_count + self.failed_count + 1,
                'area_code': area_code
            })
        
        # Start worker threads
        self._start_workers()
        
        # Start result handler thread
        self._start_result_handler()
        
        return True
    
    def pause_batch(self):
        """Pause the batch creation process"""
        if not self.is_running:
            return False
        
        self.is_paused = True
        logging.info("Pausing batch creation process...")
        
        # Save resume data
        self._save_resume_data()
        
        return True
    
    def resume_batch(self):
        """Resume a paused batch creation process"""
        if not self.is_running or not self.is_paused:
            return False
        
        self.is_paused = False
        logging.info("Resuming batch creation process...")
        
        return True
    
    def stop_batch(self):
        """Stop the batch creation process"""
        if not self.is_running:
            return False
        
        logging.info("Stopping batch creation process...")
        self.is_running = False
        self.is_paused = False
        
        # Wait for threads to complete
        for thread in self.worker_threads:
            if thread.is_alive():
                thread.join(timeout=5)
        
        # Clear the queues
        while not self.accounts_queue.empty():
            try:
                self.accounts_queue.get_nowait()
            except:
                pass
        
        # Save final resume data
        self._save_resume_data()
        
        logging.info(f"Batch creation stopped. Created: {self.created_count}, Failed: {self.failed_count}")
        
        # Call completion callback
        if self.on_complete:
            self.on_complete({
                'batch_id': self.current_batch,
                'created_count': self.created_count,
                'failed_count': self.failed_count,
                'total_count': self.total_count,
                'completed': False,
                'elapsed_time': (datetime.now() - self.start_time).total_seconds()
            })
        
        return True
    
    def get_status(self):
        """Get the current status of the batch creation process"""
        if not self.is_running:
            return {
                'status': 'idle',
                'batch_id': self.current_batch,
                'created_count': self.created_count,
                'failed_count': self.failed_count,
                'total_count': self.total_count,
                'progress_percent': 0,
                'elapsed_time': 0,
                'estimated_time_remaining': 0
            }
        
        total_processed = self.created_count + self.failed_count
        progress_percent = (total_processed / self.total_count) * 100 if self.total_count > 0 else 0
        
        # Calculate estimated time remaining
        elapsed_seconds = (datetime.now() - self.start_time).total_seconds()
        if total_processed > 0:
            seconds_per_account = elapsed_seconds / total_processed
            remaining_accounts = self.total_count - total_processed
            estimated_seconds_remaining = seconds_per_account * remaining_accounts
        else:
            estimated_seconds_remaining = 0
        
        return {
            'status': 'paused' if self.is_paused else 'running',
            'batch_id': self.current_batch,
            'created_count': self.created_count,
            'failed_count': self.failed_count,
            'total_count': self.total_count,
            'progress_percent': progress_percent,
            'elapsed_time': elapsed_seconds,
            'estimated_time_remaining': estimated_seconds_remaining
        }
    
    def _worker_thread(self):
        """Worker thread to create accounts"""
        # Create a bot instance for this worker
        bot = TextNowBot(
            device_manager=self.device_manager,
            fingerprint_manager=self.fingerprint_manager,
            data_manager=self.data_manager,
            database_path=self.database_path
        )
        
        while self.is_running:
            # Check if paused
            if self.is_paused:
                time.sleep(1)
                continue
            
            try:
                # Get the next account to create
                try:
                    account_data = self.accounts_queue.get(timeout=1)
                except queue.Empty:
                    # No more accounts to create
                    break
                
                account_index = account_data['index']
                area_code = account_data['area_code']
                
                logging.info(f"Worker creating account {account_index}/{self.total_count} with area code {area_code}")
                
                # Initialize the driver with a fresh fingerprint
                if not bot.initialize_driver():
                    error_result = {
                        'success': False,
                        'error': "Failed to initialize WebDriver",
                        'account_index': account_index,
                        'area_code': area_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results_queue.put(error_result)
                    continue
                
                # Reset connection to get a new IP
                if not self.device_manager.reset_connection():
                    error_result = {
                        'success': False,
                        'error': "Failed to reset connection for IP rotation",
                        'account_index': account_index,
                        'area_code': area_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results_queue.put(error_result)
                    continue
                
                # Create the account
                success, result = bot.create_account(area_code=area_code)
                
                if success:
                    success_result = {
                        'success': True,
                        'account_id': result,  # Account ID
                        'account_index': account_index,
                        'area_code': area_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results_queue.put(success_result)
                else:
                    error_result = {
                        'success': False,
                        'error': result,  # Error message
                        'account_index': account_index,
                        'area_code': area_code,
                        'timestamp': datetime.now().isoformat()
                    }
                    self.results_queue.put(error_result)
                
                # Clean up
                bot.close()
                
                # Random delay between account creations (30-90 seconds)
                delay = random.randint(30, 90)
                logging.info(f"Waiting {delay} seconds before next account creation")
                
                # Break the delay into smaller chunks so we can check for pause/stop
                for i in range(delay):
                    if not self.is_running or self.is_paused:
                        break
                    time.sleep(1)
            
            except Exception as e:
                logging.error(f"Worker thread error: {e}")
                logging.error(traceback.format_exc())
                
                # Report the error
                error_result = {
                    'success': False,
                    'error': f"Exception: {str(e)}",
                    'account_index': account_index if 'account_index' in locals() else -1,
                    'area_code': area_code if 'area_code' in locals() else None,
                    'timestamp': datetime.now().isoformat()
                }
                self.results_queue.put(error_result)
                
                # Clean up
                try:
                    bot.close()
                except:
                    pass
                
                # Delay before continuing
                time.sleep(5)
        
        # Final cleanup
        bot.close()
        logging.info("Worker thread exiting")
    
    def _result_handler_thread(self):
        """Thread to handle account creation results"""
        while self.is_running:
            try:
                # Get a result from the queue
                try:
                    result = self.results_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                if result['success']:
                    # Successfully created account
                    self.created_count += 1
                    logging.info(f"Account {result['account_index']} created successfully (ID: {result['account_id']})")
                    
                    # Start monitoring the account health
                    self.health_monitor.check_accounts_health(limit=1)
                else:
                    # Failed to create account
                    self.failed_count += 1
                    logging.error(f"Account {result['account_index']} creation failed: {result['error']}")
                    
                    # Log error to database
                    error_data = {
                        'timestamp': result['timestamp'],
                        'error': result['error'],
                        'area_code': result['area_code'],
                        'batch_id': self.current_batch
                    }
                    self.data_manager.log_error(error_data)
                
                # Save resume data periodically
                if (self.created_count + self.failed_count) % 5 == 0:
                    self._save_resume_data()
                
                # Call progress callback
                if self.on_progress:
                    status = self.get_status()
                    status['last_result'] = result
                    self.on_progress(status)
                
                # Check if batch is complete
                if self.created_count + self.failed_count >= self.total_count:
                    logging.info(f"Batch creation complete. Created: {self.created_count}, Failed: {self.failed_count}")
                    self.is_running = False
                    
                    # Save final resume data
                    self._save_resume_data(completed=True)
                    
                    # Call completion callback
                    if self.on_complete:
                        self.on_complete({
                            'batch_id': self.current_batch,
                            'created_count': self.created_count,
                            'failed_count': self.failed_count,
                            'total_count': self.total_count,
                            'completed': True,
                            'elapsed_time': (datetime.now() - self.start_time).total_seconds()
                        })
                    
                    break
            
            except Exception as e:
                logging.error(f"Result handler error: {e}")
                logging.error(traceback.format_exc())
                
                # Call error callback
                if self.on_error:
                    self.on_error({
                        'error': str(e),
                        'traceback': traceback.format_exc()
                    })
                
                time.sleep(5)
        
        logging.info("Result handler thread exiting")
    
    def _start_workers(self):
        """Start worker threads"""
        self.worker_threads = []
        for i in range(self.worker_count):
            thread = threading.Thread(target=self._worker_thread)
            thread.daemon = True
            thread.start()
            self.worker_threads.append(thread)
            logging.info(f"Started worker thread {i+1}")
    
    def _start_result_handler(self):
        """Start the result handler thread"""
        thread = threading.Thread(target=self._result_handler_thread)
        thread.daemon = True
        thread.start()
        logging.info("Started result handler thread")
    
    def _save_resume_data(self, completed=False):
        """Save batch resume data to file"""
        resume_data = {
            'batch_id': self.current_batch,
            'created_count': self.created_count,
            'failed_count': self.failed_count,
            'total_count': self.total_count,
            'start_time': self.start_time.isoformat(),
            'last_updated': datetime.now().isoformat(),
            'completed': completed
        }
        
        try:
            with open(self.resume_file, 'w') as f:
                json.dump(resume_data, f)
        except Exception as e:
            logging.error(f"Failed to save resume data: {e}")
    
    def _load_resume_data(self):
        """Load batch resume data from file"""
        if not os.path.exists(self.resume_file):
            return None
        
        try:
            with open(self.resume_file, 'r') as f:
                resume_data = json.load(f)
            
            # Check if the saved batch was completed
            if resume_data.get('completed', False):
                # Previous batch was completed, so don't resume it
                return None
            
            return resume_data
        except Exception as e:
            logging.error(f"Failed to load resume data: {e}")
            return None


# Singleton instance
_batch_creator = None

def get_batch_creator():
    """Get the batch creator singleton instance"""
    global _batch_creator
    if _batch_creator is None:
        _batch_creator = BatchCreator()
    return _batch_creator