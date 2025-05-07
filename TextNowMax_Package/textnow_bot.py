"""
TextNow Bot for ProgressGhostCreator

This module handles the automation of TextNow account creation and management.
"""

import logging
import time
import random
import os
import json
import traceback
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys 
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Import local modules
from device_manager import DeviceManager
from fingerprint_manager import FingerprintManager
from data_manager import DataManager
from token_manager import get_token_manager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TextNowBot:
    def __init__(self, device_manager=None, fingerprint_manager=None, data_manager=None, database_path='ghost_accounts.db'):
        """Initialize the TextNow bot"""
        self.device_manager = device_manager or DeviceManager()
        self.fingerprint_manager = fingerprint_manager or FingerprintManager()
        self.data_manager = data_manager or DataManager()
        self.token_manager = get_token_manager()
        self.driver = None
        self.database_path = database_path
        self.current_ip = None
        self.current_fingerprint = None
        self.current_account = None
    
    def initialize_driver(self, fingerprint=None):
        """Initialize the webdriver with the given fingerprint"""
        try:
            # Close existing driver if any
            if self.driver:
                self.close()
            
            # Get a fingerprint if not provided
            if not fingerprint:
                fingerprint = self.fingerprint_manager.get_random_fingerprint()
            
            self.current_fingerprint = fingerprint
            
            # Set up Chrome options
            chrome_options = Options()
            
            # Apply fingerprint settings
            chrome_options.add_argument(f"--user-agent={fingerprint['user_agent']}")
            chrome_options.add_argument(f"--window-size={fingerprint['screen_width']},{fingerprint['screen_height']}")
            
            # Add additional fingerprint options from the data
            for option in fingerprint.get('browser_options', []):
                chrome_options.add_argument(option)
            
            # Add recommended options for bot operation
            chrome_options.add_argument("--disable-notifications")
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--no-sandbox")
            
            # Add headless mode for production server
            # chrome_options.add_argument("--headless=new")
            
            # Check and set WebDriver to use the device's current IP
            self.current_ip = self.device_manager.get_ip_address()
            logging.info(f"Current IP for account creation: {self.current_ip}")
            
            # Initialize the driver
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set window position if specified in fingerprint
            window_pos_x = fingerprint.get('window_pos_x', 0)
            window_pos_y = fingerprint.get('window_pos_y', 0)
            self.driver.set_window_position(window_pos_x, window_pos_y)
            
            # Set implicit wait time
            self.driver.implicitly_wait(10)
            
            # Execute additional JS to set browser fingerprint
            self.execute_fingerprint_js(fingerprint)
            
            return True
        
        except Exception as e:
            logging.error(f"Failed to initialize WebDriver: {e}")
            logging.error(traceback.format_exc())
            return False
    
    def execute_fingerprint_js(self, fingerprint):
        """Execute JavaScript to modify browser fingerprint"""
        try:
            # Create a JavaScript object with all the fingerprint properties
            js_fingerprint = json.dumps({
                'screen': {
                    'width': fingerprint['screen_width'],
                    'height': fingerprint['screen_height'],
                    'colorDepth': fingerprint.get('color_depth', 24),
                    'availWidth': fingerprint.get('avail_width', fingerprint['screen_width']),
                    'availHeight': fingerprint.get('avail_height', fingerprint['screen_height'] - 40),
                },
                'navigator': {
                    'userAgent': fingerprint['user_agent'],
                    'language': fingerprint.get('language', 'en-US'),
                    'platform': fingerprint.get('platform', 'Win32'),
                    'hardwareConcurrency': fingerprint.get('hardware_concurrency', 8),
                    'deviceMemory': fingerprint.get('device_memory', 8),
                },
                'canvas': {
                    'noise': fingerprint.get('canvas_noise', 0.5),
                }
            })
            
            # Execute JavaScript to override navigator and screen properties
            js_script = f"""
            // Store original functions that we'll modify
            const originalGetContext = HTMLCanvasElement.prototype.getContext;
            
            // Override the Canvas API to add noise
            HTMLCanvasElement.prototype.getContext = function() {{
                const context = originalGetContext.apply(this, arguments);
                if (arguments[0] === '2d') {{
                    const originalFillRect = context.fillRect;
                    context.fillRect = function() {{
                        originalFillRect.apply(this, arguments);
                        // Add subtle noise to canvas rendering
                        const noise = {fingerprint.get('canvas_noise', 0.5)};
                        if (noise > 0) {{
                            const imageData = context.getImageData(0, 0, 10, 10);
                            const pixels = imageData.data;
                            for (let i = 0; i < pixels.length; i += 4) {{
                                const rnd = Math.random() * noise;
                                pixels[i] = Math.max(0, Math.min(255, pixels[i] + rnd));
                                pixels[i + 1] = Math.max(0, Math.min(255, pixels[i + 1] + rnd));
                                pixels[i + 2] = Math.max(0, Math.min(255, pixels[i + 2] + rnd));
                            }}
                            context.putImageData(imageData, 0, 0);
                        }}
                    }};
                }}
                return context;
            }};
            
            // Override navigator properties
            const fingerprint = {js_fingerprint};
            Object.defineProperty(navigator, 'userAgent', {{ get: () => fingerprint.navigator.userAgent }});
            Object.defineProperty(navigator, 'language', {{ get: () => fingerprint.navigator.language }});
            Object.defineProperty(navigator, 'languages', {{ get: () => [fingerprint.navigator.language] }});
            Object.defineProperty(navigator, 'platform', {{ get: () => fingerprint.navigator.platform }});
            Object.defineProperty(navigator, 'hardwareConcurrency', {{ get: () => fingerprint.navigator.hardwareConcurrency }});
            Object.defineProperty(navigator, 'deviceMemory', {{ get: () => fingerprint.navigator.deviceMemory }});
            
            // Override screen properties
            Object.defineProperty(window.screen, 'width', {{ get: () => fingerprint.screen.width }});
            Object.defineProperty(window.screen, 'height', {{ get: () => fingerprint.screen.height }});
            Object.defineProperty(window.screen, 'availWidth', {{ get: () => fingerprint.screen.availWidth }});
            Object.defineProperty(window.screen, 'availHeight', {{ get: () => fingerprint.screen.availHeight }});
            Object.defineProperty(window.screen, 'colorDepth', {{ get: () => fingerprint.screen.colorDepth }});
            Object.defineProperty(window.screen, 'pixelDepth', {{ get: () => fingerprint.screen.colorDepth }});
            """
            
            # Execute the script
            self.driver.execute_script(js_script)
            logging.info("Applied JavaScript fingerprint modifications")
            
        except Exception as e:
            logging.error(f"Failed to execute fingerprint JavaScript: {e}")
    
    def create_account(self, area_code=None):
        """Create a new TextNow account"""
        try:
            # Make sure the WebDriver is initialized
            if not self.driver:
                if not self.initialize_driver():
                    return False, "Failed to initialize WebDriver"
            
            # Get random user data
            user_data = self.data_manager.get_random_user_data()
            if not user_data:
                return False, "Failed to get random user data"
            
            # Store account data for later
            account_data = {
                'username': f"{user_data['username']}_{random.randint(100, 999)}",
                'password': f"PB{user_data['first_name']}!{random.randint(100, 999)}",
                'email': f"{user_data['username']}{random.randint(100, 999)}@progressmail.com",
                'first_name': user_data['first_name'],
                'last_name': user_data['last_name'],
                'area_code': area_code if area_code else random.choice(['201', '240', '301', '302', '303', '304', '305', '308', '309']),
                'fingerprint_id': self.current_fingerprint['id'] if self.current_fingerprint else None,
                'ip_address': self.current_ip,
                'ip_family': self.device_manager.get_ip_family(self.current_ip) if self.current_ip else None,
                'created_at': datetime.now().isoformat(),
                'active': True,
                'flagged': False,
                'health_score': 100.0
            }
            
            logging.info(f"Creating account with username: {account_data['username']}")
            
            # For the demo/EXE version, we'll create a mock account
            if os.environ.get('MOCK_MODE', 'true').lower() == 'true':
                logging.info("MOCK MODE: Simulating TextNow account creation")
                # Generate a random phone number in the format (XXX) XXX-XXXX
                area_code_num = int(account_data['area_code'])
                prefix = random.randint(201, 999)
                line = random.randint(1000, 9999)
                phone_number = f"({area_code_num}) {prefix}-{line}"
                account_data['phone_number'] = phone_number
                
                # Simulate a delay for account creation
                time.sleep(random.uniform(2, 5))
                
                # Choose a random voicemail file
                account_data['voicemail_file'] = self.data_manager.get_random_voicemail_file()
                
                # Save account to database and get the ID
                account_id = self.fingerprint_manager.save_account(account_data)
                
                if account_id:
                    # Generate mock tokens and cookies
                    mock_tokens = {
                        'access_token': f"mock_token_{random.randint(10000, 99999)}",
                        'refresh_token': f"mock_refresh_{random.randint(10000, 99999)}",
                        'user_id': f"user_{random.randint(10000, 99999)}"
                    }
                    
                    # Save tokens and cookies
                    self.token_manager.save_tokens(account_id, mock_tokens, None)
                    logging.info(f"MOCK MODE: Account created successfully: {account_data['username']} with ID {account_id}")
                    
                    # Save account data to CSV as well for backup
                    self.data_manager.save_account(account_data)
                    
                    # Set as current account
                    self.current_account = account_data
                    self.current_account['id'] = account_id
                    
                    return True, account_id
                else:
                    logging.error("MOCK MODE: Failed to save account to database")
                    return False, "Account creation successful but failed to save to database"
            
            # Production code for actual TextNow account creation
            # Navigate to TextNow signup page
            self.driver.get("https://www.textnow.com/signup")
            time.sleep(random.uniform(2, 4))
            
            # Wait for the signup form to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//form[contains(@class, 'signup-form')]"))
            )
            
            # Fill in the signup form
            # Email Field
            email_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "email"))
            )
            self.type_with_random_delays(email_field, account_data['email'])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Username Field
            username_field = self.driver.find_element(By.ID, "username")
            self.type_with_random_delays(username_field, account_data['username'])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Password Field
            password_field = self.driver.find_element(By.ID, "password")
            self.type_with_random_delays(password_field, account_data['password'])
            time.sleep(random.uniform(0.5, 1.5))
            
            # Check terms and conditions checkbox
            terms_checkbox = self.driver.find_element(By.XPATH, "//input[@type='checkbox']")
            if not terms_checkbox.is_selected():
                terms_checkbox.click()
                time.sleep(random.uniform(0.5, 1.0))
            
            # Submit the form
            signup_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            signup_button.click()
            
            # Wait for account creation to complete - this might need a page load wait
            try:
                # Wait for the next page to load - either phone selection or verification
                WebDriverWait(self.driver, 30).until(
                    EC.url_contains("/messaging")
                )
                account_created = True
            except TimeoutException:
                # Check if there's an error message
                try:
                    error_message = self.driver.find_element(By.XPATH, "//div[contains(@class, 'error-message')]").text
                    logging.error(f"Account creation failed: {error_message}")
                    return False, f"Account creation failed: {error_message}"
                except NoSuchElementException:
                    # If we can't find an error message, but we also didn't get redirected, something else is wrong
                    logging.error("Account creation failed: Unexpected page after signup submission")
                    return False, "Account creation failed: Unexpected page after signup"
            
            # Select a phone number with the desired area code
            try:
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'phone-number-selection')]"))
                )
                
                # Enter area code
                area_code_field = self.driver.find_element(By.XPATH, "//input[@placeholder='Search by area code']")
                self.type_with_random_delays(area_code_field, account_data['area_code'])
                time.sleep(random.uniform(1.0, 2.0))
                
                # Search for numbers
                search_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
                search_button.click()
                time.sleep(random.uniform(2.0, 4.0))
                
                # Select a random number from the list
                number_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'phone-number-item')]")
                if number_elements:
                    # Pick a random number
                    number_element = random.choice(number_elements)
                    number_text = number_element.text.strip()
                    number_element.click()
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    # Store the phone number
                    account_data['phone_number'] = number_text
                    logging.info(f"Selected phone number: {number_text}")
                    
                    # Click continue/done
                    continue_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Done')]")
                    continue_button.click()
                    time.sleep(random.uniform(2.0, 4.0))
                else:
                    logging.warning(f"No phone numbers available for area code {account_data['area_code']}")
                    # Try a different area code
                    new_area_code = random.choice(['201', '240', '301', '302', '303', '304', '305', '308', '309'])
                    logging.info(f"Trying different area code: {new_area_code}")
                    
                    # Clear and enter new area code
                    area_code_field.clear()
                    self.type_with_random_delays(area_code_field, new_area_code)
                    time.sleep(random.uniform(1.0, 2.0))
                    
                    # Search again
                    search_button.click()
                    time.sleep(random.uniform(2.0, 4.0))
                    
                    # Try to select a number again
                    number_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'phone-number-item')]")
                    if number_elements:
                        # Pick a random number
                        number_element = random.choice(number_elements)
                        number_text = number_element.text.strip()
                        number_element.click()
                        time.sleep(random.uniform(1.0, 2.0))
                        
                        # Store the phone number
                        account_data['phone_number'] = number_text
                        account_data['area_code'] = new_area_code
                        logging.info(f"Selected phone number: {number_text}")
                        
                        # Click continue/done
                        continue_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Continue') or contains(text(), 'Done')]")
                        continue_button.click()
                        time.sleep(random.uniform(2.0, 4.0))
                    else:
                        logging.error("Could not find any available phone numbers")
                        return False, "Account creation failed: No phone numbers available"
            except Exception as e:
                logging.error(f"Error during phone number selection: {e}")
                # Try to check if we're already on the messaging page (might mean number selection was skipped)
                try:
                    if "/messaging" in self.driver.current_url:
                        # We're already on the messaging page, which is good
                        logging.info("Already on messaging page, continuing with setup")
                    else:
                        # Not on messaging page and phone selection failed
                        return False, f"Failed during phone number selection: {str(e)}"
                except:
                    return False, f"Failed during phone number selection: {str(e)}"
            
            # Save the account cookies and tokens
            try:
                # Get cookies
                cookies = self.driver.get_cookies()
                
                # Get localStorage tokens if available
                tokens = self.driver.execute_script("""
                return {
                    access_token: localStorage.getItem('access_token'),
                    refresh_token: localStorage.getItem('refresh_token'),
                    user_id: localStorage.getItem('user_id')
                };
                """)
                
                # Save account to database and get the ID
                account_id = self.fingerprint_manager.save_account(account_data)
                
                if account_id:
                    # Save tokens and cookies
                    self.token_manager.save_tokens(account_id, tokens, cookies)
                    logging.info(f"Account created successfully: {account_data['username']} with ID {account_id}")
                    
                    # Save account data to CSV as well for backup
                    self.data_manager.save_account(account_data)
                    
                    # Set as current account
                    self.current_account = account_data
                    self.current_account['id'] = account_id
                    
                    return True, account_id
                else:
                    logging.error("Failed to save account to database")
                    return False, "Account creation successful but failed to save to database"
            
            except Exception as e:
                logging.error(f"Error saving account data: {e}")
                return False, f"Account created but failed to save data: {str(e)}"
        
        except Exception as e:
            logging.error(f"Account creation failed: {e}")
            logging.error(traceback.format_exc())
            return False, f"Account creation failed: {str(e)}"
    
    def login(self, username, password, account_id=None):
        """Log in to an existing TextNow account"""
        try:
            # Make sure the WebDriver is initialized
            if not self.driver:
                if not self.initialize_driver():
                    return False, "Failed to initialize WebDriver"
            
            # First try to use existing tokens/cookies if account_id is provided
            if account_id:
                cookies = self.token_manager.get_cookies(account_id)
                if cookies:
                    # Navigate to TextNow
                    self.driver.get("https://www.textnow.com")
                    time.sleep(2)
                    
                    # Add the cookies
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except Exception as e:
                            logging.warning(f"Failed to add cookie: {e}")
                    
                    # Refresh the page
                    self.driver.refresh()
                    time.sleep(3)
                    
                    # Check if we're logged in
                    try:
                        WebDriverWait(self.driver, 10).until(
                            EC.url_contains("/messaging")
                        )
                        logging.info(f"Successfully logged in using cookies for account ID {account_id}")
                        return True, "Login successful using cookies"
                    except TimeoutException:
                        logging.info("Cookie login failed, falling back to username/password")
            
            # For demo/EXE mode, simulate a successful login
            if os.environ.get('MOCK_MODE', 'true').lower() == 'true':
                logging.info(f"MOCK MODE: Simulating login for username: {username}")
                time.sleep(random.uniform(1, 3))
                logging.info(f"MOCK MODE: Successfully logged in as {username}")
                
                # If account_id is provided, create mock tokens
                if account_id:
                    # Generate mock tokens
                    mock_tokens = {
                        'access_token': f"mock_token_{random.randint(10000, 99999)}",
                        'refresh_token': f"mock_refresh_{random.randint(10000, 99999)}",
                        'user_id': f"user_{random.randint(10000, 99999)}"
                    }
                    
                    # Save tokens
                    self.token_manager.save_tokens(account_id, mock_tokens, None)
                    logging.info(f"MOCK MODE: Updated tokens for account ID {account_id}")
                
                return True, "MOCK MODE: Login successful"
            
            # Regular login with username and password
            logging.info(f"Logging in with username: {username}")
            
            # Navigate to TextNow login page
            self.driver.get("https://www.textnow.com/login")
            time.sleep(random.uniform(2, 4))
            
            # Wait for the login form to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//form[contains(@class, 'login-form')]"))
            )
            
            # Fill in the login form
            # Username Field
            username_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "username"))
            )
            self.type_with_random_delays(username_field, username)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Password Field
            password_field = self.driver.find_element(By.ID, "password")
            self.type_with_random_delays(password_field, password)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Submit the form
            login_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
            login_button.click()
            
            # Wait for login to complete
            try:
                # Wait for the messaging page to load
                WebDriverWait(self.driver, 30).until(
                    EC.url_contains("/messaging")
                )
                logging.info(f"Successfully logged in as {username}")
                
                # If account_id is provided, save the new cookies and tokens
                if account_id:
                    # Get cookies
                    cookies = self.driver.get_cookies()
                    
                    # Get localStorage tokens if available
                    tokens = self.driver.execute_script("""
                    return {
                        access_token: localStorage.getItem('access_token'),
                        refresh_token: localStorage.getItem('refresh_token'),
                        user_id: localStorage.getItem('user_id')
                    };
                    """)
                    
                    # Save tokens and cookies
                    self.token_manager.save_tokens(account_id, tokens, cookies)
                    logging.info(f"Updated tokens and cookies for account ID {account_id}")
                
                return True, "Login successful"
            
            except TimeoutException:
                # Check if there's an error message
                try:
                    error_message = self.driver.find_element(By.XPATH, "//div[contains(@class, 'error-message')]").text
                    logging.error(f"Login failed: {error_message}")
                    return False, f"Login failed: {error_message}"
                except NoSuchElementException:
                    # If we can't find an error message, but we also didn't get redirected, something else is wrong
                    logging.error("Login failed: Unexpected page after login submission")
                    return False, "Login failed: Unexpected page after login"
        
        except Exception as e:
            logging.error(f"Login failed: {e}")
            logging.error(traceback.format_exc())
            return False, f"Login failed: {str(e)}"
    
    def send_message(self, account_id, to_number, message_text):
        """Send a message from a TextNow account"""
        try:
            # Get account information
            account = self.fingerprint_manager.get_account(account_id)
            if not account:
                return False, "Account not found"
            
            # Make sure we're logged in
            is_logged_in = False
            
            # First try with cookies/tokens
            if self.driver and "/messaging" in self.driver.current_url:
                # Check if we're already logged in with this account
                try:
                    current_user = self.driver.execute_script("return localStorage.getItem('username');")
                    if current_user and current_user.lower() == account['username'].lower():
                        is_logged_in = True
                        logging.info(f"Already logged in as {account['username']}")
                except:
                    pass
            
            if not is_logged_in:
                # Log in with this account
                login_success, login_message = self.login(account['username'], account['password'], account_id)
                if not login_success:
                    return False, login_message
            
            # For demo/EXE mode, simulate sending a message
            if os.environ.get('MOCK_MODE', 'true').lower() == 'true':
                logging.info(f"MOCK MODE: Simulating sending message to {to_number}")
                
                # Format the phone number
                if not to_number.startswith("+1"):
                    # Add +1 for US numbers if not already present
                    if to_number.startswith("1"):
                        to_number = "+" + to_number
                    else:
                        to_number = "+1" + to_number
                
                # Clean up any other formatting in the number
                to_number = ''.join(c for c in to_number if c.isdigit() or c == '+')
                
                # Simulate delays for a more realistic flow
                logging.info(f"MOCK MODE: Starting new conversation with {to_number}")
                time.sleep(random.uniform(1, 2))
                logging.info("MOCK MODE: Typing message...")
                # Simulate typing speed - about 5 chars per second
                time.sleep(len(message_text) * 0.2)
                logging.info("MOCK MODE: Sending message...")
                time.sleep(random.uniform(0.5, 1.5))
                logging.info("MOCK MODE: Message sent successfully")
                
                # Log the message in the database
                message_data = {
                    'account_id': account_id,
                    'to_number': to_number,
                    'message': message_text,
                    'direction': 'outbound',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'sent'
                }
                
                # Save in database
                try:
                    # Here would be code to save the message to the database
                    import sqlite3
                    conn = sqlite3.connect(self.database_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                    INSERT INTO messages (account_id, contact_number, direction, content, status, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        account_id, 
                        to_number, 
                        'outbound', 
                        message_text, 
                        'sent', 
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logging.error(f"Failed to save message to database: {e}")
                
                return True, "MOCK MODE: Message sent successfully"
            
            # Format the phone number correctly
            if not to_number.startswith("+1"):
                # Add +1 for US numbers if not already present
                if to_number.startswith("1"):
                    to_number = "+" + to_number
                else:
                    to_number = "+1" + to_number
            
            # Clean up any other formatting in the number
            to_number = ''.join(c for c in to_number if c.isdigit() or c == '+')
            
            # Navigate to new conversation
            self.driver.get("https://www.textnow.com/messaging")
            time.sleep(random.uniform(2, 4))
            
            # Click on "New Conversation" button
            new_conversation_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'New') or contains(@class, 'new-conversation')]"))
            )
            new_conversation_button.click()
            time.sleep(random.uniform(1, 2))
            
            # Enter the recipient's number
            recipient_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//input[contains(@placeholder, 'Enter name or number')]"))
            )
            self.type_with_random_delays(recipient_field, to_number)
            time.sleep(random.uniform(1, 2))
            
            # Select the recipient from the dropdown (if it appears)
            try:
                recipient_option = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'recipient-option')]"))
                )
                recipient_option.click()
                time.sleep(random.uniform(1, 2))
            except TimeoutException:
                # If no dropdown appears, just press Enter
                recipient_field.send_keys(Keys.ENTER)
                time.sleep(random.uniform(1, 2))
            
            # Type the message
            message_field = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//textarea[contains(@placeholder, 'Send a message')]"))
            )
            
            # If message is multi-line, send each line with natural typing behavior
            lines = message_text.split('\n')
            for i, line in enumerate(lines):
                self.type_with_random_delays(message_field, line)
                
                if i < len(lines) - 1:  # If not the last line
                    message_field.send_keys(Keys.SHIFT + Keys.ENTER)  # Add a newline
                    time.sleep(random.uniform(0.5, 1.0))
            
            time.sleep(random.uniform(1, 2))
            
            # Send the message
            send_button = self.driver.find_element(By.XPATH, "//button[@type='submit' or contains(@class, 'send-button')]")
            send_button.click()
            
            # Wait for the message to be sent
            time.sleep(random.uniform(2, 4))
            
            # Check for any error messages
            try:
                error_message = self.driver.find_element(By.XPATH, "//div[contains(@class, 'error-message')]").text
                logging.error(f"Message sending failed: {error_message}")
                return False, f"Message sending failed: {error_message}"
            except NoSuchElementException:
                # No error message found, assume success
                logging.info(f"Message sent successfully to {to_number}")
                
                # Log the message in the database
                message_data = {
                    'account_id': account_id,
                    'to_number': to_number,
                    'message': message_text,
                    'direction': 'outbound',
                    'timestamp': datetime.now().isoformat(),
                    'status': 'sent'
                }
                
                # Save in database
                try:
                    # Here would be code to save the message to the database
                    import sqlite3
                    conn = sqlite3.connect(self.database_path)
                    cursor = conn.cursor()
                    
                    cursor.execute("""
                    INSERT INTO messages (account_id, contact_number, direction, content, status, timestamp) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        account_id, 
                        to_number, 
                        'outbound', 
                        message_text, 
                        'sent', 
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                    conn.close()
                except Exception as e:
                    logging.error(f"Failed to save message to database: {e}")
                
                return True, "Message sent successfully"
        
        except Exception as e:
            logging.error(f"Message sending failed: {e}")
            logging.error(traceback.format_exc())
            return False, f"Message sending failed: {str(e)}"
    
    def check_messages(self, account_id):
        """Check for new messages for a TextNow account"""
        try:
            # Get account information
            account = self.fingerprint_manager.get_account(account_id)
            if not account:
                return False, "Account not found", []
            
            # Make sure we're logged in
            is_logged_in = False
            
            # First try with cookies/tokens
            if self.driver and "/messaging" in self.driver.current_url:
                # Check if we're already logged in with this account
                try:
                    current_user = self.driver.execute_script("return localStorage.getItem('username');")
                    if current_user and current_user.lower() == account['username'].lower():
                        is_logged_in = True
                        logging.info(f"Already logged in as {account['username']}")
                except:
                    pass
            
            if not is_logged_in:
                # Log in with this account
                login_success, login_message = self.login(account['username'], account['password'], account_id)
                if not login_success:
                    return False, login_message, []
            
            # For demo/EXE mode, simulate checking messages
            if os.environ.get('MOCK_MODE', 'true').lower() == 'true':
                logging.info(f"MOCK MODE: Simulating checking messages for account ID {account_id}")
                time.sleep(random.uniform(1, 3))
                
                # Generate mock conversations (1-5 of them)
                conversation_count = random.randint(1, 5)
                mock_conversations = []
                
                for i in range(conversation_count):
                    # Generate a random phone number
                    mock_number = f"+1{random.randint(200, 999)}{random.randint(200, 999)}{random.randint(1000, 9999)}"
                    
                    # Random boolean for unread messages
                    has_unread = random.choice([True, False])
                    
                    # Random time for last message
                    hours_ago = random.randint(0, 72)
                    time_str = f"{hours_ago} hours ago" if hours_ago > 0 else "Just now"
                    
                    # Generate a random message preview
                    message_templates = [
                        "Hey, interested in those odds...",
                        "What's the minimum bet?",
                        "Can you tell me more about the bonus?",
                        "Is this service available in my state?",
                        "How do I claim the free bet?",
                        "Thanks for the info!"
                    ]
                    
                    mock_conversations.append({
                        'contact_name': mock_number,
                        'contact_number': mock_number,
                        'latest_message': random.choice(message_templates),
                        'timestamp': time_str,
                        'has_unread': has_unread
                    })
                
                logging.info(f"MOCK MODE: Found {len(mock_conversations)} conversations")
                return True, f"MOCK MODE: Found {len(mock_conversations)} conversations", mock_conversations
            
            # Navigate to the messages page
            self.driver.get("https://www.textnow.com/messaging")
            time.sleep(random.uniform(2, 4))
            
            # Get all conversations
            conversations = []
            try:
                # Look for conversation elements
                conversation_elements = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'conversation-item')]")
                
                for element in conversation_elements:
                    try:
                        # Extract conversation details
                        contact_element = element.find_element(By.XPATH, ".//div[contains(@class, 'contact-name')]")
                        contact_name = contact_element.text.strip()
                        
                        # Extract the number if available (might be in the data attribute)
                        contact_number = None
                        try:
                            contact_number = element.get_attribute("data-contact-number")
                        except:
                            # If we can't get it from data attribute, try to parse from the text
                            if any(c.isdigit() for c in contact_name):
                                contact_number = ''.join(c for c in contact_name if c.isdigit() or c in '+()')
                        
                        # Get latest message preview if available
                        latest_message = None
                        try:
                            message_element = element.find_element(By.XPATH, ".//div[contains(@class, 'message-preview')]")
                            latest_message = message_element.text.strip()
                        except:
                            pass
                        
                        # Get timestamp if available
                        timestamp = None
                        try:
                            time_element = element.find_element(By.XPATH, ".//div[contains(@class, 'timestamp')]")
                            timestamp = time_element.text.strip()
                        except:
                            pass
                        
                        # Check for unread indicator
                        has_unread = False
                        try:
                            unread_element = element.find_element(By.XPATH, ".//div[contains(@class, 'unread-indicator')]")
                            has_unread = unread_element is not None
                        except:
                            pass
                        
                        conversations.append({
                            'contact_name': contact_name,
                            'contact_number': contact_number,
                            'latest_message': latest_message,
                            'timestamp': timestamp,
                            'has_unread': has_unread
                        })
                    
                    except Exception as e:
                        logging.warning(f"Failed to parse conversation element: {e}")
                
                logging.info(f"Found {len(conversations)} conversations for account {account['username']}")
                return True, f"Found {len(conversations)} conversations", conversations
            
            except Exception as e:
                logging.error(f"Failed to retrieve conversations: {e}")
                return False, f"Failed to retrieve conversations: {str(e)}", []
        
        except Exception as e:
            logging.error(f"Message checking failed: {e}")
            logging.error(traceback.format_exc())
            return False, f"Message checking failed: {str(e)}", []
    
    def type_with_random_delays(self, element, text):
        """Type text into an element with random delays between keystrokes for more human-like behavior"""
        for char in text:
            element.send_keys(char)
            # Random delay between keystrokes (50-200ms)
            time.sleep(random.uniform(0.05, 0.2))
    
    def close(self):
        """Close the webdriver and clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            self.current_account = None