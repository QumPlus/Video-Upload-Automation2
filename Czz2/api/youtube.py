"""
YouTube API - Video upload integration with OAuth2
"""

import requests
import json
import os
import webbrowser
import threading
import time
from typing import Optional, Dict
from urllib.parse import urlencode, parse_qs
import http.server
import socketserver

class YouTubeAPI:
    """YouTube Data API v3 integration for video uploads"""
    
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = None
        self.access_token = None
        self.token_expires_at = 0
        
        # OAuth2 endpoints
        self.auth_base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        self.token_url = "https://oauth2.googleapis.com/token"
        
        # YouTube API endpoints
        self.youtube_base_url = "https://www.googleapis.com/youtube/v3"
        self.upload_url = "https://www.googleapis.com/upload/youtube/v3/videos"
        
        # OAuth2 scopes
        self.scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube"
        ]
        
    def authenticate(self) -> Optional[str]:
        """Perform OAuth2 authentication flow"""
        try:
            # Set up local server to receive callback
            redirect_uri = "http://localhost:8080"
            
            # Generate authorization URL
            auth_params = {
                'client_id': self.client_id,
                'redirect_uri': redirect_uri,
                'scope': ' '.join(self.scopes),
                'response_type': 'code',
                'access_type': 'offline',
                'prompt': 'consent'
            }
            
            auth_url = f"{self.auth_base_url}?{urlencode(auth_params)}"
            
            print(f"Opening browser for YouTube authentication...")
            print(f"If browser doesn't open, visit: {auth_url}")
            
            # Start local server to receive callback
            auth_code = self._start_callback_server(redirect_uri)
            
            if not auth_code:
                print("Authentication failed: No authorization code received")
                return None
                
            # Exchange authorization code for tokens
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'code': auth_code,
                'grant_type': 'authorization_code',
                'redirect_uri': redirect_uri
            }
            
            response = requests.post(self.token_url, data=token_data, timeout=10)
            
            if response.status_code == 200:
                tokens = response.json()
                
                self.access_token = tokens.get('access_token')
                self.refresh_token = tokens.get('refresh_token')
                expires_in = tokens.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in
                
                print("YouTube authentication successful!")
                return self.refresh_token
                
            else:
                print(f"Token exchange failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"YouTube authentication error: {e}")
            return None
            
    def _start_callback_server(self, redirect_uri: str) -> Optional[str]:
        """Start local server to receive OAuth callback"""
        try:
            # Extract port from redirect_uri
            port = 8080
            auth_code = None
            
            class CallbackHandler(http.server.BaseHTTPRequestHandler):
                def do_GET(self):
                    nonlocal auth_code
                    
                    if self.path.startswith('/?code='):
                        # Extract authorization code
                        query = self.path.split('?', 1)[1]
                        params = parse_qs(query)
                        auth_code = params.get('code', [None])[0]
                        
                        # Send success response
                        self.send_response(200)
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        self.wfile.write(b"""
                        <html>
                        <body>
                        <h1>Authentication Successful!</h1>
                        <p>You can close this window and return to the application.</p>
                        </body>
                        </html>
                        """)
                    else:
                        self.send_response(400)
                        self.end_headers()
                        
                def log_message(self, format, *args):
                    # Suppress log messages
                    pass
                    
            # Start server
            with socketserver.TCPServer(("", port), CallbackHandler) as httpd:
                # Open browser
                webbrowser.open(f"{self.auth_base_url}?{urlencode({
                    'client_id': self.client_id,
                    'redirect_uri': redirect_uri,
                    'scope': ' '.join(self.scopes),
                    'response_type': 'code',
                    'access_type': 'offline',
                    'prompt': 'consent'
                })}")
                
                # Wait for callback (with timeout)
                timeout = 300  # 5 minutes
                start_time = time.time()
                
                while auth_code is None and (time.time() - start_time) < timeout:
                    httpd.handle_request()
                    
            return auth_code
            
        except Exception as e:
            print(f"Callback server error: {e}")
            return None
            
    def set_refresh_token(self, refresh_token: str):
        """Set refresh token from saved configuration"""
        self.refresh_token = refresh_token
        
    def _refresh_access_token(self) -> bool:
        """Refresh access token using refresh token"""
        try:
            if not self.refresh_token:
                return False
                
            token_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(self.token_url, data=token_data, timeout=10)
            
            if response.status_code == 200:
                tokens = response.json()
                self.access_token = tokens.get('access_token')
                expires_in = tokens.get('expires_in', 3600)
                self.token_expires_at = time.time() + expires_in
                return True
                
            return False
            
        except Exception as e:
            print(f"Token refresh error: {e}")
            return False
            
    def _ensure_valid_token(self) -> bool:
        """Ensure we have a valid access token"""
        if not self.access_token or time.time() >= self.token_expires_at:
            return self._refresh_access_token()
        return True
        
    def upload_video(self, file_path: str, title: str, description: str = "", is_short: bool = False) -> Optional[Dict]:
        """Upload video to YouTube"""
        try:
            if not self._ensure_valid_token():
                print("YouTube: Invalid or expired token")
                return None
                
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Video file not found: {file_path}")
                
            # Get file size
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                raise ValueError("Video file is empty")
                
            print(f"Uploading to YouTube: {title} ({'Short' if is_short else 'Regular'}) ({file_size} bytes)")
            
            # Prepare video metadata
            video_metadata = {
                'snippet': {
                    'title': title[:100],  # YouTube title limit
                    'description': description,
                    'tags': [],
                    'categoryId': '17'  # Sports category
                },
                'status': {
                    'privacyStatus': 'private'  # Upload as private initially
                }
            }
            
            # Add Short-specific metadata
            if is_short:
                video_metadata['snippet']['tags'].extend(['#Shorts', '#fitness', '#workout'])
                
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Accept': 'application/json'
            }
            
            # Upload video using resumable upload
            params = {
                'part': 'snippet,status',
                'uploadType': 'multipart'
            }
            
            # Prepare multipart data
            files = {
                'video': (os.path.basename(file_path), open(file_path, 'rb'), 'video/*')
            }
            
            data = {
                'metadata': json.dumps(video_metadata)
            }
            
            response = requests.post(
                self.upload_url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                params=params,
                files=files,
                data=data,
                timeout=600  # 10 minute timeout for uploads
            )
            
            # Close the file
            files['video'][1].close()
            
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                
                print(f"YouTube upload successful: {video_id}")
                
                return {
                    'video_id': video_id,
                    'status': 'uploaded',
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'details': result
                }
            else:
                print(f"YouTube upload failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("YouTube upload timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"YouTube upload request error: {e}")
            return None
        except Exception as e:
            print(f"YouTube upload error: {e}")
            return None
            
    def get_video_info(self, video_id: str) -> Optional[Dict]:
        """Get information about an uploaded video"""
        try:
            if not self._ensure_valid_token():
                return None
                
            url = f"{self.youtube_base_url}/videos"
            params = {
                'part': 'snippet,status,statistics',
                'id': video_id
            }
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                items = result.get('items', [])
                if items:
                    return items[0]
                    
            return None
            
        except Exception as e:
            print(f"YouTube get video info error: {e}")
            return None
            
    def update_video_privacy(self, video_id: str, privacy_status: str) -> bool:
        """Update video privacy status"""
        try:
            if not self._ensure_valid_token():
                return False
                
            url = f"{self.youtube_base_url}/videos"
            params = {
                'part': 'status'
            }
            
            data = {
                'id': video_id,
                'status': {
                    'privacyStatus': privacy_status
                }
            }
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.put(url, headers=headers, params=params, json=data, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"YouTube update privacy error: {e}")
            return False
            
    def test_connection(self) -> bool:
        """Test YouTube API connection and credentials"""
        try:
            if not self._ensure_valid_token():
                return False
                
            # Test by getting channel info
            url = f"{self.youtube_base_url}/channels"
            params = {
                'part': 'snippet',
                'mine': 'true'
            }
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"YouTube test connection error: {e}")
            return False 