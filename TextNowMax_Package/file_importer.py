"""
File Importer for TextNow Max

This module handles importing data from various file formats (CSV, TXT, Excel)
for account creation, messaging campaigns, and other functions.
"""

import os
import csv
import json
import random
import sqlite3
import datetime
from typing import List, Dict, Any, Optional, Tuple

# Try importing optional dependencies
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class FileImporter:
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the file importer"""
        self.database_path = database_path
        self._init_database()
        
    def _init_database(self):
        """Initialize database tables for imported data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create imported_data table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS imported_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT DEFAULT 'active'
        )
        ''')
        
        # Create imported_account_data table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS imported_account_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id INTEGER NOT NULL,
            name TEXT,
            email TEXT,
            birthdate TEXT,
            area_code TEXT,
            additional_data TEXT,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (import_id) REFERENCES imported_data(id)
        )
        ''')
        
        # Create imported_message_data table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS imported_message_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_id INTEGER NOT NULL,
            message_text TEXT NOT NULL,
            phone_number TEXT,
            additional_data TEXT,
            used INTEGER DEFAULT 0,
            FOREIGN KEY (import_id) REFERENCES imported_data(id)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def import_account_data(self, file_path: str) -> Tuple[bool, str, int]:
        """
        Import account creation data from file
        
        Args:
            file_path: Path to the file to import
            
        Returns:
            Tuple of (success, message, record_count)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                success, message, data = self._import_csv(file_path)
            elif file_ext == '.txt':
                success, message, data = self._import_txt(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                if not PANDAS_AVAILABLE:
                    return False, "Pandas is required for Excel import but not installed", 0
                success, message, data = self._import_excel(file_path)
            else:
                return False, f"Unsupported file format: {file_ext}", 0
                
            if not success:
                return False, message, 0
                
            # Process the data for account creation
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Record the import
            cursor.execute(
                "INSERT INTO imported_data (import_type, filename, record_count) VALUES (?, ?, ?)",
                ('account', os.path.basename(file_path), len(data))
            )
            import_id = cursor.lastrowid
            
            # Insert the data
            for record in data:
                name = record.get('name', '')
                email = record.get('email', '')
                birthdate = record.get('birthdate', '')
                area_code = record.get('area_code', '')
                
                # Additional data as JSON
                additional_data = {k: v for k, v in record.items() 
                                   if k not in ['name', 'email', 'birthdate', 'area_code']}
                
                cursor.execute(
                    """
                    INSERT INTO imported_account_data 
                    (import_id, name, email, birthdate, area_code, additional_data) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (import_id, name, email, birthdate, area_code, json.dumps(additional_data))
                )
            
            conn.commit()
            conn.close()
            
            return True, f"Successfully imported {len(data)} records for account creation", len(data)
            
        except Exception as e:
            return False, f"Error importing file: {str(e)}", 0
    
    def import_message_data(self, file_path: str) -> Tuple[bool, str, int]:
        """
        Import message data for campaigns
        
        Args:
            file_path: Path to the file to import
            
        Returns:
            Tuple of (success, message, record_count)
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.csv':
                success, message, data = self._import_csv(file_path)
            elif file_ext == '.txt':
                success, message, data = self._import_txt(file_path, as_messages=True)
            elif file_ext in ['.xlsx', '.xls']:
                if not PANDAS_AVAILABLE:
                    return False, "Pandas is required for Excel import but not installed", 0
                success, message, data = self._import_excel(file_path)
            else:
                return False, f"Unsupported file format: {file_ext}", 0
                
            if not success:
                return False, message, 0
                
            # Process the data for messages
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            
            # Record the import
            cursor.execute(
                "INSERT INTO imported_data (import_type, filename, record_count) VALUES (?, ?, ?)",
                ('message', os.path.basename(file_path), len(data))
            )
            import_id = cursor.lastrowid
            
            # Insert the data
            for record in data:
                # For text files imported as messages, each record is just the message text
                if isinstance(record, str):
                    message_text = record
                    phone_number = None
                    additional_data = '{}'
                else:
                    message_text = record.get('message', record.get('text', ''))
                    phone_number = record.get('phone', record.get('phone_number', record.get('number', None)))
                    
                    # Additional data as JSON
                    additional_data = {k: v for k, v in record.items() 
                                      if k not in ['message', 'text', 'phone', 'phone_number', 'number']}
                
                cursor.execute(
                    """
                    INSERT INTO imported_message_data 
                    (import_id, message_text, phone_number, additional_data) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (import_id, message_text, phone_number, json.dumps(additional_data))
                )
            
            conn.commit()
            conn.close()
            
            return True, f"Successfully imported {len(data)} messages", len(data)
            
        except Exception as e:
            return False, f"Error importing file: {str(e)}", 0
    
    def _import_csv(self, file_path: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Import data from a CSV file"""
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    data.append(row)
            
            if not data:
                return False, "CSV file is empty or has no valid rows", []
            
            return True, "CSV imported successfully", data
        
        except Exception as e:
            return False, f"Error reading CSV file: {str(e)}", []
    
    def _import_txt(self, file_path: str, as_messages=False) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Import data from a TXT file"""
        try:
            data = []
            with open(file_path, 'r', encoding='utf-8') as file:
                if as_messages:
                    # Each line is a separate message
                    for line in file:
                        line = line.strip()
                        if line:  # Skip empty lines
                            data.append(line)
                else:
                    # Try to detect if it's tab/comma separated
                    first_line = file.readline().strip()
                    file.seek(0)  # Reset to beginning of file
                    
                    if '\t' in first_line:
                        # Tab-separated
                        reader = csv.DictReader(file, delimiter='\t')
                        for row in reader:
                            data.append(row)
                    elif ',' in first_line:
                        # Comma-separated
                        reader = csv.DictReader(file)
                        for row in reader:
                            data.append(row)
                    else:
                        # Each line is a key=value format
                        for line in file:
                            line = line.strip()
                            if line and '=' in line:
                                parts = line.split('=', 1)
                                key = parts[0].strip()
                                value = parts[1].strip() if len(parts) > 1 else ""
                                data.append({key: value})
            
            if not data:
                return False, "TXT file is empty or has no valid data", []
            
            return True, "TXT file imported successfully", data
        
        except Exception as e:
            return False, f"Error reading TXT file: {str(e)}", []
    
    def _import_excel(self, file_path: str) -> Tuple[bool, str, List[Dict[str, Any]]]:
        """Import data from an Excel file"""
        try:
            df = pd.read_excel(file_path)
            if df.empty:
                return False, "Excel file is empty or has no valid data", []
            
            # Convert to list of dictionaries
            data = df.to_dict('records')
            return True, "Excel file imported successfully", data
        
        except Exception as e:
            return False, f"Error reading Excel file: {str(e)}", []
    
    def get_next_account_data(self) -> Optional[Dict[str, Any]]:
        """Get the next unused account data record"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, email, birthdate, area_code, additional_data
            FROM imported_account_data
            WHERE used = 0
            ORDER BY id
            LIMIT 1
        """)
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return None
        
        id, name, email, birthdate, area_code, additional_data_json = result
        
        # Mark as used
        cursor.execute("UPDATE imported_account_data SET used = 1 WHERE id = ?", (id,))
        conn.commit()
        
        # Parse additional data
        try:
            additional_data = json.loads(additional_data_json)
        except:
            additional_data = {}
        
        conn.close()
        
        return {
            'name': name,
            'email': email,
            'birthdate': birthdate,
            'area_code': area_code,
            **additional_data
        }
    
    def get_next_message(self, return_random=True) -> Optional[Dict[str, Any]]:
        """
        Get the next message for campaigns
        
        Args:
            return_random: If True, return a random message. If False, return in order.
        """
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        if return_random:
            cursor.execute("""
                SELECT id, message_text, phone_number, additional_data
                FROM imported_message_data
                ORDER BY RANDOM()
                LIMIT 1
            """)
        else:
            cursor.execute("""
                SELECT id, message_text, phone_number, additional_data
                FROM imported_message_data
                WHERE used = 0
                ORDER BY id
                LIMIT 1
            """)
        
        result = cursor.fetchone()
        if not result:
            # If all messages are used, reset and try again
            if not return_random:
                cursor.execute("UPDATE imported_message_data SET used = 0")
                conn.commit()
                
                cursor.execute("""
                    SELECT id, message_text, phone_number, additional_data
                    FROM imported_message_data
                    WHERE used = 0
                    ORDER BY id
                    LIMIT 1
                """)
                result = cursor.fetchone()
        
        if not result:
            conn.close()
            return None
        
        id, message_text, phone_number, additional_data_json = result
        
        # Mark as used if we're returning in order
        if not return_random:
            cursor.execute("UPDATE imported_message_data SET used = 1 WHERE id = ?", (id,))
            conn.commit()
        
        # Parse additional data
        try:
            additional_data = json.loads(additional_data_json)
        except:
            additional_data = {}
        
        conn.close()
        
        return {
            'message': message_text,
            'phone_number': phone_number,
            **additional_data
        }
    
    def get_import_history(self, import_type=None) -> List[Dict[str, Any]]:
        """Get history of imports"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        query = "SELECT id, import_type, filename, record_count, import_date, status FROM imported_data"
        params = []
        
        if import_type:
            query += " WHERE import_type = ?"
            params.append(import_type)
        
        query += " ORDER BY import_date DESC"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        imports = []
        for id, type, filename, count, date, status in results:
            imports.append({
                'id': id,
                'type': type,
                'filename': filename,
                'record_count': count,
                'import_date': date,
                'status': status
            })
        
        conn.close()
        return imports
    
    def delete_import(self, import_id: int) -> Tuple[bool, str]:
        """Delete an import and its associated data"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        try:
            # Get import type to know which table to clean
            cursor.execute("SELECT import_type FROM imported_data WHERE id = ?", (import_id,))
            result = cursor.fetchone()
            
            if not result:
                conn.close()
                return False, "Import not found"
            
            import_type = result[0]
            
            # Delete the associated data
            if import_type == 'account':
                cursor.execute("DELETE FROM imported_account_data WHERE import_id = ?", (import_id,))
            elif import_type == 'message':
                cursor.execute("DELETE FROM imported_message_data WHERE import_id = ?", (import_id,))
            
            # Delete the import record
            cursor.execute("DELETE FROM imported_data WHERE id = ?", (import_id,))
            
            conn.commit()
            conn.close()
            
            return True, "Import deleted successfully"
        
        except Exception as e:
            conn.rollback()
            conn.close()
            return False, f"Error deleting import: {str(e)}"
    
    def get_import_details(self, import_id: int) -> Dict[str, Any]:
        """Get details of a specific import"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Get import record
        cursor.execute(
            "SELECT id, import_type, filename, record_count, import_date, status FROM imported_data WHERE id = ?", 
            (import_id,)
        )
        
        result = cursor.fetchone()
        if not result:
            conn.close()
            return {'success': False, 'message': 'Import not found'}
        
        id, import_type, filename, count, date, status = result
        
        # Get sample of records
        if import_type == 'account':
            cursor.execute(
                """
                SELECT name, email, birthdate, area_code, used
                FROM imported_account_data
                WHERE import_id = ?
                LIMIT 10
                """,
                (import_id,)
            )
            
            columns = ['name', 'email', 'birthdate', 'area_code', 'used']
            
        elif import_type == 'message':
            cursor.execute(
                """
                SELECT message_text, phone_number, used
                FROM imported_message_data
                WHERE import_id = ?
                LIMIT 10
                """,
                (import_id,)
            )
            
            columns = ['message', 'phone_number', 'used']
        
        records = []
        for row in cursor.fetchall():
            record = dict(zip(columns, row))
            records.append(record)
        
        # Get usage stats
        if import_type == 'account':
            cursor.execute(
                "SELECT COUNT(*) FROM imported_account_data WHERE import_id = ? AND used = 1",
                (import_id,)
            )
        elif import_type == 'message':
            cursor.execute(
                "SELECT COUNT(*) FROM imported_message_data WHERE import_id = ? AND used = 1",
                (import_id,)
            )
        
        used_count = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'success': True,
            'import': {
                'id': id,
                'type': import_type,
                'filename': filename,
                'record_count': count,
                'import_date': date,
                'status': status,
                'used_count': used_count,
                'usage_percentage': round((used_count / count) * 100, 1) if count > 0 else 0
            },
            'sample_records': records
        }

# Singleton instance
_file_importer = None

def get_file_importer():
    """Get the file importer singleton instance"""
    global _file_importer
    if _file_importer is None:
        _file_importer = FileImporter()
    return _file_importer