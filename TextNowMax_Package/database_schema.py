"""
Database Schema for ProgressGhostCreator

This module defines the database schema and provides functions for database operations.
"""

import os
import json
import time
import sqlite3
import datetime
import logging
import random
import string
from typing import Dict, List, Optional, Tuple, Any, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database.log')
    ]
)
logger = logging.getLogger('Database')

class Database:
    """Class to handle database operations"""
    
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the database connection"""
        self.database_path = database_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._init_database()
    
    def _connect(self):
        """Connect to the SQLite database"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.database_path}")
        except sqlite3.Error as e:
            logger.error(f"Error connecting to database: {str(e)}")
            raise
    
    def _init_database(self):
        """Initialize the database schema if it doesn't exist"""
        try:
            # Create accounts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT,
                    area_code TEXT,
                    email TEXT,
                    password TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    health_score INTEGER DEFAULT 100,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT,
                    login_cookie TEXT,
                    user_agent TEXT,
                    fingerprint TEXT,
                    ip_used TEXT,
                    profile_pic_path TEXT,
                    voicemail_id INTEGER,
                    FOREIGN KEY (voicemail_id) REFERENCES voicemails (id)
                )
            ''')
            
            # Create messages table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    images TEXT,
                    status TEXT DEFAULT 'pending', -- pending, sent, failed, delivered, replied
                    scheduled_time TEXT,
                    sent_time TEXT,
                    response TEXT,
                    response_time TEXT,
                    campaign_id INTEGER,
                    FOREIGN KEY (account_id) REFERENCES accounts (id),
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id)
                )
            ''')
            
            # Create campaigns table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT DEFAULT 'draft', -- draft, active, paused, completed
                    start_date TEXT,
                    end_date TEXT,
                    target_count INTEGER DEFAULT 0,
                    completion_count INTEGER DEFAULT 0,
                    success_rate REAL DEFAULT 0,
                    area_codes TEXT,
                    template_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT,
                    FOREIGN KEY (template_id) REFERENCES message_templates (id)
                )
            ''')
            
            # Create message templates table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    variables TEXT, -- JSON array of variable names
                    image_category TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')
            
            # Create voicemails table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS voicemails (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    duration INTEGER, -- in seconds
                    type TEXT, -- male, female, custom
                    text_content TEXT, -- original text for TTS voicemails
                    checksum TEXT, -- to identify duplicates
                    use_count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create images table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    category TEXT, -- profile, message, sports, betting, etc.
                    description TEXT,
                    use_count INTEGER DEFAULT 0,
                    checksum TEXT, -- to identify duplicates
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create health_checks table for account monitoring
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    check_type TEXT NOT NULL, -- login, message, voicemail, etc.
                    status TEXT NOT NULL, -- passed, failed, warning
                    score INTEGER, -- 0-100
                    details TEXT, -- JSON with additional info
                    check_date TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create ip_rotations table to track IP changes
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_rotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    old_ip TEXT,
                    new_ip TEXT,
                    success BOOLEAN,
                    duration INTEGER, -- in seconds
                    device_id TEXT,
                    notes TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create errors table for tracking errors
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT NOT NULL,
                    component TEXT,
                    details TEXT,
                    account_id INTEGER,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    resolved BOOLEAN DEFAULT 0,
                    resolution TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create settings table for application settings
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT,
                    UNIQUE(category, key)
                )
            ''')
            
            # Create target_lists table for managing lists of phone numbers
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_lists (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    count INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                )
            ''')
            
            # Create target_numbers table for storing individual phone numbers
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS target_numbers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    list_id INTEGER NOT NULL,
                    phone_number TEXT NOT NULL,
                    status TEXT DEFAULT 'active', -- active, used, blocked, invalid
                    last_used TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (list_id) REFERENCES target_lists (id)
                )
            ''')
            
            # Create campaign_targets table to link campaigns with target numbers
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaign_targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    campaign_id INTEGER NOT NULL,
                    target_number TEXT NOT NULL,
                    status TEXT DEFAULT 'pending', -- pending, sent, failed, responded
                    sent_at TEXT,
                    account_id INTEGER, -- which account sent the message
                    message_variation INTEGER, -- index of the message variation used
                    response TEXT, -- any response received
                    response_at TEXT,
                    FOREIGN KEY (campaign_id) REFERENCES campaigns (id),
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Save the changes
            self.conn.commit()
            logger.info("Database schema initialized")
            
            # Initialize default settings if not already present
            self._init_default_settings()
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _init_default_settings(self):
        """Initialize default settings if not present"""
        default_settings = [
            # General settings
            ('general', 'app_name', 'ProgressGhostCreator'),
            ('general', 'debug_mode', 'false'),
            
            # Account creation settings
            ('creation', 'preferred_area_codes', '954,754,305,786,561'),
            ('creation', 'max_accounts_per_day', '50'),
            ('creation', 'pause_between_accounts', '120'),
            
            # Messaging settings
            ('messaging', 'messages_per_day', '100'),
            ('messaging', 'start_hour', '8'),
            ('messaging', 'end_hour', '20'),
            ('messaging', 'min_delay', '30'),
            ('messaging', 'max_delay', '300'),
            
            # Device settings
            ('device', 'phone_model', 'BLU G44'),
            ('device', 'adb_path', 'platform-tools/adb'),
            ('device', 'ip_rotation_method', 'airplane'),
            ('device', 'rotation_frequency', '10')
        ]
        
        try:
            for category, key, value in default_settings:
                # Check if setting exists
                self.cursor.execute(
                    "SELECT COUNT(*) FROM settings WHERE category=? AND key=?",
                    (category, key)
                )
                if self.cursor.fetchone()[0] == 0:
                    # Insert the setting
                    self.cursor.execute(
                        "INSERT INTO settings (category, key, value) VALUES (?, ?, ?)",
                        (category, key, value)
                    )
            
            self.conn.commit()
            logger.info("Default settings initialized")
        except sqlite3.Error as e:
            logger.error(f"Error initializing default settings: {str(e)}")
            self.conn.rollback()
    
    def add_account(self, phone_number, name, password, username=None, area_code=None, email=None, 
                    status='active', login_cookie=None, user_agent=None, fingerprint=None, 
                    ip_used=None, profile_pic_path=None, voicemail_id=None):
        """Add a new account to the database"""
        try:
            # Check if phone number already exists
            self.cursor.execute("SELECT id FROM accounts WHERE phone_number=?", (phone_number,))
            existing = self.cursor.fetchone()
            if existing:
                # Update existing account
                self.cursor.execute(
                    """
                    UPDATE accounts SET 
                    name=?, username=?, area_code=?, email=?, password=?, status=?, 
                    last_used=CURRENT_TIMESTAMP, login_cookie=?, user_agent=?, 
                    fingerprint=?, ip_used=?, profile_pic_path=?, voicemail_id=?
                    WHERE phone_number=?
                    """,
                    (name, username, area_code, email, password, status, 
                     login_cookie, user_agent, fingerprint, ip_used, 
                     profile_pic_path, voicemail_id, phone_number)
                )
                self.conn.commit()
                logger.info(f"Updated existing account with phone number {phone_number}")
                return existing[0]
            
            # Insert new account
            self.cursor.execute(
                """
                INSERT INTO accounts (
                    phone_number, name, username, area_code, email, password, status,
                    login_cookie, user_agent, fingerprint, ip_used, profile_pic_path, voicemail_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (phone_number, name, username, area_code, email, password, status,
                 login_cookie, user_agent, fingerprint, ip_used, profile_pic_path, voicemail_id)
            )
            self.conn.commit()
            account_id = self.cursor.lastrowid
            logger.info(f"Added new account with ID {account_id} and phone number {phone_number}")
            return account_id
        except sqlite3.Error as e:
            logger.error(f"Error adding account: {str(e)}")
            self.conn.rollback()
            raise
    
    def get_account(self, account_id=None, phone_number=None):
        """Get account details from database"""
        try:
            if account_id:
                self.cursor.execute(
                    "SELECT * FROM accounts WHERE id=?", 
                    (account_id,)
                )
            elif phone_number:
                self.cursor.execute(
                    "SELECT * FROM accounts WHERE phone_number=?", 
                    (phone_number,)
                )
            else:
                logger.error("Either account_id or phone_number must be provided")
                return None
            
            account = self.cursor.fetchone()
            if account:
                return dict(account)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting account: {str(e)}")
            return None
    
    def update_account(self, account_id, **kwargs):
        """Update an account in the database"""
        try:
            # Build the SET part of the SQL query dynamically based on provided kwargs
            set_clauses = []
            params = []
            
            for key, value in kwargs.items():
                set_clauses.append(f"{key}=?")
                params.append(value)
            
            # Add account_id to params
            params.append(account_id)
            
            # Execute the update query
            self.cursor.execute(
                f"UPDATE accounts SET {', '.join(set_clauses)} WHERE id=?",
                tuple(params)
            )
            self.conn.commit()
            logger.info(f"Updated account with ID {account_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating account: {str(e)}")
            self.conn.rollback()
            return False
    
    def delete_account(self, account_id):
        """Delete an account from the database"""
        try:
            # First update the status to 'deleted'
            self.cursor.execute(
                "UPDATE accounts SET status='deleted' WHERE id=?",
                (account_id,)
            )
            self.conn.commit()
            logger.info(f"Marked account with ID {account_id} as deleted")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting account: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_accounts(self, status=None, area_code=None, limit=None, offset=0):
        """Get a list of accounts from the database"""
        try:
            query = "SELECT * FROM accounts"
            params = []
            
            # Add WHERE clauses based on parameters
            where_clauses = []
            if status:
                where_clauses.append("status=?")
                params.append(status)
            if area_code:
                where_clauses.append("area_code=?")
                params.append(area_code)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            accounts = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(account) for account in accounts]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting accounts: {str(e)}")
            return []
    
    def add_message(self, account_id, recipient, content, images=None, scheduled_time=None, campaign_id=None):
        """Add a new message to the database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO messages (
                    account_id, recipient, content, images, scheduled_time, campaign_id
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account_id, recipient, content, images, scheduled_time, campaign_id)
            )
            self.conn.commit()
            message_id = self.cursor.lastrowid
            logger.info(f"Added new message with ID {message_id}")
            return message_id
        except sqlite3.Error as e:
            logger.error(f"Error adding message: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_message(self, message_id):
        """Get message details from database"""
        try:
            self.cursor.execute(
                "SELECT * FROM messages WHERE id=?", 
                (message_id,)
            )
            message = self.cursor.fetchone()
            if message:
                return dict(message)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting message: {str(e)}")
            return None
    
    def update_message_status(self, message_id, status, sent_time=None, response=None, response_time=None):
        """Update the status of a message"""
        try:
            update_query = "UPDATE messages SET status=?"
            params = [status]
            
            if sent_time:
                update_query += ", sent_time=?"
                params.append(sent_time)
            
            if response:
                update_query += ", response=?"
                params.append(response)
            
            if response_time:
                update_query += ", response_time=?"
                params.append(response_time)
            
            update_query += " WHERE id=?"
            params.append(message_id)
            
            self.cursor.execute(update_query, tuple(params))
            self.conn.commit()
            logger.info(f"Updated message with ID {message_id} to status {status}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating message status: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_messages(self, account_id=None, status=None, campaign_id=None, limit=None, offset=0):
        """Get a list of messages from the database"""
        try:
            query = "SELECT * FROM messages"
            params = []
            
            # Add WHERE clauses based on parameters
            where_clauses = []
            if account_id:
                where_clauses.append("account_id=?")
                params.append(account_id)
            if status:
                where_clauses.append("status=?")
                params.append(status)
            if campaign_id:
                where_clauses.append("campaign_id=?")
                params.append(campaign_id)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY COALESCE(sent_time, scheduled_time, CURRENT_TIMESTAMP) DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            messages = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(message) for message in messages]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    def get_pending_messages(self, limit=10):
        """Get a list of pending messages that are due to be sent"""
        try:
            current_time = datetime.datetime.now().isoformat()
            
            self.cursor.execute(
                """
                SELECT m.*, a.phone_number, a.name, a.username, a.login_cookie 
                FROM messages m
                JOIN accounts a ON m.account_id = a.id
                WHERE m.status = 'pending'
                AND (m.scheduled_time IS NULL OR m.scheduled_time <= ?)
                AND a.status = 'active'
                ORDER BY m.scheduled_time ASC
                LIMIT ?
                """,
                (current_time, limit)
            )
            
            messages = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(message) for message in messages]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting pending messages: {str(e)}")
            return []
    
    def add_campaign(self, name, description=None, area_codes=None, template_id=None, 
                    start_date=None, end_date=None, target_count=0):
        """Add a new campaign to the database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO campaigns (
                    name, description, area_codes, template_id, start_date, end_date,
                    target_count, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (name, description, area_codes, template_id, start_date, end_date, target_count)
            )
            self.conn.commit()
            campaign_id = self.cursor.lastrowid
            logger.info(f"Added new campaign with ID {campaign_id}: {name}")
            return campaign_id
        except sqlite3.Error as e:
            logger.error(f"Error adding campaign: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_campaign(self, campaign_id):
        """Get campaign details from database"""
        try:
            self.cursor.execute(
                "SELECT * FROM campaigns WHERE id=?", 
                (campaign_id,)
            )
            campaign = self.cursor.fetchone()
            if campaign:
                return dict(campaign)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting campaign: {str(e)}")
            return None
    
    def update_campaign(self, campaign_id, **kwargs):
        """Update a campaign in the database"""
        try:
            # Build the SET part of the SQL query dynamically based on provided kwargs
            set_clauses = ["updated_at=CURRENT_TIMESTAMP"]
            params = []
            
            for key, value in kwargs.items():
                set_clauses.append(f"{key}=?")
                params.append(value)
            
            # Add campaign_id to params
            params.append(campaign_id)
            
            # Execute the update query
            self.cursor.execute(
                f"UPDATE campaigns SET {', '.join(set_clauses)} WHERE id=?",
                tuple(params)
            )
            self.conn.commit()
            logger.info(f"Updated campaign with ID {campaign_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating campaign: {str(e)}")
            self.conn.rollback()
            return False
    
    def delete_campaign(self, campaign_id):
        """Delete a campaign from the database"""
        try:
            # Just delete the campaign record
            self.cursor.execute(
                "DELETE FROM campaigns WHERE id=?",
                (campaign_id,)
            )
            self.conn.commit()
            logger.info(f"Deleted campaign with ID {campaign_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting campaign: {str(e)}")
            self.conn.rollback()
            return False
    
    def save_campaign(self, campaign_data):
        """Save a campaign with detailed configuration
        
        Args:
            campaign_data: Dictionary containing campaign configuration
                - name: Campaign name
                - description: Campaign description
                - template_name: Name of the message template to use
                - area_codes: Comma-separated list of area codes
                - start_date: Start date (YYYY-MM-DD)
                - end_date: End date (YYYY-MM-DD)
                - duration: Campaign duration
                - daily_limit: Maximum messages per day
                - messages_per_hour: Messages per hour
                - target_count: Number of targets
                - status: Campaign status
                - message_variations: JSON string of message variations
                - message_delay_min: Minimum delay between messages
                - message_delay_max: Maximum delay between messages
                - start_hour: Hour to start sending (0-23)
                - end_hour: Hour to stop sending (0-23)
                - selected_accounts: JSON string of selected account IDs
                
        Returns:
            Campaign ID if successful, None otherwise
        """
        try:
            # Get template ID if template name is provided
            template_id = None
            if 'template_name' in campaign_data and campaign_data['template_name']:
                # Skip if using uploaded variations
                if campaign_data['template_name'] != "Use uploaded variations":
                    self.cursor.execute(
                        "SELECT id FROM message_templates WHERE name=?", 
                        (campaign_data['template_name'],)
                    )
                    template_result = self.cursor.fetchone()
                    if template_result:
                        template_id = template_result['id']
            
            # Check if campaign exists
            existing_id = None
            if 'name' in campaign_data:
                self.cursor.execute(
                    "SELECT id FROM campaigns WHERE name=?", 
                    (campaign_data['name'],)
                )
                existing = self.cursor.fetchone()
                if existing:
                    existing_id = existing['id']
            
            if existing_id:
                # Update existing campaign
                update_data = {
                    'description': campaign_data.get('description'),
                    'area_codes': campaign_data.get('area_codes'),
                    'template_id': template_id,
                    'start_date': campaign_data.get('start_date'),
                    'end_date': campaign_data.get('end_date'),
                    'target_count': campaign_data.get('target_count', 0),
                    'status': campaign_data.get('status', 'paused'),
                    'message_variations': campaign_data.get('message_variations'),
                    'daily_limit': campaign_data.get('daily_limit'),
                    'messages_per_hour': campaign_data.get('messages_per_hour'),
                    'message_delay_min': campaign_data.get('message_delay_min'),
                    'message_delay_max': campaign_data.get('message_delay_max'),
                    'start_hour': campaign_data.get('start_hour'),
                    'end_hour': campaign_data.get('end_hour'),
                    'selected_accounts': campaign_data.get('selected_accounts'),
                    'duration': campaign_data.get('duration')
                }
                
                # Remove None values
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                # Update the campaign
                self.update_campaign(existing_id, **update_data)
                logger.info(f"Updated existing campaign with ID {existing_id}")
                return existing_id
            else:
                # Insert new campaign
                self.cursor.execute(
                    """
                    INSERT INTO campaigns (
                        name, description, area_codes, template_id, start_date, end_date,
                        target_count, status, created_at, updated_at, message_variations,
                        daily_limit, messages_per_hour, message_delay_min, message_delay_max,
                        start_hour, end_hour, selected_accounts, duration
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 
                              ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        campaign_data.get('name'),
                        campaign_data.get('description'),
                        campaign_data.get('area_codes'),
                        template_id,
                        campaign_data.get('start_date'),
                        campaign_data.get('end_date'),
                        campaign_data.get('target_count', 0),
                        campaign_data.get('status', 'paused'),
                        campaign_data.get('message_variations'),
                        campaign_data.get('daily_limit'),
                        campaign_data.get('messages_per_hour'),
                        campaign_data.get('message_delay_min'),
                        campaign_data.get('message_delay_max'),
                        campaign_data.get('start_hour'),
                        campaign_data.get('end_hour'),
                        campaign_data.get('selected_accounts'),
                        campaign_data.get('duration')
                    )
                )
                self.conn.commit()
                campaign_id = self.cursor.lastrowid
                logger.info(f"Added new campaign with ID {campaign_id}: {campaign_data.get('name')}")
                return campaign_id
                
        except sqlite3.Error as e:
            logger.error(f"Error saving campaign: {str(e)}")
            self.conn.rollback()
            return None
    
    def update_campaign_status(self, campaign_name_or_id, status):
        """Update the status of a campaign
        
        Args:
            campaign_name_or_id: Name or ID of the campaign
            status: New status ('draft', 'active', 'paused', 'completed')
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine if we have a name or ID
            if isinstance(campaign_name_or_id, int) or campaign_name_or_id.isdigit():
                # We have an ID
                campaign_id = int(campaign_name_or_id)
                self.cursor.execute(
                    """
                    UPDATE campaigns SET 
                    status=?, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (status, campaign_id)
                )
            else:
                # We have a name
                self.cursor.execute(
                    """
                    UPDATE campaigns SET 
                    status=?, updated_at=CURRENT_TIMESTAMP
                    WHERE name=?
                    """,
                    (status, campaign_name_or_id)
                )
            
            self.conn.commit()
            logger.info(f"Updated campaign {campaign_name_or_id} status to {status}")
            
            # Log the status change
            log_message = f"Campaign status changed to {status}"
            self._log_campaign_event(campaign_name_or_id, "status_change", log_message)
            
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating campaign status: {str(e)}")
            self.conn.rollback()
            return False
    
    def _log_campaign_event(self, campaign_name_or_id, event_type, message, details=None):
        """Log a campaign event
        
        Args:
            campaign_name_or_id: Name or ID of the campaign
            event_type: Type of event (status_change, message_sent, error, etc.)
            message: Event message
            details: Additional details (JSON string)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get campaign ID if name was provided
            campaign_id = None
            if isinstance(campaign_name_or_id, int) or campaign_name_or_id.isdigit():
                campaign_id = int(campaign_name_or_id)
            else:
                self.cursor.execute(
                    "SELECT id FROM campaigns WHERE name=?", 
                    (campaign_name_or_id,)
                )
                result = self.cursor.fetchone()
                if result:
                    campaign_id = result['id']
            
            if not campaign_id:
                logger.error(f"Campaign not found: {campaign_name_or_id}")
                return False
            
            # Insert the log entry
            self.cursor.execute(
                """
                INSERT INTO campaign_logs (
                    campaign_id, event_type, message, details, timestamp
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (campaign_id, event_type, message, details)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging campaign event: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_campaign_report(self, campaign_id):
        """Get a report of campaign metrics
        
        Args:
            campaign_id: ID of the campaign
            
        Returns:
            Dictionary with campaign metrics
        """
        try:
            # Get basic campaign info
            self.cursor.execute(
                "SELECT * FROM campaigns WHERE id=?", 
                (campaign_id,)
            )
            campaign = self.cursor.fetchone()
            if not campaign:
                return None
            
            # Get message counts by status
            self.cursor.execute(
                """
                SELECT status, COUNT(*) as count FROM campaign_targets
                WHERE campaign_id=?
                GROUP BY status
                """,
                (campaign_id,)
            )
            status_counts = self.cursor.fetchall()
            
            # Process the results
            report = {
                'campaign': dict(campaign),
                'message_counts': {
                    'pending': 0,
                    'sent': 0,
                    'failed': 0,
                    'responded': 0
                },
                'success_rate': 0.0,
                'response_rate': 0.0,
                'completion_percentage': 0.0
            }
            
            # Fill in the counts
            total_messages = 0
            for row in status_counts:
                status = row['status']
                count = row['count']
                report['message_counts'][status] = count
                total_messages += count
            
            # Calculate rates if we have messages
            if total_messages > 0:
                sent_count = report['message_counts']['sent']
                responded_count = report['message_counts']['responded']
                total_processed = sent_count + report['message_counts']['failed']
                
                if total_processed > 0:
                    report['success_rate'] = (sent_count / total_processed) * 100
                
                if sent_count > 0:
                    report['response_rate'] = (responded_count / sent_count) * 100
                
                target_count = campaign['target_count'] or total_messages
                report['completion_percentage'] = (total_processed / target_count) * 100
            
            return report
        except sqlite3.Error as e:
            logger.error(f"Error getting campaign report: {str(e)}")
            return None
    
    def get_campaigns(self, status=None, limit=None, offset=0):
        """Get a list of campaigns from the database"""
        try:
            query = "SELECT * FROM campaigns"
            params = []
            
            # Add WHERE clauses based on parameters
            if status:
                query += " WHERE status=?"
                params.append(status)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            campaigns = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(campaign) for campaign in campaigns]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting campaigns: {str(e)}")
            return []
    
    def add_message_template(self, name, content, variables=None, image_category=None):
        """Add a new message template to the database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO message_templates (
                    name, content, variables, image_category, created_at, updated_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (name, content, variables, image_category)
            )
            self.conn.commit()
            template_id = self.cursor.lastrowid
            logger.info(f"Added new message template with ID {template_id}: {name}")
            return template_id
        except sqlite3.Error as e:
            logger.error(f"Error adding message template: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_message_template(self, template_id):
        """Get message template details from database by ID"""
        try:
            self.cursor.execute(
                "SELECT * FROM message_templates WHERE id=?", 
                (template_id,)
            )
            template = self.cursor.fetchone()
            if template:
                return dict(template)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting message template: {str(e)}")
            return None
            
    def get_message_template_by_name(self, template_name):
        """Get message template details from database by name"""
        try:
            self.cursor.execute(
                "SELECT * FROM message_templates WHERE name=?", 
                (template_name,)
            )
            template = self.cursor.fetchone()
            if template:
                return dict(template)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting message template by name: {str(e)}")
            return None
    
    def update_message_template(self, template_id, **kwargs):
        """Update a message template in the database"""
        try:
            # Build the SET part of the SQL query dynamically based on provided kwargs
            set_clauses = ["updated_at=CURRENT_TIMESTAMP"]
            params = []
            
            for key, value in kwargs.items():
                set_clauses.append(f"{key}=?")
                params.append(value)
            
            # Add template_id to params
            params.append(template_id)
            
            # Execute the update query
            self.cursor.execute(
                f"UPDATE message_templates SET {', '.join(set_clauses)} WHERE id=?",
                tuple(params)
            )
            self.conn.commit()
            logger.info(f"Updated message template with ID {template_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating message template: {str(e)}")
            self.conn.rollback()
            return False
    
    def delete_message_template(self, template_id):
        """Delete a message template from the database"""
        try:
            # Just delete the template record
            self.cursor.execute(
                "DELETE FROM message_templates WHERE id=?",
                (template_id,)
            )
            self.conn.commit()
            logger.info(f"Deleted message template with ID {template_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error deleting message template: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_message_templates(self, limit=None, offset=0):
        """Get a list of message templates from the database"""
        try:
            query = "SELECT * FROM message_templates ORDER BY created_at DESC"
            params = []
            
            # Add LIMIT clause
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            templates = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(template) for template in templates]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting message templates: {str(e)}")
            return []
            
    def add_message_template(self, name, content, variables=None, image_category=None):
        """Add a new message template to the database
        
        Args:
            name: Name of the template
            content: JSON string of message variations
            variables: JSON string of variable names found in the template
            image_category: Category of images to use with this template
            
        Returns:
            ID of the new template or None if an error occurred
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO message_templates (
                    name, content, variables, image_category, created_at, updated_at
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (name, content, variables, image_category)
            )
            self.conn.commit()
            template_id = self.cursor.lastrowid
            logger.info(f"Added new message template with ID {template_id}: {name}")
            return template_id
        except sqlite3.Error as e:
            logger.error(f"Error adding message template: {str(e)}")
            self.conn.rollback()
            return None
    
    def add_voicemail(self, file_path, duration=None, voice_type=None, text_content=None, checksum=None):
        """Add a new voicemail to the database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO voicemails (
                    file_path, duration, type, text_content, checksum, use_count, created_at
                ) VALUES (?, ?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                """,
                (file_path, duration, voice_type, text_content, checksum)
            )
            self.conn.commit()
            voicemail_id = self.cursor.lastrowid
            logger.info(f"Added new voicemail with ID {voicemail_id}: {file_path}")
            return voicemail_id
        except sqlite3.Error as e:
            logger.error(f"Error adding voicemail: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_voicemail(self, voicemail_id):
        """Get voicemail details from database"""
        try:
            self.cursor.execute(
                "SELECT * FROM voicemails WHERE id=?", 
                (voicemail_id,)
            )
            voicemail = self.cursor.fetchone()
            if voicemail:
                return dict(voicemail)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting voicemail: {str(e)}")
            return None
    
    def increment_voicemail_use_count(self, voicemail_id):
        """Increment the use count for a voicemail"""
        try:
            self.cursor.execute(
                "UPDATE voicemails SET use_count = use_count + 1 WHERE id=?",
                (voicemail_id,)
            )
            self.conn.commit()
            logger.info(f"Incremented use count for voicemail with ID {voicemail_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error incrementing voicemail use count: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_voicemails(self, voice_type=None, limit=None, offset=0):
        """Get a list of voicemails from the database"""
        try:
            query = "SELECT * FROM voicemails"
            params = []
            
            # Add WHERE clauses based on parameters
            if voice_type:
                query += " WHERE type=?"
                params.append(voice_type)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            voicemails = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(voicemail) for voicemail in voicemails]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting voicemails: {str(e)}")
            return []
    
    def add_image(self, file_path, category=None, description=None, checksum=None):
        """Add a new image to the database"""
        try:
            self.cursor.execute(
                """
                INSERT INTO images (
                    file_path, category, description, checksum, use_count, created_at
                ) VALUES (?, ?, ?, ?, 0, CURRENT_TIMESTAMP)
                """,
                (file_path, category, description, checksum)
            )
            self.conn.commit()
            image_id = self.cursor.lastrowid
            logger.info(f"Added new image with ID {image_id}: {file_path}")
            return image_id
        except sqlite3.Error as e:
            logger.error(f"Error adding image: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_image(self, image_id):
        """Get image details from database"""
        try:
            self.cursor.execute(
                "SELECT * FROM images WHERE id=?", 
                (image_id,)
            )
            image = self.cursor.fetchone()
            if image:
                return dict(image)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting image: {str(e)}")
            return None
    
    def increment_image_use_count(self, image_id):
        """Increment the use count for an image"""
        try:
            self.cursor.execute(
                "UPDATE images SET use_count = use_count + 1 WHERE id=?",
                (image_id,)
            )
            self.conn.commit()
            logger.info(f"Incremented use count for image with ID {image_id}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error incrementing image use count: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_images(self, category=None, limit=None, offset=0):
        """Get a list of images from the database"""
        try:
            query = "SELECT * FROM images"
            params = []
            
            # Add WHERE clauses based on parameters
            if category:
                query += " WHERE category=?"
                params.append(category)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            # Execute the query
            self.cursor.execute(query, tuple(params))
            images = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(image) for image in images]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting images: {str(e)}")
            return []
    
    def log_health_check(self, account_id, check_type, status, score, details=None):
        """Log a health check for an account"""
        try:
            # Convert details to JSON if it's a dict
            if details and isinstance(details, dict):
                details = json.dumps(details)
            
            self.cursor.execute(
                """
                INSERT INTO health_checks (
                    account_id, check_type, status, score, details, check_date
                ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (account_id, check_type, status, score, details)
            )
            self.conn.commit()
            health_check_id = self.cursor.lastrowid
            
            # Update the account's health score based on the new check
            self._update_account_health_score(account_id)
            
            logger.info(f"Added health check with ID {health_check_id} for account {account_id}")
            return health_check_id
        except sqlite3.Error as e:
            logger.error(f"Error logging health check: {str(e)}")
            self.conn.rollback()
            return None
    
    def _update_account_health_score(self, account_id):
        """Update the health score for an account based on recent checks"""
        try:
            # Get recent health checks (last 7 days)
            self.cursor.execute(
                """
                SELECT AVG(score) as avg_score FROM health_checks
                WHERE account_id = ?
                AND check_date >= datetime('now', '-7 days')
                """,
                (account_id,)
            )
            result = self.cursor.fetchone()
            
            if result and result['avg_score'] is not None:
                health_score = int(result['avg_score'])
                
                # Update the account's health score
                self.cursor.execute(
                    "UPDATE accounts SET health_score = ? WHERE id = ?",
                    (health_score, account_id)
                )
                
                # Update account status based on health score
                status = 'active'
                if health_score < 30:
                    status = 'blocked'
                elif health_score < 60:
                    status = 'suspended'
                
                self.cursor.execute(
                    "UPDATE accounts SET status = ? WHERE id = ? AND status != 'deleted'",
                    (status, account_id)
                )
                
                self.conn.commit()
                logger.info(f"Updated health score for account {account_id} to {health_score}")
                return True
        except sqlite3.Error as e:
            logger.error(f"Error updating account health score: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_health_checks(self, account_id, days=7, limit=None):
        """Get recent health checks for an account"""
        try:
            query = """
                SELECT * FROM health_checks
                WHERE account_id = ?
                AND check_date >= datetime('now', ? || ' days')
                ORDER BY check_date DESC
            """
            params = [account_id, f"-{days}"]
            
            # Add LIMIT clause
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            self.cursor.execute(query, tuple(params))
            checks = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(check) for check in checks]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting health checks: {str(e)}")
            return []
    
    def log_ip_rotation(self, old_ip, new_ip, success, duration, device_id=None, notes=None):
        """Log an IP rotation event"""
        try:
            self.cursor.execute(
                """
                INSERT INTO ip_rotations (
                    old_ip, new_ip, success, duration, device_id, notes, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (old_ip, new_ip, success, duration, device_id, notes)
            )
            self.conn.commit()
            rotation_id = self.cursor.lastrowid
            logger.info(f"Logged IP rotation with ID {rotation_id}: {old_ip} -> {new_ip}")
            return rotation_id
        except sqlite3.Error as e:
            logger.error(f"Error logging IP rotation: {str(e)}")
            self.conn.rollback()
            return None
    
    def get_ip_rotations(self, limit=None, offset=0):
        """Get a list of IP rotation events"""
        try:
            query = "SELECT * FROM ip_rotations ORDER BY timestamp DESC"
            params = []
            
            # Add LIMIT clause
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            self.cursor.execute(query, tuple(params))
            rotations = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(rotation) for rotation in rotations]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting IP rotations: {str(e)}")
            return []
    
    def log_error(self, error_type, component=None, details=None, account_id=None):
        """Log an error in the database"""
        try:
            # Convert details to JSON if it's a dict
            if details and isinstance(details, dict):
                details = json.dumps(details)
            
            self.cursor.execute(
                """
                INSERT INTO errors (
                    error_type, component, details, account_id, timestamp
                ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (error_type, component, details, account_id)
            )
            self.conn.commit()
            error_id = self.cursor.lastrowid
            logger.info(f"Logged error with ID {error_id}: {error_type}")
            return error_id
        except sqlite3.Error as e:
            logger.error(f"Error logging error: {str(e)}")
            self.conn.rollback()
            return None
    
    def resolve_error(self, error_id, resolution):
        """Mark an error as resolved"""
        try:
            self.cursor.execute(
                """
                UPDATE errors SET resolved=1, resolution=? WHERE id=?
                """,
                (resolution, error_id)
            )
            self.conn.commit()
            logger.info(f"Marked error with ID {error_id} as resolved")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error resolving error: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_errors(self, resolved=None, limit=None, offset=0):
        """Get a list of errors"""
        try:
            query = "SELECT * FROM errors"
            params = []
            
            # Add WHERE clauses based on parameters
            if resolved is not None:
                query += " WHERE resolved=?"
                params.append(1 if resolved else 0)
            
            # Add ORDER BY and LIMIT clauses
            query += " ORDER BY timestamp DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            self.cursor.execute(query, tuple(params))
            errors = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(error) for error in errors]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting errors: {str(e)}")
            return []
    
    def update_setting(self, category, key, value):
        """Update a setting in the database"""
        try:
            # Try to update the existing setting
            self.cursor.execute(
                """
                UPDATE settings SET value=? WHERE category=? AND key=?
                """,
                (value, category, key)
            )
            
            # If no rows were affected, insert a new setting
            if self.cursor.rowcount == 0:
                self.cursor.execute(
                    """
                    INSERT INTO settings (category, key, value) VALUES (?, ?, ?)
                    """,
                    (category, key, value)
                )
            
            self.conn.commit()
            logger.info(f"Updated setting {category}.{key} = {value}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating setting: {str(e)}")
            self.conn.rollback()
            return False
    
    def get_setting_value(self, category, key, default=None):
        """Get a setting value from the database"""
        try:
            self.cursor.execute(
                """
                SELECT value FROM settings WHERE category=? AND key=?
                """,
                (category, key)
            )
            result = self.cursor.fetchone()
            
            if result:
                return result['value']
            return default
        except sqlite3.Error as e:
            logger.error(f"Error getting setting: {str(e)}")
            return default
    
    def get_settings(self, category=None):
        """Get all settings, optionally filtered by category"""
        try:
            query = "SELECT * FROM settings"
            params = []
            
            if category:
                query += " WHERE category=?"
                params.append(category)
            
            query += " ORDER BY category, key"
            
            self.cursor.execute(query, tuple(params))
            settings = self.cursor.fetchall()
            
            # Convert to list of dicts
            result = [dict(setting) for setting in settings]
            return result
        except sqlite3.Error as e:
            logger.error(f"Error getting settings: {str(e)}")
            return []
    
    def get_dashboard_stats(self):
        """Get statistics for the dashboard"""
        try:
            stats = {}
            
            # Total accounts
            self.cursor.execute("SELECT COUNT(*) as count FROM accounts")
            stats['total_accounts'] = self.cursor.fetchone()['count']
            
            # Active accounts
            self.cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE status='active'")
            stats['active_accounts'] = self.cursor.fetchone()['count']
            
            # Messages sent
            self.cursor.execute("SELECT COUNT(*) as count FROM messages WHERE status='sent'")
            stats['messages_sent'] = self.cursor.fetchone()['count']
            
            # Success rate
            self.cursor.execute("""
                SELECT COALESCE(
                    (SELECT COUNT(*) FROM messages WHERE status='sent') * 100.0 / NULLIF(
                        (SELECT COUNT(*) FROM messages WHERE status IN ('sent', 'failed')), 0
                    ), 0
                ) as rate
            """)
            stats['success_rate'] = round(self.cursor.fetchone()['rate'], 1)
            
            # Account health stats
            self.cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE health_score >= 80")
            stats['healthy_accounts'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE health_score >= 50 AND health_score < 80")
            stats['warning_accounts'] = self.cursor.fetchone()['count']
            
            self.cursor.execute("SELECT COUNT(*) as count FROM accounts WHERE health_score < 50")
            stats['critical_accounts'] = self.cursor.fetchone()['count']
            
            # Recent IP rotations (success rate)
            self.cursor.execute("""
                SELECT COALESCE(
                    (SELECT COUNT(*) FROM ip_rotations WHERE success=1 AND timestamp >= datetime('now', '-1 day')) * 100.0 / NULLIF(
                        (SELECT COUNT(*) FROM ip_rotations WHERE timestamp >= datetime('now', '-1 day')), 0
                    ), 0
                ) as rate
            """)
            stats['ip_rotation_success_rate'] = round(self.cursor.fetchone()['rate'], 1)
            
            # Recent activity
            self.cursor.execute("""
                SELECT COUNT(*) as count FROM messages 
                WHERE sent_time >= datetime('now', '-1 day')
            """)
            stats['messages_last_24h'] = self.cursor.fetchone()['count']
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting dashboard stats: {str(e)}")
            return {
                'total_accounts': 0,
                'active_accounts': 0,
                'messages_sent': 0,
                'success_rate': 0,
                'healthy_accounts': 0,
                'warning_accounts': 0,
                'critical_accounts': 0,
                'ip_rotation_success_rate': 0,
                'messages_last_24h': 0
            }
    
    def backup_database(self, backup_path=None):
        """Create a backup of the database"""
        if not backup_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"backup_{timestamp}.db"
        
        try:
            # Close the current connection
            self.close()
            
            # Copy the database file
            import shutil
            shutil.copy2(self.database_path, backup_path)
            
            # Reconnect to the database
            self._connect()
            
            logger.info(f"Database backed up to {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error backing up database: {str(e)}")
            
            # Try to reconnect to the database
            self._connect()
            
            return None
    
    def restore_database(self, backup_path):
        """Restore the database from a backup"""
        if not os.path.exists(backup_path):
            logger.error(f"Backup file not found: {backup_path}")
            return False
        
        try:
            # Close the current connection
            self.close()
            
            # Replace the database file
            import shutil
            shutil.copy2(backup_path, self.database_path)
            
            # Reconnect to the database
            self._connect()
            
            logger.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {str(e)}")
            
            # Try to reconnect to the database
            self._connect()
            
            return False
    
    def export_accounts_to_csv(self, csv_path):
        """Export accounts to a CSV file"""
        try:
            self.cursor.execute("""
                SELECT 
                    phone_number, name, username, area_code, email, password, status,
                    health_score, created_at, last_used
                FROM accounts
                ORDER BY created_at DESC
            """)
            accounts = self.cursor.fetchall()
            
            if not accounts:
                logger.error("No accounts to export")
                return False
            
            # Write to CSV
            import csv
            with open(csv_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                
                # Write header
                writer.writerow([
                    'Phone Number', 'Name', 'Username', 'Area Code', 'Email', 'Password',
                    'Status', 'Health Score', 'Created At', 'Last Used'
                ])
                
                # Write accounts
                for account in accounts:
                    writer.writerow([
                        account['phone_number'],
                        account['name'],
                        account['username'],
                        account['area_code'],
                        account['email'],
                        account['password'],
                        account['status'],
                        account['health_score'],
                        account['created_at'],
                        account['last_used']
                    ])
            
            logger.info(f"Exported {len(accounts)} accounts to {csv_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting accounts to CSV: {str(e)}")
            return False
    
    def import_accounts_from_csv(self, csv_path):
        """Import accounts from a CSV file"""
        if not os.path.exists(csv_path):
            logger.error(f"CSV file not found: {csv_path}")
            return False
        
        try:
            import csv
            accounts_added = 0
            accounts_updated = 0
            
            with open(csv_path, 'r', newline='') as csvfile:
                reader = csv.reader(csvfile)
                
                # Skip header
                next(reader, None)
                
                for row in reader:
                    if len(row) < 6:  # Need at least phone_number, name, password
                        continue
                    
                    phone_number = row[0]
                    name = row[1]
                    username = row[2] if len(row) > 2 and row[2] else None
                    area_code = row[3] if len(row) > 3 and row[3] else None
                    email = row[4] if len(row) > 4 and row[4] else None
                    password = row[5]
                    status = row[6] if len(row) > 6 and row[6] else 'active'
                    
                    # Check if account exists
                    self.cursor.execute(
                        "SELECT id FROM accounts WHERE phone_number=?",
                        (phone_number,)
                    )
                    existing = self.cursor.fetchone()
                    
                    if existing:
                        # Update existing account
                        self.cursor.execute(
                            """
                            UPDATE accounts SET 
                            name=?, username=?, area_code=?, email=?, password=?, status=?
                            WHERE phone_number=?
                            """,
                            (name, username, area_code, email, password, status, phone_number)
                        )
                        accounts_updated += 1
                    else:
                        # Add new account
                        self.cursor.execute(
                            """
                            INSERT INTO accounts (
                                phone_number, name, username, area_code, email, password, status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                            """,
                            (phone_number, name, username, area_code, email, password, status)
                        )
                        accounts_added += 1
            
            self.conn.commit()
            logger.info(f"Imported {accounts_added} new accounts and updated {accounts_updated} existing accounts from {csv_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing accounts from CSV: {str(e)}")
            self.conn.rollback()
            return False
    
    def generate_random_name(self):
        """Generate a random name for account creation"""
        # List of first names
        first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen",
            "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Donald", "Steven", "Paul", "Andrew", "Joshua",
            "Michelle", "Amanda", "Kimberly", "Melissa", "Stephanie", "Lisa", "Nicole", "Angela", "Helen", "Donna",
            "Brian", "Kevin", "Jason", "Jeffrey", "Ryan", "Jacob", "Gary", "Nicholas", "Eric", "Jonathan",
            "Sandra", "Ashley", "Katie", "Dorothy", "Olivia", "Emma", "Ava", "Emily", "Sophia", "Isabella"
        ]
        
        # List of last names
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
            "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson",
            "Clark", "Rodriguez", "Lewis", "Lee", "Walker", "Hall", "Allen", "Young", "Hernandez", "King",
            "Wright", "Lopez", "Hill", "Scott", "Green", "Adams", "Baker", "Gonzalez", "Nelson", "Carter",
            "Mitchell", "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans", "Edwards", "Collins"
        ]
        
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        
        return f"{first_name} {last_name}"
    
    def generate_random_email(self, name=None):
        """Generate a random email for account creation"""
        if not name:
            name = self.generate_random_name()
        
        # Remove spaces and convert to lowercase
        name_part = name.lower().replace(' ', '.')
        
        # Add some randomness
        random_part = ''.join(random.choices(string.digits, k=4))
        
        # List of common email domains
        domains = [
            "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
            "aol.com", "protonmail.com", "mail.com", "zoho.com", "yandex.com"
        ]
        
        domain = random.choice(domains)
        
        return f"{name_part}{random_part}@{domain}"
    
    def generate_random_password(self, length=12):
        """Generate a secure random password"""
        # Ensure we have at least one of each required character type
        uppercase = random.choice(string.ascii_uppercase)
        lowercase = random.choice(string.ascii_lowercase)
        digit = random.choice(string.digits)
        special = random.choice('!@#$%^&*()_-+=')
        
        # Fill the rest with a mix of character types
        rest_length = length - 4
        rest = ''.join(random.choices(
            string.ascii_uppercase + string.ascii_lowercase + string.digits + '!@#$%^&*()_-+=',
            k=rest_length
        ))
        
        # Combine and shuffle
        password = uppercase + lowercase + digit + special + rest
        password_list = list(password)
        random.shuffle(password_list)
        
        return ''.join(password_list)
    
    def save_target_numbers(self, list_name, phone_numbers, description=None):
        """Save a list of target phone numbers to the database
        
        Args:
            list_name: Name for the list of phone numbers
            phone_numbers: List of phone numbers to save
            description: Optional description for the list
            
        Returns:
            Number of phone numbers saved
        """
        try:
            # Create a new target list
            self.cursor.execute(
                """
                INSERT INTO target_lists (name, description, count, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (list_name, description, len(phone_numbers))
            )
            
            list_id = self.cursor.lastrowid
            logger.info(f"Created target list '{list_name}' with ID {list_id}")
            
            # Insert all phone numbers
            for phone in phone_numbers:
                self.cursor.execute(
                    """
                    INSERT INTO target_numbers (list_id, phone_number)
                    VALUES (?, ?)
                    """,
                    (list_id, phone)
                )
            
            self.conn.commit()
            logger.info(f"Added {len(phone_numbers)} phone numbers to list '{list_name}'")
            return len(phone_numbers)
            
        except sqlite3.Error as e:
            logger.error(f"Error saving target numbers: {str(e)}")
            self.conn.rollback()
            return 0
    
    def get_target_lists(self):
        """Get all target phone number lists
        
        Returns:
            List of target list dictionaries
        """
        try:
            self.cursor.execute("SELECT * FROM target_lists ORDER BY created_at DESC")
            lists = self.cursor.fetchall()
            return [dict(l) for l in lists]
        except sqlite3.Error as e:
            logger.error(f"Error getting target lists: {str(e)}")
            return []
    
    def get_target_numbers(self, list_id=None, limit=None, offset=0, status='active'):
        """Get target phone numbers
        
        Args:
            list_id: Optional ID of the target list to filter by
            limit: Optional maximum number of numbers to return
            offset: Optional offset for pagination
            status: Status of numbers to retrieve (default: 'active')
            
        Returns:
            List of target number dictionaries
        """
        try:
            query = "SELECT * FROM target_numbers"
            params = []
            
            # Add WHERE clauses
            where_clauses = []
            if list_id:
                where_clauses.append("list_id=?")
                params.append(list_id)
            if status:
                where_clauses.append("status=?")
                params.append(status)
                
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
                
            # Add ORDER BY and LIMIT
            query += " ORDER BY created_at DESC"
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
            self.cursor.execute(query, tuple(params))
            numbers = self.cursor.fetchall()
            return [dict(n) for n in numbers]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting target numbers: {str(e)}")
            return []
    
    def update_target_number_status(self, number_id, status):
        """Update the status of a target phone number
        
        Args:
            number_id: ID of the target number to update
            status: New status for the number (active, used, blocked, invalid)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                UPDATE target_numbers SET 
                status=?, last_used=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (status, number_id)
            )
            self.conn.commit()
            logger.info(f"Updated target number {number_id} status to {status}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error updating target number status: {str(e)}")
            self.conn.rollback()
            return False
    
    def add_campaign_targets(self, campaign_id, target_numbers):
        """Add target numbers to a campaign
        
        Args:
            campaign_id: ID of the campaign
            target_numbers: List of phone numbers to add to the campaign
            
        Returns:
            Number of targets added
        """
        try:
            count = 0
            for number in target_numbers:
                self.cursor.execute(
                    """
                    INSERT INTO campaign_targets (campaign_id, target_number)
                    VALUES (?, ?)
                    """,
                    (campaign_id, number)
                )
                count += 1
                
            self.conn.commit()
            logger.info(f"Added {count} targets to campaign {campaign_id}")
            
            # Update the campaign target count
            self.cursor.execute(
                """
                UPDATE campaigns SET 
                target_count=target_count+?, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (count, campaign_id)
            )
            self.conn.commit()
            
            return count
        except sqlite3.Error as e:
            logger.error(f"Error adding campaign targets: {str(e)}")
            self.conn.rollback()
            return 0
    
    def get_campaign_targets(self, campaign_id, status=None, limit=None, offset=0):
        """Get targets for a campaign
        
        Args:
            campaign_id: ID of the campaign
            status: Optional status to filter by
            limit: Optional maximum number of targets to return
            offset: Optional offset for pagination
            
        Returns:
            List of campaign target dictionaries
        """
        try:
            query = "SELECT * FROM campaign_targets WHERE campaign_id=?"
            params = [campaign_id]
            
            if status:
                query += " AND status=?"
                params.append(status)
                
            query += " ORDER BY id"
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
            self.cursor.execute(query, tuple(params))
            targets = self.cursor.fetchall()
            return [dict(t) for t in targets]
            
        except sqlite3.Error as e:
            logger.error(f"Error getting campaign targets: {str(e)}")
            return []
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Database connection closed")


# Singleton instance
_database_instance = None

def get_database():
    """Get the singleton database instance"""
    global _database_instance
    if _database_instance is None:
        _database_instance = Database()
    return _database_instance