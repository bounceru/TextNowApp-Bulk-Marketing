"""
TextNow Account Creator - Selenium Version

This module provides the core functionality for creating TextNow accounts
using Selenium WebDriver and Proxidize proxy management.
"""

import os
import time
import random
import logging
import json
import re
import sqlite3
from datetime import datetime
from typing import Dict, List, Union, Optional, Any, Tuple

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementNotInteractableException,
    StaleElementReferenceException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("selenium_creator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TextNowSelenium")

class Database:
    """Database handler for TextNow accounts"""
    
    def __init__(self, db_path="ghost_accounts.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self._connect()
        self._create_tables()
    
    def _connect(self):
        """Connect to SQLite database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def _create_tables(self):
        """Create necessary database tables if they don't exist"""
        try:
            # Accounts table
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone_number TEXT UNIQUE NOT NULL,
                    username TEXT,
                    name TEXT NOT NULL,
                    email TEXT,
                    password TEXT NOT NULL,
                    area_code TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    last_used TEXT,
                    login_cookie TEXT,
                    user_agent TEXT,
                    ip_used TEXT,
                    notes TEXT
                )
            ''')
            
            # IP Rotation tracking
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS ip_rotations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    old_ip TEXT,
                    new_ip TEXT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    duration REAL,
                    success INTEGER DEFAULT 0
                )
            ''')
            
            # Error tracking
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    error_type TEXT,
                    message TEXT,
                    account_id INTEGER,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def add_account(self, phone_number, name, password, username=None, 
                    email=None, area_code=None, status="active", 
                    login_cookie=None, user_agent=None, ip_used=None, notes=None):
        """Add a new account to the database"""
        try:
            self.cursor.execute('''
                INSERT INTO accounts (
                    phone_number, name, password, username, email, area_code,
                    status, login_cookie, user_agent, ip_used, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                phone_number, name, password, username, email, area_code,
                status, login_cookie, user_agent, ip_used, notes
            ))
            self.conn.commit()
            account_id = self.cursor.lastrowid
            logger.info(f"Account added successfully: {phone_number}")
            return account_id
        except sqlite3.Error as e:
            logger.error(f"Error adding account: {e}")
            self.conn.rollback()
            return None
    
    def get_account(self, account_id=None, phone_number=None):
        """Get account details by ID or phone number"""
        try:
            if account_id:
                self.cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            elif phone_number:
                self.cursor.execute("SELECT * FROM accounts WHERE phone_number = ?", (phone_number,))
            else:
                logger.error("Either account_id or phone_number must be provided")
                return None
                
            account = self.cursor.fetchone()
            return dict(account) if account else None
        except sqlite3.Error as e:
            logger.error(f"Error getting account: {e}")
            return None
    
    def get_all_accounts(self, status=None, limit=100, offset=0):
        """Get all accounts, optionally filtered by status"""
        try:
            if status:
                self.cursor.execute(
                    "SELECT * FROM accounts WHERE status = ? ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                    (status, limit, offset)
                )
            else:
                self.cursor.execute(
                    "SELECT * FROM accounts ORDER BY created_at DESC LIMIT ? OFFSET ?", 
                    (limit, offset)
                )
            
            accounts = self.cursor.fetchall()
            return [dict(account) for account in accounts]
        except sqlite3.Error as e:
            logger.error(f"Error getting accounts: {e}")
            return []
    
    def update_account(self, account_id, **kwargs):
        """Update account details"""
        valid_fields = [
            "phone_number", "username", "name", "email", "password", 
            "area_code", "status", "login_cookie", "user_agent", "ip_used", "notes"
        ]
        
        if not kwargs:
            logger.error("No update fields provided")
            return False
        
        # Filter out invalid fields
        valid_updates = {k: v for k, v in kwargs.items() if k in valid_fields}
        
        if not valid_updates:
            logger.error("No valid update fields provided")
            return False
        
        try:
            # Build the query dynamically
            set_clause = ", ".join([f"{field} = ?" for field in valid_updates.keys()])
            params = list(valid_updates.values()) + [account_id]
            
            query = f"UPDATE accounts SET {set_clause}, last_used = CURRENT_TIMESTAMP WHERE id = ?"
            self.cursor.execute(query, params)
            self.conn.commit()
            
            return self.cursor.rowcount > 0
        except sqlite3.Error as e:
            logger.error(f"Error updating account: {e}")
            self.conn.rollback()
            return False
    
    def log_error(self, error_type, message, account_id=None):
        """Log an error to the database"""
        try:
            self.cursor.execute(
                "INSERT INTO errors (error_type, message, account_id) VALUES (?, ?, ?)",
                (error_type, message, account_id)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging error to database: {e}")
            return False
    
    def log_ip_rotation(self, old_ip, new_ip, duration, success=True):
        """Log an IP rotation event"""
        try:
            self.cursor.execute(
                "INSERT INTO ip_rotations (old_ip, new_ip, duration, success) VALUES (?, ?, ?, ?)",
                (old_ip, new_ip, duration, 1 if success else 0)
            )
            self.conn.commit()
            return True
        except sqlite3.Error as e:
            logger.error(f"Error logging IP rotation: {e}")
            return False
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


class ProxidizeManager:
    """Handles IP rotation via Proxidize HTTP Proxy"""
    
    def __init__(self, host="nae2.proxi.es", port=2148, username="proxidize-4XauY", password="4mhm9"):
        """Initialize Proxidize manager with proxy settings"""
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.current_ip = None
        self.proxy_url = f"http://{username}:{password}@{host}:{port}"
        self.proxies = {
            "http": self.proxy_url,
            "https": self.proxy_url
        }
        self.db = Database()
        self.logger = logging.getLogger("ProxidizeManager")
    
    def get_proxy_options(self):
        """Get proxy options for Selenium"""
        return {
            "proxy": {
                "http": self.proxy_url,
                "https": self.proxy_url,
                "no_proxy": "localhost,127.0.0.1"
            }
        }
    
    def get_current_ip(self):
        """Get current IP address through the proxy"""
        import requests
        
        try:
            self.logger.info("Checking current IP address...")
            # Use a timeout to prevent hanging
            response = requests.get(
                "https://api.ipify.org?format=json", 
                proxies=self.proxies,
                timeout=10
            )
            
            if response.status_code == 200:
                ip_data = response.json()
                self.current_ip = ip_data.get("ip")
                self.logger.info(f"Current IP address: {self.current_ip}")
                return self.current_ip
            else:
                self.logger.error(f"Failed to get IP, status code: {response.status_code}")
                return None
        except Exception as e:
            self.logger.error(f"Error getting current IP: {str(e)}")
            return None
    
    def rotate_ip(self, max_attempts=3):
        """Rotate IP address using Proxidize API"""
        import requests
        
        old_ip = self.get_current_ip()
        if not old_ip:
            self.logger.error("Could not get current IP before rotation")
            return False
        
        self.logger.info(f"Rotating IP from: {old_ip}")
        
        # URL for rotating the Proxidize proxy IP
        rotation_url = f"http://{self.username}:{self.password}@{self.host}:{self.port}/api/rotate"
        
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Rotation attempt {attempt} of {max_attempts}...")
                start_time = time.time()
                
                # Make the rotation request
                response = requests.get(rotation_url, timeout=30)
                
                if response.status_code == 200:
                    # Wait for the rotation to take effect
                    time.sleep(5)
                    
                    # Get the new IP
                    new_ip = self.get_current_ip()
                    end_time = time.time()
                    duration = end_time - start_time
                    
                    if new_ip and new_ip != old_ip:
                        self.logger.info(f"IP successfully rotated: {old_ip} -> {new_ip} in {duration:.2f} seconds")
                        # Log the successful rotation
                        self.db.log_ip_rotation(old_ip, new_ip, duration, True)
                        return True
                    else:
                        self.logger.warning(f"IP did not change after rotation request (Attempt {attempt})")
                else:
                    self.logger.error(f"Rotation request failed with status code: {response.status_code}")
            except Exception as e:
                self.logger.error(f"Error during IP rotation (Attempt {attempt}): {str(e)}")
            
            # Wait before retrying
            if attempt < max_attempts:
                self.logger.info(f"Waiting before retry {attempt+1}...")
                time.sleep(5 * attempt)  # Exponential backoff
        
        self.logger.error(f"Failed to rotate IP after {max_attempts} attempts")
        self.db.log_ip_rotation(old_ip, old_ip, 0, False)
        return False
    
    def verify_connection(self):
        """Verify that the proxy connection is working"""
        ip = self.get_current_ip()
        return ip is not None


class TextNowSeleniumCreator:
    """Main class for creating TextNow accounts using Selenium"""
    
    TEXTNOW_URL = "https://www.textnow.com"
    SIGNUP_URL = "https://www.textnow.com/signup"
    LOGIN_URL = "https://www.textnow.com/login"
    MESSAGES_URL = "https://www.textnow.com/messaging"
    
    def __init__(self, headless=True, proxy_manager=None):
        """Initialize the TextNow creator"""
        self.headless = headless
        self.proxy_manager = proxy_manager or ProxidizeManager()
        self.db = Database()
        self.logger = logging.getLogger("TextNowSelenium")
        self.driver = None
        self.profile_dir = "chrome_profiles"
        
        # Ensure profiles directory exists
        os.makedirs(self.profile_dir, exist_ok=True)
    
    def _setup_chrome_options(self, profile=None):
        """Set up Chrome options with anti-detection measures"""
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        # Add proxy if available
        if self.proxy_manager:
            proxy = f"{self.proxy_manager.host}:{self.proxy_manager.port}"
            options.add_argument(f'--proxy-server={proxy}')
        
        # Add profile if specified
        if profile:
            profile_path = os.path.join(self.profile_dir, profile)
            os.makedirs(profile_path, exist_ok=True)
            options.add_argument(f"--user-data-dir={profile_path}")
        
        # Anti-detection measures
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=IsolateOrigins,site-per-process")
        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--log-level=3")
        
        # Set random user agent
        options.add_argument(f"--user-agent={self._generate_user_agent()}")
        
        # Add experimental options
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # If using proxy with authentication
        if self.proxy_manager:
            options.add_extension("proxy_auth_extension.zip")
        
        return options
    
    def _create_proxy_auth_extension(self):
        """Create a Chrome extension for proxy authentication"""
        if not self.proxy_manager:
            return
            
        manifest_json = """
        {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version":"22.0.0"
        }
        """
        
        background_js = """
        var config = {
                mode: "fixed_servers",
                rules: {
                singleProxy: {
                    scheme: "http",
                    host: "%s",
                    port: parseInt(%s)
                },
                bypassList: ["localhost"]
                }
            };

        chrome.proxy.settings.set({value: config, scope: "regular"}, function() {});

        function callbackFn(details) {
            return {
                authCredentials: {
                    username: "%s",
                    password: "%s"
                }
            };
        }

        chrome.webRequest.onAuthRequired.addListener(
                    callbackFn,
                    {urls: ["<all_urls>"]},
                    ['blocking']
        );
        """ % (
            self.proxy_manager.host,
            self.proxy_manager.port,
            self.proxy_manager.username,
            self.proxy_manager.password
        )
        
        # Create extension directory
        os.makedirs("proxy_auth_extension", exist_ok=True)
        
        # Write manifest and background files
        with open("proxy_auth_extension/manifest.json", "w") as f:
            f.write(manifest_json)
            
        with open("proxy_auth_extension/background.js", "w") as f:
            f.write(background_js)
        
        # Create zip file
        import zipfile
        with zipfile.ZipFile("proxy_auth_extension.zip", "w") as zp:
            zp.write("proxy_auth_extension/manifest.json", "manifest.json")
            zp.write("proxy_auth_extension/background.js", "background.js")
        
        self.logger.info("Created proxy authentication extension")
    
    def start_driver(self, profile=None):
        """Start a new Chrome WebDriver instance"""
        try:
            # Create proxy auth extension if using a proxy
            if self.proxy_manager:
                self._create_proxy_auth_extension()
            
            # Set up Chrome options
            options = self._setup_chrome_options(profile)
            
            # Set path to chromedriver
            chrome_driver_path = "chromedriver"
            service = Service(chrome_driver_path)
            
            # Create and start the driver
            self.driver = webdriver.Chrome(service=service, options=options)
            
            # Apply additional anti-detection measures
            self._apply_stealth_scripts()
            
            self.logger.info("Started Chrome WebDriver")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start Chrome WebDriver: {str(e)}")
            return False
    
    def _apply_stealth_scripts(self):
        """Apply JavaScript to hide Selenium's presence"""
        if not self.driver:
            return False
            
        try:
            # Hide automation flags
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false
                });
            """)
            
            # Add chrome object if missing
            self.driver.execute_script("""
                if (!window.chrome) {
                    window.chrome = {
                        runtime: {}
                    };
                }
            """)
            
            # Override permissions
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying stealth scripts: {str(e)}")
            return False
    
    def quit_driver(self):
        """Quit the WebDriver instance"""
        if self.driver:
            try:
                self.driver.quit()
                self.driver = None
                self.logger.info("Quit Chrome WebDriver")
                return True
            except Exception as e:
                self.logger.error(f"Error quitting Chrome WebDriver: {str(e)}")
                return False
    
    def _generate_user_agent(self):
        """Generate a realistic user agent string"""
        chrome_versions = [
            "110.0.5481.177",
            "111.0.5563.64", 
            "112.0.5615.49",
            "113.0.5672.63",
            "114.0.5735.90"
        ]
        
        windows_versions = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 10.0; WOW64",
            "Windows NT 6.3; Win64; x64",
            "Windows NT 6.1; Win64; x64"
        ]
        
        chrome_version = random.choice(chrome_versions)
        windows_version = random.choice(windows_versions)
        
        return f"Mozilla/5.0 ({windows_version}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version} Safari/537.36"
    
    def _wait_and_find_element(self, by, value, timeout=10, driver=None):
        """Wait for an element to be present and return it"""
        if driver is None:
            driver = self.driver
            
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            return element
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for element: {by}={value}")
            return None
        except Exception as e:
            self.logger.error(f"Error finding element {by}={value}: {str(e)}")
            return None
    
    def _wait_and_find_elements(self, by, value, timeout=10, driver=None):
        """Wait for elements to be present and return them"""
        if driver is None:
            driver = self.driver
            
        try:
            WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((by, value))
            )
            elements = driver.find_elements(by, value)
            return elements
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for elements: {by}={value}")
            return []
        except Exception as e:
            self.logger.error(f"Error finding elements {by}={value}: {str(e)}")
            return []
    
    def _wait_and_click(self, by, value, timeout=10, driver=None):
        """Wait for an element to be clickable and click it"""
        if driver is None:
            driver = self.driver
            
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((by, value))
            )
            element.click()
            return True
        except TimeoutException:
            self.logger.warning(f"Timeout waiting for clickable element: {by}={value}")
            return False
        except Exception as e:
            self.logger.error(f"Error clicking element {by}={value}: {str(e)}")
            return False
    
    def _safe_fill_input(self, element, text):
        """Safely fill an input element with text"""
        try:
            element.clear()
            element.send_keys(text)
            return True
        except Exception as e:
            self.logger.error(f"Error filling input: {str(e)}")
            return False
    
    def _check_for_errors(self, driver=None):
        """Check the page for error messages"""
        if driver is None:
            driver = self.driver
            
        error_selectors = [
            "div[class*='error']",
            "p[class*='error']",
            "span[class*='error']",
            ".error-message",
            "div[role='alert']"
        ]
        
        for selector in error_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    text = element.text.strip()
                    if text:
                        self.logger.error(f"Error message found: {text}")
                        return text
            except Exception:
                continue
                
        return None
    
    def _generate_random_name(self):
        """Generate a random name for account creation"""
        first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph", "Thomas", "Charles",
            "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth", "Barbara", "Susan", "Jessica", "Sarah", "Karen"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Jones", "Brown", "Davis", "Miller", "Wilson", "Moore", "Taylor",
            "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson"
        ]
        
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_random_email(self, name=None):
        """Generate a random email address"""
        if name:
            # Use name as basis for email
            name_parts = name.lower().split()
            base = f"{name_parts[0]}{random.choice(['', '.'])}{name_parts[-1]}"
        else:
            # Generate random username
            letters = "abcdefghijklmnopqrstuvwxyz"
            base = ''.join(random.choice(letters) for _ in range(random.randint(6, 10)))
        
        # Add random numbers
        num = random.randint(10, 9999)
        username = f"{base}{num}"
        
        domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com"]
        domain = random.choice(domains)
        
        return f"{username}@{domain}"
    
    def _generate_random_password(self):
        """Generate a secure random password"""
        length = random.randint(10, 14)
        chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+"
        return ''.join(random.choice(chars) for _ in range(length))
    
    def extract_phone_number(self, driver=None):
        """Extract the phone number from the messaging page"""
        if driver is None:
            driver = self.driver
            
        try:
            # Wait a moment for the page to fully load
            time.sleep(3)
            
            # Try different selectors that might contain the phone number
            phone_selectors = [
                "div[data-testid='user-phone-number']",
                ".user-phone-number",
                "div.profile-phone",
                "span:contains('+')",
                "div:contains('+')"
            ]
            
            for selector in phone_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text
                        # Extract phone number using regex
                        phone_match = re.search(r'\+1\D*(\d{3})\D*(\d{3})\D*(\d{4})', text)
                        if phone_match:
                            area_code = phone_match.group(1)
                            middle = phone_match.group(2)
                            last = phone_match.group(3)
                            phone_number = f"+1{area_code}{middle}{last}"
                            return phone_number, area_code
                except Exception:
                    continue
            
            # If we couldn't find it with selectors, try grabbing from the page URL
            try:
                url = driver.current_url
                # Sometimes the phone number is in the URL
                url_match = re.search(r'/(\d{10})$', url)
                if url_match:
                    number = url_match.group(1)
                    area_code = number[:3]
                    return f"+1{number}", area_code
            except Exception:
                pass
                
            self.logger.error("Could not extract phone number")
            return None, None
        except Exception as e:
            self.logger.error(f"Error extracting phone number: {str(e)}")
            return None, None
    
    def create_account(self, name=None, email=None, password=None, area_code=None):
        """Create a new TextNow account with the given details"""
        # Generate random details if not provided
        name = name or self._generate_random_name()
        email = email or self._generate_random_email(name)
        password = password or self._generate_random_password()
        
        self.logger.info(f"Creating new account with email: {email}")
        
        # Start a new WebDriver instance
        if not self.start_driver():
            return {
                "success": False,
                "error": "Failed to start WebDriver"
            }
        
        try:
            # Navigate to signup page
            self.logger.info("Navigating to TextNow signup page")
            self.driver.get(self.SIGNUP_URL)
            
            # Give the page time to load
            time.sleep(3)
            
            # Check for cookie acceptance
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'I Accept') or contains(text(), 'Agree')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self.logger.info("Accepted cookies")
                    time.sleep(1)
            except Exception:
                pass
            
            # Fill the signup form
            self.logger.info("Filling signup form")
            
            # Email field
            email_field = self._wait_and_find_element(
                By.CSS_SELECTOR, 
                "input[name='email'], input[type='email']"
            )
            if not email_field:
                self.logger.error("Could not find email field")
                return {
                    "success": False,
                    "error": "Could not find email field"
                }
            
            self._safe_fill_input(email_field, email)
            
            # Password field
            password_field = self._wait_and_find_element(
                By.CSS_SELECTOR, 
                "input[name='password'], input[type='password']"
            )
            if not password_field:
                self.logger.error("Could not find password field")
                return {
                    "success": False,
                    "error": "Could not find password field"
                }
                
            self._safe_fill_input(password_field, password)
            
            # Name fields
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            # Try to find first and last name fields
            first_name_field = None
            last_name_field = None
            
            try:
                first_name_field = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "input[name='firstName'], input[placeholder*='First']"
                )
                last_name_field = self.driver.find_element(
                    By.CSS_SELECTOR, 
                    "input[name='lastName'], input[placeholder*='Last']"
                )
            except NoSuchElementException:
                # Try a combined name field
                try:
                    name_field = self.driver.find_element(
                        By.CSS_SELECTOR, 
                        "input[name='name'], input[placeholder*='Name']"
                    )
                    self._safe_fill_input(name_field, name)
                except NoSuchElementException:
                    self.logger.warning("Could not find name fields")
            
            # Fill first and last name if found
            if first_name_field and last_name_field:
                self._safe_fill_input(first_name_field, first_name)
                self._safe_fill_input(last_name_field, last_name)
            
            # Submit the form
            self.logger.info("Submitting signup form")
            
            # Try different selectors for the submit button
            submit_button = None
            submit_selectors = [
                "button[type='submit']", 
                "button:contains('Sign Up')", 
                "button:contains('Continue')", 
                "input[type='submit']"
            ]
            
            for selector in submit_selectors:
                try:
                    submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                submit_button.click()
            else:
                # Try submitting the form directly
                self.driver.execute_script("document.querySelector('form').submit()")
            
            # Wait for navigation
            time.sleep(5)
            
            # Check for error messages
            error = self._check_for_errors()
            if error:
                self.logger.error(f"Signup error: {error}")
                self.db.log_error("signup", f"Error during signup: {error}")
                return {
                    "success": False,
                    "error": f"Signup error: {error}"
                }
            
            # Wait for phone number selection page
            self.logger.info("Waiting for phone number selection page")
            time.sleep(3)
            
            # Check if we've reached phone number selection
            phone_page_indicators = [
                "input[placeholder*='Area code']",
                "input[placeholder*='area code']",
                "input[placeholder*='Search']",
                "div[aria-label*='area code']",
                "div:contains('Choose your phone number')",
                "div:contains('Select a number')"
            ]
            
            phone_selection_page = False
            for selector in phone_page_indicators:
                try:
                    if self.driver.find_elements(By.CSS_SELECTOR, selector):
                        phone_selection_page = True
                        break
                except Exception:
                    continue
            
            if not phone_selection_page:
                self.logger.error("Failed to reach phone number selection page")
                return {
                    "success": False,
                    "error": "Failed to reach phone number selection page"
                }
            
            # Enter area code if provided
            if area_code:
                self.logger.info(f"Searching for area code: {area_code}")
                area_code_input = None
                
                # Try different selectors for area code input
                area_code_selectors = [
                    "input[placeholder*='Area code']", 
                    "input[placeholder*='area code']", 
                    "input[placeholder*='Search']"
                ]
                
                for selector in area_code_selectors:
                    try:
                        area_code_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if area_code_input:
                    self._safe_fill_input(area_code_input, area_code)
                    area_code_input.send_keys(Keys.RETURN)
                    time.sleep(2)
                else:
                    self.logger.warning(f"Could not find area code input field")
            
            # Select a phone number
            self.logger.info("Selecting a phone number")
            
            # Try different selectors for phone numbers
            number_selectors = [
                "div[role='button']:has-text('+')",
                "button:has-text('+')",
                "div.phone-number",
                "li:has-text('+')",
                "div:has-text('+1')"
            ]
            
            selected_number = False
            for selector in number_selectors:
                try:
                    phone_numbers = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if phone_numbers:
                        phone_numbers[0].click()
                        selected_number = True
                        self.logger.info("Selected a phone number")
                        break
                except Exception:
                    continue
            
            if not selected_number:
                # Try a more general approach
                try:
                    # Find any elements that might contain a phone number
                    elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '+1')]")
                    if elements:
                        elements[0].click()
                        selected_number = True
                        self.logger.info("Selected a phone number (using general approach)")
                except Exception as e:
                    self.logger.error(f"Error selecting phone number: {str(e)}")
            
            if not selected_number:
                self.logger.error("No phone numbers available to select")
                return {
                    "success": False,
                    "error": "No phone numbers available"
                }
            
            # Wait for the messaging page
            self.logger.info("Waiting for messaging page")
            wait = WebDriverWait(self.driver, 30)
            try:
                wait.until(lambda d: "/messaging" in d.current_url)
                self.logger.info("Successfully reached messaging page")
            except TimeoutException:
                self.logger.error("Failed to reach messaging page after selecting number")
                return {
                    "success": False,
                    "error": "Failed to reach messaging page"
                }
            
            # Extract the phone number
            phone_number, assigned_area_code = self.extract_phone_number()
            
            if not phone_number:
                self.logger.error("Failed to extract phone number")
                return {
                    "success": False,
                    "error": "Failed to extract phone number"
                }
            
            # Get cookies for later login
            cookies = self.driver.get_cookies()
            login_cookie = json.dumps(cookies)
            
            # Get user agent
            user_agent = self.driver.execute_script("return navigator.userAgent")
            
            # Get current IP
            current_ip = self.proxy_manager.current_ip if self.proxy_manager else None
            
            # Save account to database
            account_id = self.db.add_account(
                phone_number=phone_number,
                name=name,
                password=password,
                username=None,  # Will be updated later if needed
                email=email,
                area_code=assigned_area_code or area_code,
                login_cookie=login_cookie,
                user_agent=user_agent,
                ip_used=current_ip
            )
            
            if not account_id:
                self.logger.error("Failed to save account to database")
                return {
                    "success": False,
                    "error": "Failed to save account to database"
                }
            
            self.logger.info(f"Account created successfully: {phone_number}")
            
            return {
                "success": True,
                "account_id": account_id,
                "phone_number": phone_number,
                "email": email,
                "password": password,
                "area_code": assigned_area_code or area_code
            }
            
        except Exception as e:
            self.logger.error(f"Error creating account: {str(e)}")
            self.db.log_error("account_creation", str(e))
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Close the WebDriver
            self.quit_driver()
    
    def login_to_account(self, account_id=None, phone_number=None, email=None, password=None):
        """Login to an existing TextNow account"""
        # Get account details if account_id or phone_number is provided
        account = None
        if account_id or phone_number:
            account = self.db.get_account(account_id=account_id, phone_number=phone_number)
            if not account:
                self.logger.error("Account not found")
                return {
                    "success": False,
                    "error": "Account not found"
                }
            
            email = account["email"]
            password = account["password"]
        
        if not email or not password:
            self.logger.error("Email and password are required for login")
            return {
                "success": False,
                "error": "Email and password are required"
            }
        
        # Start a new WebDriver instance
        if not self.start_driver():
            return {
                "success": False,
                "error": "Failed to start WebDriver"
            }
        
        try:
            # Navigate to login page
            self.logger.info(f"Logging in with email: {email}")
            self.driver.get(self.LOGIN_URL)
            
            # Give the page time to load
            time.sleep(3)
            
            # Check for cookie acceptance
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'I Accept') or contains(text(), 'Agree')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    self.logger.info("Accepted cookies")
                    time.sleep(1)
            except Exception:
                pass
            
            # Fill the login form
            email_field = self._wait_and_find_element(
                By.CSS_SELECTOR, 
                "input[name='email'], input[type='email']"
            )
            if not email_field:
                self.logger.error("Could not find email field")
                return {
                    "success": False,
                    "error": "Could not find email field"
                }
            
            self._safe_fill_input(email_field, email)
            
            password_field = self._wait_and_find_element(
                By.CSS_SELECTOR, 
                "input[name='password'], input[type='password']"
            )
            if not password_field:
                self.logger.error("Could not find password field")
                return {
                    "success": False,
                    "error": "Could not find password field"
                }
                
            self._safe_fill_input(password_field, password)
            
            # Submit the login form
            login_button = None
            login_selectors = [
                "button[type='submit']", 
                "button:contains('Login')", 
                "button:contains('Sign In')", 
                "input[type='submit']"
            ]
            
            for selector in login_selectors:
                try:
                    login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if login_button:
                login_button.click()
            else:
                # Try submitting the form directly
                self.driver.execute_script("document.querySelector('form').submit()")
            
            # Wait for navigation
            time.sleep(5)
            
            # Check for error messages
            error = self._check_for_errors()
            if error:
                self.logger.error(f"Login error: {error}")
                if account:
                    self.db.log_error("login", f"Error during login: {error}", account_id)
                    self.db.update_account(account_id, status="login_failed")
                
                return {
                    "success": False,
                    "error": f"Login error: {error}"
                }
            
            # Wait for the messaging page
            self.logger.info("Waiting for messaging page")
            wait = WebDriverWait(self.driver, 30)
            try:
                wait.until(lambda d: "/messaging" in d.current_url)
                self.logger.info("Successfully reached messaging page")
            except TimeoutException:
                self.logger.error("Failed to reach messaging page after login")
                if account:
                    self.db.log_error("login", "Failed to reach messaging page", account_id)
                
                return {
                    "success": False,
                    "error": "Failed to reach messaging page after login"
                }
            
            # Verify phone number if we have an account
            if account:
                phone_number, _ = self.extract_phone_number()
                if phone_number and phone_number != account["phone_number"]:
                    self.logger.warning(f"Phone number mismatch: {phone_number} vs {account['phone_number']}")
            
            # Get cookies for future logins
            cookies = self.driver.get_cookies()
            login_cookie = json.dumps(cookies)
            
            # Update account in database if we have an account_id
            if account_id:
                self.db.update_account(
                    account_id,
                    login_cookie=login_cookie,
                    status="active"
                )
            
            return {
                "success": True,
                "message": "Login successful"
            }
            
        except Exception as e:
            self.logger.error(f"Error logging in: {str(e)}")
            if account:
                self.db.log_error("login", str(e), account_id)
            
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Close the WebDriver (keeping it open is not recommended with Selenium)
            self.quit_driver()
    
    def send_message(self, account_id, recipient, message_text):
        """Send a text message from a TextNow account"""
        account = self.db.get_account(account_id=account_id)
        if not account:
            self.logger.error(f"Account not found: {account_id}")
            return {
                "success": False,
                "error": "Account not found"
            }
        
        # Login to the account
        login_result = self.login_to_account(account_id=account_id)
        if not login_result["success"]:
            return login_result
        
        # Start a new session (we need to login again because Selenium session ended)
        if not self.start_driver():
            return {
                "success": False,
                "error": "Failed to start WebDriver"
            }
        
        try:
            # Login again
            email = account["email"]
            password = account["password"]
            
            self.logger.info(f"Logging in with email: {email} to send message")
            self.driver.get(self.LOGIN_URL)
            time.sleep(3)
            
            # Accept cookies if needed
            try:
                cookie_buttons = self.driver.find_elements(By.XPATH, 
                    "//button[contains(text(), 'Accept') or contains(text(), 'I Accept') or contains(text(), 'Agree')]")
                if cookie_buttons:
                    cookie_buttons[0].click()
                    time.sleep(1)
            except Exception:
                pass
            
            # Fill login form
            email_field = self._wait_and_find_element(By.CSS_SELECTOR, "input[name='email'], input[type='email']")
            if email_field:
                self._safe_fill_input(email_field, email)
            
            password_field = self._wait_and_find_element(By.CSS_SELECTOR, "input[name='password'], input[type='password']")
            if password_field:
                self._safe_fill_input(password_field, password)
            
            # Submit login form
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            if login_button:
                login_button.click()
            else:
                self.driver.execute_script("document.querySelector('form').submit()")
            
            # Wait for messaging page
            wait = WebDriverWait(self.driver, 30)
            try:
                wait.until(lambda d: "/messaging" in d.current_url)
            except TimeoutException:
                self.logger.error("Failed to reach messaging page for sending message")
                return {
                    "success": False,
                    "error": "Failed to reach messaging page"
                }
            
            # Start a new conversation
            self.logger.info(f"Starting new conversation with {recipient}")
            
            # Try different selectors for the "New" conversation button
            new_conversation_selectors = [
                "button[aria-label='New conversation']",
                "button:contains('New')",
                "div[role='button']:contains('New')",
                "a[href*='new']"
            ]
            
            clicked_new = False
            for selector in new_conversation_selectors:
                try:
                    new_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    new_button.click()
                    clicked_new = True
                    break
                except Exception:
                    continue
            
            if not clicked_new:
                # Try a more general approach
                try:
                    # Look for any buttons or elements that might be for new conversation
                    new_buttons = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'New') or @aria-label='New' or @aria-label='New conversation']")
                    if new_buttons:
                        new_buttons[0].click()
                        clicked_new = True
                    else:
                        # Try looking for plus icons which often indicate new conversation
                        plus_elements = self.driver.find_elements(By.XPATH, 
                            "//*[contains(@class, 'plus') or contains(@class, 'add') or contains(@class, 'new')]")
                        if plus_elements:
                            plus_elements[0].click()
                            clicked_new = True
                except Exception as e:
                    self.logger.error(f"Error clicking new conversation button: {str(e)}")
            
            if not clicked_new:
                self.logger.error("Could not find new conversation button")
                return {
                    "success": False,
                    "error": "Could not find new conversation button"
                }
            
            # Wait for recipient input field
            time.sleep(2)
            
            # Enter recipient number
            self.logger.info(f"Entering recipient number: {recipient}")
            recipient_input = None
            recipient_selectors = [
                "input[placeholder*='Enter name or number']",
                "input[placeholder*='Phone number']",
                "input[aria-label*='recipient']",
                "input[aria-label*='phone']"
            ]
            
            for selector in recipient_selectors:
                try:
                    recipient_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not recipient_input:
                self.logger.error("Could not find recipient input field")
                return {
                    "success": False,
                    "error": "Could not find recipient input field"
                }
            
            self._safe_fill_input(recipient_input, recipient)
            recipient_input.send_keys(Keys.RETURN)
            time.sleep(2)
            
            # Enter message text
            self.logger.info("Entering message text")
            message_input = None
            message_selectors = [
                "textarea[placeholder*='Type a message']",
                "div[role='textbox']",
                "div[contenteditable='true']",
                "textarea"
            ]
            
            for selector in message_selectors:
                try:
                    message_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not message_input:
                self.logger.error("Could not find message input field")
                return {
                    "success": False,
                    "error": "Could not find message input field"
                }
            
            self._safe_fill_input(message_input, message_text)
            time.sleep(1)
            
            # Send the message
            self.logger.info("Sending message")
            send_button = None
            send_selectors = [
                "button[aria-label='Send message']",
                "button:contains('Send')",
                "div[role='button']:contains('Send')"
            ]
            
            for selector in send_selectors:
                try:
                    send_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    break
                except NoSuchElementException:
                    continue
            
            if not send_button:
                # Try a more general approach
                try:
                    # Look for send icon or button
                    send_elements = self.driver.find_elements(By.XPATH, 
                        "//*[contains(text(), 'Send') or @aria-label='Send' or @aria-label='Send message']")
                    if send_elements:
                        send_button = send_elements[0]
                    else:
                        # Try sending with Enter key
                        message_input.send_keys(Keys.RETURN)
                        self.logger.info("Sent message using Enter key")
                        # Wait to see if message was sent
                        time.sleep(3)
                        return {
                            "success": True,
                            "message": "Message sent with Enter key"
                        }
                except Exception as e:
                    self.logger.error(f"Error trying to find send button: {str(e)}")
            
            if send_button:
                send_button.click()
                self.logger.info("Clicked send button")
            else:
                self.logger.error("Could not find send button")
                return {
                    "success": False,
                    "error": "Could not find send button"
                }
            
            # Wait for message to be sent
            time.sleep(3)
            
            # Check for error messages
            error = self._check_for_errors()
            if error:
                self.logger.error(f"Message sending error: {error}")
                self.db.log_error("message_send", f"Error sending message: {error}", account_id)
                
                return {
                    "success": False,
                    "error": f"Message sending error: {error}"
                }
            
            self.logger.info(f"Message sent successfully to {recipient}")
            
            # Update account last used time
            self.db.update_account(account_id, status="active")
            
            return {
                "success": True,
                "message": "Message sent successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error sending message: {str(e)}")
            self.db.log_error("message_send", str(e), account_id)
            
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            # Close the WebDriver
            self.quit_driver()
    
    def create_multiple_accounts(self, count, area_code=None):
        """Create multiple TextNow accounts"""
        results = {
            "total": count,
            "successful": 0,
            "failed": 0,
            "accounts": []
        }
        
        for i in range(count):
            self.logger.info(f"Creating account {i+1} of {count}")
            
            # Check if we need to rotate IP
            if i > 0 and i % 3 == 0 and self.proxy_manager:
                self.logger.info(f"Rotating IP after creating {i} accounts")
                self.proxy_manager.rotate_ip()
            
            # Create the account
            result = self.create_account(area_code=area_code)
            
            if result["success"]:
                results["successful"] += 1
                results["accounts"].append({
                    "account_id": result["account_id"],
                    "phone_number": result["phone_number"],
                    "email": result["email"],
                    "password": result["password"]
                })
            else:
                results["failed"] += 1
                results["accounts"].append({
                    "error": result["error"]
                })
            
            # Random delay between account creations
            delay = random.uniform(5, 15)
            self.logger.info(f"Waiting {delay:.2f} seconds before next account creation")
            time.sleep(delay)
        
        return results


def main():
    """Main function for creating TextNow accounts"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("textnow_selenium.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("TextNowSeleniumMain")
    
    # Initialize the proxy manager
    proxy = ProxidizeManager()
    
    # Verify proxy connection
    if not proxy.verify_connection():
        logger.error("Could not connect to proxy. Exiting.")
        return
    
    # Get current IP
    ip = proxy.get_current_ip()
    logger.info(f"Current IP: {ip}")
    
    # Initialize the TextNow creator
    creator = TextNowSeleniumCreator(headless=True, proxy_manager=proxy)
    
    try:
        # Create a single account
        result = creator.create_account(area_code="954")
        
        if result["success"]:
            logger.info(f"Account created successfully: {result['phone_number']}")
            
            # Try sending a test message
            send_result = creator.send_message(
                result["account_id"],
                "5551234567",
                "This is a test message from my new TextNow account!"
            )
            
            if send_result["success"]:
                logger.info("Test message sent successfully")
            else:
                logger.error(f"Failed to send test message: {send_result['error']}")
        else:
            logger.error(f"Failed to create account: {result['error']}")
        
    except Exception as e:
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()