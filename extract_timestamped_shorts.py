"""
Timestamped YouTube Shorts Extractor
Extracts individual Shorts from longform video using YOUTUBE_DESCRIPTION.md timestamps
Each Short is a separate clip focused on one project
"""

import os
import re
import subprocess
from pathlib import Path
from datetime import datetime

# Configuration
SHORTS_FOLDER = "shorts"
YOUTUBE_DESCRIPTION = "YOUTUBE_DESCRIPTION.md"
MAX_SHORT_DURATION = 59  # YouTube Shorts max


class TimestampedShortsExtractor:
    """Extract individual Shorts from timestamp markers"""
    
    def __init__(self):
        self.shorts_dir = Path(SHORTS_FOLDER)
        self.shorts_dir.mkdir(exist_ok=True)
    
    def find_latest_video(self):
        """Find the most recent github_roundup_*.mp4"""
        import glob
        
        # Try current date first
        current_date = datetime.now().strftime("%b%d").lower()
        video_path = Path(f"github_roundup_{current_date}.mp4")
        if video_path.exists():
            return str(video_path)
        
        # Find most recent
        videos = glob.glob("github_roundup_*.mp4")
        if videos:
            videos.sort(key=os.path.getmtime, reverse=True)
            return videos[0]
        
        return None
    
    def parse_timestamps(self, description_file):
        """Parse YOUTUBE_DESCRIPTION.md for project timestamps"""
        print(f"\n📖 Parsing {description_file}...")
        
        with open(description_file, 'r') as f:
            content = f.read()
        
        # Pattern: "0:07 - **projectname**" or "1:18 - **projectname**"
        pattern = r'(\d+):(\d+)\s*-\s*\*\*([^*]+)\*\*\s*\n\s*🔗\s*(https://github\.com/[^\s]+)'
        
        matches = re.findall(pattern, content)
        
        if not matches:
            print("❌ No timestamp patterns found!")
            return []
        
        projects = []
        for i, match in enumerate(matches):
            minutes = int(match[0])
            seconds = int(match[1])
            project_name = match[2].strip()
            github_url = match[3].strip()
            
            # Convert to seconds
            start_time = minutes * 60 + seconds
            
            projects.append({
                'index': i,
                'name': project_name,
                'url': github_url,
                'start': start_time
            })
        
        # Calculate durations by looking at next project's start time
        for i in range(len(projects)):
            if i < len(projects) - 1:
                # Duration until next project
                projects[i]['duration'] = projects[i + 1]['start'] - projects[i]['start']
            else:
                # Last project: estimate or use max duration
                projects[i]['duration'] = min(MAX_SHORT_DURATION, 60)
        
        print(f"✅ Found {len(projects)} projects with timestamps")
        
        # Display parsed projects
        print("\n📋 Projects to extract:")
        for p in projects:
            start_min = p['start'] // 60
            start_sec = p['start'] % 60
            print(f"   {p['index'] + 1}. {p['name']}")
            print(f"      Start: {start_min}:{start_sec:02d} | Duration: {p['duration']}s")
        
        return projects
    
    def get_video_duration(self, video_path):
        """Get total video duration"""
        cmd = [
            'ffprobe', '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    
    def create_vertical_short(self, input_video, project, output_path):
        """
        Extract segment and convert to vertical format
        Center-crops and ensures text is centered
        """
        start_time = project['start']
        duration = project['duration']
        project_name = project['name']
        
        # Cap duration at YouTube Shorts max
        duration = min(duration, MAX_SHORT_DURATION)
        
        print(f"\n🎬 Creating Short: {project_name}")
        print(f"   ⏱️  Timestamp: {start_time}s | Duration: {duration}s")
        
        # FFmpeg filter for horizontal → vertical conversion
        # 1. Crop the center 960x1080 (keeping max height while cropping width)
        # 2. Scale to 1080x1920 (vertical)
        # 3. Pad to exact 1080x1920 with Code Stream dark blue
        
        filter_complex = (
            f"[0:v]crop=960:1080:(1920-960)/2:0[square];"
            f"[square]scale=1080:1920:force_original_aspect_ratio=increase[scaled];"
            f"[scaled]crop=1080:1920:(1080-1080)/2:(1920-1920)/2[vertical]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', input_video,
            '-t', str(duration),
            '-filter_complex', filter_complex,
            '-map', '[vertical]',
            '-map', '0:a',  # Keep audio
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"   ✅ Short created: {output_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def create_centered_overlay_short(self, input_video, project, output_path):
        """
        Alternative approach: Scale entire frame to fit vertical, add pillars
        Better for keeping text visible but smaller
        """
        start_time = project['start']
        duration = project['duration']
        project_name = project['name']
        
        duration = min(duration, MAX_SHORT_DURATION)
        
        print(f"\n🎬 Creating Short (pillar box): {project_name}")
        
        # Scale to fit height, add pillar bars on sides
        filter_complex = (
            f"[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
            f"pad=1080:1920:(1080-iw)/2:(1920-ih)/2:color=#0a1628[vertical]"
        )
        
        cmd = [
            'ffmpeg', '-y',
            '-ss', str(start_time),
            '-i', input_video,
            '-t', str(duration),
            '-filter_complex', filter_complex,
            '-map', '[vertical]',
            '-map', '0:a',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '23',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            print(f"   ✅ Short created: {output_path.name}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Error: {e}")
            return False
    
    def extract_all_shorts(self, input_video=None, method="crop"):
        """
        Extract all Shorts from video based on timestamps
        
        Args:
            input_video: Path to video (auto-detects if None)
            method: "crop" (center crop) or "pillar" (scale to fit)
        """
        # Find video
        if not input_video:
            input_video = self.find_latest_video()
            if not input_video:
                print("❌ Error: Could not find github_roundup_*.mp4")
                return
        
        input_path = Path(input_video)
        if not input_path.exists():
            print(f"❌ Error: Video not found: {input_video}")
            return
        
        # Check description file
        if not Path(YOUTUBE_DESCRIPTION).exists():
            print(f"❌ Error: {YOUTUBE_DESCRIPTION} not found")
            return
        
        print(f"\n📱 YouTube Shorts Extractor")
        print("=" * 60)
        print(f"📹 Source video: {input_path.name}")
        print(f"📖 Description: {YOUTUBE_DESCRIPTION}")
        
        # Get video info
        video_duration = self.get_video_duration(str(input_path))
        print(f"⏱️  Video duration: {video_duration:.1f} seconds")
        
        # Parse timestamps
        projects = self.parse_timestamps(YOUTUBE_DESCRIPTION)
        
        if not projects:
            return
        
        print(f"\n🎬 Extracting {len(projects)} Shorts...")
        print(f"   Method: {method}")
        print("=" * 60)
        
        # Extract each project as a Short
        short_files = []
        for i, project in enumerate(projects):
            # Sanitize filename
            safe_name = re.sub(r'[^\w\-_]', '_', project['name'].lower())
            output_path = self.shorts_dir / f"short_{i+1:02d}_{safe_name}.mp4"
            
            # Skip if exists
            if output_path.exists():
                print(f"\n⏭️  Skipping {project['name']} (already exists)")
                short_files.append(str(output_path))
                continue
            
            # Create Short
            if method == "crop":
                success = self.create_vertical_short(str(input_path), project, output_path)
            else:  # pillar
                success = self.create_centered_overlay_short(str(input_path), project, output_path)
            
            if success:
                short_files.append(str(output_path))
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"✅ Extracted {len(short_files)} YouTube Shorts!")
        print(f"\n📁 Shorts location: {self.shorts_dir}/")
        
        # Create upload list
        upload_list = self.shorts_dir / "upload_list.txt"
        with open(upload_list, 'w') as f:
            f.write("YouTube Shorts Upload List\n")
            f.write("=" * 40 + "\n\n")
            
            for i, short_path in enumerate(short_files):
                short_name = Path(short_path).name
                project = projects[i] if i < len(projects) else {'name': 'Unknown'}
                
                f.write(f"{i + 1}. {project['name']}\n")
                f.write(f"   File: {short_name}\n")
                f.write(f"   Suggested Title: \"{project['name']} - Amazing Open Source Project! #shorts\"\n")
                f.write(f"   Description: Check out {project['name']}! 🔗 {project.get('url', '')}\n\n")
        
        print(f"📝 Upload guide: {upload_list}")
        print(f"\n🎉 Ready to upload to YouTube!")
        print("=" * 60)


def main():
    """Main entry point"""
    extractor = TimestampedShortsExtractor()
    
    print("\n📱 YouTube Shorts Extractor (Timestamp-Based)")
    print("=" * 60)
    print("Extracts individual Shorts from YOUTUBE_DESCRIPTION.md timestamps")
    
    # Find video
    video_path = extractor.find_latest_video()
    if video_path:
        print(f"✅ Found video: {Path(video_path).name}")
    else:
        print("⚠️  No github_roundup_*.mp4 found")
        return
    
    # Choose method
    print("\n📐 Choose conversion method:")
    print("   1. Center Crop (default) - Crops sides, keeps center focused")
    print("   2. Pillar Box - Scales down, adds side bars (keeps everything)")
    
    try:
        choice = input("\nEnter choice (default=1): ").strip() or "1"
        method = "crop" if choice == "1" else "pillar"
    except:
        method = "crop"
    
    # Extract
    extractor.extract_all_shorts(input_video=video_path, method=method)


if __name__ == "__main__":
    main()
