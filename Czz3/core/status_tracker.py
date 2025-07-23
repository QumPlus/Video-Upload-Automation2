"""
Status Tracker - Manages upload status files and progress tracking
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

class StatusTracker:
    """Tracks upload status for video files using status files"""
    
    def __init__(self):
        self.status_types = {
            'UPLOADING': 'Upload in progress',
            'COMPLETED': 'Upload completed successfully',
            'PARTIAL': 'Partial upload (some platforms failed)',
            'ERROR': 'Upload failed',
            'CANCELLED': 'Upload cancelled by user'
        }
        
    def create_status_file(self, file_path: str, status: str, content: str = ""):
        """Create a status file for a video file"""
        try:
            video_file = Path(file_path)
            base_name = video_file.stem
            parent_dir = video_file.parent
            
            # Clean up any existing status files first
            self.cleanup_status_files(file_path)
            
            # Create new status file
            status_file = parent_dir / f"{base_name}_{status}.txt"
            
            # Create status content
            status_content = {
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'file': video_file.name,
                'message': content,
                'details': self.status_types.get(status, 'Unknown status')
            }
            
            # Write status file
            with open(status_file, 'w', encoding='utf-8') as f:
                if content:
                    f.write(f"{status} - {content}\n")
                else:
                    f.write(f"{status}\n")
                f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"File: {video_file.name}\n")
                
            return True
            
        except Exception as e:
            print(f"Error creating status file: {e}")
            return False
            
    def update_status(self, file_path: str, status: str, platform: str, message: str):
        """Update status file with platform-specific progress"""
        try:
            video_file = Path(file_path)
            base_name = video_file.stem
            parent_dir = video_file.parent
            
            # Find existing status file
            status_file = None
            for status_type in self.status_types.keys():
                potential_file = parent_dir / f"{base_name}_{status_type}.txt"
                if potential_file.exists():
                    status_file = potential_file
                    break
                    
            if not status_file:
                # Create new status file if none exists
                status_file = parent_dir / f"{base_name}_{status}.txt"
                
            # Read existing content
            existing_content = ""
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    existing_content = f.read()
                    
            # Append new status update
            timestamp = datetime.now().strftime('%H:%M:%S')
            new_line = f"{timestamp} - {platform}: {message}\n"
            
            # Write updated content
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(existing_content)
                f.write(new_line)
                
            return True
            
        except Exception as e:
            print(f"Error updating status file: {e}")
            return False
            
    def get_file_status(self, file_path: str) -> Optional[Dict]:
        """Get current status of a file"""
        try:
            video_file = Path(file_path)
            base_name = video_file.stem
            parent_dir = video_file.parent
            
            # Check for status files
            for status_type in self.status_types.keys():
                status_file = parent_dir / f"{base_name}_{status_type}.txt"
                if status_file.exists():
                    # Read status file content
                    with open(status_file, 'r', encoding='utf-8') as f:
                        content = f.read().strip()
                        
                    # Get file modification time
                    mod_time = datetime.fromtimestamp(status_file.stat().st_mtime)
                    
                    return {
                        'status': status_type,
                        'description': self.status_types[status_type],
                        'content': content,
                        'timestamp': mod_time.isoformat(),
                        'file_path': str(status_file)
                    }
                    
            # No status file found
            return {
                'status': 'PENDING',
                'description': 'Ready for upload',
                'content': '',
                'timestamp': datetime.now().isoformat(),
                'file_path': None
            }
            
        except Exception as e:
            print(f"Error getting file status: {e}")
            return None
            
    def cleanup_status_files(self, file_path: str):
        """Remove all status files for a video file"""
        try:
            video_file = Path(file_path)
            base_name = video_file.stem
            parent_dir = video_file.parent
            
            for status_type in self.status_types.keys():
                status_file = parent_dir / f"{base_name}_{status_type}.txt"
                if status_file.exists():
                    status_file.unlink()
                    
            return True
            
        except Exception as e:
            print(f"Error cleaning up status files: {e}")
            return False
            
    def get_all_status_files(self, folder_path: str) -> Dict[str, Dict]:
        """Get status information for all files in a folder"""
        status_info = {}
        
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return status_info
                
            # Find all status files
            for status_file in folder.rglob('*_*.txt'):
                filename = status_file.name
                
                # Check if it's a status file
                for status_type in self.status_types.keys():
                    if filename.endswith(f'_{status_type}.txt'):
                        # Extract original video filename
                        base_name = filename.replace(f'_{status_type}.txt', '')
                        
                        # Read status content
                        with open(status_file, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            
                        mod_time = datetime.fromtimestamp(status_file.stat().st_mtime)
                        
                        status_info[base_name] = {
                            'status': status_type,
                            'description': self.status_types[status_type],
                            'content': content,
                            'timestamp': mod_time.isoformat(),
                            'file_path': str(status_file)
                        }
                        break
                        
        except Exception as e:
            print(f"Error getting status files: {e}")
            
        return status_info
        
    def get_upload_statistics(self, folder_path: str) -> Dict:
        """Get upload statistics for a folder"""
        stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'uploading': 0,
            'pending': 0,
            'partial': 0
        }
        
        try:
            status_info = self.get_all_status_files(folder_path)
            
            stats['total'] = len(status_info)
            
            for file_status in status_info.values():
                status = file_status['status']
                if status == 'COMPLETED':
                    stats['completed'] += 1
                elif status == 'ERROR':
                    stats['failed'] += 1
                elif status == 'UPLOADING':
                    stats['uploading'] += 1
                elif status == 'PARTIAL':
                    stats['partial'] += 1
                else:
                    stats['pending'] += 1
                    
        except Exception as e:
            print(f"Error getting upload statistics: {e}")
            
        return stats
        
    def mark_file_completed(self, file_path: str, platforms: list, details: str = ""):
        """Mark a file as completed with platform details"""
        try:
            platform_list = ", ".join(platforms)
            message = f"Successfully uploaded to: {platform_list}"
            if details:
                message += f"\nDetails: {details}"
                
            return self.create_status_file(file_path, "COMPLETED", message)
            
        except Exception as e:
            print(f"Error marking file completed: {e}")
            return False
            
    def mark_file_failed(self, file_path: str, error_message: str):
        """Mark a file as failed with error details"""
        try:
            return self.create_status_file(file_path, "ERROR", error_message)
            
        except Exception as e:
            print(f"Error marking file failed: {e}")
            return False
            
    def mark_file_partial(self, file_path: str, successful_platforms: list, failed_platforms: list):
        """Mark a file as partially uploaded"""
        try:
            success_list = ", ".join(successful_platforms)
            failed_list = ", ".join(failed_platforms)
            message = f"Successful: {success_list}\nFailed: {failed_list}"
            
            return self.create_status_file(file_path, "PARTIAL", message)
            
        except Exception as e:
            print(f"Error marking file partial: {e}")
            return False
            
    def is_file_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed (completed or failed)"""
        try:
            status = self.get_file_status(file_path)
            if status and status['status'] in ['COMPLETED', 'ERROR']:
                return True
            return False
            
        except Exception as e:
            print(f"Error checking if file is processed: {e}")
            return False
            
    def get_recent_uploads(self, folder_path: str, limit: int = 10) -> list:
        """Get recently uploaded files"""
        recent_uploads = []
        
        try:
            status_info = self.get_all_status_files(folder_path)
            
            # Convert to list and sort by timestamp
            uploads = []
            for filename, info in status_info.items():
                if info['status'] in ['COMPLETED', 'PARTIAL']:
                    uploads.append({
                        'filename': filename,
                        'status': info['status'],
                        'timestamp': info['timestamp'],
                        'content': info['content']
                    })
                    
            # Sort by timestamp (most recent first)
            uploads.sort(key=lambda x: x['timestamp'], reverse=True)
            
            # Return limited results
            recent_uploads = uploads[:limit]
            
        except Exception as e:
            print(f"Error getting recent uploads: {e}")
            
        return recent_uploads
        
    def cleanup_old_status_files(self, folder_path: str, days_old: int = 30):
        """Clean up status files older than specified days"""
        try:
            folder = Path(folder_path)
            if not folder.exists():
                return 0
                
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 3600)
            cleaned_count = 0
            
            for status_file in folder.rglob('*_*.txt'):
                # Check if it's a status file
                if any(status_file.name.endswith(f'_{status}.txt') for status in self.status_types.keys()):
                    if status_file.stat().st_mtime < cutoff_time:
                        status_file.unlink()
                        cleaned_count += 1
                        
            return cleaned_count
            
        except Exception as e:
            print(f"Error cleaning up old status files: {e}")
            return 0 