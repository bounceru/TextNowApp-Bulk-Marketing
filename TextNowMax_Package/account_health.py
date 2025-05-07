"""
Account Health Monitoring System for ProgressGhostCreator

This module monitors the health of TextNow accounts and automatically flags
or replaces accounts that show signs of being blocked or degraded.
"""

import os
import logging
import json
import time
import random
import sqlite3
from datetime import datetime, timedelta

class AccountHealthMonitor:
    def __init__(self, database_path='ghost_accounts.db', check_interval=3600):
        """Initialize the account health monitor"""
        self.database_path = database_path
        self.check_interval = check_interval  # Default 1 hour
        self.conn = None
        self._init_database()
        
        # Health check types and their weights
        self.check_types = {
            'login': 30,           # Can we still log in?
            'messaging': 25,       # Can we send messages?
            'phone_status': 20,    # Is the phone number still active?
            'voicemail': 10,       # Can we access voicemail?
            'contacts': 5,         # Can we access contacts?
            'profile': 5,          # Can we access profile settings?
            'app_usage': 5         # General app functionality
        }
        
        # Thresholds for health scores
        self.thresholds = {
            'healthy': 80,         # Above this is healthy
            'warning': 60,         # Above this is warning, below is flagged
            'critical': 40         # Below this requires replacement
        }
        
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect(self.database_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            logging.error(f"Error initializing health monitor database: {e}")
            return False
            
    def start_monitoring(self, bot=None, replacement_handler=None):
        """Start a background monitoring thread"""
        import threading
        
        self.bot = bot
        self.replacement_handler = replacement_handler
        self.running = True
        
        def monitor_thread():
            logging.info("Account health monitoring thread started")
            
            while self.running:
                try:
                    self.check_accounts_health()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logging.error(f"Error in health monitor thread: {e}")
                    time.sleep(60)  # Wait a bit before retrying
            
            logging.info("Account health monitoring thread stopped")
            
        # Start the monitoring thread
        self.monitor_thread = threading.Thread(target=monitor_thread)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        return True
        
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        
    def check_accounts_health(self, limit=100):
        """Perform health checks on accounts that need checking"""
        try:
            # Get accounts for health check
            cursor = self.conn.cursor()
            
            # Get accounts that haven't been checked recently or have warning statuses
            cursor.execute('''
            SELECT a.* FROM accounts a
            LEFT JOIN (
                SELECT account_id, MAX(checked_at) as last_check, status
                FROM health_logs
                GROUP BY account_id
            ) h ON a.id = h.account_id
            WHERE a.active = 1 AND (
                h.last_check IS NULL 
                OR datetime(h.last_check) < datetime('now', '-24 hours')
                OR (h.status = 'warning' AND datetime(h.last_check) < datetime('now', '-4 hours'))
            )
            ORDER BY h.last_check ASC NULLS FIRST, a.id ASC
            LIMIT ?
            ''', (limit,))
            
            accounts = cursor.fetchall()
            
            if not accounts:
                logging.info("No accounts due for health check")
                return
                
            logging.info(f"Checking health of {len(accounts)} accounts")
            
            for account in accounts:
                account_id = account['id']
                phone_number = account['phone_number']
                
                # Perform health checks
                health_results = {}
                overall_score = 0
                overall_status = 'healthy'
                details = {}
                
                # In a demo version, we'll simulate the checks
                # In production, this would actually test the account functionality
                for check_type, weight in self.check_types.items():
                    check_result = self._perform_check(account, check_type)
                    
                    health_results[check_type] = check_result
                    check_score = check_result['score'] * (weight / 100)
                    overall_score += check_score
                    
                    # Track the lowest status
                    if check_result['status'] == 'flagged':
                        overall_status = 'flagged'
                    elif check_result['status'] == 'warning' and overall_status != 'flagged':
                        overall_status = 'warning'
                        
                    # Store details
                    details[check_type] = {
                        'score': check_result['score'],
                        'status': check_result['status'],
                        'message': check_result['message'],
                        'weight': weight,
                        'weighted_score': check_score
                    }
                
                # Log the health check
                logging.info(f"Account {phone_number}: Health score {overall_score:.1f}, Status: {overall_status}")
                self._log_health_check(account_id, 'composite', overall_status, overall_score, details)
                
                # Update the account's health score
                self._update_account_health(account_id, overall_score, overall_status)
                
                # If flagged and below critical threshold, trigger replacement
                if overall_status == 'flagged' and overall_score < self.thresholds['critical']:
                    self._handle_flagged_account(account_id, overall_score, details)
                
                # Add a short delay between accounts
                time.sleep(random.uniform(1, 3))
                
            return True
                
        except Exception as e:
            logging.error(f"Error checking accounts health: {e}")
            return False
            
    def _perform_check(self, account, check_type):
        """Perform a specific health check on an account
        
        In a production version, this would actually test the account.
        For this demo, we'll simulate the checks with realistic probabilities.
        """
        phone_number = account['phone_number']
        account_age_days = self._get_account_age_days(account['created_at'])
        
        # This logic simulates the natural degradation of accounts over time
        # In reality, you would test actual functionality
        base_success_probability = 0.95  # 95% base success rate
        
        # Account age factor - older accounts are slightly more likely to have issues
        age_factor = min(account_age_days / 180, 0.15)  # Max 15% reduction for accounts 6+ months old
        
        # Random factor
        random_factor = random.uniform(0, 0.10)  # Up to 10% random variation
        
        # Different check types have different baseline reliabilities
        check_type_factors = {
            'login': 0.02,          # Login rarely has issues
            'messaging': 0.08,      # Messaging more commonly flagged
            'phone_status': 0.05,   # Phone number status occasionally has issues
            'voicemail': 0.03,      # Voicemail rarely has issues
            'contacts': 0.02,       # Contacts access rarely has issues
            'profile': 0.02,        # Profile access rarely has issues
            'app_usage': 0.03       # General app usage rarely has issues
        }
        
        type_factor = check_type_factors.get(check_type, 0.03)
        
        # Calculate success probability
        success_probability = base_success_probability - age_factor - type_factor - random_factor
        
        # Generate a random outcome based on the probability
        random_outcome = random.random()
        
        if random_outcome <= success_probability:
            # Healthy - score between 85-100
            score = random.uniform(85, 100)
            status = 'healthy'
            message = f"{check_type.title()} check passed"
        elif random_outcome <= success_probability + 0.08:
            # Warning - score between 60-84
            score = random.uniform(60, 84)
            status = 'warning'
            message = f"{check_type.title()} showing signs of potential issues"
        else:
            # Flagged - score between 10-59
            score = random.uniform(10, 59)
            status = 'flagged'
            message = f"{check_type.title()} check failed - account may be restricted"
            
        # For login and messaging checks, if they fail it's more severe
        if check_type in ['login', 'messaging'] and status == 'flagged':
            score = min(score, 30)  # More severe for critical functionality
            
        # Add some specific contextual messages based on check type
        if check_type == 'login' and status == 'flagged':
            message = "Login failed - invalid credentials or account locked"
        elif check_type == 'messaging' and status == 'flagged':
            message = "Message sending failed - account may be blocked from sending"
        elif check_type == 'phone_status' and status == 'flagged':
            message = "Phone number appears to be deactivated or restricted"
            
        return {
            'score': score,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
    def _get_account_age_days(self, created_at_str):
        """Calculate the age of an account in days"""
        try:
            created_at = datetime.fromisoformat(created_at_str)
            age = datetime.now() - created_at
            return age.days
        except:
            return 0
            
    def _log_health_check(self, account_id, check_type, status, score, details=None):
        """Add a health check log to the database"""
        try:
            self.conn.execute('''
            INSERT INTO health_logs (
                account_id, check_type, status, score, details, checked_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                account_id,
                check_type,
                status,
                score,
                json.dumps(details) if details else None,
                datetime.now().isoformat()
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error logging health check: {e}")
            self.conn.rollback()
            return False
            
    def _update_account_health(self, account_id, health_score, status):
        """Update the account's health score and status"""
        try:
            # If flagged, update account status
            is_flagged = 1 if status == 'flagged' else 0
            flagged_reason = "Account health check failed" if is_flagged else None
            
            self.conn.execute('''
            UPDATE accounts SET 
                health_score = ?,
                flagged = ?,
                flagged_reason = ?,
                last_used_at = ?
            WHERE id = ?
            ''', (
                health_score,
                is_flagged,
                flagged_reason,
                datetime.now().isoformat(),
                account_id
            ))
            
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error updating account health: {e}")
            self.conn.rollback()
            return False
            
    def _handle_flagged_account(self, account_id, score, details):
        """Handle a flagged account - trigger replacement if needed"""
        logging.warning(f"Account ID {account_id} flagged with score {score:.1f} - triggering replacement")
        
        # Get the account details
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
        account = cursor.fetchone()
        
        if not account:
            logging.error(f"Could not find account {account_id} for replacement")
            return False
            
        # Determine reason from details
        reason = "Low health score"
        if 'messaging' in details and details['messaging']['status'] == 'flagged':
            reason = "Messaging functionality restricted"
        elif 'login' in details and details['login']['status'] == 'flagged':
            reason = "Login functionality restricted"
        elif 'phone_status' in details and details['phone_status']['status'] == 'flagged':
            reason = "Phone number deactivated"
            
        # If we have a replacement handler, call it
        if self.replacement_handler:
            self.replacement_handler(account_id, reason)
        else:
            # Otherwise just log and mark the account
            logging.warning(f"No replacement handler for account {account_id}")
            
            # Mark account as inactive
            self.conn.execute('''
            UPDATE accounts SET 
                active = 0,
                flagged = 1,
                flagged_reason = ?
            WHERE id = ?
            ''', (reason, account_id))
            
            self.conn.commit()
            
        return True
            
    def get_health_report(self, days=7):
        """Get a health report for all accounts"""
        try:
            cursor = self.conn.cursor()
            
            # Get overall stats
            cursor.execute('''
            SELECT 
                COUNT(*) as total_accounts,
                SUM(CASE WHEN active = 1 THEN 1 ELSE 0 END) as active_accounts,
                SUM(CASE WHEN flagged = 1 THEN 1 ELSE 0 END) as flagged_accounts,
                AVG(health_score) as avg_health_score,
                COUNT(CASE WHEN health_score >= 80 THEN 1 END) as healthy_accounts,
                COUNT(CASE WHEN health_score >= 60 AND health_score < 80 THEN 1 END) as warning_accounts,
                COUNT(CASE WHEN health_score < 60 THEN 1 END) as unhealthy_accounts
            FROM accounts
            ''')
            
            overall = dict(cursor.fetchone())
            
            # Get daily health log stats
            cursor.execute('''
            SELECT 
                date(checked_at) as check_date,
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warning_checks,
                SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) as flagged_checks,
                AVG(score) as avg_score
            FROM health_logs
            WHERE datetime(checked_at) >= datetime('now', ?)
            GROUP BY date(checked_at)
            ORDER BY date(checked_at) DESC
            ''', (f'-{days} days',))
            
            daily_stats = [dict(row) for row in cursor.fetchall()]
            
            # Get recently replaced accounts
            cursor.execute('''
            SELECT 
                r.original_account_id,
                r.replacement_account_id,
                r.replaced_at,
                r.reason,
                a1.phone_number as original_phone,
                a2.phone_number as replacement_phone
            FROM account_replacements r
            JOIN accounts a1 ON r.original_account_id = a1.id
            JOIN accounts a2 ON r.replacement_account_id = a2.id
            WHERE datetime(r.replaced_at) >= datetime('now', ?)
            ORDER BY r.replaced_at DESC
            LIMIT 50
            ''', (f'-{days} days',))
            
            replacements = [dict(row) for row in cursor.fetchall()]
            
            # Get checks by type
            cursor.execute('''
            SELECT 
                check_type,
                COUNT(*) as total_checks,
                SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_checks,
                SUM(CASE WHEN status = 'warning' THEN 1 ELSE 0 END) as warning_checks,
                SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) as flagged_checks,
                AVG(score) as avg_score
            FROM health_logs
            WHERE datetime(checked_at) >= datetime('now', ?) AND check_type != 'composite'
            GROUP BY check_type
            ORDER BY total_checks DESC
            ''', (f'-{days} days',))
            
            check_type_stats = [dict(row) for row in cursor.fetchall()]
            
            return {
                'overall': overall,
                'daily_stats': daily_stats,
                'replacements': replacements,
                'check_type_stats': check_type_stats
            }
            
        except Exception as e:
            logging.error(f"Error getting health report: {e}")
            return None
            
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None


def get_account_health_monitor(check_interval=3600):
    """Get the account health monitor singleton instance"""
    return AccountHealthMonitor(check_interval=check_interval)


if __name__ == "__main__":
    # Test the account health monitor
    logging.basicConfig(level=logging.INFO, 
                       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    monitor = AccountHealthMonitor()
    
    def replacement_callback(account_id, reason):
        print(f"Need to replace account {account_id} because: {reason}")
        
    # Start monitoring
    monitor.replacement_handler = replacement_callback
    monitor.check_accounts_health(limit=10)
    
    # Get health report
    report = monitor.get_health_report()
    print(json.dumps(report, indent=2))
    
    # Close connections
    monitor.close()