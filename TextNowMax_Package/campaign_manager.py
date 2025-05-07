"""
Campaign Manager for ProgressGhostCreator

This module handles the creation, management, and execution of messaging campaigns.
It includes functionality for:
- Scheduling campaigns with specific active hours (8am-8pm by default)
- Distributing messages across multiple accounts
- Implementing rate limits and throttling to avoid detection
- Tracking campaign progress and performance
- Managing opt-outs and compliance
"""

import os
import sqlite3
import random
import time
import json
import threading
import queue
import logging
import datetime
from typing import List, Dict, Tuple, Optional, Union, Any, Callable

# Import local modules
from message_manager import get_message_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("campaign_manager.log"),
        logging.StreamHandler()
    ]
)

class Campaign:
    """Class representing a messaging campaign"""
    
    def __init__(self, 
                name: str,
                description: str = "",
                active_hours: Tuple[int, int] = (8, 20),
                active_days: List[int] = None,  # 0 = Monday, 6 = Sunday
                message_categories: List[str] = None,
                distribution_pattern: str = "even",
                max_per_account_per_day: int = 100,
                max_per_account_per_hour: int = 15,
                min_delay_seconds: int = 10,
                max_delay_seconds: int = 60,
                campaign_id: Optional[int] = None):
        """
        Initialize a campaign
        
        Args:
            name: Name of the campaign
            description: Campaign description
            active_hours: Tuple of (start_hour, end_hour) for active hours (0-23)
            active_days: List of active days (0 = Monday, 6 = Sunday)
            message_categories: List of message categories to use
            distribution_pattern: How to distribute messages ('even', 'peak', 'random')
            max_per_account_per_day: Maximum messages per account per day
            max_per_account_per_hour: Maximum messages per account per hour
            min_delay_seconds: Minimum delay between messages from same account
            max_delay_seconds: Maximum delay between messages from same account
            campaign_id: Optional ID for existing campaign
        """
        self.name = name
        self.description = description
        self.active_hours = active_hours
        self.active_days = active_days or list(range(7))  # Default to all days
        self.message_categories = message_categories
        self.distribution_pattern = distribution_pattern
        self.max_per_account_per_day = max_per_account_per_day
        self.max_per_account_per_hour = max_per_account_per_hour
        self.min_delay_seconds = min_delay_seconds
        self.max_delay_seconds = max_delay_seconds
        self.id = campaign_id
        
        # Runtime state
        self.is_running = False
        self.is_paused = False
        self.stats = {
            'messages_sent': 0,
            'messages_total': 0,
            'start_time': None,
            'accounts': {},
            'hourly_stats': {}
        }


class CampaignManager:
    """Manager class for campaigns"""
    
    def __init__(self, db_path="campaigns.db"):
        """Initialize the campaign manager"""
        self.db_path = db_path
        self._connect_database()
        
        self.message_manager = get_message_manager()
        
        self.active_campaigns = {}
        self.campaign_threads = {}
        self.campaign_queues = {}
        self.stop_events = {}
        
        # Load any campaigns that were running before
        self._load_campaigns()
    
    def _connect_database(self) -> None:
        """Connect to the campaigns database"""
        try:
            # Create database if it doesn't exist
            if not os.path.exists(self.db_path):
                self.conn = sqlite3.connect(self.db_path)
                self._create_tables()
            else:
                self.conn = sqlite3.connect(self.db_path)
            
            # Enable foreign keys
            self.conn.execute("PRAGMA foreign_keys = ON")
            
            logging.info(f"Connected to campaigns database at {self.db_path}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def _create_tables(self) -> None:
        """Create necessary tables in the database"""
        cursor = self.conn.cursor()
        
        # Campaigns table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            active_hours TEXT,
            active_days TEXT,
            message_categories TEXT,
            distribution_pattern TEXT DEFAULT 'even',
            max_per_account_per_day INTEGER DEFAULT 100,
            max_per_account_per_hour INTEGER DEFAULT 15,
            min_delay_seconds INTEGER DEFAULT 10,
            max_delay_seconds INTEGER DEFAULT 60,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            target_count INTEGER DEFAULT 0,
            completed_count INTEGER DEFAULT 0
        )
        ''')
        
        # Campaign accounts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            total_sent INTEGER DEFAULT 0,
            last_sent TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        ''')
        
        # Campaign schedule table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            schedule_type TEXT NOT NULL,
            schedule_data TEXT NOT NULL,
            start_date TEXT,
            end_date TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        ''')
        
        # Campaign recipients table (for fixed recipient lists)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_recipients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            phone_number TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP,
            account_id INTEGER,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        ''')
        
        # Opt-out table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS opt_outs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE NOT NULL,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            campaign_id INTEGER,
            account_id INTEGER,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_accounts ON campaign_accounts (campaign_id, account_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_campaign_recipients ON campaign_recipients (campaign_id, phone_number)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_opt_outs ON opt_outs (phone_number)')
        
        self.conn.commit()
        logging.info("Created campaign database tables")
    
    def _load_campaigns(self) -> None:
        """Load campaigns from the database"""
        cursor = self.conn.cursor()
        
        # Get all active campaigns
        cursor.execute("SELECT * FROM campaigns WHERE status = 'active'")
        active_campaigns = cursor.fetchall()
        
        for campaign_data in active_campaigns:
            # Create campaign object
            campaign = self._create_campaign_from_data(campaign_data)
            
            # Add to active campaigns
            self.active_campaigns[campaign.id] = campaign
    
    def _create_campaign_from_data(self, campaign_data) -> Campaign:
        """Create a Campaign object from database row"""
        # Parse JSON fields
        active_hours = json.loads(campaign_data[3]) if campaign_data[3] else (8, 20)
        active_days = json.loads(campaign_data[4]) if campaign_data[4] else list(range(7))
        message_categories = json.loads(campaign_data[5]) if campaign_data[5] else None
        
        # Create campaign object
        return Campaign(
            name=campaign_data[1],
            description=campaign_data[2],
            active_hours=active_hours,
            active_days=active_days,
            message_categories=message_categories,
            distribution_pattern=campaign_data[6],
            max_per_account_per_day=campaign_data[7],
            max_per_account_per_hour=campaign_data[8],
            min_delay_seconds=campaign_data[9],
            max_delay_seconds=campaign_data[10],
            campaign_id=campaign_data[0]
        )
    
    def create_campaign(self, campaign: Campaign) -> int:
        """
        Create a new campaign in the database
        
        Args:
            campaign: Campaign object
            
        Returns:
            Campaign ID
        """
        cursor = self.conn.cursor()
        
        # Convert lists/tuples to JSON strings
        active_hours_json = json.dumps(campaign.active_hours)
        active_days_json = json.dumps(campaign.active_days)
        message_categories_json = json.dumps(campaign.message_categories) if campaign.message_categories else None
        
        # Insert campaign
        cursor.execute('''
        INSERT INTO campaigns (
            name, description, active_hours, active_days, message_categories,
            distribution_pattern, max_per_account_per_day, max_per_account_per_hour,
            min_delay_seconds, max_delay_seconds, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'draft')
        ''', (
            campaign.name, campaign.description, active_hours_json, active_days_json,
            message_categories_json, campaign.distribution_pattern,
            campaign.max_per_account_per_day, campaign.max_per_account_per_hour,
            campaign.min_delay_seconds, campaign.max_delay_seconds
        ))
        
        self.conn.commit()
        
        # Get the new campaign ID
        campaign_id = cursor.lastrowid
        campaign.id = campaign_id
        
        logging.info(f"Created new campaign: {campaign.name} (ID: {campaign_id})")
        return campaign_id
    
    def update_campaign(self, campaign: Campaign) -> bool:
        """
        Update an existing campaign
        
        Args:
            campaign: Campaign object with updated values
            
        Returns:
            Success boolean
        """
        if not campaign.id:
            logging.error("Cannot update campaign without an ID")
            return False
        
        cursor = self.conn.cursor()
        
        # Convert lists/tuples to JSON strings
        active_hours_json = json.dumps(campaign.active_hours)
        active_days_json = json.dumps(campaign.active_days)
        message_categories_json = json.dumps(campaign.message_categories) if campaign.message_categories else None
        
        # Update campaign
        cursor.execute('''
        UPDATE campaigns SET
            name = ?,
            description = ?,
            active_hours = ?,
            active_days = ?,
            message_categories = ?,
            distribution_pattern = ?,
            max_per_account_per_day = ?,
            max_per_account_per_hour = ?,
            min_delay_seconds = ?,
            max_delay_seconds = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        ''', (
            campaign.name, campaign.description, active_hours_json, active_days_json,
            message_categories_json, campaign.distribution_pattern,
            campaign.max_per_account_per_day, campaign.max_per_account_per_hour,
            campaign.min_delay_seconds, campaign.max_delay_seconds,
            campaign.id
        ))
        
        self.conn.commit()
        
        # Update active campaign if it exists
        if campaign.id in self.active_campaigns:
            self.active_campaigns[campaign.id] = campaign
        
        logging.info(f"Updated campaign: {campaign.name} (ID: {campaign.id})")
        return True
    
    def get_campaign(self, campaign_id: int) -> Optional[Campaign]:
        """
        Get a campaign by ID
        
        Args:
            campaign_id: The campaign ID
            
        Returns:
            Campaign object or None if not found
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
        campaign_data = cursor.fetchone()
        
        if not campaign_data:
            return None
        
        return self._create_campaign_from_data(campaign_data)
    
    def get_all_campaigns(self, status: Optional[str] = None) -> List[Campaign]:
        """
        Get all campaigns, optionally filtered by status
        
        Args:
            status: Optional status filter ('draft', 'active', 'paused', 'completed')
            
        Returns:
            List of Campaign objects
        """
        cursor = self.conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM campaigns WHERE status = ?", (status,))
        else:
            cursor.execute("SELECT * FROM campaigns")
            
        campaign_data = cursor.fetchall()
        
        return [self._create_campaign_from_data(data) for data in campaign_data]
    
    def add_accounts_to_campaign(self, campaign_id: int, account_ids: List[int]) -> int:
        """
        Add accounts to a campaign
        
        Args:
            campaign_id: The campaign ID
            account_ids: List of account IDs to add
            
        Returns:
            Number of accounts added
        """
        cursor = self.conn.cursor()
        added_count = 0
        
        for account_id in account_ids:
            # Check if account is already in the campaign
            cursor.execute(
                "SELECT id FROM campaign_accounts WHERE campaign_id = ? AND account_id = ?",
                (campaign_id, account_id)
            )
            
            if not cursor.fetchone():
                # Add account to campaign
                cursor.execute(
                    "INSERT INTO campaign_accounts (campaign_id, account_id) VALUES (?, ?)",
                    (campaign_id, account_id)
                )
                added_count += 1
        
        self.conn.commit()
        
        logging.info(f"Added {added_count} accounts to campaign {campaign_id}")
        return added_count
    
    def remove_account_from_campaign(self, campaign_id: int, account_id: int) -> bool:
        """
        Remove an account from a campaign
        
        Args:
            campaign_id: The campaign ID
            account_id: The account ID to remove
            
        Returns:
            Success boolean
        """
        cursor = self.conn.cursor()
        
        cursor.execute(
            "DELETE FROM campaign_accounts WHERE campaign_id = ? AND account_id = ?",
            (campaign_id, account_id)
        )
        
        self.conn.commit()
        
        logging.info(f"Removed account {account_id} from campaign {campaign_id}")
        return cursor.rowcount > 0
    
    def get_campaign_accounts(self, campaign_id: int, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        Get accounts assigned to a campaign
        
        Args:
            campaign_id: The campaign ID
            active_only: Only return active accounts
            
        Returns:
            List of dictionaries with account info
        """
        cursor = self.conn.cursor()
        
        query = """
        SELECT 
            ca.account_id,
            ca.status,
            ca.total_sent,
            ca.last_sent
        FROM 
            campaign_accounts ca
        WHERE 
            ca.campaign_id = ?
        """
        
        if active_only:
            query += " AND ca.status = 'active'"
            
        cursor.execute(query, (campaign_id,))
        results = cursor.fetchall()
        
        accounts = []
        for row in results:
            accounts.append({
                'account_id': row[0],
                'status': row[1],
                'total_sent': row[2],
                'last_sent': row[3]
            })
        
        return accounts
    
    def set_campaign_target(self, campaign_id: int, target_count: int) -> bool:
        """
        Set the target message count for a campaign
        
        Args:
            campaign_id: The campaign ID
            target_count: Target number of messages to send
            
        Returns:
            Success boolean
        """
        cursor = self.conn.cursor()
        
        cursor.execute(
            "UPDATE campaigns SET target_count = ? WHERE id = ?",
            (target_count, campaign_id)
        )
        
        self.conn.commit()
        
        logging.info(f"Set target of {target_count} messages for campaign {campaign_id}")
        return cursor.rowcount > 0
    
    def start_campaign(self, campaign_id: int, target_count: Optional[int] = None) -> bool:
        """
        Start a campaign
        
        Args:
            campaign_id: The campaign ID
            target_count: Optional target message count to set
            
        Returns:
            Success boolean
        """
        # Get the campaign
        campaign = self.get_campaign(campaign_id)
        if not campaign:
            logging.error(f"Campaign {campaign_id} not found")
            return False
        
        # Check if campaign is already running
        if campaign_id in self.active_campaigns and self.active_campaigns[campaign_id].is_running:
            logging.warning(f"Campaign {campaign_id} is already running")
            return False
        
        # Set target count if provided
        if target_count is not None:
            self.set_campaign_target(campaign_id, target_count)
        
        # Update campaign status in database
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE campaigns SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        self.conn.commit()
        
        # Add to active campaigns
        campaign.is_running = True
        campaign.is_paused = False
        campaign.stats['start_time'] = datetime.datetime.now()
        self.active_campaigns[campaign_id] = campaign
        
        # Create a stop event for this campaign
        self.stop_events[campaign_id] = threading.Event()
        
        # Start the campaign thread
        self._start_campaign_thread(campaign_id)
        
        logging.info(f"Started campaign: {campaign.name} (ID: {campaign_id})")
        return True
    
    def pause_campaign(self, campaign_id: int) -> bool:
        """
        Pause a running campaign
        
        Args:
            campaign_id: The campaign ID
            
        Returns:
            Success boolean
        """
        if campaign_id not in self.active_campaigns or not self.active_campaigns[campaign_id].is_running:
            logging.warning(f"Campaign {campaign_id} is not running")
            return False
        
        # Update campaign status in database
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE campaigns SET status = 'paused', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        self.conn.commit()
        
        # Update campaign state
        self.active_campaigns[campaign_id].is_paused = True
        
        logging.info(f"Paused campaign: {self.active_campaigns[campaign_id].name} (ID: {campaign_id})")
        return True
    
    def resume_campaign(self, campaign_id: int) -> bool:
        """
        Resume a paused campaign
        
        Args:
            campaign_id: The campaign ID
            
        Returns:
            Success boolean
        """
        if campaign_id not in self.active_campaigns:
            logging.warning(f"Campaign {campaign_id} is not active")
            return False
        
        if not self.active_campaigns[campaign_id].is_paused:
            logging.warning(f"Campaign {campaign_id} is not paused")
            return False
        
        # Update campaign status in database
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE campaigns SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        self.conn.commit()
        
        # Update campaign state
        self.active_campaigns[campaign_id].is_paused = False
        
        logging.info(f"Resumed campaign: {self.active_campaigns[campaign_id].name} (ID: {campaign_id})")
        return True
    
    def stop_campaign(self, campaign_id: int) -> bool:
        """
        Stop a running campaign
        
        Args:
            campaign_id: The campaign ID
            
        Returns:
            Success boolean
        """
        if campaign_id not in self.active_campaigns:
            logging.warning(f"Campaign {campaign_id} is not active")
            return False
        
        # Set the stop event to signal the thread to exit
        if campaign_id in self.stop_events:
            self.stop_events[campaign_id].set()
        
        # Wait for the thread to exit (with timeout)
        if campaign_id in self.campaign_threads and self.campaign_threads[campaign_id].is_alive():
            self.campaign_threads[campaign_id].join(timeout=5)
        
        # Update campaign status in database
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE campaigns SET status = 'stopped', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (campaign_id,)
        )
        self.conn.commit()
        
        # Remove from active campaigns
        if campaign_id in self.active_campaigns:
            del self.active_campaigns[campaign_id]
        
        # Clean up resources
        if campaign_id in self.stop_events:
            del self.stop_events[campaign_id]
        
        if campaign_id in self.campaign_threads:
            del self.campaign_threads[campaign_id]
        
        if campaign_id in self.campaign_queues:
            del self.campaign_queues[campaign_id]
        
        logging.info(f"Stopped campaign: {campaign_id}")
        return True
    
    def add_opt_out(self, phone_number: str, campaign_id: Optional[int] = None, account_id: Optional[int] = None, reason: Optional[str] = None) -> bool:
        """
        Add a phone number to the opt-out list
        
        Args:
            phone_number: The phone number to opt out
            campaign_id: Optional campaign ID
            account_id: Optional account ID
            reason: Optional reason for opt-out
            
        Returns:
            Success boolean
        """
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO opt_outs (phone_number, campaign_id, account_id, reason) VALUES (?, ?, ?, ?)",
                (phone_number, campaign_id, account_id, reason)
            )
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Failed to add opt-out: {str(e)}")
            return False
    
    def is_opted_out(self, phone_number: str) -> bool:
        """
        Check if a phone number is opted out
        
        Args:
            phone_number: The phone number to check
            
        Returns:
            True if opted out, False otherwise
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT id FROM opt_outs WHERE phone_number = ?", (phone_number,))
        return cursor.fetchone() is not None
    
    def get_campaign_stats(self, campaign_id: int) -> Dict[str, Any]:
        """
        Get statistics for a campaign
        
        Args:
            campaign_id: The campaign ID
            
        Returns:
            Dictionary with campaign statistics
        """
        cursor = self.conn.cursor()
        
        # Get basic campaign info
        cursor.execute("""
        SELECT name, status, target_count, completed_count, created_at 
        FROM campaigns 
        WHERE id = ?
        """, (campaign_id,))
        
        campaign_info = cursor.fetchone()
        if not campaign_info:
            return None
        
        # Get account stats
        cursor.execute("""
        SELECT COUNT(*), SUM(total_sent) 
        FROM campaign_accounts 
        WHERE campaign_id = ?
        """, (campaign_id,))
        
        account_stats = cursor.fetchone()
        
        # Get most active accounts
        cursor.execute("""
        SELECT account_id, total_sent 
        FROM campaign_accounts 
        WHERE campaign_id = ? 
        ORDER BY total_sent DESC 
        LIMIT 5
        """, (campaign_id,))
        
        top_accounts = cursor.fetchall()
        
        # Get daily message counts
        cursor.execute("""
        SELECT date(sent_at) as send_date, COUNT(*) 
        FROM message_usage 
        WHERE campaign_id = ? 
        GROUP BY send_date 
        ORDER BY send_date
        """, (campaign_id,))
        
        daily_counts = cursor.fetchall()
        
        # Compile stats
        stats = {
            'name': campaign_info[0],
            'status': campaign_info[1],
            'target_count': campaign_info[2],
            'completed_count': campaign_info[3],
            'created_at': campaign_info[4],
            'account_count': account_stats[0] if account_stats else 0,
            'total_sent': account_stats[1] if account_stats else 0,
            'top_accounts': [{'account_id': a[0], 'sent': a[1]} for a in top_accounts],
            'daily_counts': {d[0]: d[1] for d in daily_counts},
            'progress_percent': (account_stats[1] / campaign_info[2] * 100) if account_stats and campaign_info[2] else 0
        }
        
        # Add runtime stats if campaign is active
        if campaign_id in self.active_campaigns:
            stats.update({
                'is_running': self.active_campaigns[campaign_id].is_running,
                'is_paused': self.active_campaigns[campaign_id].is_paused,
                'runtime_stats': self.active_campaigns[campaign_id].stats
            })
        
        return stats
    
    def _start_campaign_thread(self, campaign_id: int) -> None:
        """Start the worker thread for a campaign"""
        # Create a queue for this campaign
        self.campaign_queues[campaign_id] = queue.Queue()
        
        # Create and start the thread
        thread = threading.Thread(
            target=self._campaign_worker,
            args=(campaign_id,),
            daemon=True
        )
        self.campaign_threads[campaign_id] = thread
        thread.start()
    
    def _campaign_worker(self, campaign_id: int) -> None:
        """Worker thread that manages messages for a campaign"""
        campaign = self.active_campaigns[campaign_id]
        stop_event = self.stop_events[campaign_id]
        message_queue = self.campaign_queues[campaign_id]
        
        logging.info(f"Campaign worker started for campaign {campaign_id}: {campaign.name}")
        
        try:
            # Get target message count
            cursor = self.conn.cursor()
            cursor.execute("SELECT target_count, completed_count FROM campaigns WHERE id = ?", (campaign_id,))
            result = cursor.fetchone()
            
            if result:
                target_count = result[0]
                completed_count = result[1]
                remaining_count = target_count - completed_count
            else:
                remaining_count = 0
            
            campaign.stats['messages_total'] = target_count
            campaign.stats['messages_sent'] = completed_count
            
            # Get accounts for this campaign
            campaign_accounts = self.get_campaign_accounts(campaign_id)
            if not campaign_accounts:
                logging.error(f"No accounts assigned to campaign {campaign_id}")
                return
            
            # Initialize account stats
            for account in campaign_accounts:
                campaign.stats['accounts'][account['account_id']] = {
                    'sent_today': 0,
                    'sent_this_hour': 0,
                    'last_sent': None
                }
            
            # Calculate distribution of messages across hours
            distribution = self.message_manager.calculate_daily_distribution(
                total_messages=remaining_count,
                start_hour=campaign.active_hours[0],
                end_hour=campaign.active_hours[1],
                distribution_pattern=campaign.distribution_pattern
            )
            
            # Main campaign loop
            while not stop_event.is_set() and campaign.stats['messages_sent'] < campaign.stats['messages_total']:
                # Check if campaign is paused
                if campaign.is_paused:
                    time.sleep(5)
                    continue
                
                # Get current time
                now = datetime.datetime.now()
                current_hour = now.hour
                current_day = now.weekday()  # 0 = Monday, 6 = Sunday
                
                # Check if we're within active hours and days
                if current_hour < campaign.active_hours[0] or current_hour > campaign.active_hours[1]:
                    # Outside active hours, sleep until next active hour
                    if current_hour > campaign.active_hours[1]:
                        # After end hour, sleep until start hour tomorrow
                        next_time = now.replace(hour=campaign.active_hours[0], minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
                    else:
                        # Before start hour, sleep until start hour today
                        next_time = now.replace(hour=campaign.active_hours[0], minute=0, second=0, microsecond=0)
                    
                    # Calculate sleep time in seconds
                    sleep_seconds = (next_time - now).total_seconds()
                    
                    # Log and sleep
                    logging.info(f"Outside active hours for campaign {campaign_id}, sleeping for {sleep_seconds:.1f} seconds")
                    
                    # Sleep in smaller intervals to allow for interruption
                    for _ in range(int(sleep_seconds / 10) + 1):
                        if stop_event.is_set():
                            break
                        time.sleep(min(10, sleep_seconds))
                    
                    continue
                
                # Check if current day is active
                if current_day not in campaign.active_days:
                    # Not an active day, sleep until midnight
                    next_time = (now.replace(hour=0, minute=0, second=0, microsecond=0) + 
                                datetime.timedelta(days=1))
                    sleep_seconds = (next_time - now).total_seconds()
                    
                    logging.info(f"Not an active day for campaign {campaign_id}, sleeping for {sleep_seconds:.1f} seconds")
                    
                    # Sleep in smaller intervals to allow for interruption
                    for _ in range(int(sleep_seconds / 10) + 1):
                        if stop_event.is_set():
                            break
                        time.sleep(min(10, sleep_seconds))
                    
                    continue
                
                # Get target messages for this hour
                target_for_hour = distribution.get(current_hour, 0)
                
                # Check if we've already sent all messages for this hour
                hour_key = f"{now.year}-{now.month:02d}-{now.day:02d}-{current_hour}"
                if hour_key not in campaign.stats['hourly_stats']:
                    campaign.stats['hourly_stats'][hour_key] = {
                        'target': target_for_hour,
                        'sent': 0
                    }
                
                if campaign.stats['hourly_stats'][hour_key]['sent'] >= target_for_hour:
                    # Already sent all messages for this hour, sleep until next hour
                    next_hour = now.replace(hour=current_hour+1, minute=0, second=0, microsecond=0)
                    if next_hour.hour > campaign.active_hours[1]:
                        # Next hour is after end time, sleep until start hour tomorrow
                        next_hour = now.replace(hour=campaign.active_hours[0], minute=0, second=0, microsecond=0) + datetime.timedelta(days=1)
                    
                    sleep_seconds = (next_hour - now).total_seconds()
                    
                    logging.info(f"Completed message target for hour {current_hour} in campaign {campaign_id}, sleeping for {sleep_seconds:.1f} seconds")
                    
                    # Sleep in smaller intervals to allow for interruption
                    for _ in range(int(sleep_seconds / 10) + 1):
                        if stop_event.is_set():
                            break
                        time.sleep(min(10, sleep_seconds))
                    
                    continue
                
                # Select an account to send from
                selected_account = self._select_account_for_sending(campaign_accounts, campaign)
                
                if not selected_account:
                    # No accounts available right now, sleep briefly and try again
                    logging.warning(f"No accounts available for sending in campaign {campaign_id}, waiting...")
                    time.sleep(60)
                    continue
                
                # Select a message to send
                message = self.message_manager.get_personalized_message(
                    account_id=selected_account['account_id'],
                    recipient="",  # Will be filled in by the messaging system
                    categories=campaign.message_categories
                )
                
                if not message:
                    logging.error(f"Failed to get message for campaign {campaign_id}")
                    time.sleep(5)
                    continue
                
                # Record the message as queued
                queueing_time = datetime.datetime.now()
                
                # Add the message to the queue for processing
                message_task = {
                    'campaign_id': campaign_id,
                    'account_id': selected_account['account_id'],
                    'message': message,
                    'queued_at': queueing_time
                }
                
                message_queue.put(message_task)
                
                # Update account stats
                account_id = selected_account['account_id']
                account_stats = campaign.stats['accounts'][account_id]
                account_stats['sent_today'] += 1
                account_stats['sent_this_hour'] += 1
                account_stats['last_sent'] = queueing_time
                
                # Update campaign stats
                campaign.stats['messages_sent'] += 1
                campaign.stats['hourly_stats'][hour_key]['sent'] += 1
                
                # Update database
                cursor.execute(
                    "UPDATE campaign_accounts SET total_sent = total_sent + 1, last_sent = ? WHERE campaign_id = ? AND account_id = ?",
                    (queueing_time.isoformat(), campaign_id, account_id)
                )
                
                cursor.execute(
                    "UPDATE campaigns SET completed_count = completed_count + 1 WHERE id = ?",
                    (campaign_id,)
                )
                
                self.conn.commit()
                
                # Calculate delay until next message
                delay = random.uniform(campaign.min_delay_seconds, campaign.max_delay_seconds)
                time.sleep(delay)
        
        except Exception as e:
            logging.error(f"Error in campaign worker for campaign {campaign_id}: {str(e)}", exc_info=True)
        finally:
            logging.info(f"Campaign worker exiting for campaign {campaign_id}")
    
    def _select_account_for_sending(self, campaign_accounts: List[Dict[str, Any]], campaign: Campaign) -> Optional[Dict[str, Any]]:
        """
        Select an account to send the next message
        
        Args:
            campaign_accounts: List of accounts in the campaign
            campaign: Campaign object
            
        Returns:
            Selected account or None if no accounts are available
        """
        # Get current time
        now = datetime.datetime.now()
        current_hour = now.hour
        
        # Shuffle the accounts to randomize selection
        accounts = campaign_accounts.copy()
        random.shuffle(accounts)
        
        for account in accounts:
            account_id = account['account_id']
            
            # Skip accounts that aren't in the campaign stats yet
            if account_id not in campaign.stats['accounts']:
                continue
            
            account_stats = campaign.stats['accounts'][account_id]
            
            # Check if account has reached its daily limit
            if account_stats['sent_today'] >= campaign.max_per_account_per_day:
                continue
            
            # Check if account has reached its hourly limit
            if account_stats['sent_this_hour'] >= campaign.max_per_account_per_hour:
                continue
            
            # Check if account needs to wait between messages
            if account_stats['last_sent']:
                elapsed_seconds = (now - account_stats['last_sent']).total_seconds()
                if elapsed_seconds < campaign.min_delay_seconds:
                    continue
            
            # This account is available
            return account
        
        # No accounts available
        return None
    
    def process_message_queue(self, callback: Callable[[Dict[str, Any]], bool]) -> None:
        """
        Process messages in the queue using a callback function
        
        Args:
            callback: Function that sends the message and returns success boolean
        """
        # Check all campaign queues
        for campaign_id, queue in self.campaign_queues.items():
            # Process up to 10 messages at a time
            for _ in range(10):
                if queue.empty():
                    break
                
                try:
                    # Get the next message task
                    message_task = queue.get_nowait()
                    
                    # Send the message using the callback
                    success = callback(message_task)
                    
                    if success:
                        # Record the message as sent
                        self.message_manager.record_message_sent(
                            template_id=message_task['message']['id'],
                            account_id=message_task['account_id'],
                            campaign_id=message_task['campaign_id']
                        )
                    else:
                        # If failed, log error
                        logging.error(f"Failed to send message for campaign {message_task['campaign_id']}")
                    
                    # Mark task as done
                    queue.task_done()
                    
                except queue.Empty:
                    break
                except Exception as e:
                    logging.error(f"Error processing message queue: {str(e)}")
    
    def close(self):
        """Clean up resources"""
        # Stop all campaigns
        for campaign_id in list(self.active_campaigns.keys()):
            self.stop_campaign(campaign_id)
        
        # Close database connection
        if hasattr(self, 'conn'):
            self.conn.close()


# Singleton instance
_campaign_manager = None

def get_campaign_manager():
    """Get the singleton campaign manager instance"""
    global _campaign_manager
    if _campaign_manager is None:
        _campaign_manager = CampaignManager()
    return _campaign_manager


# Example usage
if __name__ == "__main__":
    # Initialize campaign manager
    manager = get_campaign_manager()
    
    # Create a simple campaign
    campaign = Campaign(
        name="Test Campaign",
        description="A test campaign",
        active_hours=(8, 20),
        active_days=[0, 1, 2, 3, 4],  # Monday to Friday
        distribution_pattern="peak",
        max_per_account_per_day=100,
        max_per_account_per_hour=15
    )
    
    # Create the campaign in the database
    campaign_id = manager.create_campaign(campaign)
    
    print(f"Created campaign with ID: {campaign_id}")
    
    # Clean up
    manager.close()