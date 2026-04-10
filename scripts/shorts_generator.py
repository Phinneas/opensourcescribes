"""
YouTube Shorts Generator for OpenSourceScribes
Extracts vertical 9:16 clips from existing horizontal main video
Generates one Short per project using precise timeline reconstruction
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
import math

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

SHORTS_FOLDER = "shorts"
MAX_SHORT_DURATION = 59  # YouTube Shorts max is 60 seconds
DATA_FILE = "posts_data.json"
ASSETS_FOLDER = "assets"

class ShortsFromVideoExtractor:
    """Extract YouTube Shorts from existing main video"""
    
    def __init__(self):
        self.shorts_dir = Path(SHORTS_FOLDER)
        self.shorts_dir.mkdir(exist_ok=True)
        self.project_data = self.load_project_data()
    
    def load_project_data(self):
        """Load project data from JSON file"""
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading project data: {e}")
            return []

    def get_audio_duration(self, audio_path):
        """Get duration of audio file in seconds"""
        if not os.path.exists(audio_path):
            return 0
            
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_path
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return float(result.stdout.strip())
        except:
            return 0

    def find_latest_video(self):
        """Find the most recently created main video file"""
        # Pattern: github_roundup_*.mp4
        current_date_pattern = datetime.now().strftime("%b%d").lower()
        
        # Try current date first
        video_path = Path(f"github_roundup_{current_date_pattern}.mp4")
        if video_path.exists():
            return str(video_path)
        
        # Fallback: find any github_roundup_*.mp4
        import glob
        videos = glob.glob("github_roundup_*.mp4")
        if videos:
            # Return most recently modified
            videos.sort(key=os.path.getmtime, reverse=True)
            return videos[0]
        
        return None
    
    def create_vertical_crop(self, input_video, start_time, duration, output_path):
        """
        Extract a segment from horizontal video and convert to vertical format
        
        Strategy: Left-aligned crop (captures Title/Desc) then add padding top/bottom
        """
        print(f"🎬 Creating Short: {output_path.name}")
        print(f"   ⏱️  Start: {start_time:.1f}s | Duration: {duration:.1f}s")
        
        # FFmpeg filter for horizontal → vertical conversion
        # 1. Extract the time segment
        # 2. Crop LEFT square (1080x1080 from 1920x1080, starting at x=0)
        #    This captures the Name/Description which are on the left side
        # 3. Add letterboxing (black bars top/bottom) to make 1080x1920
        #    Color matches Code Stream dark blue #0a1628
        filter_complex = (
            f"[0:v]crop=1080:1080:0:0[square];"
            f"[square]scale=1080:1080[scaled];"
            f"[scaled]pad=1080:1920:0:(1920-1080)/2:color=#0a1628[vertical]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', input_video,
            '-t', str(duration),
            '-filter_complex', filter_complex,
            '-map', '[vertical]',
            '-map', '0:a',  # Keep original audio
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"   ✅ Short created successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error creating Short: {e}")
            return False
            
    def generate_shorts_from_video(self, input_video=None):
        """
        Generate one Short per project using exact timeline reconstruction
        """
        # Find video if not specified
        if not input_video:
            input_video = self.find_latest_video()
            if not input_video:
                print("❌ Error: Could not find github_roundup_*.mp4 video file")
                print("   Please run video_maker.py first to create the main video")
                return
        
        input_path = Path(input_video)
        if not input_path.exists():
            print(f"❌ Error: Video file not found: {input_video}")
            return
        
        print(f"\n📱 YouTube Shorts Generator for OpenSourceScribes")
        print("=" * 60)
        print(f"📹 Source video: {input_path.name}")
        
        # Reconstruct Timeline
        current_time = 0
        
        # 1. Add Intro duration (if audio exists use that, else use config)
        intro_audio = os.path.join(ASSETS_FOLDER, "intro_audio.mp3")
        intro_duration = self.get_audio_duration(intro_audio)
        if intro_duration == 0:
            intro_duration = CONFIG['video_settings']['intro_duration']
        
        current_time += intro_duration
        print(f"ℹ️  Skipping Intro ({intro_duration:.1f}s)")
        
        # 2. Process Projects
        shorts_created = []
        midpoint = len(self.project_data) // 2
        
        for i, project in enumerate(self.project_data):
            project_id = project.get('id', f'p{i+1}')
            audio_path = os.path.join(ASSETS_FOLDER, f"{project_id}_audio.mp3")
            
            # Get precise duration from the audio file used to create the segment
            duration = self.get_audio_duration(audio_path)
            
            if duration > 0:
                # Cap duration for Shorts (max 59s)
                # If segment is longer, we might need to cut it or speed it up?
                # For now, just taking the first 59s if it's too long, but usually these are short.
                short_duration = min(duration, MAX_SHORT_DURATION)
                
                output_filename = f"short_{i+1:02d}_{project['name'].lower().replace(' ', '_')}.mp4"
                output_path = self.shorts_dir / output_filename
                
                success = self.create_vertical_crop(
                    str(input_path), 
                    current_time, 
                    short_duration, 
                    output_path
                )
                
                if success:
                    shorts_created.append(str(output_path))
                
                # Advance timeline
                current_time += duration
            else:
                print(f"⚠️  Skipping {project['name']} - Audio asset missing or empty")
            
            # Check for Mid-Roll Subscriber Ad
            if i == midpoint - 1:
                sub_audio = os.path.join(ASSETS_FOLDER, "subscribe_audio.mp3")
                sub_duration = self.get_audio_duration(sub_audio)
                if sub_duration > 0:
                     print(f"ℹ️  Skipping Subscribe Prompt ({sub_duration:.1f}s)")
                     current_time += sub_duration

        
        # Summary
        print(f"\n✅ Generated {len(shorts_created)} YouTube Shorts!")
        print(f"\n📁 Shorts location: {self.shorts_dir}/")
        for short in shorts_created:
            print(f"   - {Path(short).name}")

def main():
    """Main entry point for Shorts generation"""
    extractor = ShortsFromVideoExtractor()
    extractor.generate_shorts_from_video()

if __name__ == "__main__":
    main()
