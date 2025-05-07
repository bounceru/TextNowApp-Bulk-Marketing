"""
Data Importer for ProgressGhostCreator

This module handles importing data files for the application, including:
- Names and usernames from CSV files
- Voicemail files
- Image files for profiles
- Message templates
- Message databases from CSV files

It provides a GUI interface for selecting and previewing files.
"""

import os
import sys
import csv
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from pathlib import Path


class DataImporterWindow:
    def __init__(self, parent, import_type="names"):
        """Initialize the importer window"""
        self.parent = parent
        self.import_type = import_type
        
        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title(f"Import {import_type.capitalize()} Data")
        self.window.geometry("800x600")
        self.window.transient(parent)
        self.window.grab_set()
        
        # Set icon if available
        if os.path.exists("assets/app_icon.ico"):
            self.window.iconbitmap("assets/app_icon.ico")
        
        # Frame for file selection
        file_frame = ttk.LabelFrame(self.window, text="Select File")
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # File path entry and browse button
        file_select_frame = ttk.Frame(file_frame)
        file_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(file_select_frame, text="File Path:").pack(side=tk.LEFT, padx=(0, 5))
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_select_frame, textvariable=self.file_path_var, width=60).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_select_frame, text="Browse...", command=self.browse_file).pack(side=tk.LEFT)
        
        # Additional options based on import type
        self.setup_import_options()
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.window, text="Preview")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Preview contents
        self.preview_widget = self.create_preview_widget(preview_frame)
        
        # Buttons frame
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(buttons_frame, text="Import", command=self.import_data).pack(side=tk.RIGHT, padx=5)
        ttk.Button(buttons_frame, text="Cancel", command=self.window.destroy).pack(side=tk.RIGHT, padx=5)
        
        # Result variables
        self.import_success = False
        self.imported_data = None
    
    def setup_import_options(self):
        """Setup import options based on import type"""
        if self.import_type == "names":
            options_frame = ttk.LabelFrame(self.window, text="Import Options")
            options_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # CSV format settings
            format_frame = ttk.Frame(options_frame)
            format_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(format_frame, text="Column Mapping:").grid(row=0, column=0, sticky=tk.W)
            
            # First name column
            ttk.Label(format_frame, text="First Name:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.first_name_col_var = tk.StringVar(value="first_name")
            ttk.Entry(format_frame, textvariable=self.first_name_col_var, width=15).grid(row=1, column=1, padx=5, pady=2)
            
            # Last name column
            ttk.Label(format_frame, text="Last Name:").grid(row=2, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.last_name_col_var = tk.StringVar(value="last_name")
            ttk.Entry(format_frame, textvariable=self.last_name_col_var, width=15).grid(row=2, column=1, padx=5, pady=2)
            
            # Username column
            ttk.Label(format_frame, text="Username:").grid(row=3, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.username_col_var = tk.StringVar(value="username")
            ttk.Entry(format_frame, textvariable=self.username_col_var, width=15).grid(row=3, column=1, padx=5, pady=2)
            
            # Email column
            ttk.Label(format_frame, text="Email:").grid(row=4, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.email_col_var = tk.StringVar(value="email")
            ttk.Entry(format_frame, textvariable=self.email_col_var, width=15).grid(row=4, column=1, padx=5, pady=2)
            
            # Has header checkbox
            self.has_header_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(format_frame, text="File has header row", variable=self.has_header_var).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=5)
            
            # Generate missing checkboxes
            ttk.Label(format_frame, text="Generate Missing:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
            
            self.gen_usernames_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(format_frame, text="Usernames", variable=self.gen_usernames_var).grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
            
            self.gen_emails_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(format_frame, text="Emails", variable=self.gen_emails_var).grid(row=2, column=2, sticky=tk.W, padx=(20, 5))
        
        elif self.import_type == "voicemail":
            options_frame = ttk.LabelFrame(self.window, text="Import Options")
            options_frame.pack(fill=tk.X, padx=10, pady=10)
            
            copy_frame = ttk.Frame(options_frame)
            copy_frame.pack(fill=tk.X, padx=5, pady=5)
            
            self.copy_files_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(copy_frame, text="Copy files to application voicemail folder", variable=self.copy_files_var).pack(anchor=tk.W)
            
            self.rename_files_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(copy_frame, text="Rename files sequentially (voicemail_001.mp3, etc.)", variable=self.rename_files_var).pack(anchor=tk.W)
            
        elif self.import_type == "messages":
            options_frame = ttk.LabelFrame(self.window, text="Message Database Import Options")
            options_frame.pack(fill=tk.X, padx=10, pady=10)
            
            # File format options
            format_frame = ttk.Frame(options_frame)
            format_frame.pack(fill=tk.X, padx=5, pady=5)
            
            ttk.Label(format_frame, text="Column Mapping:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
            
            # Message text column
            ttk.Label(format_frame, text="Message Text:").grid(row=1, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.message_text_col_var = tk.StringVar(value="message")
            ttk.Entry(format_frame, textvariable=self.message_text_col_var, width=15).grid(row=1, column=1, padx=5, pady=2)
            
            # Category column (optional)
            ttk.Label(format_frame, text="Category (optional):").grid(row=2, column=0, sticky=tk.W, padx=(20, 5), pady=2)
            self.category_col_var = tk.StringVar(value="category")
            ttk.Entry(format_frame, textvariable=self.category_col_var, width=15).grid(row=2, column=1, padx=5, pady=2)
            
            # Has header checkbox
            self.has_header_var = tk.BooleanVar(value=True)
            ttk.Checkbutton(format_frame, text="File has header row", variable=self.has_header_var).grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
            
            # Categorization options
            ttk.Label(format_frame, text="Categorization:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
            
            self.auto_categorize_var = tk.BooleanVar(value=False)
            ttk.Checkbutton(format_frame, text="Auto-categorize messages", variable=self.auto_categorize_var, command=self.toggle_categorization).grid(row=1, column=2, sticky=tk.W, padx=(20, 5))
            
            # Database storage options
            storage_frame = ttk.Frame(options_frame)
            storage_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # File size warning
            ttk.Label(storage_frame, text="Note: Large message databases (50,000+ messages) may take several minutes to import.", 
                      font=("Arial", 9, "italic")).pack(anchor=tk.W, pady=(0, 5))
            
            # Batch size
            batch_size_frame = ttk.Frame(storage_frame)
            batch_size_frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(batch_size_frame, text="Import Batch Size:").pack(side=tk.LEFT, padx=(0, 5))
            self.batch_size_var = tk.StringVar(value="10000")
            ttk.Entry(batch_size_frame, textvariable=self.batch_size_var, width=10).pack(side=tk.LEFT)
            ttk.Label(batch_size_frame, text="(larger values use more memory)").pack(side=tk.LEFT, padx=(5, 0))
            
            # Auto-categorization frame (hidden by default)
            self.categorization_frame = ttk.LabelFrame(options_frame, text="Auto-Categorization Settings")
            
            category_settings_frame = ttk.Frame(self.categorization_frame)
            category_settings_frame.pack(fill=tk.X, padx=5, pady=5)
            
            # Default categories
            ttk.Label(category_settings_frame, text="Default Categories:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
            
            self.categories = [
                ("intro", "Introduction Messages"),
                ("promo", "Promotional Offers"),
                ("followup", "Follow-up Messages"),
                ("reminder", "Reminder Messages"),
                ("response", "Response Messages")
            ]
            
            self.category_vars = {}
            for i, (code, name) in enumerate(self.categories):
                var = tk.BooleanVar(value=True)
                self.category_vars[code] = var
                ttk.Checkbutton(category_settings_frame, text=name, variable=var).grid(row=i+1, column=0, sticky=tk.W, padx=(20, 5))
            
            # Custom category
            custom_frame = ttk.Frame(category_settings_frame)
            custom_frame.grid(row=len(self.categories)+1, column=0, sticky=tk.W, padx=(20, 5), pady=(5, 0))
            
            ttk.Label(custom_frame, text="Add Custom Category:").pack(side=tk.LEFT, padx=(0, 5))
            self.custom_category_var = tk.StringVar()
            ttk.Entry(custom_frame, textvariable=self.custom_category_var, width=15).pack(side=tk.LEFT, padx=(0, 5))
            ttk.Button(custom_frame, text="Add", command=self.add_custom_category).pack(side=tk.LEFT)
            
            # If auto-categorize is enabled, show categorization frame
            if self.auto_categorize_var.get():
                self.categorization_frame.pack(fill=tk.X, padx=10, pady=5)
    
    def create_preview_widget(self, parent):
        """Create the appropriate preview widget based on import type"""
        if self.import_type == "names":
            # Create a treeview for CSV preview
            columns = ("first_name", "last_name", "username", "email")
            preview = ttk.Treeview(parent, columns=columns, show="headings")
            
            # Set column headings
            preview.heading("first_name", text="First Name")
            preview.heading("last_name", text="Last Name")
            preview.heading("username", text="Username")
            preview.heading("email", text="Email")
            
            # Set column widths
            preview.column("first_name", width=150)
            preview.column("last_name", width=150)
            preview.column("username", width=200)
            preview.column("email", width=250)
            
            # Add scrollbars
            scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=preview.yview)
            scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=preview.xview)
            preview.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
            
            # Layout
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            preview.pack(fill=tk.BOTH, expand=True)
            
            return preview
        
        elif self.import_type == "voicemail":
            # Create a listbox for voicemail files preview
            frame = ttk.Frame(parent)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Add a listbox with scrollbar
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set)
            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            scrollbar.config(command=listbox.yview)
            
            # Add play button for selected file
            play_frame = ttk.Frame(parent)
            play_frame.pack(fill=tk.X, pady=5)
            
            ttk.Button(play_frame, text="Play Selected", command=self.play_selected_audio).pack(side=tk.LEFT)
            
            return listbox
            
        elif self.import_type == "messages":
            # Create a treeview for messages preview
            columns = ("message", "category", "length")
            preview = ttk.Treeview(parent, columns=columns, show="headings")
            
            # Set column headings
            preview.heading("message", text="Message Text")
            preview.heading("category", text="Category")
            preview.heading("length", text="Length")
            
            # Set column widths
            preview.column("message", width=500)
            preview.column("category", width=150)
            preview.column("length", width=80)
            
            # Add scrollbars
            scrollbar_y = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=preview.yview)
            scrollbar_x = ttk.Scrollbar(parent, orient=tk.HORIZONTAL, command=preview.xview)
            preview.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
            
            # Layout
            scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
            scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
            preview.pack(fill=tk.BOTH, expand=True)
            
            # Add stats frame
            stats_frame = ttk.Frame(parent)
            stats_frame.pack(fill=tk.X, pady=5)
            
            self.total_messages_var = tk.StringVar(value="Total Messages: 0")
            self.avg_length_var = tk.StringVar(value="Average Length: 0 chars")
            self.category_count_var = tk.StringVar(value="Categories: 0")
            
            ttk.Label(stats_frame, textvariable=self.total_messages_var).pack(side=tk.LEFT, padx=(0, 15))
            ttk.Label(stats_frame, textvariable=self.avg_length_var).pack(side=tk.LEFT, padx=(0, 15))
            ttk.Label(stats_frame, textvariable=self.category_count_var).pack(side=tk.LEFT)
            
            return preview
    
    def browse_file(self):
        """Open file browser to select import file"""
        if self.import_type == "names":
            filetypes = [("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            title = "Select Names Data File"
            mode = "file"
        elif self.import_type == "voicemail":
            filetypes = [
                ("Audio Files", "*.mp3 *.wav *.ogg *.m4a"), 
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("All Files", "*.*")
            ]
            title = "Select Voicemail Files"
            mode = "files"
        elif self.import_type == "messages":
            filetypes = [("CSV Files", "*.csv"), ("Text Files", "*.txt"), ("All Files", "*.*")]
            title = "Select Messages Database File"
            mode = "file"
        
        if mode == "file":
            filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
            if filepath:
                self.file_path_var.set(filepath)
                self.load_preview()
        elif mode == "files":
            filepaths = filedialog.askopenfilenames(title=title, filetypes=filetypes)
            if filepaths:
                self.file_path_var.set(";".join(filepaths))  # Join multiple files with semicolon
                self.load_preview()
    
    def load_preview(self):
        """Load a preview of the selected file"""
        filepath = self.file_path_var.get()
        if not filepath:
            return
        
        if self.import_type == "names":
            try:
                # Clear existing items
                for item in self.preview_widget.get_children():
                    self.preview_widget.delete(item)
                
                # Read CSV file
                if self.has_header_var.get():
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_csv(filepath, header=None)
                    # Assign default column names
                    df.columns = [f"Column {i+1}" for i in range(len(df.columns))]
                
                # Map columns
                first_name_col = self.first_name_col_var.get()
                last_name_col = self.last_name_col_var.get()
                username_col = self.username_col_var.get()
                email_col = self.email_col_var.get()
                
                # Get actual column names or indices
                columns = list(df.columns)
                
                # Try to find the specified columns
                try:
                    first_name_idx = columns.index(first_name_col) if first_name_col in columns else 0
                    last_name_idx = columns.index(last_name_col) if last_name_col in columns else 1
                    username_idx = columns.index(username_col) if username_col in columns else 2
                    email_idx = columns.index(email_col) if email_col in columns else 3
                except:
                    # Default to column indices
                    first_name_idx = 0 if len(columns) > 0 else None
                    last_name_idx = 1 if len(columns) > 1 else None
                    username_idx = 2 if len(columns) > 2 else None
                    email_idx = 3 if len(columns) > 3 else None
                
                # Update column variables to match actual columns
                if first_name_idx is not None:
                    self.first_name_col_var.set(columns[first_name_idx])
                if last_name_idx is not None:
                    self.last_name_col_var.set(columns[last_name_idx])
                if username_idx is not None:
                    self.username_col_var.set(columns[username_idx])
                if email_idx is not None:
                    self.email_col_var.set(columns[email_idx])
                
                # Populate preview (up to 100 rows)
                for i, row in df.head(100).iterrows():
                    values = [
                        row[columns[first_name_idx]] if first_name_idx is not None and first_name_idx < len(columns) else "",
                        row[columns[last_name_idx]] if last_name_idx is not None and last_name_idx < len(columns) else "",
                        row[columns[username_idx]] if username_idx is not None and username_idx < len(columns) else "",
                        row[columns[email_idx]] if email_idx is not None and email_idx < len(columns) else ""
                    ]
                    self.preview_widget.insert("", tk.END, values=values)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {str(e)}")
                return
        
        elif self.import_type == "voicemail":
            # Clear existing items
            self.preview_widget.delete(0, tk.END)
            
            # Get list of files
            filepaths = filepath.split(";")
            for path in filepaths:
                if os.path.isfile(path):
                    filename = os.path.basename(path)
                    file_size = os.path.getsize(path) / 1024  # Size in KB
                    self.preview_widget.insert(tk.END, f"{filename} ({file_size:.1f} KB)")
                    
        elif self.import_type == "messages":
            try:
                # Clear existing items
                for item in self.preview_widget.get_children():
                    self.preview_widget.delete(item)
                
                # Read CSV file with message data
                if self.has_header_var.get():
                    df = pd.read_csv(filepath)
                else:
                    df = pd.read_csv(filepath, header=None)
                    # Assign default column names
                    df.columns = [f"Column {i+1}" for i in range(len(df.columns))]
                
                # Map columns
                message_col = self.message_text_col_var.get()
                category_col = self.category_col_var.get()
                
                # Get actual column names or indices
                columns = list(df.columns)
                
                # Try to find the specified columns
                try:
                    message_idx = columns.index(message_col) if message_col in columns else 0
                    category_idx = columns.index(category_col) if category_col in columns and self.auto_categorize_var.get() else None
                except:
                    # Default to column indices
                    message_idx = 0 if len(columns) > 0 else None
                    category_idx = 1 if len(columns) > 1 and self.auto_categorize_var.get() else None
                
                # Update column variables to match actual columns
                if message_idx is not None:
                    self.message_text_col_var.set(columns[message_idx])
                if category_idx is not None:
                    self.category_col_var.set(columns[category_idx])
                
                # Analyze the data
                total_messages = len(df)
                
                # Calculate average message length
                if message_idx is not None:
                    message_lengths = df.iloc[:, message_idx].astype(str).str.len()
                    avg_length = message_lengths.mean()
                else:
                    avg_length = 0
                
                # Count categories if available
                categories = set()
                if category_idx is not None:
                    categories = set(df.iloc[:, category_idx].dropna().unique())
                
                # Update stats
                self.total_messages_var.set(f"Total Messages: {total_messages}")
                self.avg_length_var.set(f"Average Length: {avg_length:.1f} chars")
                self.category_count_var.set(f"Categories: {len(categories)}")
                
                # Populate preview (up to 100 rows)
                for i, row in df.head(100).iterrows():
                    message = str(row[columns[message_idx]]) if message_idx is not None else ""
                    category = str(row[columns[category_idx]]) if category_idx is not None and category_idx < len(columns) else ""
                    length = len(message)
                    
                    # Truncate long messages for display
                    if len(message) > 100:
                        message = message[:97] + "..."
                    
                    values = [message, category, length]
                    self.preview_widget.insert("", tk.END, values=values)
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load messages file: {str(e)}")
                return
    
    def play_selected_audio(self):
        """Play the selected audio file"""
        selected = self.preview_widget.curselection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a voicemail file to play")
            return
        
        # Get the selected file path
        filepaths = self.file_path_var.get().split(";")
        if selected[0] < len(filepaths):
            file_path = filepaths[selected[0]]
            
            # Play the audio file
            try:
                import pygame
                pygame.mixer.init()
                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to play audio file: {str(e)}")
    
    def import_data(self):
        """Import the selected data"""
        filepath = self.file_path_var.get()
        if not filepath:
            messagebox.showwarning("No File", "Please select a file to import")
            return
        
        try:
            if self.import_type == "names":
                # Import names data
                result = self.import_names_data(filepath)
                if result:
                    messagebox.showinfo("Success", f"Successfully imported names data from {os.path.basename(filepath)}")
                    self.import_success = True
                    self.window.destroy()
            
            elif self.import_type == "voicemail":
                # Import voicemail files
                result = self.import_voicemail_files(filepath.split(";"))
                if result:
                    messagebox.showinfo("Success", f"Successfully imported {len(filepath.split(';'))} voicemail files")
                    self.import_success = True
                    self.window.destroy()
            
            elif self.import_type == "messages":
                # Import message database
                result = self.import_messages_data(filepath)
                if result:
                    messagebox.showinfo("Success", f"Successfully imported {result} messages from {os.path.basename(filepath)}")
                    self.import_success = True
                    self.window.destroy()
        
        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import data: {str(e)}")
    
    def import_names_data(self, filepath):
        """Import names data from CSV file"""
        try:
            # Read CSV file
            if self.has_header_var.get():
                df = pd.read_csv(filepath)
            else:
                df = pd.read_csv(filepath, header=None)
                # Assign default column names
                df.columns = [f"Column {i+1}" for i in range(len(df.columns))]
            
            # Map columns
            first_name_col = self.first_name_col_var.get()
            last_name_col = self.last_name_col_var.get()
            username_col = self.username_col_var.get()
            email_col = self.email_col_var.get()
            
            # Get actual column names or indices
            columns = list(df.columns)
            
            # Try to find the specified columns
            try:
                first_name_idx = columns.index(first_name_col) if first_name_col in columns else 0
                last_name_idx = columns.index(last_name_col) if last_name_col in columns else 1
                username_idx = columns.index(username_col) if username_col in columns else 2
                email_idx = columns.index(email_col) if email_col in columns else 3
            except:
                # Default to column indices
                first_name_idx = 0 if len(columns) > 0 else None
                last_name_idx = 1 if len(columns) > 1 else None
                username_idx = 2 if len(columns) > 2 else None
                email_idx = 3 if len(columns) > 3 else None
            
            # Prepare data for saving
            data = []
            for i, row in df.iterrows():
                first_name = str(row[columns[first_name_idx]]) if first_name_idx is not None and first_name_idx < len(columns) else ""
                last_name = str(row[columns[last_name_idx]]) if last_name_idx is not None and last_name_idx < len(columns) else ""
                username = str(row[columns[username_idx]]) if username_idx is not None and username_idx < len(columns) else ""
                email = str(row[columns[email_idx]]) if email_idx is not None and email_idx < len(columns) else ""
                
                # Generate missing usernames if needed
                if self.gen_usernames_var.get() and not username and first_name:
                    import random
                    suffixes = ["", str(random.randint(1, 999)), "_" + str(random.randint(1, 99))]
                    username = (first_name.lower() + random.choice(suffixes)).replace(" ", "_")
                    if last_name:
                        username += last_name[0].lower()
                
                # Generate missing emails if needed
                if self.gen_emails_var.get() and not email and first_name:
                    import random
                    domains = ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "mail.com"]
                    email_username = username if username else first_name.lower().replace(" ", "") + last_name[0].lower() if last_name else ""
                    email = f"{email_username}{random.randint(1, 999)}@{random.choice(domains)}"
                
                data.append([first_name, last_name, username, email])
            
            # Save to ghost_names_usernames.csv
            output_file = "ghost_names_usernames.csv"
            with open(output_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["first_name", "last_name", "username", "email"])
                writer.writerows(data)
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to import names data: {str(e)}")
    
    def import_voicemail_files(self, filepaths):
        """Import voicemail audio files"""
        try:
            # Make sure voicemail directory exists
            voicemail_dir = "voicemail"
            os.makedirs(voicemail_dir, exist_ok=True)
            
            # Copy files to voicemail directory if selected
            if self.copy_files_var.get():
                for i, path in enumerate(filepaths):
                    if not os.path.isfile(path):
                        continue
                    
                    filename = os.path.basename(path)
                    if self.rename_files_var.get():
                        base, ext = os.path.splitext(filename)
                        filename = f"voicemail_{i+1:03d}{ext}"
                    
                    dest_path = os.path.join(voicemail_dir, filename)
                    shutil.copy2(path, dest_path)
            
            return True
        
        except Exception as e:
            raise Exception(f"Failed to import voicemail files: {str(e)}")
    
    def import_messages_data(self, filepath):
        """Import message database from CSV file"""
        try:
            # Read CSV file
            if self.has_header_var.get():
                df = pd.read_csv(filepath)
            else:
                df = pd.read_csv(filepath, header=None)
                # Assign default column names
                df.columns = [f"Column {i+1}" for i in range(len(df.columns))]
            
            # Map columns
            message_col = self.message_text_col_var.get()
            category_col = self.category_col_var.get()
            
            # Get actual column names or indices
            columns = list(df.columns)
            
            # Try to find the specified columns
            try:
                message_idx = columns.index(message_col) if message_col in columns else 0
                category_idx = columns.index(category_col) if category_col in columns and self.auto_categorize_var.get() else None
            except:
                # Default to column indices
                message_idx = 0 if len(columns) > 0 else None
                category_idx = 1 if len(columns) > 1 and self.auto_categorize_var.get() else None
            
            # Prepare data for saving to database
            # Use SQLite for efficient storage of large message databases
            import sqlite3
            
            # Create or connect to messages database
            db_path = "message_templates.db"
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create messages table if it doesn't exist
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS message_templates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                category TEXT,
                length INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create categories table if using categories
            if self.auto_categorize_var.get():
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    description TEXT
                )
                ''')
                
                # Insert default categories
                for code, name in self.categories:
                    if self.category_vars.get(code, tk.BooleanVar(value=False)).get():
                        try:
                            cursor.execute('INSERT OR IGNORE INTO message_categories (name, description) VALUES (?, ?)',
                                          (code, name))
                        except:
                            pass
            
            # Start a transaction for better performance
            conn.execute('BEGIN TRANSACTION')
            
            # Get the batch size
            try:
                batch_size = int(self.batch_size_var.get())
                if batch_size <= 0:
                    batch_size = 10000
            except:
                batch_size = 10000
            
            # Import messages in batches for better memory management
            total_imported = 0
            batch_data = []
            
            for i, row in df.iterrows():
                # Extract message and category from row
                message = str(row[columns[message_idx]]) if message_idx is not None else ""
                category = str(row[columns[category_idx]]) if category_idx is not None and category_idx < len(columns) else ""
                
                # Skip empty messages
                if not message.strip():
                    continue
                
                # Prepare data
                message_data = (message, category, len(message))
                batch_data.append(message_data)
                
                # Insert batch if reached batch size
                if len(batch_data) >= batch_size:
                    cursor.executemany(
                        'INSERT INTO message_templates (message, category, length) VALUES (?, ?, ?)',
                        batch_data
                    )
                    total_imported += len(batch_data)
                    batch_data = []
                    
                    # Commit every batch to avoid too large transactions
                    conn.commit()
                    conn.execute('BEGIN TRANSACTION')
            
            # Insert any remaining messages
            if batch_data:
                cursor.executemany(
                    'INSERT INTO message_templates (message, category, length) VALUES (?, ?, ?)',
                    batch_data
                )
                total_imported += len(batch_data)
            
            # Commit the final transaction
            conn.commit()
            
            # Create indexes for better query performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_category ON message_templates (category)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_message_length ON message_templates (length)')
            
            # Close the database connection
            conn.close()
            
            return total_imported
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to import message data: {str(e)}")
    
    def toggle_categorization(self):
        """Toggle display of categorization settings"""
        if self.auto_categorize_var.get():
            self.categorization_frame.pack(fill=tk.X, padx=10, pady=5)
        else:
            self.categorization_frame.pack_forget()
    
    def add_custom_category(self):
        """Add a custom category to the list"""
        category = self.custom_category_var.get().strip()
        if not category:
            return
            
        # Add the category to the list
        code = category.lower().replace(" ", "_")
        display_name = category
        
        # Check if it already exists
        if code in self.category_vars:
            messagebox.showinfo("Category Exists", f"Category '{display_name}' already exists")
            return
            
        # Add the new category
        var = tk.BooleanVar(value=True)
        self.category_vars[code] = var
        
        # Add to categories list
        self.categories.append((code, display_name))
        
        # Add checkbox to the UI
        i = len(self.categories)
        frame = self.categorization_frame.winfo_children()[0]  # Get the first frame inside categorization_frame
        ttk.Checkbutton(frame, text=display_name, variable=var).grid(
            row=i, column=0, sticky=tk.W, padx=(20, 5)
        )
        
        # Clear the entry
        self.custom_category_var.set("")
        
    @staticmethod
    def open_importer(parent, import_type="names"):
        """Open the importer window and return result"""
        importer = DataImporterWindow(parent, import_type)
        parent.wait_window(importer.window)
        return importer.import_success