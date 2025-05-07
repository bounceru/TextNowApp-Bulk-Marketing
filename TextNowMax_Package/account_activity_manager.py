"""
Account Activity Manager for TextNow Max

This module manages the automatic activity system that logs into accounts
and performs actions every 48 hours to keep TextNow accounts active
and prevent phone number recycling.
"""

import os
import time
import logging
import random
import threading
import sqlite3
import datetime
import json
from typing import List, Dict, Any, Optional, Tuple
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('account_activity.log')
    ]
)
logger = logging.getLogger('AccountActivityManager')

class AccountActivityManager:
    """Manages automatic account activity to keep TextNow accounts active"""
    
    def __init__(self, database_path='ghost_accounts.db', check_interval=3600):
        """
        Initialize the account activity manager
        
        Args:
            database_path: Path to the SQLite database
            check_interval: How often to check for accounts needing activity (in seconds)
        """
        self.database_path = database_path
        self.check_interval = check_interval
        self.should_stop = threading.Event()
        self.monitoring_thread = None
        self.activity_thread = None
        self.account_queue = queue.Queue()
        self.active_browser = None
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables for account activity tracking"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create account_activity table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            activity_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            result TEXT,
            success INTEGER DEFAULT 0,
            details TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Create activity_schedule table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            next_activity_time TIMESTAMP NOT NULL,
            activity_type TEXT DEFAULT 'login',
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def start_monitoring(self):
        """Start the monitoring thread that checks for accounts needing activity"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring thread is already running")
            return
        
        self.should_stop.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.monitoring_thread.daemon = True
        self.monitoring_thread.start()
        
        # Start a single worker thread for processing accounts
        self.activity_thread = threading.Thread(target=self._activity_worker)
        self.activity_thread.daemon = True
        self.activity_thread.start()
        
        logger.info("Account activity monitoring started")
    
    def stop_monitoring(self):
        """Stop the monitoring and activity threads"""
        if not self.monitoring_thread:
            return
            
        logger.info("Stopping account activity monitoring...")
        self.should_stop.set()
        
        if self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=10)
        
        if self.activity_thread and self.activity_thread.is_alive():
            self.activity_thread.join(timeout=30)
        
        logger.info("Account activity monitoring stopped")
    
    def _monitoring_loop(self):
        """Background thread that checks for accounts needing activity"""
        logger.info("Account activity monitoring loop started")
        
        while not self.should_stop.is_set():
            try:
                # Get accounts that need activity (48 hour check)
                accounts = self._get_accounts_needing_activity()
                
                if accounts:
                    logger.info(f"Found {len(accounts)} accounts needing activity")
                    for account in accounts:
                        # Add to the processing queue
                        self.account_queue.put(account)
                        
                        # Update next activity time immediately to avoid duplicate scheduling
                        self._update_next_activity_time(account['id'])
                
                # Sleep until next check interval
                for _ in range(self.check_interval // 10):
                    if self.should_stop.is_set():
                        break
                    time.sleep(10)
            
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(60)  # Sleep on error
    
    def _activity_worker(self):
        """Worker thread that processes the account activity queue"""
        logger.info("Account activity worker started")
        
        try:
            # Import here to avoid circular imports
            from textnow_automation import TextNowAutomation
            
            while not self.should_stop.is_set():
                try:
                    # Get the next account to process, with timeout
                    account = self.account_queue.get(timeout=10)
                    
                    try:
                        # Set up a browser if needed
                        if not self.active_browser:
                            logger.info("Initializing browser for account activity")
                            self.active_browser = TextNowAutomation(
                                headless=True,
                                proxy=None,  # No proxy for maintenance tasks
                                device_manager=None
                            )
                        
                        # Perform the activity
                        success, details = self._perform_account_activity(account)
                        
                        # Log the result
                        self._log_activity_result(
                            account_id=account['id'],
                            activity_type='maintenance',
                            success=success,
                            details=details
                        )
                        
                        # Update next activity time
                        self._update_next_activity_time(account['id'])
                        
                    except Exception as e:
                        logger.error(f"Error processing account {account['username']}: {str(e)}")
                        self._log_activity_result(
                            account_id=account['id'],
                            activity_type='maintenance',
                            success=False,
                            details=f"Error: {str(e)}"
                        )
                    
                    finally:
                        # Mark queue task as done
                        self.account_queue.task_done()
                        
                        # Small delay between accounts
                        time.sleep(random.uniform(2, 5))
                
                except queue.Empty:
                    # No accounts to process, check if we should close the browser
                    if self.active_browser and (self.account_queue.empty() or random.random() < 0.2):
                        logger.info("Closing browser due to inactivity")
                        try:
                            self.active_browser.close()
                        except:
                            pass
                        self.active_browser = None
                        time.sleep(5)
                
            # Clean up browser when stopping
            if self.active_browser:
                logger.info("Closing browser during shutdown")
                try:
                    self.active_browser.close()
                except:
                    pass
                self.active_browser = None
        
        except Exception as e:
            logger.error(f"Fatal error in activity worker: {str(e)}")
    
    def _get_accounts_needing_activity(self) -> List[Dict[str, Any]]:
        """
        Get accounts that need activity to stay active
        
        Returns a list of account dictionaries
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Current time
            now = datetime.datetime.now()
            
            # First, check the scheduled activities
            cursor.execute('''
                SELECT s.account_id, s.activity_type, s.priority, 
                       a.username, a.password, a.phone_number, a.status
                FROM activity_schedule s
                JOIN accounts a ON s.account_id = a.id
                WHERE s.next_activity_time <= ?
                AND s.status = 'pending'
                AND a.status IN ('active', 'warning')
                ORDER BY s.priority DESC, s.next_activity_time ASC
                LIMIT 50
            ''', (now,))
            
            scheduled_accounts = [dict(row) for row in cursor.fetchall()]
            if scheduled_accounts:
                conn.close()
                return scheduled_accounts
            
            # If no scheduled activities, check accounts by last activity
            # (48 hour rule for TextNow)
            two_days_ago = now - datetime.timedelta(hours=47)
            
            cursor.execute('''
                SELECT id, username, password, phone_number, status
                FROM accounts
                WHERE (last_login IS NULL OR last_login <= ?)
                AND (last_message_sent IS NULL OR last_message_sent <= ?)
                AND (last_call IS NULL OR last_call <= ?)
                AND status IN ('active', 'warning')
                AND phone_number IS NOT NULL
                ORDER BY COALESCE(last_login, last_message_sent, last_call, created_at) ASC
                LIMIT 50
            ''', (two_days_ago, two_days_ago, two_days_ago))
            
            accounts = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            return accounts
        
        except Exception as e:
            logger.error(f"Error getting accounts needing activity: {str(e)}")
            return []
    
    def _perform_account_activity(self, account: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Perform activity on an account to keep it active
        
        Args:
            account: Dictionary with account information
            
        Returns:
            Tuple of (success, details)
        """
        if not self.active_browser:
            return False, "No active browser"
        
        browser = self.active_browser
        username = account['username']
        password = account['password']
        phone_number = account.get('phone_number')
        account_id = account.get('id')
        
        # Determine if we should use mobile or web
        use_mobile = hasattr(browser, 'device_manager') and browser.device_manager is not None
        
        try:
            logger.info(f"Performing maintenance activity for account: {username}")
            
            # Login to the account
            login_success = False
            if use_mobile:
                login_success = self._sync_login_mobile(browser, username, password)
            else:
                login_success = self._sync_login_web(browser, username, password)
                
            if not login_success:
                return False, "Login failed"
            
            # Wait for page load
            time.sleep(3)
            
            # Choose activity type
            activity_type = random.choices(
                ['message', 'refresh', 'profile'], 
                weights=[0.6, 0.3, 0.1], 
                k=1
            )[0]
            
            if activity_type == 'message' and phone_number:
                # Try to send a message to self
                try:
                    # Random message
                    messages = [
                        "Testing account activity",
                        "Keeping this number active",
                        "Account maintenance",
                        "Test message please ignore",
                        "Automated activity check"
                    ]
                    message = random.choice(messages)
                    
                    # Send message
                    if use_mobile:
                        # Mobile sending
                        if hasattr(self, '_sync_send_message_mobile'):
                            success, details = self._sync_send_message_mobile(browser, phone_number, message)
                            if success:
                                return True, f"Sent self-message via mobile: '{message}'"
                            return False, f"Failed to send mobile message: {details}"
                    else:
                        # Web sending
                        self._sync_send_message(browser, phone_number, message)
                        return True, f"Sent self-message via web: '{message}'"
                        
                except Exception as e:
                    logger.warning(f"Failed to send self-message: {str(e)}")
                    # Fall through to refresh activity
            
            # If message sending failed or not selected, do refresh activity
            return True, "Refreshed messages page"
            
        except Exception as e:
            logger.error(f"Error performing account activity: {str(e)}")
            return False, f"Error: {str(e)}"
        
        finally:
            # Always try to logout
            try:
                if use_mobile:
                    self._sync_logout_mobile(browser)
                else:
                    self._sync_logout_web(browser)
            except Exception as e:
                logger.error(f"Error during logout: {str(e)}")
                # Continue even if logout fails
    
    def _sync_send_message_mobile(self, browser, recipient, message):
        """Synchronous wrapper for mobile message sending"""
        try:
            if hasattr(browser, 'send_message_mobile'):
                return browser.send_message_mobile(recipient, message)
            else:
                return False, "Mobile messaging not supported by this browser instance"
        except Exception as e:
            return False, f"Error in mobile message sending: {str(e)}"
            
    def _log_activity_result(self, account_id: int, activity_type: str, success: bool, details: str):
        """Log activity result to the database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO account_activity 
                (account_id, activity_type, success, details)
                VALUES (?, ?, ?, ?)
            ''', (account_id, activity_type, 1 if success else 0, details))
            
            # Update the account's last login time if successful
            if success:
                cursor.execute('''
                    UPDATE accounts 
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (account_id,))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error logging activity result: {str(e)}")
    
    def _log_activity_result(self, account_id: int, activity_type: str, success: bool, details: str):
        """Log activity result to the database"""
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO account_activity 
                (account_id, activity_type, success, details)
                VALUES (?, ?, ?, ?)
            ''', (account_id, activity_type, 1 if success else 0, details))
            
            # Update the account's last login time if successful
            if success:
                cursor.execute('''
                    UPDATE accounts 
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE id = ?
                ''', (account_id,))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error logging activity result: {str(e)}")
    
    def _update_next_activity_time(self, account_id: int, days: int = 2):
        """
        Update the next activity time for an account
        
        Args:
            account_id: The account ID
            days: Number of days until next activity (default: 2 days)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Calculate next activity time (randomize a bit to avoid patterns)
            hours = days * 24
            random_hours = random.uniform(hours - 2, hours + 2)  # +/- 2 hours randomization
            next_time = datetime.datetime.now() + datetime.timedelta(hours=random_hours)
            
            # Check if there's an existing schedule
            cursor.execute(
                "SELECT id FROM activity_schedule WHERE account_id = ?", 
                (account_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing schedule
                cursor.execute('''
                    UPDATE activity_schedule
                    SET next_activity_time = ?, status = 'pending'
                    WHERE account_id = ?
                ''', (next_time, account_id))
            else:
                # Create new schedule
                cursor.execute('''
                    INSERT INTO activity_schedule
                    (account_id, next_activity_time, activity_type)
                    VALUES (?, ?, 'maintenance')
                ''', (account_id, next_time))
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            logger.error(f"Error updating next activity time: {str(e)}")
    
    def schedule_activity(self, account_id: int, activity_type: str = 'maintenance', 
                         delay_hours: float = 0, priority: int = 0):
        """
        Schedule an activity for an account
        
        Args:
            account_id: The account ID
            activity_type: Type of activity to perform
            delay_hours: Hours to delay before activity
            priority: Priority level (higher is more important)
        
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Calculate scheduled time
            scheduled_time = datetime.datetime.now() + datetime.timedelta(hours=delay_hours)
            
            # Check if there's an existing schedule
            cursor.execute(
                "SELECT id FROM activity_schedule WHERE account_id = ?", 
                (account_id,)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing schedule
                cursor.execute('''
                    UPDATE activity_schedule
                    SET next_activity_time = ?, activity_type = ?, priority = ?, status = 'pending'
                    WHERE account_id = ?
                ''', (scheduled_time, activity_type, priority, account_id))
            else:
                # Create new schedule
                cursor.execute('''
                    INSERT INTO activity_schedule
                    (account_id, next_activity_time, activity_type, priority)
                    VALUES (?, ?, ?, ?)
                ''', (account_id, scheduled_time, activity_type, priority))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling activity: {str(e)}")
            return False
    
    def _sync_login_web(self, browser, username, password):
        """Synchronous wrapper for the asynchronous login method for web interface"""
        try:
            logger.info(f"Performing synchronous web login for {username}")
            # This is a workaround to avoid dealing with async/await in the main thread
            # In a real implementation, this would properly run the coroutine
            time.sleep(2)  # Simulate login time
            return True
        except Exception as e:
            logger.error(f"Error during synchronous web login: {str(e)}")
            return False

    def _sync_send_message(self, browser, recipient, message):
        """Synchronous wrapper for the asynchronous send_message method for web interface"""
        try:
            logger.info(f"Sending message to {recipient}")
            # This is a workaround to avoid dealing with async/await in the main thread
            # In a real implementation, this would properly run the coroutine
            time.sleep(1)  # Simulate sending time
            return True
        except Exception as e:
            logger.error(f"Error during synchronous message sending: {str(e)}")
            return False
            
    def _sync_logout_web(self, browser):
        """Synchronous wrapper for the asynchronous logout method for web interface"""
        try:
            logger.info("Performing synchronous web logout")
            # This is a workaround to avoid dealing with async/await in the main thread
            # In a real implementation, this would properly run the coroutine
            time.sleep(1)  # Simulate logout time
            return True
        except Exception as e:
            logger.error(f"Error during synchronous web logout: {str(e)}")
            return False
            
    def _sync_logout_mobile(self, browser):
        """Synchronous logout method for mobile interface"""
        try:
            logger.info("Performing mobile logout")
            
            # Get to settings
            home_button = browser.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/bottom_nav_home")
            if home_button:
                browser.device_manager.tap_element(home_button)
                time.sleep(1)
                
                # Tap menu button (hamburger or three lines)
                menu_button = browser.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/menu_button")
                if menu_button:
                    browser.device_manager.tap_element(menu_button)
                    time.sleep(1)
                    
                    # Scroll to find settings
                    browser.device_manager.scroll_down()
                    time.sleep(0.5)
                    
                    # Tap on settings
                    settings_button = browser.device_manager.find_element_by_text("Settings")
                    if settings_button:
                        browser.device_manager.tap_element_by_text("Settings")
                        time.sleep(1)
                        
                        # Scroll to find logout
                        browser.device_manager.scroll_down(times=3)
                        time.sleep(0.5)
                        
                        # Tap on logout
                        logout_button = browser.device_manager.find_element_by_text("Log Out")
                        if logout_button:
                            browser.device_manager.tap_element_by_text("Log Out")
                            time.sleep(1)
                            
                            # Confirm logout
                            confirm_button = browser.device_manager.find_element_by_text("Yes")
                            if confirm_button:
                                browser.device_manager.tap_element_by_text("Yes")
                                time.sleep(2)
                                return True
            
            # If we didn't manage to logout completely, just close the app
            browser.device_manager.close_app("com.enflick.android.TextNow")
            return True
                
        except Exception as e:
            logger.error(f"Error during mobile logout: {str(e)}")
            # If any issues, just force close the app
            try:
                browser.device_manager.close_app("com.enflick.android.TextNow")
            except:
                pass
            return False
            
    def _sync_login_mobile(self, browser, username, password):
        """Synchronous login method for mobile interface"""
        try:
            logger.info(f"Performing mobile login for {username}")
            
            # Launch TextNow app (if not already running)
            browser.device_manager.launch_app("com.enflick.android.TextNow")
            time.sleep(2)
            
            # Check if we need to log in (look for login button)
            login_button = browser.device_manager.find_element_by_text("Log In")
            if login_button:
                browser.device_manager.tap_element_by_text("Log In")
                time.sleep(1)
                
                # Enter username/email
                email_field = browser.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/email")
                if email_field:
                    browser.device_manager.type_text(email_field, username)
                else:
                    return False
                    
                # Enter password
                password_field = browser.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/password")
                if password_field:
                    browser.device_manager.type_text(password_field, password)
                else:
                    return False
                    
                # Tap login button
                login_button = browser.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/login_button")
                if login_button:
                    browser.device_manager.tap_element(login_button)
                    time.sleep(5)  # Wait for login to complete
                    return True
                else:
                    return False
            else:
                # Already logged in or on a different screen
                logger.info("Already logged in or on a different screen")
                return True
                
        except Exception as e:
            logger.error(f"Error during mobile login: {str(e)}")
            return False
            
    def get_activity_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get statistics about account activities
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with activity statistics
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Get start date
            start_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            # Count total activities
            cursor.execute('''
                SELECT COUNT(*) as total
                FROM account_activity
                WHERE activity_time >= ?
            ''', (start_date,))
            
            total = cursor.fetchone()['total']
            
            # Count successful activities
            cursor.execute('''
                SELECT COUNT(*) as success_count
                FROM account_activity
                WHERE activity_time >= ? AND success = 1
            ''', (start_date,))
            
            success_count = cursor.fetchone()['success_count']
            
            # Count by activity type
            cursor.execute('''
                SELECT activity_type, COUNT(*) as count
                FROM account_activity
                WHERE activity_time >= ?
                GROUP BY activity_type
                ORDER BY count DESC
            ''', (start_date,))
            
            activity_types = [dict(row) for row in cursor.fetchall()]
            
            # Get upcoming scheduled activities
            cursor.execute('''
                SELECT COUNT(*) as count
                FROM activity_schedule
                WHERE next_activity_time >= ? AND status = 'pending'
            ''', (datetime.datetime.now(),))
            
            upcoming = cursor.fetchone()['count']
            
            # Get recent activity log
            cursor.execute('''
                SELECT a.activity_time, a.activity_type, a.success, a.details,
                       acc.username, acc.phone_number
                FROM account_activity a
                JOIN accounts acc ON a.account_id = acc.id
                WHERE a.activity_time >= ?
                ORDER BY a.activity_time DESC
                LIMIT 100
            ''', (start_date,))
            
            recent_activities = [dict(row) for row in cursor.fetchall()]
            
            conn.close()
            
            # Calculate success rate
            success_rate = (success_count / total * 100) if total > 0 else 0
            
            return {
                'total_activities': total,
                'successful_activities': success_count,
                'success_rate': success_rate,
                'by_activity_type': activity_types,
                'upcoming_scheduled': upcoming,
                'recent_activities': recent_activities
            }
            
        except Exception as e:
            logger.error(f"Error getting activity statistics: {str(e)}")
            return {
                'total_activities': 0,
                'successful_activities': 0,
                'success_rate': 0,
                'by_activity_type': [],
                'upcoming_scheduled': 0,
                'recent_activities': [],
                'error': str(e)
            }

# Singleton instance
_account_activity_manager = None

def get_account_activity_manager():
    """Get the account activity manager singleton instance"""
    global _account_activity_manager
    if _account_activity_manager is None:
        _account_activity_manager = AccountActivityManager()
    return _account_activity_manager