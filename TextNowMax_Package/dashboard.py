"""
Dashboard for ProgressGhostCreator account management
"""

import os
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import logging
import time
import threading
from datetime import datetime
import random

class ProgressGhostDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("PB BETTING - TextNow Account Manager")
        self.root.geometry("1280x720")
        self.root.minsize(1024, 600)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        
        # Initialize database connection
        self.init_database()
        
        # Initialize UI variables
        self.selected_account = None
        self.current_campaign = None
        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value="All Accounts")
        self.status_message = tk.StringVar(value="Ready")
        
        # Set up the UI
        self.setup_ui()
        
        # Load initial data
        self.load_accounts()
        self.load_campaigns()
    
    def init_database(self):
        """Initialize database connection"""
        try:
            # Create database and tables if they don't exist
            if not os.path.exists('ghost_accounts.db'):
                import create_database
                create_database.create_database()
                create_database.create_sample_data()
            
            # Connect to the database
            self.conn = sqlite3.connect('ghost_accounts.db', check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")
    
    def setup_ui(self):
        """Set up the main UI components"""
        # Load styling
        self.setup_styles()
        
        # Create main frame
        main_frame = ttk.Frame(self.root, style="Main.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Add header with logo
        self.create_header(main_frame)
        
        # Create the main content area with left and right panels
        content_frame = ttk.Frame(main_frame, style="Content.TFrame")
        content_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Create a PanedWindow for resizable panels
        paned_window = ttk.PanedWindow(content_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # Left panel: Account list and filters
        left_panel = ttk.Frame(paned_window, style="Panel.TFrame")
        paned_window.add(left_panel, weight=40)
        
        # Right panel: Account details and messaging
        right_panel = ttk.Frame(paned_window, style="Panel.TFrame")
        paned_window.add(right_panel, weight=60)
        
        # Set up the left panel (account list)
        self.setup_left_panel(left_panel)
        
        # Set up the right panel (account details and messaging)
        self.setup_right_panel(right_panel)
        
        # Add status bar
        self.create_status_bar(main_frame)
    
    def setup_styles(self):
        """Set up ttk styles"""
        style = ttk.Style()
        
        # Create custom ttk styles
        style.configure("TFrame", background="#FFFFFF")
        style.configure("Main.TFrame", background="#FFFFFF")
        style.configure("Header.TFrame", background="#FF6600")
        style.configure("Content.TFrame", background="#F0F0F0")
        style.configure("Panel.TFrame", background="#FFFFFF")
        style.configure("Status.TFrame", background="#F0F0F0")
        
        style.configure("Header.TLabel", 
                        background="#FF6600", 
                        foreground="white", 
                        font=("Helvetica", 16, "bold"))
        
        style.configure("Title.TLabel", 
                        background="#FFFFFF", 
                        foreground="#333333", 
                        font=("Helvetica", 14, "bold"))
        
        style.configure("Section.TLabel", 
                        background="#FFFFFF", 
                        foreground="#666666", 
                        font=("Helvetica", 12, "bold"))
        
        style.configure("Status.TLabel", 
                        background="#F0F0F0", 
                        foreground="#333333", 
                        font=("Helvetica", 10))
        
        # Configure Treeview
        style.configure("Treeview", 
                        background="#FFFFFF",
                        fieldbackground="#FFFFFF",
                        foreground="#333333",
                        rowheight=25)
        
        style.configure("Treeview.Heading", 
                        background="#E0E0E0", 
                        foreground="#333333",
                        font=("Helvetica", 10, "bold"))
        
        style.map("Treeview", 
                 background=[("selected", "#FF6600")],
                 foreground=[("selected", "white")])
        
        # Configure buttons
        style.configure("TButton", 
                        background="#FF6600", 
                        foreground="#333333")
        
        style.configure("Primary.TButton", 
                        background="#FF6600", 
                        foreground="white",
                        font=("Helvetica", 10, "bold"))
        
        style.map("Primary.TButton",
                 background=[("active", "#FF8000"), ("disabled", "#CCCCCC")],
                 foreground=[("disabled", "#888888")])
        
        style.configure("Secondary.TButton", 
                        background="#E0E0E0", 
                        foreground="#333333")
        
        style.map("Secondary.TButton",
                 background=[("active", "#D0D0D0"), ("disabled", "#CCCCCC")],
                 foreground=[("disabled", "#888888")])
        
        # Configure combobox
        style.configure("TCombobox", 
                        fieldbackground="#FFFFFF", 
                        background="#FFFFFF",
                        selectbackground="#FF6600",
                        selectforeground="white")
    
    def create_header(self, parent):
        """Create the header with logo and title"""
        header_frame = ttk.Frame(parent, style="Header.TFrame")
        header_frame.pack(fill=tk.X, pady=0)
        
        # Try to load logo if it exists
        try:
            # Look for logo in different potential locations
            logo_paths = [
                "assets/progress_logo.png",
                "static/progress_logo.png",
                "attached_assets/progress_logo.png"
            ]
            
            logo_path = None
            for path in logo_paths:
                if os.path.exists(path):
                    logo_path = path
                    break
            
            if logo_path:
                from PIL import Image, ImageTk
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((150, 50), Image.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                
                logo_label = ttk.Label(header_frame, image=self.logo_photo, background="#FF6600")
                logo_label.pack(side=tk.LEFT, padx=15, pady=10)
            else:
                # Fallback to text if logo image not found
                logo_label = ttk.Label(header_frame, text="PB BETTING", 
                                     style="Header.TLabel")
                logo_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        except Exception as e:
            logging.error(f"Failed to load logo: {e}")
            # Fallback to text
            logo_label = ttk.Label(header_frame, text="PB BETTING", 
                                 style="Header.TLabel")
            logo_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Add dashboard title
        title_label = ttk.Label(header_frame, text="TextNow Account Manager", 
                               style="Header.TLabel")
        title_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Add user info on the right side
        user_frame = ttk.Frame(header_frame, style="Header.TFrame")
        user_frame.pack(side=tk.RIGHT, padx=15, pady=10)
        
        user_label = ttk.Label(user_frame, text="Admin Dashboard", 
                              style="Header.TLabel", font=("Helvetica", 12))
        user_label.pack(side=tk.RIGHT)
    
    def create_status_bar(self, parent):
        """Create the status bar at the bottom"""
        status_frame = ttk.Frame(parent, style="Status.TFrame")
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        status_label = ttk.Label(status_frame, textvariable=self.status_message, 
                                style="Status.TLabel")
        status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Add count of accounts on the right
        self.accounts_count_var = tk.StringVar(value="Total Accounts: 0")
        accounts_count_label = ttk.Label(status_frame, 
                                        textvariable=self.accounts_count_var,
                                        style="Status.TLabel")
        accounts_count_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Add copyright info
        copyright_label = ttk.Label(status_frame, text="© PB BETTING™", 
                                   style="Status.TLabel", 
                                   foreground="#888888")
        copyright_label.pack(anchor=tk.CENTER, expand=True, pady=5)
    
    def setup_left_panel(self, parent):
        """Set up the left panel with account list and filters"""
        # Control section
        control_frame = ttk.Frame(parent, style="Panel.TFrame")
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Title for the panel
        accounts_title = ttk.Label(control_frame, text="TextNow Accounts", 
                                  style="Title.TLabel")
        accounts_title.pack(anchor=tk.W, pady=(0, 10))
        
        # Search and filter section
        search_frame = ttk.Frame(control_frame, style="Panel.TFrame")
        search_frame.pack(fill=tk.X, pady=5)
        
        # Search field
        search_label = ttk.Label(search_frame, text="Search:", 
                                style="Section.TLabel")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=5)
        
        search_button = ttk.Button(search_frame, text="Search", 
                                  command=self.search_accounts,
                                  style="Primary.TButton")
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Filter dropdown
        filter_frame = ttk.Frame(control_frame, style="Panel.TFrame")
        filter_frame.pack(fill=tk.X, pady=5)
        
        filter_label = ttk.Label(filter_frame, text="Filter:", 
                                style="Section.TLabel")
        filter_label.pack(side=tk.LEFT, padx=(0, 5))
        
        filter_options = ["All Accounts", "Active Accounts", "Inactive Accounts", 
                         "Recently Used", "In Campaign", "Available for Campaign"]
        filter_dropdown = ttk.Combobox(filter_frame, textvariable=self.filter_var, 
                                      values=filter_options, state="readonly", width=20)
        filter_dropdown.pack(side=tk.LEFT, padx=5)
        filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.load_accounts())
        
        # Buttons for account management
        button_frame = ttk.Frame(control_frame, style="Panel.TFrame")
        button_frame.pack(fill=tk.X, pady=10)
        
        refresh_button = ttk.Button(button_frame, text="Refresh", 
                                   command=self.load_accounts,
                                   style="Secondary.TButton")
        refresh_button.pack(side=tk.LEFT, padx=5)
        
        new_button = ttk.Button(button_frame, text="Start Creator", 
                               command=self.open_creator,
                               style="Primary.TButton")
        new_button.pack(side=tk.LEFT, padx=5)
        
        delete_button = ttk.Button(button_frame, text="Delete", 
                                  command=self.delete_account,
                                  style="Secondary.TButton")
        delete_button.pack(side=tk.LEFT, padx=5)
        
        # Account list
        list_frame = ttk.Frame(parent, style="Panel.TFrame")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        # Create a frame with a scrollbar for the treeview
        tree_frame = ttk.Frame(list_frame, style="Panel.TFrame")
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create the treeview
        self.account_tree = ttk.Treeview(tree_frame, columns=("phone", "username", "created", "status"),
                                       show="headings", selectmode="browse")
        
        # Configure the treeview
        self.account_tree.heading("phone", text="Phone Number")
        self.account_tree.heading("username", text="Username")
        self.account_tree.heading("created", text="Created")
        self.account_tree.heading("status", text="Status")
        
        self.account_tree.column("phone", width=120, anchor=tk.W)
        self.account_tree.column("username", width=100, anchor=tk.W)
        self.account_tree.column("created", width=100, anchor=tk.W)
        self.account_tree.column("status", width=80, anchor=tk.CENTER)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.account_tree.yview)
        self.account_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack the treeview and scrollbar
        self.account_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind event for selection
        self.account_tree.bind("<<TreeviewSelect>>", self.on_account_select)
    
    def setup_right_panel(self, parent):
        """Set up the right panel with account details and messaging"""
        # Setup tab layout
        self.tabs = ttk.Notebook(parent)
        self.tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Account Details Tab
        self.details_tab = ttk.Frame(self.tabs, style="Panel.TFrame")
        self.tabs.add(self.details_tab, text="Account Details")
        
        # Messaging Tab
        self.messaging_tab = ttk.Frame(self.tabs, style="Panel.TFrame")
        self.tabs.add(self.messaging_tab, text="Messaging")
        
        # Campaign Tab
        self.campaign_tab = ttk.Frame(self.tabs, style="Panel.TFrame")
        self.tabs.add(self.campaign_tab, text="Campaigns")
        
        # Set up the account details tab
        self.setup_details_tab()
        
        # Set up the messaging tab
        self.setup_messaging_tab()
        
        # Set up the campaigns tab
        self.setup_campaign_tab()
    
    def setup_details_tab(self):
        """Set up the account details tab"""
        # Create header section
        header_frame = ttk.Frame(self.details_tab, style="Panel.TFrame")
        header_frame.pack(fill=tk.X, pady=10)
        
        self.details_title = ttk.Label(header_frame, text="Account Details", 
                                     style="Title.TLabel")
        self.details_title.pack(anchor=tk.W, padx=10)
        
        # Create a frame for the account details
        details_frame = ttk.Frame(self.details_tab, style="Panel.TFrame")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Create a label frame for the basic details
        basic_frame = ttk.LabelFrame(details_frame, text="Basic Information", 
                                    style="Panel.TFrame")
        basic_frame.pack(fill=tk.X, pady=10)
        
        # Create details grid
        self.detail_vars = {
            "id": tk.StringVar(),
            "username": tk.StringVar(),
            "email": tk.StringVar(),
            "password": tk.StringVar(),
            "phone_number": tk.StringVar(),
            "created_at": tk.StringVar(),
            "last_used": tk.StringVar(),
            "ip_used": tk.StringVar(),
            "voicemail_file": tk.StringVar(),
            "active": tk.BooleanVar(),
            "notes": tk.StringVar()
        }
        
        # Create grid layout
        row = 0
        
        # Phone Number
        ttk.Label(basic_frame, text="Phone Number:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(basic_frame, textvariable=self.detail_vars["phone_number"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Username
        row += 1
        ttk.Label(basic_frame, text="Username:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(basic_frame, textvariable=self.detail_vars["username"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Email
        row += 1
        ttk.Label(basic_frame, text="Email:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(basic_frame, textvariable=self.detail_vars["email"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Password
        row += 1
        ttk.Label(basic_frame, text="Password:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        
        password_frame = ttk.Frame(basic_frame)
        password_frame.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        self.password_display = ttk.Label(password_frame, text="********")
        self.password_display.pack(side=tk.LEFT)
        
        def toggle_password():
            if self.password_display["text"] == "********":
                self.password_display["text"] = self.detail_vars["password"].get()
                show_button["text"] = "Hide"
            else:
                self.password_display["text"] = "********"
                show_button["text"] = "Show"
        
        show_button = ttk.Button(password_frame, text="Show", 
                               command=toggle_password, width=5)
        show_button.pack(side=tk.LEFT, padx=5)
        
        # More details in a separate frame
        more_frame = ttk.LabelFrame(details_frame, text="Additional Information", 
                                   style="Panel.TFrame")
        more_frame.pack(fill=tk.X, pady=10)
        
        row = 0
        
        # Created date
        ttk.Label(more_frame, text="Created:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(more_frame, textvariable=self.detail_vars["created_at"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Last used
        row += 1
        ttk.Label(more_frame, text="Last Used:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(more_frame, textvariable=self.detail_vars["last_used"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # IP Used
        row += 1
        ttk.Label(more_frame, text="IP Address:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        ttk.Label(more_frame, textvariable=self.detail_vars["ip_used"]).grid(
            row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Voicemail file
        row += 1
        ttk.Label(more_frame, text="Voicemail:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        
        voicemail_frame = ttk.Frame(more_frame)
        voicemail_frame.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        ttk.Label(voicemail_frame, textvariable=self.detail_vars["voicemail_file"]).pack(
            side=tk.LEFT)
        
        play_button = ttk.Button(voicemail_frame, text="Play", width=5,
                               command=self.play_voicemail)
        play_button.pack(side=tk.LEFT, padx=5)
        
        # Active status
        row += 1
        ttk.Label(more_frame, text="Active:", 
                 font=("Helvetica", 10, "bold")).grid(row=row, column=0, 
                                                    sticky=tk.W, padx=10, pady=5)
        
        active_check = ttk.Checkbutton(more_frame, variable=self.detail_vars["active"],
                                     command=self.toggle_active_status)
        active_check.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Notes section
        notes_frame = ttk.LabelFrame(details_frame, text="Notes", 
                                   style="Panel.TFrame")
        notes_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.notes_text = tk.Text(notes_frame, height=5, width=40, wrap=tk.WORD)
        self.notes_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add a button to save notes
        save_frame = ttk.Frame(details_frame, style="Panel.TFrame")
        save_frame.pack(fill=tk.X, pady=10)
        
        save_button = ttk.Button(save_frame, text="Save Notes", 
                               command=self.save_notes,
                               style="Primary.TButton")
        save_button.pack(side=tk.RIGHT, padx=10)
    
    def setup_messaging_tab(self):
        """Set up the messaging tab"""
        # Create header section
        header_frame = ttk.Frame(self.messaging_tab, style="Panel.TFrame")
        header_frame.pack(fill=tk.X, pady=10)
        
        self.messaging_title = ttk.Label(header_frame, text="Messaging", 
                                       style="Title.TLabel")
        self.messaging_title.pack(anchor=tk.W, padx=10)
        
        # Create main messaging frame
        messaging_frame = ttk.Frame(self.messaging_tab, style="Panel.TFrame")
        messaging_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Split into left and right areas
        messaging_pane = ttk.PanedWindow(messaging_frame, orient=tk.HORIZONTAL)
        messaging_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left side: contacts list
        contacts_frame = ttk.LabelFrame(messaging_pane, text="Conversations", 
                                      style="Panel.TFrame")
        messaging_pane.add(contacts_frame, weight=30)
        
        # Search box for contacts
        contact_search_frame = ttk.Frame(contacts_frame, style="Panel.TFrame")
        contact_search_frame.pack(fill=tk.X, padx=10, pady=5)
        
        contact_search_var = tk.StringVar()
        contact_entry = ttk.Entry(contact_search_frame, textvariable=contact_search_var)
        contact_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        search_contact_button = ttk.Button(contact_search_frame, text="Search", width=8)
        search_contact_button.pack(side=tk.RIGHT)
        
        # Contacts treeview
        contacts_tree_frame = ttk.Frame(contacts_frame)
        contacts_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.contacts_tree = ttk.Treeview(contacts_tree_frame, 
                                        columns=("contact", "last_message", "time"),
                                        show="headings", selectmode="browse")
        
        self.contacts_tree.heading("contact", text="Contact")
        self.contacts_tree.heading("last_message", text="Last Message")
        self.contacts_tree.heading("time", text="Time")
        
        self.contacts_tree.column("contact", width=100, anchor=tk.W)
        self.contacts_tree.column("last_message", width=150, anchor=tk.W)
        self.contacts_tree.column("time", width=50, anchor=tk.CENTER)
        
        contacts_scrollbar = ttk.Scrollbar(contacts_tree_frame, orient="vertical", 
                                         command=self.contacts_tree.yview)
        self.contacts_tree.configure(yscrollcommand=contacts_scrollbar.set)
        
        self.contacts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        contacts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Button to add new contact
        new_contact_button = ttk.Button(contacts_frame, text="New Conversation", 
                                      style="Primary.TButton", 
                                      command=self.new_conversation)
        new_contact_button.pack(fill=tk.X, padx=10, pady=10)
        
        # Right side: message conversation
        conversation_frame = ttk.LabelFrame(messaging_pane, text="Messages", 
                                          style="Panel.TFrame")
        messaging_pane.add(conversation_frame, weight=70)
        
        # Contact info
        self.convo_contact = tk.StringVar(value="No Contact Selected")
        convo_header = ttk.Frame(conversation_frame, style="Panel.TFrame")
        convo_header.pack(fill=tk.X, padx=10, pady=5)
        
        contact_label = ttk.Label(convo_header, textvariable=self.convo_contact,
                                font=("Helvetica", 12, "bold"))
        contact_label.pack(side=tk.LEFT)
        
        # Message history display
        message_frame = ttk.Frame(conversation_frame, style="Panel.TFrame")
        message_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.message_display = scrolledtext.ScrolledText(message_frame, 
                                                      wrap=tk.WORD, 
                                                      state=tk.DISABLED,
                                                      bg="#F7F7F7")
        self.message_display.pack(fill=tk.BOTH, expand=True)
        
        # Apply tags for message formatting
        self.message_display.tag_configure("incoming", background="#E0E0E0", 
                                         lmargin1=10, lmargin2=10, rmargin=80)
        self.message_display.tag_configure("outgoing", background="#CCE5FF", 
                                         lmargin1=80, lmargin2=80, rmargin=10,
                                         justify="right")
        self.message_display.tag_configure("time", foreground="#888888", 
                                         font=("Helvetica", 8))
        
        # Message input and send button
        input_frame = ttk.Frame(conversation_frame, style="Panel.TFrame")
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.message_input = tk.Text(input_frame, height=3, width=30, wrap=tk.WORD)
        self.message_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        send_button = ttk.Button(input_frame, text="Send", width=10, 
                               style="Primary.TButton",
                               command=self.send_message)
        send_button.pack(side=tk.RIGHT)
    
    def setup_campaign_tab(self):
        """Set up the campaign tab"""
        # Create header section
        header_frame = ttk.Frame(self.campaign_tab, style="Panel.TFrame")
        header_frame.pack(fill=tk.X, pady=10)
        
        self.campaign_title = ttk.Label(header_frame, text="Campaign Management", 
                                      style="Title.TLabel")
        self.campaign_title.pack(anchor=tk.W, padx=10)
        
        # Create main frame
        campaign_frame = ttk.Frame(self.campaign_tab, style="Panel.TFrame")
        campaign_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # Split into two sections
        campaign_pane = ttk.PanedWindow(campaign_frame, orient=tk.HORIZONTAL)
        campaign_pane.pack(fill=tk.BOTH, expand=True)
        
        # Left side: campaign list
        campaign_list_frame = ttk.LabelFrame(campaign_pane, text="Campaigns", 
                                           style="Panel.TFrame")
        campaign_pane.add(campaign_list_frame, weight=40)
        
        # Campaign controls
        campaign_control_frame = ttk.Frame(campaign_list_frame, style="Panel.TFrame")
        campaign_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        new_campaign_button = ttk.Button(campaign_control_frame, text="New Campaign", 
                                       style="Primary.TButton", 
                                       command=self.new_campaign)
        new_campaign_button.pack(side=tk.LEFT, padx=(0, 5))
        
        delete_campaign_button = ttk.Button(campaign_control_frame, text="Delete", 
                                         style="Secondary.TButton",
                                         command=self.delete_campaign)
        delete_campaign_button.pack(side=tk.LEFT)
        
        # Campaign treeview
        campaign_tree_frame = ttk.Frame(campaign_list_frame)
        campaign_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.campaign_tree = ttk.Treeview(campaign_tree_frame, 
                                        columns=("name", "status", "accounts", "sent"),
                                        show="headings", selectmode="browse")
        
        self.campaign_tree.heading("name", text="Campaign Name")
        self.campaign_tree.heading("status", text="Status")
        self.campaign_tree.heading("accounts", text="Accounts")
        self.campaign_tree.heading("sent", text="Sent")
        
        self.campaign_tree.column("name", width=150, anchor=tk.W)
        self.campaign_tree.column("status", width=80, anchor=tk.CENTER)
        self.campaign_tree.column("accounts", width=80, anchor=tk.CENTER)
        self.campaign_tree.column("sent", width=80, anchor=tk.CENTER)
        
        campaign_scrollbar = ttk.Scrollbar(campaign_tree_frame, orient="vertical", 
                                        command=self.campaign_tree.yview)
        self.campaign_tree.configure(yscrollcommand=campaign_scrollbar.set)
        
        self.campaign_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        campaign_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind selection event
        self.campaign_tree.bind("<<TreeviewSelect>>", self.on_campaign_select)
        
        # Right side: campaign details
        campaign_details_frame = ttk.LabelFrame(campaign_pane, text="Campaign Details", 
                                              style="Panel.TFrame")
        campaign_pane.add(campaign_details_frame, weight=60)
        
        # Campaign info
        self.campaign_info_frame = ttk.Frame(campaign_details_frame, style="Panel.TFrame")
        self.campaign_info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Campaign name
        campaign_name_frame = ttk.Frame(self.campaign_info_frame, style="Panel.TFrame")
        campaign_name_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(campaign_name_frame, text="Campaign Name:", 
                 font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.campaign_name_var = tk.StringVar()
        self.campaign_name_display = ttk.Label(campaign_name_frame, 
                                             textvariable=self.campaign_name_var,
                                             font=("Helvetica", 10))
        self.campaign_name_display.pack(side=tk.LEFT)
        
        # Campaign status
        campaign_status_frame = ttk.Frame(self.campaign_info_frame, style="Panel.TFrame")
        campaign_status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(campaign_status_frame, text="Status:", 
                 font=("Helvetica", 10, "bold")).pack(side=tk.LEFT, padx=(0, 5))
        
        self.campaign_status_var = tk.StringVar()
        ttk.Label(campaign_status_frame, 
                 textvariable=self.campaign_status_var).pack(side=tk.LEFT)
        
        # Campaign description
        campaign_desc_frame = ttk.LabelFrame(campaign_details_frame, text="Description", 
                                           style="Panel.TFrame")
        campaign_desc_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.campaign_desc_text = tk.Text(campaign_desc_frame, height=4, width=40, 
                                        wrap=tk.WORD)
        self.campaign_desc_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Campaign message template
        campaign_msg_frame = ttk.LabelFrame(campaign_details_frame, text="Message Template", 
                                          style="Panel.TFrame")
        campaign_msg_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.campaign_msg_text = tk.Text(campaign_msg_frame, height=4, width=40, 
                                       wrap=tk.WORD)
        self.campaign_msg_text.pack(fill=tk.X, padx=10, pady=10)
        
        # Accounts in campaign
        accounts_frame = ttk.LabelFrame(campaign_details_frame, text="Accounts in Campaign", 
                                      style="Panel.TFrame")
        accounts_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Accounts treeview
        accounts_tree_frame = ttk.Frame(accounts_frame)
        accounts_tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.campaign_accounts_tree = ttk.Treeview(accounts_tree_frame, 
                                                columns=("phone", "username", "status"),
                                                show="headings", selectmode="browse")
        
        self.campaign_accounts_tree.heading("phone", text="Phone Number")
        self.campaign_accounts_tree.heading("username", text="Username")
        self.campaign_accounts_tree.heading("status", text="Status")
        
        self.campaign_accounts_tree.column("phone", width=120, anchor=tk.W)
        self.campaign_accounts_tree.column("username", width=100, anchor=tk.W)
        self.campaign_accounts_tree.column("status", width=80, anchor=tk.CENTER)
        
        accounts_scrollbar = ttk.Scrollbar(accounts_tree_frame, orient="vertical", 
                                         command=self.campaign_accounts_tree.yview)
        self.campaign_accounts_tree.configure(yscrollcommand=accounts_scrollbar.set)
        
        self.campaign_accounts_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        accounts_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Campaign actions
        action_frame = ttk.Frame(campaign_details_frame, style="Panel.TFrame")
        action_frame.pack(fill=tk.X, padx=10, pady=10)
        
        add_account_button = ttk.Button(action_frame, text="Add Accounts", 
                                      style="Secondary.TButton",
                                      command=self.add_accounts_to_campaign)
        add_account_button.pack(side=tk.LEFT, padx=(0, 5))
        
        remove_account_button = ttk.Button(action_frame, text="Remove Account", 
                                        style="Secondary.TButton",
                                        command=self.remove_account_from_campaign)
        remove_account_button.pack(side=tk.LEFT, padx=(0, 5))
        
        start_campaign_button = ttk.Button(action_frame, text="Start Campaign", 
                                         style="Primary.TButton",
                                         command=self.start_campaign)
        start_campaign_button.pack(side=tk.RIGHT)
    
    def load_accounts(self):
        """Load accounts from the database into the treeview"""
        try:
            # Clear the treeview
            for item in self.account_tree.get_children():
                self.account_tree.delete(item)
            
            # Get filter value
            filter_value = self.filter_var.get()
            
            # Construct the query based on filter
            query = "SELECT * FROM accounts"
            params = []
            
            if filter_value == "Active Accounts":
                query += " WHERE active = 1"
            elif filter_value == "Inactive Accounts":
                query += " WHERE active = 0"
            elif filter_value == "Recently Used":
                query += " WHERE last_used IS NOT NULL AND last_used != '' ORDER BY last_used DESC"
            elif filter_value == "In Campaign":
                query = """
                SELECT a.* FROM accounts a
                JOIN campaign_accounts ca ON a.id = ca.account_id
                GROUP BY a.id
                """
            elif filter_value == "Available for Campaign":
                query = """
                SELECT a.* FROM accounts a
                LEFT JOIN campaign_accounts ca ON a.id = ca.account_id
                WHERE ca.account_id IS NULL AND a.active = 1
                """
            
            # Get search term
            search_term = self.search_var.get().strip()
            if search_term:
                if "WHERE" in query:
                    query += " AND (username LIKE ? OR phone_number LIKE ? OR email LIKE ?)"
                else:
                    query += " WHERE (username LIKE ? OR phone_number LIKE ? OR email LIKE ?)"
                
                params.extend([f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"])
            
            # Execute the query
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            accounts = cursor.fetchall()
            
            # Add accounts to the treeview
            for account in accounts:
                created_date = datetime.fromisoformat(account["created_at"]).strftime("%Y-%m-%d")
                status = "Active" if account["active"] else "Inactive"
                
                self.account_tree.insert("", "end", 
                                        values=(account["phone_number"], 
                                              account["username"], 
                                              created_date, 
                                              status),
                                        tags=(str(account["id"]),))
            
            # Update account count
            self.accounts_count_var.set(f"Total Accounts: {len(accounts)}")
            
            # Update status
            self.status_message.set(f"Loaded {len(accounts)} accounts")
            
        except Exception as e:
            logging.error(f"Failed to load accounts: {e}")
            messagebox.showerror("Database Error", f"Failed to load accounts: {e}")
    
    def load_campaigns(self):
        """Load campaigns from the database"""
        try:
            # Clear the treeview
            for item in self.campaign_tree.get_children():
                self.campaign_tree.delete(item)
            
            # Query campaigns
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT c.*, COUNT(ca.account_id) as account_count
            FROM campaigns c
            LEFT JOIN campaign_accounts ca ON c.id = ca.campaign_id
            GROUP BY c.id
            """)
            
            campaigns = cursor.fetchall()
            
            # Add campaigns to the treeview
            for campaign in campaigns:
                self.campaign_tree.insert("", "end", 
                                        values=(campaign["name"], 
                                              campaign["status"].title(), 
                                              campaign["account_count"],
                                              campaign["messages_sent"]),
                                        tags=(str(campaign["id"]),))
            
            # Update status
            self.status_message.set(f"Loaded {len(campaigns)} campaigns")
            
        except Exception as e:
            logging.error(f"Failed to load campaigns: {e}")
            messagebox.showerror("Database Error", f"Failed to load campaigns: {e}")
    
    def on_account_select(self, event):
        """Handle account selection in the treeview"""
        try:
            # Get selected item
            selection = self.account_tree.selection()
            if not selection:
                return
            
            # Get the account ID from the tags
            account_id = self.account_tree.item(selection[0], "tags")[0]
            
            # Query account details
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM accounts WHERE id = ?", (account_id,))
            account = cursor.fetchone()
            
            if account:
                # Store selected account
                self.selected_account = account
                
                # Update title
                self.details_title.config(text=f"Account Details: {account['phone_number']}")
                
                # Update detail variables
                for key in self.detail_vars:
                    if key in account and account[key] is not None:
                        if key == "active":
                            self.detail_vars[key].set(bool(account[key]))
                        else:
                            self.detail_vars[key].set(account[key])
                
                # Update notes
                self.notes_text.delete(1.0, tk.END)
                if account["notes"]:
                    self.notes_text.insert(tk.END, account["notes"])
                
                # Update messaging tab
                self.load_conversations()
                
                # Switch to details tab
                self.tabs.select(self.details_tab)
                
                # Update status
                self.status_message.set(f"Account {account['phone_number']} loaded")
            
        except Exception as e:
            logging.error(f"Error loading account details: {e}")
            messagebox.showerror("Error", f"Failed to load account details: {e}")
    
    def on_campaign_select(self, event):
        """Handle campaign selection in the treeview"""
        try:
            # Get selected item
            selection = self.campaign_tree.selection()
            if not selection:
                return
            
            # Get the campaign ID from the tags
            campaign_id = self.campaign_tree.item(selection[0], "tags")[0]
            
            # Query campaign details
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,))
            campaign = cursor.fetchone()
            
            if campaign:
                # Store selected campaign
                self.current_campaign = campaign
                
                # Update campaign details
                self.campaign_name_var.set(campaign["name"])
                self.campaign_status_var.set(campaign["status"].title())
                
                # Update description
                self.campaign_desc_text.delete(1.0, tk.END)
                if campaign["description"]:
                    self.campaign_desc_text.insert(tk.END, campaign["description"])
                
                # Update message template (sample)
                self.campaign_msg_text.delete(1.0, tk.END)
                self.campaign_msg_text.insert(tk.END, "Hey there! Check out our latest offers at PB BETTING!")
                
                # Load accounts in this campaign
                self.load_campaign_accounts(campaign_id)
                
                # Switch to campaign tab
                self.tabs.select(self.campaign_tab)
                
                # Update status
                self.status_message.set(f"Campaign {campaign['name']} loaded")
                
        except Exception as e:
            logging.error(f"Error loading campaign details: {e}")
            messagebox.showerror("Error", f"Failed to load campaign details: {e}")
    
    def load_campaign_accounts(self, campaign_id):
        """Load accounts for a specific campaign"""
        try:
            # Clear the treeview
            for item in self.campaign_accounts_tree.get_children():
                self.campaign_accounts_tree.delete(item)
            
            # Query accounts in this campaign
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT a.*, ca.status as campaign_status
            FROM accounts a
            JOIN campaign_accounts ca ON a.id = ca.account_id
            WHERE ca.campaign_id = ?
            """, (campaign_id,))
            
            accounts = cursor.fetchall()
            
            # Add accounts to the treeview
            for account in accounts:
                self.campaign_accounts_tree.insert("", "end", 
                                                 values=(account["phone_number"], 
                                                       account["username"], 
                                                       account["campaign_status"].title()),
                                                 tags=(str(account["id"]),))
            
        except Exception as e:
            logging.error(f"Failed to load campaign accounts: {e}")
            messagebox.showerror("Database Error", f"Failed to load campaign accounts: {e}")
    
    def load_conversations(self):
        """Load conversations for the selected account"""
        if not self.selected_account:
            return
        
        try:
            # Clear the treeview
            for item in self.contacts_tree.get_children():
                self.contacts_tree.delete(item)
            
            # For demo, we'll add some sample conversations
            sample_contacts = [
                ("(555) 123-4567", "Hey there!", "10:30 AM"),
                ("(555) 987-6543", "When will you be available?", "Yesterday"),
                ("(555) 456-7890", "Check out this new offer!", "Monday"),
                ("(555) 321-0987", "Thanks for your help", "Last week")
            ]
            
            # Add conversations to the treeview
            for i, (contact, last_msg, time) in enumerate(sample_contacts):
                self.contacts_tree.insert("", "end", 
                                        values=(contact, last_msg[:20] + "...", time),
                                        tags=(f"contact_{i}",))
            
        except Exception as e:
            logging.error(f"Error loading conversations: {e}")
    
    def search_accounts(self):
        """Search accounts based on the search term"""
        self.load_accounts()
    
    def open_creator(self):
        """Open the account creator window"""
        messagebox.showinfo("Account Creator", 
                          "This will launch the TextNow Account Creator in a separate window.")
        
        # In a real implementation, this would start the creator process
        # For demo, we'll just show a message
        self.status_message.set("Account creator launched in a separate window")
    
    def delete_account(self):
        """Delete the selected account"""
        if not self.selected_account:
            messagebox.showinfo("No Selection", "Please select an account to delete.")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    f"Are you sure you want to delete the account {self.selected_account['phone_number']}?")
        
        if confirm:
            try:
                # Delete the account
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM accounts WHERE id = ?", (self.selected_account["id"],))
                self.conn.commit()
                
                # Reload accounts
                self.load_accounts()
                
                # Clear selection
                self.selected_account = None
                
                # Update status
                self.status_message.set("Account deleted successfully")
                
            except Exception as e:
                logging.error(f"Error deleting account: {e}")
                messagebox.showerror("Database Error", f"Failed to delete account: {e}")
    
    def toggle_active_status(self):
        """Toggle the active status of the selected account"""
        if not self.selected_account:
            return
        
        try:
            # Get new status
            new_status = self.detail_vars["active"].get()
            
            # Update the database
            cursor = self.conn.cursor()
            cursor.execute("UPDATE accounts SET active = ? WHERE id = ?", 
                         (int(new_status), self.selected_account["id"]))
            self.conn.commit()
            
            # Reload accounts
            self.load_accounts()
            
            # Update status message
            status_text = "activated" if new_status else "deactivated"
            self.status_message.set(f"Account {self.selected_account['phone_number']} {status_text}")
            
        except Exception as e:
            logging.error(f"Error updating account status: {e}")
            messagebox.showerror("Database Error", f"Failed to update account status: {e}")
    
    def save_notes(self):
        """Save notes for the selected account"""
        if not self.selected_account:
            return
        
        try:
            # Get notes text
            notes = self.notes_text.get(1.0, tk.END).strip()
            
            # Update the database
            cursor = self.conn.cursor()
            cursor.execute("UPDATE accounts SET notes = ? WHERE id = ?", 
                         (notes, self.selected_account["id"]))
            self.conn.commit()
            
            # Update status
            self.status_message.set("Notes saved successfully")
            
        except Exception as e:
            logging.error(f"Error saving notes: {e}")
            messagebox.showerror("Database Error", f"Failed to save notes: {e}")
    
    def play_voicemail(self):
        """Play the voicemail for the selected account"""
        if not self.selected_account or not self.selected_account["voicemail_file"]:
            messagebox.showinfo("No Voicemail", "No voicemail file available for this account.")
            return
        
        messagebox.showinfo("Voicemail", f"Playing voicemail: {self.selected_account['voicemail_file']}")
        # In a real implementation, this would play the audio file
    
    def new_conversation(self):
        """Start a new conversation"""
        if not self.selected_account:
            messagebox.showinfo("No Account", "Please select an account first.")
            return
        
        # In a real app, this would open a dialog to enter a new contact
        # For demo, we'll just show a message
        messagebox.showinfo("New Conversation", 
                          "This would open a dialog to enter a new contact number.")
        
        # Update status
        self.status_message.set("New conversation started")
    
    def send_message(self):
        """Send a message in the current conversation"""
        if not self.selected_account:
            messagebox.showinfo("No Account", "Please select an account first.")
            return
        
        # Get the message text
        message = self.message_input.get(1.0, tk.END).strip()
        
        if not message:
            return
        
        # In a real app, this would send the message via the TextNow API
        # For demo, we'll just add it to the message display
        
        # Format the timestamp
        timestamp = time.strftime("%I:%M %p")
        
        # Add message to the display
        self.message_display.config(state=tk.NORMAL)
        
        # Add a separator if there are already messages
        if self.message_display.get(1.0, tk.END).strip():
            self.message_display.insert(tk.END, "\n\n")
        
        # Add the outgoing message
        self.message_display.insert(tk.END, f"{message}\n", "outgoing")
        self.message_display.insert(tk.END, f"{timestamp}\n", "time")
        
        # Clear the input
        self.message_input.delete(1.0, tk.END)
        
        # Scroll to the bottom
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
        
        # Update status
        self.status_message.set("Message sent")
        
        # Simulate a reply after a delay
        self.root.after(2000, self.simulate_reply)
    
    def simulate_reply(self):
        """Simulate a reply message (for demo purposes)"""
        if not self.selected_account:
            return
        
        # Sample replies
        replies = [
            "Hey there! What's up?",
            "Thanks for your message!",
            "Sorry, I'm busy right now.",
            "Can we talk later?",
            "Sounds good to me!",
            "I'll check and get back to you.",
            "Is this about the new offer?",
            "Sure, I'm interested. Tell me more."
        ]
        
        # Choose a random reply
        reply = random.choice(replies)
        
        # Format the timestamp
        timestamp = time.strftime("%I:%M %p")
        
        # Add message to the display
        self.message_display.config(state=tk.NORMAL)
        self.message_display.insert(tk.END, "\n\n")
        self.message_display.insert(tk.END, f"{reply}\n", "incoming")
        self.message_display.insert(tk.END, f"{timestamp}\n", "time")
        
        # Scroll to the bottom
        self.message_display.see(tk.END)
        self.message_display.config(state=tk.DISABLED)
        
        # Update status
        self.status_message.set("New message received")
    
    def new_campaign(self):
        """Create a new campaign"""
        # In a real app, this would open a dialog to create a new campaign
        # For demo, we'll just create a sample campaign
        
        try:
            # Get a name for the campaign
            campaign_name = f"Campaign {int(time.time())}"
            
            # Insert into database
            cursor = self.conn.cursor()
            cursor.execute("""
            INSERT INTO campaigns (name, description, created_at, status, messages_sent, messages_failed)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                campaign_name,
                "New campaign created via dashboard",
                datetime.now().isoformat(),
                "setup",
                0,
                0
            ))
            self.conn.commit()
            
            # Reload campaigns
            self.load_campaigns()
            
            # Update status
            self.status_message.set(f"Campaign '{campaign_name}' created")
            
        except Exception as e:
            logging.error(f"Error creating campaign: {e}")
            messagebox.showerror("Database Error", f"Failed to create campaign: {e}")
    
    def delete_campaign(self):
        """Delete the selected campaign"""
        if not self.current_campaign:
            messagebox.showinfo("No Selection", "Please select a campaign to delete.")
            return
        
        # Confirm deletion
        confirm = messagebox.askyesno("Confirm Deletion", 
                                    f"Are you sure you want to delete the campaign '{self.current_campaign['name']}'?")
        
        if confirm:
            try:
                # Delete the campaign
                cursor = self.conn.cursor()
                cursor.execute("DELETE FROM campaign_accounts WHERE campaign_id = ?", 
                             (self.current_campaign["id"],))
                cursor.execute("DELETE FROM campaigns WHERE id = ?", 
                             (self.current_campaign["id"],))
                self.conn.commit()
                
                # Reload campaigns
                self.load_campaigns()
                
                # Clear selection
                self.current_campaign = None
                
                # Update status
                self.status_message.set("Campaign deleted successfully")
                
            except Exception as e:
                logging.error(f"Error deleting campaign: {e}")
                messagebox.showerror("Database Error", f"Failed to delete campaign: {e}")
    
    def add_accounts_to_campaign(self):
        """Add accounts to the current campaign"""
        if not self.current_campaign:
            messagebox.showinfo("No Campaign", "Please select a campaign first.")
            return
        
        # In a real app, this would open a dialog to select accounts
        # For demo, we'll just add some random accounts
        
        try:
            # Get some available accounts
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT a.* FROM accounts a
            LEFT JOIN campaign_accounts ca ON a.id = ca.account_id AND ca.campaign_id = ?
            WHERE ca.account_id IS NULL AND a.active = 1
            LIMIT 5
            """, (self.current_campaign["id"],))
            
            accounts = cursor.fetchall()
            
            if not accounts:
                messagebox.showinfo("No Accounts", "No available accounts to add to the campaign.")
                return
            
            # Add accounts to the campaign
            for account in accounts:
                cursor.execute("""
                INSERT INTO campaign_accounts (campaign_id, account_id, status)
                VALUES (?, ?, ?)
                """, (
                    self.current_campaign["id"],
                    account["id"],
                    "active"
                ))
            
            self.conn.commit()
            
            # Reload campaign accounts
            self.load_campaign_accounts(self.current_campaign["id"])
            self.load_campaigns()  # Refresh campaign list to update account count
            
            # Update status
            self.status_message.set(f"Added {len(accounts)} accounts to campaign")
            
        except Exception as e:
            logging.error(f"Error adding accounts to campaign: {e}")
            messagebox.showerror("Database Error", f"Failed to add accounts to campaign: {e}")
    
    def remove_account_from_campaign(self):
        """Remove an account from the current campaign"""
        if not self.current_campaign:
            messagebox.showinfo("No Campaign", "Please select a campaign first.")
            return
        
        # Get selected account
        selection = self.campaign_accounts_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select an account to remove.")
            return
        
        # Get the account ID from the tags
        account_id = self.campaign_accounts_tree.item(selection[0], "tags")[0]
        
        try:
            # Remove the account from the campaign
            cursor = self.conn.cursor()
            cursor.execute("""
            DELETE FROM campaign_accounts 
            WHERE campaign_id = ? AND account_id = ?
            """, (
                self.current_campaign["id"],
                account_id
            ))
            self.conn.commit()
            
            # Reload campaign accounts
            self.load_campaign_accounts(self.current_campaign["id"])
            self.load_campaigns()  # Refresh campaign list to update account count
            
            # Update status
            self.status_message.set("Account removed from campaign")
            
        except Exception as e:
            logging.error(f"Error removing account from campaign: {e}")
            messagebox.showerror("Database Error", f"Failed to remove account from campaign: {e}")
    
    def start_campaign(self):
        """Start the current campaign"""
        if not self.current_campaign:
            messagebox.showinfo("No Campaign", "Please select a campaign first.")
            return
        
        # In a real app, this would start the campaign messaging process
        # For demo, we'll just update the status
        
        try:
            # Check if there are accounts in the campaign
            cursor = self.conn.cursor()
            cursor.execute("""
            SELECT COUNT(*) as count FROM campaign_accounts
            WHERE campaign_id = ?
            """, (self.current_campaign["id"],))
            
            count = cursor.fetchone()["count"]
            
            if count == 0:
                messagebox.showinfo("No Accounts", "Please add accounts to the campaign before starting.")
                return
            
            # Update campaign status
            cursor.execute("""
            UPDATE campaigns SET status = ? WHERE id = ?
            """, (
                "active",
                self.current_campaign["id"]
            ))
            self.conn.commit()
            
            # Update the status var
            self.campaign_status_var.set("Active")
            
            # Reload campaigns
            self.load_campaigns()
            
            # Update status
            self.status_message.set(f"Campaign '{self.current_campaign['name']}' started")
            
            # Show confirmation
            messagebox.showinfo("Campaign Started", 
                              f"Campaign '{self.current_campaign['name']}' has been started with {count} accounts.")
            
        except Exception as e:
            logging.error(f"Error starting campaign: {e}")
            messagebox.showerror("Database Error", f"Failed to start campaign: {e}")

def main():
    root = tk.Tk()
    app = ProgressGhostDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main()