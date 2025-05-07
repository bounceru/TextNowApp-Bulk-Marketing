"""
Token and cookie manager for TextNow accounts
Handles storing and retrieving authentication tokens and cookies for accounts
"""

import os
import json
import logging
import pickle
import sqlite3
from datetime import datetime
import threading
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TokenManager:
    def __init__(self, database_path='ghost_accounts.db', tokens_dir='account_tokens'):
        """Initialize the token manager"""
        self.database_path = database_path
        self.tokens_dir = tokens_dir
        
        # Create tokens directory if it doesn't exist
        os.makedirs(self.tokens_dir, exist_ok=True)
        
        # Initialize database connection
        self._init_database()
        
        # Set up token check thread
        self.running = True
        self.check_thread = threading.Thread(target=self._token_check_thread)
        self.check_thread.daemon = True
        self.check_thread.start()
    
    def _init_database(self):
        """Initialize the database connection and tables"""
        try:
            self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            
            cursor = self.conn.cursor()
            
            # Add token_status field to accounts table if it doesn't exist
            cursor.execute("PRAGMA table_info(accounts)")
            columns = cursor.fetchall()
            column_names = [col["name"] for col in columns]
            
            if "token_status" not in column_names:
                cursor.execute("""
                ALTER TABLE accounts ADD COLUMN token_status TEXT DEFAULT 'unknown'
                """)
                
            if "last_token_update" not in column_names:
                cursor.execute("""
                ALTER TABLE accounts ADD COLUMN last_token_update TEXT
                """)
                
            if "last_token_check" not in column_names:
                cursor.execute("""
                ALTER TABLE accounts ADD COLUMN last_token_check TEXT
                """)
                
            # Create token_log table if it doesn't exist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS token_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
            """)
            
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Failed to initialize token manager database: {e}")
            raise
    
    def save_tokens(self, account_id, tokens_data, cookies=None):
        """Save tokens and cookies for an account"""
        try:
            # Generate token filename
            token_file = os.path.join(self.tokens_dir, f"account_{account_id}_tokens.json")
            cookie_file = os.path.join(self.tokens_dir, f"account_{account_id}_cookies.pkl")
            
            # Save tokens to file
            with open(token_file, 'w') as f:
                json.dump(tokens_data, f)
            
            # Save cookies if provided
            if cookies:
                with open(cookie_file, 'wb') as f:
                    pickle.dump(cookies, f)
            
            # Update account status in database
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE accounts 
            SET token_status = ?, last_token_update = ? 
            WHERE id = ?
            """, ('valid', datetime.now().isoformat(), account_id))
            
            # Log the token update
            cursor.execute("""
            INSERT INTO token_log (account_id, event_type, status, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """, (
                account_id, 
                'save', 
                'success', 
                datetime.now().isoformat(),
                f"Tokens and cookies saved for account {account_id}"
            ))
            
            self.conn.commit()
            
            logging.info(f"Tokens and cookies saved for account {account_id}")
            return True
        
        except Exception as e:
            logging.error(f"Failed to save tokens for account {account_id}: {e}")
            
            # Log the error
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                INSERT INTO token_log (account_id, event_type, status, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    account_id, 
                    'save', 
                    'failed', 
                    datetime.now().isoformat(),
                    f"Error: {str(e)}"
                ))
                self.conn.commit()
            except:
                pass
            
            return False
    
    def get_tokens(self, account_id):
        """Get tokens for an account"""
        try:
            # Generate token filename
            token_file = os.path.join(self.tokens_dir, f"account_{account_id}_tokens.json")
            
            # Check if file exists
            if not os.path.exists(token_file):
                return None
            
            # Read tokens from file
            with open(token_file, 'r') as f:
                tokens_data = json.load(f)
            
            # Update last check time
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE accounts 
            SET last_token_check = ? 
            WHERE id = ?
            """, (datetime.now().isoformat(), account_id))
            self.conn.commit()
            
            return tokens_data
        
        except Exception as e:
            logging.error(f"Failed to get tokens for account {account_id}: {e}")
            return None
    
    def get_cookies(self, account_id):
        """Get cookies for an account"""
        try:
            # Generate cookie filename
            cookie_file = os.path.join(self.tokens_dir, f"account_{account_id}_cookies.pkl")
            
            # Check if file exists
            if not os.path.exists(cookie_file):
                return None
            
            # Read cookies from file
            with open(cookie_file, 'rb') as f:
                cookies = pickle.load(f)
            
            return cookies
        
        except Exception as e:
            logging.error(f"Failed to get cookies for account {account_id}: {e}")
            return None
    
    def verify_token(self, account_id):
        """Verify if a token is still valid"""
        try:
            # Get the tokens
            tokens = self.get_tokens(account_id)
            if not tokens:
                return False
            
            # In a real implementation, this would make an API call to verify the token
            # For now, we'll just check if the token file exists
            
            # This is where you would add TextNow API verification
            # Example:
            # response = requests.get(
            #     "https://api.textnow.com/api/v1/user/profile",
            #     headers={"Authorization": f"Bearer {tokens['access_token']}"}
            # )
            # is_valid = response.status_code == 200
            
            # For demo purposes, we'll assume it's valid if we have it
            is_valid = True
            
            # Update token status
            status = 'valid' if is_valid else 'invalid'
            cursor = self.conn.cursor()
            cursor.execute("""
            UPDATE accounts 
            SET token_status = ?, last_token_check = ? 
            WHERE id = ?
            """, (status, datetime.now().isoformat(), account_id))
            
            # Log the verification
            cursor.execute("""
            INSERT INTO token_log (account_id, event_type, status, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """, (
                account_id, 
                'verify', 
                status, 
                datetime.now().isoformat(),
                f"Token verification for account {account_id}: {status}"
            ))
            
            self.conn.commit()
            
            return is_valid
        
        except Exception as e:
            logging.error(f"Failed to verify token for account {account_id}: {e}")
            return False
    
    def refresh_token(self, account_id):
        """Refresh an expired token"""
        try:
            # Get the tokens
            tokens = self.get_tokens(account_id)
            if not tokens or 'refresh_token' not in tokens:
                return False
            
            # In a real implementation, this would make an API call to refresh the token
            # Example:
            # response = requests.post(
            #     "https://api.textnow.com/api/v1/oauth/token",
            #     data={
            #         "grant_type": "refresh_token",
            #         "refresh_token": tokens['refresh_token']
            #     }
            # )
            # 
            # if response.status_code == 200:
            #     new_tokens = response.json()
            #     self.save_tokens(account_id, new_tokens)
            #     return True
            
            # For demo purposes, we'll just simulate a refresh
            tokens['access_token'] = f"refreshed_token_{int(time.time())}"
            self.save_tokens(account_id, tokens)
            
            # Log the refresh
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO token_log (account_id, event_type, status, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """, (
                account_id, 
                'refresh', 
                'success', 
                datetime.now().isoformat(),
                f"Token refreshed for account {account_id}"
            ))
            self.conn.commit()
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to refresh token for account {account_id}: {e}")
            
            # Log the error
            try:
                cursor = self.conn.cursor()
                cursor.execute("""
                INSERT INTO token_log (account_id, event_type, status, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
                """, (
                    account_id, 
                    'refresh', 
                    'failed', 
                    datetime.now().isoformat(),
                    f"Error: {str(e)}"
                ))
                self.conn.commit()
            except:
                pass
            
            return False
    
    def get_account_status(self, account_id):
        """Get the token status for an account"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT token_status, last_token_update, last_token_check
            FROM accounts
            WHERE id = ?
            """, (account_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'status': row['token_status'],
                    'last_update': row['last_token_update'],
                    'last_check': row['last_token_check']
                }
            
            return None
        
        except Exception as e:
            logging.error(f"Failed to get token status for account {account_id}: {e}")
            return None
    
    def get_accounts_needing_refresh(self):
        """Get accounts with tokens that need to be refreshed"""
        try:
            cursor = self.conn.cursor()
            
            # Get accounts with invalid tokens or ones that haven't been checked in 24 hours
            cursor.execute("""
            SELECT id FROM accounts
            WHERE token_status = 'invalid' 
            OR last_token_check IS NULL
            OR datetime(last_token_check) < datetime('now', '-1 day')
            """)
            
            accounts = cursor.fetchall()
            return [account['id'] for account in accounts]
        
        except Exception as e:
            logging.error(f"Failed to get accounts needing refresh: {e}")
            return []
    
    def _token_check_thread(self):
        """Background thread to periodically check and refresh tokens"""
        while self.running:
            try:
                # Get accounts needing refresh
                accounts = self.get_accounts_needing_refresh()
                
                for account_id in accounts:
                    # Verify and refresh if needed
                    if not self.verify_token(account_id):
                        self.refresh_token(account_id)
                
                # Log check completed
                logging.debug(f"Token check completed for {len(accounts)} accounts")
            
            except Exception as e:
                logging.error(f"Error in token check thread: {e}")
            
            # Sleep for an hour before next check
            time.sleep(3600)
    
    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.conn:
            self.conn.close()

# Singleton instance
_token_manager = None

def get_token_manager():
    """Get the token manager singleton instance"""
    global _token_manager
    if _token_manager is None:
        _token_manager = TokenManager()
    return _token_manager