"""
Messaging System for ProgressGhostCreator

This module handles mass messaging, conversation management, and scheduling
for the TextNow ghost accounts.
"""

import os
import re
import logging
import json
import time
import random
import sqlite3
from datetime import datetime, timedelta
import threading
import queue

class MessageTemplate:
    def __init__(self, content, variables=None):
        """Initialize a message template
        
        Args:
            content (str): The template content with variables in {{variable}} format
            variables (list): List of variable names expected in the template
        """
        self.content = content
        self.variables = variables or []
        self._extract_variables()
        
    def _extract_variables(self):
        """Extract variables from the template content"""
        # Find all {{variable}} occurrences
        matches = re.findall(r'\{\{(\w+)\}\}', self.content)
        self.variables = list(set(matches))  # Remove duplicates
    
    def render(self, variable_values):
        """Render the template with the provided variable values
        
        Args:
            variable_values (dict): Dictionary of variable name to value
            
        Returns:
            str: The rendered message
        """
        message = self.content
        
        # Replace each variable
        for var in self.variables:
            if var in variable_values:
                placeholder = f"{{{{{var}}}}}"
                message = message.replace(placeholder, str(variable_values[var]))
                
        return message
        
    @classmethod
    def from_db(cls, template_data):
        """Create a template from database data"""
        content = template_data.get('content', '')
        
        # Parse variables if they exist
        variables = []
        if 'variables' in template_data:
            try:
                if isinstance(template_data['variables'], str):
                    variables = json.loads(template_data['variables'])
                else:
                    variables = template_data['variables']
            except:
                pass
                
        return cls(content, variables)


class MessagingSystem:
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the messaging system"""
        self.database_path = database_path
        self.conn = None
        self._init_database()
        
        # Thread management
        self.running = False
        self.message_queue = queue.Queue()
        self.worker_threads = []
        self.max_workers = 5
        
        # Time windows for sending (24-hour format)
        self.active_hours = {
            'start': '08:00',
            'end': '20:00'
        }
        
        # Throttling settings
        self.throttling = {
            'max_per_account_per_day': 100,
            'max_per_account_per_hour': 15,
            'min_delay_between_msgs': 5,  # seconds
            'max_delay_between_msgs': 30,  # seconds
            'cooldown_after_batch': 300,  # seconds (5 minutes)
            'batch_size': 10  # messages before cooldown
        }
        
    def _init_database(self):
        """Initialize database connection"""
        try:
            self.conn = sqlite3.connect(self.database_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            logging.error(f"Error initializing messaging system database: {e}")
            return False
            
    def start(self):
        """Start the messaging system"""
        if self.running:
            logging.warning("Messaging system already running")
            return False
            
        self.running = True
        
        # Start the scheduler thread
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        # Start worker threads
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, args=(i,))
            worker.daemon = True
            worker.start()
            self.worker_threads.append(worker)
            
        logging.info(f"Messaging system started with {self.max_workers} workers")
        return True
        
    def stop(self):
        """Stop the messaging system"""
        if not self.running:
            return
            
        self.running = False
        
        # Clear the queue
        while not self.message_queue.empty():
            try:
                self.message_queue.get_nowait()
                self.message_queue.task_done()
            except:
                pass
                
        logging.info("Messaging system stopped")
        
    def _scheduler_loop(self):
        """Main scheduler loop that checks for campaigns to process"""
        logging.info("Messaging scheduler started")
        
        while self.running:
            try:
                # Check if we're in active hours
                if not self._is_active_time():
                    logging.info("Outside active messaging hours, sleeping...")
                    time.sleep(300)  # Check every 5 minutes during inactive hours
                    continue
                    
                # Get active campaigns
                campaigns = self._get_active_campaigns()
                
                if not campaigns:
                    logging.info("No active campaigns to process")
                    time.sleep(60)  # Check every minute for new campaigns
                    continue
                    
                for campaign in campaigns:
                    self._process_campaign(campaign)
                    
                # Sleep before checking again
                time.sleep(60)
                
            except Exception as e:
                logging.error(f"Error in messaging scheduler: {e}")
                time.sleep(60)  # Sleep for a minute on error
                
        logging.info("Messaging scheduler stopped")
                
    def _worker_loop(self, worker_id):
        """Worker thread that processes message tasks from the queue"""
        logging.info(f"Messaging worker {worker_id} started")
        
        while self.running:
            try:
                # Get a task from the queue
                task = self.message_queue.get(timeout=1)
                
                try:
                    # Process the task
                    if task['type'] == 'send_message':
                        self._send_message_task(task)
                    elif task['type'] == 'check_responses':
                        self._check_responses_task(task)
                    elif task['type'] == 'update_campaign':
                        self._update_campaign_task(task)
                    else:
                        logging.warning(f"Unknown task type: {task['type']}")
                except Exception as e:
                    logging.error(f"Error processing task: {e}")
                finally:
                    # Mark task as done
                    self.message_queue.task_done()
                    
            except queue.Empty:
                pass  # No tasks available
                
            except Exception as e:
                logging.error(f"Error in worker {worker_id}: {e}")
                time.sleep(1)
                
        logging.info(f"Messaging worker {worker_id} stopped")
        
    def _is_active_time(self):
        """Check if current time is within active messaging hours"""
        now = datetime.now().time()
        start_time = datetime.strptime(self.active_hours['start'], '%H:%M').time()
        end_time = datetime.strptime(self.active_hours['end'], '%H:%M').time()
        
        return start_time <= now <= end_time
        
    def _get_active_campaigns(self):
        """Get active campaigns that are scheduled to run now"""
        try:
            cursor = self.conn.cursor()
            
            # Get the current day of week
            day_of_week = datetime.now().strftime('%a')
            
            cursor.execute('''
            SELECT * FROM campaigns
            WHERE status = 'active'
            AND target_count > completed_count
            ORDER BY id
            ''')
            
            campaigns = []
            
            for row in cursor.fetchall():
                campaign = dict(row)
                
                # Check if campaign should run today
                schedule_days = json.loads(campaign.get('schedule_days', '["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]'))
                
                if day_of_week in schedule_days:
                    campaigns.append(campaign)
                    
            return campaigns
            
        except Exception as e:
            logging.error(f"Error getting active campaigns: {e}")
            return []
            
    def _process_campaign(self, campaign):
        """Process a campaign by scheduling messages"""
        try:
            campaign_id = campaign['id']
            
            # Check if we've reached the target count
            if campaign['completed_count'] >= campaign['target_count']:
                logging.info(f"Campaign {campaign_id} has reached its target count")
                self._update_campaign_status(campaign_id, 'completed')
                return
                
            # Get accounts assigned to this campaign that haven't hit their daily limit
            accounts = self._get_available_campaign_accounts(campaign_id)
            
            if not accounts:
                logging.info(f"No available accounts for campaign {campaign_id}")
                return
                
            # Load the message template
            template = self._get_campaign_template(campaign)
            
            if not template:
                logging.error(f"No valid template found for campaign {campaign_id}")
                return
                
            # Get contact numbers to message (targets)
            targets = self._get_campaign_targets(campaign_id, len(accounts) * 10)
            
            if not targets:
                logging.info(f"No targets available for campaign {campaign_id}")
                return
                
            logging.info(f"Processing campaign {campaign_id} with {len(accounts)} accounts and {len(targets)} targets")
            
            # Distribute targets among accounts
            account_idx = 0
            messages_scheduled = 0
            
            for target in targets:
                # Get current account
                account = accounts[account_idx]
                account_idx = (account_idx + 1) % len(accounts)
                
                # Schedule a message
                self._schedule_message(account, target, template, campaign_id)
                messages_scheduled += 1
                
                # Check if we've reached the campaign target
                remaining = campaign['target_count'] - campaign['completed_count'] - messages_scheduled
                if remaining <= 0:
                    break
                    
            logging.info(f"Scheduled {messages_scheduled} messages for campaign {campaign_id}")
            
            # Queue a task to update campaign stats later
            self.message_queue.put({
                'type': 'update_campaign',
                'campaign_id': campaign_id
            })
            
            return messages_scheduled
            
        except Exception as e:
            logging.error(f"Error processing campaign {campaign['id']}: {e}")
            return 0
            
    def _get_available_campaign_accounts(self, campaign_id):
        """Get accounts assigned to a campaign that are available to send messages"""
        try:
            cursor = self.conn.cursor()
            
            # Get the datetime 24 hours ago
            day_ago = (datetime.now() - timedelta(days=1)).isoformat()
            
            # Get accounts that:
            # 1. Are active and not flagged
            # 2. Are assigned to this campaign
            # 3. Haven't hit their daily message limit
            cursor.execute('''
            SELECT a.* FROM accounts a
            JOIN campaign_accounts ca ON a.id = ca.account_id
            WHERE ca.campaign_id = ?
            AND a.active = 1
            AND a.flagged = 0
            AND ca.status IN ('pending', 'active')
            AND (
                SELECT COUNT(*) FROM messages
                WHERE account_id = a.id
                AND sent_at > ?
            ) < ?
            ORDER BY a.id
            ''', (
                campaign_id,
                day_ago,
                self.throttling['max_per_account_per_day']
            ))
            
            return [dict(row) for row in cursor.fetchall()]
            
        except Exception as e:
            logging.error(f"Error getting available accounts for campaign {campaign_id}: {e}")
            return []
            
    def _get_campaign_template(self, campaign):
        """Get the message template for a campaign"""
        try:
            template_id = campaign.get('message_template_id')
            
            if not template_id:
                logging.error(f"Campaign {campaign['id']} has no template ID")
                return None
                
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM message_templates WHERE id = ?', (template_id,))
            
            template_data = cursor.fetchone()
            if not template_data:
                logging.error(f"Template {template_id} not found")
                return None
                
            return MessageTemplate.from_db(dict(template_data))
            
        except Exception as e:
            logging.error(f"Error getting campaign template: {e}")
            return None
            
    def _get_campaign_targets(self, campaign_id, limit=100):
        """Get phone numbers to target for this campaign
        
        This is where you would implement your targeting logic.
        For this example, we'll generate random phone numbers.
        """
        # In a real implementation, you would get actual phone numbers from a database
        # For demo purposes, we'll generate random numbers
        targets = []
        
        for _ in range(limit):
            area_code = random.randint(200, 999)
            prefix = random.randint(200, 999)
            line = random.randint(1000, 9999)
            phone = f"({area_code}) {prefix}-{line}"
            
            # Don't include opted-out numbers
            if not self._is_opted_out(phone):
                targets.append({
                    'phone_number': phone,
                    'variables': {
                        'name': random.choice(['John', 'Mary', 'Robert', 'Lisa', 'Michael', 'Sarah']),
                        'sport': random.choice(['football', 'basketball', 'baseball', 'hockey', 'soccer']),
                        'event': random.choice(['SuperBowl', 'NBA Finals', 'World Series', 'Stanley Cup', 'World Cup'])
                    }
                })
                
        return targets
        
    def _is_opted_out(self, phone_number):
        """Check if a phone number is opted out"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id FROM opt_outs WHERE phone_number = ?', (phone_number,))
            return cursor.fetchone() is not None
        except Exception as e:
            logging.error(f"Error checking opt-out status: {e}")
            return False  # Assume not opted out on error
            
    def _schedule_message(self, account, target, template, campaign_id):
        """Schedule a message to be sent"""
        try:
            # Prepare the message task
            rendered_message = template.render(target.get('variables', {}))
            
            task = {
                'type': 'send_message',
                'account_id': account['id'],
                'account_phone': account['phone_number'],
                'target_phone': target['phone_number'],
                'message': rendered_message,
                'campaign_id': campaign_id,
                'scheduled_at': datetime.now().isoformat()
            }
            
            # Add to queue
            self.message_queue.put(task)
            
            return True
            
        except Exception as e:
            logging.error(f"Error scheduling message: {e}")
            return False
            
    def _send_message_task(self, task):
        """Worker task to send a message"""
        try:
            account_id = task['account_id']
            account_phone = task['account_phone']
            target_phone = task['target_phone']
            message = task['message']
            campaign_id = task.get('campaign_id')
            
            logging.info(f"Sending message from {account_phone} to {target_phone}")
            
            # Simulate network delay
            time.sleep(random.uniform(0.5, 2.0))
            
            # In a real implementation, this would use the TextNow API or automation to send the message
            # For demo purposes, we'll simulate success
            if random.random() < 0.95:  # 95% success rate
                status = 'sent'
                
                # Record in database
                message_id = self._record_message({
                    'account_id': account_id,
                    'contact_number': target_phone,
                    'message_text': message,
                    'direction': 'outbound',
                    'status': status,
                    'campaign_id': campaign_id,
                    'metadata': {'source': 'campaign'}
                })
                
                logging.info(f"Message sent successfully: ID {message_id}")
                
                # Schedule response check in 5-15 minutes
                delay = random.randint(300, 900)
                response_check_time = datetime.now() + timedelta(seconds=delay)
                
                # Queue task to check for responses
                response_task = {
                    'type': 'check_responses',
                    'account_id': account_id,
                    'account_phone': account_phone,
                    'target_phone': target_phone,
                    'original_message_id': message_id,
                    'campaign_id': campaign_id,
                    'check_at': response_check_time.isoformat()
                }
                
                # We use a timer here to delay the task
                timer = threading.Timer(delay, lambda: self.message_queue.put(response_task))
                timer.daemon = True
                timer.start()
                
                return True
            else:
                # Message failed to send
                logging.warning(f"Failed to send message from {account_phone} to {target_phone}")
                
                self._record_message({
                    'account_id': account_id,
                    'contact_number': target_phone,
                    'message_text': message,
                    'direction': 'outbound',
                    'status': 'failed',
                    'campaign_id': campaign_id,
                    'metadata': {'source': 'campaign', 'error': 'Failed to send'}
                })
                
                return False
                
        except Exception as e:
            logging.error(f"Error sending message: {e}")
            return False
            
    def _check_responses_task(self, task):
        """Worker task to check for responses to a message"""
        try:
            account_id = task['account_id']
            account_phone = task['account_phone']
            target_phone = task['target_phone']
            campaign_id = task.get('campaign_id')
            
            logging.info(f"Checking for responses from {target_phone} to {account_phone}")
            
            # Simulate network delay
            time.sleep(random.uniform(0.3, 1.0))
            
            # In a real implementation, this would check TextNow for new messages
            # For demo purposes, we'll simulate responses with a 10% chance
            if random.random() < 0.10:  # 10% response rate
                # Generate a realistic response
                responses = [
                    "Yes, I'm interested. Tell me more.",
                    "How much does it cost?",
                    "What kind of odds do you offer?",
                    "Thanks for the info. When does the promotion end?",
                    "STOP",  # Opt-out message
                    "Not interested",
                    "Who is this?",
                    "Sure, sounds good",
                    "Can you send me the website?",
                    "How do I sign up?"
                ]
                
                response_text = random.choice(responses)
                
                # Check for opt-out message
                if response_text.upper() == "STOP" or "not interested" in response_text.lower():
                    logging.info(f"Opt-out received from {target_phone}")
                    self._handle_opt_out(target_phone, response_text, account_id, campaign_id)
                else:
                    # Record the incoming message
                    self._record_message({
                        'account_id': account_id,
                        'contact_number': target_phone,
                        'message_text': response_text,
                        'direction': 'inbound',
                        'status': 'received',
                        'campaign_id': campaign_id,
                        'metadata': {'source': 'campaign_response'}
                    })
                    
                    # Update conversation status
                    self._update_conversation(account_id, target_phone, 'active')
                    
                    # Check if we should send an auto-reply
                    self._check_auto_reply(account_id, target_phone, response_text, campaign_id)
                    
                logging.info(f"Received response from {target_phone}: {response_text}")
                return True
            else:
                # No response
                logging.info(f"No response from {target_phone}")
                return False
                
        except Exception as e:
            logging.error(f"Error checking responses: {e}")
            return False
            
    def _handle_opt_out(self, phone_number, message, account_id=None, campaign_id=None):
        """Handle an opt-out request"""
        try:
            cursor = self.conn.cursor()
            
            # Check if already opted out
            cursor.execute('SELECT id FROM opt_outs WHERE phone_number = ?', (phone_number,))
            if cursor.fetchone():
                # Already opted out
                return True
                
            # Add to opt-out list
            cursor.execute('''
            INSERT INTO opt_outs (
                phone_number, opt_out_message, opt_out_time, account_id, campaign_id, confirmed
            ) VALUES (?, ?, ?, ?, ?, 1)
            ''', (
                phone_number,
                message,
                datetime.now().isoformat(),
                account_id,
                campaign_id
            ))
            
            # Record the opt-out message
            self._record_message({
                'account_id': account_id,
                'contact_number': phone_number,
                'message_text': message,
                'direction': 'inbound',
                'status': 'received',
                'campaign_id': campaign_id,
                'metadata': {'opt_out': True}
            })
            
            # Send confirmation message
            self._record_message({
                'account_id': account_id,
                'contact_number': phone_number,
                'message_text': "You've been unsubscribed from our messages. Reply START to opt back in.",
                'direction': 'outbound',
                'status': 'sent',
                'campaign_id': campaign_id,
                'metadata': {'opt_out_confirmation': True}
            })
            
            # Update conversation status
            self._update_conversation(account_id, phone_number, 'closed')
            
            self.conn.commit()
            logging.info(f"Opted out {phone_number} from messages")
            return True
            
        except Exception as e:
            logging.error(f"Error handling opt-out: {e}")
            self.conn.rollback()
            return False
            
    def _check_auto_reply(self, account_id, phone_number, incoming_message, campaign_id=None):
        """Check if we should send an auto-reply to this message"""
        try:
            cursor = self.conn.cursor()
            
            # Get auto-reply settings for this account
            cursor.execute('''
            SELECT ar.*, t.content, t.variables 
            FROM auto_replies ar
            JOIN message_templates t ON ar.template_id = t.id
            WHERE ar.account_id = ? AND ar.enabled = 1
            ''', (account_id,))
            
            auto_reply = cursor.fetchone()
            if not auto_reply:
                return False
                
            # Check if keywords match
            keywords = json.loads(auto_reply['keywords'])
            if keywords and not any(keyword.lower() in incoming_message.lower() for keyword in keywords):
                return False
                
            # Check if within cooldown period
            cooldown_minutes = auto_reply['cooldown_minutes']
            cooldown_time = (datetime.now() - timedelta(minutes=cooldown_minutes)).isoformat()
            
            cursor.execute('''
            SELECT count(*) as recent_count FROM messages
            WHERE account_id = ? AND contact_number = ?
            AND direction = 'outbound'
            AND sent_at > ?
            ''', (account_id, phone_number, cooldown_time))
            
            recent_count = cursor.fetchone()[0]
            if recent_count > 0:
                logging.info(f"In cooldown period for {phone_number}, skipping auto-reply")
                return False
                
            # Check daily reply limit
            today = datetime.now().date().isoformat()
            cursor.execute('''
            SELECT count(*) as daily_count FROM messages
            WHERE account_id = ? AND direction = 'outbound'
            AND date(sent_at) = ? AND json_extract(metadata, '$.auto_reply') = 1
            ''', (account_id, today))
            
            daily_count = cursor.fetchone()[0]
            max_replies = auto_reply['max_replies_per_day']
            
            if daily_count >= max_replies:
                logging.info(f"Daily auto-reply limit reached for account {account_id}")
                return False
                
            # Check if within active hours
            active_hours = auto_reply['active_hours']
            if active_hours:
                now = datetime.now().time()
                try:
                    start_time, end_time = active_hours.split('-')
                    start = datetime.strptime(start_time, '%H:%M').time()
                    end = datetime.strptime(end_time, '%H:%M').time()
                    
                    if not (start <= now <= end):
                        logging.info(f"Outside active hours {active_hours} for auto-reply")
                        return False
                except:
                    pass
            
            # All checks passed, send the auto-reply
            template = MessageTemplate(auto_reply['content'])
            
            # Generate variables for the template
            variables = {
                'name': phone_number.split(' ')[0],  # Just use something as placeholder
                'account': account_id,
                'phone': phone_number
            }
            
            # Render the message
            message = template.render(variables)
            
            # Record and send the message
            self._record_message({
                'account_id': account_id,
                'contact_number': phone_number,
                'message_text': message,
                'direction': 'outbound',
                'status': 'sent',
                'campaign_id': campaign_id,
                'metadata': {'auto_reply': True, 'to_message': incoming_message}
            })
            
            logging.info(f"Sent auto-reply to {phone_number}")
            return True
            
        except Exception as e:
            logging.error(f"Error checking auto-reply: {e}")
            return False
            
    def _update_campaign_task(self, task):
        """Update campaign statistics"""
        try:
            campaign_id = task.get('campaign_id')
            if not campaign_id:
                return
                
            # Get counts from database
            cursor = self.conn.cursor()
            
            # Count all successful outbound messages for this campaign
            cursor.execute('''
            SELECT COUNT(*) as sent_count FROM messages
            WHERE campaign_id = ? AND direction = 'outbound' AND status = 'sent'
            ''', (campaign_id,))
            
            sent_count = cursor.fetchone()[0]
            
            # Update campaign completed count
            cursor.execute('''
            UPDATE campaigns SET
                completed_count = ?
            WHERE id = ?
            ''', (sent_count, campaign_id))
            
            # Check if campaign is complete
            cursor.execute('SELECT * FROM campaigns WHERE id = ?', (campaign_id,))
            campaign = cursor.fetchone()
            
            if campaign and campaign['target_count'] <= campaign['completed_count']:
                self._update_campaign_status(campaign_id, 'completed')
                logging.info(f"Campaign {campaign_id} has completed its target count")
                
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Error updating campaign: {e}")
            self.conn.rollback()
            
    def _update_campaign_status(self, campaign_id, status):
        """Update a campaign's status"""
        try:
            self.conn.execute('''
            UPDATE campaigns SET
                status = ?,
                completed_at = CASE WHEN ? = 'completed' THEN ? ELSE completed_at END
            WHERE id = ?
            ''', (
                status,
                status,
                datetime.now().isoformat() if status == 'completed' else None,
                campaign_id
            ))
            
            self.conn.commit()
            logging.info(f"Updated campaign {campaign_id} status to {status}")
            return True
            
        except Exception as e:
            logging.error(f"Error updating campaign status: {e}")
            self.conn.rollback()
            return False
            
    def _record_message(self, message_data):
        """Record a message in the database"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT INTO messages (
                account_id, contact_number, message_text, direction,
                sent_at, status, template_id, campaign_id, media_url, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_data.get('account_id'),
                message_data.get('contact_number'),
                message_data.get('message_text'),
                message_data.get('direction', 'outbound'),
                message_data.get('sent_at', datetime.now().isoformat()),
                message_data.get('status', 'sent'),
                message_data.get('template_id'),
                message_data.get('campaign_id'),
                message_data.get('media_url'),
                json.dumps(message_data.get('metadata', {}))
            ))
            
            message_id = cursor.lastrowid
            
            # Update account message count
            self.conn.execute('''
            UPDATE accounts SET 
                message_count = message_count + 1,
                last_activity_at = ?
            WHERE id = ?
            ''', (
                datetime.now().isoformat(),
                message_data.get('account_id')
            ))
            
            # Update or create conversation record
            self._update_conversation(
                message_data.get('account_id'),
                message_data.get('contact_number'),
                'active'
            )
            
            # Update campaign stats if applicable
            if message_data.get('campaign_id') and message_data.get('direction') == 'outbound':
                # Update campaign accounts
                self.conn.execute('''
                UPDATE campaign_accounts SET 
                    messages_sent = messages_sent + 1,
                    status = CASE WHEN status = 'pending' THEN 'active' ELSE status END
                WHERE campaign_id = ? AND account_id = ?
                ''', (
                    message_data.get('campaign_id'),
                    message_data.get('account_id')
                ))
                
            # For inbound messages in a campaign
            if message_data.get('campaign_id') and message_data.get('direction') == 'inbound':
                self.conn.execute('''
                UPDATE campaign_accounts SET 
                    responses_received = responses_received + 1
                WHERE campaign_id = ? AND account_id = ?
                ''', (
                    message_data.get('campaign_id'),
                    message_data.get('account_id')
                ))
            
            self.conn.commit()
            return message_id
            
        except Exception as e:
            logging.error(f"Error recording message: {e}")
            self.conn.rollback()
            return None
            
    def _update_conversation(self, account_id, contact_number, status='active'):
        """Update or create a conversation record"""
        try:
            cursor = self.conn.cursor()
            
            # Check if conversation exists
            cursor.execute('''
            SELECT id FROM conversations 
            WHERE account_id = ? AND contact_number = ?
            ''', (account_id, contact_number))
            
            result = cursor.fetchone()
            now = datetime.now().isoformat()
            
            if result:
                # Update existing conversation
                self.conn.execute('''
                UPDATE conversations SET 
                    last_message_at = ?,
                    message_count = message_count + 1,
                    status = ?
                WHERE id = ?
                ''', (now, status, result[0]))
            else:
                # Create new conversation
                self.conn.execute('''
                INSERT INTO conversations (
                    account_id, contact_number, started_at, last_message_at,
                    message_count, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    account_id,
                    contact_number,
                    now,
                    now,
                    1,
                    status
                ))
                
                # Update account conversation count
                self.conn.execute('''
                UPDATE accounts SET 
                    conversation_count = conversation_count + 1
                WHERE id = ?
                ''', (account_id,))
                
            self.conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"Error updating conversation: {e}")
            self.conn.rollback()
            return False
            
    def send_message(self, account_id, target_phone, message, campaign_id=None, media_url=None):
        """Send a single message (API for manual sending)"""
        try:
            # Get account info
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
            account = cursor.fetchone()
            
            if not account:
                logging.error(f"Account {account_id} not found")
                return False
                
            # Check if opted out
            if self._is_opted_out(target_phone):
                logging.warning(f"Cannot send to {target_phone}: opted out")
                return False
                
            # Create and queue the message task
            task = {
                'type': 'send_message',
                'account_id': account_id,
                'account_phone': account['phone_number'],
                'target_phone': target_phone,
                'message': message,
                'campaign_id': campaign_id,
                'media_url': media_url,
                'scheduled_at': datetime.now().isoformat(),
                'metadata': {'source': 'manual'}
            }
            
            # Add to queue with high priority
            self.message_queue.put(task)
            
            return True
            
        except Exception as e:
            logging.error(f"Error sending manual message: {e}")
            return False
            
    def create_template(self, name, content, variables=None, category='general'):
        """Create a message template"""
        try:
            # Extract variables if not provided
            if variables is None:
                template = MessageTemplate(content)
                variables = template.variables
                
            cursor = self.conn.cursor()
            
            cursor.execute('''
            INSERT INTO message_templates (
                name, content, variables, created_at, updated_at, category, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                content,
                json.dumps(variables),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                category,
                1
            ))
            
            template_id = cursor.lastrowid
            self.conn.commit()
            
            return template_id
            
        except Exception as e:
            logging.error(f"Error creating message template: {e}")
            self.conn.rollback()
            return None
            
    def create_campaign(self, name, template_id, target_count, description=None, schedule=None):
        """Create a messaging campaign"""
        try:
            cursor = self.conn.cursor()
            
            if not schedule:
                schedule = {
                    'start_time': '08:00',
                    'end_time': '20:00',
                    'days': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
                }
                
            cursor.execute('''
            INSERT INTO campaigns (
                name, description, status, created_at, target_count,
                message_template_id, start_time, end_time, schedule_days
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                name,
                description,
                'draft',
                datetime.now().isoformat(),
                target_count,
                template_id,
                schedule.get('start_time', '08:00'),
                schedule.get('end_time', '20:00'),
                json.dumps(schedule.get('days', ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']))
            ))
            
            campaign_id = cursor.lastrowid
            self.conn.commit()
            
            return campaign_id
            
        except Exception as e:
            logging.error(f"Error creating campaign: {e}")
            self.conn.rollback()
            return None
            
    def add_accounts_to_campaign(self, campaign_id, account_ids):
        """Add accounts to a campaign"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            for account_id in account_ids:
                # Check if already in the campaign
                cursor.execute('''
                SELECT id FROM campaign_accounts 
                WHERE campaign_id = ? AND account_id = ?
                ''', (campaign_id, account_id))
                
                if cursor.fetchone():
                    continue
                
                # Add to campaign
                cursor.execute('''
                INSERT INTO campaign_accounts (
                    campaign_id, account_id, status, assigned_at
                ) VALUES (?, ?, ?, ?)
                ''', (
                    campaign_id,
                    account_id,
                    'pending',
                    now
                ))
            
            self.conn.commit()
            return True
            
        except Exception as e:
            logging.error(f"Error adding accounts to campaign: {e}")
            self.conn.rollback()
            return False
            
    def start_campaign(self, campaign_id):
        """Start a campaign"""
        return self._update_campaign_status(campaign_id, 'active')
        
    def pause_campaign(self, campaign_id):
        """Pause a campaign"""
        return self._update_campaign_status(campaign_id, 'paused')
        
    def resume_campaign(self, campaign_id):
        """Resume a paused campaign"""
        return self._update_campaign_status(campaign_id, 'active')
        
    def cancel_campaign(self, campaign_id):
        """Cancel a campaign"""
        return self._update_campaign_status(campaign_id, 'cancelled')
        
    def close(self):
        """Close database connection and stop system"""
        self.stop()
        
        if self.conn:
            self.conn.close()
            self.conn = None


def get_messaging_system():
    """Get the messaging system singleton instance"""
    return MessagingSystem()


if __name__ == "__main__":
    # Test the messaging system
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    ms = MessagingSystem()
    
    # Create a template
    template_id = ms.create_template(
        "Test Template",
        "Hi {{name}}! Check out our promotion for {{event}}. Great odds available!"
    )
    
    print(f"Created template with ID: {template_id}")
    
    # Create a campaign
    campaign_id = ms.create_campaign(
        "Test Campaign",
        template_id,
        100,
        "Test campaign for demo"
    )
    
    print(f"Created campaign with ID: {campaign_id}")
    
    # Start the system
    ms.start()
    
    # Add all active accounts to campaign
    cursor = ms.conn.cursor()
    cursor.execute('SELECT id FROM accounts WHERE active = 1')
    account_ids = [row[0] for row in cursor.fetchall()]
    
    ms.add_accounts_to_campaign(campaign_id, account_ids)
    print(f"Added {len(account_ids)} accounts to campaign")
    
    # Start the campaign
    ms.start_campaign(campaign_id)
    print("Started campaign")
    
    # Let it run for a bit
    print("System running... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")
        
    # Clean up
    ms.close()