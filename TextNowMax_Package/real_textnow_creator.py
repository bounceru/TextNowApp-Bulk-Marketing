"""
TextNow Account Creator - Full Production Version

This module provides the core functionality for creating TextNow accounts
with Playwright browser automation and Proxidize proxy management.
"""

import os
import time
import random
import logging
import json
import sqlite3
import asyncio
from datetime import datetime
from typing import Dict, List, Union, Optional, Any, Tuple
from playwright.async_api import async_playwright, Browser, Page, BrowserContext

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("account_creator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TextNowCreator")

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
        """Get proxy options for Playwright"""
        return {
            "server": f"http://{self.host}:{self.port}",
            "username": self.username,
            "password": self.password
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


class TextNowCreator:
    """Main class for creating TextNow accounts"""
    
    TEXTNOW_URL = "https://www.textnow.com"
    SIGNUP_URL = "https://www.textnow.com/signup"
    LOGIN_URL = "https://www.textnow.com/login"
    MESSAGES_URL = "https://www.textnow.com/messaging"
    
    def __init__(self, headless=True, proxy_manager=None):
        """Initialize the TextNow creator"""
        self.headless = headless
        self.proxy_manager = proxy_manager or ProxidizeManager()
        self.db = Database()
        self.logger = logging.getLogger("TextNowCreator")
        self.browser = None
        self.browser_context = None
        
        # Ensure profiles directory exists
        os.makedirs("profiles", exist_ok=True)
    
    async def start_browser(self):
        """Start the browser with appropriate settings"""
        if self.browser:
            return True
            
        try:
            # Initialize Playwright
            playwright = await async_playwright().start()
            
            # Get proxy options
            proxy_options = self.proxy_manager.get_proxy_options() if self.proxy_manager else None
            
            # Launch the browser with anti-bot measures
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                proxy=proxy_options,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            self.logger.info("Browser started successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to start browser: {str(e)}")
            return False
    
    async def stop_browser(self):
        """Close the browser"""
        if self.browser:
            try:
                await self.browser.close()
                self.browser = None
                self.logger.info("Browser closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing browser: {str(e)}")
    
    async def create_browser_context(self):
        """Create a new browser context with anti-detection measures"""
        if not self.browser:
            success = await self.start_browser()
            if not success:
                return None
        
        try:
            # Generate random user agent
            user_agent = self._generate_user_agent()
            
            # Create a new context
            context = await self.browser.new_context(
                user_agent=user_agent,
                viewport=self._random_viewport(),
                locale="en-US",
                timezone_id="America/New_York"
            )
            
            # Apply stealth settings
            await self._apply_stealth_settings(context)
            
            self.logger.info("Created new browser context with anti-detection measures")
            return context
        except Exception as e:
            self.logger.error(f"Error creating browser context: {str(e)}")
            return None
    
    async def _apply_stealth_settings(self, context):
        """Apply stealth settings to avoid detection"""
        try:
            # Execute scripts to modify browser fingerprinting
            await context.add_init_script("""
                // Override WebGL vendor and renderer
                const getParameterProxyHandler = {
                    apply: function(target, thisArg, args) {
                        if (args[0] === 37445) {
                            return "Google Inc. (Intel)";
                        } else if (args[0] === 37446) {
                            return "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)";
                        }
                        return Reflect.apply(target, thisArg, args);
                    }
                };
                
                if (WebGLRenderingContext.prototype.getParameter) {
                    WebGLRenderingContext.prototype.getParameter = new Proxy(
                        WebGLRenderingContext.prototype.getParameter, 
                        getParameterProxyHandler
                    );
                }
                
                // Hide automation flags
                Object.defineProperty(navigator, 'webdriver', { get: () => false });
                
                // Add common properties that headless browsers might miss
                window.chrome = { runtime: {} };
                
                // Fix hairline feature detection
                const elementDescriptor = Object.getOwnPropertyDescriptor(HTMLElement.prototype, 'offsetHeight');
                if (elementDescriptor && elementDescriptor.configurable) {
                    Object.defineProperty(HTMLDivElement.prototype, 'offsetHeight', {
                        ...elementDescriptor,
                        get: function() { 
                            const height = elementDescriptor.get.apply(this);
                            if (height === 0 && this.id === 'modernizr') {
                                return 1;
                            }
                            return height;
                        }
                    });
                }
                
                // Prevent iframe detection
                Object.defineProperty(HTMLIFrameElement.prototype, 'contentWindow', {
                    get: function() {
                        return window;
                    }
                });
            """)
            
            return True
        except Exception as e:
            self.logger.error(f"Error applying stealth settings: {str(e)}")
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
    
    def _random_viewport(self):
        """Generate a random viewport size to avoid detection"""
        widths = [1280, 1366, 1440, 1600, 1920]
        heights = [720, 768, 800, 900, 1080]
        
        return {
            "width": random.choice(widths),
            "height": random.choice(heights)
        }
    
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
    
    async def extract_phone_number(self, page):
        """Extract the phone number from the messaging page"""
        try:
            # Wait for the phone number to appear on the page
            await page.wait_for_timeout(3000)
            
            # Try different selectors that might contain the phone number
            phone_selectors = [
                'div[data-testid="user-phone-number"]',
                '.user-phone-number',
                'div.profile-phone',
                'span:has-text("+")',
                'div:has-text("+")'
            ]
            
            for selector in phone_selectors:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        text = await element.text_content()
                        # Extract phone number using regex
                        import re
                        phone_match = re.search(r'\+1\D*(\d{3})\D*(\d{3})\D*(\d{4})', text)
                        if phone_match:
                            area_code = phone_match.group(1)
                            middle = phone_match.group(2)
                            last = phone_match.group(3)
                            phone_number = f"+1{area_code}{middle}{last}"
                            area_code = area_code
                            return phone_number, area_code
                except Exception:
                    continue
            
            # If we couldn't find it with selectors, try grabbing from the page URL
            try:
                url = page.url
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
    
    async def create_account(self, name=None, email=None, password=None, area_code=None):
        """Create a new TextNow account with the given details"""
        # Generate random details if not provided
        name = name or self._generate_random_name()
        email = email or self._generate_random_email(name)
        password = password or self._generate_random_password()
        
        self.logger.info(f"Creating new account with email: {email}")
        
        # Create a browser context
        context = await self.create_browser_context()
        if not context:
            return {
                "success": False,
                "error": "Failed to create browser context"
            }
        
        page = None
        try:
            # Create a new page
            page = await context.new_page()
            
            # Navigate to signup page
            self.logger.info("Navigating to TextNow signup page")
            await page.goto(self.SIGNUP_URL)
            await page.wait_for_load_state("networkidle")
            
            # Check for cookie acceptance
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("I Accept"), button:has-text("Agree")')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    self.logger.info("Accepted cookies")
            except Exception:
                pass
            
            # Fill the signup form
            self.logger.info("Filling signup form")
            
            # Email field
            await page.fill('input[name="email"], input[type="email"]', email)
            
            # Password field
            await page.fill('input[name="password"], input[type="password"]', password)
            
            # Name fields (some versions have separate first/last name fields)
            name_parts = name.split(' ', 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            
            try:
                first_name_field = page.locator('input[name="firstName"], input[placeholder*="First"]').first
                last_name_field = page.locator('input[name="lastName"], input[placeholder*="Last"]').first
                
                if await first_name_field.count() > 0 and await last_name_field.count() > 0:
                    await first_name_field.fill(first_name)
                    await last_name_field.fill(last_name)
                else:
                    # Try a single name field
                    name_field = page.locator('input[name="name"], input[placeholder*="Name"]').first
                    if await name_field.count() > 0:
                        await name_field.fill(name)
            except Exception as e:
                self.logger.warning(f"Error filling name fields: {str(e)}")
            
            # Submit the form
            self.logger.info("Submitting signup form")
            
            submit_button = page.locator('button[type="submit"], button:has-text("Sign Up"), button:has-text("Continue"), input[type="submit"]').first
            
            if await submit_button.count() > 0:
                await submit_button.click()
            else:
                # Try submitting the form directly
                await page.evaluate("document.querySelector('form').submit()")
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            # Check for error messages
            error_selectors = [
                'div[class*="error"]', 
                'p[class*="error"]',
                'span[class*="error"]',
                '.error-message',
                'div[role="alert"]'
            ]
            
            for selector in error_selectors:
                error_elements = page.locator(selector)
                if await error_elements.count() > 0:
                    error_message = await error_elements.first.text_content()
                    if error_message and len(error_message.strip()) > 0:
                        self.logger.error(f"Signup error: {error_message}")
                        self.db.log_error("signup", f"Error during signup: {error_message}")
                        return {
                            "success": False,
                            "error": f"Signup error: {error_message}"
                        }
            
            # Wait for phone number selection page
            await page.wait_for_timeout(5000)
            
            # Check if we've reached phone number selection
            phone_page_indicators = [
                'input[placeholder*="Area code"]',
                'input[placeholder*="area code"]',
                'input[placeholder*="Search"]',
                'div[aria-label*="area code"]',
                'div:has-text("Choose your phone number")',
                'div:has-text("Select a number")'
            ]
            
            phone_selection_page = False
            for indicator in phone_page_indicators:
                if await page.locator(indicator).count() > 0:
                    phone_selection_page = True
                    break
            
            if not phone_selection_page:
                self.logger.error("Failed to reach phone number selection page")
                return {
                    "success": False,
                    "error": "Failed to reach phone number selection page"
                }
            
            # Enter area code if provided
            if area_code:
                self.logger.info(f"Searching for area code: {area_code}")
                area_code_inputs = page.locator('input[placeholder*="Area code"], input[placeholder*="area code"], input[placeholder*="Search"]')
                
                if await area_code_inputs.count() > 0:
                    await area_code_inputs.first.fill(area_code)
                    await area_code_inputs.first.press("Enter")
                    await page.wait_for_timeout(2000)
            
            # Select a phone number
            self.logger.info("Selecting a phone number")
            number_selectors = [
                'div[role="button"]:has-text("+")',
                'button:has-text("+")',
                'div.phone-number',
                'li:has-text("+")',
                'div:has-text("+1")'
            ]
            
            selected_number = False
            for selector in number_selectors:
                phone_numbers = page.locator(selector)
                if await phone_numbers.count() > 0:
                    await phone_numbers.first.click()
                    selected_number = True
                    self.logger.info("Selected a phone number")
                    break
            
            if not selected_number:
                self.logger.error("No phone numbers available to select")
                return {
                    "success": False,
                    "error": "No phone numbers available"
                }
            
            # Wait for the messaging page
            try:
                await page.wait_for_url("**/messaging", timeout=30000)
                self.logger.info("Successfully reached messaging page")
            except Exception as e:
                self.logger.error(f"Failed to reach messaging page: {str(e)}")
                return {
                    "success": False,
                    "error": "Failed to reach messaging page"
                }
            
            # Extract the phone number
            phone_number, assigned_area_code = await self.extract_phone_number(page)
            
            if not phone_number:
                self.logger.error("Failed to extract phone number")
                return {
                    "success": False,
                    "error": "Failed to extract phone number"
                }
            
            # Get cookies for later login
            cookies = await context.cookies()
            login_cookie = json.dumps(cookies)
            
            # Get user agent
            user_agent = await page.evaluate("() => navigator.userAgent")
            
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
            # Close the page and context
            if page:
                await page.close()
            if context:
                await context.close()

    async def login_to_account(self, account_id=None, phone_number=None, email=None, password=None):
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
        
        # Create a browser context
        context = await self.create_browser_context()
        if not context:
            return {
                "success": False,
                "error": "Failed to create browser context"
            }
        
        page = None
        try:
            # Create a new page
            page = await context.new_page()
            
            # Navigate to login page
            self.logger.info(f"Logging in with email: {email}")
            await page.goto(self.LOGIN_URL)
            await page.wait_for_load_state("networkidle")
            
            # Check for cookie acceptance
            try:
                cookie_button = page.locator('button:has-text("Accept"), button:has-text("I Accept"), button:has-text("Agree")')
                if await cookie_button.count() > 0:
                    await cookie_button.first.click()
                    self.logger.info("Accepted cookies")
            except Exception:
                pass
            
            # Fill the login form
            await page.fill('input[name="email"], input[type="email"]', email)
            await page.fill('input[name="password"], input[type="password"]', password)
            
            # Submit the form
            login_button = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign In"), input[type="submit"]').first
            
            if await login_button.count() > 0:
                await login_button.click()
            else:
                # Try submitting the form directly
                await page.evaluate("document.querySelector('form').submit()")
            
            # Wait for navigation
            await page.wait_for_load_state("networkidle")
            
            # Check for error messages
            error_selectors = [
                'div[class*="error"]', 
                'p[class*="error"]',
                'span[class*="error"]',
                '.error-message',
                'div[role="alert"]'
            ]
            
            for selector in error_selectors:
                error_elements = page.locator(selector)
                if await error_elements.count() > 0:
                    error_message = await error_elements.first.text_content()
                    if error_message and len(error_message.strip()) > 0:
                        self.logger.error(f"Login error: {error_message}")
                        if account:
                            self.db.log_error("login", f"Error during login: {error_message}", account_id)
                            self.db.update_account(account_id, status="login_failed")
                        
                        return {
                            "success": False,
                            "error": f"Login error: {error_message}"
                        }
            
            # Wait for the messaging page
            try:
                await page.wait_for_url("**/messaging", timeout=30000)
                self.logger.info("Successfully logged in and reached messaging page")
            except Exception as e:
                self.logger.error(f"Failed to reach messaging page after login: {str(e)}")
                if account:
                    self.db.log_error("login", f"Failed to reach messaging page: {str(e)}", account_id)
                
                return {
                    "success": False,
                    "error": "Failed to reach messaging page after login"
                }
            
            # Extract the phone number to verify it matches
            if account:
                phone_number, _ = await self.extract_phone_number(page)
                if phone_number and phone_number != account["phone_number"]:
                    self.logger.warning(f"Phone number mismatch: {phone_number} vs {account['phone_number']}")
            
            # Get cookies for future logins
            cookies = await context.cookies()
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
                "message": "Login successful",
                "page": page,
                "context": context
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
            # We don't close page and context here because they might be used by the caller
            pass
    
    async def create_multiple_accounts(self, count, area_code=None):
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
            result = await self.create_account(area_code=area_code)
            
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
            await asyncio.sleep(delay)
        
        return results
    
    async def send_message(self, account_id, recipient, message_text):
        """Send a text message from a TextNow account"""
        account = self.db.get_account(account_id=account_id)
        if not account:
            self.logger.error(f"Account not found: {account_id}")
            return {
                "success": False,
                "error": "Account not found"
            }
        
        # Login to the account
        login_result = await self.login_to_account(account_id=account_id)
        if not login_result["success"]:
            return login_result
        
        # Use the page and context from the login result
        page = login_result["page"]
        context = login_result["context"]
        
        try:
            # Navigate to messaging if not already there
            if not page.url.endswith("/messaging"):
                await page.goto(self.MESSAGES_URL)
                await page.wait_for_load_state("networkidle")
            
            # Start a new conversation
            new_conversation_selectors = [
                'button[aria-label="New conversation"]',
                'button:has-text("New")',
                'div[role="button"]:has-text("New")',
                'a[href*="new"]'
            ]
            
            for selector in new_conversation_selectors:
                new_conversation = page.locator(selector)
                if await new_conversation.count() > 0:
                    await new_conversation.first.click()
                    break
            
            await page.wait_for_timeout(2000)
            
            # Enter recipient number
            recipient_input_selectors = [
                'input[placeholder*="Enter name or number"]',
                'input[placeholder*="Phone number"]',
                'input[aria-label*="recipient"]',
                'input[aria-label*="phone"]'
            ]
            
            for selector in recipient_input_selectors:
                recipient_input = page.locator(selector)
                if await recipient_input.count() > 0:
                    await recipient_input.fill(recipient)
                    await recipient_input.press("Enter")
                    break
            
            await page.wait_for_timeout(2000)
            
            # Enter message text
            message_input_selectors = [
                'textarea[placeholder*="Type a message"]',
                'div[role="textbox"]',
                'div[contenteditable="true"]',
                'textarea'
            ]
            
            for selector in message_input_selectors:
                message_input = page.locator(selector)
                if await message_input.count() > 0:
                    await message_input.fill(message_text)
                    break
            
            await page.wait_for_timeout(1000)
            
            # Send the message
            send_button_selectors = [
                'button[aria-label="Send message"]',
                'button:has-text("Send")',
                'div[role="button"]:has-text("Send")'
            ]
            
            for selector in send_button_selectors:
                send_button = page.locator(selector)
                if await send_button.count() > 0:
                    await send_button.click()
                    break
            
            # Wait for message to be sent
            await page.wait_for_timeout(3000)
            
            # Check for error messages
            error_selectors = [
                'div[class*="error"]',
                'p[class*="error"]',
                'span[class*="error"]',
                '.error-message',
                'div[role="alert"]'
            ]
            
            for selector in error_selectors:
                error_elements = page.locator(selector)
                if await error_elements.count() > 0:
                    error_message = await error_elements.first.text_content()
                    if error_message and len(error_message.strip()) > 0:
                        self.logger.error(f"Message sending error: {error_message}")
                        self.db.log_error("message_send", f"Error sending message: {error_message}", account_id)
                        
                        return {
                            "success": False,
                            "error": f"Message sending error: {error_message}"
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
            # Close the page and context
            await page.close()
            await context.close()


async def main():
    """Main function for creating TextNow accounts"""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("textnow_creator.log"),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("TextNowCreatorMain")
    
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
    creator = TextNowCreator(headless=True, proxy_manager=proxy)
    
    try:
        # Start the browser
        success = await creator.start_browser()
        if not success:
            logger.error("Failed to start browser. Exiting.")
            return
        
        # Create a single account
        result = await creator.create_account(area_code="954")
        
        if result["success"]:
            logger.info(f"Account created successfully: {result['phone_number']}")
            
            # Try sending a test message
            send_result = await creator.send_message(
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
    finally:
        # Stop the browser
        await creator.stop_browser()

if __name__ == "__main__":
    asyncio.run(main())