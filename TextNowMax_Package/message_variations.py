"""
Message Variations Manager for TextNow Max Creator

This module handles the loading, parsing, and management of message variations
for campaigns. It supports loading variations from text files and CSV files.
"""

import os
import csv
import re
import json
import random
import logging

logger = logging.getLogger(__name__)

def parse_message_file(file_path):
    """
    Parse a file containing message variations.
    Supports .txt (one message per line) and .csv formats.
    
    Returns a list of message variations.
    """
    _, file_ext = os.path.splitext(file_path)
    file_ext = file_ext.lower()
    
    try:
        if file_ext == '.txt':
            return parse_text_file(file_path)
        elif file_ext == '.csv':
            return parse_csv_file(file_path)
        else:
            logger.error(f"Unsupported file extension: {file_ext}")
            return []
    except Exception as e:
        logger.error(f"Error parsing message file: {str(e)}")
        return []

def parse_text_file(file_path):
    """Parse a text file with one message per line"""
    messages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    messages.append(line)
        return messages
    except Exception as e:
        logger.error(f"Error reading text file: {str(e)}")
        return []

def parse_csv_file(file_path):
    """Parse a CSV file with message variations"""
    messages = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            for row in reader:
                if row and len(row) > 0 and row[0].strip() and not row[0].startswith('#'):
                    messages.append(row[0].strip())
        return messages
    except Exception as e:
        logger.error(f"Error reading CSV file: {str(e)}")
        return []

def save_variations_to_json(variations):
    """Convert variations list to JSON string for storage"""
    try:
        return json.dumps(variations)
    except Exception as e:
        logger.error(f"Error converting variations to JSON: {str(e)}")
        return json.dumps([])

def load_variations_from_json(json_str):
    """Load variations from JSON string"""
    try:
        if not json_str:
            return []
        return json.loads(json_str)
    except Exception as e:
        logger.error(f"Error loading variations from JSON: {str(e)}")
        return []

def random_variation(variations, used_variations=None):
    """
    Get a random message variation that hasn't been used recently
    
    Args:
        variations: List of message variations
        used_variations: List of recently used variation indices
        
    Returns:
        Tuple of (message, index)
    """
    if not variations:
        return "Hello! How are you today?", -1
    
    if not used_variations:
        used_variations = []
    
    # Get available variations (not recently used)
    available = [i for i in range(len(variations)) if i not in used_variations]
    
    # If all have been used, reset
    if not available:
        available = list(range(len(variations)))
    
    # Pick a random available variation
    index = random.choice(available)
    return variations[index], index

def insert_variables(message_template, variables=None):
    """
    Insert variables into a message template.
    
    Variables are in the format {variable_name}.
    
    Args:
        message_template: The message template with variables
        variables: Dict of variable names to values
        
    Returns:
        Message with variables replaced
    """
    if not variables:
        variables = {}
    
    # Find all variables in the template
    template_vars = re.findall(r'\{(\w+)\}', message_template)
    
    # Replace each variable with its value
    result = message_template
    for var in template_vars:
        if var in variables:
            result = result.replace(f"{{{var}}}", str(variables[var]))
    
    return result

def get_message_with_variables(variations, variables=None, used_variations=None):
    """
    Get a random message variation with variables inserted
    
    Args:
        variations: List of message variations
        variables: Dict of variable names to values
        used_variations: List of recently used variation indices
        
    Returns:
        Tuple of (final_message, variation_index)
    """
    message, index = random_variation(variations, used_variations)
    return insert_variables(message, variables), index