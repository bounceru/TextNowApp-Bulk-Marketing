"""
Area Code Manager for TextNow Max

This module manages area code prioritization and selection for TextNow account creation,
with special emphasis on Florida area codes.
"""

import random
import sqlite3
import json
import os
from collections import defaultdict

class AreaCodeManager:
    def __init__(self, database_path='ghost_accounts.db'):
        """Initialize the area code manager"""
        self.database_path = database_path
        self._init_database()
        self.florida_area_codes = ['954', '754', '305', '786', '561']
        self.load_area_codes()
        
    def _init_database(self):
        """Initialize database connection and tables if needed"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Create area code tracking table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS area_code_stats (
            area_code TEXT PRIMARY KEY,
            state TEXT,
            city TEXT,
            usage_count INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0,
            priority INTEGER DEFAULT 0
        )
        ''')
        
        # Create area code set table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS area_code_sets (
            set_name TEXT PRIMARY KEY,
            description TEXT,
            area_codes TEXT,
            is_default INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def load_area_codes(self):
        """Load area code data from the database or initialize with defaults"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Check if area code data exists
        cursor.execute("SELECT COUNT(*) FROM area_code_stats")
        count = cursor.fetchone()[0]
        
        if count == 0:
            # Initialize with ALL US area codes, organized by state
            # Dictionary of all area codes by state, with major cities
            # This includes all 50 states plus DC, organized alphabetically
            all_area_codes = {
                'Alabama': [
                    ('205', 'Birmingham', 60), ('251', 'Mobile', 60), ('256', 'Huntsville', 60), 
                    ('334', 'Montgomery', 60), ('938', 'Huntsville', 60)
                ],
                'Alaska': [
                    ('907', 'Anchorage', 50)
                ],
                'Arizona': [
                    ('480', 'Phoenix/Mesa', 60), ('520', 'Tucson', 60), ('602', 'Phoenix', 60), 
                    ('623', 'Phoenix', 60), ('928', 'Flagstaff', 60)
                ],
                'Arkansas': [
                    ('479', 'Fort Smith', 50), ('501', 'Little Rock', 50), ('870', 'Jonesboro', 50)
                ],
                'California': [
                    ('209', 'Stockton', 70), ('213', 'Los Angeles', 70), ('279', 'Sacramento', 70),
                    ('310', 'Los Angeles', 70), ('323', 'Los Angeles', 70), ('341', 'Oakland', 70),
                    ('408', 'San Jose', 70), ('415', 'San Francisco', 70), ('424', 'Los Angeles', 70),
                    ('442', 'Palm Springs', 60), ('510', 'Oakland', 70), ('530', 'Redding', 60),
                    ('559', 'Fresno', 60), ('562', 'Long Beach', 70), ('619', 'San Diego', 70),
                    ('626', 'Pasadena', 70), ('628', 'San Francisco', 70), ('650', 'San Mateo', 70),
                    ('657', 'Anaheim', 70), ('661', 'Bakersfield', 60), ('669', 'San Jose', 70),
                    ('707', 'Santa Rosa', 60), ('714', 'Anaheim', 70), ('747', 'Los Angeles', 70),
                    ('760', 'Palm Springs', 60), ('805', 'Ventura', 60), ('818', 'Burbank', 70),
                    ('820', 'Los Angeles', 70), ('831', 'Salinas', 60), ('858', 'San Diego', 70),
                    ('909', 'San Bernardino', 70), ('916', 'Sacramento', 70), ('925', 'Concord', 60),
                    ('949', 'Irvine', 70), ('951', 'Riverside', 70)
                ],
                'Colorado': [
                    ('303', 'Denver', 60), ('719', 'Colorado Springs', 60), ('720', 'Denver', 60), 
                    ('970', 'Fort Collins', 60)
                ],
                'Connecticut': [
                    ('203', 'Bridgeport', 60), ('475', 'New Haven', 60), ('860', 'Hartford', 60), 
                    ('959', 'Hartford', 60)
                ],
                'Delaware': [
                    ('302', 'Wilmington', 50)
                ],
                'District of Columbia': [
                    ('202', 'Washington DC', 60)
                ],
                'Florida': [
                    ('239', 'Fort Myers', 90), ('305', 'Miami', 100), ('321', 'Orlando', 90), 
                    ('352', 'Gainesville', 90), ('386', 'Daytona Beach', 90), ('407', 'Orlando', 90), 
                    ('561', 'West Palm Beach', 100), ('727', 'St. Petersburg', 90), ('754', 'Fort Lauderdale', 100), 
                    ('772', 'Port St. Lucie', 90), ('786', 'Miami', 100), ('813', 'Tampa', 90), 
                    ('850', 'Tallahassee', 90), ('863', 'Lakeland', 90), ('904', 'Jacksonville', 90), 
                    ('941', 'Sarasota', 90), ('954', 'Fort Lauderdale', 100)
                ],
                'Georgia': [
                    ('229', 'Albany', 60), ('404', 'Atlanta', 70), ('470', 'Atlanta', 70), 
                    ('478', 'Macon', 60), ('678', 'Atlanta', 70), ('706', 'Augusta', 60), 
                    ('762', 'Augusta', 60), ('770', 'Atlanta', 70), ('912', 'Savannah', 60), 
                    ('943', 'Atlanta', 70)
                ],
                'Hawaii': [
                    ('808', 'Honolulu', 50)
                ],
                'Idaho': [
                    ('208', 'Boise', 50), ('986', 'Boise', 50)
                ],
                'Illinois': [
                    ('217', 'Springfield', 60), ('224', 'Chicago', 70), ('309', 'Peoria', 60), 
                    ('312', 'Chicago', 70), ('331', 'Aurora', 60), ('618', 'East St. Louis', 60), 
                    ('630', 'Aurora', 60), ('708', 'Cicero', 60), ('773', 'Chicago', 70), 
                    ('779', 'Rockford', 60), ('815', 'Rockford', 60), ('847', 'Evanston', 60), 
                    ('872', 'Chicago', 70)
                ],
                'Indiana': [
                    ('219', 'Gary', 60), ('260', 'Fort Wayne', 60), ('317', 'Indianapolis', 60), 
                    ('463', 'Indianapolis', 60), ('574', 'South Bend', 60), ('765', 'Lafayette', 60), 
                    ('812', 'Evansville', 60), ('930', 'Evansville', 60)
                ],
                'Iowa': [
                    ('319', 'Cedar Rapids', 50), ('515', 'Des Moines', 50), ('563', 'Davenport', 50), 
                    ('641', 'Mason City', 50), ('712', 'Sioux City', 50)
                ],
                'Kansas': [
                    ('316', 'Wichita', 50), ('620', 'Dodge City', 50), ('785', 'Topeka', 50), 
                    ('913', 'Kansas City', 50)
                ],
                'Kentucky': [
                    ('270', 'Bowling Green', 50), ('364', 'Bowling Green', 50), ('502', 'Louisville', 50), 
                    ('606', 'Ashland', 50), ('859', 'Lexington', 50)
                ],
                'Louisiana': [
                    ('225', 'Baton Rouge', 60), ('318', 'Shreveport', 60), ('337', 'Lafayette', 60), 
                    ('504', 'New Orleans', 60), ('985', 'Houma', 60)
                ],
                'Maine': [
                    ('207', 'Portland', 50)
                ],
                'Maryland': [
                    ('240', 'Silver Spring', 60), ('301', 'Silver Spring', 60), ('410', 'Baltimore', 60), 
                    ('443', 'Baltimore', 60), ('667', 'Baltimore', 60)
                ],
                'Massachusetts': [
                    ('339', 'Boston', 60), ('351', 'Lowell', 60), ('413', 'Springfield', 60), 
                    ('508', 'Worcester', 60), ('617', 'Boston', 60), ('774', 'Worcester', 60), 
                    ('781', 'Lynn', 60), ('857', 'Boston', 60), ('978', 'Lowell', 60)
                ],
                'Michigan': [
                    ('231', 'Muskegon', 60), ('248', 'Troy', 60), ('269', 'Kalamazoo', 60), 
                    ('313', 'Detroit', 60), ('517', 'Lansing', 60), ('586', 'Warren', 60), 
                    ('616', 'Grand Rapids', 60), ('734', 'Ann Arbor', 60), ('810', 'Flint', 60), 
                    ('906', 'Marquette', 50), ('947', 'Troy', 60), ('989', 'Saginaw', 50)
                ],
                'Minnesota': [
                    ('218', 'Duluth', 50), ('320', 'St. Cloud', 50), ('507', 'Rochester', 50), 
                    ('612', 'Minneapolis', 60), ('651', 'St. Paul', 60), ('763', 'Brooklyn Park', 60), 
                    ('952', 'Bloomington', 60)
                ],
                'Mississippi': [
                    ('228', 'Gulfport', 50), ('601', 'Jackson', 50), ('662', 'Tupelo', 50), 
                    ('769', 'Jackson', 50)
                ],
                'Missouri': [
                    ('314', 'St. Louis', 60), ('417', 'Springfield', 50), ('557', 'St. Louis', 60), 
                    ('573', 'Columbia', 50), ('636', 'OFallon', 60), ('660', 'Sedalia', 50), 
                    ('816', 'Kansas City', 60)
                ],
                'Montana': [
                    ('406', 'Billings', 50)
                ],
                'Nebraska': [
                    ('308', 'Grand Island', 50), ('402', 'Omaha', 50), ('531', 'Omaha', 50)
                ],
                'Nevada': [
                    ('702', 'Las Vegas', 60), ('725', 'Las Vegas', 60), ('775', 'Reno', 50)
                ],
                'New Hampshire': [
                    ('603', 'Manchester', 50)
                ],
                'New Jersey': [
                    ('201', 'Jersey City', 60), ('551', 'Jersey City', 60), ('609', 'Trenton', 60), 
                    ('640', 'Camden', 60), ('732', 'Toms River', 60), ('848', 'Toms River', 60), 
                    ('856', 'Camden', 60), ('862', 'Newark', 60), ('908', 'Elizabeth', 60), 
                    ('973', 'Newark', 60)
                ],
                'New Mexico': [
                    ('505', 'Albuquerque', 50), ('575', 'Las Cruces', 50)
                ],
                'New York': [
                    ('212', 'New York City', 70), ('315', 'Syracuse', 60), ('332', 'New York City', 70), 
                    ('347', 'Brooklyn', 70), ('516', 'Hempstead', 70), ('518', 'Albany', 60), 
                    ('585', 'Rochester', 60), ('607', 'Binghamton', 60), ('631', 'Brentwood', 70), 
                    ('646', 'New York City', 70), ('680', 'Buffalo', 60), ('716', 'Buffalo', 60), 
                    ('718', 'New York City', 70), ('838', 'Albany', 60), ('845', 'Poughkeepsie', 60), 
                    ('914', 'Yonkers', 70), ('917', 'New York City', 70), ('929', 'New York City', 70), 
                    ('934', 'Brentwood', 70)
                ],
                'North Carolina': [
                    ('252', 'Greenville', 60), ('336', 'Greensboro', 60), ('704', 'Charlotte', 60), 
                    ('743', 'Greensboro', 60), ('828', 'Asheville', 60), ('910', 'Fayetteville', 60), 
                    ('919', 'Raleigh', 60), ('980', 'Charlotte', 60), ('984', 'Raleigh', 60)
                ],
                'North Dakota': [
                    ('701', 'Fargo', 50)
                ],
                'Ohio': [
                    ('216', 'Cleveland', 60), ('220', 'Newark', 60), ('234', 'Akron', 60), 
                    ('330', 'Akron', 60), ('380', 'Columbus', 60), ('419', 'Toledo', 60), 
                    ('440', 'Parma', 60), ('513', 'Cincinnati', 60), ('567', 'Toledo', 60), 
                    ('614', 'Columbus', 60), ('740', 'Newark', 60), ('937', 'Dayton', 60)
                ],
                'Oklahoma': [
                    ('405', 'Oklahoma City', 50), ('539', 'Tulsa', 50), ('572', 'Tulsa', 50), 
                    ('580', 'Lawton', 50), ('918', 'Tulsa', 50)
                ],
                'Oregon': [
                    ('458', 'Eugene', 60), ('503', 'Portland', 60), ('541', 'Eugene', 60), 
                    ('971', 'Portland', 60)
                ],
                'Pennsylvania': [
                    ('215', 'Philadelphia', 60), ('223', 'Lancaster', 60), ('267', 'Philadelphia', 60), 
                    ('272', 'Scranton', 60), ('412', 'Pittsburgh', 60), ('445', 'Philadelphia', 60), 
                    ('484', 'Allentown', 60), ('570', 'Scranton', 60), ('610', 'Allentown', 60), 
                    ('717', 'Lancaster', 60), ('724', 'New Castle', 60), ('814', 'Erie', 60), 
                    ('878', 'Pittsburgh', 60)
                ],
                'Rhode Island': [
                    ('401', 'Providence', 50)
                ],
                'South Carolina': [
                    ('803', 'Columbia', 60), ('843', 'Charleston', 60), ('854', 'Charleston', 60), 
                    ('864', 'Greenville', 60)
                ],
                'South Dakota': [
                    ('605', 'Sioux Falls', 50)
                ],
                'Tennessee': [
                    ('423', 'Chattanooga', 60), ('615', 'Nashville', 60), ('629', 'Nashville', 60), 
                    ('731', 'Jackson', 60), ('865', 'Knoxville', 60), ('901', 'Memphis', 60), 
                    ('931', 'Clarksville', 60)
                ],
                'Texas': [
                    ('210', 'San Antonio', 60), ('214', 'Dallas', 60), ('254', 'Killeen', 60), 
                    ('281', 'Houston', 60), ('325', 'Abilene', 60), ('346', 'Houston', 60), 
                    ('361', 'Corpus Christi', 60), ('409', 'Beaumont', 60), ('430', 'Tyler', 60), 
                    ('432', 'Midland', 60), ('469', 'Dallas', 60), ('512', 'Austin', 60), 
                    ('682', 'Fort Worth', 60), ('713', 'Houston', 60), ('726', 'San Antonio', 60), 
                    ('737', 'Austin', 60), ('806', 'Lubbock', 60), ('817', 'Fort Worth', 60), 
                    ('830', 'New Braunfels', 60), ('832', 'Houston', 60), ('903', 'Tyler', 60), 
                    ('915', 'El Paso', 60), ('936', 'Conroe', 60), ('940', 'Denton', 60), 
                    ('956', 'Laredo', 60), ('972', 'Dallas', 60), ('979', 'College Station', 60)
                ],
                'Utah': [
                    ('385', 'Salt Lake City', 50), ('435', 'St. George', 50), ('801', 'Salt Lake City', 50)
                ],
                'Vermont': [
                    ('802', 'Burlington', 50)
                ],
                'Virginia': [
                    ('276', 'Bristol', 60), ('434', 'Lynchburg', 60), ('540', 'Roanoke', 60), 
                    ('571', 'Arlington', 60), ('703', 'Arlington', 60), ('757', 'Virginia Beach', 60), 
                    ('804', 'Richmond', 60), ('826', 'Virginia Beach', 60), ('948', 'Roanoke', 60)
                ],
                'Washington': [
                    ('206', 'Seattle', 60), ('253', 'Tacoma', 60), ('360', 'Vancouver', 60), 
                    ('425', 'Bellevue', 60), ('509', 'Spokane', 60), ('564', 'Vancouver', 60)
                ],
                'West Virginia': [
                    ('304', 'Charleston', 50), ('681', 'Charleston', 50)
                ],
                'Wisconsin': [
                    ('262', 'Kenosha', 50), ('414', 'Milwaukee', 60), ('534', 'Eau Claire', 50), 
                    ('608', 'Madison', 60), ('715', 'Eau Claire', 50), ('920', 'Green Bay', 50)
                ],
                'Wyoming': [
                    ('307', 'Cheyenne', 50)
                ]
            }
            
            # Flatten the data for database insertion
            area_code_data = []
            for state, codes in all_area_codes.items():
                for code, city, priority in codes:
                    area_code_data.append((code, state, city, 0, 0, priority))
            
            cursor.executemany(
                "INSERT INTO area_code_stats (area_code, state, city, usage_count, success_rate, priority) VALUES (?, ?, ?, ?, ?, ?)",
                area_code_data
            )
            
            # Create default area code sets for each state and some common groupings
            sets_data = []
            
            # Default Florida set (south Florida priority for backward compatibility)
            sets_data.append(('florida_south', 'South Florida Area Codes', json.dumps(['954', '754', '305', '786', '561']), 1))
            
            # Add sets for each state
            for state, codes in all_area_codes.items():
                state_code = state.lower().replace(' ', '_')
                state_codes = [code[0] for code in codes]
                sets_data.append((f'{state_code}_all', f'All {state} Area Codes', json.dumps(state_codes), 0))
            
            # Add regional groupings
            northeast_states = ['Connecticut', 'Maine', 'Massachusetts', 'New Hampshire', 
                                'New Jersey', 'New York', 'Pennsylvania', 'Rhode Island', 'Vermont']
            southeast_states = ['Alabama', 'Florida', 'Georgia', 'Kentucky', 'Mississippi', 
                                'North Carolina', 'South Carolina', 'Tennessee', 'Virginia', 'West Virginia']
            midwest_states = ['Illinois', 'Indiana', 'Iowa', 'Kansas', 'Michigan', 
                              'Minnesota', 'Missouri', 'Nebraska', 'North Dakota', 'Ohio', 'South Dakota', 'Wisconsin']
            southwest_states = ['Arizona', 'New Mexico', 'Oklahoma', 'Texas']
            west_states = ['Alaska', 'California', 'Colorado', 'Hawaii', 'Idaho', 
                           'Montana', 'Nevada', 'Oregon', 'Utah', 'Washington', 'Wyoming']
            
            # Get area codes for each region
            northeast_codes = []
            for state in northeast_states:
                if state in all_area_codes:
                    northeast_codes.extend([code[0] for code in all_area_codes[state]])
            
            southeast_codes = []
            for state in southeast_states:
                if state in all_area_codes:
                    southeast_codes.extend([code[0] for code in all_area_codes[state]])
            
            midwest_codes = []
            for state in midwest_states:
                if state in all_area_codes:
                    midwest_codes.extend([code[0] for code in all_area_codes[state]])
            
            southwest_codes = []
            for state in southwest_states:
                if state in all_area_codes:
                    southwest_codes.extend([code[0] for code in all_area_codes[state]])
            
            west_codes = []
            for state in west_states:
                if state in all_area_codes:
                    west_codes.extend([code[0] for code in all_area_codes[state]])
            
            # Add regional sets
            sets_data.append(('northeast', 'Northeast US Area Codes', json.dumps(northeast_codes), 0))
            sets_data.append(('southeast', 'Southeast US Area Codes', json.dumps(southeast_codes), 0))
            sets_data.append(('midwest', 'Midwest US Area Codes', json.dumps(midwest_codes), 0))
            sets_data.append(('southwest', 'Southwest US Area Codes', json.dumps(southwest_codes), 0))
            sets_data.append(('west', 'Western US Area Codes', json.dumps(west_codes), 0))
            
            # Add major cities set
            major_cities = [
                '212', '332', '646', '718', '917', '929',  # NYC
                '213', '310', '323', '424', '213', '818',  # LA
                '312', '773', '872',                       # Chicago
                '713', '281', '832', '346',                # Houston
                '602', '480', '623',                       # Phoenix
                '215', '267', '445',                       # Philadelphia
                '210', '726',                              # San Antonio
                '619', '858',                              # San Diego
                '214', '469', '972',                       # Dallas
                '512', '737'                               # Austin
            ]
            sets_data.append(('major_cities', 'Major US Cities Area Codes', json.dumps(major_cities), 0))
            
            # Insert all sets
            cursor.executemany(
                "INSERT INTO area_code_sets (set_name, description, area_codes, is_default) VALUES (?, ?, ?, ?)",
                sets_data
            )
            
            conn.commit()
        
        conn.close()
    
    def get_florida_area_codes(self):
        """Get the list of Florida area codes with priority on south Florida"""
        return self.florida_area_codes
    
    def get_all_area_codes_by_state(self):
        """Get all area codes grouped by state"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT area_code, state, city, priority FROM area_code_stats ORDER BY state, priority DESC, city")
        results = cursor.fetchall()
        
        conn.close()
        
        area_codes_by_state = defaultdict(list)
        for area_code, state, city, priority in results:
            area_codes_by_state[state].append({
                'area_code': area_code,
                'city': city,
                'priority': priority
            })
        
        return dict(area_codes_by_state)
    
    def get_area_code_sets(self):
        """Get all defined area code sets"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT set_name, description, area_codes, is_default FROM area_code_sets")
        results = cursor.fetchall()
        
        conn.close()
        
        sets = []
        for set_name, description, area_codes_json, is_default in results:
            sets.append({
                'name': set_name,
                'description': description,
                'area_codes': json.loads(area_codes_json),
                'is_default': bool(is_default)
            })
        
        return sets
    
    def get_default_area_code_set(self):
        """Get the default area code set"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT area_codes FROM area_code_sets WHERE is_default=1 LIMIT 1")
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return json.loads(result[0])
        else:
            return self.florida_area_codes
    
    def set_default_area_code_set(self, set_name):
        """Set a new default area code set"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Reset all defaults
        cursor.execute("UPDATE area_code_sets SET is_default=0")
        
        # Set new default
        cursor.execute("UPDATE area_code_sets SET is_default=1 WHERE set_name=?", (set_name,))
        
        conn.commit()
        conn.close()
    
    def create_area_code_set(self, set_name, description, area_codes, set_as_default=False):
        """Create a new area code set"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # If setting as default, reset all others
        if set_as_default:
            cursor.execute("UPDATE area_code_sets SET is_default=0")
        
        # Convert area codes to JSON
        area_codes_json = json.dumps(area_codes)
        
        # Check if set already exists
        cursor.execute("SELECT COUNT(*) FROM area_code_sets WHERE set_name=?", (set_name,))
        count = cursor.fetchone()[0]
        
        if count > 0:
            # Update existing set
            cursor.execute(
                "UPDATE area_code_sets SET description=?, area_codes=?, is_default=? WHERE set_name=?",
                (description, area_codes_json, 1 if set_as_default else 0, set_name)
            )
        else:
            # Create new set
            cursor.execute(
                "INSERT INTO area_code_sets (set_name, description, area_codes, is_default) VALUES (?, ?, ?, ?)",
                (set_name, description, area_codes_json, 1 if set_as_default else 0)
            )
        
        conn.commit()
        conn.close()
    
    def delete_area_code_set(self, set_name):
        """Delete an area code set"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Check if set is default
        cursor.execute("SELECT is_default FROM area_code_sets WHERE set_name=?", (set_name,))
        result = cursor.fetchone()
        
        if result and result[0] == 1:
            # Set was default, set Florida South as default
            cursor.execute("UPDATE area_code_sets SET is_default=1 WHERE set_name='florida_south'")
        
        # Delete the set
        cursor.execute("DELETE FROM area_code_sets WHERE set_name=?", (set_name,))
        
        conn.commit()
        conn.close()
    
    def get_random_area_code(self, state=None, prioritize_florida=True):
        """Get a random area code, prioritizing Florida if specified"""
        if prioritize_florida:
            return random.choice(self.florida_area_codes)
        
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        if state:
            cursor.execute("SELECT area_code FROM area_code_stats WHERE state=? ORDER BY priority DESC", (state,))
        else:
            cursor.execute("SELECT area_code FROM area_code_stats ORDER BY priority DESC")
        
        results = cursor.fetchall()
        conn.close()
        
        if results:
            # Weighted random selection based on priority
            area_codes = [row[0] for row in results]
            return random.choice(area_codes)
        else:
            # Fallback to Florida area codes
            return random.choice(self.florida_area_codes)
    
    def record_area_code_usage(self, area_code, success=True):
        """Record usage of an area code and update success rate"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        # Check if area code exists
        cursor.execute("SELECT usage_count, success_rate FROM area_code_stats WHERE area_code=?", (area_code,))
        result = cursor.fetchone()
        
        if result:
            usage_count, success_rate = result
            new_count = usage_count + 1
            
            # Calculate new success rate
            if success:
                new_success_rate = ((success_rate * usage_count) + 1) / new_count
            else:
                new_success_rate = (success_rate * usage_count) / new_count
            
            cursor.execute(
                "UPDATE area_code_stats SET usage_count=?, success_rate=? WHERE area_code=?",
                (new_count, new_success_rate, area_code)
            )
        else:
            # Add new area code with default values
            cursor.execute(
                "INSERT INTO area_code_stats (area_code, usage_count, success_rate) VALUES (?, ?, ?)",
                (area_code, 1, 1.0 if success else 0.0)
            )
        
        conn.commit()
        conn.close()
    
    def get_area_code_stats(self):
        """Get statistics on area code usage and success rates"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT area_code, state, city, usage_count, success_rate, priority 
            FROM area_code_stats 
            ORDER BY usage_count DESC, success_rate DESC
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        stats = []
        for area_code, state, city, usage_count, success_rate, priority in results:
            stats.append({
                'area_code': area_code,
                'state': state or 'Unknown',
                'city': city or 'Unknown',
                'usage_count': usage_count,
                'success_rate': success_rate,
                'priority': priority
            })
        
        return stats

# Singleton instance
_area_code_manager = None

def get_area_code_manager():
    """Get the area code manager singleton instance"""
    global _area_code_manager
    if _area_code_manager is None:
        _area_code_manager = AreaCodeManager()
    return _area_code_manager

# Initialize singleton on module load
get_area_code_manager()