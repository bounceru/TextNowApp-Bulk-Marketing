"""
TextNow Automation Module for ProgressGhostCreator

This module handles all TextNow automation tasks, including:
- Creating new TextNow accounts
- Logging in to existing accounts
- Sending messages
- Setting up voicemail greetings
- Managing account settings
- Android emulator integration for TextNow mobile app
"""

import os
import time
import random
import logging
import json
import re
import asyncio
import datetime
import subprocess
from typing import Dict, List, Tuple, Optional, Union, Any
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Error as PlaywrightError

# Database access for account information
from database_schema import get_database

# Android device integration
try:
    from device_manager import DeviceManager
    from emulator_controller import EmulatorController
except ImportError:
    logger.warning("Android device management modules not available")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('textnow_automation.log')
    ]
)
logger = logging.getLogger('TextNowAutomation')

class TextNowAutomation:
    """Class to handle all TextNow automation tasks"""
    
    TEXTNOW_URL = "https://www.textnow.com"
    SIGNUP_URL = "https://www.textnow.com/signup"
    LOGIN_URL = "https://www.textnow.com/login"
    MESSAGES_URL = "https://www.textnow.com/messaging"
    
    def __init__(self, headless=True, proxy=None, user_data_dir=None, device_manager=None):
        """Initialize TextNow automation with optional proxy support and Android device manager"""
        self.headless = headless
        self.proxy = proxy
        self.user_data_dir = user_data_dir or os.path.join(os.getcwd(), "browser_profiles")
        self.device_manager = device_manager
        
        # Check for TextNow APK file
        self.apk_path = os.path.join(os.getcwd(), "textnow.apk")
        if not os.path.exists(self.apk_path):
            logger.warning(f"TextNow APK not found at {self.apk_path}")
        else:
            logger.info(f"Found TextNow APK at {self.apk_path}")
            
        # Initialize Android emulator if device manager is provided
        if self.device_manager:
            logger.info("Android device manager provided, will use mobile app automation")
        else:
            logger.info("No device manager provided, will use web automation only")
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.database = get_database()
        
        # Create browser profiles directory if it doesn't exist
        os.makedirs(self.user_data_dir, exist_ok=True)
        
        # For account status tracking
        self.current_account_id = None
        self.current_phone_number = None
    
    async def start(self):
        """Start Playwright and open browser"""
        try:
            self.playwright = await async_playwright().start()
            
            # Use the chromium browser (less likely to be detected than Chrome)
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                proxy=self.proxy if self.proxy else None,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )
            
            logger.info("Playwright browser started")
            return True
        except Exception as e:
            logger.error(f"Error starting Playwright: {str(e)}")
            await self.cleanup()
            return False
    
    async def cleanup(self):
        """Close browser and stop Playwright"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
                
            logger.info("Playwright resources cleaned up")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    @asynccontextmanager
    async def get_context(self, profile_name=None, account_id=None):
        """Get a browser context, optionally with a specific profile"""
        # If account_id is provided, use it to get the profile name
        if account_id and not profile_name:
            account = self.database.get_account(account_id=account_id)
            if account:
                profile_name = f"account_{account_id}"
        
        # Use a persistent context for better cookie and storage handling
        user_data_dir = None
        if profile_name:
            user_data_dir = os.path.join(self.user_data_dir, profile_name)
            os.makedirs(user_data_dir, exist_ok=True)
        
        # Create a context with anti-detection measures
        context = await self.browser.new_context(
            user_agent=self._generate_user_agent(),
            viewport=self._random_viewport(),
            locale="en-US",
            timezone_id="America/New_York",
            user_data_dir=user_data_dir,
            java_script_enabled=True,
            accept_downloads=True
        )
        
        # Add additional anti-detection measures
        await self._apply_stealth_settings(context)
        
        try:
            yield context
        finally:
            await context.close()
    
    async def _apply_stealth_settings(self, context):
        """Apply stealth settings to avoid detection"""
        # Emulate WebGL vendor and renderer for fingerprinting prevention
        webgl_vendor = "Google Inc. (Intel)"
        webgl_renderer = "ANGLE (Intel, Intel(R) UHD Graphics Direct3D11 vs_5_0 ps_5_0, D3D11)"
        
        # Execute scripts to modify browser fingerprinting surfaces
        await context.add_init_script("""
            // Override WebGL vendor and renderer
            const getParameterProxyHandler = {
                apply: function(target, thisArg, args) {
                    if (args[0] === 37445) {
                        return "%s";
                    } else if (args[0] === 37446) {
                        return "%s";
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
            
            // Spoof screen resolution
            Object.defineProperty(window.screen, 'height', { get: () => %d });
            Object.defineProperty(window.screen, 'width', { get: () => %d });
            Object.defineProperty(window.screen, 'availHeight', { get: () => %d });
            Object.defineProperty(window.screen, 'availWidth', { get: () => %d });
            
            // Spoof color depth
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """ % (
            webgl_vendor, 
            webgl_renderer,
            random.choice([768, 800, 900, 1024, 1080]),  # height
            random.choice([1280, 1366, 1440, 1600, 1920]),  # width
            random.choice([728, 760, 860, 984, 1040]),  # availHeight
            random.choice([1260, 1346, 1420, 1580, 1900])  # availWidth
        ))
    
    def _generate_user_agent(self):
        """Generate a realistic user agent string"""
        # Different Chrome versions
        chrome_versions = [
            "110.0.5481.177",
            "111.0.5563.64",
            "112.0.5615.49",
            "113.0.5672.63",
            "114.0.5735.90"
        ]
        
        # Different OS versions
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
        # Common screen resolutions
        widths = [1280, 1366, 1440, 1600, 1920]
        heights = [720, 768, 800, 900, 1080]
        
        return {
            "width": random.choice(widths),
            "height": random.choice(heights)
        }
    
    # Android-specific methods
    def initialize_emulator(self):
        """Initialize the Android emulator for TextNow automation"""
        if not self.device_manager:
            logger.warning("No device manager provided, cannot initialize emulator")
            return False
            
        try:
            # Start the emulator if it's not already running
            if not self.device_manager.is_device_connected():
                logger.info("Starting Android emulator")
                self.device_manager.start_emulator()
                
                # Wait for emulator to start
                max_wait = 60
                for i in range(max_wait):
                    if self.device_manager.is_device_connected():
                        logger.info(f"Emulator started after {i+1} seconds")
                        break
                    time.sleep(1)
                    
                if not self.device_manager.is_device_connected():
                    logger.error(f"Emulator failed to start after {max_wait} seconds")
                    return False
            
            # Install TextNow APK if needed
            if not self.device_manager.is_app_installed("com.enflick.android.TextNow"):
                if os.path.exists(self.apk_path):
                    logger.info(f"Installing TextNow APK from {self.apk_path}")
                    self.device_manager.install_app(self.apk_path)
                else:
                    logger.error(f"TextNow APK not found at {self.apk_path}")
                    return False
            
            logger.info("Android emulator initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing emulator: {str(e)}")
            return False
    
    def create_account_mobile(self, name, email, password, area_code=None):
        """Create a new TextNow account using the mobile app"""
        if not self.device_manager:
            logger.error("No device manager available for mobile account creation")
            return False, "No device manager available"
        
        try:
            # Initialize emulator
            if not self.initialize_emulator():
                return False, "Failed to initialize emulator"
            
            # Launch TextNow app
            self.device_manager.launch_app("com.enflick.android.TextNow")
            time.sleep(2)
            
            # Check if we need to sign up (look for sign up button)
            if self.device_manager.find_element_by_text("Sign Up"):
                logger.info("Found Sign Up button, proceeding with account creation")
                self.device_manager.tap_element_by_text("Sign Up")
                time.sleep(1)
                
                # Fill email
                email_field = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/email")
                if email_field:
                    self.device_manager.type_text(email_field, email)
                else:
                    return False, "Email field not found"
                    
                # Fill password
                password_field = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/password")
                if password_field:
                    self.device_manager.type_text(password_field, password)
                else:
                    return False, "Password field not found"
                
                # Tap Next button
                next_button = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/next_button")
                if next_button:
                    self.device_manager.tap_element(next_button)
                else:
                    return False, "Next button not found"
                    
                # Wait for area code selection
                time.sleep(3)
                
                # Select area code if provided
                if area_code:
                    logger.info(f"Selecting area code: {area_code}")
                    area_code_field = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/area_code")
                    if area_code_field:
                        self.device_manager.tap_element(area_code_field)
                        time.sleep(1)
                        
                        # Type area code
                        self.device_manager.type_text(None, area_code)
                        time.sleep(1)
                        
                        # Select the first result
                        self.device_manager.tap_coordinates(300, 400)  # Approximate position of first result
                    else:
                        logger.warning("Area code field not found, using random area code")
                
                # Tap Next/Continue button to complete signup
                continue_button = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/next_button")
                if continue_button:
                    self.device_manager.tap_element(continue_button)
                else:
                    return False, "Continue button not found"
                
                # Wait for account creation and verification
                time.sleep(10)
                
                # Check if we have a phone number assigned (success indicator)
                if self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/phone_number"):
                    phone_number = self.device_manager.get_element_text("com.enflick.android.TextNow:id/phone_number")
                    logger.info(f"Successfully created account with phone number: {phone_number}")
                    return True, phone_number
                else:
                    return False, "Phone number not assigned"
            else:
                logger.error("Could not find Sign Up button in TextNow app")
                return False, "Sign Up button not found"
                
        except Exception as e:
            logger.error(f"Error creating mobile account: {str(e)}")
            return False, str(e)
    
    def send_message_mobile(self, phone_number, message):
        """Send a message using the TextNow mobile app"""
        if not self.device_manager:
            logger.error("No device manager available for mobile messaging")
            return False, "No device manager available"
        
        try:
            # Initialize emulator
            if not self.initialize_emulator():
                return False, "Failed to initialize emulator"
            
            # Launch TextNow app
            self.device_manager.launch_app("com.enflick.android.TextNow")
            time.sleep(2)
            
            # Tap on new message button
            new_message_button = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/fab")
            if new_message_button:
                self.device_manager.tap_element(new_message_button)
            else:
                return False, "New message button not found"
            
            time.sleep(1)
            
            # Enter recipient phone number
            recipient_field = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/recipient_text_field")
            if recipient_field:
                self.device_manager.type_text(recipient_field, phone_number)
            else:
                return False, "Recipient field not found"
                
            time.sleep(1)
            
            # Tap on the contact/phone number to select it
            self.device_manager.tap_coordinates(300, 400)  # Approximate position of first result
            time.sleep(1)
            
            # Enter message text
            message_field = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/compose_edit_text")
            if message_field:
                self.device_manager.type_text(message_field, message)
            else:
                return False, "Message field not found"
            
            # Tap send button
            send_button = self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/send_button")
            if send_button:
                self.device_manager.tap_element(send_button)
            else:
                return False, "Send button not found"
                
            time.sleep(2)
            
            # Check for message sent indicator
            if self.device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/message_status"):
                logger.info(f"Message sent to {phone_number}")
                return True, "Message sent successfully"
            else:
                return False, "Message sending status unknown"
                
        except Exception as e:
            logger.error(f"Error sending mobile message: {str(e)}")
            return False, str(e)
    
    async def create_account(self, name, email, password, area_code=None):
        """Create a new TextNow account"""
        try:
            async with self.get_context() as context:
                # Open a new page
                page = await context.new_page()
                self.page = page
                
                # Navigate to the signup page
                logger.info(f"Navigating to TextNow signup page")
                await page.goto(self.SIGNUP_URL)
                
                # Wait for the page to load
                await page.wait_for_load_state("networkidle")
                
                # Check if we need to accept cookies
                try:
                    accept_cookies = page.locator('button:has-text("Accept")')
                    if await accept_cookies.is_visible(timeout=5000):
                        await accept_cookies.click()
                        logger.info("Accepted cookies")
                except Exception:
                    logger.info("No cookie acceptance needed")
                
                # Fill out the form
                logger.info(f"Filling signup form for {email}")
                
                # Email field
                await page.fill('input[name="email"]', email)
                
                # Password field
                await page.fill('input[name="password"]', password)
                
                # First and Last name split from full name
                name_parts = name.split(' ', 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                # Fill name fields if they exist
                try:
                    await page.fill('input[name="firstName"]', first_name)
                    await page.fill('input[name="lastName"]', last_name)
                except:
                    # Some versions might use different field names or a single name field
                    try:
                        await page.fill('input[name="name"]', name)
                    except:
                        logger.warning("Could not find name fields")
                
                # Submit form
                logger.info("Submitting signup form")
                
                # Try different possible submit buttons
                try:
                    # Look for a button with text like "Sign Up", "Create Account", etc.
                    signup_button = page.locator('button:has-text("Sign Up"), button:has-text("Create Account"), button:has-text("Register"), input[type="submit"]').first
                    await signup_button.click()
                except:
                    logger.warning("Could not find standard signup button, trying form submission")
                    # Fallback to form submission
                    await page.evaluate('document.querySelector("form").submit()')
                
                # Wait for navigation to complete
                await page.wait_for_load_state("networkidle")
                
                # Check for errors
                error_message = await self._check_for_signup_errors(page)
                if error_message:
                    logger.error(f"Signup error: {error_message}")
                    return {
                        "success": False,
                        "error": error_message
                    }
                
                # Wait for phone number selection page
                logger.info("Waiting for phone number selection")
                await self._wait_for_element(page, 'input[placeholder*="Area code"], input[placeholder*="area code"], input[placeholder*="search"], div[aria-label*="area code"]', timeout=30000)
                
                # Enter area code if provided
                if area_code:
                    logger.info(f"Searching for area code: {area_code}")
                    
                    # Try different possible area code input fields
                    try:
                        area_code_input = page.locator('input[placeholder*="Area code"], input[placeholder*="area code"], input[placeholder*="search"], div[aria-label*="area code"]').first
                        await area_code_input.fill(area_code)
                        await area_code_input.press("Enter")
                        
                        # Wait for search results
                        await page.wait_for_timeout(2000)
                    except:
                        logger.warning(f"Could not enter area code {area_code}")
                
                # Select the first available phone number
                logger.info("Selecting a phone number")
                
                # Try different ways to select a phone number
                try:
                    # Look for phone number containers or buttons
                    number_selector = 'div[role="button"]:has-text("+1"), button:has-text("+1"), div.phone-number, div:has-text("+1")'
                    await page.wait_for_selector(number_selector, timeout=10000)
                    
                    # Click on the first available phone number
                    phone_numbers = page.locator(number_selector)
                    
                    if await phone_numbers.count() > 0:
                        await phone_numbers.first.click()
                        logger.info("Selected a phone number")
                    else:
                        logger.error("No phone numbers available to select")
                        return {
                            "success": False,
                            "error": "No phone numbers available"
                        }
                except Exception as e:
                    logger.error(f"Error selecting phone number: {str(e)}")
                    return {
                        "success": False,
                        "error": f"Error selecting phone number: {str(e)}"
                    }
                
                # Wait for the messaging page to load
                try:
                    await page.wait_for_url("**/messaging", timeout=30000)
                    logger.info("Successfully created account and reached messaging page")
                except:
                    logger.error("Failed to reach messaging page after selecting number")
                    return {
                        "success": False,
                        "error": "Failed to reach messaging page"
                    }
                
                # Extract the phone number
                phone_number = await self._extract_phone_number(page)
                if not phone_number:
                    logger.error("Could not extract phone number from page")
                    return {
                        "success": False,
                        "error": "Could not extract phone number"
                    }
                
                # Extract actual area code from the phone number
                actual_area_code = phone_number[2:5] if phone_number.startswith("+1") else phone_number[:3]
                
                # Get cookies and local storage for future sessions
                cookies = await context.cookies()
                storage_state = await context.storage_state()
                
                # Generate a username from the name
                username = self._generate_username(name)
                
                # Save the account in the database
                logger.info(f"Saving account with phone number {phone_number}")
                try:
                    account_id = self.database.add_account(
                        phone_number=phone_number,
                        name=name,
                        username=username,
                        password=password,
                        area_code=actual_area_code,
                        email=email,
                        status='active',
                        user_agent=self._generate_user_agent(),
                        fingerprint=json.dumps(storage_state),
                        ip_used=await self._get_current_ip(page)
                    )
                    
                    # Update the account with cookies
                    self.database.update_account(
                        account_id=account_id,
                        login_cookie=json.dumps(cookies)
                    )
                    
                    logger.info(f"Account created successfully with ID: {account_id}")
                except Exception as e:
                    logger.error(f"Error saving account to database: {str(e)}")
                    return {
                        "success": True,
                        "account_id": None,
                        "phone_number": phone_number,
                        "area_code": actual_area_code,
                        "error": f"Account created but failed to save to database: {str(e)}"
                    }
                
                return {
                    "success": True,
                    "account_id": account_id,
                    "phone_number": phone_number,
                    "area_code": actual_area_code
                }
                
        except Exception as e:
            logger.error(f"Error creating TextNow account: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def login(self, account_id=None, phone_number=None, email=None, password=None):
        """Login to an existing TextNow account"""
        # Get account details from database if account_id or phone_number is provided
        account = None
        if account_id or phone_number:
            account = self.database.get_account(account_id=account_id, phone_number=phone_number)
            if not account:
                logger.error(f"Account not found in database")
                return {
                    "success": False,
                    "error": "Account not found"
                }
            
            email = account['email']
            password = account['password']
        
        if not email or not password:
            logger.error("Login requires either account_id/phone_number or email/password")
            return {
                "success": False,
                "error": "Missing login credentials"
            }
        
        try:
            profile_name = f"account_{account_id}" if account_id else None
            async with self.get_context(profile_name=profile_name) as context:
                # Open a new page
                page = await context.new_page()
                self.page = page
                
                # Try to restore session from cookies if available
                restored_session = False
                if account and account.get('login_cookie'):
                    try:
                        cookies = json.loads(account['login_cookie'])
                        await context.add_cookies(cookies)
                        
                        # Try to go directly to messaging
                        await page.goto(self.MESSAGES_URL)
                        await page.wait_for_load_state("networkidle")
                        
                        # Check if we're actually logged in
                        if not await self._is_login_page(page):
                            logger.info("Successfully restored session from cookies")
                            restored_session = True
                            
                            # Update the current account info
                            self.current_account_id = account_id
                            self.current_phone_number = account['phone_number']
                            
                            # Check account health
                            await self._check_account_health(page, account_id)
                            
                            return {
                                "success": True,
                                "account_id": account_id,
                                "phone_number": account['phone_number'],
                                "method": "cookie"
                            }
                    except Exception as e:
                        logger.warning(f"Failed to restore session from cookies: {str(e)}")
                
                # If session restoration failed, do a normal login
                if not restored_session:
                    logger.info(f"Performing normal login for {email}")
                    
                    # Navigate to the login page
                    await page.goto(self.LOGIN_URL)
                    await page.wait_for_load_state("networkidle")
                    
                    # Check for cookie acceptance
                    try:
                        accept_cookies = page.locator('button:has-text("Accept")')
                        if await accept_cookies.is_visible(timeout=5000):
                            await accept_cookies.click()
                    except:
                        pass
                    
                    # Fill the login form
                    await page.fill('input[type="email"], input[name="email"], input[placeholder*="Email"]', email)
                    await page.fill('input[type="password"], input[name="password"], input[placeholder*="Password"]', password)
                    
                    # Submit the form
                    try:
                        login_button = page.locator('button:has-text("Sign In"), button:has-text("Log In"), button[type="submit"], input[type="submit"]').first
                        await login_button.click()
                    except:
                        # Fallback to form submission
                        await page.evaluate('document.querySelector("form").submit()')
                    
                    # Wait for navigation
                    await page.wait_for_load_state("networkidle")
                    
                    # Check for login errors
                    error_message = await self._check_for_login_errors(page)
                    if error_message:
                        logger.error(f"Login error: {error_message}")
                        
                        # If the account exists in DB, update its status
                        if account_id:
                            if "password" in error_message.lower():
                                self.database.update_account(account_id, status="blocked")
                            else:
                                self.database.log_health_check(
                                    account_id=account_id,
                                    check_type="login",
                                    status="failed",
                                    score=0,
                                    details={"error": error_message}
                                )
                        
                        return {
                            "success": False,
                            "error": error_message
                        }
                    
                    # Check if we're on the messaging page or if we need to select a number
                    current_url = page.url
                    logger.info(f"Current URL after login: {current_url}")
                    
                    if "messaging" not in current_url:
                        # We might need to select a phone number
                        try:
                            await self._wait_for_element(page, 'div[role="button"]:has-text("+1"), button:has-text("+1"), div.phone-number', timeout=10000)
                            logger.info("Need to select a phone number after login")
                            
                            # Click on the first available phone number
                            phone_numbers = page.locator('div[role="button"]:has-text("+1"), button:has-text("+1"), div.phone-number')
                            if await phone_numbers.count() > 0:
                                await phone_numbers.first.click()
                                logger.info("Selected a phone number after login")
                                
                                # Wait for the messaging page
                                await page.wait_for_url("**/messaging", timeout=15000)
                            else:
                                logger.error("No phone numbers available to select after login")
                                return {
                                    "success": False,
                                    "error": "No phone numbers available"
                                }
                        except Exception as e:
                            logger.error(f"Error during post-login flow: {str(e)}")
                            return {
                                "success": False,
                                "error": f"Error during post-login flow: {str(e)}"
                            }
                    
                    # Extract the phone number if we're on the messaging page
                    phone_number = await self._extract_phone_number(page)
                    
                    if not phone_number:
                        logger.error("Could not extract phone number after login")
                        return {
                            "success": False,
                            "error": "Could not extract phone number"
                        }
                    
                    # Save cookies for future sessions
                    cookies = await context.cookies()
                    storage_state = await context.storage_state()
                    
                    # Update the account in the database if it exists
                    if account_id:
                        self.database.update_account(
                            account_id=account_id,
                            login_cookie=json.dumps(cookies),
                            fingerprint=json.dumps(storage_state),
                            last_used=datetime.datetime.now().isoformat(),
                            status='active'
                        )
                        
                        # Log a successful health check
                        self.database.log_health_check(
                            account_id=account_id,
                            check_type="login",
                            status="passed",
                            score=100,
                            details={"method": "password"}
                        )
                    # If the account doesn't exist in our DB but we have phone_number and credentials,
                    # we could add it to the database here
                    
                    # Update the current account info
                    self.current_account_id = account_id
                    self.current_phone_number = phone_number
                    
                    return {
                        "success": True,
                        "account_id": account_id,
                        "phone_number": phone_number,
                        "method": "password"
                    }
                    
        except Exception as e:
            logger.error(f"Error logging in to TextNow: {str(e)}")
            return {
                "success": False, 
                "error": str(e)
            }
    
    async def send_message(self, recipient, message, account_id=None, image_paths=None):
        """Send a message from the currently logged in account or specified account"""
        # Make sure we're logged in
        if not self.page and not account_id:
            logger.error("No active session and no account_id provided")
            return {
                "success": False,
                "error": "No active session"
            }
        
        # If an account_id is provided, log in first
        if account_id:
            login_result = await self.login(account_id=account_id)
            if not login_result['success']:
                return login_result
        
        try:
            # Get the current page or context
            page = self.page
            
            # Make sure we're on the messaging page
            if not page.url.startswith(self.MESSAGES_URL):
                await page.goto(self.MESSAGES_URL)
                await page.wait_for_load_state("networkidle")
            
            # Start a new conversation
            logger.info(f"Starting new conversation with {recipient}")
            
            # Click on new conversation button
            new_conversation_button = page.locator('button[aria-label="New conversation"], div[aria-label="New conversation"], button:has-text("New message")')
            await new_conversation_button.click()
            
            # Wait for the recipient input field
            await self._wait_for_element(page, 'input[placeholder*="Enter name or number"], input[aria-label*="number"], input[placeholder*="Type a name or number"]')
            
            # Enter the recipient
            recipient_input = page.locator('input[placeholder*="Enter name or number"], input[aria-label*="number"], input[placeholder*="Type a name or number"]')
            await recipient_input.fill(recipient)
            await page.wait_for_timeout(1000)
            
            # Press Enter or click a "Next" button to confirm recipient
            try:
                await recipient_input.press("Enter")
            except:
                next_button = page.locator('button:has-text("Next"), button:has-text("Continue"), button[type="submit"]')
                if await next_button.count() > 0:
                    await next_button.click()
            
            # Wait for the message input to appear
            await self._wait_for_element(page, 'div[contenteditable="true"], textarea[placeholder*="message"], textarea[aria-label*="message"]')
            
            # If we have images to send
            if image_paths and len(image_paths) > 0:
                for image_path in image_paths:
                    if os.path.exists(image_path):
                        logger.info(f"Attaching image: {image_path}")
                        
                        # Click the attachment button
                        attachment_button = page.locator('button[aria-label="Add attachment"], button[aria-label="Attach"], div[aria-label*="attachment"]')
                        await attachment_button.click()
                        
                        # Wait for the file input to appear
                        await page.wait_for_timeout(1000)
                        
                        # Find and use the file input
                        file_input = page.locator('input[type="file"]')
                        await file_input.set_input_files(image_path)
                        
                        # Wait for the image to upload
                        await page.wait_for_timeout(2000)
                    else:
                        logger.warning(f"Image file not found: {image_path}")
            
            # Enter the message text
            message_input = page.locator('div[contenteditable="true"], textarea[placeholder*="message"], textarea[aria-label*="message"]')
            
            # For contenteditable divs we need to use evaluate
            if "contenteditable" in await message_input.get_attribute("contenteditable", timeout=1000):
                await page.evaluate(f'document.querySelector("div[contenteditable=\\"true\\"]").innerHTML = "{message}"')
            else:
                await message_input.fill(message)
            
            # Send the message
            logger.info("Sending message")
            send_button = page.locator('button[aria-label="Send message"], button:has-text("Send"), button[type="submit"]')
            await send_button.click()
            
            # Wait a moment for the message to be sent
            await page.wait_for_timeout(2000)
            
            # Check if the message was sent successfully
            # Look for elements that indicate success or failure
            try:
                error_indicator = page.locator('div.error, div[aria-label*="error"], p.error-text')
                if await error_indicator.count() > 0:
                    error_text = await error_indicator.text_content()
                    logger.error(f"Error sending message: {error_text}")
                    
                    # Log the error in the database
                    if self.current_account_id:
                        self.database.log_health_check(
                            account_id=self.current_account_id,
                            check_type="message",
                            status="failed",
                            score=30,
                            details={"error": error_text, "recipient": recipient}
                        )
                    
                    return {
                        "success": False,
                        "error": error_text
                    }
            except:
                # No error found
                pass
            
            # Log the successful message in the database
            message_id = None
            if self.current_account_id:
                message_id = self.database.add_message(
                    account_id=self.current_account_id,
                    recipient=recipient,
                    content=message,
                    images=json.dumps(image_paths) if image_paths else None,
                    scheduled_time=None,
                    campaign_id=None
                )
                
                # Update the message status to sent
                self.database.update_message_status(
                    message_id=message_id,
                    status="sent",
                    sent_time=datetime.datetime.now().isoformat()
                )
                
                # Log a successful health check
                self.database.log_health_check(
                    account_id=self.current_account_id,
                    check_type="message",
                    status="passed",
                    score=100,
                    details={"recipient": recipient}
                )
            
            logger.info("Message sent successfully")
            return {
                "success": True,
                "message_id": message_id
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            
            # Log the error in the database
            if self.current_account_id:
                self.database.log_health_check(
                    account_id=self.current_account_id,
                    check_type="message",
                    status="failed",
                    score=30,
                    details={"error": str(e), "recipient": recipient}
                )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def setup_voicemail(self, account_id, voicemail_path):
        """Setup a voicemail greeting for an account"""
        if not os.path.exists(voicemail_path):
            logger.error(f"Voicemail file not found: {voicemail_path}")
            return {
                "success": False,
                "error": "Voicemail file not found"
            }
        
        # Login to the account
        login_result = await self.login(account_id=account_id)
        if not login_result['success']:
            return login_result
        
        try:
            page = self.page
            
            # Navigate to settings
            logger.info("Navigating to settings")
            
            # Look for settings button and click it
            settings_button = page.locator('button[aria-label="Settings"], a[href*="settings"], button:has-text("Settings")')
            await settings_button.click()
            
            # Wait for settings page to load
            await page.wait_for_load_state("networkidle")
            
            # Look for voicemail section
            logger.info("Looking for voicemail settings")
            voicemail_section = page.locator('a:has-text("Voicemail"), button:has-text("Voicemail"), div:has-text("Voicemail greeting")')
            await voicemail_section.click()
            
            # Wait for voicemail settings to load
            await page.wait_for_timeout(2000)
            
            # Look for "Custom greeting" option
            custom_greeting = page.locator('button:has-text("Custom"), label:has-text("Custom"), div:has-text("Custom greeting")')
            await custom_greeting.click()
            
            # Wait for file input to be available
            await page.wait_for_timeout(1000)
            
            # Find file input and upload voicemail file
            file_input = page.locator('input[type="file"]')
            await file_input.set_input_files(voicemail_path)
            
            # Wait for upload to complete
            await page.wait_for_timeout(5000)
            
            # Look for save/confirm button
            save_button = page.locator('button:has-text("Save"), button:has-text("Confirm"), button[type="submit"]')
            await save_button.click()
            
            # Wait for confirmation
            await page.wait_for_timeout(2000)
            
            # Update the account in the database
            voicemail_id = None
            try:
                # First add the voicemail to the database if it's not already there
                voicemail_records = self.database.get_voicemails()
                for record in voicemail_records:
                    if record['file_path'] == voicemail_path:
                        voicemail_id = record['id']
                        break
                
                if not voicemail_id:
                    # Add new voicemail record
                    voicemail_id = self.database.add_voicemail(
                        file_path=voicemail_path,
                        duration=None,  # We could calculate this if needed
                        voice_type="custom",
                        text_content=None,
                        checksum=None
                    )
                
                # Update the account with the voicemail ID
                self.database.update_account(
                    account_id=account_id,
                    voicemail_id=voicemail_id
                )
                
                # Increment voicemail use count
                self.database.increment_voicemail_use_count(voicemail_id)
                
                # Log a successful health check
                self.database.log_health_check(
                    account_id=account_id,
                    check_type="voicemail",
                    status="passed",
                    score=100,
                    details={"voicemail_path": voicemail_path}
                )
            except Exception as e:
                logger.error(f"Error updating database with voicemail info: {str(e)}")
            
            logger.info("Voicemail setup successfully")
            return {
                "success": True,
                "voicemail_id": voicemail_id
            }
            
        except Exception as e:
            logger.error(f"Error setting up voicemail: {str(e)}")
            
            # Log the error in the database
            self.database.log_health_check(
                account_id=account_id,
                check_type="voicemail",
                status="failed",
                score=30,
                details={"error": str(e)}
            )
            
            return {
                "success": False,
                "error": str(e)
            }
    
    async def check_messages(self, account_id):
        """Check for any new messages on an account"""
        # Login to the account
        login_result = await self.login(account_id=account_id)
        if not login_result['success']:
            return login_result
        
        try:
            page = self.page
            
            # Make sure we're on the messaging page
            if not page.url.startswith(self.MESSAGES_URL):
                await page.goto(self.MESSAGES_URL)
                await page.wait_for_load_state("networkidle")
            
            # Look for conversation list
            logger.info("Checking for new messages")
            
            # Wait for conversation list to load
            await self._wait_for_element(page, 'div[role="listbox"], div.conversation-list, ul.conversations', timeout=10000)
            
            # Look for unread conversations (this will depend on TextNow's UI)
            unread_conversations = page.locator('div.unread, div[aria-label*="unread"], div.new-message')
            
            unread_count = await unread_conversations.count()
            logger.info(f"Found {unread_count} unread conversations")
            
            # Process each unread conversation
            new_messages = []
            
            for i in range(unread_count):
                conv = unread_conversations.nth(i)
                await conv.click()
                
                # Wait for conversation to load
                await page.wait_for_timeout(2000)
                
                # Extract the sender
                sender_elem = page.locator('div.header h1, div.conversation-header h1, span.recipient-name')
                sender = await sender_elem.text_content() if await sender_elem.count() > 0 else "Unknown"
                
                # Extract the messages
                message_elems = page.locator('div.message.from-other, div.bubble.inbound')
                
                for j in range(await message_elems.count()):
                    msg_elem = message_elems.nth(j)
                    content = await msg_elem.text_content()
                    
                    # Create message entry
                    new_messages.append({
                        "sender": sender,
                        "content": content
                    })
                    
                    # Add to database
                    # Note: This is simplified - in a real implementation, we'd need to more carefully
                    # track which messages we've already processed
                    message_id = self.database.add_message(
                        account_id=account_id,
                        recipient=sender,  # In this case, it's incoming so the recipient is actually the sender
                        content=content,
                        images=None
                    )
                    
                    self.database.update_message_status(
                        message_id=message_id,
                        status="received",
                        sent_time=datetime.datetime.now().isoformat(),
                        response=content,
                        response_time=datetime.datetime.now().isoformat()
                    )
            
            return {
                "success": True,
                "unread_count": unread_count,
                "messages": new_messages
            }
            
        except Exception as e:
            logger.error(f"Error checking messages: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def logout(self):
        """Logout from the current TextNow session"""
        if not self.page:
            logger.warning("No active session to logout from")
            return {
                "success": True,
                "message": "No active session"
            }
        
        try:
            page = self.page
            
            # Look for settings/menu button
            settings_button = page.locator('button[aria-label="Settings"], button[aria-label="Menu"], div.settings-icon')
            await settings_button.click()
            
            # Wait for menu to appear
            await page.wait_for_timeout(1000)
            
            # Look for logout option
            logout_option = page.locator('button:has-text("Sign Out"), button:has-text("Log Out"), a:has-text("Sign Out")')
            await logout_option.click()
            
            # Wait for logout to complete
            await page.wait_for_url("**/login", timeout=10000)
            
            # Update account status in database
            if self.current_account_id:
                self.database.update_account(
                    account_id=self.current_account_id,
                    last_used=datetime.datetime.now().isoformat()
                )
            
            # Clear current account info
            self.current_account_id = None
            self.current_phone_number = None
            
            logger.info("Successfully logged out")
            return {
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            
            # Even if there's an error, clear the current session info
            self.current_account_id = None
            self.current_phone_number = None
            
            return {
                "success": False,
                "error": str(e)
            }
    
    # Helper methods
    async def _wait_for_element(self, page, selector, timeout=10000):
        """Wait for an element to be present on the page"""
        try:
            await page.wait_for_selector(selector, timeout=timeout)
            return True
        except PlaywrightError:
            logger.warning(f"Timeout waiting for element: {selector}")
            return False
    
    async def _extract_phone_number(self, page):
        """Extract the current account's phone number from the page"""
        try:
            # Try different selectors where the phone number might be displayed
            selectors = [
                'div.user-info-number, span.phone-number, div[aria-label*="phone number"]',
                'header span:has-text("+1")',
                'div:has-text("+1"):not(:has(*))',  # Text-only divs containing +1
                '[aria-label*="phone"]:has-text("+1")'
            ]
            
            for selector in selectors:
                element = page.locator(selector)
                if await element.count() > 0:
                    text = await element.text_content()
                    # Extract phone number using regex to handle different formats
                    phone_match = re.search(r'(\+1\d{10}|\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', text)
                    if phone_match:
                        phone_number = phone_match.group(1)
                        # Normalize the format to +1XXXXXXXXXX
                        if not phone_number.startswith('+1'):
                            # Remove non-digit characters and add +1
                            digits = ''.join(c for c in phone_number if c.isdigit())
                            if len(digits) == 10:
                                phone_number = '+1' + digits
                            elif len(digits) == 11 and digits.startswith('1'):
                                phone_number = '+' + digits
                        return phone_number
            
            # If we couldn't find it with selectors, try extracting it from the page HTML
            html = await page.content()
            phone_match = re.search(r'(\+1\d{10}|\(\d{3}\)\s*\d{3}-\d{4}|\d{3}-\d{3}-\d{4})', html)
            if phone_match:
                phone_number = phone_match.group(1)
                # Normalize the format
                if not phone_number.startswith('+1'):
                    digits = ''.join(c for c in phone_number if c.isdigit())
                    if len(digits) == 10:
                        phone_number = '+1' + digits
                    elif len(digits) == 11 and digits.startswith('1'):
                        phone_number = '+' + digits
                return phone_number
            
            # Last resort: check the URL for a phone number
            url_match = re.search(r'/(\d+)/', page.url)
            if url_match:
                digits = url_match.group(1)
                if len(digits) == 10:
                    return '+1' + digits
            
            logger.warning("Could not extract phone number from page")
            return None
        except Exception as e:
            logger.error(f"Error extracting phone number: {str(e)}")
            return None
    
    async def _check_for_signup_errors(self, page):
        """Check if there are any signup errors displayed on the page"""
        try:
            # Check for error messages
            error_selectors = [
                'div.error-message',
                'div.error',
                'p.error',
                'span.error',
                '.field-error',
                '.alert-danger',
                '[role="alert"]'
            ]
            
            for selector in error_selectors:
                error_elem = page.locator(selector)
                if await error_elem.is_visible(timeout=1000):
                    error_message = await error_elem.text_content()
                    if error_message and len(error_message.strip()) > 0:
                        return error_message.strip()
            
            # Check for specific error patterns in the page content
            content = await page.content()
            error_patterns = [
                r'error.*?:\s*(.*?)<',
                r'alert.*?>\s*(.*?)<',
                r'invalid.*?>\s*(.*?)<'
            ]
            
            for pattern in error_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
            
            return None
        except Exception as e:
            logger.error(f"Error checking for signup errors: {str(e)}")
            return None
    
    async def _check_for_login_errors(self, page):
        """Check if there are any login errors displayed on the page"""
        try:
            # Similar to signup errors, but might have different selectors
            error_selectors = [
                'div.error-message',
                'div.error',
                'p.error',
                'span.error',
                '.field-error',
                '.alert-danger',
                '[role="alert"]'
            ]
            
            for selector in error_selectors:
                error_elem = page.locator(selector)
                if await error_elem.is_visible(timeout=1000):
                    error_message = await error_elem.text_content()
                    if error_message and len(error_message.strip()) > 0:
                        return error_message.strip()
            
            # If we're still on the login page, that's also an error
            if await self._is_login_page(page):
                return "Login failed - still on login page"
            
            return None
        except Exception as e:
            logger.error(f"Error checking for login errors: {str(e)}")
            return None
    
    async def _is_login_page(self, page):
        """Check if we're on the login page"""
        try:
            # Check URL first
            if '/login' in page.url:
                return True
            
            # Look for login form elements
            login_elements = [
                'input[name="email"]',
                'input[name="password"]',
                'button:has-text("Sign In")',
                'button:has-text("Log In")'
            ]
            
            for selector in login_elements:
                elem = page.locator(selector)
                if await elem.is_visible(timeout=1000):
                    return True
            
            return False
        except Exception:
            return False
    
    async def _get_current_ip(self, page):
        """Get the current external IP address"""
        try:
            # Use an IP checking service
            ip_response = await page.evaluate('''
                async () => {
                    try {
                        const response = await fetch('https://api.ipify.org?format=json');
                        const data = await response.json();
                        return data.ip;
                    } catch (e) {
                        return null;
                    }
                }
            ''')
            
            if ip_response:
                return ip_response
            
            # Alternative method
            ip_response = await page.evaluate('''
                async () => {
                    try {
                        const response = await fetch('https://ifconfig.me/ip');
                        const data = await response.text();
                        return data.trim();
                    } catch (e) {
                        return null;
                    }
                }
            ''')
            
            return ip_response
        except Exception as e:
            logger.error(f"Error getting current IP: {str(e)}")
            return None
    
    def _generate_username(self, name):
        """Generate a username based on a person's name"""
        # Remove spaces and special characters
        base_name = ''.join(c.lower() for c in name if c.isalnum())
        
        # Add some random numbers
        random_numbers = ''.join(random.choices(string.digits, k=4))
        
        # Common username patterns
        patterns = [
            f"{base_name}{random_numbers}",
            f"{base_name}_",
            f"{base_name}.",
            f"the.{base_name}"
        ]
        
        return random.choice(patterns)
    
    async def _check_account_health(self, page, account_id):
        """Check the health of an account based on various indicators"""
        try:
            # Check for warning banners
            warning_selectors = [
                'div.warning-banner',
                'div.account-warning',
                'div[role="alert"]',
                '.notification.warning',
                '.notification.error'
            ]
            
            for selector in warning_selectors:
                warning_elem = page.locator(selector)
                if await warning_elem.is_visible(timeout=1000):
                    warning_text = await warning_elem.text_content()
                    if warning_text and len(warning_text.strip()) > 0:
                        # This is a warning, log it
                        self.database.log_health_check(
                            account_id=account_id,
                            check_type="health",
                            status="warning",
                            score=50,
                            details={"warning": warning_text.strip()}
                        )
                        logger.warning(f"Account {account_id} has warning: {warning_text.strip()}")
                        return False
            
            # Get account settings to check for limitations
            try:
                settings_button = page.locator('button[aria-label="Settings"], a[href*="settings"], button:has-text("Settings")')
                await settings_button.click()
                
                await page.wait_for_load_state("networkidle")
                
                # Look for account status or limitations
                restrictions_elem = page.locator('div:has-text("Account status"), div:has-text("Limitations"), div:has-text("Restrictions")')
                
                if await restrictions_elem.count() > 0:
                    parent_elem = await restrictions_elem.evaluate('el => el.parentElement')
                    parent_text = await page.evaluate('el => el.textContent', parent_elem)
                    
                    if 'restrict' in parent_text.lower() or 'limit' in parent_text.lower() or 'warning' in parent_text.lower():
                        self.database.log_health_check(
                            account_id=account_id,
                            check_type="health",
                            status="warning",
                            score=60,
                            details={"restrictions": parent_text.strip()}
                        )
                        logger.warning(f"Account {account_id} has restrictions: {parent_text.strip()}")
                        return False
                
                # Go back to messaging
                back_button = page.locator('button[aria-label="Back"], button:has-text("Back"), a.back-button')
                await back_button.click()
                
            except Exception as e:
                logger.warning(f"Error checking account settings: {str(e)}")
            
            # If we got here, the account seems healthy
            self.database.log_health_check(
                account_id=account_id,
                check_type="health",
                status="passed",
                score=100,
                details={"message": "Account appears healthy"}
            )
            logger.info(f"Account {account_id} appears healthy")
            return True
            
        except Exception as e:
            logger.error(f"Error checking account health: {str(e)}")
            return False

# Singleton instance for global access
_textnow_automation_instance = None

def get_textnow_automation(headless=True, proxy=None):
    """Get the singleton instance of TextNowAutomation"""
    global _textnow_automation_instance
    if _textnow_automation_instance is None:
        _textnow_automation_instance = TextNowAutomation(headless=headless, proxy=proxy)
    return _textnow_automation_instance

# Example usage
async def main():
    """Example of using the TextNow automation module"""
    # Initialize automation
    automation = TextNowAutomation(headless=False)
    await automation.start()
    
    try:
        # Create a new account
        result = await automation.create_account(
            name="Test User",
            email="test.user" + str(random.randint(1000, 9999)) + "@example.com",
            password="Password123!",
            area_code="954"
        )
        
        print(f"Account creation result: {result}")
        
        # If successful, send a test message
        if result['success']:
            account_id = result['account_id']
            
            # Send a message
            message_result = await automation.send_message(
                account_id=account_id,
                recipient="+15551234567",
                message="This is a test message"
            )
            
            print(f"Message result: {message_result}")
            
            # Set up voicemail
            voicemail_result = await automation.setup_voicemail(
                account_id=account_id,
                voicemail_path="voicemail/greeting1.mp3"
            )
            
            print(f"Voicemail result: {voicemail_result}")
            
            # Check for new messages
            check_result = await automation.check_messages(account_id=account_id)
            
            print(f"Message check result: {check_result}")
            
            # Logout
            await automation.logout()
    finally:
        # Clean up
        await automation.cleanup()

if __name__ == "__main__":
    asyncio.run(main())