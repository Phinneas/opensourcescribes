"""
Integrated Video Suite
Creates a full GitHub roundup video AND custom YouTube Shorts based on user selection.
Enhanced with MiniMax integration for dynamic content and scrolling animations.
"""

import os
import asyncio
import json
import subprocess
import random
from datetime import datetime
from pathlib import Path
from gtts import gTTS
from typing import Optional, Dict

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Import enhanced modules
try:
    from minimax_integration import get_minimax_generator
    from github_page_capture import GitHubPageCapture
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False
    print("⚠️  MiniMax modules not available - using static graphics only")

# Directories
OUTPUT_FOLDER = "assets"
DATA_FILE = "posts_data.json"
DATA_OUTPUT_FILE = "posts_data_longform.json"

# Video settings - organized delivery structure
current_date_mmdd = datetime.now().strftime("%m-%d")
DELIVERIES_ROOT = "deliveries"
DELIVERY_FOLDER = os.path.join(DELIVERIES_ROOT, current_date_mmdd)
SHORTS_FOLDER_NAME = "shorts"
SHORTS_FOLDER = os.path.join(DELIVERY_FOLDER, SHORTS_FOLDER_NAME)
DEEP_DIVES_FOLDER = os.path.join(DELIVERY_FOLDER, "deep_dives")
LONGFORM_VIDEO = os.path.join(DELIVERY_FOLDER, "longform_github_roundup.mp4")
SHORTS_REEL = os.path.join(DELIVERY_FOLDER, f"github_shorts_{current_date_mmdd}.mp4")

os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(DELIVERY_FOLDER, exist_ok=True)
os.makedirs(DEEP_DIVES_FOLDER, exist_ok=True)
Path(SHORTS_FOLDER).mkdir(exist_ok=True)


MAX_DEEP_DIVES = 3  # Limit deep dives per roundup


class VideoSuite:
    """Creates both longform and short videos with interactive selection"""
    
    def __init__(self):
        self.projects = []
        self.shorts_selection = []
        self.deep_dive_selection = []
        self.use_minimax = CONFIG.get('video_settings', {}).get('use_minimax', True)
        self.minimax_generator = get_minimax_generator() if MINIMAX_AVAILABLE else None
        self.github_capture = GitHubPageCapture() if MINIMAX_AVAILABLE else None
        
    def load_projects(self):
        """Load projects from posts_data.json"""
        try:
            with open(DATA_FILE, 'r') as f:
                self.projects = json.load(f)
            print(f"✅ Loaded {len(self.projects)} projects from {DATA_FILE}")
            
            # Ensure IDs
            for i, p in enumerate(self.projects):
                if 'id' not in p:
                    p['id'] = f"p{i+1}"
            
        except FileNotFoundError:
            print(f"❌ Error: {DATA_FILE} not found. Run auto_script_generator.py first.")
            self.projects = []
            
    def select_shorts(self):
        """Interactive selection for Shorts"""
        print("\n" + "="*60)
        print("📱 SHORTS SELECTION")
        print("="*60)
        
        print("Available Projects:")
        for i, p in enumerate(self.projects):
            print(f"   [{i+1}] {p['name']} (ID: {p['id']})")
            
        print("\nOptions:")
        print("   [A]ll    - Generate Shorts for ALL projects")
        print("   [N]one   - Skip Shorts generation")
        print("   1,3,5    - Enter numbers separated by commas")
        
        choice = input("\nSelect projects for Shorts > ").strip().lower()
        
        self.shorts_selection = []
        
        if choice == 'a' or choice == 'all':
            self.shorts_selection = self.projects
            print(f"✅ Selected ALL {len(self.projects)} projects for Shorts")
        elif choice == 'n' or choice == 'none' or choice == '':
            print("❌ No Shorts will be generated")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                valid_indices = [i for i in indices if 0 <= i < len(self.projects)]
                self.shorts_selection = [self.projects[i] for i in valid_indices]
                print(f"✅ Selected {len(self.shorts_selection)} projects for Shorts")
            except ValueError:
                print("❌ Invalid input. Skipping Shorts.")

    def select_deep_dives(self):
        """Interactive selection for Deep Dives (max 3)"""
        print("\n" + "="*60)
        print(f"🔍 DEEP DIVE SELECTION (max {MAX_DEEP_DIVES})")
        print("="*60)
        
        print("Available Projects:")
        for i, p in enumerate(self.projects):
            print(f"   [{i+1}] {p['name']} (ID: {p['id']})")
            
        print(f"\nOptions:")
        print(f"   [N]one   - Skip Deep Dives")
        print(f"   1,3,5    - Enter up to {MAX_DEEP_DIVES} numbers separated by commas")
        
        choice = input(f"\nSelect up to {MAX_DEEP_DIVES} projects for Deep Dives > ").strip().lower()
        
        self.deep_dive_selection = []
        
        if choice == 'n' or choice == 'none' or choice == '':
            print("❌ No Deep Dives will be generated")
        else:
            try:
                indices = [int(x.strip()) - 1 for x in choice.split(',')]
                valid_indices = [i for i in indices if 0 <= i < len(self.projects)][:MAX_DEEP_DIVES]
                self.deep_dive_selection = [self.projects[i] for i in valid_indices]
                print(f"✅ Selected {len(self.deep_dive_selection)} projects for Deep Dives")
            except ValueError:
                print("❌ Invalid input. Skipping Deep Dives.")
                
    async def prepare_assets(self):
        """Generate graphics and audio for projects with MiniMax enhancement"""
        from branding import create_intro_card, create_outro_card
        
        tasks = []
        
        # 1. Prepare Main Video Assets (with MiniMax if available)
        print(f"\n🎨 Generating Main Video Assets (Horizontal)...")
        
        for project in self.projects:
            # Paths
            img_path = Path(OUTPUT_FOLDER) / f"{project['id']}_screen.png"
            audio_path = Path(OUTPUT_FOLDER) / f"{project['id']}_audio.mp3"
            
            project['img_path'] = str(img_path)
            project['audio_path'] = str(audio_path)
            
            # Generate Audio (if not exists)
            self.generate_audio(project['script_text'], str(audio_path))
            
            # Try MiniMax enhancement first
            if self.use_minimax and self.minimax_generator and self.minimax_generator.enabled:
                minimax_video = await self.generate_minimax_enhancement(project)
                if minimax_video:
                    project['enhanced_video'] = minimax_video
                    print(f"   ✅ MiniMax enhanced video generated")
                    continue
            
            # Fallback to static graphic
            # specific logic to not regenerate if exists? 
            # Handled inside create_project_graphic mostly, but let's be safe
            tasks.append(self.create_project_graphic(
                project['name'],
                project['github_url'],
                str(img_path)
            ))
            
        # 2. Prepare Shorts Assets (Vertical)
        if self.shorts_selection:
            print(f"\n🎨 Generating Shorts Assets (Vertical)...")
            for project in self.shorts_selection:
                short_img_path = Path(SHORTS_FOLDER) / f"{project['id']}_short.png"
                # Reuse audio from main video
                project['short_img_path'] = str(short_img_path)
                
                tasks.append(self.create_shorts_graphic(
                    project['name'],
                    project['github_url'],
                    str(short_img_path)
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
        """Create horizontal graphic (1920x1080)"""
        from codestream_graphics import CodeStreamGraphics
        
        if os.path.exists(output_path):
            return
        
        print(f"   Horizontal: {project_name}")
        
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
         """Create vertical graphic (1080x1920)"""
         from PIL import Image, ImageDraw, ImageFont
         from codestream_graphics import CodeStreamGraphics, COLORS
         
         if os.path.exists(output_path):
             return
         
         print(f"   Vertical: {project_name}")
         
         # Reuse the class but force dimensions manually
         graphics = CodeStreamGraphics(output_dir=Path(output_path).parent)
         graphics.width = 1080
         graphics.height = 1920
         
         loop = asyncio.get_event_loop()
         await loop.run_in_executor(
            None,
            self._generate_vertical_image_sync,
            graphics,
            project_name,
            github_url,
            output_path
        )

    def _generate_vertical_image_sync(self, graphics, project_name, github_url, output_path):
        """Synchronous part of vertical image generation"""
        from codestream_graphics import COLORS
        from PIL import Image, ImageDraw, ImageFont

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
        img = graphics.add_grid_pattern(img)
        img = graphics.add_data_flow_lines(img)
        img = graphics.add_glow_accents(img)
        
        # New draw object for the new image
        draw = ImageDraw.Draw(img)
        
        # Branding at bottom
        branding_y = 1920 - 200
        draw.text((margin, branding_y), "Open Source Scribes", font=desc_font, fill=COLORS['electric_green'])
        draw.text((1080 - 250, branding_y), "#Shorts", font=stats_font, fill=COLORS['electric_teal'])
        
        # Save
        img.save(output_path)

    async def generate_minimax_enhancement(self, project) -> Optional[str]:
        """Generate MiniMax-enhanced video content for a project"""
        if not self.use_minimax or not self.minimax_generator or not self.minimax_generator.enabled:
            return None
        
        print(f"\n🎬 Generating MiniMax-enhanced video for {project['name']}...")
        
        try:
            # Generate UI demonstration based on project
            project_name = project['name']
            description = project.get('script_text', '')
            
            # Create prompt for UI demo
            ui_prompt = f"""A professional, smooth demonstration of {project_name}, which {description.lower()}, 
            showing modern interface elements, animations, and interactive features. High quality rendering with 
            cinematic camera movements revealing the application's capabilities."""
            
            # Generate video
            video_path = Path(OUTPUT_FOLDER) / f"{project['id']}_minimax_enhanced.mp4"
            
            result = self.minimax_generator.generate_ui_demonstration(
                ui_prompt,
                str(video_path)
            )
            
            return result
            
        except Exception as e:
            print(f"⚠️  MiniMax enhancement failed: {e}")
            return None

    async def generate_captures_and_code_animations(self, project):
        """Generate GitHub page captures and code animations for a project"""
        if not self.github_capture:
            return None
        
        print(f"\n🎬 Generating GitHub captures and code animations for {project['name']}...")
        
        try:
            # Capture GitHub page scrolling
            github_url = project['github_url']
            captures = self.github_capture.capture_all_key_sections(github_url)
            
            project['github_captures'] = captures
            print(f"   ✅ Captured {len(captures)} GitHub sections")
            
            # Generate code animation
            if self.minimax_generator and self.minimax_generator.enabled:
                # Find sample code from description
                description = project.get('script_text', '')
                # Extract potential code snippet or use placeholder
                code_snippet = f"# {project['name']} implementation\nimport os\nfrom typing import List\n\ndef process_data(data: List[str]) -> List[str]:\n    # Process and transform data\n    return [d.upper() for d in data]"
                
                code_animation_path = Path(OUTPUT_FOLDER) / f"{project['id']}_code_animation.mp4"
                
                language = project.get('metadata', {}).get('language', 'python')
                result = self.minimax_generator.generate_code_animation(
                    code_snippet,
                    language,
                    str(code_animation_path)
                )
                
                if result:
                    project['code_animation'] = result
                    print(f"   ✅ Generated code animation")
            
            return captures
            
        except Exception as e:
            print(f"⚠️  Failed to generate captures/animations: {e}")
            return None

    def create_segment(self, project, index, is_short=False):
        """Create video segment"""
        if is_short:
            image_path = project.get('short_img_path', project.get('img_path'))
            # Re-use audio from main video
            audio_path = project['audio_path']
            output_path = Path(SHORTS_FOLDER) / f"short_{project['id']}.mp4"
            print(f"🎬 Rendering Short: {project['name']}")
        else:
            # Check for enhanced video first
            if 'enhanced_video' in project:
                # Copy MiniMax-enhanced video as segment
                enhanced_src = project['enhanced_video']
                output_path = Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4"
                subprocess.run(['cp', enhanced_src, output_path], check=True)
                print(f"🎬 Using enhanced video: {project['name']}")
                return str(output_path)
            
            image_path = project.get('img_path')
            audio_path = project['audio_path']
            output_path = Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4"
            print(f"🎬 Rendering Segment: {project['name']}")
        
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
    
    def assemble_longform_video(self):
        """Assemble full longform video"""
        from branding import create_intro_card, create_outro_card

        print(f"\n🎬 Assembling Longform Video...")
        
        # Intro/Outro
        intro_path = create_intro_card(CONFIG, "GitHub Projects Roundup")
        outro_path = create_outro_card(CONFIG)
        
        segment_files = []
        
        # Intro
        if os.path.exists(intro_path):
             # Check for intro audio
            intro_audio = Path(OUTPUT_FOLDER) / "intro_audio.mp3"
            if intro_audio.exists():
                segment_files.append(self.create_static_segment(intro_path, 0, "seg_intro.mp4", audio_path=str(intro_audio)))
            else:
                segment_files.append(self.create_static_segment(intro_path, 3, "seg_intro.mp4"))
        
        # Projects
        for i, project in enumerate(self.projects):
            segment_files.append(self.create_segment(project, i, is_short=False))
            
        # Outro
        if os.path.exists(outro_path):
            segment_files.append(self.create_static_segment(outro_path, 5, "seg_outro.mp4"))
            
        # Concatenate
        self.concatenate_segments(segment_files, LONGFORM_VIDEO)
        
        # Cleanup segments
        for seg in segment_files:
            if os.path.exists(seg):
                os.remove(seg)
                
    def assemble_shorts(self):
        """Assemble individual Shorts"""
        if not self.shorts_selection:
            return
            
        print(f"\n🎬 Assembling Shorts Videos...")
        
        for i, project in enumerate(self.shorts_selection):
            self.create_segment(project, i, is_short=True)
            
        print(f"✅ Created {len(self.shorts_selection)} Shorts in {SHORTS_FOLDER}/")

    async def generate_deep_dives(self):
        """Generate deep dive videos for selected projects"""
        if not self.deep_dive_selection:
            return
            
        print(f"\n🔍 Generating Deep Dive Videos...")
        
        from single_project_video import create_single_project_video
        
        for project in self.deep_dive_selection:
            project_id = project['id']
            output_path = os.path.join(DEEP_DIVES_FOLDER, f"{project_id}_deep_dive.mp4")
            print(f"   Creating deep dive: {project['name']}")
            await create_single_project_video(project_id, output_path)
            
        print(f"✅ Created {len(self.deep_dive_selection)} Deep Dives in {DEEP_DIVES_FOLDER}/")

    def create_static_segment(self, image_path, duration, output_name, audio_path=None):
        """Create static video segment"""
        output_path = Path(OUTPUT_FOLDER) / output_name
        
        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-framerate', '24',
            '-i', image_path
        ]
        
        if audio_path:
            cmd.extend(['-i', audio_path, '-shortest'])
        else:
            cmd.extend(['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=44100', '-t', str(duration)])
            
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return str(output_path)

    def concatenate_segments(self, segment_files, output_name):
        """Concatenate video segments"""
        concat_list = Path("concat_list.txt")
        
        with open(concat_list, 'w') as f:
            for seg in segment_files:
                f.write(f"file '{seg}'\n")
        
        print(f"🔗 Concatenating to {output_name}...")
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac', '-b:a', '192k',
            output_name
        ]
        
        subprocess.run(cmd, check=True)
        print(f"✅ Created: {output_name}")
        
        if concat_list.exists():
            concat_list.unlink()

    async def run(self):
        """Main execution flow"""
        print("\n🎬 Video Suite - Longform + Shorts")
        print("="*60)
        
        # 1. Load Data
        self.load_projects()
        if not self.projects:
            return
            
        # 2. Select Shorts
        self.select_shorts()
        
        # 3. Select Deep Dives
        self.select_deep_dives()
        
        # 4. Save Longform Data for Description Generator
        # (Contains all projects)
        with open(DATA_OUTPUT_FILE, 'w') as f:
            json.dump(self.projects, f, indent=4)
        print(f"\n💾 Saved longform data to {DATA_OUTPUT_FILE}")
            
        # 4. Process Assets
        await self.prepare_assets()
        
        # 5. Assemble Videos
        self.assemble_longform_video()
        self.assemble_shorts()
        
        # 6. Generate Deep Dives
        await self.generate_deep_dives()
        
        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE")
        print("="*60)

if __name__ == "__main__":
    suite = VideoSuite()
    asyncio.run(suite.run())
