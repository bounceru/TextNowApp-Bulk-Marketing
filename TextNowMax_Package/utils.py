import os
import sys
import logging
import random
import string
import time
from datetime import datetime

def setup_logger(log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """Setup logger with console and file handlers"""
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file is provided)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def generate_random_string(length=10, include_digits=True, include_special=False):
    """Generate a random string of specified length"""
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    if include_special:
        chars += string.punctuation
    
    return ''.join(random.choice(chars) for _ in range(length))

def generate_random_email():
    """Generate a random email address"""
    username = generate_random_string(8, include_digits=True)
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
    domain = random.choice(domains)
    
    return f"{username}@{domain}"

def generate_strong_password():
    """Generate a strong random password"""
    # At least 8 characters with mix of letters, numbers, and special chars
    length = random.randint(10, 14)
    password = generate_random_string(length, include_digits=True, include_special=True)
    
    # Ensure it has at least one uppercase, one lowercase, one digit and one special char
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in string.punctuation for c in password)
    
    if not (has_upper and has_lower and has_digit and has_special):
        # If missing any requirement, regenerate
        return generate_strong_password()
    
    return password

def wait_with_progress(seconds, message=None, callback=None):
    """Wait with progress updates"""
    if message:
        logging.info(message)
    
    start = time.time()
    end = start + seconds
    
    while time.time() < end:
        elapsed = time.time() - start
        remaining = seconds - elapsed
        percent = (elapsed / seconds) * 100
        
        if callback:
            callback(percent, remaining)
        
        time.sleep(1)

def timestamp():
    """Get current timestamp in a readable format"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def safe_filename(name):
    """Convert a string to a safe filename"""
    # Replace spaces, remove invalid characters
    safe_chars = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    return ''.join(c for c in name if c in safe_chars).replace(' ', '_')
