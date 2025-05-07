"""
Message Manager for TextNow Max

This module handles the sending, receiving, and management of messages for TextNow accounts.
It provides a unified interface for messaging functionality regardless of whether we're
using the mobile app or web interface.
"""

import os
import time
import json
import random
import sqlite3
import logging
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("message_manager.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("message_manager")

class MessageManager:
    """Manages sending and receiving messages for TextNow accounts"""
    
    def __init__(self, database_path='ghost_accounts.db'):
        """
        Initialize the message manager
        
        Args:
            database_path: Path to the SQLite database
        """
        self.database_path = database_path
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables for message tracking"""
        conn = None
        try:
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Create the messages table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    recipient TEXT NOT NULL,
                    content TEXT NOT NULL,
                    media_url TEXT,
                    sent_time TEXT,
                    delivery_status TEXT DEFAULT 'pending',
                    read_status TEXT DEFAULT 'unread',
                    response_text TEXT,
                    response_time TEXT,
                    error_message TEXT,
                    FOREIGN KEY (account_id) REFERENCES accounts (id)
                )
            ''')
            
            # Create message templates table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    category TEXT,
                    variables TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logger.info("Message database tables initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
        finally:
            if conn:
                conn.close()
    
    def send_message(self, account_id: int, recipient: str, content: str, 
                    media_url: Optional[str] = None, 
                    use_mobile: bool = False,
                    device_manager=None) -> Dict[str, Any]:
        """
        Send a message from a specific account
        
        Args:
            account_id: The ID of the account sending the message
            recipient: The phone number to send the message to
            content: The text content of the message
            media_url: Optional URL to media (image, audio, etc.)
            use_mobile: Whether to use mobile app for sending
            device_manager: Optional device manager for mobile sending
            
        Returns:
            Dictionary with the result of the send operation
        """
        logger.info(f"Sending message from account {account_id} to {recipient} {'via mobile' if use_mobile else 'via web'}")
        
        try:
            # First, verify the account exists and is active
            account = self._get_account(account_id)
            if not account:
                return {
                    'success': False,
                    'message': f"Account {account_id} not found",
                    'message_id': None
                }
                
            if account['status'] != 'active':
                return {
                    'success': False, 
                    'message': f"Account {account_id} is not active (status: {account['status']})",
                    'message_id': None
                }
            
            # Log the message to the database first (will update status later)
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            current_time = datetime.datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO messages (account_id, recipient, content, media_url, sent_time, delivery_status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (account_id, recipient, content, media_url, current_time, 'pending'))
            
            message_id = cursor.lastrowid
            conn.commit()
            
            # If using mobile app and device_manager is provided, use that
            if use_mobile and device_manager:
                logger.info("Using mobile app for message sending")
                success, details = self._send_message_mobile(
                    device_manager=device_manager,
                    username=account['username'],
                    password=account['password'],
                    recipient=recipient,
                    content=content,
                    media_url=media_url
                )
            else:
                # Otherwise, use web (or simulation if no automation is available)
                logger.info("Using web interface for message sending")
                
                # In a real implementation, we would use TextNowAutomation here
                # For this version, we'll simulate with 90% success rate
                time.sleep(0.5)  # Simulate network delay
                success = random.random() < 0.9
                
                if success:
                    details = "Message sent successfully"
                else:
                    errors = [
                        "Network connection error",
                        "TextNow service temporarily unavailable",
                        "Message delivery failed - recipient not found",
                        "Account rate limit exceeded",
                        "Invalid recipient number format"
                    ]
                    details = random.choice(errors)
            
            # Update message status based on result
            if success:
                # Message sent successfully
                cursor.execute('''
                    UPDATE messages
                    SET delivery_status = ?
                    WHERE id = ?
                ''', ('delivered', message_id))
                
                logger.info(f"Message sent successfully. Message ID: {message_id}")
                
                result = {
                    'success': True,
                    'message': details,
                    'message_id': message_id,
                    'sent_time': current_time,
                    'status': 'delivered'
                }
            else:
                # Message failed
                cursor.execute('''
                    UPDATE messages
                    SET delivery_status = ?, error_message = ?
                    WHERE id = ?
                ''', ('failed', details, message_id))
                
                logger.warning(f"Message sending failed: {details}")
                
                result = {
                    'success': False,
                    'message': f"Failed to send message: {details}",
                    'message_id': message_id,
                    'sent_time': current_time,
                    'status': 'failed',
                    'error': details
                }
                
            conn.commit()
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                'success': False,
                'message': f"Error sending message: {str(e)}",
                'message_id': None
            }
    
    def get_messages(self, account_id: Optional[int] = None, 
                    recipient: Optional[str] = None,
                    status: Optional[str] = None,
                    limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages, optionally filtered by account, recipient, and status
        
        Args:
            account_id: Optional account ID to filter by
            recipient: Optional recipient number to filter by
            status: Optional delivery status to filter by
            limit: Maximum number of messages to return
            offset: Offset for pagination
            
        Returns:
            List of message dictionaries
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            query = "SELECT * FROM messages"
            params = []
            conditions = []
            
            if account_id is not None:
                conditions.append("account_id = ?")
                params.append(account_id)
                
            if recipient is not None:
                conditions.append("recipient = ?")
                params.append(recipient)
                
            if status is not None:
                conditions.append("delivery_status = ?")
                params.append(status)
                
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY sent_time DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            messages = cursor.fetchall()
            
            result = []
            for message in messages:
                result.append(dict(message))
                
            conn.close()
            return result
            
        except Exception as e:
            logger.error(f"Error getting messages: {e}")
            return []
            
    def _send_message_mobile(self, device_manager, username: str, password: str, 
                         recipient: str, content: str, media_url: Optional[str] = None,
                         max_retries: int = 3) -> Tuple[bool, str]:
        """
        Send a message using the TextNow mobile app via device_manager
        
        Args:
            device_manager: The Android device manager instance
            username: TextNow account username
            password: TextNow account password
            recipient: The phone number to send to
            content: Message content
            media_url: Optional media URL (for images, audio, etc.)
            max_retries: Maximum number of retry attempts for failed operations
            
        Returns:
            Tuple of (success, details)
        """
        logger.info(f"Sending message via mobile app to {recipient}")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    logger.info(f"Retry attempt {attempt} of {max_retries-1} for sending message to {recipient}")
                    # For retries, restart the app to ensure clean state
                    try:
                        device_manager.close_app("com.enflick.android.TextNow")
                        time.sleep(1)
                    except:
                        pass  # Ignore errors in closing
                
                # Launch TextNow app
                device_manager.launch_app("com.enflick.android.TextNow")
                time.sleep(2)
                
                # Check if we need to log in
                login_button = device_manager.find_element_by_text("Log In")
                if login_button:
                    logger.info("Not logged in - performing login first")
                    # Perform login sequence
                    device_manager.tap_element_by_text("Log In")
                    time.sleep(1)
                    
                    # Enter username
                    email_field = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/email")
                    if email_field:
                        device_manager.type_text(email_field, username)
                    else:
                        continue  # Skip to next retry
                    
                    # Enter password
                    password_field = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/password")
                    if password_field:
                        device_manager.type_text(password_field, password)
                    else:
                        continue  # Skip to next retry
                    
                    # Tap login button
                    login_button = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/login_button")
                    if login_button:
                        device_manager.tap_element(login_button)
                        time.sleep(5)  # Wait for login to complete
                    else:
                        continue  # Skip to next retry
                
                # At this point we should be logged in
                
                # Navigate to messages tab if not already there
                messages_tab = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/bottom_nav_messages")
                if messages_tab:
                    device_manager.tap_element(messages_tab)
                    time.sleep(1)
                
                # Start a new conversation
                new_convo_button = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/new_conversation_button")
                if new_convo_button:
                    device_manager.tap_element(new_convo_button)
                    time.sleep(1)
                else:
                    continue  # Skip to next retry
                
                # Enter the recipient number
                to_field = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/recipient_edit_text")
                if to_field:
                    device_manager.type_text(to_field, recipient)
                    time.sleep(0.5)
                else:
                    continue  # Skip to next retry
                
                # Tap next or confirm button
                next_button = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/menu_done")
                if next_button:
                    device_manager.tap_element(next_button)
                    time.sleep(1)
                else:
                    continue  # Skip to next retry
                
                # Now we should be in the conversation view
                # Enter message text
                message_field = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/compose_edit_text")
                if message_field:
                    device_manager.type_text(message_field, content)
                    time.sleep(0.5)
                else:
                    continue  # Skip to next retry
                
                # If we have media to attach
                if media_url:
                    # In a real implementation, we would handle media attachment here
                    # This would require downloading the media and then attaching it
                    logger.info(f"Media attachment requested: {media_url} - simulating attachment")
                    
                    # Tap attachment button
                    attach_button = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/attach_button")
                    if attach_button:
                        device_manager.tap_element(attach_button)
                        time.sleep(0.5)
                        
                        # This is a simplified version - in reality you'd need to select the right media type
                        # and navigate the file picker
                        gallery_option = device_manager.find_element_by_text("Gallery")
                        if gallery_option:
                            device_manager.tap_element_by_text("Gallery")
                            time.sleep(1)
                            # Would need to select the actual image here
                            logger.warning("Media attachment simulation stopped at gallery selection")
                            # For now, cancel and just send text
                            device_manager.press_back()
                            time.sleep(0.5)
                
                # Send the message
                send_button = device_manager.find_element_by_resource_id("com.enflick.android.TextNow:id/send_button")
                if send_button:
                    device_manager.tap_element(send_button)
                    time.sleep(1)
                    
                    # Check for sending indicators
                    # In a real implementation, we would check for message status indicators
                    # For now, we'll assume success if we don't crash
                    logger.info(f"Message sent via mobile app to {recipient}")
                    return True, "Message sent successfully via mobile app"
                else:
                    continue  # Skip to next retry
                
            except Exception as e:
                error_details = str(e)
                logger.error(f"Error sending message via mobile app (attempt {attempt+1}): {error_details}")
                if attempt == max_retries - 1:
                    # Last attempt failed
                    return False, f"Error after {max_retries} attempts: {error_details}"
                # Otherwise, continue to next retry
                time.sleep(1)  # Brief pause before retrying
                
        # If we reach here, all attempts failed
        return False, f"Failed to send message after {max_retries} attempts"
            
    def _get_account(self, account_id: int) -> Optional[Dict[str, Any]]:
        """
        Get account details from the database
        
        Args:
            account_id: The account ID to retrieve
            
        Returns:
            Account dictionary or None if not found
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM accounts WHERE id = ?
            ''', (account_id,))
            
            account = cursor.fetchone()
            conn.close()
            
            if account:
                return dict(account)
            return None
            
        except Exception as e:
            logger.error(f"Error getting account: {e}")
            return None
    
    def get_message_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get message sending statistics
        
        Args:
            days: Number of days to include in statistics
            
        Returns:
            Dictionary with message statistics
        """
        try:
            conn = sqlite3.connect(self.database_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Calculate date for filtering
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            # Get total count
            cursor.execute('''
                SELECT COUNT(*) as total_count
                FROM messages
                WHERE sent_time >= ?
            ''', (cutoff_date,))
            
            total_count = cursor.fetchone()['total_count']
            
            # Get counts by status
            cursor.execute('''
                SELECT delivery_status, COUNT(*) as count
                FROM messages
                WHERE sent_time >= ?
                GROUP BY delivery_status
            ''', (cutoff_date,))
            
            status_counts = {}
            for row in cursor.fetchall():
                status_counts[row['delivery_status']] = row['count']
                
            # Get counts by day
            cursor.execute('''
                SELECT 
                    date(sent_time) as send_date,
                    COUNT(*) as message_count,
                    SUM(CASE WHEN delivery_status = 'delivered' THEN 1 ELSE 0 END) as delivered_count
                FROM messages
                WHERE sent_time >= ?
                GROUP BY date(sent_time)
                ORDER BY send_date
            ''', (cutoff_date,))
            
            daily_stats = []
            for row in cursor.fetchall():
                daily_stats.append({
                    'date': row['send_date'],
                    'total': row['message_count'],
                    'delivered': row['delivered_count']
                })
                
            conn.close()
            
            # Calculate success rate
            delivered = status_counts.get('delivered', 0)
            success_rate = (delivered / total_count * 100) if total_count > 0 else 0
            
            return {
                'total_messages': total_count,
                'delivered_messages': delivered,
                'failed_messages': status_counts.get('failed', 0),
                'pending_messages': status_counts.get('pending', 0),
                'success_rate': round(success_rate, 2),
                'daily_stats': daily_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting message statistics: {e}")
            return {
                'total_messages': 0,
                'delivered_messages': 0,
                'failed_messages': 0,
                'pending_messages': 0,
                'success_rate': 0,
                'daily_stats': []
            }

# Singleton instance
_message_manager = None

def get_message_manager() -> MessageManager:
    """Get the singleton instance of the MessageManager"""
    global _message_manager
    
    if _message_manager is None:
        _message_manager = MessageManager()
        
    return _message_manager

if __name__ == "__main__":
    # Simple test when run directly
    manager = get_message_manager()
    
    # Send a test message
    print("Sending test message...")
    result = manager.send_message(
        account_id=1,
        recipient="(555) 123-4567",
        content="This is a test message from the message manager."
    )
    
    print(f"Send result: {result}")
    
    # Get messages
    print("\nGetting recent messages:")
    messages = manager.get_messages(limit=5)
    for msg in messages:
        print(f"Message {msg['id']}: To {msg['recipient']} - {msg['content']} ({msg['delivery_status']})")
    
    # Get statistics
    print("\nMessage statistics:")
    stats = manager.get_message_statistics()
    for key, value in stats.items():
        if key != 'daily_stats':
            print(f"{key}: {value}")
            
    print("\nDaily stats:")
    for day in stats['daily_stats']:
        print(f"{day['date']}: {day['total']} messages, {day['delivered']} delivered")