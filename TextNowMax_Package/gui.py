import os
import sys
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import time
import logging
from pathlib import Path
import io
import base64

class ProgressGhostGUI:
    def __init__(self, root, bot, data_manager):
        self.root = root
        self.bot = bot
        self.data_manager = data_manager
        self.setup_gui()
        self.running = False
        self.paused = False
        self.bot_thread = None
        self.update_status_thread = None
        
    def resource_path(self, relative_path):
        """Get absolute path to resource, works for dev and for PyInstaller"""
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            import sys
            base_path = getattr(sys, '_MEIPASS', os.path.abspath("."))
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def setup_gui(self):
        # Configure main window
        self.root.title("ProgressGhostCreator")
        self.root.geometry("800x600")
        self.root.minsize(800, 600)
        self.root.configure(bg="#1E1E1E")  # Dark mode background
        
        # Load background image from file
        try:
            bg_path = self.resource_path("assets/progress_background.jpg")
            
            # Convert image for tkinter
            bg_image = Image.open(bg_path)
            bg_image = bg_image.resize((800, 600), Image.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(bg_image)
            
            # Create a label with the background image
            bg_label = tk.Label(self.root, image=self.bg_photo)
            bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            logging.error(f"Failed to load background image: {e}")
            # Create a fallback orange gradient background
            bg_frame = tk.Frame(self.root, bg="#FF6600")
            bg_frame.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Main frame for controls with some transparency
        main_frame = tk.Frame(self.root, bg="#1E1E1E", bd=2, relief=tk.RIDGE)
        main_frame.place(relx=0.5, rely=0.03, relwidth=0.9, relheight=0.94, anchor=tk.N)
        
        # Load and place the logo
        try:
            logo_path = self.resource_path("assets/progress_logo.png")
            
            # Convert image for tkinter
            logo_image = Image.open(logo_path)
            logo_image = logo_image.resize((300, 80), Image.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_image)
            
            logo_label = tk.Label(main_frame, image=self.logo_photo, bg="#1E1E1E")
            logo_label.pack(pady=10)
        except Exception as e:
            logging.error(f"Failed to load logo: {e}")
            # Fallback logo
            logo_label = tk.Label(main_frame, text="PB BETTING", font=("Helvetica", 24, "bold"), 
                                 fg="#FF6600", bg="#1E1E1E")
            logo_label.pack(pady=10)
        
        # Title label
        title_label = tk.Label(main_frame, text="ProgressGhostCreator", 
                              font=("Helvetica", 18, "bold"), 
                              fg="#FF6600", bg="#1E1E1E")
        title_label.pack(pady=5)
        
        # Input frame
        input_frame = tk.Frame(main_frame, bg="#1E1E1E")
        input_frame.pack(pady=10, fill=tk.X, padx=20)
        
        # Account count input
        account_label = tk.Label(input_frame, text="Number of accounts to create:", 
                                font=("Helvetica", 12), fg="white", bg="#1E1E1E")
        account_label.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        
        self.account_count = tk.StringVar(value="10")
        account_entry = tk.Entry(input_frame, textvariable=self.account_count, 
                               width=10, font=("Helvetica", 12))
        account_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        # Button style
        button_style = {"font": ("Helvetica", 12, "bold"), 
                       "bg": "#FF6600", "fg": "white", 
                       "activebackground": "#FF8833",
                       "activeforeground": "white", 
                       "bd": 1, "relief": tk.RAISED,
                       "padx": 15, "pady": 5}
        
        # Control buttons
        button_frame = tk.Frame(main_frame, bg="#1E1E1E")
        button_frame.pack(pady=10)
        
        self.start_button = tk.Button(button_frame, text="Start Bot", 
                                    command=self.start_bot, **button_style)
        self.start_button.grid(row=0, column=0, padx=10, pady=5)
        
        self.pause_button = tk.Button(button_frame, text="Pause", 
                                    command=self.toggle_pause, state=tk.DISABLED, **button_style)
        self.pause_button.grid(row=0, column=1, padx=10, pady=5)
        
        self.stop_button = tk.Button(button_frame, text="Stop", 
                                   command=self.stop_bot, state=tk.DISABLED, **button_style)
        self.stop_button.grid(row=0, column=2, padx=10, pady=5)
        
        # Status frame
        status_frame = tk.Frame(main_frame, bg="#1E1E1E")
        status_frame.pack(pady=10, fill=tk.BOTH, expand=True, padx=20)
        
        # Status label
        status_label = tk.Label(status_frame, text="Status Log:", 
                              font=("Helvetica", 12, "bold"), 
                              fg="white", bg="#1E1E1E", anchor=tk.W)
        status_label.pack(fill=tk.X)
        
        # Status log
        self.status_log = scrolledtext.ScrolledText(status_frame, height=15, 
                                                  font=("Courier", 10),
                                                  bg="#2D2D2D", fg="#CCCCCC")
        self.status_log.pack(fill=tk.BOTH, expand=True)
        self.status_log.config(state=tk.DISABLED)
        
        # Progress bar and status counter
        progress_frame = tk.Frame(main_frame, bg="#1E1E1E")
        progress_frame.pack(pady=10, fill=tk.X, padx=20)
        
        self.progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                      length=100, mode='determinate')
        progress_bar.pack(fill=tk.X, pady=5)
        
        self.counter_label = tk.Label(progress_frame, 
                                    text="Created: 0 | Failed: 0 | Remaining: 0", 
                                    font=("Helvetica", 10), fg="white", bg="#1E1E1E")
        self.counter_label.pack(fill=tk.X)
        
        # Footer with credits
        footer_label = tk.Label(main_frame, text="© PB BETTING™", 
                              font=("Helvetica", 8), fg="#888888", bg="#1E1E1E")
        footer_label.pack(side=tk.BOTTOM, pady=5)
        
        # Initialize counters
        self.created_count = 0
        self.failed_count = 0
        self.total_count = 0
        
        # Center window on screen
        self.center_window()
    
    def center_window(self):
        """Center the window on the screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def update_status(self, message, message_type="info"):
        """Update the status log with a colored message"""
        self.status_log.config(state=tk.NORMAL)
        
        # Add timestamp to message
        timestamp = time.strftime("%H:%M:%S")
        
        # Color code by message type
        if message_type == "error":
            tag = "error"
            color = "#FF5555"  # Red for errors
        elif message_type == "success":
            tag = "success"
            color = "#55FF55"  # Green for success
        elif message_type == "warning":
            tag = "warning"
            color = "#FFFF55"  # Yellow for warnings
        else:
            tag = "info"
            color = "#CCCCCC"  # Light gray for info
            
        self.status_log.tag_config(tag, foreground=color)
        
        # Insert the message
        self.status_log.insert(tk.END, f"[{timestamp}] ", "timestamp")
        self.status_log.tag_config("timestamp", foreground="#888888")
        self.status_log.insert(tk.END, f"{message}\n", tag)
        
        # Auto-scroll to the bottom
        self.status_log.see(tk.END)
        self.status_log.config(state=tk.DISABLED)
    
    def update_counters(self):
        """Update the counter display and progress bar"""
        if self.total_count > 0:
            remaining = self.total_count - (self.created_count + self.failed_count)
            progress = ((self.created_count + self.failed_count) / self.total_count) * 100
            self.progress_var.set(progress)
            self.counter_label.config(
                text=f"Created: {self.created_count} | Failed: {self.failed_count} | Remaining: {remaining}"
            )
    
    def start_bot(self):
        """Start the bot in a separate thread"""
        try:
            # Get the number of accounts to create
            try:
                self.total_count = int(self.account_count.get())
                if self.total_count <= 0:
                    raise ValueError("Number of accounts must be positive")
            except ValueError as e:
                messagebox.showerror("Invalid Input", f"Please enter a valid number: {e}")
                return
            
            # Reset counters
            self.created_count = 0
            self.failed_count = 0
            self.progress_var.set(0)
            self.update_counters()
            
            # Clear the status log
            self.status_log.config(state=tk.NORMAL)
            self.status_log.delete(1.0, tk.END)
            self.status_log.config(state=tk.DISABLED)
            
            # Update UI state
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL, text="Pause")
            self.stop_button.config(state=tk.NORMAL)
            
            # Start the bot thread
            self.running = True
            self.paused = False
            
            self.update_status("Initializing TextNow Bot...")
            
            self.bot_thread = threading.Thread(target=self.run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            
            # Start status updating thread
            self.update_status_thread = threading.Thread(target=self.monitor_status)
            self.update_status_thread.daemon = True
            self.update_status_thread.start()
            
        except Exception as e:
            self.update_status(f"Error starting bot: {str(e)}", "error")
            logging.error(f"Error starting bot: {e}", exc_info=True)
    
    def run_bot(self):
        """Run the bot operation in a separate thread"""
        try:
            # Initialize the bot if needed
            self.update_status("Setting up browser and device...")
            
            # Run the account creation process
            self.bot.create_accounts(
                count=self.total_count,
                callback=self.account_callback,
                should_continue=self.should_continue
            )
            
        except Exception as e:
            self.update_status(f"Bot error: {str(e)}", "error")
            logging.error(f"Bot error: {e}", exc_info=True)
        finally:
            # Clean up when done
            self.root.after(0, self.bot_finished)
    
    def account_callback(self, result, success):
        """Callback function for the bot to report results"""
        if success:
            self.created_count += 1
            self.update_status(f"Account created: {result.get('phone_number', 'unknown')}", "success")
        else:
            self.failed_count += 1
            self.update_status(f"Failed to create account: {result.get('error', 'unknown error')}", "error")
        
        # Update the UI
        self.root.after(0, self.update_counters)
    
    def should_continue(self):
        """Check if the bot should continue running"""
        return self.running and not self.paused
    
    def toggle_pause(self):
        """Pause or resume the bot"""
        if self.running:
            self.paused = not self.paused
            if self.paused:
                self.pause_button.config(text="Resume")
                self.update_status("Bot paused. Click Resume to continue.", "warning")
                
                # Create pause.txt file
                with open("pause.txt", "w") as f:
                    f.write("PAUSED")
            else:
                self.pause_button.config(text="Pause")
                self.update_status("Bot resumed.", "info")
                
                # Delete pause.txt file if it exists
                if os.path.exists("pause.txt"):
                    os.remove("pause.txt")
    
    def stop_bot(self):
        """Stop the bot"""
        if messagebox.askyesno("Stop Bot", "Are you sure you want to stop the bot? This will terminate all operations."):
            self.running = False
            self.update_status("Stopping bot. Please wait...", "warning")
            
            # Delete pause.txt file if it exists
            if os.path.exists("pause.txt"):
                os.remove("pause.txt")
    
    def bot_finished(self):
        """Called when the bot has finished"""
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Bot finished.", "info")
    
    def monitor_status(self):
        """Thread to monitor and update bot status"""
        while self.running:
            # Update status with the latest count
            if self.created_count + self.failed_count > 0:
                self.root.after(0, self.update_counters)
            time.sleep(1)
