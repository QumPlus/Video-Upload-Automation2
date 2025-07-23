"""
Pinterest API - Video pin creation integration
"""

import requests
import json
import os
from typing import Optional, Dict

class PinterestAPI:
    """Pinterest API v5 integration for creating video pins"""
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://api.pinterest.com/v5"
        
        # Set up headers
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Product tags for fitness videos
        self.product_tags = ['80817', '64237', '83349', '26803', '25007']
        self.shop_link = "https://www.cavemantrainingc.com/shop"
        
    def test_connection(self) -> bool:
        """Test API credentials and connection"""
        try:
            # Validate credentials first
            if not self.access_token or not self.access_token.strip():
                print("Pinterest API: Access token is empty or missing")
                return False
            
            # Test by getting user info
            url = f"{self.base_url}/user_account"
            print(f"Pinterest API: Testing connection to {url}")
            
            response = requests.get(url, headers=self.headers, timeout=10)
            
            print(f"Pinterest API: Response status code: {response.status_code}")
            
            if response.status_code == 200:
                user_info = response.json()
                username = user_info.get('username', 'Unknown')
                print(f"Pinterest API: Connection successful! Connected as: {username}")
                return True
            elif response.status_code == 401:
                print("Pinterest API: Invalid access token - check your credentials")
                try:
                    error_data = response.json()
                    print(f"Pinterest API: Error details: {error_data}")
                except:
                    print(f"Pinterest API: Response text: {response.text}")
                return False
            elif response.status_code == 403:
                print("Pinterest API: Access forbidden - check account permissions")
                try:
                    error_data = response.json()
                    print(f"Pinterest API: Error details: {error_data}")
                except:
                    print(f"Pinterest API: Response text: {response.text}")
                return False
            else:
                print(f"Pinterest API: Unexpected status code {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"Pinterest API: Error details: {error_data}")
                except:
                    print(f"Pinterest API: Response text: {response.text}")
                return False
                
        except requests.exceptions.Timeout as e:
            print(f"Pinterest API: Request timeout - check your internet connection: {e}")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"Pinterest API: Connection error - check your internet connection: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Pinterest API: Request error: {e}")
            return False
        except Exception as e:
            print(f"Pinterest API: Unexpected error: {e}")
            return False
            
    def create_pin(self, video_path: str, title: str, description: str, board_id: str = None) -> Optional[Dict]:
        """Create a video pin on Pinterest"""
        try:
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
                
            # Get file size
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("Video file is empty")
                
            print(f"Creating Pinterest pin: {title} ({file_size} bytes)")
            
            # First, upload the video to get a media ID
            media_id = self._upload_video(video_path)
            if not media_id:
                print("Failed to upload video to Pinterest")
                return None
                
            # Format description with hashtags and shop link
            formatted_description = self._format_description(description)
            
            # Create pin data
            pin_data = {
                'title': title,
                'description': formatted_description,
                'link': self.shop_link,
                'media_source': {
                    'source_type': 'video_id',
                    'media_id': media_id
                }
            }
            
            # Add board if specified
            if board_id:
                pin_data['board_id'] = board_id
                
            # Add product tags
            if self.product_tags:
                pin_data['product_rich_metadata'] = {
                    'product_ids': self.product_tags
                }
                
            # Create the pin
            url = f"{self.base_url}/pins"
            response = requests.post(url, headers=self.headers, json=pin_data, timeout=30)
            
            if response.status_code in [200, 201]:
                result = response.json()
                pin_id = result.get('id')
                
                print(f"Pinterest pin created successfully: {pin_id}")
                
                return {
                    'pin_id': pin_id,
                    'status': 'created',
                    'url': f"https://pinterest.com/pin/{pin_id}",
                    'details': result
                }
            else:
                print(f"Pinterest pin creation failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print("Pinterest pin creation timeout")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Pinterest pin creation request error: {e}")
            return None
        except Exception as e:
            print(f"Pinterest pin creation error: {e}")
            return None
            
    def _upload_video(self, video_path: str) -> Optional[str]:
        """Upload video to Pinterest and return media ID"""
        try:
            # Step 1: Register the upload
            register_url = f"{self.base_url}/media"
            register_data = {
                'media_type': 'video'
            }
            
            response = requests.post(register_url, headers=self.headers, json=register_data, timeout=10)
            
            if response.status_code != 201:
                print(f"Pinterest media registration failed: {response.status_code}")
                return None
                
            result = response.json()
            media_id = result.get('media_id')
            upload_url = result.get('upload_url')
            upload_parameters = result.get('upload_parameters', {})
            
            if not media_id or not upload_url:
                print("Pinterest media registration incomplete")
                return None
                
            # Step 2: Upload the video file
            with open(video_path, 'rb') as video_file:
                files = {'file': (os.path.basename(video_path), video_file, 'video/mp4')}
                
                # Use upload parameters from Pinterest
                upload_response = requests.post(
                    upload_url,
                    files=files,
                    data=upload_parameters,
                    timeout=300  # 5 minute timeout for video upload
                )
                
            if upload_response.status_code in [200, 204]:
                print(f"Pinterest video upload successful: {media_id}")
                return media_id
            else:
                print(f"Pinterest video upload failed: {upload_response.status_code}")
                return None
                
        except Exception as e:
            print(f"Pinterest video upload error: {e}")
            return None
            
    def _format_description(self, description: str) -> str:
        """Format description with fitness hashtags and shop link"""
        # Fitness-related hashtags
        hashtags = [
            '#fitness', '#workout', '#exercise', '#training',
            '#health', '#wellness', '#strength', '#motivation',
            '#fitnessmotivation', '#workoutmotivation', '#gym',
            '#homeworkout', '#fitnessjourney', '#healthy'
        ]
        
        # Limit description length (Pinterest limit is around 500 characters)
        max_desc_length = 300
        if len(description) > max_desc_length:
            description = description[:max_desc_length] + "..."
            
        # Add hashtags
        formatted_desc = description
        if not formatted_desc.endswith('.'):
            formatted_desc += '.'
            
        formatted_desc += '\n\n'
        formatted_desc += ' '.join(hashtags[:10])  # Add first 10 hashtags
        
        # Add shop link
        formatted_desc += f'\n\nShop: {self.shop_link}'
        
        return formatted_desc
        
    def get_pin_info(self, pin_id: str) -> Optional[Dict]:
        """Get information about a pin"""
        try:
            url = f"{self.base_url}/pins/{pin_id}"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Pinterest get pin info error: {e}")
            return None
            
    def get_boards(self) -> Optional[list]:
        """Get user's boards"""
        try:
            url = f"{self.base_url}/boards"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('items', [])
                
            return None
            
        except Exception as e:
            print(f"Pinterest get boards error: {e}")
            return None
            
    def create_board(self, name: str, description: str = "") -> Optional[Dict]:
        """Create a new board"""
        try:
            url = f"{self.base_url}/boards"
            data = {
                'name': name,
                'description': description,
                'privacy': 'PUBLIC'
            }
            
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            
            if response.status_code in [200, 201]:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Pinterest create board error: {e}")
            return None
            
    def delete_pin(self, pin_id: str) -> bool:
        """Delete a pin"""
        try:
            url = f"{self.base_url}/pins/{pin_id}"
            response = requests.delete(url, headers=self.headers, timeout=10)
            
            return response.status_code == 204
            
        except Exception as e:
            print(f"Pinterest delete pin error: {e}")
            return False
            
    def get_user_info(self) -> Optional[Dict]:
        """Get user account information"""
        try:
            url = f"{self.base_url}/user_account"
            response = requests.get(url, headers=self.headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Pinterest get user info error: {e}")
            return None
            
    def get_pin_analytics(self, pin_id: str) -> Optional[Dict]:
        """Get analytics for a pin (if available)"""
        try:
            url = f"{self.base_url}/pins/{pin_id}/analytics"
            params = {
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'metric_types': 'IMPRESSION,SAVE,PIN_CLICK'
            }
            
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
                
            return None
            
        except Exception as e:
            print(f"Pinterest get pin analytics error: {e}")
            return None 