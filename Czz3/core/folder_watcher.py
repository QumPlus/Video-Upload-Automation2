"""
Folder Watcher - Real-time folder monitoring for video file detection
"""

import os
import time
import threading
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class VideoFileHandler(FileSystemEventHandler):
    """Handles file system events for video files"""
    
    def __init__(self, callback, valid_extensions=None):
        self.callback = callback
        self.valid_extensions = valid_extensions or ['.mov', '.mp4', '.avi', '.mkv', '.m4v', '.wmv']
        self.processing_files = set()  # Track files being processed
        self.file_timers = {}  # Track file modification timers
        
    def on_created(self, event):
        """Handle file creation events"""
        if not event.is_directory:
            self.handle_file_event(event.src_path, 'created')
    
    def on_modified(self, event):
        """Handle file modification events"""
        if not event.is_directory:
            self.handle_file_event(event.src_path, 'modified')
    
    def handle_file_event(self, file_path, event_type):
        """Process file system events for video files"""
        # Check if it's a video file
        if not any(file_path.lower().endswith(ext) for ext in self.valid_extensions):
            return
            
        # Avoid processing the same file multiple times
        if file_path in self.processing_files:
            return
            
        # Cancel any existing timer for this file
        if file_path in self.file_timers:
            self.file_timers[file_path].cancel()
        
        # Set a timer to process the file after it's stable (not being written to)
        timer = threading.Timer(3.0, self.process_stable_file, args=[file_path])
        self.file_timers[file_path] = timer
        timer.start()
    
    def process_stable_file(self, file_path):
        """Process file after it's been stable for a few seconds"""
        try:
            # Remove from timers
            if file_path in self.file_timers:
                del self.file_timers[file_path]
            
            # Check if file is complete (not being written to)
            if self.is_file_complete(file_path):
                self.processing_files.add(file_path)
                self.callback(file_path)
        except Exception as e:
            print(f"Error processing file {file_path}: {e}")
    
    def is_file_complete(self, file_path):
        """Check if file is completely written (not being modified)"""
        try:
            # Try to get file size twice with a small delay
            size1 = os.path.getsize(file_path)
            time.sleep(1)
            size2 = os.path.getsize(file_path)
            
            # File is complete if size hasn't changed and size > 0
            return size1 == size2 and size1 > 0
        except (OSError, FileNotFoundError):
            return False
    
    def mark_file_processed(self, file_path):
        """Mark file as processed to avoid reprocessing"""
        self.processing_files.discard(file_path)

class FolderWatcher:
    """Main folder watcher class that monitors video file folders"""
    
    def __init__(self, base_path, file_callback):
        self.base_path = base_path
        self.file_callback = file_callback
        self.observer = Observer()
        self.is_watching = False
        
        # Paths to watch - these match your folder structure
        self.watch_paths = [
            os.path.join(base_path, "CloudFlare"),
            os.path.join(base_path, "Pinterest"), 
            os.path.join(base_path, "YouTube Shorts")
        ]
        
        # Create handler
        self.handler = VideoFileHandler(self.on_file_detected)
    
    def start_watching(self):
        """Start monitoring all folders"""
        if self.is_watching:
            return
            
        try:
            # Schedule monitoring for each folder
            watched_count = 0
            for watch_path in self.watch_paths:
                if os.path.exists(watch_path):
                    self.observer.schedule(self.handler, watch_path, recursive=False)
                    print(f"Started watching: {watch_path}")
                    watched_count += 1
                else:
                    print(f"Warning: Folder doesn't exist: {watch_path}")
            
            if watched_count == 0:
                raise Exception("No valid folders found to watch")
            
            self.observer.start()
            self.is_watching = True
            print(f"Folder watching started successfully - monitoring {watched_count} folders")
            
        except Exception as e:
            print(f"Error starting folder watcher: {e}")
            raise
    
    def stop_watching(self):
        """Stop monitoring folders"""
        if self.is_watching:
            self.observer.stop()
            self.observer.join()
            self.is_watching = False
            print("Folder watching stopped")
    
    def on_file_detected(self, file_path):
        """Called when a new video file is detected"""
        print(f"New file detected: {file_path}")
        
        # Determine which folder the file is in
        folder_type = self.get_folder_type(file_path)
        
        # Call the main callback with file info
        self.file_callback(file_path, folder_type)
    
    def get_folder_type(self, file_path):
        """Determine which type of folder contains the file"""
        normalized_path = file_path.replace('\\', '/')
        
        if "CloudFlare" in normalized_path:
            return "cloudflare"
        elif "Pinterest" in normalized_path:
            return "pinterest"
        elif "YouTube Shorts" in normalized_path:
            return "youtube_shorts"
        else:
            return "unknown"
    
    def create_missing_folders(self):
        """Create any missing watch folders"""
        created_folders = []
        for watch_path in self.watch_paths:
            if not os.path.exists(watch_path):
                try:
                    os.makedirs(watch_path, exist_ok=True)
                    created_folders.append(watch_path)
                    print(f"Created missing folder: {watch_path}")
                except Exception as e:
                    print(f"Failed to create folder {watch_path}: {e}")
        return created_folders
    
    def get_watch_status(self):
        """Get the current watching status and folder availability"""
        status = {
            'is_watching': self.is_watching,
            'base_path': self.base_path,
            'folders': {}
        }
        
        for watch_path in self.watch_paths:
            folder_name = os.path.basename(watch_path)
            status['folders'][folder_name] = {
                'path': watch_path,
                'exists': os.path.exists(watch_path),
                'monitoring': self.is_watching and os.path.exists(watch_path)
            }
        
        return status 