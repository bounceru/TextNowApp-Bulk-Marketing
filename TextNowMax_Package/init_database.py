"""
Initialize the database for TextNow Max

This script creates all the necessary database tables for the TextNow Max application
and ensures that the system is ready to start with empty tables rather than demo data.
"""

import sqlite3
import os
import logging
from datetime import datetime, timedelta

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='database.log'
)
logger = logging.getLogger('database_init')

def init_database(db_path='ghost_accounts.db'):
    """Initialize the database with all necessary tables"""
    try:
        # Check if database exists
        db_exists = os.path.exists(db_path)
        
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create accounts table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
            username TEXT,
            email TEXT,
            password TEXT,
            first_name TEXT,
            last_name TEXT,
            birthdate TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            next_activity TIMESTAMP,
            area_code TEXT,
            status TEXT DEFAULT 'active',
            health_score INTEGER DEFAULT 100,
            session_data TEXT,
            device_fingerprint TEXT,
            notes TEXT
        )
        ''')
        
        # Create messages table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            recipient TEXT,
            content TEXT,
            media_url TEXT,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            campaign_id INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')
        
        # Create campaigns table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            start_date TIMESTAMP,
            end_date TIMESTAMP,
            status TEXT DEFAULT 'draft',
            message_template TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            account_ids TEXT,
            target_numbers TEXT,
            schedule_type TEXT,
            schedule_data TEXT
        )
        ''')
        
        # Create area_codes table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS area_codes (
            area_code TEXT PRIMARY KEY,
            state TEXT,
            region TEXT,
            city TEXT,
            timezone TEXT,
            available INTEGER DEFAULT 1,
            popularity INTEGER DEFAULT 0
        )
        ''')
        
        # Create account_activity_log table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            activity_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            success INTEGER,
            details TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')
        
        # Create account_health_checks table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS account_health_checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER,
            check_type TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            score INTEGER,
            details TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts (id)
        )
        ''')
        
        # Create images table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            description TEXT,
            mime_type TEXT,
            size INTEGER,
            width INTEGER,
            height INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            tags TEXT
        )
        ''')
        
        # Create voicemails table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS voicemails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            description TEXT,
            duration INTEGER,
            size INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            usage_count INTEGER DEFAULT 0,
            transcription TEXT,
            voice_type TEXT
        )
        ''')
        
        # Commit the changes
        conn.commit()
        
        logger.info("Database tables created successfully")
        
        # Check if we should create seed data for testing
        if not db_exists or cursor.execute("SELECT COUNT(*) FROM accounts").fetchone()[0] == 0:
            create_seed_data(conn, cursor)
        
        # Close the connection
        conn.close()
        
        return True
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

def create_seed_data(conn, cursor):
    """Create minimal seed data for testing"""
    try:
        # Insert a few common area codes
        area_codes = [
            ('213', 'California', 'West', 'Los Angeles', 'America/Los_Angeles', 1, 90),
            ('312', 'Illinois', 'Midwest', 'Chicago', 'America/Chicago', 1, 85),
            ('404', 'Georgia', 'Southeast', 'Atlanta', 'America/New_York', 1, 80),
            ('415', 'California', 'West', 'San Francisco', 'America/Los_Angeles', 1, 90),
            ('469', 'Texas', 'Southwest', 'Dallas', 'America/Chicago', 1, 75),
            ('512', 'Texas', 'Southwest', 'Austin', 'America/Chicago', 1, 80),
            ('617', 'Massachusetts', 'Northeast', 'Boston', 'America/New_York', 1, 75),
            ('702', 'Nevada', 'West', 'Las Vegas', 'America/Los_Angeles', 1, 70),
            ('713', 'Texas', 'Southwest', 'Houston', 'America/Chicago', 1, 75),
            ('818', 'California', 'West', 'Los Angeles', 'America/Los_Angeles', 1, 85)
        ]
        
        cursor.executemany('''
        INSERT OR IGNORE INTO area_codes (area_code, state, region, city, timezone, available, popularity)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', area_codes)
        
        conn.commit()
        logger.info("Seed data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating seed data: {e}")
        conn.rollback()

if __name__ == "__main__":
    init_database()
    print("Database initialized successfully.")