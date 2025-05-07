"""
TextNow Integration Module

This module connects the real TextNow account creation and messaging functionality
with the TextNow Max Creator user interfaces (both web and console).
"""

import os
import sys
import json
import logging
import asyncio
import threading
import time
import random
import sqlite3
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Tuple

# Import automation modules
try:
    # First try importing the Playwright version (preferred)
    from real_textnow_creator import TextNowCreator, ProxidizeManager, Database
    USING_PLAYWRIGHT = True
    print("Using Playwright for TextNow automation")
except ImportError:
    # Fall back to Selenium if Playwright isn't available
    from selenium_textnow_creator import TextNowSeleniumCreator as TextNowCreator
    from selenium_textnow_creator import ProxidizeManager, Database
    USING_PLAYWRIGHT = False
    print("Using Selenium for TextNow automation")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("textnow_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TextNowIntegration")

class TextNowIntegrator:
    """Main integrator class to connect automation with UI"""
    
    def __init__(self):
        """Initialize the integrator"""
        # Connect to database
        self.db = Database()
        
        # Initialize proxy manager
        self.proxy = ProxidizeManager()
        
        # Check proxy connection
        if not self.proxy.verify_connection():
            logger.warning("Could not connect to Proxidize. Some features may not work correctly.")
        
        # Initialize TextNow creator
        if USING_PLAYWRIGHT:
            # Playwright version requires async
            self.creator = None
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.creator_task = self.loop.create_task(self._init_playwright_creator())
            self.loop.run_until_complete(self.creator_task)
        else:
            # Selenium version is synchronous
            self.creator = TextNowCreator(headless=True, proxy_manager=self.proxy)
        
        logger.info("TextNow integrator initialized")
    
    async def _init_playwright_creator(self):
        """Initialize the Playwright-based creator"""
        self.creator = TextNowCreator(headless=True, proxy_manager=self.proxy)
        await self.creator.start_browser()
        logger.info("Playwright creator initialized")
    
    def close(self):
        """Close all resources"""
        try:
            if USING_PLAYWRIGHT:
                # Close Playwright resources
                if self.creator:
                    asyncio.run_coroutine_threadsafe(self.creator.stop_browser(), self.loop)
            else:
                # Close Selenium resources
                if self.creator:
                    self.creator.quit_driver()
            
            # Close database
            if self.db:
                self.db.close()
                
            logger.info("All resources closed")
        except Exception as e:
            logger.error(f"Error closing resources: {str(e)}")
    
    def create_account(self, name=None, email=None, password=None, area_code=None):
        """Create a TextNow account"""
        logger.info(f"Creating account with area code: {area_code}")
        
        try:
            if USING_PLAYWRIGHT:
                # Playwright requires async
                result = asyncio.run_coroutine_threadsafe(
                    self.creator.create_account(
                        name=name, 
                        email=email, 
                        password=password, 
                        area_code=area_code
                    ), 
                    self.loop
                ).result()
            else:
                # Selenium is synchronous
                result = self.creator.create_account(
                    name=name,
                    email=email,
                    password=password,
                    area_code=area_code
                )
            
            return result
        except Exception as e:
            logger.error(f"Error creating account: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_multiple_accounts(self, count, area_code=None):
        """Create multiple TextNow accounts"""
        logger.info(f"Creating {count} accounts with area code: {area_code}")
        
        results = {
            "total": count,
            "successful": 0,
            "failed": 0,
            "accounts": []
        }
        
        for i in range(count):
            logger.info(f"Creating account {i+1} of {count}")
            
            # Check if we need to rotate IP
            if i > 0 and i % 3 == 0:
                logger.info("Rotating IP...")
                self.proxy.rotate_ip()
            
            # Generate random account details
            name = self._generate_random_name()
            email = self._generate_random_email(name)
            password = self._generate_random_password()
            
            # Create the account
            result = self.create_account(
                name=name,
                email=email,
                password=password,
                area_code=area_code
            )
            
            if result["success"]:
                results["successful"] += 1
                results["accounts"].append({
                    "account_id": result["account_id"],
                    "phone_number": result["phone_number"],
                    "email": email,
                    "password": password
                })
            else:
                results["failed"] += 1
                results["accounts"].append({
                    "error": result["error"]
                })
            
            # Random delay between account creations
            delay = random.uniform(5, 15)
            logger.info(f"Waiting {delay:.2f} seconds before next account creation")
            time.sleep(delay)
        
        return results
    
    def create_accounts_background(self, count, area_code=None, callback=None):
        """Create accounts in a background thread"""
        def _background_task():
            result = self.create_multiple_accounts(count, area_code)
            if callback:
                callback(result)
        
        thread = threading.Thread(target=_background_task)
        thread.daemon = True
        thread.start()
        
        return {
            "success": True,
            "message": f"Started creating {count} accounts in background"
        }
    
    def send_message(self, account_id, recipient, message_text):
        """Send a message from a TextNow account"""
        logger.info(f"Sending message to {recipient} from account {account_id}")
        
        try:
            if USING_PLAYWRIGHT:
                # Playwright requires async
                result = asyncio.run_coroutine_threadsafe(
                    self.creator.send_message(
                        account_id=account_id,
                        recipient=recipient,
                        message_text=message_text
                    ),
                    self.loop
                ).result()
            else:
                # Selenium is synchronous
                result = self.creator.send_message(
                    account_id=account_id,
                    recipient=recipient,
                    message_text=message_text
                )
            
            return result
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def login_to_account(self, account_id=None, phone_number=None, email=None, password=None):
        """Login to a TextNow account"""
        logger.info(f"Logging in to account {account_id or phone_number or email}")
        
        try:
            if USING_PLAYWRIGHT:
                # Playwright requires async
                result = asyncio.run_coroutine_threadsafe(
                    self.creator.login_to_account(
                        account_id=account_id,
                        phone_number=phone_number,
                        email=email,
                        password=password
                    ),
                    self.loop
                ).result()
            else:
                # Selenium is synchronous
                result = self.creator.login_to_account(
                    account_id=account_id,
                    phone_number=phone_number,
                    email=email,
                    password=password
                )
            
            return result
        except Exception as e:
            logger.error(f"Error logging in: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def rotate_ip(self):
        """Rotate IP address using Proxidize"""
        logger.info("Rotating IP address")
        return self.proxy.rotate_ip()
    
    def get_current_ip(self):
        """Get current IP address"""
        return self.proxy.get_current_ip()
    
    def get_all_accounts(self, status=None, limit=100, offset=0):
        """Get all accounts from the database"""
        return self.db.get_all_accounts(status=status, limit=limit, offset=offset)
    
    def get_account(self, account_id=None, phone_number=None):
        """Get account details"""
        return self.db.get_account(account_id=account_id, phone_number=phone_number)
    
    def _generate_random_name(self):
        """Generate a random name"""
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


# Global integrator instance
_integrator = None

def get_integrator():
    """Get the global integrator instance"""
    global _integrator
    if _integrator is None:
        _integrator = TextNowIntegrator()
    return _integrator


# API functions for the web interface
def api_create_account(area_code=None):
    """API function to create a single account"""
    integrator = get_integrator()
    return integrator.create_account(area_code=area_code)

def api_create_multiple_accounts(count, area_code=None):
    """API function to create multiple accounts"""
    integrator = get_integrator()
    return integrator.create_accounts_background(count, area_code)

def api_send_message(account_id, recipient, message):
    """API function to send a message"""
    integrator = get_integrator()
    return integrator.send_message(account_id, recipient, message)

def api_rotate_ip():
    """API function to rotate IP"""
    integrator = get_integrator()
    success = integrator.rotate_ip()
    ip = integrator.get_current_ip()
    
    return {
        "success": success,
        "ip": ip
    }

def api_get_accounts(status=None, limit=100, offset=0):
    """API function to get accounts"""
    integrator = get_integrator()
    accounts = integrator.get_all_accounts(status, limit, offset)
    
    return {
        "success": True,
        "accounts": accounts,
        "count": len(accounts)
    }

def api_get_account(account_id=None, phone_number=None):
    """API function to get account details"""
    integrator = get_integrator()
    account = integrator.get_account(account_id, phone_number)
    
    if account:
        return {
            "success": True,
            "account": account
        }
    else:
        return {
            "success": False,
            "error": "Account not found"
        }


# Console interface functions
def console_create_account():
    """Console function to create a single account"""
    print("\n=== CREATE NEW TEXTNOW ACCOUNT ===")
    print("Enter area code or leave blank for random:")
    area_code = input("> ").strip() or None
    
    print("\nCreating account...")
    integrator = get_integrator()
    result = integrator.create_account(area_code=area_code)
    
    if result["success"]:
        print("\n✓ Account created successfully!")
        print(f"Phone number: {result['phone_number']}")
        print(f"Email: {result['email']}")
        print(f"Password: {result['password']}")
    else:
        print(f"\n✗ Error creating account: {result['error']}")
    
    input("\nPress Enter to continue...")

def console_create_multiple_accounts():
    """Console function to create multiple accounts"""
    print("\n=== CREATE MULTIPLE TEXTNOW ACCOUNTS ===")
    
    count = 0
    while count <= 0:
        try:
            count = int(input("How many accounts to create? > "))
            if count <= 0:
                print("Please enter a positive number.")
        except ValueError:
            print("Please enter a valid number.")
    
    print("Enter area code or leave blank for random:")
    area_code = input("> ").strip() or None
    
    print("\nCreating accounts...")
    integrator = get_integrator()
    
    # Start thread to create accounts
    def callback(result):
        print(f"\n✓ Account creation completed!")
        print(f"Successful: {result['successful']}")
        print(f"Failed: {result['failed']}")
    
    integrator.create_accounts_background(count, area_code, callback)
    print(f"Started creating {count} accounts in background.")
    print("You can continue using other functions while accounts are being created.")
    
    input("\nPress Enter to continue...")

def console_send_message():
    """Console function to send a message"""
    print("\n=== SEND TEXTNOW MESSAGE ===")
    
    # Get account to use
    account_id = None
    while not account_id:
        account_id_str = input("Enter account ID (or 'list' to see accounts): ").strip()
        
        if account_id_str.lower() == 'list':
            # Show list of accounts
            integrator = get_integrator()
            accounts = integrator.get_all_accounts(limit=10)
            
            print("\n=== AVAILABLE ACCOUNTS ===")
            for account in accounts:
                print(f"ID: {account['id']} | Phone: {account['phone_number']} | Status: {account['status']}")
            print("")
            continue
        
        try:
            account_id = int(account_id_str)
        except ValueError:
            print("Please enter a valid account ID.")
    
    # Get recipient
    recipient = None
    while not recipient:
        recipient = input("Enter recipient phone number: ").strip()
        if not recipient:
            print("Recipient number is required.")
    
    # Get message
    message = None
    while not message:
        message = input("Enter message text: ").strip()
        if not message:
            print("Message text is required.")
    
    print("\nSending message...")
    integrator = get_integrator()
    result = integrator.send_message(account_id, recipient, message)
    
    if result["success"]:
        print("\n✓ Message sent successfully!")
    else:
        print(f"\n✗ Error sending message: {result['error']}")
    
    input("\nPress Enter to continue...")

def console_view_accounts():
    """Console function to view accounts"""
    print("\n=== VIEW TEXTNOW ACCOUNTS ===")
    
    status_filter = input("Filter by status (active, inactive, blocked) or leave blank for all: ").strip() or None
    
    integrator = get_integrator()
    accounts = integrator.get_all_accounts(status=status_filter, limit=50)
    
    if not accounts:
        print("\nNo accounts found.")
    else:
        print(f"\nFound {len(accounts)} accounts:\n")
        print(f"{'ID':<5} | {'Phone Number':<15} | {'Status':<10} | {'Created':<20} | {'Last Used':<20}")
        print("-" * 80)
        
        for account in accounts:
            print(f"{account['id']:<5} | {account['phone_number']:<15} | {account['status']:<10} | " + 
                  f"{account['created_at'][:19]:<20} | {account['last_used'][:19] if account['last_used'] else 'Never':<20}")
    
    input("\nPress Enter to continue...")

def console_rotate_ip():
    """Console function to rotate IP"""
    print("\n=== ROTATE IP ADDRESS ===")
    
    integrator = get_integrator()
    old_ip = integrator.get_current_ip()
    print(f"Current IP: {old_ip}")
    
    print("Rotating IP...")
    success = integrator.rotate_ip()
    
    if success:
        new_ip = integrator.get_current_ip()
        print(f"\n✓ IP rotated successfully!")
        print(f"Old IP: {old_ip}")
        print(f"New IP: {new_ip}")
    else:
        print("\n✗ Failed to rotate IP.")
    
    input("\nPress Enter to continue...")

def console_menu():
    """Main console menu"""
    integrator = get_integrator()
    
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("======================================================================")
        print("                  TEXTNOW MAX CREATOR - FULL VERSION")
        print("           Ghost Account Management & Messaging")
        print("======================================================================")
        print(f"Proxidize Status: {'Connected' if integrator.proxy.verify_connection() else 'Not Connected'}")
        print("MAIN MENU")
        print("1. Create Single Account")
        print("2. Create Multiple Accounts")
        print("3. View Accounts")
        print("4. Send Message")
        print("5. Rotate IP")
        print("0. Exit")
        
        choice = input("Enter your choice (0-5): ").strip()
        
        if choice == '0':
            break
        elif choice == '1':
            console_create_account()
        elif choice == '2':
            console_create_multiple_accounts()
        elif choice == '3':
            console_view_accounts()
        elif choice == '4':
            console_send_message()
        elif choice == '5':
            console_rotate_ip()
        else:
            print("Invalid choice. Press Enter to continue...")
            input()
    
    print("Exiting TextNow Max Creator...")
    integrator.close()


if __name__ == "__main__":
    try:
        console_menu()
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
        if _integrator:
            _integrator.close()
    except Exception as e:
        print(f"Error: {str(e)}")
        if _integrator:
            _integrator.close()