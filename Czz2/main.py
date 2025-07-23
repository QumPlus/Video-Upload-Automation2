#!/usr/bin/env python3
"""
Video Upload Automation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import json
import threading
from pathlib import Path

# Add project directories to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from gui.main_tab import MainTab
from gui.settings_tab import SettingsTab
from gui.schedule_tab import ScheduleTab
from core.file_manager import FileManager
from core.upload_manager import UploadManager

class VideoUploadApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Video Upload Automation")
        self.root.geometry("800x600")
        self.root.minsize(700, 500)
        
        # Configure style for macOS
        self.setup_theme()
        
        # Initialize components
        self.file_manager = None
        self.upload_manager = None
        
        # Create GUI
        self.create_notebook()
        self.load_settings()
        
    def setup_theme(self):
        """Configure theme for macOS appearance"""
        try:
            # Try to detect dark mode on macOS
            import subprocess
            result = subprocess.run(['defaults', 'read', '-g', 'AppleInterfaceStyle'], 
                                  capture_output=True, text=True)
            if result.returncode == 0 and 'Dark' in result.stdout:
                # Dark mode detected
                self.root.configure(bg='#2b2b2b')
            else:
                # Light mode
                self.root.configure(bg='#f0f0f0')
        except:
            # Default to light theme
            self.root.configure(bg='#f0f0f0')
            
        # Configure ttk styles
        style = ttk.Style()
        style.theme_use('aqua')  # macOS native theme
        
    def create_notebook(self):
        """Create the tabbed interface"""
        # Create notebook widget
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Create tabs
        self.main_tab = MainTab(self.notebook, self)
        self.settings_tab = SettingsTab(self.notebook, self)
        self.schedule_tab = ScheduleTab(self.notebook, self)
        
        # Add tabs to notebook
        self.notebook.add(self.main_tab.frame, text="Main")
        self.notebook.add(self.settings_tab.frame, text="Settings")
        self.notebook.add(self.schedule_tab.frame, text="Schedule")
        
    def load_settings(self):
        """Load application settings"""
        try:
            config_path = Path("config/settings.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    settings = json.load(f)
                    self.settings_tab.load_settings(settings)
                    self.schedule_tab.load_settings(settings)
        except Exception as e:
            print(f"Error loading settings: {e}")
            
    def save_settings(self):
        """Save application settings"""
        try:
            config_dir = Path("config")
            config_dir.mkdir(exist_ok=True)
            
            settings = {
                "platforms": self.settings_tab.get_settings(),
                "general": self.settings_tab.get_general_settings(),
                "scheduling": self.schedule_tab.get_settings()
            }
            
            with open("config/settings.json", 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
            
    def get_enabled_platforms(self):
        """Get list of enabled platforms"""
        return self.settings_tab.get_enabled_platforms()
        
    def get_upload_manager(self):
        """Get or create upload manager"""
        if not self.upload_manager:
            self.upload_manager = UploadManager(
                max_concurrent=self.settings_tab.get_max_concurrent()
            )
        return self.upload_manager
        
    def get_file_manager(self, base_path):
        """Get or create file manager"""
        if not self.file_manager or self.file_manager.base_path != base_path:
            self.file_manager = FileManager(base_path)
        return self.file_manager
        
    def on_closing(self):
        """Handle application closing"""
        try:
            # Stop any running uploads
            if self.upload_manager:
                self.upload_manager.abort_all()
                
            # Save settings
            self.save_settings()
            
        except Exception as e:
            print(f"Error during shutdown: {e}")
        finally:
            self.root.destroy()

def main():
    """Application entry point"""
    try:
        app = VideoUploadApp()
        app.root.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.root.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Fatal Error", f"Application failed to start: {e}")

if __name__ == "__main__":
    main() 