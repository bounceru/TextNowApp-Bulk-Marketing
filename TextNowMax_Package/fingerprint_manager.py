"""
Fingerprint Manager for ProgressGhostCreator

This module handles the creation, storage, and application of browser fingerprints
for TextNow accounts. Each account maintains a consistent fingerprint across sessions
to avoid detection.
"""

import os
import json
import random
import hashlib
import sqlite3
import logging
import uuid
import platform
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fingerprint_manager.log"),
        logging.StreamHandler()
    ]
)

class FingerprintManager:
    """Manager class for browser fingerprints"""
    
    def __init__(self, db_path: str = "fingerprints.db"):
        """
        Initialize the fingerprint manager
        
        Args:
            db_path: Path to the SQLite database file for storing fingerprints
        """
        self.db_path = db_path
        self._connect_database()
        self.user_agents = self._load_user_agents()
        self.screen_resolutions = self._load_screen_resolutions()
        self.timezone_offsets = self._load_timezone_offsets()
        self.languages = self._load_languages()
        self.font_families = self._load_font_families()
        
    def _connect_database(self) -> None:
        """Connect to the fingerprints database"""
        try:
            # Create database if it doesn't exist
            db_exists = os.path.exists(self.db_path)
            
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            
            if not db_exists:
                self._create_tables()
            
            logging.info(f"Connected to fingerprints database at {self.db_path}")
        except Exception as e:
            logging.error(f"Failed to connect to database: {str(e)}")
            raise
    
    def _create_tables(self) -> None:
        """Create necessary tables in the database"""
        cursor = self.conn.cursor()
        
        # Fingerprints table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS fingerprints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER UNIQUE,
            user_agent TEXT,
            screen_width INTEGER,
            screen_height INTEGER,
            color_depth INTEGER,
            timezone_offset INTEGER,
            language TEXT,
            platform TEXT,
            do_not_track INTEGER,
            hardware_concurrency INTEGER,
            device_memory INTEGER,
            canvas_fingerprint TEXT,
            webgl_fingerprint TEXT,
            audio_fingerprint TEXT,
            fonts TEXT,
            plugins TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_fingerprints_account_id ON fingerprints (account_id)')
        
        self.conn.commit()
        logging.info("Created fingerprints database tables")
    
    def _load_user_agents(self) -> List[str]:
        """Load list of realistic user agents"""
        # Common mobile user agents (focusing on Android for the BLU G44)
        return [
            # Chrome on Android
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.87 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.73 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Mobile Safari/537.36",
            
            # Firefox on Android
            "Mozilla/5.0 (Android 10; Mobile; rv:96.0; BLU G44) Gecko/96.0 Firefox/96.0",
            "Mozilla/5.0 (Android 10; Mobile; rv:97.0; BLU G44) Gecko/97.0 Firefox/97.0",
            "Mozilla/5.0 (Android 10; Mobile; rv:98.0; BLU G44) Gecko/98.0 Firefox/98.0",
            
            # Samsung Browser on Android
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/16.0 Chrome/92.0.4515.166 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/16.2 Chrome/92.0.4515.166 Mobile Safari/537.36",
            
            # Opera on Android
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.104 Mobile Safari/537.36 OPR/65.2.3381.61420",
            "Mozilla/5.0 (Linux; Android 10; BLU G44) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.87 Mobile Safari/537.36 OPR/66.0.3445.62346"
        ]
    
    def _load_screen_resolutions(self) -> List[Tuple[int, int]]:
        """Load list of common mobile screen resolutions"""
        return [
            (360, 640),   # Common mobile resolution
            (375, 667),   # iPhone 6/7/8
            (360, 740),   # Samsung Galaxy S8/S9
            (360, 760),   # Many budget Android devices
            (412, 846),   # Pixel 2
            (414, 896),   # iPhone XR/11
            (360, 780),   # Many mid-range Android devices
            (720, 1280),  # Higher density mobile display
            (320, 568),   # iPhone 5/SE
            (480, 854),   # Common on budget phones like BLU G44
            (540, 960),   # Common qHD resolution
            (600, 1024),  # Small tablet
        ]
    
    def _load_timezone_offsets(self) -> List[int]:
        """Load list of common US timezone offsets (in minutes)"""
        return [
            -300,  # EST
            -360,  # CST
            -420,  # MST
            -480,  # PST
            -240,  # AST (e.g., Puerto Rico)
            -600,  # AKST (Alaska)
            -540,  # Hawaiian Time
        ]
    
    def _load_languages(self) -> List[str]:
        """Load list of common browser language settings"""
        return [
            "en-US",
            "en-US,en;q=0.9",
            "en-US,en;q=0.8,es;q=0.6",
            "en-US,en;q=0.8",
            "en-US,en;q=0.9,es-US;q=0.8,es;q=0.7",
            "es-US,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "en-US,en;q=0.9,fr;q=0.8",
            "en",
        ]
    
    def _load_font_families(self) -> List[List[str]]:
        """Load lists of font families commonly available on Android"""
        android_fonts = [
            "Roboto", "Droid Sans", "Droid Serif", "Droid Sans Mono",
            "Dancing Script", "Carrois Gothic SC", "Coming Soon", "Cutive Mono",
            "Open Sans", "Roboto Condensed", "Lato", "Oswald", "Source Sans Pro",
            "PT Sans", "Ubuntu", "Noto Sans", "Noto Serif"
        ]
        
        # Create different font lists as combinations
        result = []
        for _ in range(10):
            # Shuffle and pick a random subset
            fonts = android_fonts.copy()
            random.shuffle(fonts)
            num_fonts = random.randint(7, len(fonts))
            result.append(fonts[:num_fonts])
            
        return result
    
    def get_random_fingerprint(self, account_id: int = None) -> Dict[str, Any]:
        """
        Generate a random browser fingerprint
        
        Args:
            account_id: Optional account ID to associate with this fingerprint
            
        Returns:
            Dictionary containing fingerprint properties
        """
        # User agent
        user_agent = random.choice(self.user_agents)
        
        # Screen properties
        screen_width, screen_height = random.choice(self.screen_resolutions)
        color_depth = random.choice([24, 32])
        
        # System properties
        timezone_offset = random.choice(self.timezone_offsets)
        language = random.choice(self.languages)
        platform = "Android"
        do_not_track = random.choice([0, 1])
        hardware_concurrency = random.choice([2, 4, 6, 8])
        device_memory = random.choice([2, 4])
        
        # Canvas fingerprint (a hash that would normally come from rendering a canvas)
        canvas_hash = hashlib.md5(f"{account_id or random.random()}_{time.time()}".encode()).hexdigest()
        
        # WebGL fingerprint
        webgl_hash = hashlib.md5(f"{canvas_hash}_{random.random()}".encode()).hexdigest()
        
        # Audio fingerprint
        audio_hash = hashlib.md5(f"{webgl_hash}_{random.random()}".encode()).hexdigest()
        
        # Fonts
        fonts = random.choice(self.font_families)
        
        # Plugins (mobile browsers typically have limited or no plugins)
        plugins = []
        
        # Combine into a fingerprint
        fingerprint = {
            "account_id": account_id,
            "user_agent": user_agent,
            "screen_width": screen_width,
            "screen_height": screen_height,
            "color_depth": color_depth,
            "timezone_offset": timezone_offset,
            "language": language,
            "platform": platform,
            "do_not_track": do_not_track,
            "hardware_concurrency": hardware_concurrency,
            "device_memory": device_memory,
            "canvas_fingerprint": canvas_hash,
            "webgl_fingerprint": webgl_hash,
            "audio_fingerprint": audio_hash,
            "fonts": json.dumps(fonts),
            "plugins": json.dumps(plugins),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return fingerprint
    
    def generate_account_fingerprint(self, account_id: int) -> Dict[str, Any]:
        """
        Generate and store a new fingerprint for an account
        
        Args:
            account_id: Account ID to generate a fingerprint for
            
        Returns:
            Dictionary containing the new fingerprint
        """
        fingerprint = self.get_random_fingerprint(account_id)
        self.save_account_fingerprint(account_id, fingerprint)
        return fingerprint
    
    def save_account_fingerprint(self, account_id: int, fingerprint: Dict[str, Any]) -> bool:
        """
        Save a fingerprint for an account
        
        Args:
            account_id: Account ID
            fingerprint: Fingerprint data
            
        Returns:
            Success boolean
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if a fingerprint already exists for this account
            cursor.execute("SELECT id FROM fingerprints WHERE account_id = ?", (account_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing fingerprint
                cursor.execute('''
                UPDATE fingerprints SET
                    user_agent = ?,
                    screen_width = ?,
                    screen_height = ?,
                    color_depth = ?,
                    timezone_offset = ?,
                    language = ?,
                    platform = ?,
                    do_not_track = ?,
                    hardware_concurrency = ?,
                    device_memory = ?,
                    canvas_fingerprint = ?,
                    webgl_fingerprint = ?,
                    audio_fingerprint = ?,
                    fonts = ?,
                    plugins = ?,
                    updated_at = ?
                WHERE account_id = ?
                ''', (
                    fingerprint.get("user_agent"),
                    fingerprint.get("screen_width"),
                    fingerprint.get("screen_height"),
                    fingerprint.get("color_depth"),
                    fingerprint.get("timezone_offset"),
                    fingerprint.get("language"),
                    fingerprint.get("platform"),
                    fingerprint.get("do_not_track"),
                    fingerprint.get("hardware_concurrency"),
                    fingerprint.get("device_memory"),
                    fingerprint.get("canvas_fingerprint"),
                    fingerprint.get("webgl_fingerprint"),
                    fingerprint.get("audio_fingerprint"),
                    fingerprint.get("fonts"),
                    fingerprint.get("plugins"),
                    datetime.now().isoformat(),
                    account_id
                ))
            else:
                # Insert new fingerprint
                cursor.execute('''
                INSERT INTO fingerprints (
                    account_id,
                    user_agent,
                    screen_width,
                    screen_height,
                    color_depth,
                    timezone_offset,
                    language,
                    platform,
                    do_not_track,
                    hardware_concurrency,
                    device_memory,
                    canvas_fingerprint,
                    webgl_fingerprint,
                    audio_fingerprint,
                    fonts,
                    plugins,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    fingerprint.get("user_agent"),
                    fingerprint.get("screen_width"),
                    fingerprint.get("screen_height"),
                    fingerprint.get("color_depth"),
                    fingerprint.get("timezone_offset"),
                    fingerprint.get("language"),
                    fingerprint.get("platform"),
                    fingerprint.get("do_not_track"),
                    fingerprint.get("hardware_concurrency"),
                    fingerprint.get("device_memory"),
                    fingerprint.get("canvas_fingerprint"),
                    fingerprint.get("webgl_fingerprint"),
                    fingerprint.get("audio_fingerprint"),
                    fingerprint.get("fonts"),
                    fingerprint.get("plugins"),
                    fingerprint.get("created_at", datetime.now().isoformat()),
                    fingerprint.get("updated_at", datetime.now().isoformat())
                ))
            
            self.conn.commit()
            logging.info(f"Saved fingerprint for account ID: {account_id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to save fingerprint for account {account_id}: {str(e)}")
            return False
    
    def get_account_fingerprint(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Get the stored fingerprint for an account
        
        Args:
            account_id: Account ID
            
        Returns:
            Dictionary containing the fingerprint or None if not found
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT * FROM fingerprints WHERE account_id = ?", (account_id,))
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Convert Row to dictionary
            fingerprint = {key: result[key] for key in result.keys()}
            
            # Parse JSON strings
            if "fonts" in fingerprint and fingerprint["fonts"]:
                fingerprint["fonts"] = json.loads(fingerprint["fonts"])
            
            if "plugins" in fingerprint and fingerprint["plugins"]:
                fingerprint["plugins"] = json.loads(fingerprint["plugins"])
            
            return fingerprint
            
        except Exception as e:
            logging.error(f"Failed to get fingerprint for account {account_id}: {str(e)}")
            return None
    
    def get_or_create_fingerprint(self, account_id: int) -> Dict[str, Any]:
        """
        Get an existing fingerprint or create a new one if none exists
        
        Args:
            account_id: Account ID
            
        Returns:
            Dictionary containing the fingerprint
        """
        fingerprint = self.get_account_fingerprint(account_id)
        
        if not fingerprint:
            fingerprint = self.generate_account_fingerprint(account_id)
        
        return fingerprint
    
    def batch_update_fingerprints(self, account_ids: List[int]) -> Dict[str, Any]:
        """
        Update multiple accounts with related fingerprints (same IP family)
        
        Args:
            account_ids: List of account IDs to update
            
        Returns:
            Dictionary with results: {"success_count": int, "failure_count": int}
        """
        success_count = 0
        failure_count = 0
        
        if not account_ids:
            return {"success_count": 0, "failure_count": 0}
        
        # Generate a base fingerprint to share common elements
        base_fingerprint = self.get_random_fingerprint()
        
        # User agent (use the same browser but with variations)
        base_ua = base_fingerprint["user_agent"]
        
        # Common platform settings to make the accounts seem related
        platform = base_fingerprint["platform"]
        device_memory = base_fingerprint["device_memory"]
        color_depth = base_fingerprint["color_depth"]
        
        for account_id in account_ids:
            # Start with the base fingerprint
            fingerprint = base_fingerprint.copy()
            
            # Modify fingerprint with account-specific variations
            fingerprint["account_id"] = account_id
            
            # Slight variations in user agent to make it look like the same device but different sessions
            if "Chrome/" in base_ua:
                # Modify Chrome version slightly
                chrome_ver = base_ua.split("Chrome/")[1].split(" ")[0]
                major, minor_full = chrome_ver.split(".")
                minor_parts = minor_full.split(".")
                if len(minor_parts) > 1:
                    minor, build = minor_parts[0], ".".join(minor_parts[1:])
                    new_build = str(int(build.split(".")[0]) + random.randint(-2, 2))
                    new_chrome_ver = f"{major}.{minor}.{new_build}"
                    fingerprint["user_agent"] = base_ua.replace(f"Chrome/{chrome_ver}", f"Chrome/{new_chrome_ver}")
            
            # Screen resolution (minor variations to simulate different device settings)
            width, height = base_fingerprint["screen_width"], base_fingerprint["screen_height"]
            fingerprint["screen_width"] = width + random.choice([-5, 0, 5, 10])
            fingerprint["screen_height"] = height + random.choice([-10, 0, 10, 20])
            
            # Generate unique canvas/WebGL/audio fingerprints
            fingerprint["canvas_fingerprint"] = hashlib.md5(f"{account_id}_{time.time()}".encode()).hexdigest()
            fingerprint["webgl_fingerprint"] = hashlib.md5(f"{fingerprint['canvas_fingerprint']}_{random.random()}".encode()).hexdigest()
            fingerprint["audio_fingerprint"] = hashlib.md5(f"{fingerprint['webgl_fingerprint']}_{random.random()}".encode()).hexdigest()
            
            # Save the fingerprint
            if self.save_account_fingerprint(account_id, fingerprint):
                success_count += 1
            else:
                failure_count += 1
        
        return {
            "success_count": success_count,
            "failure_count": failure_count
        }
    
    def get_accounts_with_fingerprints(self) -> List[int]:
        """
        Get a list of all accounts that have fingerprints
        
        Returns:
            List of account IDs
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT account_id FROM fingerprints")
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Failed to get accounts with fingerprints: {str(e)}")
            return []
    
    def delete_fingerprint(self, account_id: int) -> bool:
        """
        Delete a fingerprint for an account
        
        Args:
            account_id: Account ID
            
        Returns:
            Success boolean
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM fingerprints WHERE account_id = ?", (account_id,))
            self.conn.commit()
            return cursor.rowcount > 0
        except Exception as e:
            logging.error(f"Failed to delete fingerprint for account {account_id}: {str(e)}")
            return False
    
    def close(self) -> None:
        """Close the database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()


# Singleton instance
_fingerprint_manager = None

def get_fingerprint_manager():
    """Get the singleton fingerprint manager instance"""
    global _fingerprint_manager
    if _fingerprint_manager is None:
        _fingerprint_manager = FingerprintManager()
    return _fingerprint_manager


# Example usage
if __name__ == "__main__":
    manager = get_fingerprint_manager()
    
    # Generate a random fingerprint
    print("Random Fingerprint:")
    fingerprint = manager.get_random_fingerprint()
    print(json.dumps(fingerprint, indent=2))
    
    # Test with account ID
    account_id = 12345
    print(f"\nGenerating fingerprint for account {account_id}")
    fingerprint = manager.generate_account_fingerprint(account_id)
    
    # Retrieve the fingerprint
    print(f"\nRetrieving fingerprint for account {account_id}")
    retrieved = manager.get_account_fingerprint(account_id)
    if retrieved:
        print("Retrieved successfully!")
    
    # Batch update
    print("\nBatch updating fingerprints for related accounts")
    results = manager.batch_update_fingerprints([12346, 12347, 12348])
    print(f"Batch update results: {results}")
    
    # Clean up
    manager.close()