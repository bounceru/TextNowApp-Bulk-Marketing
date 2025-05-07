import sqlite3
import sys

def fix_database():
    """Fix the database schema by adding missing columns"""
    conn = None
    try:
        # Connect to the database
        conn = sqlite3.connect('ghost_accounts.db')
        cursor = conn.cursor()
        
        # Check if accounts table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accounts'")
        if not cursor.fetchone():
            print("The accounts table doesn't exist yet. No changes made.")
            return
            
        # Check for missing columns
        cursor.execute("PRAGMA table_info(accounts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add missing columns if needed
        if 'last_login' not in columns:
            print("Adding missing column 'last_login' to accounts table")
            cursor.execute('ALTER TABLE accounts ADD COLUMN last_login TIMESTAMP')
        
        if 'last_message_sent' not in columns:
            print("Adding missing column 'last_message_sent' to accounts table")
            cursor.execute('ALTER TABLE accounts ADD COLUMN last_message_sent TIMESTAMP')
        
        if 'last_call' not in columns:
            print("Adding missing column 'last_call' to accounts table")
            cursor.execute('ALTER TABLE accounts ADD COLUMN last_call TIMESTAMP')
            
        # Check if the activity tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='account_activity'")
        if not cursor.fetchone():
            print("Creating account_activity table")
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
            
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_schedule'")
        if not cursor.fetchone():
            print("Creating activity_schedule table")
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
            
        # Commit changes
        conn.commit()
        print("Database schema fixed successfully!")
        
    except Exception as e:
        print(f"Error fixing database: {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("Fixing database schema...")
    fix_database()
