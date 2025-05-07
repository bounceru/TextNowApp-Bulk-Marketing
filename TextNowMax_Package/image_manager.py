"""
Image Management System for ProgressGhostCreator

This module handles the management of large image pools for use in TextNow messages,
including categorization, variation tracking, and intelligent rotation to avoid detection patterns.
"""

import os
import json
import random
import hashlib
import sqlite3
import logging
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple, Set
import threading
import queue
from PIL import Image, ImageFile
import io

# Allow partial image loading to handle corrupt images more gracefully
ImageFile.LOAD_TRUNCATED_IMAGES = True

class ImageManager:
    """Class to manage large image pools for TextNow messages"""
    
    def __init__(self, db_path='ghost_accounts.db', image_dir='images'):
        """
        Initialize the image manager
        
        Args:
            db_path: Path to the SQLite database
            image_dir: Directory containing image files
        """
        self.db_path = db_path
        self.image_dir = image_dir
        self.default_category = "general"
        
        # Create images directory if it doesn't exist
        os.makedirs(image_dir, exist_ok=True)
        
        # Categories subdirectories
        self.categories = ["general", "sports", "lifestyle", "betting", "promotional", "seasonal", "personal"]
        for category in self.categories:
            os.makedirs(os.path.join(image_dir, category), exist_ok=True)
        
        # Initialize database connection
        self._init_database()
        
        # Cache for image metadata to avoid excessive database queries
        self.image_cache = {}
        self.cache_lock = threading.RLock()
        
        # Image processing queue
        self.processing_queue = queue.Queue()
        self.processing_thread = threading.Thread(target=self._process_images_thread)
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        logging.info(f"Image manager initialized with directory: {image_dir}")
        
    def _init_database(self):
        """Initialize the database tables"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            
            # Create images table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                checksum TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                width INTEGER,
                height INTEGER,
                file_size INTEGER,
                mime_type TEXT,
                created_at TEXT NOT NULL,
                last_used TEXT,
                use_count INTEGER DEFAULT 0,
                UNIQUE(checksum)
            )
            """)
            
            # Create image_usage table to track which accounts used which images
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                contact TEXT,
                used_at TEXT NOT NULL,
                campaign_id INTEGER,
                FOREIGN KEY (image_id) REFERENCES images(id),
                FOREIGN KEY (account_id) REFERENCES accounts(id)
            )
            """)
            
            # Create images_tags table for organizing with multiple tags
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS image_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id INTEGER NOT NULL,
                tag TEXT NOT NULL,
                FOREIGN KEY (image_id) REFERENCES images(id),
                UNIQUE(image_id, tag)
            )
            """)
            
            self.conn.commit()
            
        except sqlite3.Error as e:
            logging.error(f"Database initialization error: {e}")
            raise
    
    def import_images(self, source_path, category=None, recursive=False, batch_size=100):
        """
        Import images from a directory
        
        Args:
            source_path: Directory containing images to import
            category: Category to assign to imported images (uses directory name if None)
            recursive: Whether to search subdirectories
            batch_size: Number of images to process in each batch
            
        Returns:
            Dict with import statistics
        """
        if not os.path.exists(source_path):
            raise FileNotFoundError(f"Source path does not exist: {source_path}")
        
        # If category is None, use the directory name
        if category is None:
            category = os.path.basename(source_path)
            if category not in self.categories:
                category = self.default_category
        
        # Get list of image files
        image_files = []
        if recursive:
            for root, _, files in os.walk(source_path):
                for file in files:
                    if self._is_image_file(file):
                        image_files.append(os.path.join(root, file))
        else:
            image_files = [os.path.join(source_path, f) for f in os.listdir(source_path) 
                         if os.path.isfile(os.path.join(source_path, f)) and self._is_image_file(f)]
        
        # Process images in batches
        total_files = len(image_files)
        imported = 0
        skipped = 0
        failed = 0
        
        for i in range(0, total_files, batch_size):
            batch_files = image_files[i:i+batch_size]
            
            for file_path in batch_files:
                try:
                    # Check if image already exists by calculating checksum
                    checksum = self._calculate_checksum(file_path)
                    
                    # Check if image with this checksum already exists
                    cursor = self.conn.cursor()
                    cursor.execute("SELECT id FROM images WHERE checksum = ?", (checksum,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        logging.info(f"Skipping duplicate image: {file_path}")
                        skipped += 1
                        continue
                    
                    # Get image metadata
                    try:
                        metadata = self._get_image_metadata(file_path)
                    except Exception as e:
                        logging.warning(f"Error getting metadata for {file_path}: {e}")
                        failed += 1
                        continue
                    
                    # Copy image to appropriate category directory
                    filename = os.path.basename(file_path)
                    dest_path = os.path.join(self.image_dir, category, filename)
                    
                    # If a file with the same name exists in the destination, add a unique suffix
                    if os.path.exists(dest_path):
                        name, ext = os.path.splitext(filename)
                        dest_path = os.path.join(self.image_dir, category, f"{name}_{checksum[:8]}{ext}")
                    
                    shutil.copy2(file_path, dest_path)
                    
                    # Add to database
                    cursor.execute("""
                    INSERT INTO images (filename, path, checksum, category, width, height, 
                                       file_size, mime_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        os.path.basename(dest_path),
                        dest_path,
                        checksum,
                        category,
                        metadata.get('width', 0),
                        metadata.get('height', 0),
                        metadata.get('file_size', 0),
                        metadata.get('mime_type', ''),
                        datetime.now().isoformat()
                    ))
                    
                    self.conn.commit()
                    imported += 1
                    
                except Exception as e:
                    logging.error(f"Error importing image {file_path}: {e}")
                    failed += 1
        
        # Refresh cache
        self._refresh_cache()
            
        return {
            "total": total_files,
            "imported": imported,
            "skipped": skipped,
            "failed": failed
        }
    
    def _process_images_thread(self):
        """Background thread to process image files (calculate checksums, extract metadata, etc.)"""
        while True:
            try:
                # Get task from queue
                task = self.processing_queue.get()
                
                if task['action'] == 'process_image':
                    image_path = task['image_path']
                    category = task.get('category', self.default_category)
                    
                    try:
                        # Process the image
                        logging.debug(f"Processing image: {image_path}")
                        
                        # Calculate checksum
                        checksum = self._calculate_checksum(image_path)
                        
                        # Get image metadata
                        metadata = self._get_image_metadata(image_path)
                        
                        # Check if image already exists
                        cursor = self.conn.cursor()
                        cursor.execute("SELECT id FROM images WHERE checksum = ?", (checksum,))
                        existing = cursor.fetchone()
                        
                        if existing:
                            logging.debug(f"Image already exists with checksum: {checksum}")
                            continue
                        
                        # Copy image to appropriate category directory
                        filename = os.path.basename(image_path)
                        dest_path = os.path.join(self.image_dir, category, filename)
                        
                        # If a file with the same name exists in the destination, add a unique suffix
                        if os.path.exists(dest_path):
                            name, ext = os.path.splitext(filename)
                            dest_path = os.path.join(self.image_dir, category, f"{name}_{checksum[:8]}{ext}")
                        
                        shutil.copy2(image_path, dest_path)
                        
                        # Add to database
                        cursor.execute("""
                        INSERT INTO images (filename, path, checksum, category, width, height, 
                                          file_size, mime_type, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            os.path.basename(dest_path),
                            dest_path,
                            checksum,
                            category,
                            metadata.get('width', 0),
                            metadata.get('height', 0),
                            metadata.get('file_size', 0),
                            metadata.get('mime_type', ''),
                            datetime.now().isoformat()
                        ))
                        
                        # Add tags if provided
                        if 'tags' in task and task['tags']:
                            image_id = cursor.lastrowid
                            for tag in task['tags']:
                                cursor.execute("""
                                INSERT OR IGNORE INTO image_tags (image_id, tag)
                                VALUES (?, ?)
                                """, (image_id, tag))
                        
                        self.conn.commit()
                        logging.debug(f"Successfully processed image: {image_path}")
                        
                    except Exception as e:
                        logging.error(f"Error processing image {image_path}: {e}")
                
                # Mark task as done
                self.processing_queue.task_done()
                
            except Exception as e:
                logging.error(f"Error in image processing thread: {e}")
    
    def _calculate_checksum(self, file_path):
        """Calculate a checksum for an image file"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _get_image_metadata(self, file_path):
        """Extract metadata from an image file"""
        try:
            with Image.open(file_path) as img:
                file_size = os.path.getsize(file_path)
                return {
                    'width': img.width,
                    'height': img.height,
                    'file_size': file_size,
                    'mime_type': f"image/{img.format.lower() if img.format else 'unknown'}"
                }
        except Exception as e:
            logging.warning(f"Could not extract metadata from {file_path}: {e}")
            # Return basic metadata that doesn't require opening the image
            return {
                'width': 0,
                'height': 0,
                'file_size': os.path.getsize(file_path),
                'mime_type': 'image/unknown'
            }
    
    def _is_image_file(self, filename):
        """Check if a file is a supported image format based on extension"""
        _, ext = os.path.splitext(filename.lower())
        return ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
    
    def _refresh_cache(self):
        """Refresh the in-memory cache of image metadata"""
        with self.cache_lock:
            self.image_cache = {}
            
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT id, filename, path, category, use_count, last_used
            FROM images
            """)
            
            for row in cursor.fetchall():
                image_id, filename, path, category, use_count, last_used = row
                self.image_cache[image_id] = {
                    'id': image_id,
                    'filename': filename,
                    'path': path,
                    'category': category,
                    'use_count': use_count,
                    'last_used': last_used
                }
    
    def get_image(self, category=None, tag=None, excluded_images=None, account_id=None, contact=None):
        """
        Get an image for use in a message, prioritizing less frequently used images
        
        Args:
            category: Specific category to draw from
            tag: Specific tag to filter by
            excluded_images: List of image IDs to exclude
            account_id: Account that will use the image
            contact: Contact the message is being sent to
            
        Returns:
            Dict with image info including path
        """
        excluded_images = excluded_images or []
        
        try:
            cursor = self.conn.cursor()
            
            # Build query based on parameters
            query = """
            SELECT i.id, i.filename, i.path, i.category, i.use_count, i.last_used
            FROM images i
            """
            
            params = []
            where_clauses = []
            
            # Add tag join if needed
            if tag:
                query += """
                JOIN image_tags t ON i.id = t.image_id
                """
                where_clauses.append("t.tag = ?")
                params.append(tag)
            
            # Add category filter if provided
            if category:
                where_clauses.append("i.category = ?")
                params.append(category)
            
            # Exclude specified images
            if excluded_images:
                placeholders = ','.join(['?'] * len(excluded_images))
                where_clauses.append(f"i.id NOT IN ({placeholders})")
                params.extend(excluded_images)
            
            # If account_id is provided, exclude images recently sent by this account
            if account_id:
                # Get images used by this account in the last 3 days
                cursor.execute("""
                SELECT DISTINCT image_id FROM image_usage
                WHERE account_id = ? AND used_at > ?
                """, (account_id, (datetime.now() - timedelta(days=3)).isoformat()))
                
                recent_images = [row[0] for row in cursor.fetchall()]
                
                if recent_images:
                    placeholders = ','.join(['?'] * len(recent_images))
                    where_clauses.append(f"i.id NOT IN ({placeholders})")
                    params.extend(recent_images)
            
            # If contact is provided, exclude images sent to this contact
            if contact:
                cursor.execute("""
                SELECT DISTINCT image_id FROM image_usage
                WHERE contact = ?
                """, (contact,))
                
                contact_images = [row[0] for row in cursor.fetchall()]
                
                if contact_images:
                    placeholders = ','.join(['?'] * len(contact_images))
                    where_clauses.append(f"i.id NOT IN ({placeholders})")
                    params.extend(contact_images)
            
            # Add where clause to query
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            # Order by use count (prioritizing least used)
            query += """
            ORDER BY i.use_count ASC, RANDOM()
            LIMIT 1
            """
            
            cursor.execute(query, params)
            row = cursor.fetchone()
            
            if not row:
                # If no image found with the specific criteria, try without filters
                logging.warning(f"No image found with criteria - category:{category}, tag:{tag}")
                cursor.execute("""
                SELECT id, filename, path, category, use_count, last_used
                FROM images
                ORDER BY use_count ASC, RANDOM()
                LIMIT 1
                """)
                row = cursor.fetchone()
            
            if not row:
                # Still no images found
                logging.error("No images available in the database")
                return None
            
            image_id, filename, path, image_category, use_count, last_used = row
            
            # Update usage statistics
            cursor.execute("""
            UPDATE images
            SET use_count = use_count + 1, last_used = ?
            WHERE id = ?
            """, (datetime.now().isoformat(), image_id))
            
            # Record usage if account_id is provided
            if account_id:
                cursor.execute("""
                INSERT INTO image_usage (image_id, account_id, contact, used_at)
                VALUES (?, ?, ?, ?)
                """, (image_id, account_id, contact or "", datetime.now().isoformat()))
            
            self.conn.commit()
            
            # Update cache
            with self.cache_lock:
                if image_id in self.image_cache:
                    self.image_cache[image_id]['use_count'] += 1
                    self.image_cache[image_id]['last_used'] = datetime.now().isoformat()
            
            # Return image info
            return {
                'id': image_id,
                'filename': filename,
                'path': path,
                'category': image_category,
                'use_count': use_count + 1  # Include the just-recorded use
            }
            
        except Exception as e:
            logging.error(f"Error selecting image: {e}")
            return None
    
    def add_tag(self, image_id, tag):
        """Add a tag to an image"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT OR IGNORE INTO image_tags (image_id, tag)
            VALUES (?, ?)
            """, (image_id, tag))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error adding tag to image {image_id}: {e}")
            return False
    
    def remove_tag(self, image_id, tag):
        """Remove a tag from an image"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            DELETE FROM image_tags
            WHERE image_id = ? AND tag = ?
            """, (image_id, tag))
            self.conn.commit()
            return True
        except Exception as e:
            logging.error(f"Error removing tag from image {image_id}: {e}")
            return False
    
    def get_tags(self, image_id):
        """Get all tags for an image"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT tag FROM image_tags
            WHERE image_id = ?
            """, (image_id,))
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting tags for image {image_id}: {e}")
            return []
    
    def get_all_tags(self):
        """Get all unique tags in the system"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT DISTINCT tag FROM image_tags
            ORDER BY tag
            """)
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logging.error(f"Error getting all tags: {e}")
            return []
    
    def change_category(self, image_id, new_category):
        """
        Change the category of an image
        
        This will move the file to the new category directory
        """
        try:
            # Ensure the category exists
            if new_category not in self.categories:
                logging.error(f"Category {new_category} does not exist")
                return False
            
            # Get current image info
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT filename, path, category
            FROM images
            WHERE id = ?
            """, (image_id,))
            
            row = cursor.fetchone()
            if not row:
                logging.error(f"Image {image_id} not found")
                return False
            
            filename, old_path, old_category = row
            
            # Build new path
            new_path = os.path.join(self.image_dir, new_category, filename)
            
            # If a file with the same name exists in the destination, add a unique suffix
            if os.path.exists(new_path):
                name, ext = os.path.splitext(filename)
                new_path = os.path.join(self.image_dir, new_category, f"{name}_{image_id}{ext}")
                filename = os.path.basename(new_path)
            
            # Move the file
            shutil.move(old_path, new_path)
            
            # Update database
            cursor.execute("""
            UPDATE images
            SET path = ?, category = ?, filename = ?
            WHERE id = ?
            """, (new_path, new_category, filename, image_id))
            
            self.conn.commit()
            
            # Update cache
            with self.cache_lock:
                if image_id in self.image_cache:
                    self.image_cache[image_id]['path'] = new_path
                    self.image_cache[image_id]['category'] = new_category
                    self.image_cache[image_id]['filename'] = filename
            
            return True
            
        except Exception as e:
            logging.error(f"Error changing category for image {image_id}: {e}")
            return False
    
    def delete_image(self, image_id):
        """Delete an image from the system"""
        try:
            # Get image path
            cursor = self.conn.cursor()
            cursor.execute("SELECT path FROM images WHERE id = ?", (image_id,))
            row = cursor.fetchone()
            
            if not row:
                logging.error(f"Image {image_id} not found")
                return False
            
            path = row[0]
            
            # Delete file
            if os.path.exists(path):
                os.remove(path)
            
            # Delete from database (cascade will delete tags and usage)
            cursor.execute("DELETE FROM image_tags WHERE image_id = ?", (image_id,))
            cursor.execute("DELETE FROM image_usage WHERE image_id = ?", (image_id,))
            cursor.execute("DELETE FROM images WHERE id = ?", (image_id,))
            
            self.conn.commit()
            
            # Remove from cache
            with self.cache_lock:
                if image_id in self.image_cache:
                    del self.image_cache[image_id]
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting image {image_id}: {e}")
            return False
    
    def get_image_info(self, image_id):
        """Get detailed information about an image"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT id, filename, path, checksum, category, width, height, 
                   file_size, mime_type, created_at, last_used, use_count
            FROM images
            WHERE id = ?
            """, (image_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Get tags
            tags = self.get_tags(image_id)
            
            # Get recent usage
            cursor.execute("""
            SELECT account_id, contact, used_at
            FROM image_usage
            WHERE image_id = ?
            ORDER BY used_at DESC
            LIMIT 10
            """, (image_id,))
            
            recent_usage = []
            for usage_row in cursor.fetchall():
                account_id, contact, used_at = usage_row
                recent_usage.append({
                    'account_id': account_id,
                    'contact': contact,
                    'used_at': used_at
                })
            
            # Build result
            id, filename, path, checksum, category, width, height, file_size, mime_type, created_at, last_used, use_count = row
            
            return {
                'id': id,
                'filename': filename,
                'path': path,
                'checksum': checksum,
                'category': category,
                'width': width,
                'height': height,
                'file_size': file_size,
                'mime_type': mime_type,
                'created_at': created_at,
                'last_used': last_used,
                'use_count': use_count,
                'tags': tags,
                'recent_usage': recent_usage
            }
            
        except Exception as e:
            logging.error(f"Error getting image info for {image_id}: {e}")
            return None
    
    def search_images(self, query=None, category=None, tag=None, min_width=None, min_height=None, 
                     max_use_count=None, unused_only=False, limit=100, offset=0):
        """
        Search for images based on various criteria
        
        Args:
            query: Text to search in filename (contains match)
            category: Category to filter by (exact match)
            tag: Tag to filter by (exact match)
            min_width: Minimum width in pixels
            min_height: Minimum height in pixels
            max_use_count: Maximum number of times the image has been used
            unused_only: If True, only return images that haven't been used
            limit: Maximum number of results to return
            offset: Number of results to skip (for pagination)
            
        Returns:
            List of matching image records
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            sql = """
            SELECT i.id, i.filename, i.path, i.category, i.width, i.height, 
                   i.created_at, i.last_used, i.use_count
            FROM images i
            """
            
            params = []
            where_clauses = []
            
            # Add tag join if needed
            if tag:
                sql += """
                JOIN image_tags t ON i.id = t.image_id
                """
                where_clauses.append("t.tag = ?")
                params.append(tag)
            
            # Add other filters
            if query:
                where_clauses.append("i.filename LIKE ?")
                params.append(f"%{query}%")
            
            if category:
                where_clauses.append("i.category = ?")
                params.append(category)
            
            if min_width:
                where_clauses.append("i.width >= ?")
                params.append(min_width)
            
            if min_height:
                where_clauses.append("i.height >= ?")
                params.append(min_height)
            
            if max_use_count is not None:
                where_clauses.append("i.use_count <= ?")
                params.append(max_use_count)
            
            if unused_only:
                where_clauses.append("i.use_count = 0")
            
            # Add where clause if any filters were specified
            if where_clauses:
                sql += " WHERE " + " AND ".join(where_clauses)
            
            # Add order and limit
            sql += """
            ORDER BY i.created_at DESC
            LIMIT ? OFFSET ?
            """
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(sql, params)
            
            # Build results
            results = []
            for row in cursor.fetchall():
                id, filename, path, img_category, width, height, created_at, last_used, use_count = row
                
                # Get tags for this image
                cursor.execute("""
                SELECT tag FROM image_tags
                WHERE image_id = ?
                """, (id,))
                
                tags = [tag_row[0] for tag_row in cursor.fetchall()]
                
                results.append({
                    'id': id,
                    'filename': filename,
                    'path': path,
                    'category': img_category,
                    'width': width,
                    'height': height,
                    'created_at': created_at,
                    'last_used': last_used,
                    'use_count': use_count,
                    'tags': tags
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error searching images: {e}")
            return []
    
    def get_image_counts(self):
        """Get image counts by category and usage statistics"""
        try:
            cursor = self.conn.cursor()
            
            # Get counts by category
            cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM images
            GROUP BY category
            """)
            
            categories = {}
            for category, count in cursor.fetchall():
                categories[category] = count
            
            # Get total image count
            cursor.execute("SELECT COUNT(*) FROM images")
            total_images = cursor.fetchone()[0]
            
            # Get unused image count
            cursor.execute("SELECT COUNT(*) FROM images WHERE use_count = 0")
            unused_images = cursor.fetchone()[0]
            
            # Get frequently used image count (used more than 5 times)
            cursor.execute("SELECT COUNT(*) FROM images WHERE use_count > 5")
            frequent_images = cursor.fetchone()[0]
            
            # Get total usage count
            cursor.execute("SELECT SUM(use_count) FROM images")
            total_usage = cursor.fetchone()[0] or 0
            
            return {
                'total_images': total_images,
                'unused_images': unused_images,
                'frequent_images': frequent_images,
                'total_usage': total_usage,
                'categories': categories
            }
            
        except Exception as e:
            logging.error(f"Error getting image counts: {e}")
            return {
                'total_images': 0,
                'unused_images': 0,
                'frequent_images': 0,
                'total_usage': 0,
                'categories': {}
            }
    
    def bulk_change_category(self, image_ids, new_category):
        """Change the category of multiple images"""
        success_count = 0
        failed_count = 0
        
        for image_id in image_ids:
            result = self.change_category(image_id, new_category)
            if result:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count
        }
    
    def bulk_add_tag(self, image_ids, tag):
        """Add a tag to multiple images"""
        success_count = 0
        failed_count = 0
        
        for image_id in image_ids:
            result = self.add_tag(image_id, tag)
            if result:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count
        }
    
    def bulk_delete(self, image_ids):
        """Delete multiple images"""
        success_count = 0
        failed_count = 0
        
        for image_id in image_ids:
            result = self.delete_image(image_id)
            if result:
                success_count += 1
            else:
                failed_count += 1
        
        return {
            'success_count': success_count,
            'failed_count': failed_count
        }
    
    def get_images_for_campaign(self, count, category=None, tag=None, min_width=None, min_height=None):
        """
        Get a list of images suitable for a campaign, with minimal overlap in usage
        
        This is useful for pre-selecting a batch of images for a campaign
        """
        try:
            # First, search for images matching the criteria with minimal usage
            images = self.search_images(
                category=category,
                tag=tag,
                min_width=min_width,
                min_height=min_height,
                limit=count * 3  # Get more than needed to allow for filtering
            )
            
            # Sort by use_count to prioritize least used
            images.sort(key=lambda img: img['use_count'])
            
            # Take the top 'count' images
            selected_images = images[:count]
            
            # If we don't have enough images, broaden the search
            if len(selected_images) < count:
                logging.warning(f"Not enough images found with specified criteria. Found {len(selected_images)}, needed {count}")
                
                # Try without category constraint
                if category:
                    additional_images = self.search_images(
                        tag=tag,
                        min_width=min_width,
                        min_height=min_height,
                        limit=count * 3
                    )
                    
                    # Filter out images we already have
                    selected_ids = [img['id'] for img in selected_images]
                    additional_images = [img for img in additional_images if img['id'] not in selected_ids]
                    
                    # Sort by use_count
                    additional_images.sort(key=lambda img: img['use_count'])
                    
                    # Add as many as needed
                    needed = count - len(selected_images)
                    selected_images.extend(additional_images[:needed])
            
            return selected_images
            
        except Exception as e:
            logging.error(f"Error getting images for campaign: {e}")
            return []
    
    def check_image_health(self):
        """
        Check for potential issues in the image database
        
        Identifies:
        - Missing files
        - Corrupt images
        - Overused images
        """
        issues = {
            'missing': [],
            'corrupt': [],
            'overused': []
        }
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT id, filename, path, use_count
            FROM images
            """)
            
            for row in cursor.fetchall():
                image_id, filename, path, use_count = row
                
                # Check if file exists
                if not os.path.exists(path):
                    issues['missing'].append({
                        'id': image_id,
                        'filename': filename,
                        'path': path
                    })
                    continue
                
                # Check if image is corrupt
                try:
                    with Image.open(path) as img:
                        # Try to load the image
                        img.verify()
                except Exception:
                    issues['corrupt'].append({
                        'id': image_id,
                        'filename': filename,
                        'path': path
                    })
                
                # Check if image is overused
                if use_count > 20:  # Threshold for "overused"
                    issues['overused'].append({
                        'id': image_id,
                        'filename': filename,
                        'path': path,
                        'use_count': use_count
                    })
            
            return issues
            
        except Exception as e:
            logging.error(f"Error checking image health: {e}")
            return issues
    
    def get_recent_usage(self, image_id=None, limit=100):
        """Get recent image usage"""
        try:
            cursor = self.conn.cursor()
            
            if image_id:
                # Get usage for a specific image
                cursor.execute("""
                SELECT u.id, u.image_id, u.account_id, u.contact, u.used_at, u.campaign_id,
                       i.filename, i.category
                FROM image_usage u
                JOIN images i ON u.image_id = i.id
                WHERE u.image_id = ?
                ORDER BY u.used_at DESC
                LIMIT ?
                """, (image_id, limit))
            else:
                # Get overall recent usage
                cursor.execute("""
                SELECT u.id, u.image_id, u.account_id, u.contact, u.used_at, u.campaign_id,
                       i.filename, i.category
                FROM image_usage u
                JOIN images i ON u.image_id = i.id
                ORDER BY u.used_at DESC
                LIMIT ?
                """, (limit,))
            
            results = []
            for row in cursor.fetchall():
                usage_id, img_id, account_id, contact, used_at, campaign_id, filename, category = row
                
                results.append({
                    'id': usage_id,
                    'image_id': img_id,
                    'account_id': account_id,
                    'contact': contact,
                    'used_at': used_at,
                    'campaign_id': campaign_id,
                    'filename': filename,
                    'category': category
                })
            
            return results
            
        except Exception as e:
            logging.error(f"Error getting recent usage: {e}")
            return []
    
    def close(self):
        """Close the database connection"""
        if hasattr(self, 'conn') and self.conn:
            self.conn.close()


# Singleton instance
_image_manager = None

def get_image_manager():
    """Get the singleton ImageManager instance"""
    global _image_manager
    if _image_manager is None:
        _image_manager = ImageManager()
    return _image_manager