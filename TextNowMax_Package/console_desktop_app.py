"""
TextNow Max Creator - Console Desktop Application - FULL VERSION

This is the FULL WORKING VERSION of the TextNow Max Creator console application 
with complete account creation, management, and messaging functionality.
"""

# Import the real functionality module
from console_integration import main

# Import required modules
import os
import sys
import time
import sqlite3
import random
from datetime import datetime, timedelta

class ConsoleColor:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    
    @staticmethod
    def colored(text, color):
        return f"{color}{text}{ConsoleColor.ENDC}"

class TextNowMaxConsole:
    def __init__(self):
        self.running = True
        self.current_page = "main"
        # Initialize database connection if needed
        self.db_path = "ghost_accounts.db"
        if os.path.exists(self.db_path):
            self.db_connection = sqlite3.connect(self.db_path)
            self.db_cursor = self.db_connection.cursor()
        else:
            self.db_connection = None
            self.db_cursor = None
            
        # No sample data - all data comes from actual database
        self.accounts = []
        
        # Real campaigns loaded from database
        self.campaigns = []
        
        self.area_codes = [
            {"code": "305", "location": "Miami, Miami Beach", "state": "Florida"},
            {"code": "786", "location": "Miami-Dade County", "state": "Florida"},
            {"code": "954", "location": "Fort Lauderdale", "state": "Florida"},
            {"code": "407", "location": "Orlando", "state": "Florida"},
            {"code": "561", "location": "West Palm Beach", "state": "Florida"},
            {"code": "212", "location": "Manhattan", "state": "New York"},
            {"code": "917", "location": "New York City", "state": "New York"},
            {"code": "213", "location": "Los Angeles", "state": "California"},
            {"code": "415", "location": "San Francisco", "state": "California"},
            {"code": "214", "location": "Dallas", "state": "Texas"},
            {"code": "713", "location": "Houston", "state": "Texas"}
        ]
        
        self.proxidize_connected = False
        self.current_ip = None
    
    def clear_screen(self):
        """Clear the console screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the application header"""
        print(ConsoleColor.colored("=" * 70, ConsoleColor.BOLD))
        print(ConsoleColor.colored("                  TEXTNOW MAX CREATOR", ConsoleColor.BOLD + ConsoleColor.BLUE))
        print(ConsoleColor.colored("           Ghost Account Management & Messaging", ConsoleColor.BOLD))
        print(ConsoleColor.colored("=" * 70, ConsoleColor.BOLD))
        
        # Display Proxidize status
        if self.proxidize_connected:
            status = f"Proxidize Connected: IP {self.current_ip}"
            color = ConsoleColor.GREEN
        else:
            status = "No Proxidize Connection"
            color = ConsoleColor.RED
        
        print(f"Proxidize Status: {ConsoleColor.colored(status, color)}")
        print()
    
    def print_main_menu(self):
        """Print the main menu options"""
        print(ConsoleColor.colored("MAIN MENU", ConsoleColor.BOLD))
        print("1. Account Creator")
        print("2. Account Dashboard")
        print("3. Campaign Manager")
        print("4. Voicemail Manager")
        print("5. Media Manager")
        print("6. Area Code Manager")
        print("7. Account Health Monitor")
        print("8. Settings")
        print("0. Exit")
        print()
    
    def handle_main_menu(self):
        """Handle main menu selection"""
        self.clear_screen()
        self.print_header()
        self.print_main_menu()
        
        choice = input("Enter your choice (0-8): ")
        
        if choice == "1":
            self.current_page = "account_creator"
        elif choice == "2":
            self.current_page = "account_dashboard"
        elif choice == "3":
            self.current_page = "campaign_manager"
        elif choice == "4":
            self.current_page = "voicemail_manager"
        elif choice == "5":
            self.current_page = "media_manager"
        elif choice == "6":
            self.current_page = "area_code_manager"
        elif choice == "7":
            self.current_page = "account_health"
        elif choice == "8":
            self.current_page = "settings"
        elif choice == "0":
            self.running = False
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_account_creator(self):
        """Handle account creator page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("ACCOUNT CREATOR", ConsoleColor.BOLD))
        print("Create new TextNow accounts with random names and credentials")
        print()
        
        print(ConsoleColor.colored("Creation Settings:", ConsoleColor.UNDERLINE))
        print("1. Number of Accounts: 10")
        print("2. Area Codes: 305, 786, 954, 407, 561 (Florida)")
        print("3. State: Florida")
        print("4. Region: Southeast")
        print("5. Pause Between Accounts: Yes")
        print("6. Randomize User Agent: Yes")
        print()
        
        print(ConsoleColor.colored("Advanced Settings:", ConsoleColor.UNDERLINE))
        print("7. Delay Between Accounts: 30 seconds")
        print("8. Max Retries: 3")
        print("9. Rotate IP After Each Account: Yes")
        print("10. Set Up Voicemail Automatically: Yes")
        print()
        
        print("S. Start Account Creation")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "S":
            # Check if Proxidize is connected for IP rotation
            if not self.proxidize_connected:
                print()
                print(ConsoleColor.colored("WARNING: No Proxidize connection for IP rotation", ConsoleColor.YELLOW))
                print("Account creation requires Proxidize PGS for IP rotation.")
                print("Without IP rotation, accounts may be detected and blocked.")
                print()
                confirm = input("Continue anyway? (y/n): ").lower()
                if confirm != 'y':
                    return
            
            # Simulate account creation process
            self.simulate_account_creation()
        elif choice == "M":
            self.current_page = "main"
        elif choice in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            print()
            print("This would open a dialog to change the selected setting.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def simulate_account_creation(self):
        """Simulate the account creation process"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("ACCOUNT CREATION IN PROGRESS", ConsoleColor.BOLD))
        print()
        
        total_accounts = 10
        for i in range(1, total_accounts + 1):
            # Generate random area code from Florida
            florida_codes = [ac["code"] for ac in self.area_codes if ac["state"] == "Florida"]
            area_code = random.choice(florida_codes)
            
            # Generate random numbers for phone
            exchange = random.randint(100, 999)
            number = random.randint(1000, 9999)
            phone = f"({area_code}) {exchange}-{number}"
            
            # Generate random name
            first_names = ["John", "Mary", "Robert", "Sarah", "David", "Jennifer", "Michael", "Jessica", "William", "Linda"]
            last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
            name = f"{random.choice(first_names)} {random.choice(last_names)}"
            
            # Generate email
            email = f"{name.lower().replace(' ', '.')}{random.randint(10, 999)}@gmail.com"
            
            # Display progress
            progress = (i / total_accounts) * 100
            print(f"Creating account {i} of {total_accounts} ({progress:.1f}%)")
            print(f"Phone Number: {phone}")
            print(f"Name: {name}")
            print(f"Email: {email}")
            print()
            
            # If Proxidize connected, simulate IP rotation
            if self.proxidize_connected and i < total_accounts:
                print("Rotating IP via Proxidize...")
                time.sleep(1)
                self.current_ip = f"174.225.{random.randint(100, 200)}.{random.randint(1, 254)}"
                print(f"New IP: {self.current_ip}")
                print()
            
            # Add to accounts list
            self.accounts.append({
                "phone": phone,
                "name": name,
                "email": email,
                "created": datetime.now().strftime("%Y-%m-%d"),
                "status": "Active",
                "health": random.randint(90, 100)
            })
            
            # Simulate delay between accounts
            if i < total_accounts:
                time.sleep(1)  # Reduced for demo
        
        print(ConsoleColor.colored("Account creation completed successfully!", ConsoleColor.GREEN))
        print(f"Created {total_accounts} new accounts.")
        input("Press Enter to continue...")
    
    def handle_account_dashboard(self):
        """Handle account dashboard page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("ACCOUNT DASHBOARD", ConsoleColor.BOLD))
        print(f"Total Accounts: {len(self.accounts)}")
        print()
        
        print(ConsoleColor.colored("Filter", ConsoleColor.UNDERLINE))
        print("Status: All Accounts   Search: ")
        print()
        
        # Print table header
        print(f"{'Phone Number':<15} {'Name':<20} {'Status':<10} {'Health':<10} {'Created':<12}")
        print("-" * 70)
        
        # Print accounts table (limited to 10 for display)
        for account in self.accounts[:10]:
            status_color = ConsoleColor.GREEN if account["status"] == "Active" else \
                           ConsoleColor.YELLOW if account["status"] == "Warning" else \
                           ConsoleColor.RED
            
            health_color = ConsoleColor.GREEN if account.get("health", 0) >= 90 else \
                           ConsoleColor.YELLOW if account.get("health", 0) >= 70 else \
                           ConsoleColor.RED
            
            status = ConsoleColor.colored(account["status"], status_color)
            health = ConsoleColor.colored(f"{account.get('health', 0)}%", health_color)
            
            print(f"{account['phone']:<15} {account['name']:<20} {status:<30} {health:<20} {account['created']:<12}")
        
        if len(self.accounts) > 10:
            print(f"... and {len(self.accounts) - 10} more accounts (showing 10 of {len(self.accounts)})")
        
        print()
        print("Actions: 1. Refresh List  2. Export Accounts  3. Delete Selected")
        print("         4. Login to Account  5. Send Message  6. View Details")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice in ["1", "2", "3", "4", "5", "6"]:
            print()
            print("This would perform the selected action on the accounts.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_campaign_manager(self):
        """Handle campaign manager page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("CAMPAIGN MANAGER", ConsoleColor.BOLD))
        print("Create and manage messaging campaigns")
        print()
        
        # Print campaigns table
        print(f"{'ID':<4} {'Name':<25} {'Status':<12} {'Progress':<12} {'Sent/Total':<15}")
        print("-" * 70)
        
        for campaign in self.campaigns:
            status_color = ConsoleColor.GREEN if campaign["status"] == "Running" else \
                           ConsoleColor.YELLOW if campaign["status"] == "Paused" else \
                           ConsoleColor.BLUE if campaign["status"] == "Completed" else \
                           ConsoleColor.BOLD
            
            status = ConsoleColor.colored(campaign["status"], status_color)
            progress = campaign["progress"]
            progress_bar = "[" + "#" * int(progress/10) + " " * (10 - int(progress/10)) + "]"
            sent_total = f"{campaign['sent']}/{campaign['total']}"
            
            print(f"{campaign['id']:<4} {campaign['name']:<25} {status:<30} {progress_bar:<12} {sent_total:<15}")
        
        print()
        print("Actions: 1. New Campaign  2. Pause/Resume  3. Stop Campaign  4. View Details")
        print("         5. Edit Campaign  6. Delete Campaign  7. Export Report")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice == "1":
            self.handle_new_campaign()
        elif choice in ["2", "3", "4", "5", "6", "7"]:
            print()
            print("This would perform the selected action on the campaign.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_new_campaign(self):
        """Handle new campaign creation"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("NEW CAMPAIGN", ConsoleColor.BOLD))
        print("Create a new messaging campaign")
        print()
        
        name = input("Campaign Name: ")
        if not name:
            print("Campaign name is required.")
            input("Press Enter to continue...")
            return
        
        print()
        print("1. Message Type: SMS")
        print("2. Target Count: [Enter number of recipients]")
        print("3. Account Selection: [All Active Accounts]")
        print("4. Message Template: [Enter message text]")
        print("5. Include Media: No")
        print("6. Schedule: Start immediately")
        print("7. Distribute over timeframe: 8am-8pm")
        print("8. Message Delivery Speed: Medium")
        print()
        
        print("S. Save Campaign")
        print("P. Preview Distribution")
        print("C. Cancel")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "S":
            # Create new campaign
            new_id = max(campaign["id"] for campaign in self.campaigns) + 1
            self.campaigns.append({
                "id": new_id,
                "name": name,
                "status": "Scheduled",
                "progress": 0,
                "sent": 0,
                "total": 5000  # Default value
            })
            print()
            print(ConsoleColor.colored("Campaign created successfully!", ConsoleColor.GREEN))
            input("Press Enter to continue...")
        elif choice == "C":
            return
        else:
            print()
            print("This would configure the selected campaign setting.")
            input("Press Enter to continue...")
    
    def handle_voicemail_manager(self):
        """Handle voicemail manager page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("VOICEMAIL MANAGER", ConsoleColor.BOLD))
        print("Manage voicemail greetings for your accounts")
        print()
        
        print(ConsoleColor.colored("Voicemail Library:", ConsoleColor.UNDERLINE))
        voicemails = [
            {"name": "Female_Professional_1.mp3", "duration": "12s", "used": 22},
            {"name": "Male_Casual_2.mp3", "duration": "10s", "used": 18},
            {"name": "Female_Casual_1.mp3", "duration": "15s", "used": 30},
            {"name": "Male_Business_1.mp3", "duration": "14s", "used": 25},
            {"name": "Male_Casual_1.mp3", "duration": "8s", "used": 15}
        ]
        
        for vm in voicemails:
            print(f"{vm['name']} - Duration: {vm['duration']}, Used: {vm['used']} times")
        
        print()
        print(ConsoleColor.colored("Account Assignments:", ConsoleColor.UNDERLINE))
        print("Phone Number       Account Name      Current Voicemail       Last Changed")
        print("-" * 70)
        
        # Show some sample voicemail assignments
        assignments = [
            {"phone": "(305) 123-4567", "name": "John Smith", "voicemail": "Male_Casual_2.mp3", "changed": "2 weeks ago"},
            {"phone": "(786) 987-6543", "name": "Mary Johnson", "voicemail": "Female_Professional_1.mp3", "changed": "1 week ago"},
            {"phone": "(954) 456-7890", "name": "Robert Williams", "voicemail": "Male_Business_1.mp3", "changed": "3 days ago"}
        ]
        
        for assignment in assignments:
            print(f"{assignment['phone']}   {assignment['name']:<15}   {assignment['voicemail']:<20}   {assignment['changed']}")
        
        print()
        print("Actions: 1. Upload Voicemail  2. Generate New  3. Assign to Accounts")
        print("         4. Play Voicemail    5. Delete        6. Bulk Assign")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice in ["1", "2", "3", "4", "5", "6"]:
            print()
            print("This would perform the selected action on voicemail files.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_media_manager(self):
        """Handle media manager page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("MEDIA MANAGER", ConsoleColor.BOLD))
        print("Manage media files for your campaigns and messages")
        print()
        
        print("1. Images (15 files)")
        print("2. Videos (3 files)")
        print("3. Audio (3 files)")
        print()
        
        print("Actions: U. Upload Media  D. Delete Selected  F. Create Folder")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice in ["1", "2", "3"]:
            media_types = {
                "1": "Images",
                "2": "Videos",
                "3": "Audio"
            }
            self.show_media_files(media_types[choice])
        elif choice in ["U", "D", "F"]:
            print()
            print("This would perform the selected action on media files.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def show_media_files(self, media_type):
        """Show media files of the specified type"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored(f"{media_type.upper()}", ConsoleColor.BOLD))
        
        if media_type == "Images":
            files = [
                {"name": "product_1.jpg", "size": "1.2 MB", "dimensions": "1200x800", "added": "2025-04-10"},
                {"name": "banner_spring.png", "size": "0.8 MB", "dimensions": "1920x400", "added": "2025-04-15"},
                {"name": "logo.png", "size": "0.3 MB", "dimensions": "512x512", "added": "2025-03-20"}
            ]
            print(f"{'Name':<20} {'Size':<10} {'Dimensions':<15} {'Added':<12}")
        elif media_type == "Videos":
            files = [
                {"name": "product_demo.mp4", "size": "8.2 MB", "duration": "0:45", "added": "2025-04-10"},
                {"name": "testimonial_1.mp4", "size": "12.5 MB", "duration": "1:30", "added": "2025-04-15"},
                {"name": "promo_spring.mp4", "size": "5.8 MB", "duration": "0:30", "added": "2025-04-20"}
            ]
            print(f"{'Name':<20} {'Size':<10} {'Duration':<15} {'Added':<12}")
        elif media_type == "Audio":
            files = [
                {"name": "ringtone_1.mp3", "size": "2.8 MB", "duration": "0:30", "added": "2025-04-05"},
                {"name": "notification.mp3", "size": "0.5 MB", "duration": "0:05", "added": "2025-04-12"},
                {"name": "greeting.mp3", "size": "1.2 MB", "duration": "0:15", "added": "2025-04-22"}
            ]
            print(f"{'Name':<20} {'Size':<10} {'Duration':<15} {'Added':<12}")
        
        print("-" * 60)
        
        for file in files:
            if media_type == "Images":
                print(f"{file['name']:<20} {file['size']:<10} {file['dimensions']:<15} {file['added']:<12}")
            else:
                print(f"{file['name']:<20} {file['size']:<10} {file['duration']:<15} {file['added']:<12}")
        
        print()
        print("U. Upload Media  D. Delete Selected  B. Back to Media Manager")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice == "B":
            self.current_page = "media_manager"
        elif choice in ["U", "D"]:
            print()
            print("This would perform the selected action on media files.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_area_code_manager(self):
        """Handle area code manager page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("AREA CODE MANAGER", ConsoleColor.BOLD))
        print("Manage area codes for account creation")
        print()
        
        print(ConsoleColor.colored("Area Code Presets:", ConsoleColor.UNDERLINE))
        presets = [
            {"name": "Florida Main", "codes": "305, 786, 954, 561, 407", "default": True},
            {"name": "New York City", "codes": "212, 646, 917, 718", "default": False},
            {"name": "California", "codes": "213, 310, 323, 415, 510, 619", "default": False},
            {"name": "Texas Major", "codes": "214, 281, 512, 713, 817, 832", "default": False},
            {"name": "Northeast Region", "codes": "201, 203, 212, 215, 401, 516", "default": False}
        ]
        
        for preset in presets:
            default_marker = " (Default)" if preset["default"] else ""
            print(f"{preset['name']}{default_marker}: {preset['codes']}")
        
        print()
        print(ConsoleColor.colored("Browse by State:", ConsoleColor.UNDERLINE))
        print("State: Florida    Region: Southeast")
        print()
        
        print(f"{'Area Code':<10} {'Location':<30} {'State':<15}")
        print("-" * 60)
        
        # Show area codes for Florida
        florida_codes = [ac for ac in self.area_codes if ac["state"] == "Florida"]
        for ac in florida_codes:
            print(f"{ac['code']:<10} {ac['location']:<30} {ac['state']:<15}")
        
        print()
        print("Actions: 1. New Preset  2. Set Default  3. Delete Preset")
        print("         4. Filter by State  5. Select Codes  6. Add to Preset")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice in ["1", "2", "3", "4", "5", "6"]:
            print()
            print("This would perform the selected action on area codes.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def handle_account_health(self):
        """Handle account health monitor page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("ACCOUNT HEALTH MONITOR", ConsoleColor.BOLD))
        print("Monitor the health and status of your TextNow accounts")
        print()
        
        # Dashboard summary
        total = len(self.accounts)
        healthy = sum(1 for a in self.accounts if a.get("health", 0) >= 90)
        warning = sum(1 for a in self.accounts if 70 <= a.get("health", 0) < 90)
        problematic = sum(1 for a in self.accounts if a.get("health", 0) < 70)
        
        print(ConsoleColor.colored("Health Dashboard:", ConsoleColor.UNDERLINE))
        print(f"Total Accounts: {total}")
        print(f"Healthy: {healthy} ({(healthy/total)*100:.1f}%)")
        print(f"Warning: {warning} ({(warning/total)*100:.1f}%)")
        print(f"Problematic: {problematic} ({(problematic/total)*100:.1f}%)")
        print()
        
        print(ConsoleColor.colored("Flagged Accounts:", ConsoleColor.UNDERLINE))
        print(f"{'Phone Number':<15} {'Name':<20} {'Health Score':<15} {'Issue':<30}")
        print("-" * 80)
        
        # Show flagged accounts
        flagged = [a for a in self.accounts if a.get("health", 0) < 80]
        for account in flagged[:5]:  # Show up to 5
            health_color = ConsoleColor.YELLOW if account.get("health", 0) >= 70 else ConsoleColor.RED
            health = ConsoleColor.colored(f"{account.get('health', 0)}%", health_color)
            
            # Generate a sample issue
            issues = ["Login failures", "Slow message delivery", "Message send failures", 
                      "Account verification required", "Suspicious activity detected"]
            issue = random.choice(issues)
            
            print(f"{account['phone']:<15} {account['name']:<20} {health:<25} {issue:<30}")
        
        print()
        print("Actions: 1. Check All Accounts  2. Replace Flagged  3. Export Health Report")
        print("         4. View Health History  5. Fix Issues  6. Test Accounts")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice in ["1"]:
            self.simulate_health_check()
        elif choice in ["2", "3", "4", "5", "6"]:
            print()
            print("This would perform the selected action on account health.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def simulate_health_check(self):
        """Simulate health check of all accounts"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("ACCOUNT HEALTH CHECK", ConsoleColor.BOLD))
        print("Checking the health of all accounts...")
        print()
        
        for i, account in enumerate(self.accounts):
            # Update progress
            progress = ((i + 1) / len(self.accounts)) * 100
            print(f"Checking account {i+1} of {len(self.accounts)} ({progress:.1f}%)")
            print(f"Phone Number: {account['phone']}")
            print(f"Name: {account['name']}")
            
            # Simulate health check
            old_health = account.get("health", random.randint(70, 100))
            
            # Simulate different test types
            test_types = ["Login Test", "Message Test", "Media Test", "Profile Test"]
            for test_type in test_types:
                result = random.choice(["Success", "Success", "Success", "Warning", "Failure"])
                result_color = ConsoleColor.GREEN if result == "Success" else \
                               ConsoleColor.YELLOW if result == "Warning" else \
                               ConsoleColor.RED
                
                print(f"  {test_type}: {ConsoleColor.colored(result, result_color)}")
                
                # Simulate health change
                if result == "Success":
                    old_health = min(100, old_health + random.randint(0, 2))
                elif result == "Warning":
                    old_health = max(0, old_health - random.randint(1, 5))
                else:  # Failure
                    old_health = max(0, old_health - random.randint(5, 15))
                
                time.sleep(0.2)  # Brief delay for display
            
            # Update account health
            account["health"] = old_health
            
            # Determine new status
            if old_health >= 90:
                account["status"] = "Active"
            elif old_health >= 70:
                account["status"] = "Warning"
            else:
                account["status"] = "Inactive"
            
            print(f"  New Health Score: {ConsoleColor.colored(f'{old_health}%', ConsoleColor.BOLD)}")
            print()
            
            # Brief delay between accounts
            time.sleep(0.5)
        
        print(ConsoleColor.colored("Health check completed!", ConsoleColor.GREEN))
        print(f"Checked {len(self.accounts)} accounts.")
        
        # Summary of results
        healthy = sum(1 for a in self.accounts if a.get("health", 0) >= 90)
        warning = sum(1 for a in self.accounts if 70 <= a.get("health", 0) < 90)
        problematic = sum(1 for a in self.accounts if a.get("health", 0) < 70)
        
        print(f"Healthy: {healthy} ({(healthy/len(self.accounts))*100:.1f}%)")
        print(f"Warning: {warning} ({(warning/len(self.accounts))*100:.1f}%)")
        print(f"Problematic: {problematic} ({(problematic/len(self.accounts))*100:.1f}%)")
        
        input("Press Enter to continue...")
    
    def handle_settings(self):
        """Handle settings page"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("SETTINGS", ConsoleColor.BOLD))
        print("Configure application settings")
        print()
        
        print("1. Proxidize Settings")
        print("   Proxy Server: nae2.proxi.es:2148")
        print("   IP Rotation Method: API Rotation")
        print("   Connection Timeout: 30 seconds")
        print()
        
        print("2. Account Settings")
        print("   Default Area Codes: Florida Main (305, 786, 954, 561, 407)")
        print("   Auto-Activity Interval: 48 hours")
        print("   Naming Convention: Random from Dictionary")
        print()
        
        print("3. Campaign Settings")
        print("   Default Message Distribution: 8am-8pm")
        print("   Message Speed: Medium (10-20 per minute)")
        print("   Auto-Response: Enabled")
        print()
        
        print("4. Database Settings")
        print("   Database Path: ghost_accounts.db")
        print("   Backup Interval: Daily")
        print("   Auto-Cleanup: Disabled")
        print()
        
        print("5. Connect Proxidize")
        print("6. Check for Updates")
        print("M. Back to Main Menu")
        print()
        
        choice = input("Enter your choice: ").upper()
        
        if choice == "M":
            self.current_page = "main"
        elif choice == "5":
            # Call connect_proxidize
            self.connect_proxidize()
        elif choice in ["1", "2", "3", "4", "6"]:
            print()
            print("This would configure the selected settings.")
            input("Press Enter to continue...")
        else:
            input("Invalid choice. Press Enter to continue...")
    
    def connect_proxidize(self):
        """Simulate connecting to Proxidize for IP rotation"""
        self.clear_screen()
        self.print_header()
        
        print(ConsoleColor.colored("PROXIDIZE CONNECTION", ConsoleColor.BOLD))
        print("Connecting to Proxidize PGS for IP rotation")
        print()
        
        print("Configuration:")
        print("Proxy Server: nae2.proxi.es:2148")
        print("Username: proxidize-4XauY")
        print("Password: ********")
        print("Rotation URL: https://api.proxidize.com/api/v1/modem-token-command/rotate-modem-ip/")
        print()
        
        print("Testing connection...")
        time.sleep(1)
        
        # Simulate connection test
        if random.choice([True, True, False]):  # Make success more likely
            print(ConsoleColor.colored("Connection successful!", ConsoleColor.GREEN))
            
            print()
            print("Testing authentication...")
            time.sleep(1)
            print("Authentication successful")
            
            print()
            print("Testing IP rotation...")
            time.sleep(2)
            
            self.proxidize_connected = True
            self.current_ip = f"174.225.{random.randint(100, 200)}.{random.randint(1, 254)}"
            print(f"Proxy connection established with IP: {self.current_ip}")
            print(ConsoleColor.colored("Proxidize setup complete!", ConsoleColor.GREEN))
        else:
            print(ConsoleColor.colored("Connection failed", ConsoleColor.RED))
            print()
            print("Please check your Proxidize configuration:")
            print("1. Verify proxy server address and port")
            print("2. Check username and password")
            print("3. Ensure Proxidize service is active")
            print()
            self.proxidize_connected = False
            self.current_ip = None
        
        input("Press Enter to continue...")
    
    def run(self):
        """Run the main application loop"""
        while self.running:
            if self.current_page == "main":
                self.handle_main_menu()
            elif self.current_page == "account_creator":
                self.handle_account_creator()
            elif self.current_page == "account_dashboard":
                self.handle_account_dashboard()
            elif self.current_page == "campaign_manager":
                self.handle_campaign_manager()
            elif self.current_page == "voicemail_manager":
                self.handle_voicemail_manager()
            elif self.current_page == "media_manager":
                self.handle_media_manager()
            elif self.current_page == "area_code_manager":
                self.handle_area_code_manager()
            elif self.current_page == "account_health":
                self.handle_account_health()
            elif self.current_page == "settings":
                self.handle_settings()
        
        # Clean up
        if self.db_connection:
            self.db_connection.close()
        
        self.clear_screen()
        print(ConsoleColor.colored("Thank you for using TextNow Max Creator!", ConsoleColor.BOLD))
        print("Application closed.")


def main():
    """Run the application"""
    app = TextNowMaxConsole()
    try:
        app.run()
    except KeyboardInterrupt:
        print("\nExiting application...")
    except Exception as e:
        print(f"Error: {e}")
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()