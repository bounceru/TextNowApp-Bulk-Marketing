"""
Create and initialize the database for ProgressGhostCreator
"""

import os
import sqlite3
import csv
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_database():
    """Create SQLite database and tables"""
    try:
        # Create the database connection
        conn = sqlite3.connect('ghost_accounts.db')
        cursor = conn.cursor()
        
        # Create accounts table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL,
            password TEXT NOT NULL,
            phone_number TEXT NOT NULL,
            created_at TEXT NOT NULL,
            ip_used TEXT,
            voicemail_file TEXT,
            active BOOLEAN DEFAULT 1,
            last_used TEXT,
            notes TEXT
        )
        ''')
        
        # Create messages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            direction TEXT NOT NULL,  /* 'incoming' or 'outgoing' */
            contact TEXT NOT NULL,
            message_text TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Create a table for campaign tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            messages_sent INTEGER DEFAULT 0,
            messages_failed INTEGER DEFAULT 0
        )
        ''')
        
        # Create a table for campaign accounts (which accounts are used in which campaigns)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_accounts (
            campaign_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            status TEXT NOT NULL,
            PRIMARY KEY (campaign_id, account_id),
            FOREIGN KEY (campaign_id) REFERENCES campaigns(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id)
        )
        ''')
        
        # Commit changes and close connection
        conn.commit()
        logging.info("Database created successfully")
        
        # Import existing accounts if available
        import_from_csv(conn)
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error creating database: {e}")
        return False

def import_from_csv(conn):
    """Import accounts from CSV file if it exists"""
    try:
        if os.path.exists('accounts.csv'):
            with open('accounts.csv', 'r') as file:
                reader = csv.DictReader(file)
                cursor = conn.cursor()
                
                # Get the list of columns from the CSV
                if reader.fieldnames:
                    # Map CSV columns to database columns
                    for row in reader:
                        # Create a dictionary with default values
                        account_data = {
                            'username': row.get('username', ''),
                            'email': row.get('email', ''),
                            'password': row.get('password', ''),
                            'phone_number': row.get('phone_number', ''),
                            'created_at': row.get('created_at', datetime.now().isoformat()),
                            'ip_used': row.get('ip_used', ''),
                            'voicemail_file': row.get('voicemail_file', ''),
                            'active': 1,
                            'last_used': '',
                            'notes': ''
                        }
                        
                        # Insert into database
                        cursor.execute('''
                        INSERT INTO accounts (
                            username, email, password, phone_number, created_at, 
                            ip_used, voicemail_file, active, last_used, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            account_data['username'],
                            account_data['email'],
                            account_data['password'],
                            account_data['phone_number'],
                            account_data['created_at'],
                            account_data['ip_used'],
                            account_data['voicemail_file'],
                            account_data['active'],
                            account_data['last_used'],
                            account_data['notes']
                        ))
                
                conn.commit()
                logging.info(f"Imported accounts from CSV file")
    except Exception as e:
        logging.error(f"Error importing accounts from CSV: {e}")

def create_sample_data():
    """Create sample data for demonstration purposes"""
    try:
        conn = sqlite3.connect('ghost_accounts.db')
        cursor = conn.cursor()
        
        # Check if we already have accounts
        cursor.execute("SELECT COUNT(*) FROM accounts")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Create 25 sample accounts
            for i in range(1, 26):
                cursor.execute('''
                INSERT INTO accounts (
                    username, email, password, phone_number, created_at, 
                    ip_used, voicemail_file, active, last_used, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    f"ghostuser{i}",
                    f"ghost{i}@example.com",
                    f"Password123!{i}",
                    f"(555) {100+i}-{1000+i}",
                    datetime.now().isoformat(),
                    f"192.168.1.{i}",
                    f"voicemail/greeting{i % 10 + 1}.mp3",
                    1,
                    "",
                    "Sample account for testing"
                ))
            
            # Create a sample campaign
            cursor.execute('''
            INSERT INTO campaigns (
                name, description, created_at, status, messages_sent, messages_failed
            ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                "Welcome Campaign",
                "Initial outreach to potential customers",
                datetime.now().isoformat(),
                "active",
                142,
                8
            ))
            
            # Add some accounts to the campaign
            campaign_id = 1
            for account_id in range(1, 11):  # First 10 accounts
                cursor.execute('''
                INSERT INTO campaign_accounts (
                    campaign_id, account_id, status
                ) VALUES (?, ?, ?)
                ''', (
                    campaign_id,
                    account_id,
                    "active"
                ))
            
            # Add some sample messages
            for account_id in range(1, 6):  # First 5 accounts
                # Outgoing message
                cursor.execute('''
                INSERT INTO messages (
                    account_id, direction, contact, message_text, sent_at, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    "outgoing",
                    f"(777) {800+account_id}-{2000+account_id}",
                    "Hey there! Check out our latest offers!",
                    datetime.now().isoformat(),
                    "delivered"
                ))
                
                # Incoming reply
                cursor.execute('''
                INSERT INTO messages (
                    account_id, direction, contact, message_text, sent_at, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    "incoming",
                    f"(777) {800+account_id}-{2000+account_id}",
                    "What kind of offers are you talking about?",
                    datetime.now().isoformat(),
                    "received"
                ))
            
            conn.commit()
            logging.info("Sample data created successfully")
        else:
            logging.info("Database already contains data, skipping sample data creation")
        
        conn.close()
        return True
    
    except Exception as e:
        logging.error(f"Error creating sample data: {e}")
        return False

if __name__ == "__main__":
    create_database()
    create_sample_data()