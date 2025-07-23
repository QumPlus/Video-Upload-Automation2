"""
CloudFlare Stream API - Video upload integration
"""

import requests
import json
import os
from typing import Optional, Dict

class CloudFlareAPI:
    """CloudFlare Stream API integration for video uploads"""
    
    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"
        
        # Set up headers
        self.headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
    def test_connection(self) -> bool:
        """Test API credentials and connection"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/stream"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return True
            elif response.status_code == 401:
                print("CloudFlare API: Invalid credentials")
                return False
            elif response.status_code == 403:
                print("CloudFlare API: Access forbidden")
                return False
            else:
                print(f"CloudFlare API: Unexpected status code {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"CloudFlare API connection error: {e}")
            return False
        except Exception as e:
            print(f"CloudFlare API test error: {e}")
            return False
            
    def upload_video(self, file_path: str, title: str, description: str = "") -> Optional[Dict]:
        """Upload video to CloudFlare Stream"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")
                
            # Get file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError("Video file is empty")
                
            print(f"Uploading to CloudFlare: {title} ({file_size} bytes)")
            
            # Create upload URL
            upload_url = f"{self.base_url}/accounts/{self.account_id}/stream"
            
            # Prepare metadata
            metadata = {
                'name': title,
                'meta': {
                    'title': title,
                    'description': description
                }
            }
            
            # Upload file
            with open(file_path, 'rb') as video_file:
                files = {
                    'file': (os.path.basename(file_path), video_file, 'video/mp4')
                }
                
                # Remove Content-Type header for multipart upload
                upload_headers = {
                    'Authorization': f'Bearer {self.api_token}'
                }
                
                data = {'meta': json.dumps(metadata)}
                
                response = requests.post(
                    upload_url, 
                    headers=upload_headers,
                    files=files,
                    data=data,
                    timeout=300  # 5 minute timeout for uploads
                )
                
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    video_id = result['result']['uid']
                    print(f"CloudFlare upload successful: {video_id}")
                    return {
                        'video_id': video_id,
                        'status': 'uploaded',
                        'preview_url': f"https://cloudflarestream.com/{video_id}/iframe",
                        'details': result['result']
                    }
                else:
                    errors = result.get('errors', [])
                    error_msg = ', '.join([err.get('message', str(err)) for err in errors])
                    print(f"CloudFlare upload failed: {error_msg}")
                    return None
            else:
                print(f"CloudFlare upload failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("CloudFlare upload timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"CloudFlare upload request error: {e}")
            return None
        except Exception as e:
            print(f"CloudFlare upload error: {e}")
            return None
            
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get information about an uploaded video"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/stream/{video_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['result']
                    
            return None
            
        except Exception as e:
            print(f"CloudFlare get video info error: {e}")
            return None
            
    def update_video_metadata(self, video_id: str, title: str, description: str = "") -> bool:
        """Update metadata for an uploaded video"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/stream/{video_id}"
            
            payload = {
                'meta': {
                    'title': title,
                    'description': description
                }
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
                
            return False
            
        except Exception as e:
            print(f"CloudFlare update metadata error: {e}")
            return False
            
    def delete_video(self, video_id: str) -> bool:
        """Delete a video from CloudFlare Stream"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/stream/{video_id}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('success', False)
                
            return False
            
        except Exception as e:
            print(f"CloudFlare delete video error: {e}")
            return False
            
    def list_videos(self, limit: int = 50) -> Optional[list]:
        """List uploaded videos"""
        try:
            url = f"{self.base_url}/accounts/{self.account_id}/stream"
            params = {'per_page': limit}
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result['result']
                    
            return None
            
        except Exception as e:
            print(f"CloudFlare list videos error: {e}")
            return None
            
    def get_upload_status(self, video_id: str) -> Optional[str]:
        """Get upload processing status"""
        try:
            video_info = self.get_video_info(video_id)
            if video_info:
                return video_info.get('status', {}).get('state', 'unknown')
            return None
            
        except Exception as e:
            print(f"CloudFlare get upload status error: {e}")
            return None
            
    def generate_signed_url(self, video_id: str, expires_in: int = 3600) -> Optional[str]:
        """Generate a signed URL for video access (if available)"""
        try:
            # This would require additional setup with CloudFlare Stream
            # For now, return the basic iframe URL
            return f"https://cloudflarestream.com/{video_id}/iframe"
            
        except Exception as e:
            print(f"CloudFlare generate signed URL error: {e}")
            return None 