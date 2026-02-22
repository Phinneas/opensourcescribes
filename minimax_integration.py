"""
MiniMax Integration Module for Video Generation
Handles text-to-video, image-to-video, and animated content generation
"""

import os
import json
import requests
import time
import asyncio
from typing import Dict, Optional, List
from pathlib import Path

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


class MiniMaxVideoGenerator:
    """Main class for MiniMax video generation"""
    
    def __init__(self):
        self.api_key = os.getenv('MINIMAX_API_KEY') or CONFIG.get('minimax', {}).get('api_key')
        self.base_url = "https://api.minimax.io/v1"
        self.model = "MiniMax-Hailuo-2.3"  # Correct model name from docs
        self.supported_durations = [6, 10]  # Only 6s and 10s are supported
        self.default_duration = 6
        self.timeout = 180  # 3 minutes timeout
        
        if not self.api_key:
            print("⚠️  MINIMAX_API_KEY not found in config.json or environment variables")
            print("   Please add 'minimax.api_key' to config.json to enable MiniMax features")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ MiniMax integration enabled")
    
    def generate_text_to_video(self, prompt: str, output_path: str, duration: int = None) -> Optional[str]:
        """
        Generate video from text prompt
        
        Args:
            prompt: Text description of desired video
            output_path: Where to save the video
            duration: Video duration in seconds (must be 6 or 10)
            
        Returns:
            Path to generated video or None if failed
        """
        if not self.enabled:
            return None
            
        # Ensure duration is valid
        if duration is None:
            duration = self.default_duration
        if duration not in self.supported_durations:
            candidates = [d for d in self.supported_durations if d >= duration]
            duration = min(candidates) if candidates else self.default_duration
            print(f"⚠️  Duration adjusted to {duration}s (supported: {self.supported_durations})")
            
        print(f"🎬 Generating video from text: {prompt[:50]}...")
        print(f"   Duration: {duration}s, Resolution: 1080P")
        
        try:
            # Create video generation task
            response = requests.post(
                f"{self.base_url}/video_generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "duration": duration,
                    "resolution": "1080P"
                }
            )
            
            # Debug: print response
            print(f"   Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"❌ MiniMax API error: {response.text}")
                return None
            
            task_data = response.json()
            print(f"   Response data: {task_data}")
            
            task_id = task_data.get('task_id')
            
            if not task_id:
                print("❌ No task ID returned from MiniMax")
                print(f"   Full response: {json.dumps(task_data, indent=2)}")
                return None
            
            print(f"   Task ID: {task_id}")
            
            # Poll for completion
            video_url = self._poll_task_completion(task_id)
            
            if video_url:
                # Download video
                self._download_video(video_url, output_path)
                print(f"   ✅ Video saved to {output_path}")
                return output_path
            else:
                print("❌ Video generation failed or timed out")
                return None
                
        except Exception as e:
            print(f"❌ Error generating text-to-video: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_image_to_video(
        self, 
        image_path: str, 
        prompt: str, 
        output_path: str = None, 
        duration: int = None
    ) -> Optional[str]:
        """
        Generate video by animating a starting image (i2v)
        """
        if not self.enabled:
            return None
            
        # Ensure duration is valid
        if duration is None:
            duration = self.default_duration
            
        print(f"🎬 Generating video from physical image: {image_path}")
        
        try:
            # 1. Convert image to Base64
            import base64
            with open(image_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            first_frame_data_url = f"data:image/png;base64,{encoded_string}"

            # 2. Create the i2v task
            response = requests.post(
                f"{self.base_url}/video_generation",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "first_frame_image": first_frame_data_url,
                    "duration": duration,
                    "resolution": "1080P"
                }
            )
            
            if response.status_code != 200:
                print(f"❌ MiniMax i2v error: {response.text}")
                return None
            
            task_data = response.json()
            task_id = task_data.get('task_id')
            
            if not task_id:
                return None
            
            print(f"   Task ID: {task_id}")
            video_url = self._poll_task_completion(task_id)
            
            if video_url:
                self._download_video(video_url, output_path)
                return output_path
            return None
                
        except Exception as e:
            print(f"❌ Error in image-to-video: {e}")
            return None
    
    def generate_code_animation(self, code_snippet: str, language: str = "python", output_path: str = None) -> Optional[str]:
        """
        Generate animated video showing code being typed/animated
        
        Args:
            code_snippet: Code text to animate
            language: Programming language
            output_path: Where to save the video
            
        Returns:
            Path to generated video or None if failed
        """
        if not output_path:
            output_path = f"assets/code_animation_{int(time.time())}.mp4"
        
        # Create a rich prompt for code animation
        prompt = f"""[Static shot] A professional IDE interface displaying {language} code being typed. 
        The code appears character by character with smooth typing animation. 
        High contrast syntax highlighting. Professional clean interface. 
        The code reads: {code_snippet[:100]}...
        Cinematic smooth camera movement showing complete code gradually appearing."""
        
        return self.generate_text_to_video(prompt, output_path, duration=6)
    
    def generate_ui_demonstration(self, ui_description: str, output_path: str = None) -> Optional[str]:
        """
        Generate animated UI demonstration
        
        Args:
            ui_description: Description of the UI to show
            output_path: Where to save the video
            
        Returns:
            Path to generated video or None if failed
        """
        if not output_path:
            output_path = f"assets/ui_demo_{int(time.time())}.mp4"
        
        # Create prompt for UI demo
        prompt = f"""[Static shot] A smooth professional UI demonstration showing {ui_description}. 
        Cursor movements and interactions are animated smoothly. 
        High quality rendering, modern interface design. 
        Cinematic camera movements showing the UI features being explored gradually."""
        
        return self.generate_text_to_video(prompt, output_path, duration=6)
    
    
    def _poll_task_completion(self, task_id: str, max_wait: int = 300) -> Optional[str]:
        """Poll task status until complete"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            try:
                # Using correct query endpoint
                response = requests.get(
                    f"{self.base_url}/query/video_generation?task_id={task_id}",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # MiniMax returns a flat response, not nested under 'task'
                    status = data.get('status', '')
                    print(f"   Status: {status}")

                    if status in ('Success', 'success'):
                        file_id = data.get('file_id', '')
                        # Need to fetch file download URL
                        if file_id:
                            return self._get_file_download_url(file_id)
                    elif status in ('Failed', 'failed'):
                        error_msg = data.get('base_resp', {}).get('status_msg', 'Unknown error')
                        print(f"❌ Task failed: {error_msg}")
                        return None
                    
                # Wait before next poll
                time.sleep(5)
                
            except Exception as e:
                print(f"❌ Error polling task: {e}")
                return None
        
        print("⏰ Task timed out")
        return None

    def _get_file_download_url(self, file_id: str) -> Optional[str]:
        """Get download URL for a generated file"""
        try:
            response = requests.get(
                f"{self.base_url}/files/retrieve",
                params={"file_id": file_id},
                headers={
                    "Authorization": f"Bearer {self.api_key}"
                }
            )

            if response.status_code == 200:
                data = response.json()
                # MiniMax nests file details under 'file'
                return data.get('file', {}).get('download_url')
            else:
                print(f"❌ Failed to get download URL: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error getting download URL: {e}")
            return None
    
    def _download_video(self, video_url: str, output_path: str) -> bool:
        """Download video from URL"""
        try:
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
            
        except Exception as e:
            print(f"❌ Error downloading video: {e}")
            return False


# Singleton instance
_minimax_instance = None

def get_minimax_generator() -> MiniMaxVideoGenerator:
    """Get singleton instance of MiniMax generator"""
    global _minimax_instance
    if _minimax_instance is None:
        _minimax_instance = MiniMaxVideoGenerator()
    return _minimax_instance


if __name__ == "__main__":
    # Test basic functionality
    generator = get_minimax_generator()
    
    # Test with a simple prompt
    test_prompt = "A smooth camera pan across a modern GitHub repository page showing code and features"
    test_output = "test_minimax_video.mp4"
    
    print("Testing MiniMax text-to-video generation...")
    result = generator.generate_text_to_video(test_prompt, test_output)
    
    if result:
        print(f"✅ Test video created: {result}")
    else:
        print("❌ Test failed")
