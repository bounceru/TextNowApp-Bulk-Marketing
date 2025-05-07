"""
Data Manager for TextNow Max

This module manages the database operations for TextNow accounts, campaigns,
and other data structures for the TextNow Max application.
"""

import os
import json
import sqlite3
import datetime
import hashlib
import random
import string
from typing import Dict, List, Any, Optional, Tuple

class DataManager:
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the data manager"""
        self.database_path = database_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create accounts table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            phone_number TEXT,
            area_code TEXT,
            name TEXT,
            email TEXT,
            birth_date TEXT,
            registration_ip TEXT,
            ip_family TEXT,
            browser_fingerprint TEXT,
            device_fingerprint TEXT,
            creation_method TEXT DEFAULT 'auto',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP,
            last_message_sent TIMESTAMP,
            last_call TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            health_score INTEGER DEFAULT 100,
            status TEXT DEFAULT 'active',
            voicemail_id INTEGER,
            profile_photo TEXT,
            notes TEXT,
            additional_data TEXT,
            next_check_time TIMESTAMP
        )
        ''')
        
        # Create account_health_checks table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            check_type TEXT NOT NULL,
            check_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL,
            score INTEGER,
            details TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Create account_activity_log table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            activity_type TEXT NOT NULL,
            activity_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            details TEXT,
            success INTEGER DEFAULT 1,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Create campaigns table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'draft',
            target_count INTEGER,
            completed_count INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            message_variation_type TEXT DEFAULT 'random',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            distribution_profile TEXT DEFAULT 'even',
            duration_hours INTEGER DEFAULT 12,
            image_variation BOOLEAN DEFAULT 0,
            multimedia_variation BOOLEAN DEFAULT 0,
            allow_resume BOOLEAN DEFAULT 1,
            last_position TEXT,
            random_delay_min INTEGER DEFAULT 30,
            random_delay_max INTEGER DEFAULT 180
        )
        ''')
        
        # Create target_numbers table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS target_numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            phone_number TEXT NOT NULL,
            name TEXT,
            status TEXT DEFAULT 'pending',
            processed_at TIMESTAMP,
            account_id INTEGER,
            message_id INTEGER,
            message_status TEXT,
            additional_data TEXT,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Create campaign_messages table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            image_path TEXT,
            multimedia_path TEXT,
            usage_count INTEGER DEFAULT 0,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id)
        )
        ''')
        
        # Create campaign_accounts table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            usage_count INTEGER DEFAULT 0,
            last_used TIMESTAMP,
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_account(self, account_data: Dict[str, Any]) -> Tuple[bool, str, Optional[int]]:
        """
        Add a new account to the database (manual entry)
        
        Args:
            account_data: Dictionary containing account information
            
        Returns:
            Tuple of (success, message, account_id)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Required fields
            username = account_data.get('username')
            password = account_data.get('password')
            
            if not username or not password:
                conn.close()
                return False, "Username and password are required", None
            
            # Check if account already exists
            cursor.execute("SELECT id FROM accounts WHERE username = ?", (username,))
            if cursor.fetchone():
                conn.close()
                return False, f"Account with username '{username}' already exists", None
            
            # Prepare optional fields
            phone_number = account_data.get('phone_number', '')
            area_code = account_data.get('area_code', '')
            name = account_data.get('name', '')
            email = account_data.get('email', '')
            birth_date = account_data.get('birth_date', '')
            registration_ip = account_data.get('registration_ip', '')
            ip_family = account_data.get('ip_family', '')
            browser_fingerprint = account_data.get('browser_fingerprint', '')
            device_fingerprint = account_data.get('device_fingerprint', '')
            
            # Set default dates if provided
            created_at = account_data.get('created_at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            last_login = account_data.get('last_login', None)
            last_message_sent = account_data.get('last_message_sent', None)
            last_call = account_data.get('last_call', None)
            
            # Other optional fields
            usage_count = account_data.get('usage_count', 0)
            health_score = account_data.get('health_score', 100)
            status = account_data.get('status', 'active')
            voicemail_id = account_data.get('voicemail_id', None)
            profile_photo = account_data.get('profile_photo', None)
            notes = account_data.get('notes', '')
            
            # Additional data as JSON
            additional_data = {k: v for k, v in account_data.items() 
                               if k not in [
                                   'username', 'password', 'phone_number', 'area_code',
                                   'name', 'email', 'birth_date', 'registration_ip', 
                                   'ip_family', 'browser_fingerprint', 'device_fingerprint',
                                   'created_at', 'last_login', 'last_message_sent', 
                                   'last_call', 'usage_count', 'health_score', 'status',
                                   'voicemail_id', 'profile_photo', 'notes'
                               ]}
            
            # Insert the account
            cursor.execute(
                """
                INSERT INTO accounts (
                    username, password, phone_number, area_code, name, email, birth_date,
                    registration_ip, ip_family, browser_fingerprint, device_fingerprint,
                    creation_method, created_at, last_login, last_message_sent, last_call,
                    usage_count, health_score, status, voicemail_id, profile_photo,
                    notes, additional_data
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username, password, phone_number, area_code, name, email, birth_date,
                    registration_ip, ip_family, browser_fingerprint, device_fingerprint,
                    'manual', created_at, last_login, last_message_sent, last_call,
                    usage_count, health_score, status, voicemail_id, profile_photo,
                    notes, json.dumps(additional_data)
                )
            )
            
            account_id = cursor.lastrowid
            
            # Log activity
            cursor.execute(
                "INSERT INTO account_activity_log (account_id, activity_type, details) VALUES (?, ?, ?)",
                (account_id, 'manual_creation', 'Account manually added to the system')
            )
            
            conn.commit()
            conn.close()
            
            return True, f"Account {username} added successfully", account_id
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False, f"Error adding account: {str(e)}", None
    
    def update_account(self, account_id: int, account_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Update an existing account
        
        Args:
            account_id: The ID of the account to update
            account_data: Dictionary containing updated account information
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check if account exists
            cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
            if not cursor.fetchone():
                conn.close()
                return False, f"Account with ID {account_id} does not exist"
            
            # Prepare update fields
            update_fields = []
            params = []
            
            # Handle all possible fields for update
            field_mappings = {
                'username': 'username',
                'password': 'password',
                'phone_number': 'phone_number',
                'area_code': 'area_code',
                'name': 'name',
                'email': 'email',
                'birth_date': 'birth_date',
                'registration_ip': 'registration_ip',
                'ip_family': 'ip_family',
                'browser_fingerprint': 'browser_fingerprint',
                'device_fingerprint': 'device_fingerprint',
                'last_login': 'last_login',
                'last_message_sent': 'last_message_sent',
                'last_call': 'last_call',
                'usage_count': 'usage_count',
                'health_score': 'health_score',
                'status': 'status',
                'voicemail_id': 'voicemail_id',
                'profile_photo': 'profile_photo',
                'notes': 'notes'
            }
            
            for key, field in field_mappings.items():
                if key in account_data:
                    update_fields.append(f"{field} = ?")
                    params.append(account_data[key])
            
            # Handle additional data separately
            additional_data_keys = [k for k in account_data.keys() if k not in field_mappings]
            if additional_data_keys:
                # Get existing additional data
                cursor.execute("SELECT additional_data FROM accounts WHERE id = ?", (account_id,))
                result = cursor.fetchone()
                
                if result and result[0]:
                    try:
                        existing_data = json.loads(result[0])
                    except:
                        existing_data = {}
                else:
                    existing_data = {}
                
                # Update with new values
                for key in additional_data_keys:
                    existing_data[key] = account_data[key]
                
                update_fields.append("additional_data = ?")
                params.append(json.dumps(existing_data))
            
            # Always update updated_at
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            if not update_fields:
                conn.close()
                return False, "No fields to update"
            
            # Build and execute update query
            query = f"UPDATE accounts SET {', '.join(update_fields)} WHERE id = ?"
            params.append(account_id)
            
            cursor.execute(query, params)
            
            # Log activity
            cursor.execute(
                "INSERT INTO account_activity_log (account_id, activity_type, details) VALUES (?, ?, ?)",
                (account_id, 'account_update', f"Account updated: {', '.join(field_mappings.keys() & account_data.keys())}")
            )
            
            conn.commit()
            conn.close()
            
            return True, f"Account updated successfully"
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False, f"Error updating account: {str(e)}"
    
    def get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Get account details by ID
        
        Args:
            account_id: The ID of the account to retrieve
            
        Returns:
            Dictionary with account details or None if not found
        """
        try:
            conn = sqlite3.connect(self.database_path)
            # Convert row names to dictionary keys
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                """
                SELECT id, username, password, phone_number, area_code, name, email,
                       birth_date, registration_ip, ip_family, browser_fingerprint, 
                       device_fingerprint, creation_method, created_at, last_login,
                       last_message_sent, last_call, usage_count, health_score, status,
                       voicemail_id, profile_photo, notes, additional_data
                FROM accounts
                WHERE id = ?
                """,
                (account_id,)
            )
            
            row = cursor.fetchone()
            
            if not row:
                conn.close()
                return None
            
            # Convert to dictionary
            account = dict(row)
            
            # Parse additional data
            if account['additional_data']:
                try:
                    account['additional_data'] = json.loads(account['additional_data'])
                except:
                    account['additional_data'] = {}
            else:
                account['additional_data'] = {}
            
            # Get recent activity logs
            cursor.execute(
                """
                SELECT activity_type, activity_date, details, success
                FROM account_activity_log
                WHERE account_id = ?
                ORDER BY activity_date DESC
                LIMIT 10
                """,
                (account_id,)
            )
            
            activity_logs = []
            for row in cursor.fetchall():
                activity_logs.append({
                    'type': row[0],
                    'date': row[1],
                    'details': row[2],
                    'success': bool(row[3])
                })
            
            account['recent_activity'] = activity_logs
            
            # Get health check history
            cursor.execute(
                """
                SELECT check_type, check_date, status, score, details
                FROM account_health_checks
                WHERE account_id = ?
                ORDER BY check_date DESC
                LIMIT 5
                """,
                (account_id,)
            )
            
            health_checks = []
            for row in cursor.fetchall():
                health_checks.append({
                    'type': row[0],
                    'date': row[1],
                    'status': row[2],
                    'score': row[3],
                    'details': row[4]
                })
            
            account['health_checks'] = health_checks
            
            conn.close()
            return account
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.close()
            print(f"Error getting account: {str(e)}")
            return None
    
    def delete_account(self, account_id: int) -> Tuple[bool, str]:
        """
        Delete an account
        
        Args:
            account_id: The ID of the account to delete
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Check if account exists
            cursor.execute("SELECT id FROM accounts WHERE id = ?", (account_id,))
            if not cursor.fetchone():
                conn.close()
                return False, f"Account with ID {account_id} does not exist"
            
            # Delete related records
            cursor.execute("DELETE FROM account_health_checks WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM account_activity_log WHERE account_id = ?", (account_id,))
            cursor.execute("DELETE FROM campaign_accounts WHERE account_id = ?", (account_id,))
            
            # Update any target numbers that used this account to NULL
            cursor.execute("UPDATE target_numbers SET account_id = NULL WHERE account_id = ?", (account_id,))
            
            # Delete the account
            cursor.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            
            conn.commit()
            conn.close()
            
            return True, f"Account and related records deleted successfully"
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False, f"Error deleting account: {str(e)}"
    
    def get_accounts(self, filters: Dict[str, Any] = None, page: int = 1, page_size: int = 50, 
                     sort_by: str = 'id', sort_order: str = 'asc') -> Dict[str, Any]:
        """
        Get accounts with filtering, pagination and sorting
        
        Args:
            filters: Dictionary of filter criteria
            page: Page number, starting from 1
            page_size: Number of results per page
            sort_by: Field to sort by
            sort_order: 'asc' or 'desc'
            
        Returns:
            Dictionary with accounts and pagination info
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Start building the query
            query = """
                SELECT id, username, phone_number, area_code, name, email,
                       created_at, last_login, last_message_sent, usage_count, 
                       health_score, status, registration_ip, ip_family
                FROM accounts
            """
            
            count_query = "SELECT COUNT(*) FROM accounts"
            
            # Apply filters
            conditions = []
            params = []
            
            if filters:
                if filters.get('username'):
                    conditions.append("username LIKE ?")
                    params.append(f"%{filters['username']}%")
                
                if filters.get('phone_number'):
                    conditions.append("phone_number LIKE ?")
                    params.append(f"%{filters['phone_number']}%")
                
                if filters.get('area_code'):
                    conditions.append("area_code = ?")
                    params.append(filters['area_code'])
                
                if filters.get('name'):
                    conditions.append("name LIKE ?")
                    params.append(f"%{filters['name']}%")
                
                if filters.get('email'):
                    conditions.append("email LIKE ?")
                    params.append(f"%{filters['email']}%")
                
                if filters.get('status'):
                    conditions.append("status = ?")
                    params.append(filters['status'])
                
                if filters.get('health_score_min') is not None:
                    conditions.append("health_score >= ?")
                    params.append(filters['health_score_min'])
                
                if filters.get('health_score_max') is not None:
                    conditions.append("health_score <= ?")
                    params.append(filters['health_score_max'])
                
                if filters.get('creation_date_start'):
                    conditions.append("created_at >= ?")
                    params.append(filters['creation_date_start'])
                
                if filters.get('creation_date_end'):
                    conditions.append("created_at <= ?")
                    params.append(filters['creation_date_end'])
                
                if filters.get('last_login_start'):
                    conditions.append("last_login >= ?")
                    params.append(filters['last_login_start'])
                
                if filters.get('last_login_end'):
                    conditions.append("last_login <= ?")
                    params.append(filters['last_login_end'])
                
                if filters.get('usage_count_min') is not None:
                    conditions.append("usage_count >= ?")
                    params.append(filters['usage_count_min'])
                
                if filters.get('usage_count_max') is not None:
                    conditions.append("usage_count <= ?")
                    params.append(filters['usage_count_max'])
                
                if filters.get('creation_method'):
                    conditions.append("creation_method = ?")
                    params.append(filters['creation_method'])
                
                if filters.get('registration_ip'):
                    conditions.append("registration_ip LIKE ?")
                    params.append(f"%{filters['registration_ip']}%")
                
                if filters.get('ip_family'):
                    conditions.append("ip_family LIKE ?")
                    params.append(f"%{filters['ip_family']}%")
            
            # Add WHERE clause if there are conditions
            if conditions:
                query += f" WHERE {' AND '.join(conditions)}"
                count_query += f" WHERE {' AND '.join(conditions)}"
            
            # Add sorting
            valid_sort_fields = [
                'id', 'username', 'phone_number', 'area_code', 'name', 'email',
                'created_at', 'last_login', 'last_message_sent', 'usage_count',
                'health_score', 'status', 'registration_ip', 'ip_family'
            ]
            
            if sort_by not in valid_sort_fields:
                sort_by = 'id'
            
            sort_order = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
            query += f" ORDER BY {sort_by} {sort_order}"
            
            # Add pagination
            offset = (page - 1) * page_size
            query += f" LIMIT {page_size} OFFSET {offset}"
            
            # Get total count
            cursor.execute(count_query, params)
            total_count = cursor.fetchone()[0]
            
            # Execute the main query
            cursor.execute(query, params)
            
            accounts = []
            for row in cursor.fetchall():
                accounts.append(dict(row))
            
            # Calculate pagination info
            total_pages = (total_count + page_size - 1) // page_size  # Ceiling division
            has_next = page < total_pages
            has_prev = page > 1
            
            conn.close()
            
            return {
                'accounts': accounts,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': total_count,
                    'total_pages': total_pages,
                    'has_next': has_next,
                    'has_prev': has_prev
                }
            }
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.close()
            print(f"Error getting accounts: {str(e)}")
            return {
                'accounts': [],
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total_count': 0,
                    'total_pages': 0,
                    'has_next': False,
                    'has_prev': False
                },
                'error': str(e)
            }
    
    def log_account_activity(self, account_id: int, activity_type: str, details: str = None, 
                          success: bool = True) -> bool:
        """
        Log an activity for an account
        
        Args:
            account_id: ID of the account
            activity_type: Type of activity (login, message, call, etc.)
            details: Optional details about the activity
            success: Whether the activity was successful
            
        Returns:
            True if logged successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO account_activity_log (account_id, activity_type, details, success) VALUES (?, ?, ?, ?)",
                (account_id, activity_type, details, 1 if success else 0)
            )
            
            # Update relevant timestamp in accounts table
            if activity_type == 'login':
                cursor.execute(
                    "UPDATE accounts SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
                    (account_id,)
                )
            elif activity_type == 'message_sent':
                cursor.execute(
                    "UPDATE accounts SET last_message_sent = CURRENT_TIMESTAMP, usage_count = usage_count + 1 WHERE id = ?",
                    (account_id,)
                )
            elif activity_type == 'call':
                cursor.execute(
                    "UPDATE accounts SET last_call = CURRENT_TIMESTAMP WHERE id = ?",
                    (account_id,)
                )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            print(f"Error logging account activity: {str(e)}")
            return False
    
    def add_account_health_check(self, account_id: int, check_type: str, status: str, 
                              score: int, details: str = None) -> bool:
        """
        Add a health check record for an account
        
        Args:
            account_id: ID of the account
            check_type: Type of health check (login, message, profile, etc.)
            status: Status of the check (pass, warning, fail)
            score: Health score (0-100)
            details: Optional details about the check
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            cursor.execute(
                """
                INSERT INTO account_health_checks 
                (account_id, check_type, status, score, details)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account_id, check_type, status, score, details)
            )
            
            # Update account health score and status
            if status == 'fail':
                new_status = 'flagged'
            elif status == 'warning':
                new_status = 'warning'
            else:
                new_status = 'active'
            
            cursor.execute(
                """
                UPDATE accounts 
                SET health_score = ?, status = ?, next_check_time = datetime('now', '+1 day')
                WHERE id = ?
                """,
                (score, new_status, account_id)
            )
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            print(f"Error adding account health check: {str(e)}")
            return False
    
    def send_message_from_account(self, account_id: int, to_number: str, message: str, 
                               image_path: str = None, multimedia_path: str = None) -> Tuple[bool, str]:
        """
        Record a message sent from an account (for manual messaging feature)
        
        Args:
            account_id: ID of the account sending the message
            to_number: Recipient phone number
            message: Message text
            image_path: Optional path to image attachment
            multimedia_path: Optional path to other multimedia attachment
            
        Returns:
            Tuple of (success, message)
        """
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Get account information
            cursor.execute("SELECT username, phone_number FROM accounts WHERE id = ?", (account_id,))
            account = cursor.fetchone()
            
            if not account:
                conn.close()
                return False, f"Account with ID {account_id} not found"
            
            username, phone_number = account
            
            # Create a target number record (not associated with any campaign)
            cursor.execute(
                """
                INSERT INTO target_numbers 
                (phone_number, status, processed_at, account_id, message_status, additional_data)
                VALUES (?, ?, CURRENT_TIMESTAMP, ?, ?, ?)
                """,
                (
                    to_number, 
                    'completed', 
                    account_id, 
                    'sent', 
                    json.dumps({
                        'message': message,
                        'image_path': image_path,
                        'multimedia_path': multimedia_path,
                        'manual_send': True
                    })
                )
            )
            
            # Log the activity
            message_details = f"To: {to_number}, Message: {message[:50]}..."
            if image_path:
                message_details += f" [with image: {os.path.basename(image_path)}]"
            if multimedia_path:
                message_details += f" [with multimedia: {os.path.basename(multimedia_path)}]"
                
            cursor.execute(
                "INSERT INTO account_activity_log (account_id, activity_type, details) VALUES (?, ?, ?)",
                (account_id, 'manual_message_sent', message_details)
            )
            
            # Update account usage stats
            cursor.execute(
                """
                UPDATE accounts 
                SET usage_count = usage_count + 1, 
                    last_message_sent = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (account_id,)
            )
            
            conn.commit()
            conn.close()
            
            return True, f"Message sent from {username} ({phone_number}) to {to_number}"
            
        except Exception as e:
            if 'conn' in locals() and conn:
                conn.rollback()
                conn.close()
            return False, f"Error sending message: {str(e)}"

# Singleton instance
_data_manager = None

def get_data_manager():
    """Get the data manager singleton instance"""
    global _data_manager
    if _data_manager is None:
        _data_manager = DataManager()
    return _data_manager