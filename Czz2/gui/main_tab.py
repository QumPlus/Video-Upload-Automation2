"""
Main Tab - Upload interface for Video Upload Automation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
from pathlib import Path

class MainTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Variables
        self.folder_path = tk.StringVar()
        self.is_running = False
        self.upload_queue = queue.Queue()
        self.progress_queue = queue.Queue()
        
        # Create GUI components
        self.create_widgets()
        self.start_progress_monitor()
        
    def create_widgets(self):
        """Create all GUI widgets for the main tab"""
        # Folder Selection Section
        folder_frame = ttk.LabelFrame(self.frame, text="Folder Selection", padding=10)
        folder_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(folder_frame, text="Rendered Folder:").pack(anchor='w')
        
        path_frame = ttk.Frame(folder_frame)
        path_frame.pack(fill='x', pady=5)
        
        self.path_entry = ttk.Entry(path_frame, textvariable=self.folder_path, width=60)
        self.path_entry.pack(side='left', fill='x', expand=True)
        
        self.browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_folder)
        self.browse_button.pack(side='right', padx=(5, 0))
        
        # Control Section
        control_frame = ttk.LabelFrame(self.frame, text="Control", padding=10)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        button_frame = ttk.Frame(control_frame)
        button_frame.pack()
        
        self.run_button = ttk.Button(button_frame, text="RUN", command=self.run_uploads, 
                                   width=15)
        self.run_button.pack(side='left', padx=5)
        
        self.abort_button = ttk.Button(button_frame, text="ABORT", command=self.abort_uploads, 
                                     state='disabled', width=15)
        self.abort_button.pack(side='left', padx=5)
        
        # Progress Section
        progress_frame = ttk.LabelFrame(self.frame, text="Progress", padding=10)
        progress_frame.pack(fill='x', padx=10, pady=5)
        
        self.current_label = ttk.Label(progress_frame, text="Current: Ready to start")
        self.current_label.pack(anchor='w')
        
        self.queue_label = ttk.Label(progress_frame, text="Queue: 0 files")
        self.queue_label.pack(anchor='w')
        
        self.active_label = ttk.Label(progress_frame, text="Active: 0/0 uploads")
        self.active_label.pack(anchor='w')
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=300)
        self.progress_bar.pack(pady=5, anchor='w')
        
        # Log Window
        log_frame = ttk.LabelFrame(self.frame, text="Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD)
        self.log_text.pack(fill='both', expand=True)
        
    def browse_folder(self):
        """Open folder selection dialog"""
        folder = filedialog.askdirectory(title="Select Rendered Folder")
        if folder:
            self.folder_path.set(folder)
            self.log_message(f"Selected folder: {folder}")
            
    def run_uploads(self):
        """Start the upload process"""
        if not self.folder_path.get():
            messagebox.showwarning("Warning", "Please select a folder first")
            return
            
        if not os.path.exists(self.folder_path.get()):
            messagebox.showerror("Error", "Selected folder does not exist")
            return
            
        # Check if any platforms are enabled
        enabled_platforms = self.app.get_enabled_platforms()
        if not enabled_platforms:
            messagebox.showwarning("Warning", "No platforms are enabled. Check Settings tab.")
            return
            
        self.is_running = True
        self.run_button.config(state='disabled')
        self.abort_button.config(state='normal')
        
        self.log_message("=== Starting upload process ===")
        self.log_message(f"Enabled platforms: {', '.join(enabled_platforms.keys())}")
        
        # Start upload process in background thread
        upload_thread = threading.Thread(target=self.upload_worker, daemon=True)
        upload_thread.start()
        
    def upload_worker(self):
        """Background worker for upload process"""
        try:
            # Get file manager and scan folders
            file_manager = self.app.get_file_manager(self.folder_path.get())
            files = file_manager.scan_folders()
            
            if not files:
                self.progress_queue.put(("log", "No video files found in selected folders"))
                self.progress_queue.put(("complete", None))
                return
                
            self.progress_queue.put(("log", f"Found {len(files)} files to process"))
            
            # Get upload manager and start uploads
            upload_manager = self.app.get_upload_manager()
            upload_manager.set_progress_callback(self.upload_progress_callback)
            
            enabled_platforms = self.app.get_enabled_platforms()
            upload_manager.set_enabled_platforms(enabled_platforms)
            
            # Add files to queue and start uploads
            for file_info in files:
                upload_manager.add_to_queue(file_info)
                
            upload_manager.start_uploads()
            
        except Exception as e:
            self.progress_queue.put(("error", f"Upload error: {str(e)}"))
            self.progress_queue.put(("complete", None))
            
    def upload_progress_callback(self, message_type, data):
        """Callback for upload progress updates"""
        self.progress_queue.put((message_type, data))
        
    def abort_uploads(self):
        """Stop all uploads"""
        if self.app.upload_manager:
            self.app.upload_manager.abort_all()
            
        self.is_running = False
        self.run_button.config(state='normal')
        self.abort_button.config(state='disabled')
        self.log_message("=== Upload process aborted ===")
        
    def start_progress_monitor(self):
        """Start monitoring progress queue"""
        self.monitor_progress()
        
    def monitor_progress(self):
        """Monitor progress queue and update GUI"""
        try:
            while True:
                message_type, data = self.progress_queue.get_nowait()
                
                if message_type == "log":
                    self.log_message(data)
                elif message_type == "current":
                    self.current_label.config(text=f"Current: {data}")
                elif message_type == "queue":
                    self.queue_label.config(text=f"Queue: {data} files remaining")
                elif message_type == "active":
                    self.active_label.config(text=f"Active: {data}")
                elif message_type == "progress":
                    self.progress_var.set(data)
                elif message_type == "complete":
                    self.upload_complete()
                elif message_type == "error":
                    self.log_message(f"ERROR: {data}")
                    
        except queue.Empty:
            pass
            
        # Schedule next check
        self.frame.after(100, self.monitor_progress)
        
    def upload_complete(self):
        """Handle upload completion"""
        self.is_running = False
        self.run_button.config(state='normal')
        self.abort_button.config(state='disabled')
        self.current_label.config(text="Current: Upload complete")
        self.progress_var.set(100)
        self.log_message("=== Upload process completed ===")
        
    def log_message(self, message):
        """Add message to log window"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        formatted_message = f"{timestamp} - {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def clear_log(self):
        """Clear the log window"""
        self.log_text.delete(1.0, tk.END) 