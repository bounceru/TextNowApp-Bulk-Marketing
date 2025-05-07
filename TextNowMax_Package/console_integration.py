"""
Console Integration for TextNow Max

This module connects the real TextNow automation backend with the console application.
"""

import os
import sys
import logging
import time
import threading
from textnow_integration import get_integrator, console_menu

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("console_integration.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("ConsoleIntegration")

# Get the integrator instance
integrator = get_integrator()

def main():
    """Main function to run the console integration"""
    try:
        # Display banner
        print("======================================================================")
        print("                  TEXTNOW MAX CREATOR - FULL VERSION")
        print("           Ghost Account Management & Messaging")
        print("======================================================================")
        print("Initializing TextNow Max Creator...")
        print("Checking Proxidize connection...")
        
        # Verify proxy connection
        ip = integrator.get_current_ip()
        if ip:
            print(f"Proxidize connected. Current IP: {ip}")
        else:
            print("WARNING: Could not connect to Proxidize. Some features may not work correctly.")
        
        print("Checking database...")
        accounts = integrator.get_all_accounts(limit=5)
        print(f"Found {len(accounts)} existing accounts in database.")
        
        print("\nTextNow Max Creator initialized successfully!")
        print("Starting console menu...")
        time.sleep(1)
        
        # Start the console menu
        console_menu()
        
    except KeyboardInterrupt:
        print("\nExiting due to user interrupt...")
    except Exception as e:
        logger.error(f"Error in console integration: {str(e)}")
        print(f"Error: {str(e)}")
    finally:
        # Clean up resources
        print("Closing resources...")
        integrator.close()

if __name__ == "__main__":
    main()