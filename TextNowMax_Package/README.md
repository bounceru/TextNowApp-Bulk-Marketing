# TextNow Max - Advanced Automation Platform

A robust web-based Python automation platform for TextNow messaging, leveraging advanced proxy management and dynamic interaction technologies to streamline web communication workflows.

## Overview

TextNow Max is a comprehensive automation tool for creating and managing TextNow ghost accounts. The system features a custom web interface with connection to Proxidize for IP rotation, and includes capabilities for creating and managing 10,000+ accounts with randomized attributes.

## Key Features

- **Dual-mode automation**: Uses both Android emulator (for account creation) and Proxidize (for IP rotation)
- **Mass account creation**: Generate and manage 10,000+ accounts with randomized attributes
- **IP rotation**: Integrated with Proxidize PGS for reliable IP rotation
- **Campaign management**: Distribute 100,000+ messages within 12-hour window
- **Multi-state support**: Coverage for all 50 US states and territories
- **Dashboard monitoring**: Track account status, messaging activity, and IP rotation
- **Persistent logins**: Keep accounts active to prevent phone number recycling
- **Automated responses**: Manage incoming messages with customizable rules

## Technical Architecture

- **Python-based web automation**: Core automation framework
- **Selenium/Playwright**: Browser interactions for web components
- **Proxidize PGS**: Mobile proxy integration for IP rotation
- **Flask API**: Route management and web interface
- **SQLite**: Account and proxy tracking database
- **ADB**: Android device control for mobile app interactions

## For Developers

This package contains the complete TextNow Max application with fixes for the IP rotation functionality in the Replit environment. The main components include:

- `fixed_clickable_original.py`: Main application entry point
- `api_routes.py`: API endpoints for the web interface 
- `proxidize_manager.py`: Handles interaction with Proxidize proxies
- `textnow_automation.py`: Core automation logic for TextNow
- `device_manager.py`: Manages device connections and IP rotation

See `INSTALLATION.md` for setup instructions.

## Important Note

The IP rotation functionality has been modified to handle environments where proxy connections might be blocked. The system sends real rotation commands to Proxidize but may display simulated IPs in restricted environments like Replit.

In production environments with proper proxy access, the system will automatically use and display real IPs.