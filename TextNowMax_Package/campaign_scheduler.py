"""
Campaign Scheduler for TextNow Max

This module handles the intelligent scheduling and distribution of mass messages
over specified time periods, supporting natural distribution patterns.
"""

import random
import math
import time
import json
import sqlite3
import datetime
from collections import defaultdict

class CampaignScheduler:
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the campaign scheduler"""
        self.database_path = database_path
        self._init_database()
        
    def _init_database(self):
        """Initialize the database tables for campaign scheduling"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create campaigns table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS campaign_schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            campaign_id INTEGER,
            total_messages INTEGER NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            start_date TEXT NOT NULL,
            message_pattern TEXT NOT NULL,
            status TEXT DEFAULT 'draft',
            current_progress INTEGER DEFAULT 0,
            area_codes TEXT,
            account_selection TEXT,
            max_per_account INTEGER DEFAULT 250,
            delivery_priority TEXT DEFAULT 'balanced',
            template_variation TEXT DEFAULT 'balanced',
            image_variation TEXT DEFAULT 'random',
            response_handling TEXT DEFAULT 'auto',
            advanced_options TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create schedule distribution table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_distributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER,
            hour INTEGER,
            minute INTEGER,
            message_count INTEGER,
            executed_count INTEGER DEFAULT 0,
            FOREIGN KEY (schedule_id) REFERENCES campaign_schedules(id)
        )
        ''')
        
        # Create schedule logs
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedule_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_id INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            details TEXT,
            FOREIGN KEY (schedule_id) REFERENCES campaign_schedules(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_schedule(self, name, total_messages, start_time, end_time, start_date, message_pattern='bell',
                        campaign_id=None, area_codes=None, account_selection='optimized',
                        max_per_account=250, delivery_priority='balanced', template_variation='balanced',
                        image_variation='random', response_handling='auto', advanced_options=None):
        """
        Create a new campaign schedule
        
        Args:
            name: Name of the schedule
            total_messages: Total number of messages to send
            start_time: Start time in format 'HH:MM' (24-hour)
            end_time: End time in format 'HH:MM' (24-hour)
            start_date: Start date in format 'YYYY-MM-DD'
            message_pattern: Distribution pattern ('bell', 'even', 'morning', 'afternoon', 'custom')
            campaign_id: Associated campaign ID (optional)
            area_codes: Target area codes as a list or comma-separated string
            account_selection: Method of selecting accounts
            max_per_account: Maximum messages per account
            delivery_priority: Delivery speed priority
            template_variation: Message template variation method
            image_variation: Image variation method
            response_handling: Response handling method
            advanced_options: JSON string or dict of advanced options
        
        Returns:
            ID of the created schedule
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Convert area codes to string if it's a list
        if isinstance(area_codes, list):
            area_codes = ','.join(area_codes)
            
        # Convert advanced options to JSON if it's a dict
        if isinstance(advanced_options, dict):
            advanced_options = json.dumps(advanced_options)
        
        cursor.execute(
            '''
            INSERT INTO campaign_schedules (
                name, campaign_id, total_messages, start_time, end_time, start_date,
                message_pattern, area_codes, account_selection, max_per_account,
                delivery_priority, template_variation, image_variation, response_handling,
                advanced_options
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                name, campaign_id, total_messages, start_time, end_time, start_date,
                message_pattern, area_codes, account_selection, max_per_account,
                delivery_priority, template_variation, image_variation, response_handling,
                advanced_options
            )
        )
        
        schedule_id = cursor.lastrowid
        
        # Generate distribution
        self._generate_distribution(cursor, schedule_id, total_messages, start_time, end_time, message_pattern)
        
        # Log creation
        cursor.execute(
            "INSERT INTO schedule_logs (schedule_id, action, details) VALUES (?, ?, ?)",
            (schedule_id, 'created', f'Created schedule with {total_messages} messages from {start_time} to {end_time}')
        )
        
        conn.commit()
        conn.close()
        
        return schedule_id
    
    def _generate_distribution(self, cursor, schedule_id, total_messages, start_time, end_time, pattern):
        """Generate hourly distribution based on pattern"""
        # Parse start and end times
        start_hour, start_minute = map(int, start_time.split(':'))
        end_hour, end_minute = map(int, end_time.split(':'))
        
        # Calculate total minutes in the time window
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute
        total_minutes = end_minutes - start_minutes
        
        # Generate distribution based on pattern
        if pattern == 'even':
            # Even distribution
            messages_per_minute = total_messages / total_minutes
            distribution = {minute: messages_per_minute for minute in range(start_minutes, end_minutes)}
        
        elif pattern == 'bell':
            # Bell curve distribution
            midpoint = start_minutes + (total_minutes / 2)
            std_dev = total_minutes / 6  # This gives a bell curve that fits well within the time window
            
            # Generate probability for each minute
            total_prob = 0
            minute_probs = {}
            
            for minute in range(start_minutes, end_minutes):
                # Bell curve formula
                prob = math.exp(-0.5 * ((minute - midpoint) / std_dev) ** 2)
                minute_probs[minute] = prob
                total_prob += prob
            
            # Normalize and scale to total messages
            distribution = {minute: (prob / total_prob) * total_messages for minute, prob in minute_probs.items()}
        
        elif pattern == 'morning':
            # Front-loaded distribution (more in the morning)
            midpoint = start_minutes + (total_minutes / 3)  # Peak at 1/3 of the time window
            std_dev = total_minutes / 4
            
            total_prob = 0
            minute_probs = {}
            
            for minute in range(start_minutes, end_minutes):
                # Modified bell curve with earlier peak
                prob = math.exp(-0.5 * ((minute - midpoint) / std_dev) ** 2)
                minute_probs[minute] = prob
                total_prob += prob
            
            distribution = {minute: (prob / total_prob) * total_messages for minute, prob in minute_probs.items()}
        
        elif pattern == 'afternoon':
            # Back-loaded distribution (more in the afternoon)
            midpoint = start_minutes + (2 * total_minutes / 3)  # Peak at 2/3 of the time window
            std_dev = total_minutes / 4
            
            total_prob = 0
            minute_probs = {}
            
            for minute in range(start_minutes, end_minutes):
                # Modified bell curve with later peak
                prob = math.exp(-0.5 * ((minute - midpoint) / std_dev) ** 2)
                minute_probs[minute] = prob
                total_prob += prob
            
            distribution = {minute: (prob / total_prob) * total_messages for minute, prob in minute_probs.items()}
        
        else:
            # Default to even distribution
            messages_per_minute = total_messages / total_minutes
            distribution = {minute: messages_per_minute for minute in range(start_minutes, end_minutes)}
        
        # Aggregate by hour and minute
        hourly_distribution = defaultdict(lambda: defaultdict(float))
        
        for minute, message_count in distribution.items():
            hour = minute // 60
            min_within_hour = minute % 60
            hourly_distribution[hour][min_within_hour] += message_count
        
        # Insert into database
        for hour, minutes in hourly_distribution.items():
            for minute, count in minutes.items():
                if count > 0:  # Skip minutes with 0 messages
                    cursor.execute(
                        "INSERT INTO schedule_distributions (schedule_id, hour, minute, message_count) VALUES (?, ?, ?, ?)",
                        (schedule_id, hour, minute, round(count))
                    )
    
    def get_schedule(self, schedule_id):
        """Get details of a specific schedule"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM campaign_schedules WHERE id=?", (schedule_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        schedule = dict(zip(columns, result))
        
        # Get distribution
        cursor.execute(
            "SELECT hour, minute, message_count, executed_count FROM schedule_distributions WHERE schedule_id=? ORDER BY hour, minute",
            (schedule_id,)
        )
        distribution_results = cursor.fetchall()
        
        distribution = []
        for hour, minute, message_count, executed_count in distribution_results:
            distribution.append({
                'hour': hour,
                'minute': minute,
                'message_count': message_count,
                'executed_count': executed_count
            })
        
        schedule['distribution'] = distribution
        
        # Get logs
        cursor.execute(
            "SELECT timestamp, action, details FROM schedule_logs WHERE schedule_id=? ORDER BY timestamp DESC",
            (schedule_id,)
        )
        logs_results = cursor.fetchall()
        
        logs = []
        for timestamp, action, details in logs_results:
            logs.append({
                'timestamp': timestamp,
                'action': action,
                'details': details
            })
        
        schedule['logs'] = logs
        
        conn.close()
        return schedule
    
    def get_all_schedules(self, status=None):
        """Get all schedules, optionally filtered by status"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        query = "SELECT * FROM campaign_schedules"
        params = []
        
        if status:
            query += " WHERE status=?"
            params.append(status)
        
        query += " ORDER BY created_at DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        columns = [description[0] for description in cursor.description]
        schedules = []
        
        for result in results:
            schedule = dict(zip(columns, result))
            
            # Get progress info
            cursor.execute(
                "SELECT SUM(message_count) as total, SUM(executed_count) as executed FROM schedule_distributions WHERE schedule_id=?",
                (schedule['id'],)
            )
            progress_result = cursor.fetchone()
            
            if progress_result:
                total, executed = progress_result
                schedule['progress_percentage'] = round((executed or 0) / (total or 1) * 100, 1)
            else:
                schedule['progress_percentage'] = 0
            
            schedules.append(schedule)
        
        conn.close()
        return schedules
    
    def update_schedule_status(self, schedule_id, status):
        """Update the status of a schedule"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE campaign_schedules SET status=? WHERE id=?", (status, schedule_id))
        
        # Log status change
        cursor.execute(
            "INSERT INTO schedule_logs (schedule_id, action, details) VALUES (?, ?, ?)",
            (schedule_id, 'status_change', f'Status changed to: {status}')
        )
        
        conn.commit()
        conn.close()
    
    def delete_schedule(self, schedule_id):
        """Delete a schedule and its related data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Delete related data first
        cursor.execute("DELETE FROM schedule_distributions WHERE schedule_id=?", (schedule_id,))
        cursor.execute("DELETE FROM schedule_logs WHERE schedule_id=?", (schedule_id,))
        
        # Delete the schedule
        cursor.execute("DELETE FROM campaign_schedules WHERE id=?", (schedule_id,))
        
        conn.commit()
        conn.close()
    
    def clone_schedule(self, schedule_id, new_name=None):
        """Clone a schedule with a new name"""
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return None
        
        if not new_name:
            new_name = f"{schedule['name']} (Copy)"
        
        # Create a new schedule with the same parameters
        new_id = self.create_schedule(
            name=new_name,
            total_messages=schedule['total_messages'],
            start_time=schedule['start_time'],
            end_time=schedule['end_time'],
            start_date=schedule['start_date'],
            message_pattern=schedule['message_pattern'],
            campaign_id=schedule['campaign_id'],
            area_codes=schedule['area_codes'],
            account_selection=schedule['account_selection'],
            max_per_account=schedule['max_per_account'],
            delivery_priority=schedule['delivery_priority'],
            template_variation=schedule['template_variation'],
            image_variation=schedule['image_variation'],
            response_handling=schedule['response_handling'],
            advanced_options=schedule['advanced_options']
        )
        
        return new_id
    
    def get_today_distribution(self, schedule_id, as_hourly=True):
        """
        Get distribution for today, either by hour or by minute
        
        Returns format:
        {
            'hour1': count1,
            'hour2': count2,
            ...
        }
        
        or 
        
        {
            'hour1': {
                'min1': count1,
                'min2': count2,
                ...
            },
            ...
        }
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT hour, minute, message_count FROM schedule_distributions WHERE schedule_id=? ORDER BY hour, minute",
            (schedule_id,)
        )
        results = cursor.fetchall()
        
        conn.close()
        
        if as_hourly:
            # Aggregate by hour
            hourly = defaultdict(int)
            for hour, _, count in results:
                hourly[hour] += count
            return dict(hourly)
        else:
            # Keep minute-level detail
            detailed = defaultdict(dict)
            for hour, minute, count in results:
                detailed[hour][minute] = count
            return dict(detailed)
    
    def get_distribution_for_visualization(self, schedule_id):
        """Get distribution data formatted for UI visualization"""
        hourly_totals = self.get_today_distribution(schedule_id, as_hourly=True)
        
        # Get the schedule details to know start and end times
        schedule = self.get_schedule(schedule_id)
        
        if not schedule:
            return []
        
        # Parse start and end hours
        start_hour = int(schedule['start_time'].split(':')[0])
        end_hour = int(schedule['end_time'].split(':')[0])
        
        # Create visualization data
        visualization = []
        
        for hour in range(start_hour, end_hour + 1):
            count = hourly_totals.get(hour, 0)
            
            # Format hour for display
            if hour < 12:
                display_hour = f"{hour}am"
            elif hour == 12:
                display_hour = "12pm"
            else:
                display_hour = f"{hour-12}pm"
            
            visualization.append({
                'hour': hour,
                'display_hour': display_hour,
                'count': count,
                'is_current': hour == datetime.datetime.now().hour
            })
        
        return visualization
    
    def record_message_sent(self, schedule_id, hour, minute=None):
        """Record that a message was sent at the specified time"""
        if minute is None:
            minute = datetime.datetime.now().minute
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Find the closest distribution entry
        cursor.execute(
            "SELECT id, executed_count FROM schedule_distributions WHERE schedule_id=? AND hour=? ORDER BY ABS(minute - ?) LIMIT 1",
            (schedule_id, hour, minute)
        )
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return False
        
        distribution_id, executed_count = result
        
        # Update executed count
        cursor.execute(
            "UPDATE schedule_distributions SET executed_count=? WHERE id=?",
            (executed_count + 1, distribution_id)
        )
        
        # Update overall progress on the schedule
        cursor.execute(
            "UPDATE campaign_schedules SET current_progress = current_progress + 1 WHERE id=?",
            (schedule_id,)
        )
        
        conn.commit()
        conn.close()
        return True
    
    def get_active_schedules(self):
        """Get schedules that are currently active"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        now = datetime.datetime.now()
        today = now.strftime('%Y-%m-%d')
        current_time = now.strftime('%H:%M')
        
        cursor.execute(
            """
            SELECT id, name, total_messages, start_time, end_time, current_progress 
            FROM campaign_schedules 
            WHERE status='active' AND start_date <= ? AND start_time <= ? AND end_time >= ?
            """,
            (today, current_time, current_time)
        )
        
        results = cursor.fetchall()
        
        active_schedules = []
        for id, name, total, start, end, progress in results:
            active_schedules.append({
                'id': id,
                'name': name,
                'total_messages': total,
                'start_time': start,
                'end_time': end,
                'current_progress': progress
            })
        
        conn.close()
        return active_schedules
    
    def calculate_distribution(self, total_messages, start_hour, end_hour, pattern='bell'):
        """
        Calculate message distribution (simulation only, doesn't save to DB)
        
        Returns:
        {
            'hourly': {hour: count, ...},
            'visualization': [{hour, display_hour, count, percentage}, ...],
            'stats': {peak_hour, peak_count, avg_per_hour}
        }
        """
        # Handle 24-hour time format
        hours_range = end_hour - start_hour
        if hours_range <= 0:
            hours_range = (24 + end_hour) - start_hour
        
        hourly = {}
        
        if pattern == 'bell':
            # Bell curve distribution
            midpoint = start_hour + (hours_range / 2)
            std_dev = hours_range / 4
            
            # Generate probability for each hour
            total_prob = 0
            hour_probs = {}
            
            for h in range(hours_range):
                hour = (start_hour + h) % 24
                # Bell curve formula
                x = hour if hour >= start_hour else hour + 24  # Adjust for wraparound
                prob = math.exp(-0.5 * ((x - midpoint) / std_dev) ** 2)
                hour_probs[hour] = prob
                total_prob += prob
            
            # Normalize and scale to total messages
            for hour, prob in hour_probs.items():
                hourly[hour] = round((prob / total_prob) * total_messages)
        
        elif pattern == 'morning':
            # More messages in the morning
            midpoint = start_hour + (hours_range / 3)
            std_dev = hours_range / 3
            
            total_prob = 0
            hour_probs = {}
            
            for h in range(hours_range):
                hour = (start_hour + h) % 24
                x = hour if hour >= start_hour else hour + 24
                prob = math.exp(-0.5 * ((x - midpoint) / std_dev) ** 2)
                hour_probs[hour] = prob
                total_prob += prob
            
            for hour, prob in hour_probs.items():
                hourly[hour] = round((prob / total_prob) * total_messages)
        
        elif pattern == 'afternoon':
            # More messages in the afternoon
            midpoint = start_hour + (2 * hours_range / 3)
            std_dev = hours_range / 3
            
            total_prob = 0
            hour_probs = {}
            
            for h in range(hours_range):
                hour = (start_hour + h) % 24
                x = hour if hour >= start_hour else hour + 24
                prob = math.exp(-0.5 * ((x - midpoint) / std_dev) ** 2)
                hour_probs[hour] = prob
                total_prob += prob
            
            for hour, prob in hour_probs.items():
                hourly[hour] = round((prob / total_prob) * total_messages)
        
        else:  # 'even'
            # Even distribution
            per_hour = total_messages / hours_range
            for h in range(hours_range):
                hour = (start_hour + h) % 24
                hourly[hour] = round(per_hour)
        
        # Make sure total is correct (rounding might change it slightly)
        total = sum(hourly.values())
        if total != total_messages:
            # Add or subtract the difference from the peak hour
            peak_hour = max(hourly, key=hourly.get)
            hourly[peak_hour] += (total_messages - total)
        
        # Create visualization data
        visualization = []
        for h in range(hours_range):
            hour = (start_hour + h) % 24
            count = hourly.get(hour, 0)
            
            # Format hour for display
            if hour == 0:
                display_hour = "12am"
            elif hour < 12:
                display_hour = f"{hour}am"
            elif hour == 12:
                display_hour = "12pm"
            else:
                display_hour = f"{hour-12}pm"
            
            visualization.append({
                'hour': hour,
                'display_hour': display_hour,
                'count': count,
                'percentage': round((count / total_messages) * 100, 1)
            })
        
        # Calculate stats
        peak_hour = max(hourly, key=hourly.get)
        peak_count = hourly[peak_hour]
        avg_per_hour = total_messages / hours_range
        
        stats = {
            'peak_hour': peak_hour,
            'peak_count': peak_count,
            'avg_per_hour': round(avg_per_hour, 1)
        }
        
        return {
            'hourly': hourly,
            'visualization': visualization,
            'stats': stats
        }

# Singleton instance
_campaign_scheduler = None

def get_campaign_scheduler():
    """Get the campaign scheduler singleton instance"""
    global _campaign_scheduler
    if _campaign_scheduler is None:
        _campaign_scheduler = CampaignScheduler()
    return _campaign_scheduler