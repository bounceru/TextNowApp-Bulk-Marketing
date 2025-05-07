import os
import io
import uuid
import sqlite3
import logging
import random
import time
import hashlib
from pathlib import Path
from datetime import datetime

# Conditionally import audio libraries to avoid dependency errors
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available, text-to-speech features will be disabled")

try:
    from pydub import AudioSegment
    from pydub.playback import play
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available, audio playback features will be disabled")

class AudioManager:
    def __init__(self, voicemail_folder="voicemail", custom_voicemail_folder=None, db_path="ghost_accounts.db"):
        self.voicemail_folder = voicemail_folder
        self.custom_voicemail_folder = custom_voicemail_folder
        self.db_path = db_path
        
        # Create default folder
        os.makedirs(voicemail_folder, exist_ok=True)
        
        # Create/connect to the database for voicemail usage tracking
        self._init_database()
        
        # Initialize text-to-speech engine if available
        self.tts_engine = None
        if PYTTSX3_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
            except Exception as e:
                logging.error(f"Error initializing text-to-speech engine: {e}")
    
    def _init_database(self):
        """Initialize the database connection and create tables if needed"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create a table to track voicemail usage
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS voicemail_usage (
                    voicemail_id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    source TEXT NOT NULL,
                    last_used TIMESTAMP,
                    use_count INTEGER DEFAULT 0,
                    account_id TEXT,
                    checksum TEXT
                )
            ''')
            
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error initializing voicemail database: {e}")
            self.conn = None
    
    def get_voicemail_files(self, include_custom=True):
        """Get list of available voicemail files"""
        files = []
        
        # Get files from the default folder
        try:
            default_files = [os.path.join(self.voicemail_folder, f) for f in os.listdir(self.voicemail_folder) 
                           if f.lower().endswith(('.mp3', '.wav'))]
            files.extend(default_files)
        except Exception as e:
            logging.error(f"Error listing default voicemail files: {e}")
        
        # Get files from the custom folder if specified
        if include_custom and self.custom_voicemail_folder and os.path.exists(self.custom_voicemail_folder):
            try:
                custom_files = [os.path.join(self.custom_voicemail_folder, f) for f in os.listdir(self.custom_voicemail_folder) 
                              if f.lower().endswith(('.mp3', '.wav'))]
                files.extend(custom_files)
            except Exception as e:
                logging.error(f"Error listing custom voicemail files: {e}")
        
        return files
    
    def import_custom_voicemails(self, custom_folder=None):
        """Import and track custom voicemails from the specified folder"""
        if custom_folder:
            self.custom_voicemail_folder = custom_folder
        
        if not self.custom_voicemail_folder or not os.path.exists(self.custom_voicemail_folder):
            logging.error(f"Custom voicemail folder not found: {self.custom_voicemail_folder}")
            return 0
        
        if not self.conn:
            logging.error("Database connection not available")
            return 0
        
        # Get list of audio files
        try:
            files = [f for f in os.listdir(self.custom_voicemail_folder) 
                   if f.lower().endswith(('.mp3', '.wav'))]
            
            # Add each file to the database if not already present
            count = 0
            for filename in files:
                file_path = os.path.join(self.custom_voicemail_folder, filename)
                
                # Calculate file checksum to identify duplicates
                checksum = self._calculate_file_checksum(file_path)
                
                # Check if file already exists in database
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT voicemail_id FROM voicemail_usage WHERE checksum = ?", 
                    (checksum,)
                )
                existing = cursor.fetchone()
                
                if not existing:
                    # Generate a unique ID for the voicemail
                    voicemail_id = str(uuid.uuid4())
                    
                    # Add to database
                    cursor.execute(
                        """INSERT INTO voicemail_usage 
                           (voicemail_id, filename, source, last_used, use_count, checksum) 
                           VALUES (?, ?, ?, NULL, 0, ?)""",
                        (voicemail_id, filename, "custom", checksum)
                    )
                    count += 1
            
            self.conn.commit()
            logging.info(f"Imported {count} new custom voicemails")
            return count
        
        except Exception as e:
            logging.error(f"Error importing custom voicemails: {e}")
            return 0
    
    def _calculate_file_checksum(self, file_path):
        """Calculate a checksum for a file to identify duplicates"""
        if not os.path.exists(file_path):
            return None
        
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logging.error(f"Error calculating file checksum: {e}")
            return None
    
    def get_random_voicemail(self, prioritize_unused=True, max_uses=3):
        """Get a random voicemail file path with smart selection
        
        Args:
            prioritize_unused: Whether to prioritize voicemails that haven't been used yet
            max_uses: Maximum number of times a voicemail should be used before deprioritizing
            
        Returns:
            Path to the selected voicemail file
        """
        if not self.conn:
            # If database not available, fall back to simple random selection
            files = self.get_voicemail_files()
            if not files:
                logging.warning("No voicemail files found")
                return None
            
            random_file = random.choice(files)
            return random_file
        
        try:
            cursor = self.conn.cursor()
            
            if prioritize_unused:
                # First try to find voicemails that haven't been used yet
                cursor.execute(
                    """SELECT voicemail_id, filename, source 
                       FROM voicemail_usage 
                       WHERE use_count = 0 
                       ORDER BY RANDOM() 
                       LIMIT 1"""
                )
                unused = cursor.fetchone()
                
                if unused:
                    voicemail_id, filename, source = unused
                    folder = self.custom_voicemail_folder if source == "custom" else self.voicemail_folder
                    file_path = os.path.join(folder, filename)
                    
                    if os.path.exists(file_path):
                        # Update usage statistics
                        self._log_voicemail_use(voicemail_id)
                        return file_path
            
            # If no unused voicemails or prioritize_unused is False, select one with use_count < max_uses
            cursor.execute(
                """SELECT voicemail_id, filename, source 
                   FROM voicemail_usage 
                   WHERE use_count < ? 
                   ORDER BY use_count ASC, RANDOM() 
                   LIMIT 1""",
                (max_uses,)
            )
            result = cursor.fetchone()
            
            if result:
                voicemail_id, filename, source = result
                folder = self.custom_voicemail_folder if source == "custom" else self.voicemail_folder
                file_path = os.path.join(folder, filename)
                
                if os.path.exists(file_path):
                    # Update usage statistics
                    self._log_voicemail_use(voicemail_id)
                    return file_path
            
            # If all voicemails have been used more than max_uses, just pick a random one
            cursor.execute(
                """SELECT voicemail_id, filename, source 
                   FROM voicemail_usage 
                   ORDER BY RANDOM() 
                   LIMIT 1"""
            )
            result = cursor.fetchone()
            
            if result:
                voicemail_id, filename, source = result
                folder = self.custom_voicemail_folder if source == "custom" else self.voicemail_folder
                file_path = os.path.join(folder, filename)
                
                if os.path.exists(file_path):
                    # Update usage statistics
                    self._log_voicemail_use(voicemail_id)
                    return file_path
            
            # Fallback to simple random selection if database approach failed
            files = self.get_voicemail_files()
            if not files:
                logging.warning("No voicemail files found")
                return None
            
            random_file = random.choice(files)
            return random_file
            
        except Exception as e:
            logging.error(f"Error selecting random voicemail: {e}")
            
            # Fallback to simple random selection
            files = self.get_voicemail_files()
            if not files:
                logging.warning("No voicemail files found")
                return None
            
            random_file = random.choice(files)
            return random_file
    
    def _log_voicemail_use(self, voicemail_id, account_id=None):
        """Log the use of a voicemail"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            # Update usage count and timestamp
            cursor.execute(
                """UPDATE voicemail_usage 
                   SET use_count = use_count + 1, last_used = ?, account_id = ? 
                   WHERE voicemail_id = ?""",
                (now, account_id, voicemail_id)
            )
            self.conn.commit()
        except Exception as e:
            logging.error(f"Error logging voicemail use: {e}")
    
    def assign_voicemail_to_account(self, account_id, voicemail_path=None):
        """Assign a voicemail to an account. If no voicemail_path is provided, select a random one."""
        if not voicemail_path:
            voicemail_path = self.get_random_voicemail()
        
        if not voicemail_path:
            logging.error("No voicemail available to assign")
            return None
        
        if not self.conn:
            return voicemail_path
        
        try:
            # Find the voicemail ID from the path
            filename = os.path.basename(voicemail_path)
            cursor = self.conn.cursor()
            
            cursor.execute(
                "SELECT voicemail_id FROM voicemail_usage WHERE filename = ?",
                (filename,)
            )
            result = cursor.fetchone()
            
            if result:
                voicemail_id = result[0]
                # Update the account_id for this voicemail
                self._log_voicemail_use(voicemail_id, account_id)
            
            return voicemail_path
            
        except Exception as e:
            logging.error(f"Error assigning voicemail to account: {e}")
            return voicemail_path
    
    def create_tts_voicemail(self, text, filename=None):
        """Create a voicemail greeting using text-to-speech"""
        if not self.tts_engine:
            logging.error("Text-to-speech engine not available")
            return None
        
        try:
            # Generate a filename if not provided
            if not filename:
                timestamp = int(time.time())
                filename = f"voicemail_{timestamp}.mp3"
            
            # Ensure the filename has the right extension
            if not filename.lower().endswith('.mp3'):
                filename += '.mp3'
            
            # Full path
            full_path = os.path.join(self.voicemail_folder, filename)
            
            # Generate and save the audio
            self.tts_engine.save_to_file(text, full_path)
            self.tts_engine.runAndWait()
            
            logging.info(f"Created TTS voicemail: {full_path}")
            return full_path
        
        except Exception as e:
            logging.error(f"Error creating TTS voicemail: {e}")
            return None
    
    def play_audio_file(self, file_path, block=True):
        """Play an audio file"""
        if not PYDUB_AVAILABLE:
            logging.error("pydub not available, cannot play audio")
            return False
        
        try:
            if not os.path.exists(file_path):
                logging.error(f"Audio file not found: {file_path}")
                return False
            
            # Determine file type
            if file_path.lower().endswith('.mp3'):
                audio = AudioSegment.from_mp3(file_path)
            elif file_path.lower().endswith('.wav'):
                audio = AudioSegment.from_wav(file_path)
            else:
                logging.error(f"Unsupported audio format: {file_path}")
                return False
            
            # Play the audio
            logging.info(f"Playing audio: {file_path}")
            if block:
                play(audio)
            else:
                # For non-blocking playback, use a separate thread
                import threading
                threading.Thread(target=play, args=(audio,)).start()
            
            return True
        
        except Exception as e:
            logging.error(f"Error playing audio: {e}")
            return False
    
    def generate_default_voicemails(self):
        """Generate a set of default voicemail greetings if folder is empty"""
        if not self.tts_engine:
            logging.error("Text-to-speech engine not available, cannot generate default voicemails")
            return
        
        # Check if folder is empty
        if self.get_voicemail_files():
            return  # Already has files
        
        # Default greetings
        greetings = [
            "Hi, you've reached my voicemail. Please leave a message after the tone and I'll get back to you as soon as possible.",
            "Hello, I can't take your call right now. Please leave your name, number, and a brief message, and I'll return your call.",
            "Sorry I missed your call. Leave a message and I'll call you back when I'm available.",
            "Thanks for calling. I'm not available right now, but if you leave a message, I'll return your call shortly.",
            "You've reached my voicemail. I'm either away from my phone or on another call. Please leave a message."
        ]
        
        # Generate voices with different parameters
        voices = self.tts_engine.getProperty('voices')
        
        for i, greeting in enumerate(greetings):
            # Alternate voices if multiple are available
            if voices and len(voices) > 1:
                voice_index = i % len(voices)
                self.tts_engine.setProperty('voice', voices[voice_index].id)
            
            # Vary rate and volume slightly
            rate = self.tts_engine.getProperty('rate')
            volume = self.tts_engine.getProperty('volume')
            
            # Adjust rate by ±10%
            rate_adjust = random.uniform(0.9, 1.1)
            self.tts_engine.setProperty('rate', rate * rate_adjust)
            
            # Adjust volume by ±20%
            volume_adjust = random.uniform(0.8, 1.0)
            self.tts_engine.setProperty('volume', volume * volume_adjust)
            
            # Create the voicemail
            filename = f"default_greeting_{i+1}.mp3"
            self.create_tts_voicemail(greeting, filename)
            
        logging.info("Generated default voicemail greetings")
