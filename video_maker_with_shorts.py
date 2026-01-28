"""
Integrated Video Creator - Longform + Shorts
Creates both a full GitHub roundup video AND YouTube Shorts simultaneously
Shorts are created from randomly selected URLs (not extracted from main video)
"""

import os
import asyncio
import json
import subprocess
import random
from datetime import datetime
from pathlib import Path
from gtts import gTTS

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Directories
OUTPUT_FOLDER = "assets"
SHORTS_FOLDER = "shorts"
DATA_FILE = "posts_data.json"
GITHUB_URLS_FILE = "github_urls.txt"

# Video settings
current_date = datetime.now().strftime("%b%d").lower()
LONGFORM_VIDEO = f"github_roundup_{current_date}.mp4"
SHORTS_REEL = f"github_shorts_{current_date}.mp4"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
Path(SHORTS_FOLDER).mkdir(exist_ok=True)


class DualVideoCreator:
    """Creates both longform and short videos in parallel"""
    
    def __init__(self, num_shorts=2):
        self.num_shorts = num_shorts
        self.short_urls = []  # URLs selected for Shorts
        self.longform_urls = []  # Remaining URLs for longform
        
    def load_github_urls(self):
        """Load all GitHub URLs from github_urls.txt"""
        try:
            with open(GITHUB_URLS_FILE, 'r') as f:
                urls = [line.strip() for line in f if line.strip()]
            return urls
        except FileNotFoundError:
            print(f"❌ Error: {GITHUB_URLS_FILE} not found")
            return []
    
    def split_urls(self, all_urls):
        """Randomly select URLs for Shorts, rest go to longform"""
        num_urls = len(all_urls)
        
        # Calculate how many to allocate
        # Rule: Shorts need at least 2 URLs, longform needs at least 3
        max_shorts = min(self.num_shorts, num_urls - 3)
        actual_shorts = max(2, max_shorts)  # At least 2 for Shorts
        
        print(f"\n📊 URL Distribution:")
        print(f"   Total URLs: {num_urls}")
        print(f"   Shorts: {actual_shorts}")
        print(f"   Longform: {num_urls - actual_shorts}")
        
        # Randomly shuffle and split
        shuffled = all_urls.copy()
        random.shuffle(shuffled)
        
        self.short_urls = shuffled[:actual_shorts]
        self.longform_urls = shuffled[actual_shorts:]
        
        print(f"\n🎲 Randomly selected for Shorts:")
        for i, url in enumerate(self.short_urls, 1):
            print(f"   {i}. {url}")
        
        return self.short_urls, self.longform_urls
    
    def extract_project_name(self, url):
        """Extract project name from GitHub URL"""
        # https://github.com/owner/repo -> repo
        parts = url.rstrip('/').split('/')
        if len(parts) >= 2:
            return parts[-1]
        return "Unknown Project"
    
    def create_project_data_for_urls(self, urls, prefix='p'):
        """Create minimal project data structure for URLs"""
        projects = []
        for i, url in enumerate(urls):
            project_name = self.extract_project_name(url)
            projects.append({
                'id': f'{prefix}{i+1}',
                'name': project_name,
                'github_url': url,
                'script_text': f"{project_name} is an incredible open source project. Check it out on GitHub!"
            })
        return projects
    
    async def prepare_assets_for_urls(self, projects, is_short=False):
        """Generate graphics and audio for projects"""
        from branding import create_intro_card, create_outro_card
        
        tasks = []
        output_subdir = Path(SHORTS_FOLDER) if is_short else Path(OUTPUT_FOLDER)
        
        for i, project in enumerate(projects):
            project_id = project['id']
            
            if is_short:
                img_path = output_subdir / f"{project_id}_short.png"
                audio_path = output_subdir / f"{project_id}_short_audio.mp3"
            else:
                img_path = output_subdir / f"{project_id}_screen.png"
                audio_path = output_subdir / f"{project_id}_audio.mp3"
            
            project['img_path'] = str(img_path)
            project['audio_path'] = str(audio_path)
            
            # Generate audio
            self.generate_audio(project['script_text'], str(audio_path))
            
            # Create graphic
            if is_short:
                tasks.append(self.create_shorts_graphic(
                    project['name'],
                    project['github_url'],
                    str(img_path)
                ))
            else:
                tasks.append(self.create_project_graphic(
                    project['name'],
                    project['github_url'],
                    str(img_path)
                ))
        
        await asyncio.gather(*tasks)
    
    def generate_audio(self, text, output_path):
        """Generate audio using Hume.ai or gTTS"""
        if os.path.exists(output_path):
            return
        
        # Try Hume.ai first
        if CONFIG.get('hume_ai', {}).get('use_hume', False):
            try:
                from hume import HumeClient
                from hume.tts import PostedUtterance
                
                print(f"🎙️ Hume.ai: {text[:30]}...")
                client = HumeClient(api_key=CONFIG['hume_ai']['api_key'])
                
                audio_generator = client.tts.synthesize_file(
                    utterances=[PostedUtterance(text=text)]
                )
                
                audio_chunks = []
                for chunk in audio_generator:
                    audio_chunks.append(chunk)
                
                audio_bytes = b''.join(audio_chunks)
                
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                
                self.trim_audio_silence(output_path)
                print(f"   ✅ Hume.ai audio generated")
                return True
            except Exception as e:
                print(f"⚠️  Hume.ai failed: {e}")
        
        # Fallback to gTTS
        print(f"🎙️ gTTS: {text[:30]}...")
        tts = gTTS(text=text, lang='en')
        tts.save(output_path)
        self.trim_audio_silence(output_path)
        return True
    
    def trim_audio_silence(self, input_path):
        """Trim silence from beginning"""
        temp_path = input_path.replace('.mp3', '_trimmed.mp3')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-af', 'silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB',
            temp_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        os.replace(temp_path, input_path)
    
    async def create_project_graphic(self, project_name, github_url, output_path):
        """Create horizontal graphic (1920x1080) for longform video"""
        from codestream_graphics import CodeStreamGraphics
        
        if os.path.exists(output_path):
            return
        
        print(f"🎨 Creating longform graphic: {project_name}")
        
        graphics = CodeStreamGraphics(output_dir=Path(output_path).parent)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            graphics.create_project_graphic,
            project_name,
            github_url,
            output_path
        )
    
    async def create_shorts_graphic(self, project_name, github_url, output_path):
        """Create vertical graphic (1080x1920) for YouTube Short"""
        from PIL import Image, ImageDraw, ImageFont
        from codestream_graphics import CodeStreamGraphics, COLORS
        
        if os.path.exists(output_path):
            return
        
        print(f"🎨 Creating Shorts graphic: {project_name}")
        
        # Create graphics instance with vertical dimensions
        graphics = CodeStreamGraphics(output_dir=Path(output_path).parent)
        graphics.width = 1080
        graphics.height = 1920
        
        # Create base image
        img = graphics.create_base_image()
        draw = ImageDraw.Draw(img)
        
        # Get GitHub stats
        stats = graphics.get_github_stats(github_url)
        
        # Layout settings for vertical
        margin = 80
        title_y = 300
        
        # Fonts
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 80)
            desc_font = ImageFont.truetype("Arial.ttf", 48)
            stats_font = ImageFont.truetype("Arial.ttf", 42)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            stats_font = ImageFont.load_default()
        
        # Draw project name
        draw.text((margin, title_y), project_name, font=title_font, fill=COLORS['white'])
        
        # Draw stats
        if stats:
            y_offset = title_y + 150
            stats_text = f"⭐ {stats.get('stars', 'N/A')} | 🔄 {stats.get('forks', 'N/A')} forks"
            draw.text((margin, y_offset), stats_text, font=stats_font, fill=COLORS['electric_teal'])
            y_offset += 80
            
            if stats.get('description'):
                # Word wrap description
                desc = stats['description']
                words = desc.split()
                lines = []
                current_line = []
                
                for word in words:
                    current_line.append(word)
                    test_line = ' '.join(current_line)
                    bbox = draw.textbbox((0, 0), test_line, font=desc_font)
                    if bbox[2] - bbox[0] > 1080 - 2 * margin:
                        current_line.pop()
                        lines.append(' '.join(current_line))
                        current_line = [word]
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                # Draw description (max 3 lines)
                for i, line in enumerate(lines[:3]):
                    draw.text((margin, y_offset + i * 70), line, font=desc_font, fill=COLORS['soft_gray'])
        
        # Add Code Stream branding
        graphics.add_grid_pattern(img, draw)
        graphics.add_data_flow_lines(img, draw)
        graphics.add_glow_accents(img, draw)
        
        # Branding at bottom
        branding_y = 1920 - 200
        draw.text((margin, branding_y), "Open Source Scribes", font=desc_font, fill=COLORS['electric_green'])
        draw.text((1080 - 250, branding_y), "#Shorts", font=stats_font, fill=COLORS['electric_teal'])
        
        # Save
        img.save(output_path)
        print(f"   ✅ Shorts graphic saved")
    
    def create_segment(self, project, index, is_short=False):
        """Create video segment from image and audio"""
        image_path = project['img_path']
        audio_path = project['audio_path']
        
        if is_short:
            output_path = Path(SHORTS_FOLDER) / f"short_{index:03d}.mp4"
        else:
            output_path = Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4"
        
        print(f"🎬 Rendering segment: {project['name']}")
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-framerate', '24',
            '-i', image_path,
            '-i', audio_path,
            '-r', '24',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return str(output_path)
    
    def assemble_longform_video(self, projects):
        """Assemble full longform video from all segments"""
        from branding import create_intro_card, create_outro_card, create_subscribe_card
        
        print(f"\n🎬 Assembling Longform Video...")
        
        # Create intro/outro
        intro_path = create_intro_card(CONFIG, "GitHub Projects Roundup")
        outro_path = create_outro_card(CONFIG)
        
        segment_files = []
        
        # Intro
        if os.path.exists(intro_path):
            segment_files.append(self.create_static_segment(intro_path, 5, "seg_intro.mp4"))
        
        # Projects
        for i, project in enumerate(projects):
            segment_files.append(self.create_segment(project, i, is_short=False))
        
        # Outro
        if os.path.exists(outro_path):
            segment_files.append(self.create_static_segment(outro_path, 5, "seg_outro.mp4"))
        
        # Concatenate
        self.concatenate_segments(segment_files, LONGFORM_VIDEO)
        
        # Cleanup
        for seg in segment_files:
            if os.path.exists(seg):
                os.remove(seg)
    
    def assemble_shorts_video(self, projects):
        """Assemble Shorts from randomly selected projects"""
        print(f"\n🎬 Assembling Shorts...")
        
        short_files = []
        
        # Each project becomes a Short
        for i, project in enumerate(projects):
            short_files.append(self.create_segment(project, i, is_short=True))
        
        # Compile into reel
        if len(short_files) > 1:
            self.concatenate_segments(short_files, SHORTS_REEL, output_dir=SHORTS_FOLDER)
        
        return short_files
    
    def create_static_segment(self, image_path, duration, output_name):
        """Create static video segment (intro/outro)"""
        output_path = Path(OUTPUT_FOLDER) / output_name
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-framerate', '24',
            '-i', image_path,
            '-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac',
            '-t', str(duration),
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return str(output_path)
    
    def concatenate_segments(self, segment_files, output_name, output_dir="."):
        """Concatenate video segments into final video"""
        concat_list = Path(output_dir) / "concat_list.txt"
        
        with open(concat_list, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        
        output_path = Path(output_dir) / output_name
        
        print(f"🔗 Concatenating to {output_name}...")
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '192k',
            str(output_path)
        ]
        
        subprocess.run(cmd, check=True)
        print(f"✅ Created: {output_path}")
        
        # Cleanup concat list
        if concat_list.exists():
            concat_list.unlink()
    
    async def create_both_videos(self):
        """Main workflow: create both longform and short videos"""
        print("\n🎬 Dual Video Creator for OpenSourceScribes")
        print("=" * 60)
        
        # Load URLs
        all_urls = self.load_github_urls()
        if not all_urls:
            print("❌ No URLs found in github_urls.txt")
            return
        
        # Split URLs
        short_urls, longform_urls = self.split_urls(all_urls)
        
        # Create project data
        short_projects = self.create_project_data_for_urls(short_urls, prefix='s')
        longform_projects = self.create_project_data_for_urls(longform_urls, prefix='p')
        
        print(f"\n📝 Creating project data...")
        print(f"   Shorts: {len(short_projects)} projects")
        print(f"   Longform: {len(longform_projects)} projects")
        
        # Prepare assets (parallel)
        print(f"\n🎨 Generating graphics and audio...")
        
        # Prepare Shorts assets
        await self.prepare_assets_for_urls(short_projects, is_short=True)
        
        # Prepare longform assets
        await self.prepare_assets_for_urls(longform_projects, is_short=False)
        
        # Assemble videos
        print(f"\n🎬 Assembling videos...")
        
        # Assemble Shorts
        short_files = self.assemble_shorts_video(short_projects)
        
        # Assemble longform
        self.assemble_longform_video(longform_projects)
        
        # Summary
        print(f"\n" + "=" * 60)
        print(f"✅ Both videos created successfully!")
        print(f"\n📹 Longform Video:")
        print(f"   - {LONGFORM_VIDEO}")
        print(f"   - {len(longform_projects)} projects")
        print(f"\n📱 YouTube Shorts:")
        print(f"   - {SHORTS_REEL} (compilation)")
        for short in short_files:
            print(f"   - {short}")
        print(f"\n🎉 Ready to upload!")
        print("=" * 60)


def main():
    """Main entry point"""
    print("\n🎬 Dual Video Creator - Longform + Shorts")
    print("=" * 60)
    
    # Get number of Shorts
    try:
        num_shorts = int(input("\nHow many YouTube Shorts to create? (default=2): ").strip() or "2")
        num_shorts = max(1, min(num_shorts, 5))  # Limit to 1-5
    except ValueError:
        num_shorts = 2
    
    print(f"\n📱 Configuration:")
    print(f"   YouTube Shorts: {num_shorts}")
    print(f"   Longform video: All remaining projects")
    
    # Create videos
    creator = DualVideoCreator(num_shorts=num_shorts)
    asyncio.run(creator.create_both_videos())


if __name__ == "__main__":
    main()
