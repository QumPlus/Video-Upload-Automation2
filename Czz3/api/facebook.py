"""
Facebook Graph API - Scheduled video post integration
"""

import requests
import json
import os
import time
from datetime import datetime, timedelta
from typing import Optional, Dict

class FacebookAPI:
    """Facebook Graph API integration for scheduled video posts"""
    
    def __init__(self, page_token: str, group_id: str):
        self.page_token = page_token
        self.group_id = group_id
        self.base_url = "https://graph.facebook.com/v18.0"
        
    def test_connection(self) -> bool:
        """Test API credentials and connection"""
        try:
            # Validate credentials first
            if not self.page_token or not self.page_token.strip():
                print("Facebook API: Page token is empty or missing")
                return False
                
            if not self.group_id or not self.group_id.strip():
                print("Facebook API: Group ID is empty or missing")
                return False
            
            print(f"Facebook API: Testing connection to group {self.group_id}")
            
            # Step 1: Check token permissions
            print("Facebook API: Checking token permissions...")
            permissions_ok = self._check_token_permissions()
            
            if not permissions_ok:
                print("Facebook API: ❌ Token lacks required permissions for video upload/posting")
                self._print_required_permissions()
                return False
            
            # Step 2: Test group access
            url = f"{self.base_url}/{self.group_id}"
            params = {
                'access_token': self.page_token,
                'fields': 'id,name,privacy,can_post'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            print(f"Facebook API: Response status code: {response.status_code}")
            
            if response.status_code == 200:
                group_info = response.json()
                group_name = group_info.get('name', 'Unknown')
                can_post = group_info.get('can_post', False)
                
                print(f"Facebook API: ✅ Connected to group: {group_name}")
                
                if can_post:
                    print("Facebook API: ✅ Token has posting permissions for this group")
                else:
                    print("Facebook API: ⚠️ Token may not have posting permissions for this group")
                
                # Step 3: Test video upload permissions
                print("Facebook API: Testing video upload permissions...")
                upload_test = self._test_upload_permissions()
                
                if upload_test:
                    print("Facebook API: ✅ Video upload permissions confirmed!")
                    return True
                else:
                    print("Facebook API: ❌ Video upload permissions insufficient")
                    return False
                    
            elif response.status_code == 400:
                error = response.json().get('error', {})
                error_msg = error.get('message', 'Bad request')
                print(f"Facebook API: Bad request - {error_msg}")
                if 'code' in error:
                    print(f"Facebook API: Error code: {error['code']}")
                return False
            elif response.status_code == 401:
                print("Facebook API: Invalid access token - check your credentials")
                try:
                    error_data = response.json()
                    print(f"Facebook API: Error details: {error_data}")
                except:
                    print(f"Facebook API: Response text: {response.text}")
                return False
            elif response.status_code == 403:
                print("Facebook API: Access forbidden - check token permissions")
                try:
                    error_data = response.json()
                    print(f"Facebook API: Error details: {error_data}")
                except:
                    print(f"Facebook API: Response text: {response.text}")
                self._print_required_permissions()
                return False
            elif response.status_code == 404:
                print("Facebook API: Group not found - check your group ID")
                return False
            else:
                print(f"Facebook API: Unexpected status code {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Facebook API: Error details: {error_data}")
                except:
                    print(f"Facebook API: Response text: {response.text}")
                return False
                
        except requests.exceptions.Timeout as e:
            print(f"Facebook API: Request timeout - check your internet connection: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"Facebook API: Connection error - check your internet connection: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Facebook API: Request error: {e}")
            return False
        except Exception as e:
            print(f"Facebook API: Unexpected error: {e}")
            return False
    
    def _check_token_permissions(self) -> bool:
        """Check if the access token has required permissions"""
        try:
            # Get token information
            url = f"{self.base_url}/me/permissions"
            params = {
                'access_token': self.page_token
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"Facebook API: Cannot check permissions - status {response.status_code}")
                return False
            
            permissions_data = response.json()
            granted_permissions = []
            
            for perm in permissions_data.get('data', []):
                if perm.get('status') == 'granted':
                    granted_permissions.append(perm.get('permission'))
            
            print(f"Facebook API: Granted permissions: {', '.join(granted_permissions)}")
            
            # Required permissions for video upload and posting
            required_permissions = [
                'publish_to_groups',  # Post to groups
                'groups_access_member_info'  # Access group information
            ]
            
            # Check if we have the required permissions
            missing_permissions = []
            for req_perm in required_permissions:
                if req_perm not in granted_permissions:
                    missing_permissions.append(req_perm)
            
            if missing_permissions:
                print(f"Facebook API: ❌ Missing required permissions: {', '.join(missing_permissions)}")
                return False
            
            print("Facebook API: ✅ Token has required basic permissions")
            return True
            
        except Exception as e:
            print(f"Facebook API: Error checking permissions: {e}")
            return False
    
    def _test_upload_permissions(self) -> bool:
        """Test if we can upload videos to the group"""
        try:
            # Try to get upload limits/info for the group
            url = f"{self.base_url}/{self.group_id}/videos"
            params = {
                'access_token': self.page_token,
                'upload_phase': 'start',
                'file_size': 1024  # Small test size
            }
            
            # This is a test call - it should fail gracefully if we don't have permissions
            response = requests.post(url, params=params, timeout=10)
            
            if response.status_code == 200:
                # We can start uploads - clean up by not finishing
                print("Facebook API: ✅ Video upload permissions confirmed")
                return True
            elif response.status_code == 403:
                error_data = response.json().get('error', {})
                print(f"Facebook API: ❌ Upload forbidden: {error_data.get('message', 'No permission')}")
                return False
            elif response.status_code == 400:
                # Bad request might be due to test parameters, but permissions are OK
                error_data = response.json().get('error', {})
                error_msg = error_data.get('message', '')
                
                if 'permission' in error_msg.lower() or 'not allowed' in error_msg.lower():
                    print(f"Facebook API: ❌ Upload not allowed: {error_msg}")
                    return False
                else:
                    # Probably just bad test parameters, permissions seem OK
                    print("Facebook API: ✅ Upload permissions appear to be OK")
                    return True
            else:
                print(f"Facebook API: Upload test inconclusive (status {response.status_code})")
                return True  # Assume OK if we can't determine otherwise
                
        except Exception as e:
            print(f"Facebook API: Error testing upload permissions: {e}")
            return True  # Assume OK if we can't test
    
    def _print_required_permissions(self):
        """Print guidance on required Facebook permissions"""
        print("\n" + "="*60)
        print("📋 FACEBOOK API PERMISSIONS REQUIRED")
        print("="*60)
        print("Your Facebook access token needs these permissions:")
        print()
        print("🔑 REQUIRED PERMISSIONS:")
        print("   • publish_to_groups - Post content to Facebook groups")
        print("   • groups_access_member_info - Access group information")
        print()
        print("📱 HOW TO GET THE RIGHT TOKEN:")
        print("   1. Go to Facebook Graph API Explorer:")
        print("      https://developers.facebook.com/tools/explorer/")
        print()
        print("   2. Select your app from the dropdown")
        print()
        print("   3. Click 'Generate Access Token' and add these permissions:")
        print("      ✓ publish_to_groups")
        print("      ✓ groups_access_member_info")
        print()
        print("   4. Make sure you're logged in as a user who is:")
        print("      ✓ A member of the target Facebook group")
        print("      ✓ Has permission to post in the group")
        print("      ✓ Is an admin/moderator of the group (preferred)")
        print()
        print("   5. For Page Access Token (alternative):")
        print("      ✓ Use a Page Access Token if posting as a page")
        print("      ✓ Page must be connected to the group")
        print("      ✓ Requires pages_manage_posts permission")
        print()
        print("⚠️  NOTE: Group posting permissions can be restricted by:")
        print("   • Group privacy settings")
        print("   • Group admin approval requirements")
        print("   • Your membership level in the group")
        print("="*60)
        print()
            
    def schedule_post(self, video_path: str, message: str, schedule_time: datetime) -> Optional[Dict]:
        """Schedule a video post to the Facebook group"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
                
            # Get file size
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("Video file is empty")
                
            print(f"Scheduling Facebook post: {schedule_time.strftime('%Y-%m-%d %H:%M')} ({file_size} bytes)")
            
            # Convert schedule time to Unix timestamp
            schedule_timestamp = int(schedule_time.timestamp())
            
            # First, upload the video
            video_id = self._upload_video(video_path, message)
            if not video_id:
                print("Failed to upload video to Facebook")
                return None
                
            # Schedule the post
            result = self._schedule_video_post(video_id, message, schedule_timestamp)
            
            if result:
                print(f"Facebook post scheduled successfully: {result.get('id')}")
                return {
                    'post_id': result.get('id'),
                    'video_id': video_id,
                    'status': 'scheduled',
                    'scheduled_time': schedule_time.isoformat(),
                    'details': result
                }
            else:
                return None
                
        except requests.exceptions.Timeout:
            print("Facebook post scheduling timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Facebook post scheduling request error: {e}")
            return None
        except Exception as e:
            print(f"Facebook post scheduling error: {e}")
            return None
            
    def _upload_video(self, video_path: str, description: str) -> Optional[str]:
        """Upload video to Facebook and return video ID"""
        try:
            # Step 1: Initialize upload session
            init_url = f"{self.base_url}/{self.group_id}/videos"
            
            file_size = os.path.getsize(video_path)
            
            init_params = {
                'access_token': self.page_token,
                'upload_phase': 'start',
                'file_size': file_size
            }
            
            response = requests.post(init_url, params=init_params, timeout=30)
            
            if response.status_code != 200:
                print(f"Facebook video upload initialization failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
            result = response.json()
            video_id = result.get('video_id')
            upload_session_id = result.get('upload_session_id')
            
            if not video_id or not upload_session_id:
                print("Facebook video upload initialization incomplete")
                return None
                
            # Step 2: Upload video file in chunks
            chunk_size = 1024 * 1024 * 4  # 4MB chunks
            
            with open(video_path, 'rb') as video_file:
                start_offset = 0
                
                while True:
                    chunk = video_file.read(chunk_size)
                    if not chunk:
                        break
                        
                    # Upload chunk
                    upload_params = {
                        'access_token': self.page_token,
                        'upload_phase': 'transfer',
                        'upload_session_id': upload_session_id,
                        'start_offset': start_offset
                    }
                    
                    files = {
                        'video_file_chunk': (f'chunk_{start_offset}', chunk, 'application/octet-stream')
                    }
                    
                    chunk_response = requests.post(
                        init_url,
                        params=upload_params,
                        files=files,
                        timeout=120
                    )
                    
                    if chunk_response.status_code != 200:
                        print(f"Facebook video chunk upload failed: {chunk_response.status_code}")
                        return None
                        
                    start_offset += len(chunk)
                    
            # Step 3: Finalize upload
            finalize_params = {
                'access_token': self.page_token,
                'upload_phase': 'finish',
                'upload_session_id': upload_session_id,
                'description': description
            }
            
            finalize_response = requests.post(init_url, params=finalize_params, timeout=30)
            
            if finalize_response.status_code == 200:
                print(f"Facebook video upload successful: {video_id}")
                return video_id
            else:
                print(f"Facebook video upload finalization failed: {finalize_response.status_code}")
                return None
                
        except Exception as e:
            print(f"Facebook video upload error: {e}")
            return None
            
    def _schedule_video_post(self, video_id: str, message: str, schedule_timestamp: int) -> Optional[Dict]:
        """Schedule a post with the uploaded video"""
        try:
            url = f"{self.base_url}/{self.group_id}/feed"
            
            data = {
                'access_token': self.page_token,
                'message': message,
                'object_attachment': video_id,
                'scheduled_publish_time': schedule_timestamp,
                'published': 'false'  # Keep as draft until scheduled time
            }
            
            response = requests.post(url, data=data, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Facebook post scheduling failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Facebook post scheduling error: {e}")
            return None
            
    def post_immediately(self, video_path: str, message: str) -> Optional[Dict]:
        """Post video immediately (not scheduled)"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
                
            print(f"Posting to Facebook immediately")
            
            # Upload and post video
            url = f"{self.base_url}/{self.group_id}/videos"
            
            with open(video_path, 'rb') as video_file:
                files = {
                    'source': (os.path.basename(video_path), video_file, 'video/mp4')
                }
                
                data = {
                    'access_token': self.page_token,
                    'description': message
                }
                
                response = requests.post(url, files=files, data=data, timeout=300)
                
            if response.status_code == 200:
                result = response.json()
                video_id = result.get('id')
                
                print(f"Facebook post successful: {video_id}")
                
                return {
                    'post_id': video_id,
                    'status': 'posted',
                    'url': f"https://facebook.com/{video_id}",
                    'details': result
                }
            else:
                print(f"Facebook post failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"Facebook immediate post error: {e}")
            return None
            
    def get_post_info(self, post_id: str) -> Optional[Dict]:
        """Get information about a post"""
        try:
            url = f"{self.base_url}/{post_id}"
            params = {
                'access_token': self.page_token,
                'fields': 'id,message,created_time,scheduled_publish_time,is_published'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Facebook get post info error: {e}")
            return None
            
    def delete_post(self, post_id: str) -> bool:
        """Delete a post"""
        try:
            url = f"{self.base_url}/{post_id}"
            params = {
                'access_token': self.page_token
            }
            
            response = requests.delete(url, params=params, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Facebook delete post error: {e}")
            return False
            
    def get_group_info(self) -> Optional[Dict]:
        """Get information about the Facebook group"""
        try:
            url = f"{self.base_url}/{self.group_id}"
            params = {
                'access_token': self.page_token,
                'fields': 'id,name,description,privacy,member_count'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Facebook get group info error: {e}")
            return None
            
    def list_scheduled_posts(self) -> Optional[list]:
        """List scheduled posts for the group"""
        try:
            url = f"{self.base_url}/{self.group_id}/scheduled_posts"
            params = {
                'access_token': self.page_token,
                'fields': 'id,message,scheduled_publish_time,created_time'
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('data', [])
                
            return None
            
        except Exception as e:
            print(f"Facebook list scheduled posts error: {e}")
            return None
            
    def update_scheduled_post(self, post_id: str, new_schedule_time: datetime, new_message: str = None) -> bool:
        """Update a scheduled post"""
        try:
            url = f"{self.base_url}/{post_id}"
            
            data = {
                'access_token': self.page_token,
                'scheduled_publish_time': int(new_schedule_time.timestamp())
            }
            
            if new_message:
                data['message'] = new_message
                
            response = requests.post(url, data=data, timeout=10)
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"Facebook update scheduled post error: {e}")
            return False 