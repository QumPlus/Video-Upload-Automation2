"""
Main Tab - Upload interface for Video Upload Automation
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import queue
import os
import datetime
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
        
        # Folder scanning variables
        self.folder_watcher = None
        self.scanning_active = False
        self.auto_process = tk.BooleanVar(value=True)
        
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
        
        # Scanning Section
        scanning_frame = ttk.LabelFrame(self.frame, text="Auto-Scanning", padding=10)
        scanning_frame.pack(fill='x', padx=10, pady=5)
        
        # Scanning status row
        status_row = ttk.Frame(scanning_frame)
        status_row.pack(fill='x', pady=(0, 5))
        
        ttk.Label(status_row, text="Status:").pack(side='left')
        self.scanning_status = tk.StringVar(value="Stopped")
        self.scanning_status_label = ttk.Label(status_row, textvariable=self.scanning_status, 
                                              foreground="red")
        self.scanning_status_label.pack(side='left', padx=(5, 20))
        
        # Control buttons
        self.start_scanning_btn = ttk.Button(status_row, text="Start Scanning", 
                                            command=self.start_scanning)
        self.start_scanning_btn.pack(side='left', padx=(0, 5))
        
        self.stop_scanning_btn = ttk.Button(status_row, text="Stop Scanning", 
                                           command=self.stop_scanning, state="disabled")
        self.stop_scanning_btn.pack(side='left', padx=(5, 0))
        
        # Auto-process checkbox
        auto_checkbox = ttk.Checkbutton(scanning_frame, text="Auto-process detected files", 
                                       variable=self.auto_process)
        auto_checkbox.pack(anchor='w', pady=(5, 0))
        
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
        
    # Folder Scanning Methods
    
    def start_scanning(self):
        """Start folder scanning"""
        if not self.folder_path.get():
            messagebox.showerror("Error", "Please select a folder first")
            return
        
        try:
            from core.folder_watcher import FolderWatcher
            
            self.folder_watcher = FolderWatcher(
                self.folder_path.get(), 
                self.on_file_detected
            )
            
            # Create missing folders if needed
            created_folders = self.folder_watcher.create_missing_folders()
            if created_folders:
                self.log_message(f"Created missing folders: {', '.join([os.path.basename(f) for f in created_folders])}")
            
            self.folder_watcher.start_watching()
            
            # Update GUI
            self.scanning_status.set("Scanning...")
            self.scanning_status_label.config(foreground="green")
            self.start_scanning_btn.config(state="disabled")
            self.stop_scanning_btn.config(state="normal")
            self.scanning_active = True
            
            # Add to log
            self.log_message("=== Started folder scanning - ready to process files as they appear ===")
            
            # Show watch status
            status = self.folder_watcher.get_watch_status()
            for folder_name, folder_info in status['folders'].items():
                if folder_info['monitoring']:
                    self.log_message(f"✓ Monitoring: {folder_name}")
                elif folder_info['exists']:
                    self.log_message(f"⚠ Folder exists but not monitoring: {folder_name}")
                else:
                    self.log_message(f"✗ Folder missing: {folder_name}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scanning: {e}")
            self.log_message(f"ERROR: Failed to start scanning: {e}")

    def stop_scanning(self):
        """Stop folder scanning"""
        try:
            if self.folder_watcher:
                self.folder_watcher.stop_watching()
                self.folder_watcher = None
            
            # Update GUI
            self.scanning_status.set("Stopped")
            self.scanning_status_label.config(foreground="red")
            self.start_scanning_btn.config(state="normal")
            self.stop_scanning_btn.config(state="disabled")
            self.scanning_active = False
            
            # Add to log
            self.log_message("=== Stopped folder scanning ===")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop scanning: {e}")
            self.log_message(f"ERROR: Failed to stop scanning: {e}")

    def on_file_detected(self, file_path, folder_type):
        """Called when folder watcher detects a new file"""
        
        # Add to log
        filename = os.path.basename(file_path)
        self.log_message(f"🎬 Detected new file: {filename} in {folder_type} folder")
        
        # Auto-process if enabled
        if self.auto_process.get():
            # Check if file has required text files
            if self.validate_file_requirements(file_path):
                self.log_message(f"📤 Auto-processing: {filename}")
                self.process_single_file(file_path, folder_type)
            else:
                self.log_message(f"⏳ Waiting for text files for: {filename}")
                # Set up a timer to check again later
                self.schedule_recheck(file_path, folder_type)

    def validate_file_requirements(self, file_path):
        """Check if video file has required text files"""
        base_name = os.path.splitext(file_path)[0]
        
        # Check for TITLE.txt
        title_file = base_name + "_TITLE.txt"
        if not os.path.exists(title_file):
            return False
        
        # Check for folder-specific requirements
        folder_type = self.folder_watcher.get_folder_type(file_path) if self.folder_watcher else "unknown"
        
        if folder_type == "cloudflare":
            desc_file = base_name + "_DESCRIPTION.txt"
            return os.path.exists(desc_file)
        elif folder_type == "youtube_shorts":
            short_desc_file = base_name + "_SHORT_DESC.txt"
            return os.path.exists(short_desc_file)
        
        return True

    def schedule_recheck(self, file_path, folder_type, attempts=0):
        """Schedule a recheck for files missing text files"""
        max_attempts = 10  # Check for up to 50 minutes (5 min intervals)
        
        if attempts >= max_attempts:
            filename = os.path.basename(file_path)
            self.log_message(f"⚠ Giving up on {filename} - text files not found after {max_attempts * 5} minutes")
            return
        
        # Check again in 5 minutes
        def recheck():
            if self.validate_file_requirements(file_path):
                filename = os.path.basename(file_path)
                self.log_message(f"✅ Text files found! Processing: {filename}")
                self.process_single_file(file_path, folder_type)
            else:
                self.schedule_recheck(file_path, folder_type, attempts + 1)
        
        # Schedule the recheck
        threading.Timer(300, recheck).start()  # 300 seconds = 5 minutes

    def process_single_file(self, file_path, folder_type):
        """Process a single file for upload"""
        try:
            # Create file info object similar to what FileManager creates
            file_info = self.create_file_info(file_path, folder_type)
            
            # Get upload manager and add to queue
            upload_manager = self.app.get_upload_manager()
            upload_manager.set_progress_callback(self.upload_progress_callback)
            
            enabled_platforms = self.app.get_enabled_platforms()
            upload_manager.set_enabled_platforms(enabled_platforms)
            
            # Add to upload queue
            upload_manager.add_single_file(file_path, folder_type)
            
            # Start upload if not already running
            if not upload_manager.is_running:
                upload_manager.start_uploads()
                
        except Exception as e:
            filename = os.path.basename(file_path)
            self.log_message(f"ERROR: Failed to process {filename}: {e}")

    def create_file_info(self, file_path, folder_type):
        """Create file info object from a single file"""
        try:
            # Get file manager to extract metadata
            file_manager = self.app.get_file_manager(self.folder_path.get())
            
            # Extract metadata for this single file
            base_name = os.path.splitext(file_path)[0]
            
            # Read text files
            title = self.read_text_file(base_name + "_TITLE.txt")
            description = self.read_text_file(base_name + "_DESCRIPTION.txt") 
            short_desc = self.read_text_file(base_name + "_SHORT_DESC.txt")
            
            # Create file info object
            from core.file_manager import FileInfo
            
            file_info = FileInfo(
                path=file_path,
                filename=os.path.basename(file_path),
                title=title or os.path.splitext(os.path.basename(file_path))[0],
                description=description,
                short_description=short_desc,
                platforms=self.get_target_platforms_for_file(file_path, folder_type)
            )
            
            return file_info
            
        except Exception as e:
            raise Exception(f"Failed to create file info: {e}")

    def read_text_file(self, file_path):
        """Read text file content, return None if file doesn't exist"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except:
            pass
        return None

    def get_target_platforms_for_file(self, file_path, folder_type):
        """Determine which platforms this file should be uploaded to"""
        platforms = []
        filename = os.path.basename(file_path)
        
        if folder_type == 'cloudflare':
            # Always upload to CloudFlare and Facebook
            platforms.extend(['cloudflare', 'facebook'])
            
            # Upload "001" files to YouTube as well
            if "001" in filename:
                platforms.append('youtube')
                
        elif folder_type == 'pinterest':
            platforms.append('pinterest')
            
        elif folder_type == 'youtube_shorts':
            platforms.append('youtube_shorts')
        
        return platforms 