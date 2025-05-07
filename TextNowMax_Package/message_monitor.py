"""
Message monitoring system for TextNow accounts
Periodically checks accounts for new messages and can trigger automated responses
"""

import os
import logging
import threading
import time
import json
import sqlite3
import random
from datetime import datetime, timedelta
import ipaddress
import requests
import queue

from token_manager import get_token_manager
from device_manager import DeviceManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class MessageMonitor:
    def __init__(self, database_path='ghost_accounts.db', check_interval=180, stagger_factor=0.3):
        """Initialize the message monitor"""
        self.database_path = database_path
        self.check_interval = check_interval  # seconds between checks (default 3 minutes)
        self.stagger_factor = stagger_factor  # randomize check times to avoid patterns
        self.token_manager = get_token_manager()
        
        # Initialize database connection
        self._init_database()
        
        # Set up worker threads and queues
        self.message_queue = queue.Queue()
        self.priority_queue = queue.PriorityQueue()  # For recently active accounts
        self.running = True
        self.account_threads = {}
        self.max_worker_threads = 20  # Increased number of worker threads
        
        # Track active conversations for more frequent checks
        self.active_conversations = {}
        
        # Start the dispatcher thread
        self.dispatcher_thread = threading.Thread(target=self._dispatcher_thread)
        self.dispatcher_thread.daemon = True
        self.dispatcher_thread.start()
        
        # Start worker threads
        for i in range(self.max_worker_threads):
            worker = threading.Thread(target=self._worker_thread)
            worker.daemon = True
            worker.start()
        
        logging.info(f"Message monitor initialized with {self.max_worker_threads} worker threads")
    
    def _init_database(self):
        """Initialize the database connection and tables"""
        try:
            self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Add message monitoring fields to accounts table if they don't exist
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()
            column_names = [col["name"] for col in columns]
            
            new_columns = [
                ("last_message_check", "TEXT"),
                ("auto_reply_enabled", "INTEGER DEFAULT 0"),
                ("reply_template_id", "INTEGER"),
                ("ip_family", "TEXT"),
                ("proxy_settings", "TEXT")
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in column_names:
                    cursor.execute(f"""
                    ALTER TABLE accounts ADD COLUMN {col_name} {col_type}
                    """)
            
            # Create message_templates table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                template TEXT NOT NULL,
                variables TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT
            )
            """)
            
            # Create message_responses table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                contact TEXT NOT NULL,
                incoming_message TEXT NOT NULL,
                response_message TEXT,
                response_status TEXT,
                received_at TEXT NOT NULL,
                responded_at TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
            """)
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Failed to initialize message monitor database: {e}")
            raise
    
    def _dispatcher_thread(self):
        """Thread that schedules account checks"""
        while self.running:
            try:
                # First, check the priority queue for active conversations that need frequent checks
                while not self.priority_queue.empty():
                    priority, account_info = self.priority_queue.get_nowait()
                    current_time = time.time()
                    
                    # If this account is due for checking
                    if priority <= current_time:
                        account_id = account_info['account_id']
                        logging.info(f"Priority check for active conversation on account {account_id}")
                        
                        # Add to regular queue for immediate processing
                        self.message_queue.put({
                            'action': 'check_messages',
                            'account_id': account_info['account_id'],
                            'phone_number': account_info['phone_number'],
                            'ip_family': account_info['ip_family'],
                            'is_priority': True,
                            'next_check_delay': 60  # Recheck active conversations every minute
                        })
                        
                        # Reschedule this account for the next quick check
                        next_check_time = current_time + 60  # Check again in 60 seconds
                        self.priority_queue.put((next_check_time, account_info))
                    else:
                        # Put it back in the queue if it's not time yet
                        self.priority_queue.put((priority, account_info))
                        break
                
                # Get accounts that need to be checked from the regular schedule
                cursor = self.conn.cursor()
                
                # First prioritize accounts with recent activity (last 24 hours)
                cursor.execute("""
                SELECT a.id, a.phone_number, a.ip_family FROM accounts a
                JOIN message_responses m ON a.id = m.account_id
                WHERE a.active = 1 
                AND a.token_status = 'valid'
                AND datetime(m.received_at) > datetime('now', '-24 hours')
                AND (a.last_message_check IS NULL 
                     OR datetime(a.last_message_check) < datetime('now', ?) )
                GROUP BY a.id
                ORDER BY MAX(datetime(m.received_at)) DESC
                LIMIT 40
                """, (f"-{self.check_interval / 2} seconds",))  # Check active accounts twice as often
                
                active_accounts = cursor.fetchall()
                
                # Then get other accounts that need checking
                cursor.execute("""
                SELECT id, phone_number, ip_family FROM accounts
                WHERE active = 1 
                AND token_status = 'valid'
                AND id NOT IN (SELECT id FROM accounts WHERE id IN 
                    (SELECT DISTINCT account_id FROM message_responses 
                     WHERE datetime(received_at) > datetime('now', '-24 hours')))
                AND (last_message_check IS NULL 
                     OR datetime(last_message_check) < datetime('now', ?) )
                LIMIT 60
                """, (f"-{self.check_interval} seconds",))
                
                regular_accounts = cursor.fetchall()
                
                all_accounts = active_accounts + regular_accounts
                
                if all_accounts:
                    logging.info(f"Scheduling message checks for {len(all_accounts)} accounts ({len(active_accounts)} active, {len(regular_accounts)} regular)")
                    
                    # Schedule each account for checking with staggered timing
                    for i, account in enumerate(all_accounts):
                        account_id = account['id']
                        
                        # Different timing strategy based on account activity
                        is_active = i < len(active_accounts)
                        
                        # Calculate a staggered delay to avoid all accounts checking at exactly the same time
                        # Active accounts get checked sooner with less stagger
                        if is_active:
                            base_delay = i * 1  # 1 second between active account checks
                            random_factor = random.uniform(0, 30)  # Up to 30 seconds of randomness
                            check_interval = self.check_interval / 2  # Active accounts checked twice as often
                        else:
                            base_delay = i * 2  # 2 seconds between regular account checks  
                            random_factor = random.uniform(0, self.check_interval * self.stagger_factor)
                            check_interval = self.check_interval
                            
                        delay = base_delay + random_factor
                        
                        # Log the next check time
                        next_check = datetime.now() + timedelta(seconds=check_interval + delay)
                        logging.debug(f"Account {account_id} scheduled for next check at {next_check.strftime('%H:%M:%S')} ({'active' if is_active else 'regular'})")
                        
                        # Add task to queue with delay info
                        self.message_queue.put({
                            'action': 'check_messages',
                            'account_id': account_id,
                            'phone_number': account['phone_number'],
                            'ip_family': account['ip_family'],
                            'is_active': is_active,
                            'next_check_delay': check_interval + delay  # Store the full delay until next check
                        })
                        
                        # Update last check time to avoid rechecking too soon
                        cursor.execute("""
                        UPDATE accounts 
                        SET last_message_check = ? 
                        WHERE id = ?
                        """, (datetime.now().isoformat(), account_id))
                
                self.conn.commit()
                
            except Exception as e:
                logging.error(f"Error in message monitor dispatcher: {e}")
            
            # Sleep before next check - check more frequently now
            time.sleep(15)  # Check for new accounts to schedule every 15 seconds
    
    def _worker_thread(self):
        """Worker thread to process message checking and responses"""
        while self.running:
            try:
                # Get a task from the queue
                task = self.message_queue.get(timeout=10)
                
                if task['action'] == 'check_messages':
                    # Get the current IP family for this account
                    current_ip_family = task.get('ip_family')
                    
                    # Check if we need to preserve IP family consistency
                    if current_ip_family:
                        device_manager = DeviceManager()
                        
                        # Get current IP and IP family
                        current_ip = device_manager.get_ip_address()
                        ip_family = device_manager.get_ip_family(current_ip)
                        
                        # If we're on a different network family, reset to get new IP
                        if ip_family != current_ip_family:
                            logging.info(f"Current IP family {ip_family} doesn't match account family {current_ip_family}. Resetting connection...")
                            device_manager.reset_connection()
                    
                    # Now process the actual message check
                    self._check_account_messages(task['account_id'], task['phone_number'], task['ip_family'])
                    
                    # Update account's next check time in the database with staggered timing
                    if 'next_check_delay' in task:
                        cursor = self.conn.cursor()
                        next_check_time = datetime.now() + timedelta(seconds=task['next_check_delay'])
                        cursor.execute("""
                        UPDATE accounts 
                        SET next_scheduled_check = ? 
                        WHERE id = ?
                        """, (next_check_time.isoformat(), task['account_id']))
                        self.conn.commit()
                        
                elif task['action'] == 'send_response':
                    self._send_response(task['account_id'], task['contact'], task['message'], task['response_id'])
                
                # Mark task as done
                self.message_queue.task_done()
                
            except queue.Empty:
                # No tasks available, just continue
                pass
            except Exception as e:
                logging.error(f"Error in message monitor worker: {e}")
    
    def _check_account_messages(self, account_id, phone_number, ip_family):
        """Check for new messages for an account"""
        try:
            # Get token for this account
            tokens = self.token_manager.get_tokens(account_id)
            if not tokens:
                logging.warning(f"No valid tokens for account {account_id}, skipping message check")
                return
            
            # Configure IP if needed
            proxy = None
            if ip_family:
                proxy = self._get_proxy_for_ip_family(ip_family)
            
            # In a real implementation, this would use the TextNow API to check messages
            # For now, we'll simulate random messages
            
            # Get last message time for this account to avoid duplicates
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT MAX(received_at) as last_received 
            FROM message_responses 
            WHERE account_id = ?
            """, (account_id,))
            
            last_received = cursor.fetchone()['last_received']
            
            # Simulate checking messages from TextNow API
            new_messages = self._simulate_message_check(account_id, phone_number, last_received)
            
            if new_messages:
                logging.info(f"Found {len(new_messages)} new messages for account {account_id}")
                
                # Process each message
                for message in new_messages:
                    # Store the message
                    cursor.execute("""
                    INSERT INTO message_responses (
                        account_id, contact, incoming_message, 
                        received_at, response_status
                    ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        account_id,
                        message['contact'],
                        message['message'],
                        message['timestamp'],
                        'pending'
                    ))
                    
                    self.conn.commit()
                    
                    # Get the ID of the inserted message
                    response_id = cursor.lastrowid
                    
                    # Check if auto-reply is enabled for this account
                    cursor.execute("""
                    SELECT auto_reply_enabled, reply_template_id 
                    FROM accounts 
                    WHERE id = ?
                    """, (account_id,))
                    
                    account_settings = cursor.fetchone()
                    
                    if account_settings and account_settings['auto_reply_enabled']:
                        # Generate a reply
                        reply = self._generate_reply(account_id, message['contact'], 
                                                    message['message'], 
                                                    account_settings['reply_template_id'])
                        
                        if reply:
                            # Schedule sending the reply
                            self.message_queue.put({
                                'action': 'send_response',
                                'account_id': account_id,
                                'contact': message['contact'],
                                'message': reply,
                                'response_id': response_id
                            })
            
        except Exception as e:
            logging.error(f"Error checking messages for account {account_id}: {e}")
    
    def _simulate_message_check(self, account_id, phone_number, last_received):
        """Simulate checking messages from TextNow API"""
        # This is a placeholder implementation
        # In a real app, this would make API calls to TextNow
        
        # Randomly decide if there are new messages (10% chance)
        if random.random() < 0.1:
            # Generate 1-3 random messages
            num_messages = random.randint(1, 3)
            messages = []
            
            for i in range(num_messages):
                contact = f"(555) {random.randint(100, 999)}-{random.randint(1000, 9999)}"
                
                # Sample message templates
                message_templates = [
                    "Hey, how's it going?",
                    "Can you tell me more about your offers?",
                    "What's the best deal right now?",
                    "Are you still running that special?",
                    "I saw your ad, is it still valid?",
                    "Do you have any new promotions?",
                    "What's the price on that?",
                    "Hey, I'm interested in your service",
                    "Can you give me more details?",
                    "Is this number still active?"
                ]
                
                message = random.choice(message_templates)
                timestamp = datetime.now().isoformat()
                
                messages.append({
                    'contact': contact,
                    'message': message,
                    'timestamp': timestamp
                })
            
            return messages
        
        return []
    
    def _generate_reply(self, account_id, contact, message, template_id):
        """Generate a reply to a message"""
        try:
            cursor = self.conn.cursor()
            
            # Get the template
            if template_id:
                cursor.execute("""
                SELECT * FROM message_templates WHERE id = ?
                """, (template_id,))
            else:
                # Use a default template if none specified
                cursor.execute("""
                SELECT * FROM message_templates ORDER BY id LIMIT 1
                """)
            
            template = cursor.fetchone()
            
            if not template:
                # No template available, use hardcoded defaults
                default_replies = [
                    "Thanks for your message! We'll get back to you shortly.",
                    "Hey there! We appreciate your interest. One of our agents will respond soon.",
                    "Thanks for reaching out! We'll review your message and get back to you.",
                    "Hi! Thanks for your message. We'll respond as soon as possible."
                ]
                return random.choice(default_replies)
            
            # Parse the template
            template_text = template['template']
            
            # Check for variables to replace
            variables = {}
            if template['variables']:
                try:
                    variables = json.loads(template['variables'])
                except:
                    pass
            
            # Replace variables in the template
            for var_name, var_values in variables.items():
                if var_name in template_text and isinstance(var_values, list) and var_values:
                    replacement = random.choice(var_values)
                    template_text = template_text.replace(f"{{{var_name}}}", replacement)
            
            return template_text
            
        except Exception as e:
            logging.error(f"Error generating reply for account {account_id}: {e}")
            return None
    
    def _send_response(self, account_id, contact, message, response_id):
        """Send a response message"""
        try:
            # Get token for this account
            tokens = self.token_manager.get_tokens(account_id)
            if not tokens:
                logging.warning(f"No valid tokens for account {account_id}, cannot send response")
                self._update_response_status(response_id, 'failed', 'No valid tokens')
                return
            
            # Get IP family for this account
            cursor = self.conn.cursor()
            cursor.execute("SELECT ip_family FROM accounts WHERE id = ?", (account_id,))
            account = cursor.fetchone()
            
            proxy = None
            if account and account['ip_family']:
                proxy = self._get_proxy_for_ip_family(account['ip_family'])
            
            # In a real implementation, this would use the TextNow API to send a message
            # For demo purposes, we'll simulate a successful send
            
            # Add a small delay to simulate network latency
            time.sleep(random.uniform(1, 3))
            
            # 90% success rate
            success = random.random() < 0.9
            
            if success:
                self._update_response_status(response_id, 'sent', message)
                logging.info(f"Sent response for account {account_id} to {contact}")
            else:
                self._update_response_status(response_id, 'failed', 'API error')
                logging.warning(f"Failed to send response for account {account_id} to {contact}")
            
        except Exception as e:
            logging.error(f"Error sending response for account {account_id}: {e}")
            self._update_response_status(response_id, 'failed', str(e))
    
    def _update_response_status(self, response_id, status, response_message=None):
        """Update the status of a response in the database"""
        try:
            cursor = self.conn.cursor()
            
            if response_message:
                cursor.execute("""
                UPDATE message_responses 
                SET response_status = ?, response_message = ?, responded_at = ?
                WHERE id = ?
                """, (status, response_message, datetime.now().isoformat(), response_id))
            else:
                cursor.execute("""
                UPDATE message_responses 
                SET response_status = ?, responded_at = ?
                WHERE id = ?
                """, (status, datetime.now().isoformat(), response_id))
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Error updating response status: {e}")
    
    def _get_proxy_for_ip_family(self, ip_family):
        """Get a proxy server for the specified IP family"""
        # This is a placeholder implementation
        # In a real app, this would get a proxy from your proxy provider
        # or configure a mobile connection through ADB
        
        try:
            # Parse the IP family
            if not ip_family:
                return None
            
            # Example format: "192.168.1.0/24"
            # Here you would select a proxy server that is within this subnet
            
            # For demo purposes, we'll just return a simulated proxy configuration
            return {
                'ip_family': ip_family,
                'proxy_url': f"http://proxy{random.randint(1, 10)}.example.com:8080"
            }
            
        except Exception as e:
            logging.error(f"Error getting proxy for IP family {ip_family}: {e}")
            return None
    
    def enable_auto_reply(self, account_id, template_id=None):
        """Enable auto-reply for an account"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
            UPDATE accounts 
            SET auto_reply_enabled = 1, reply_template_id = ?
            WHERE id = ?
            """, (template_id, account_id))
            
            self.conn.commit()
            
            logging.info(f"Enabled auto-reply for account {account_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error enabling auto-reply for account {account_id}: {e}")
            return False
    
    def disable_auto_reply(self, account_id):
        """Disable auto-reply for an account"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
            UPDATE accounts 
            SET auto_reply_enabled = 0
            WHERE id = ?
            """, (account_id,))
            
            self.conn.commit()
            
            logging.info(f"Disabled auto-reply for account {account_id}")
            return True
            
        except Exception as e:
            logging.error(f"Error disabling auto-reply for account {account_id}: {e}")
            return False
    
    def create_template(self, name, template_text, variables=None):
        """Create a new message template"""
        try:
            cursor = self.conn.cursor()
            
            variables_json = None
            if variables:
                variables_json = json.dumps(variables)
            
            cursor.execute("""
            INSERT INTO message_templates (name, template, variables, created_at)
            VALUES (?, ?, ?, ?)
            """, (name, template_text, variables_json, datetime.now().isoformat()))
            
            self.conn.commit()
            
            template_id = cursor.lastrowid
            logging.info(f"Created message template {template_id}: {name}")
            
            return template_id
            
        except Exception as e:
            logging.error(f"Error creating message template: {e}")
            return None
    
    def get_recent_messages(self, account_id=None, limit=50):
        """Get recent messages, optionally filtered by account"""
        try:
            cursor = self.conn.cursor()
            
            if account_id:
                cursor.execute("""
                SELECT m.*, a.phone_number
                FROM message_responses m
                JOIN accounts a ON m.account_id = a.id
                WHERE m.account_id = ?
                ORDER BY m.received_at DESC
                LIMIT ?
                """, (account_id, limit))
            else:
                cursor.execute("""
                SELECT m.*, a.phone_number
                FROM message_responses m
                JOIN accounts a ON m.account_id = a.id
                ORDER BY m.received_at DESC
                LIMIT ?
                """, (limit,))
            
            return cursor.fetchall()
            
        except Exception as e:
            logging.error(f"Error getting recent messages: {e}")
            return []
    
    def set_account_ip_family(self, account_id, ip_family):
        """Set the IP family for an account"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
            UPDATE accounts 
            SET ip_family = ?
            WHERE id = ?
            """, (ip_family, account_id))
            
            self.conn.commit()
            
            logging.info(f"Set IP family for account {account_id}: {ip_family}")
            return True
            
        except Exception as e:
            logging.error(f"Error setting IP family for account {account_id}: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.conn:
            self.conn.close()

# Singleton instance
_message_monitor = None

def get_message_monitor():
    """Get the message monitor singleton instance"""
    global _message_monitor
    if _message_monitor is None:
        _message_monitor = MessageMonitor()
    return _message_monitor