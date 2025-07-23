"""
Upload Manager - Handles concurrent uploads and queue management
"""

import threading
import queue
import time
import os
from typing import Dict, List, Callable, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from core.file_manager import FileInfo
from core.status_tracker import StatusTracker

class UploadManager:
    """Manages concurrent file uploads to multiple platforms"""
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.upload_queue = queue.Queue()
        self.active_uploads = {}
        self.enabled_platforms = {}
        self.progress_callback = None
        self.status_tracker = StatusTracker()
        self.executor = None
        self.is_running = False
        self.abort_requested = False
        
    def set_enabled_platforms(self, platforms: Dict):
        """Set which platforms are enabled with their credentials"""
        self.enabled_platforms = platforms
        
    def set_progress_callback(self, callback: Callable):
        """Set callback function for progress updates"""
        self.progress_callback = callback
        
    def add_to_queue(self, file_info: FileInfo):
        """Add a file to the upload queue"""
        self.upload_queue.put(file_info)
        
    def add_single_file(self, file_path: str, folder_type: str):
        """Add a single file to the upload queue with minimal processing"""
        try:
            # Create basic file info
            filename = os.path.basename(file_path)
            base_name = os.path.splitext(file_path)[0]
            
            # Read metadata files
            title = self._read_text_file(base_name + "_TITLE.txt")
            description = self._read_text_file(base_name + "_DESCRIPTION.txt")
            short_desc = self._read_text_file(base_name + "_SHORT_DESC.txt")
            
            # Determine target platforms
            platforms = self._get_target_platforms_for_folder(folder_type, filename)
            
            # Create FileInfo object
            file_info = FileInfo(
                path=file_path,
                filename=filename,
                title=title or os.path.splitext(filename)[0],
                description=description,
                short_description=short_desc,
                platforms=platforms
            )
            
            # Add to queue
            self.upload_queue.put(file_info)
            
            self._send_progress("log", f"Added to queue: {filename}")
            self._send_progress("queue", self.upload_queue.qsize())
            
        except Exception as e:
            self._send_progress("log", f"Error adding file to queue: {str(e)}")
            
    def _read_text_file(self, file_path: str) -> str:
        """Read text file content, return empty string if file doesn't exist"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read().strip()
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
        return ""
        
    def _get_target_platforms_for_folder(self, folder_type: str, filename: str) -> List[str]:
        """Determine target platforms based on folder type and filename"""
        platforms = []
        
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
        
    def start_uploads(self):
        """Start processing the upload queue"""
        if self.is_running:
            return
            
        self.is_running = True
        self.abort_requested = False
        
        # Start upload processor in background thread
        upload_thread = threading.Thread(target=self._process_upload_queue, daemon=True)
        upload_thread.start()
        
    def _process_upload_queue(self):
        """Process files in the upload queue with concurrent uploads"""
        try:
            # Get all files from queue
            files_to_upload = []
            while not self.upload_queue.empty():
                try:
                    file_info = self.upload_queue.get_nowait()
                    files_to_upload.append(file_info)
                except queue.Empty:
                    break
                    
            if not files_to_upload:
                self._send_progress("log", "No files to upload")
                self._send_progress("complete", None)
                return
                
            self._send_progress("log", f"Starting upload of {len(files_to_upload)} files")
            self._send_progress("queue", len(files_to_upload))
            
            # Process uploads with thread pool
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                self.executor = executor
                
                # Submit all upload tasks
                future_to_file = {}
                for file_info in files_to_upload:
                    if self.abort_requested:
                        break
                        
                    future = executor.submit(self._upload_file, file_info)
                    future_to_file[future] = file_info
                    
                # Process completed uploads
                completed = 0
                for future in as_completed(future_to_file):
                    if self.abort_requested:
                        break
                        
                    file_info = future_to_file[future]
                    try:
                        result = future.result()
                        completed += 1
                        
                        remaining = len(files_to_upload) - completed
                        self._send_progress("queue", remaining)
                        
                        progress_percent = (completed / len(files_to_upload)) * 100
                        self._send_progress("progress", progress_percent)
                        
                        if result:
                            self._send_progress("log", f"Completed upload: {file_info.filename}")
                        else:
                            self._send_progress("log", f"Failed upload: {file_info.filename}")
                            
                    except Exception as e:
                        self._send_progress("log", f"Upload error for {file_info.filename}: {str(e)}")
                        
            self._send_progress("log", "All uploads completed")
            self._send_progress("complete", None)
            
        except Exception as e:
            self._send_progress("error", f"Upload manager error: {str(e)}")
            
        finally:
            self.is_running = False
            self.executor = None
            
    def _upload_file(self, file_info: FileInfo) -> bool:
        """Upload a single file to all its target platforms"""
        try:
            self._send_progress("current", f"{file_info.filename}")
            
            # Create status file to indicate upload in progress
            self.status_tracker.create_status_file(file_info.path, "UPLOADING")
            
            success_count = 0
            total_platforms = 0
            
            # Filter platforms based on what's enabled and what the file targets
            target_platforms = self._get_target_platforms(file_info)
            
            if not target_platforms:
                self._send_progress("log", f"No enabled platforms for {file_info.filename}")
                return False
                
            self._send_progress("log", f"Uploading {file_info.filename} to: {', '.join(target_platforms)}")
            
            # Upload to each target platform
            for platform in target_platforms:
                if self.abort_requested:
                    break
                    
                total_platforms += 1
                
                try:
                    success = self._upload_to_platform(file_info, platform)
                    if success:
                        success_count += 1
                        self._send_progress("log", f"✓ {platform}: {file_info.filename}")
                    else:
                        self._send_progress("log", f"✗ {platform}: {file_info.filename}")
                        
                except Exception as e:
                    self._send_progress("log", f"✗ {platform}: {file_info.filename} - {str(e)}")
                    
            # Update status based on results
            if success_count == total_platforms:
                self.status_tracker.create_status_file(file_info.path, "COMPLETED", 
                    f"Successfully uploaded to {success_count} platforms")
                return True
            elif success_count > 0:
                self.status_tracker.create_status_file(file_info.path, "PARTIAL", 
                    f"Uploaded to {success_count}/{total_platforms} platforms")
                return False
            else:
                self.status_tracker.create_status_file(file_info.path, "ERROR", 
                    "Failed to upload to any platform")
                return False
                
        except Exception as e:
            self.status_tracker.create_status_file(file_info.path, "ERROR", str(e))
            return False
            
    def _get_target_platforms(self, file_info: FileInfo) -> List[str]:
        """Get list of platforms this file should be uploaded to"""
        target_platforms = []
        
        for platform in file_info.platforms:
            # Map internal platform names to enabled platform names
            platform_key = platform
            if platform == 'youtube_shorts':
                platform_key = 'youtube'  # YouTube Shorts uses same API as regular YouTube
                
            if platform_key in self.enabled_platforms:
                target_platforms.append(platform)
                
        return target_platforms
        
    def _upload_to_platform(self, file_info: FileInfo, platform: str) -> bool:
        """Upload file to a specific platform"""
        try:
            if platform == 'cloudflare':
                return self._upload_to_cloudflare(file_info)
            elif platform == 'youtube':
                return self._upload_to_youtube(file_info, is_short=False)
            elif platform == 'youtube_shorts':
                return self._upload_to_youtube(file_info, is_short=True)
            elif platform == 'pinterest':
                return self._upload_to_pinterest(file_info)
            elif platform == 'facebook':
                return self._upload_to_facebook(file_info)
            else:
                return False
                
        except Exception as e:
            self._send_progress("log", f"Platform upload error ({platform}): {str(e)}")
            return False
            
    def _upload_to_cloudflare(self, file_info: FileInfo) -> bool:
        """Upload file to CloudFlare Stream"""
        try:
            from api.cloudflare import CloudFlareAPI
            
            creds = self.enabled_platforms['cloudflare']
            api = CloudFlareAPI(creds['api_token'], creds['account_id'])
            
            result = api.upload_video(file_info.path, file_info.title)
            return result is not None
            
        except ImportError:
            self._send_progress("log", "CloudFlare API not available")
            return False
        except Exception as e:
            self._send_progress("log", f"CloudFlare upload error: {str(e)}")
            return False
            
    def _upload_to_youtube(self, file_info: FileInfo, is_short: bool = False) -> bool:
        """Upload file to YouTube"""
        try:
            from api.youtube import YouTubeAPI
            
            creds = self.enabled_platforms['youtube']
            api = YouTubeAPI(creds['client_id'], creds['client_secret'])
            
            # Set refresh token if available
            if creds.get('refresh_token'):
                api.set_refresh_token(creds['refresh_token'])
                
            # Limit title length for YouTube
            title = file_info.title[:100]  # YouTube title limit
            description = file_info.description or file_info.short_description
            
            result = api.upload_video(file_info.path, title, description, is_short=is_short)
            return result is not None
            
        except ImportError:
            self._send_progress("log", "YouTube API not available")
            return False
        except Exception as e:
            self._send_progress("log", f"YouTube upload error: {str(e)}")
            return False
            
    def _upload_to_pinterest(self, file_info: FileInfo) -> bool:
        """Upload file to Pinterest"""
        try:
            from api.pinterest import PinterestAPI
            
            creds = self.enabled_platforms['pinterest']
            api = PinterestAPI(creds['access_token'])
            
            # Format title for Pinterest
            pinterest_title = self._format_pinterest_title(file_info.title)
            description = file_info.short_description or file_info.description
            
            result = api.create_pin(file_info.path, pinterest_title, description)
            return result is not None
            
        except ImportError:
            self._send_progress("log", "Pinterest API not available")
            return False
        except Exception as e:
            self._send_progress("log", f"Pinterest upload error: {str(e)}")
            return False
            
    def _upload_to_facebook(self, file_info: FileInfo) -> bool:
        """Upload file to Facebook (scheduled)"""
        try:
            from api.facebook import FacebookAPI
            from gui.schedule_tab import ScheduleTab
            
            creds = self.enabled_platforms['facebook']
            api = FacebookAPI(creds['page_token'], creds['group_id'])
            
            # Calculate schedule time (30 days in future by default)
            schedule_time = datetime.now() + timedelta(days=30)
            
            # Create message for Facebook post
            message = f"{file_info.title}\n\n{file_info.description or file_info.short_description}"
            
            result = api.schedule_post(file_info.path, message, schedule_time)
            return result is not None
            
        except ImportError:
            self._send_progress("log", "Facebook API not available")
            return False
        except Exception as e:
            self._send_progress("log", f"Facebook upload error: {str(e)}")
            return False
            
    def _format_pinterest_title(self, title: str) -> str:
        """Format title for Pinterest with hashtags and keywords"""
        # Add fitness-related hashtags
        hashtags = [
            "#fitness", "#workout", "#training", "#exercise", 
            "#health", "#gym", "#strength", "#motivation"
        ]
        
        # Limit title length and add hashtags
        formatted_title = title[:80]  # Leave room for hashtags
        formatted_title += " " + " ".join(hashtags[:5])  # Add first 5 hashtags
        
        return formatted_title
        
    def abort_all(self):
        """Abort all running uploads"""
        self.abort_requested = True
        
        if self.executor:
            self.executor.shutdown(wait=False)
            
        # Clear the queue
        while not self.upload_queue.empty():
            try:
                self.upload_queue.get_nowait()
            except queue.Empty:
                break
                
        self.is_running = False
        self._send_progress("log", "Upload process aborted")
        
    def get_queue_size(self) -> int:
        """Get current queue size"""
        return self.upload_queue.qsize()
        
    def get_active_count(self) -> int:
        """Get number of active uploads"""
        return len(self.active_uploads)
        
    def _send_progress(self, message_type: str, data):
        """Send progress update via callback"""
        if self.progress_callback:
            try:
                self.progress_callback(message_type, data)
            except Exception as e:
                print(f"Progress callback error: {e}")
                
    def get_upload_stats(self) -> Dict:
        """Get upload statistics"""
        return {
            'queue_size': self.get_queue_size(),
            'active_uploads': self.get_active_count(),
            'max_concurrent': self.max_concurrent,
            'is_running': self.is_running,
            'enabled_platforms': list(self.enabled_platforms.keys())
        } 