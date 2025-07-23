"""
Settings Tab - Platform and API configuration for Video Upload Automation
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import json

class SettingsTab:
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.frame = ttk.Frame(parent)
        
        # Platform enable/disable variables
        self.cloudflare_enabled = tk.BooleanVar(value=True)
        self.youtube_enabled = tk.BooleanVar(value=True)
        self.pinterest_enabled = tk.BooleanVar(value=False)
        self.facebook_enabled = tk.BooleanVar(value=True)
        
        # API credential variables
        self.cloudflare_token = tk.StringVar()
        self.cloudflare_account = tk.StringVar()
        
        self.youtube_client_id = tk.StringVar()
        self.youtube_client_secret = tk.StringVar()
        self.youtube_refresh_token = tk.StringVar()
        
        self.pinterest_token = tk.StringVar()
        self.pinterest_board_id = tk.StringVar()
        
        self.facebook_token = tk.StringVar()
        self.facebook_group_id = tk.StringVar()
        
        # General settings variables
        self.max_concurrent = tk.IntVar(value=3)
        self.retry_attempts = tk.IntVar(value=3)
        self.upload_timeout = tk.IntVar(value=300)
        
        # Scanning settings variables
        self.stability_timeout = tk.IntVar(value=3)
        self.recheck_interval = tk.IntVar(value=5)
        self.max_attempts = tk.IntVar(value=10)
        
        # Create GUI components
        self.create_widgets()
        
    def create_widgets(self):
        """Create all GUI widgets for the settings tab"""
        # Create scrollable frame
        canvas = tk.Canvas(self.frame)
        scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Platform Configuration Section
        platform_frame = ttk.LabelFrame(scrollable_frame, text="Platform Configuration", padding=10)
        platform_frame.pack(fill='x', pady=5)
        
        self.create_cloudflare_section(platform_frame)
        self.create_youtube_section(platform_frame)
        self.create_pinterest_section(platform_frame)
        self.create_facebook_section(platform_frame)
        
        # General Settings Section
        general_frame = ttk.LabelFrame(scrollable_frame, text="General Settings", padding=10)
        general_frame.pack(fill='x', pady=10)
        
        self.create_general_section(general_frame)
        
        # Scanning Settings Section
        scanning_frame = ttk.LabelFrame(scrollable_frame, text="Auto-Scanning Settings", padding=10)
        scanning_frame.pack(fill='x', pady=10)
        
        self.create_scanning_section(scanning_frame)
        
        # Action buttons
        button_frame = ttk.Frame(scrollable_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Save Settings", command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Load Defaults", command=self.load_defaults).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Test All APIs", command=self.test_all_apis).pack(side='left', padx=5)
        
    def create_cloudflare_section(self, parent):
        """Create CloudFlare configuration section"""
        cf_frame = ttk.Frame(parent)
        cf_frame.pack(fill='x', pady=5)
        
        # Enable checkbox
        cf_check = ttk.Checkbutton(cf_frame, text="CloudFlare Stream", 
                                 variable=self.cloudflare_enabled)
        cf_check.pack(anchor='w')
        
        # API fields
        fields_frame = ttk.Frame(cf_frame)
        fields_frame.pack(fill='x', padx=20, pady=5)
        
        # API Token
        token_frame = ttk.Frame(fields_frame)
        token_frame.pack(fill='x', pady=2)
        ttk.Label(token_frame, text="API Token:", width=15).pack(side='left')
        token_entry = ttk.Entry(token_frame, textvariable=self.cloudflare_token, width=40, show='*')
        token_entry.pack(side='left', padx=5)
        ttk.Button(token_frame, text="Test", 
                  command=lambda: self.test_api('cloudflare')).pack(side='left', padx=5)
        
        # Account ID
        account_frame = ttk.Frame(fields_frame)
        account_frame.pack(fill='x', pady=2)
        ttk.Label(account_frame, text="Account ID:", width=15).pack(side='left')
        ttk.Entry(account_frame, textvariable=self.cloudflare_account, width=40).pack(side='left', padx=5)
        
    def create_youtube_section(self, parent):
        """Create YouTube configuration section"""
        yt_frame = ttk.Frame(parent)
        yt_frame.pack(fill='x', pady=5)
        
        # Enable checkbox
        yt_check = ttk.Checkbutton(yt_frame, text="YouTube", 
                                 variable=self.youtube_enabled)
        yt_check.pack(anchor='w')
        
        # API fields
        fields_frame = ttk.Frame(yt_frame)
        fields_frame.pack(fill='x', padx=20, pady=5)
        
        # Client ID
        client_frame = ttk.Frame(fields_frame)
        client_frame.pack(fill='x', pady=2)
        ttk.Label(client_frame, text="Client ID:", width=15).pack(side='left')
        ttk.Entry(client_frame, textvariable=self.youtube_client_id, width=40).pack(side='left', padx=5)
        ttk.Button(client_frame, text="Auth", 
                  command=lambda: self.youtube_auth()).pack(side='left', padx=5)
        
        # Client Secret
        secret_frame = ttk.Frame(fields_frame)
        secret_frame.pack(fill='x', pady=2)
        ttk.Label(secret_frame, text="Client Secret:", width=15).pack(side='left')
        ttk.Entry(secret_frame, textvariable=self.youtube_client_secret, width=40, show='*').pack(side='left', padx=5)
        
        # Refresh Token
        refresh_frame = ttk.Frame(fields_frame)
        refresh_frame.pack(fill='x', pady=2)
        ttk.Label(refresh_frame, text="Refresh Token:", width=15).pack(side='left')
        refresh_entry = ttk.Entry(refresh_frame, textvariable=self.youtube_refresh_token, 
                                width=40, state='readonly')
        refresh_entry.pack(side='left', padx=5)
        ttk.Label(refresh_frame, text="Auto-generated").pack(side='left', padx=5)
        
    def create_pinterest_section(self, parent):
        """Create Pinterest configuration section"""
        pin_frame = ttk.Frame(parent)
        pin_frame.pack(fill='x', pady=5)
        
        # Enable checkbox
        pin_check = ttk.Checkbutton(pin_frame, text="Pinterest", 
                                  variable=self.pinterest_enabled)
        pin_check.pack(anchor='w')
        
        # API fields
        fields_frame = ttk.Frame(pin_frame)
        fields_frame.pack(fill='x', padx=20, pady=5)
        
        # Access Token
        token_frame = ttk.Frame(fields_frame)
        token_frame.pack(fill='x', pady=2)
        ttk.Label(token_frame, text="Access Token:", width=15).pack(side='left')
        token_entry = ttk.Entry(token_frame, textvariable=self.pinterest_token, width=40, show='*')
        token_entry.pack(side='left', padx=5)
        ttk.Button(token_frame, text="Test", 
                  command=lambda: self.test_api('pinterest')).pack(side='left', padx=5)
        
        # Board ID
        board_frame = ttk.Frame(fields_frame)
        board_frame.pack(fill='x', pady=2)
        ttk.Label(board_frame, text="Board ID:", width=15).pack(side='left')
        ttk.Entry(board_frame, textvariable=self.pinterest_board_id, width=40).pack(side='left', padx=5)
        
    def create_facebook_section(self, parent):
        """Create Facebook configuration section"""
        fb_frame = ttk.Frame(parent)
        fb_frame.pack(fill='x', pady=5)
        
        # Enable checkbox
        fb_check = ttk.Checkbutton(fb_frame, text="Facebook", 
                                 variable=self.facebook_enabled)
        fb_check.pack(anchor='w')
        
        # API fields
        fields_frame = ttk.Frame(fb_frame)
        fields_frame.pack(fill='x', padx=20, pady=5)
        
        # Page Token
        token_frame = ttk.Frame(fields_frame)
        token_frame.pack(fill='x', pady=2)
        ttk.Label(token_frame, text="Access Token:", width=15).pack(side='left')
        token_entry = ttk.Entry(token_frame, textvariable=self.facebook_token, width=35, show='*')
        token_entry.pack(side='left', padx=5)
        ttk.Button(token_frame, text="Test", 
                  command=lambda: self.test_api('facebook')).pack(side='left', padx=2)
        ttk.Button(token_frame, text="Help", 
                  command=self.show_facebook_help).pack(side='left', padx=2)
        
        # Group ID
        group_frame = ttk.Frame(fields_frame)
        group_frame.pack(fill='x', pady=2)
        ttk.Label(group_frame, text="Group ID:", width=15).pack(side='left')
        ttk.Entry(group_frame, textvariable=self.facebook_group_id, width=40).pack(side='left', padx=5)
        
        # Permissions info
        info_frame = ttk.Frame(fields_frame)
        info_frame.pack(fill='x', pady=(5, 0))
        info_label = ttk.Label(info_frame, text="ℹ️ Requires: publish_to_groups + groups_access_member_info permissions", 
                              font=('TkDefaultFont', 8), foreground='#666666')
        info_label.pack(anchor='w')
        
    def create_general_section(self, parent):
        """Create general settings section"""
        # Max Concurrent Uploads
        concurrent_frame = ttk.Frame(parent)
        concurrent_frame.pack(fill='x', pady=2)
        ttk.Label(concurrent_frame, text="Max Concurrent Uploads:", width=25).pack(side='left')
        concurrent_combo = ttk.Combobox(concurrent_frame, textvariable=self.max_concurrent, 
                                      values=[1, 2, 3, 4, 5], width=10, state='readonly')
        concurrent_combo.pack(side='left', padx=5)
        
        # Retry Attempts
        retry_frame = ttk.Frame(parent)
        retry_frame.pack(fill='x', pady=2)
        ttk.Label(retry_frame, text="Retry Attempts:", width=25).pack(side='left')
        retry_combo = ttk.Combobox(retry_frame, textvariable=self.retry_attempts, 
                                 values=[1, 2, 3, 4, 5], width=10, state='readonly')
        retry_combo.pack(side='left', padx=5)
        
        # Upload Timeout
        timeout_frame = ttk.Frame(parent)
        timeout_frame.pack(fill='x', pady=2)
        ttk.Label(timeout_frame, text="Upload Timeout (seconds):", width=25).pack(side='left')
        ttk.Entry(timeout_frame, textvariable=self.upload_timeout, width=10).pack(side='left', padx=5)
        
    def create_scanning_section(self, parent):
        """Create scanning settings section"""
        # File stability timeout
        stability_frame = ttk.Frame(parent)
        stability_frame.pack(fill='x', pady=2)
        ttk.Label(stability_frame, text="File stability timeout:", width=25).pack(side='left')
        stability_spin = ttk.Spinbox(stability_frame, from_=1, to=10, width=10, 
                                    textvariable=self.stability_timeout)
        stability_spin.pack(side='left', padx=5)
        ttk.Label(stability_frame, text="seconds").pack(side='left', padx=5)
        
        # Text file check interval
        recheck_frame = ttk.Frame(parent)
        recheck_frame.pack(fill='x', pady=2)
        ttk.Label(recheck_frame, text="Text file recheck interval:", width=25).pack(side='left')
        recheck_spin = ttk.Spinbox(recheck_frame, from_=1, to=30, width=10, 
                                  textvariable=self.recheck_interval)
        recheck_spin.pack(side='left', padx=5)
        ttk.Label(recheck_frame, text="minutes").pack(side='left', padx=5)
        
        # Max recheck attempts
        attempts_frame = ttk.Frame(parent)
        attempts_frame.pack(fill='x', pady=2)
        ttk.Label(attempts_frame, text="Max recheck attempts:", width=25).pack(side='left')
        attempts_spin = ttk.Spinbox(attempts_frame, from_=1, to=50, width=10, 
                                   textvariable=self.max_attempts)
        attempts_spin.pack(side='left', padx=5)
        ttk.Label(attempts_frame, text="attempts").pack(side='left', padx=5)
        
    def test_api(self, platform):
        """Test API connection for a specific platform"""
        def test_worker():
            import sys
            from io import StringIO
            
            # Capture print output to show detailed error messages
            old_stdout = sys.stdout
            captured_output = StringIO()
            sys.stdout = captured_output
            
            try:
                if platform == 'cloudflare':
                    from api.cloudflare import CloudFlareAPI
                    api = CloudFlareAPI(self.cloudflare_token.get(), self.cloudflare_account.get())
                    result = api.test_connection()
                    
                elif platform == 'pinterest':
                    from api.pinterest import PinterestAPI
                    api = PinterestAPI(self.pinterest_token.get())
                    result = api.test_connection()
                    
                elif platform == 'facebook':
                    from api.facebook import FacebookAPI
                    api = FacebookAPI(self.facebook_token.get(), self.facebook_group_id.get())
                    result = api.test_connection()
                    
                else:
                    result = False
                
                # Restore stdout
                sys.stdout = old_stdout
                output_messages = captured_output.getvalue()
                
                if result:
                    success_msg = f"{platform.title()} API connection successful!"
                    if output_messages.strip():
                        success_msg += f"\n\nDetails:\n{output_messages.strip()}"
                    messagebox.showinfo("Success", success_msg)
                else:
                    error_msg = f"{platform.title()} API connection failed!"
                    if output_messages.strip():
                        error_msg += f"\n\nDetails:\n{output_messages.strip()}"
                    else:
                        error_msg += "\n\nPlease check your credentials and try again."
                    messagebox.showerror("Error", error_msg)
                    
            except Exception as e:
                # Restore stdout in case of exception
                sys.stdout = old_stdout
                output_messages = captured_output.getvalue()
                
                error_msg = f"{platform.title()} API test failed: {str(e)}"
                if output_messages.strip():
                    error_msg += f"\n\nDetails:\n{output_messages.strip()}"
                messagebox.showerror("Error", error_msg)
                
        # Run test in background thread
        test_thread = threading.Thread(target=test_worker, daemon=True)
        test_thread.start()
        
    def youtube_auth(self):
        """Handle YouTube OAuth authentication"""
        try:
            from api.youtube import YouTubeAPI
            api = YouTubeAPI(self.youtube_client_id.get(), self.youtube_client_secret.get())
            refresh_token = api.authenticate()
            
            if refresh_token:
                self.youtube_refresh_token.set(refresh_token)
                messagebox.showinfo("Success", "YouTube authentication successful!")
            else:
                messagebox.showerror("Error", "YouTube authentication failed!")
                
        except Exception as e:
            messagebox.showerror("Error", f"YouTube authentication error: {str(e)}")
            
    def test_all_apis(self):
        """Test all enabled API connections"""
        def test_all_worker():
            enabled_platforms = self.get_enabled_platforms()
            results = []
            
            for platform in enabled_platforms:
                try:
                    if platform == 'cloudflare':
                        self.test_api('cloudflare')
                    elif platform == 'youtube':
                        # YouTube requires special handling for OAuth
                        results.append(f"YouTube: OAuth token present")
                    elif platform == 'pinterest':
                        self.test_api('pinterest')
                    elif platform == 'facebook':
                        self.test_api('facebook')
                except Exception as e:
                    results.append(f"{platform}: {str(e)}")
                    
        test_thread = threading.Thread(target=test_all_worker, daemon=True)
        test_thread.start()
    
    def show_facebook_help(self):
        """Show Facebook permissions help dialog"""
        help_window = tk.Toplevel(self.frame)
        help_window.title("Facebook API Setup Help")
        help_window.geometry("700x600")
        help_window.resizable(True, True)
        
        # Make it modal
        help_window.transient(self.frame)
        help_window.grab_set()
        
        # Create scrollable text widget
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Text widget with scrollbar
        text_widget = tk.Text(text_frame, wrap='word', font=('Consolas', 9), padx=10, pady=10)
        scrollbar = ttk.Scrollbar(text_frame, orient='vertical', command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Help content
        help_text = """📋 FACEBOOK API PERMISSIONS SETUP GUIDE

🔥 PROBLEM: Your Facebook token only has READ permissions!
✅ SOLUTION: Get a token with WRITE permissions for video uploads.

═══════════════════════════════════════════════════════════════

🔑 REQUIRED PERMISSIONS:
   • publish_to_groups - Post content to Facebook groups
   • groups_access_member_info - Access group information

📱 STEP-BY-STEP INSTRUCTIONS:

1. 📖 Go to Facebook Graph API Explorer:
   https://developers.facebook.com/tools/explorer/

2. 🏗️ Create or Select Your App:
   • If you don't have an app, create one at:
     https://developers.facebook.com/apps/
   • Select your app from the dropdown in Graph API Explorer

3. 🎯 Generate Access Token:
   • Click "Generate Access Token"
   • Add these specific permissions:
     ✓ publish_to_groups
     ✓ groups_access_member_info
   
4. 👤 Important User Requirements:
   • You must be logged in as a user who is:
     ✓ A member of the target Facebook group
     ✓ Has permission to post in the group
     ✓ Preferably an admin/moderator of the group

5. 📋 Copy the Generated Token:
   • Copy the access token from Graph API Explorer
   • Paste it into the "Access Token" field above

═══════════════════════════════════════════════════════════════

🛠️ ALTERNATIVE: PAGE ACCESS TOKEN

If you want to post as a Facebook Page:

1. Get a Page Access Token instead of User Access Token
2. Required permissions:
   • pages_manage_posts
   • pages_read_engagement
3. The page must be connected to/admin of the group

═══════════════════════════════════════════════════════════════

⚠️ COMMON ISSUES:

❌ "Access forbidden" error:
   → Your token lacks write permissions
   → Regenerate token with publish_to_groups permission

❌ "Group not found" error:
   → Check your Group ID is correct
   → Make sure you're a member of the group

❌ "Upload forbidden" error:
   → Group settings may restrict video uploads
   → You may need admin approval for posts
   → Check if you're banned/restricted in the group

❌ "Invalid token" error:
   → Token may have expired
   → Regenerate a new access token

═══════════════════════════════════════════════════════════════

🔍 HOW TO FIND YOUR GROUP ID:

1. Go to your Facebook group
2. Look at the URL: facebook.com/groups/[GROUP_ID]
3. Or use Graph API Explorer:
   • Search: me/groups
   • Find your group in the results

═══════════════════════════════════════════════════════════════

💡 TESTING TIPS:

✅ Use the "Test" button to verify:
   • Token permissions are correct
   • You can access the group
   • Video upload permissions work

✅ If test passes, you're ready to upload videos!

═══════════════════════════════════════════════════════════════

🔐 SECURITY NOTE:

• Keep your access token private
• Tokens can expire - you may need to regenerate them
• Use User tokens for personal posting
• Use Page tokens for business/page posting

═══════════════════════════════════════════════════════════════

Need more help? Check Facebook's Developer Documentation:
https://developers.facebook.com/docs/graph-api/reference/group/videos/
"""
        
        # Insert help text
        text_widget.insert('1.0', help_text)
        text_widget.config(state='disabled')  # Make read-only
        
        # Close button
        button_frame = ttk.Frame(help_window)
        button_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="Close", command=help_window.destroy).pack(side='right')
        ttk.Button(button_frame, text="Open Graph API Explorer", 
                  command=lambda: self.open_url("https://developers.facebook.com/tools/explorer/")).pack(side='right', padx=(0, 5))
        
        # Center the window
        help_window.update_idletasks()
        x = (help_window.winfo_screenwidth() // 2) - (help_window.winfo_width() // 2)
        y = (help_window.winfo_screenheight() // 2) - (help_window.winfo_height() // 2)
        help_window.geometry(f"+{x}+{y}")
    
    def open_url(self, url):
        """Open URL in default browser"""
        import webbrowser
        webbrowser.open(url)
        
    def save_settings(self):
        """Save current settings"""
        try:
            self.app.save_settings()
            messagebox.showinfo("Success", "Settings saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def load_defaults(self):
        """Load default settings"""
        self.cloudflare_enabled.set(True)
        self.youtube_enabled.set(True)
        self.pinterest_enabled.set(False)
        self.facebook_enabled.set(True)
        
        self.max_concurrent.set(3)
        self.retry_attempts.set(3)
        self.upload_timeout.set(300)
        
        # Scanning defaults
        self.stability_timeout.set(3)
        self.recheck_interval.set(5)
        self.max_attempts.set(10)
        
        # Clear credentials
        self.cloudflare_token.set("")
        self.cloudflare_account.set("")
        self.youtube_client_id.set("")
        self.youtube_client_secret.set("")
        self.youtube_refresh_token.set("")
        self.pinterest_token.set("")
        self.pinterest_board_id.set("")
        self.facebook_token.set("")
        self.facebook_group_id.set("")
        
    def get_enabled_platforms(self):
        """Get dictionary of enabled platforms with their credentials"""
        enabled = {}
        
        if self.cloudflare_enabled.get() and self.cloudflare_token.get():
            enabled['cloudflare'] = {
                'api_token': self.cloudflare_token.get(),
                'account_id': self.cloudflare_account.get()
            }
            
        if self.youtube_enabled.get() and self.youtube_client_id.get():
            enabled['youtube'] = {
                'client_id': self.youtube_client_id.get(),
                'client_secret': self.youtube_client_secret.get(),
                'refresh_token': self.youtube_refresh_token.get()
            }
            
        if self.pinterest_enabled.get() and self.pinterest_token.get():
            enabled['pinterest'] = {
                'access_token': self.pinterest_token.get(),
                'board_id': self.pinterest_board_id.get()
            }
            
        if self.facebook_enabled.get() and self.facebook_token.get():
            enabled['facebook'] = {
                'page_token': self.facebook_token.get(),
                'group_id': self.facebook_group_id.get()
            }
            
        return enabled
        
    def get_settings(self):
        """Get platform settings for saving"""
        return {
            'cloudflare': {
                'enabled': self.cloudflare_enabled.get(),
                'api_token': self.cloudflare_token.get(),
                'account_id': self.cloudflare_account.get()
            },
            'youtube': {
                'enabled': self.youtube_enabled.get(),
                'client_id': self.youtube_client_id.get(),
                'client_secret': self.youtube_client_secret.get(),
                'refresh_token': self.youtube_refresh_token.get()
            },
            'pinterest': {
                'enabled': self.pinterest_enabled.get(),
                'access_token': self.pinterest_token.get(),
                'board_id': self.pinterest_board_id.get()
            },
            'facebook': {
                'enabled': self.facebook_enabled.get(),
                'page_token': self.facebook_token.get(),
                'group_id': self.facebook_group_id.get()
            }
        }
        
    def get_general_settings(self):
        """Get general settings for saving"""
        return {
            'max_concurrent': self.max_concurrent.get(),
            'retry_attempts': self.retry_attempts.get(),
            'upload_timeout': self.upload_timeout.get(),
            'scanning': {
                'stability_timeout': self.stability_timeout.get(),
                'recheck_interval': self.recheck_interval.get(),
                'max_attempts': self.max_attempts.get()
            }
        }
        
    def get_max_concurrent(self):
        """Get max concurrent uploads setting"""
        return self.max_concurrent.get()
        
    def get_scanning_settings(self):
        """Get scanning settings"""
        return {
            'stability_timeout': self.stability_timeout.get(),
            'recheck_interval': self.recheck_interval.get(),
            'max_attempts': self.max_attempts.get()
        }
        
    def load_settings(self, settings):
        """Load settings from configuration"""
        try:
            platforms = settings.get('platforms', {})
            
            # CloudFlare
            cf = platforms.get('cloudflare', {})
            self.cloudflare_enabled.set(cf.get('enabled', True))
            self.cloudflare_token.set(cf.get('api_token', ''))
            self.cloudflare_account.set(cf.get('account_id', ''))
            
            # YouTube
            yt = platforms.get('youtube', {})
            self.youtube_enabled.set(yt.get('enabled', True))
            self.youtube_client_id.set(yt.get('client_id', ''))
            self.youtube_client_secret.set(yt.get('client_secret', ''))
            self.youtube_refresh_token.set(yt.get('refresh_token', ''))
            
            # Pinterest
            pin = platforms.get('pinterest', {})
            self.pinterest_enabled.set(pin.get('enabled', False))
            self.pinterest_token.set(pin.get('access_token', ''))
            self.pinterest_board_id.set(pin.get('board_id', ''))
            
            # Facebook
            fb = platforms.get('facebook', {})
            self.facebook_enabled.set(fb.get('enabled', True))
            self.facebook_token.set(fb.get('page_token', ''))
            self.facebook_group_id.set(fb.get('group_id', ''))
            
            # General settings
            general = settings.get('general', {})
            self.max_concurrent.set(general.get('max_concurrent', 3))
            self.retry_attempts.set(general.get('retry_attempts', 3))
            self.upload_timeout.set(general.get('upload_timeout', 300))
            
            # Scanning settings
            scanning = general.get('scanning', {})
            self.stability_timeout.set(scanning.get('stability_timeout', 3))
            self.recheck_interval.set(scanning.get('recheck_interval', 5))
            self.max_attempts.set(scanning.get('max_attempts', 10))
            
        except Exception as e:
            print(f"Error loading settings: {e}") 