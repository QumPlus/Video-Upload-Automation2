"""
File Manager - Handles file scanning, validation, and metadata extraction
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class FileInfo:
    """Data class for file information"""
    path: str
    filename: str
    folder_type: str  # 'cloudflare', 'pinterest', 'youtube_shorts'
    title: str
    description: str
    short_description: str
    platforms: List[str]  # Which platforms this file should be uploaded to
    
class FileManager:
    """Manages file scanning and validation for video uploads"""
    
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        
        # Define folder paths
        self.cloudflare_path = self.base_path / "CloudFlare"
        self.pinterest_path = self.base_path / "Pinterest"
        self.youtube_shorts_path = self.base_path / "YouTube Shorts"
        
        # Supported video extensions
        self.video_extensions = {'.mov', '.mp4', '.avi', '.mkv', '.wmv', '.flv', '.webm'}
        
    def scan_folders(self) -> List[FileInfo]:
        """Scan all three folders for video files and return file info objects"""
        all_files = []
        
        # Scan CloudFlare folder
        if self.cloudflare_path.exists():
            cf_files = self._scan_folder(self.cloudflare_path, 'cloudflare')
            all_files.extend(cf_files)
            
        # Scan Pinterest folder
        if self.pinterest_path.exists():
            pin_files = self._scan_folder(self.pinterest_path, 'pinterest')
            all_files.extend(pin_files)
            
        # Scan YouTube Shorts folder
        if self.youtube_shorts_path.exists():
            yt_files = self._scan_folder(self.youtube_shorts_path, 'youtube_shorts')
            all_files.extend(yt_files)
            
        return self.validate_files(all_files)
        
    def _scan_folder(self, folder_path: Path, folder_type: str) -> List[FileInfo]:
        """Scan a specific folder for video files"""
        files = []
        
        try:
            for file_path in folder_path.rglob('*'):
                if (file_path.is_file() and 
                    file_path.suffix.lower() in self.video_extensions and
                    not self._is_status_file(file_path.name)):
                    
                    # Skip files that are already being processed or completed
                    if self._has_status_file(file_path, '_UPLOADING') or \
                       self._has_status_file(file_path, '_COMPLETED'):
                        continue
                        
                    file_info = self._create_file_info(file_path, folder_type)
                    if file_info:
                        files.append(file_info)
                        
        except Exception as e:
            print(f"Error scanning folder {folder_path}: {e}")
            
        return files
        
    def _create_file_info(self, file_path: Path, folder_type: str) -> Optional[FileInfo]:
        """Create FileInfo object for a video file"""
        try:
            filename = file_path.name
            
            # Extract metadata from text files
            metadata = self.get_file_metadata(file_path)
            
            # Determine which platforms this file should be uploaded to
            platforms = self._determine_platforms(filename, folder_type)
            
            return FileInfo(
                path=str(file_path),
                filename=filename,
                folder_type=folder_type,
                title=metadata.get('title', filename),
                description=metadata.get('description', ''),
                short_description=metadata.get('short_description', ''),
                platforms=platforms
            )
            
        except Exception as e:
            print(f"Error creating file info for {file_path}: {e}")
            return None
            
    def _determine_platforms(self, filename: str, folder_type: str) -> List[str]:
        """Determine which platforms a file should be uploaded to based on folder and filename"""
        platforms = []
        
        if folder_type == 'cloudflare':
            # CloudFlare folder files always go to CloudFlare and Facebook
            platforms.extend(['cloudflare', 'facebook'])
            
            # Files with "001" in the name also go to YouTube
            if '001' in filename:
                platforms.append('youtube')
                
        elif folder_type == 'pinterest':
            # Pinterest folder files only go to Pinterest
            platforms.append('pinterest')
            
        elif folder_type == 'youtube_shorts':
            # YouTube Shorts folder files only go to YouTube Shorts
            platforms.append('youtube_shorts')
            
        return platforms
        
    def validate_files(self, file_list: List[FileInfo]) -> List[FileInfo]:
        """Validate files and filter out invalid ones"""
        validated_files = []
        
        for file_info in file_list:
            try:
                # Check if file still exists
                if not os.path.exists(file_info.path):
                    continue
                    
                # Check if file has minimum required metadata
                if not file_info.title:
                    print(f"Warning: No title found for {file_info.filename}")
                    # Use filename as title if no title found
                    file_info.title = Path(file_info.filename).stem
                    
                # Check file size (skip empty files)
                file_size = os.path.getsize(file_info.path)
                if file_size == 0:
                    print(f"Skipping empty file: {file_info.filename}")
                    continue
                    
                validated_files.append(file_info)
                
            except Exception as e:
                print(f"Error validating file {file_info.filename}: {e}")
                
        return validated_files
        
    def get_file_metadata(self, file_path: Path) -> Dict[str, str]:
        """Extract title, description from associated text files"""
        metadata = {}
        
        try:
            # Look for text files with same base name
            base_name = file_path.stem
            parent_dir = file_path.parent
            
            # Look for TITLE.txt
            title_file = parent_dir / f"{base_name} TITLE.txt"
            if not title_file.exists():
                title_file = parent_dir / "TITLE.txt"
            if title_file.exists():
                metadata['title'] = self._read_text_file(title_file)
                
            # Look for DESCRIPTION.txt
            desc_file = parent_dir / f"{base_name} DESCRIPTION.txt"
            if not desc_file.exists():
                desc_file = parent_dir / "DESCRIPTION.txt"
            if desc_file.exists():
                metadata['description'] = self._read_text_file(desc_file)
                
            # Look for SHORT_DESCRIPTION.txt
            short_desc_file = parent_dir / f"{base_name} SHORT_DESCRIPTION.txt"
            if not short_desc_file.exists():
                short_desc_file = parent_dir / "SHORT_DESCRIPTION.txt"
            if short_desc_file.exists():
                metadata['short_description'] = self._read_text_file(short_desc_file)
                
            # If no metadata files found, try to extract from filename
            if not metadata.get('title'):
                # Remove extension and common prefixes/suffixes
                title = base_name
                # Remove numbers and common separators
                import re
                title = re.sub(r'^\d+\s*[-_\s]*', '', title)  # Remove leading numbers
                title = re.sub(r'[-_]', ' ', title)  # Replace dashes/underscores with spaces
                title = title.strip().title()
                metadata['title'] = title
                
        except Exception as e:
            print(f"Error extracting metadata for {file_path}: {e}")
            
        return metadata
        
    def _read_text_file(self, file_path: Path) -> str:
        """Read content from a text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                return content
        except Exception as e:
            print(f"Error reading text file {file_path}: {e}")
            return ""
            
    def _is_status_file(self, filename: str) -> bool:
        """Check if a file is a status file"""
        status_indicators = ['_UPLOADING', '_COMPLETED', '_ERROR']
        return any(indicator in filename for indicator in status_indicators)
        
    def _has_status_file(self, video_path: Path, status: str) -> bool:
        """Check if a video file has an associated status file"""
        base_name = video_path.stem
        status_file = video_path.parent / f"{base_name}{status}.txt"
        return status_file.exists()
        
    def get_folder_stats(self) -> Dict[str, int]:
        """Get statistics about files in each folder"""
        stats = {
            'cloudflare': 0,
            'pinterest': 0,
            'youtube_shorts': 0,
            'total': 0
        }
        
        try:
            if self.cloudflare_path.exists():
                stats['cloudflare'] = len([f for f in self.cloudflare_path.rglob('*') 
                                         if f.is_file() and f.suffix.lower() in self.video_extensions])
                                         
            if self.pinterest_path.exists():
                stats['pinterest'] = len([f for f in self.pinterest_path.rglob('*') 
                                        if f.is_file() and f.suffix.lower() in self.video_extensions])
                                        
            if self.youtube_shorts_path.exists():
                stats['youtube_shorts'] = len([f for f in self.youtube_shorts_path.rglob('*') 
                                             if f.is_file() and f.suffix.lower() in self.video_extensions])
                                             
            stats['total'] = stats['cloudflare'] + stats['pinterest'] + stats['youtube_shorts']
            
        except Exception as e:
            print(f"Error getting folder stats: {e}")
            
        return stats
        
    def create_folder_structure(self):
        """Create the required folder structure if it doesn't exist"""
        try:
            self.cloudflare_path.mkdir(parents=True, exist_ok=True)
            self.pinterest_path.mkdir(parents=True, exist_ok=True)
            self.youtube_shorts_path.mkdir(parents=True, exist_ok=True)
            
            # Create sample text files for guidance
            self._create_sample_files()
            
        except Exception as e:
            print(f"Error creating folder structure: {e}")
            
    def _create_sample_files(self):
        """Create sample text files to guide users"""
        try:
            # Create sample in CloudFlare folder
            cf_sample = self.cloudflare_path / "TITLE.txt"
            if not cf_sample.exists():
                with open(cf_sample, 'w') as f:
                    f.write("Sample Video Title")
                    
            cf_desc = self.cloudflare_path / "DESCRIPTION.txt"
            if not cf_desc.exists():
                with open(cf_desc, 'w') as f:
                    f.write("This is a sample description for your video. Edit this file to customize the description.")
                    
        except Exception as e:
            print(f"Error creating sample files: {e}")
            
    def cleanup_status_files(self, video_path: str):
        """Clean up old status files for a video"""
        try:
            video_file = Path(video_path)
            base_name = video_file.stem
            parent_dir = video_file.parent
            
            status_types = ['_UPLOADING', '_COMPLETED', '_ERROR']
            for status in status_types:
                status_file = parent_dir / f"{base_name}{status}.txt"
                if status_file.exists():
                    status_file.unlink()
                    
        except Exception as e:
            print(f"Error cleaning up status files: {e}")
            
    def get_upload_history(self) -> List[Dict]:
        """Get history of uploaded files"""
        history = []
        
        try:
            for folder_path in [self.cloudflare_path, self.pinterest_path, self.youtube_shorts_path]:
                if not folder_path.exists():
                    continue
                    
                for status_file in folder_path.rglob('*_COMPLETED.txt'):
                    try:
                        # Get the original video filename
                        base_name = status_file.stem.replace('_COMPLETED', '')
                        
                        # Read status file content
                        with open(status_file, 'r') as f:
                            content = f.read().strip()
                            
                        history.append({
                            'filename': base_name,
                            'folder': folder_path.name,
                            'completion_time': status_file.stat().st_mtime,
                            'details': content
                        })
                        
                    except Exception as e:
                        print(f"Error reading status file {status_file}: {e}")
                        
        except Exception as e:
            print(f"Error getting upload history: {e}")
            
        # Sort by completion time (most recent first)
        history.sort(key=lambda x: x['completion_time'], reverse=True)
        return history 