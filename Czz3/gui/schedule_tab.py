"""
Schedule Tab - Scheduling functionality for Video Upload Automation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import schedule
import threading
import time
from datetime import datetime, timedelta

class ScheduleTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Scheduling variables
        self.schedule_type = tk.StringVar(value="manual")
        self.schedule_time = tk.StringVar(value="14:00")
        self.schedule_day = tk.StringVar(value="Monday")
        self.facebook_delay_days = tk.IntVar(value=30)
        self.auto_retry = tk.BooleanVar(value=True)
        self.scheduling_enabled = tk.BooleanVar(value=False)
        
        # Scheduler state
        self.scheduler_thread = None
        self.scheduler_running = False
        self.next_run_time = None
        self.last_run_time = None
        
        # Create GUI components
        self.create_widgets()
        self.start_status_updater()
        
    def create_widgets(self):
        """Create all GUI widgets for the schedule tab"""
        # Scheduling Options Section
        options_frame = ttk.LabelFrame(self.frame, text="Scheduling Options", padding=10)
        options_frame.pack(fill='x', padx=10, pady=5)
        
        # Manual option
        manual_frame = ttk.Frame(options_frame)
        manual_frame.pack(fill='x', pady=2)
        ttk.Radiobutton(manual_frame, text="Run Once (Manual)", 
                       variable=self.schedule_type, value="manual").pack(anchor='w')
        
        # Daily option
        daily_frame = ttk.Frame(options_frame)
        daily_frame.pack(fill='x', pady=2)
        ttk.Radiobutton(daily_frame, text="Run Daily at:", 
                       variable=self.schedule_type, value="daily").pack(side='left')
        
        time_combo = ttk.Combobox(daily_frame, textvariable=self.schedule_time, width=8)
        time_combo['values'] = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
        time_combo.pack(side='left', padx=5)
        
        # Weekly option
        weekly_frame = ttk.Frame(options_frame)
        weekly_frame.pack(fill='x', pady=2)
        ttk.Radiobutton(weekly_frame, text="Run Weekly on:", 
                       variable=self.schedule_type, value="weekly").pack(side='left')
        
        day_combo = ttk.Combobox(weekly_frame, textvariable=self.schedule_day, width=10)
        day_combo['values'] = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        day_combo.pack(side='left', padx=5)
        
        ttk.Label(weekly_frame, text="at").pack(side='left', padx=2)
        
        weekly_time_combo = ttk.Combobox(weekly_frame, textvariable=self.schedule_time, width=8)
        weekly_time_combo['values'] = [f"{h:02d}:{m:02d}" for h in range(24) for m in [0, 30]]
        weekly_time_combo.pack(side='left', padx=5)
        
        # Custom schedule option
        custom_frame = ttk.Frame(options_frame)
        custom_frame.pack(fill='x', pady=2)
        ttk.Radiobutton(custom_frame, text="Custom Schedule", 
                       variable=self.schedule_type, value="custom").pack(anchor='w')
        
        # Facebook delay setting
        fb_frame = ttk.Frame(options_frame)
        fb_frame.pack(fill='x', pady=5)
        ttk.Label(fb_frame, text="Facebook Post Delay:").pack(side='left')
        delay_combo = ttk.Combobox(fb_frame, textvariable=self.facebook_delay_days, width=8)
        delay_combo['values'] = [1, 7, 14, 21, 30, 45, 60, 90]
        delay_combo.pack(side='left', padx=5)
        ttk.Label(fb_frame, text="days").pack(side='left')
        
        # Auto-retry option
        retry_frame = ttk.Frame(options_frame)
        retry_frame.pack(fill='x', pady=2)
        ttk.Checkbutton(retry_frame, text="Auto-retry Failed (every 2 hours)", 
                       variable=self.auto_retry).pack(anchor='w')
        
        # Scheduled Tasks Section
        tasks_frame = ttk.LabelFrame(self.frame, text="Scheduled Tasks", padding=10)
        tasks_frame.pack(fill='x', padx=10, pady=5)
        
        # Status labels
        self.next_run_label = ttk.Label(tasks_frame, text="Next Run: Not scheduled")
        self.next_run_label.pack(anchor='w', pady=2)
        
        self.last_run_label = ttk.Label(tasks_frame, text="Last Run: Never")
        self.last_run_label.pack(anchor='w', pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(tasks_frame)
        button_frame.pack(fill='x', pady=10)
        
        self.enable_button = ttk.Button(button_frame, text="Enable Scheduling", 
                                      command=self.enable_scheduling)
        self.enable_button.pack(side='left', padx=5)
        
        self.disable_button = ttk.Button(button_frame, text="Disable", 
                                       command=self.disable_scheduling, state='disabled')
        self.disable_button.pack(side='left', padx=5)
        
        self.run_now_button = ttk.Button(button_frame, text="Run Now", 
                                       command=self.run_now)
        self.run_now_button.pack(side='left', padx=5)
        
        # Log section
        log_frame = ttk.LabelFrame(self.frame, text="Schedule Log", padding=10)
        log_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=8, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side='left', fill='both', expand=True)
        log_scrollbar.pack(side='right', fill='y')
        
    def enable_scheduling(self):
        """Enable automatic scheduling"""
        if self.schedule_type.get() == "manual":
            messagebox.showwarning("Warning", "Please select a scheduling option other than 'Manual'")
            return
            
        try:
            self.scheduling_enabled.set(True)
            self.setup_scheduler()
            
            self.enable_button.config(state='disabled')
            self.disable_button.config(state='normal')
            
            self.log_message("Scheduling enabled")
            self.update_next_run_display()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable scheduling: {str(e)}")
            
    def disable_scheduling(self):
        """Disable automatic scheduling"""
        try:
            self.scheduling_enabled.set(False)
            self.stop_scheduler()
            
            self.enable_button.config(state='normal')
            self.disable_button.config(state='disabled')
            
            self.next_run_label.config(text="Next Run: Not scheduled")
            self.log_message("Scheduling disabled")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to disable scheduling: {str(e)}")
            
    def run_now(self):
        """Run upload process immediately"""
        try:
            self.log_message("Running upload process manually")
            
            # Get the main tab and trigger upload
            main_tab = self.app.main_tab
            if hasattr(main_tab, 'run_uploads'):
                # Switch to main tab
                self.app.notebook.select(0)
                # Run uploads
                main_tab.run_uploads()
                
                self.last_run_time = datetime.now()
                self.update_last_run_display()
                
        except Exception as e:
            self.log_message(f"Error running manual upload: {str(e)}")
            
    def setup_scheduler(self):
        """Set up the scheduler based on selected options"""
        schedule.clear()  # Clear any existing schedules
        
        schedule_time = self.schedule_time.get()
        
        if self.schedule_type.get() == "daily":
            schedule.every().day.at(schedule_time).do(self.scheduled_upload)
            self.log_message(f"Scheduled daily upload at {schedule_time}")
            
        elif self.schedule_type.get() == "weekly":
            day = self.schedule_day.get().lower()
            getattr(schedule.every(), day).at(schedule_time).do(self.scheduled_upload)
            self.log_message(f"Scheduled weekly upload on {self.schedule_day.get()} at {schedule_time}")
            
        elif self.schedule_type.get() == "custom":
            # For custom schedules, you could add more complex logic here
            self.log_message("Custom schedule not yet implemented")
            return
            
        # Start scheduler thread
        if not self.scheduler_running:
            self.scheduler_running = True
            self.scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
            self.scheduler_thread.start()
            
    def run_scheduler(self):
        """Run the scheduler in a background thread"""
        while self.scheduler_running and self.scheduling_enabled.get():
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                self.log_message(f"Scheduler error: {str(e)}")
                time.sleep(60)
                
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.scheduler_running = False
        schedule.clear()
        
    def scheduled_upload(self):
        """Perform scheduled upload"""
        try:
            self.log_message("Starting scheduled upload")
            
            # Check if main tab has a folder selected
            main_tab = self.app.main_tab
            if not main_tab.folder_path.get():
                self.log_message("ERROR: No folder selected for upload")
                return
                
            # Check if any platforms are enabled
            enabled_platforms = self.app.get_enabled_platforms()
            if not enabled_platforms:
                self.log_message("ERROR: No platforms enabled")
                return
                
            # Trigger upload process
            # Note: This runs in the scheduler thread, so we need to be careful with GUI updates
            self.app.root.after(0, self.trigger_main_upload)
            
            self.last_run_time = datetime.now()
            
        except Exception as e:
            self.log_message(f"Scheduled upload error: {str(e)}")
            
    def trigger_main_upload(self):
        """Trigger upload from main tab (called from GUI thread)"""
        try:
            main_tab = self.app.main_tab
            main_tab.run_uploads()
            self.update_last_run_display()
        except Exception as e:
            self.log_message(f"Error triggering upload: {str(e)}")
            
    def start_status_updater(self):
        """Start periodic status updates"""
        self.update_next_run_display()
        self.frame.after(60000, self.start_status_updater)  # Update every minute
        
    def update_next_run_display(self):
        """Update the next run time display"""
        if not self.scheduling_enabled.get():
            self.next_run_label.config(text="Next Run: Not scheduled")
            return
            
        try:
            next_run = schedule.next_run()
            if next_run:
                time_until = next_run - datetime.now()
                days = time_until.days
                hours, remainder = divmod(time_until.seconds, 3600)
                minutes, _ = divmod(remainder, 60)
                
                if days > 0:
                    time_str = f"in {days} days, {hours} hours"
                elif hours > 0:
                    time_str = f"in {hours} hours, {minutes} minutes"
                else:
                    time_str = f"in {minutes} minutes"
                    
                self.next_run_label.config(text=f"Next Run: {next_run.strftime('%A %H:%M')} ({time_str})")
            else:
                self.next_run_label.config(text="Next Run: Not scheduled")
                
        except Exception as e:
            self.next_run_label.config(text="Next Run: Error calculating")
            
    def update_last_run_display(self):
        """Update the last run time display"""
        if self.last_run_time:
            time_str = self.last_run_time.strftime('%A %H:%M')
            # Add file count if available
            self.last_run_label.config(text=f"Last Run: {time_str}")
        else:
            self.last_run_label.config(text="Last Run: Never")
            
    def log_message(self, message):
        """Add message to schedule log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"{timestamp} - {message}\n"
        
        self.log_text.insert(tk.END, formatted_message)
        self.log_text.see(tk.END)
        self.log_text.update()
        
    def get_settings(self):
        """Get scheduling settings for saving"""
        return {
            'enabled': self.scheduling_enabled.get(),
            'schedule_type': self.schedule_type.get(),
            'schedule_time': self.schedule_time.get(),
            'schedule_day': self.schedule_day.get(),
            'facebook_delay_days': self.facebook_delay_days.get(),
            'auto_retry': self.auto_retry.get()
        }
        
    def load_settings(self, settings):
        """Load scheduling settings from configuration"""
        try:
            scheduling = settings.get('scheduling', {})
            
            self.scheduling_enabled.set(scheduling.get('enabled', False))
            self.schedule_type.set(scheduling.get('schedule_type', 'manual'))
            self.schedule_time.set(scheduling.get('schedule_time', '14:00'))
            self.schedule_day.set(scheduling.get('schedule_day', 'Monday'))
            self.facebook_delay_days.set(scheduling.get('facebook_delay_days', 30))
            self.auto_retry.set(scheduling.get('auto_retry', True))
            
            # If scheduling was enabled, restart it
            if self.scheduling_enabled.get() and self.schedule_type.get() != 'manual':
                self.enable_scheduling()
                
        except Exception as e:
            print(f"Error loading schedule settings: {e}")
            
    def get_facebook_delay_days(self):
        """Get Facebook posting delay in days"""
        return self.facebook_delay_days.get() 