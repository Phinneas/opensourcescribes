"""
Automated Video Suite
Creates a full GitHub roundup video, ALL YouTube Shorts, and 3 Random Deep Dives.
NON-INTERACTIVE VERSION.
"""

import os
import sys
import asyncio
import json
import subprocess
import random
import math
from datetime import datetime
from pathlib import Path
from gtts import gTTS
from typing import Optional, Dict

# Import Seedream 5 Generator
from seedream_generator import SeedreamGenerator

# Import content generators
from generate_description import generate_description
from generate_medium_post import main as generate_medium_post
from generate_reddit_post import main as generate_reddit_post
from generate_newsletter import main as generate_newsletter
from reformat_newsletter import main as reformat_newsletter

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# Directories
OUTPUT_FOLDER = "assets"
DATA_FILE = "posts_data.json"
DATA_OUTPUT_FILE = "posts_data_longform.json"

# Video settings - organized delivery structure
current_date_mmdd = os.environ.get("DELIVERY_DATE", datetime.now().strftime("%m-%d"))
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

MAX_DEEP_DIVES = 3  # Limit deep dives per roundup (Set to 0 to disable)

# Legacy feature flag — superseded by Seedream + Remotion pipeline
HYBRID_AVAILABLE = False


class VideoSuiteAutomated:
    """Creates both longform and short videos automatically"""
    
    def __init__(self):
        self.projects = []
        self.shorts_selection = []
        self.deep_dive_selection = []
        self.seedream_generator = SeedreamGenerator()
        self.video_settings = CONFIG.get('video_settings', {})
        
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
            
    def auto_select(self):
        """Automatic selection for Shorts and Deep Dives"""
        print("\n" + "="*60)
        print("🤖 AUTOMATIC SELECTION")
        print("="*60)
        
        # Shorts: Select ALL
        self.shorts_selection = self.projects
        print(f"✅ Selected ALL {len(self.projects)} projects for Shorts")
        
        # Deep Dives: Randomly select 3
        if len(self.projects) <= MAX_DEEP_DIVES:
            self.deep_dive_selection = self.projects
        else:
            self.deep_dive_selection = random.sample(self.projects, MAX_DEEP_DIVES)
        
        print(f"✅ Selected {len(self.deep_dive_selection)} random projects for Deep Dives:")
        for p in self.deep_dive_selection:
            print(f"   - {p['name']}")

    async def prepare_assets(self):
        """Generate graphics and audio for projects"""
        tasks = []

        # 1. GitHub page screenshots for longform scroll segments
        # Run in a subprocess to avoid sync_playwright conflict with asyncio event loop
        print(f"\n📸 Capturing GitHub page screenshots...")
        for project in self.projects:
            try:
                result = subprocess.run(
                    [sys.executable, "github_screenshot.py", project['github_url']],
                    capture_output=True, text=True, timeout=60,
                    cwd=os.path.dirname(os.path.abspath(__file__))
                )
                # Parse the output path from the script's stdout
                screenshot_path = None
                for line in result.stdout.splitlines():
                    if line.startswith("Screenshot saved to:"):
                        screenshot_path = line.split(":", 1)[1].strip()
                        break
                if not screenshot_path:
                    # Derive expected path the same way github_screenshot.py does
                    import re as _re
                    m = _re.search(r"github\.com/([^/]+)/([^/]+)", project['github_url'])
                    if m:
                        slug = f"{m.group(1)}_{m.group(2).rstrip('/')}".lower().replace("-", "_")
                        screenshot_path = f"assets/screenshots/{slug}_github.png"
                if screenshot_path and os.path.exists(screenshot_path):
                    project['screenshot_path'] = screenshot_path
                    print(f"  [screenshot] {project['name']}: {screenshot_path}")
                else:
                    project['screenshot_path'] = ''
                    if result.stderr:
                        print(f"  ⚠️  Screenshot failed for {project['name']}: {result.stderr[-200:]}")
            except Exception as e:
                print(f"  ⚠️  Screenshot failed for {project['name']}: {e}")
                project['screenshot_path'] = ''

        # 2. Prepare Main Video Assets (horizontal graphics for shorts/thumbnails)
        print(f"\n🎨 Generating Main Video Assets (Horizontal)...")
        for project in self.projects:
            img_path = Path(OUTPUT_FOLDER) / f"{project['id']}_screen.png"
            audio_path = Path(OUTPUT_FOLDER) / f"{project['id']}_audio.mp3"

            project['img_path'] = str(img_path)
            project['audio_path'] = str(audio_path)

            # Generate Audio
            self.generate_audio(project['script_text'], str(audio_path))

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
                project['short_img_path'] = str(short_img_path)
                
                tasks.append(self.create_shorts_graphic(
                    project['name'],
                    project['github_url'],
                    str(short_img_path)
                ))
        
        await asyncio.gather(*tasks)

    async def generate_minimax_enhancement(self, project) -> Optional[str]:
        """Generate multiple unique MiniMax clips to fill the narration time exactly"""
        if not self.use_minimax or not self.minimax_generator or not self.minimax_generator.enabled:
            return None
        
        print(f"🎬 Premium Cinematic Enhancement: {project['name']}")
        
        try:
            final_video_path = Path(OUTPUT_FOLDER) / f"{project['id']}_minimax_enhanced.mp4"
            audio_path = project.get('audio_path')
            
            # 1. Calculate clips needed based on audio duration (Each MiniMax clip is 6s)
            duration = self._get_audio_duration(audio_path)
            num_clips_needed = math.ceil(duration / 6)
            # Ensure at least 1 clip and cap it at a reasonable number to save credits if needed, 
            # though here we prioritize quality as requested.
            num_clips_needed = max(1, num_clips_needed)
            
            print(f"   ⏱️  Audio duration: {duration:.2f}s. Generating {num_clips_needed} unique clips.")
            
            # 2. Take screenshots for each required segment
            project_url = project.get('github_url')
            project_id = project['id']
            
            if self.github_capture:
                loop = asyncio.get_event_loop()
                screenshot_paths = await loop.run_in_executor(
                    None, 
                    self.github_capture.take_multi_screenshots, 
                    project_url, 
                    project_id,
                    num_clips_needed
                )
            else:
                screenshot_paths = []

            if not screenshot_paths:
                print("   ⚠️  Capture failed, using fallback UI demo")
                return self.minimax_generator.generate_ui_demonstration(
                    f"A professional demonstration of {project['name']}.", 
                    str(final_video_path)
                )

            # 3. Generate unique motions for each clip
            # Choose unique motions from library, reusing if num_clips > library size
            motions = random.sample(MOTION_LIBRARY, min(num_clips_needed, len(MOTION_LIBRARY)))
            if num_clips_needed > len(motions):
                extra_needed = num_clips_needed - len(motions)
                motions.extend(random.choices(MOTION_LIBRARY, k=extra_needed))
            
            clip_paths = []
            for i, (path, motion) in enumerate(zip(screenshot_paths, motions)):
                segment_path = Path(OUTPUT_FOLDER) / f"{project_id}_enh_seg_{i}.mp4"
                
                # REUSE existing segments if they exist to save credits
                if segment_path.exists() and segment_path.stat().st_size > 1000:
                    print(f"   ♻️  Reusing existing segment {i+1}: {segment_path.name}")
                    clip_paths.append(str(segment_path))
                    continue
                
                prompt = f"{motion} Modern professional studio lighting. Clean interface for {project['name']}."
                
                print(f"   🪄  Animating segment {i+1}/{num_clips_needed}: {motion[:40]}...")
                res = self.minimax_generator.generate_image_to_video(path, prompt, str(segment_path))
                if res:
                    clip_paths.append(res)

            # 4. Sequence clips
            if len(clip_paths) > 1:
                print(f"   🔗 Stitching {len(clip_paths)} unique cinematic angles...")
                concat_list = Path(OUTPUT_FOLDER) / f"{project_id}_concat_list.txt"
                with open(concat_list, 'w') as f:
                    for clip in clip_paths:
                        # Use only the filename since the list is in the same directory
                        f.write(f"file '{os.path.basename(clip)}'\n")
                
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'concat', '-safe', '0',
                    '-i', str(concat_list),
                    '-c', 'copy',
                    str(final_video_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                return str(final_video_path)
            elif clip_paths:
                return clip_paths[0]
            
            return None
            
        except Exception as e:
            print(f"⚠️  MiniMax cinematic enhancement failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def render_remotion_scene(
        self,
        composition: str,
        props: dict,
        output_path: Path,
        duration_seconds: float
    ) -> Path:
        """
        Render a Remotion composition scene via subprocess.
        
        Args:
            composition: Remotion composition ID (e.g., "IntroScene", "SegmentScene")
            props: Props dict for the composition
            output_path: Output video file path
            duration_seconds: Duration in seconds
            
        Returns:
            Path to rendered video
        """
        fps = self.video_settings.get('fps', 30)
        duration_frames = int(duration_seconds * fps)
        
        # Resolve output path to absolute so Remotion (cwd=remotion_video) writes to the right place
        abs_output = Path(output_path).resolve()

        # Remotion only serves files from its public/ folder.
        # Copy any local file paths in props there and pass just the filename.
        remotion_public = Path(__file__).parent / 'remotion_video' / 'public'
        remotion_public.mkdir(parents=True, exist_ok=True)
        resolved_props = {}
        for k, v in props.items():
            if isinstance(v, str) and os.path.exists(v):
                src = Path(v).resolve()
                dest = remotion_public / src.name
                import shutil
                shutil.copy2(src, dest)
                resolved_props[k] = src.name  # Remotion resolves from public/ root
            else:
                resolved_props[k] = v

        # Build remotion render command
        cmd = [
            'npx', 'remotion', 'render',
            'src/index.ts',
            composition,
            '--props', json.dumps(resolved_props),
            '--output', str(abs_output),
            '--frame-range', f'0-{duration_frames - 1}'
        ]
        
        print(f"  Rendering {composition} ({duration_seconds}s)...")
        result = subprocess.run(
            cmd,
            cwd=Path(__file__).parent / 'remotion_video',
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            raise RuntimeError(f"Remotion render failed: {result.stderr}")

        if not abs_output.exists():
            raise FileNotFoundError(f"Remotion output not found: {abs_output}")
        
        print(f"  ✓ Rendered to {output_path.name}")
        return output_path

    def _get_audio_duration(self, audio_path: str) -> float:
        """Helper to get audio duration using ffprobe"""
        if not os.path.exists(audio_path):
            return 6.0  # Default to one MiniMax clip duration
        try:
            cmd = [
                'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1', audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return float(result.stdout.strip())
        except:
            return 6.0
        
    def generate_audio(self, text, output_path):
        """Generate audio: MiniMax → Hume → gTTS fallback"""

        import re

        # Phonetic corrections for common technical terms/acronyms
        pronunciation_map = {
            "webmcp": "Web M C P",
            "sqlite": "sequel lite",
            "github": "git hub",
            "substack": "sub stack",
            "osmnx": "O S M N X"
        }
        processed_text = text
        for term, phonetic in pronunciation_map.items():
            processed_text = re.sub(rf'\b{term}\b', phonetic, processed_text, flags=re.IGNORECASE)

        if os.path.exists(output_path):
            # Reject suspiciously small cached files (e.g. old JSON errors saved as audio)
            if os.path.getsize(output_path) < 1000:
                os.remove(output_path)
                print(f"⚠️  Removed invalid cached audio at {output_path}")
            else:
                return

        # 1. MiniMax T2A v2 — international platform (api.minimax.io)
        minimax_key   = CONFIG.get('minimax', {}).get('api_key', '')
        minimax_group = CONFIG.get('minimax', {}).get('group_id', '')
        if minimax_key and minimax_group:
            try:
                import requests as _req
                voice_id = CONFIG.get('voice', {}).get('minimax_voice_id', 'male-qn-qingse')
                speed    = CONFIG.get('voice', {}).get('minimax_speed', 1.0)
                print(f"🎙️ MiniMax: {processed_text[:50]}...")
                url = f"https://api.minimax.io/v1/t2a_v2?GroupId={minimax_group}"
                resp = _req.post(url, headers={
                    "Authorization": f"Bearer {minimax_key}",
                    "Content-Type": "application/json",
                }, json={
                    "model": "speech-02-hd",
                    "text": processed_text,
                    "stream": False,
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": speed,
                        "vol": 1.0,
                        "pitch": 0,
                    },
                    "audio_setting": {
                        "sample_rate": 32000,
                        "bitrate": 128000,
                        "format": "mp3",
                        "channel": 1,
                    },
                }, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("base_resp", {}).get("status_code") == 0:
                        audio_hex = data.get("data", {}).get("audio", "")
                        if audio_hex:
                            audio_bytes = bytes.fromhex(audio_hex)
                            with open(output_path, "wb") as f:
                                f.write(audio_bytes)
                            try:
                                self.trim_audio_silence(output_path)
                            except Exception:
                                pass
                            return True
                        else:
                            print("⚠️  MiniMax: no audio in response")
                    else:
                        print(f"⚠️  MiniMax error: {data.get('base_resp')}")
                else:
                    print(f"⚠️  MiniMax HTTP {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                print(f"⚠️  MiniMax failed: {e}")

        # 2. Hume (fallback)
        hume_key = CONFIG.get('hume_ai', {}).get('api_key', '')
        if hume_key:
            try:
                from hume import HumeClient
                from hume.tts import PostedUtterance
                print(f"🎙️ Hume: {processed_text[:50]}...")
                client = HumeClient(api_key=hume_key)
                audio_generator = client.tts.synthesize_file(
                    utterances=[PostedUtterance(text=processed_text)]
                )
                audio_bytes = b''.join(chunk for chunk in audio_generator)
                if len(audio_bytes) < 1000:
                    raise ValueError(f"Hume returned {len(audio_bytes)} bytes")
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                try:
                    self.trim_audio_silence(output_path)
                except Exception:
                    pass
                return True
            except Exception as e:
                print(f"⚠️  Hume failed: {e}")

        # 3. gTTS (last resort)
        print(f"🎙️ gTTS: {processed_text[:50]}...")
        tts = gTTS(text=processed_text, lang='en')
        tts.save(output_path)
        try:
            self.trim_audio_silence(output_path)
        except Exception:
            pass
        return True
    
    def trim_audio_silence(self, input_path):
        """Trim silence from beginning — silently skips if ffmpeg fails."""
        temp_path = input_path.replace('.mp3', '_trimmed.mp3')
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-af', 'silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB',
            temp_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if result.returncode == 0 and os.path.exists(temp_path):
            os.replace(temp_path, input_path)
        else:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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
         from codestream_graphics import CodeStreamGraphics
         
         if os.path.exists(output_path):
             return
         
         print(f"   Vertical: {project_name}")
         
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

        img = graphics.create_base_image()
        draw = ImageDraw.Draw(img)
        stats = graphics.get_github_stats(github_url)
        
        margin = 80
        title_y = 300
        
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 80)
            desc_font = ImageFont.truetype("Arial.ttf", 48)
            stats_font = ImageFont.truetype("Arial.ttf", 42)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            stats_font = ImageFont.load_default()
        
        draw.text((margin, title_y), project_name, font=title_font, fill=COLORS['white'])
        
        if stats:
            y_offset = title_y + 150
            stats_text = f"⭐ {stats.get('stars', 'N/A')} | 🔄 {stats.get('forks', 'N/A')} forks"
            draw.text((margin, y_offset), stats_text, font=stats_font, fill=COLORS['electric_teal'])
            y_offset += 80
            
            if stats.get('description'):
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
                
                for i, line in enumerate(lines[:3]):
                    draw.text((margin, y_offset + i * 70), line, font=desc_font, fill=COLORS['soft_gray'])
        
        img = graphics.add_grid_pattern(img)
        img = graphics.add_data_flow_lines(img)
        img = graphics.add_glow_accents(img)
        
        draw = ImageDraw.Draw(img)
        branding_y = 1920 - 200
        draw.text((margin, branding_y), "Open Source Scribes", font=desc_font, fill=COLORS['electric_green'])
        draw.text((1080 - 250, branding_y), "#Shorts", font=stats_font, fill=COLORS['electric_teal'])
        
        img.save(output_path)

    def create_segment(self, project, index, is_short=False):
        """Create video segment"""
        if is_short:
            image_path = project['short_img_path']
            audio_path = project['audio_path']
            output_path = Path(SHORTS_FOLDER) / f"short_{project['id']}.mp4"
            print(f"🎬 Rendering Short: {project['name']}")
        else:
            # Check for enhanced video first
            if 'enhanced_video' in project:
                enhanced_src = project['enhanced_video']
                audio_path = project['audio_path']
                output_path = Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4"
                
                print(f"🎬 Merging audio with enhanced video: {project['name']}")
                
                # Combine video and audio, looping the video if narration is longer
                cmd = [
                    'ffmpeg', '-y',
                    '-stream_loop', '-1',  # Loop input video
                    '-i', enhanced_src,
                    '-i', audio_path,
                    '-c:v', 'libx264', '-preset', 'ultrafast',
                    '-c:a', 'aac', '-b:a', '192k',
                    '-pix_fmt', 'yuv420p',
                    '-map', '0:v:0',      # Use video from first input
                    '-map', '1:a:0',      # Use audio from second input
                    '-shortest',          # Match duration to audio
                    str(output_path)
                ]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                return str(output_path)
                
            image_path = project.get('img_path', '')
            audio_path = project['audio_path']
            output_path = Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4"
            print(f"🎬 Rendering Segment: {project['name']}")

        # Full pipeline: Gemini image → Ken Burns → Remotion overlay → composite
        if HYBRID_AVAILABLE:
            return self._create_segment_with_overlay(
                project, image_path, audio_path, str(output_path)
            )

        cmd = [
            'ffmpeg', '-y',
            '-loop', '1', '-framerate', '24',
            '-i', str(Path(image_path).resolve()),
            '-i', str(Path(audio_path).resolve()),
            '-r', '24',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p',
            '-shortest',
            str(Path(output_path).resolve())
        ]

        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"⚠️  ffmpeg error (code {result.returncode}): {result.stderr[-500:]}")
        return str(output_path)
    
    def _create_segment_with_overlay(
        self,
        project: Dict,
        fallback_image_path: str,
        audio_path: str,
        output_path: str,
    ) -> str:
        """
        Full segment pipeline:
          1. Generate abstract Gemini background image (falls back to screenshot/card)
          2. Apply Ken Burns effect + audio  → background.mp4
          3. Render Remotion combined overlay → overlay_{id}.webm  (VP8 alpha)
          4. FFmpeg composite: overlay on top of background video
          5. Return final segment path

        If overlay generation fails, the background-only video is returned
        (graceful degradation — no crash).
        """
        project_id = project.get('id', 'unknown')
        bg_video_path = str(Path(OUTPUT_FOLDER) / f"bg_{project_id}.mp4")
        overlay_path = str(Path(OUTPUT_FOLDER) / f"overlay_{project_id}.webm")

        # --- Step 1: Background image ---
        image_path = fallback_image_path
        if self.gemini_image_gen and self.gemini_image_gen.available:
            generated = self.gemini_image_gen.generate_project_image(
                project, fallback_path=fallback_image_path
            )
            if generated and os.path.exists(generated):
                image_path = generated

        if not image_path or not os.path.exists(image_path):
            print(f"  ⚠️  No background image for {project.get('name')} — skipping segment")
            return output_path  # caller handles missing file

        # --- Step 2: Ken Burns + audio → background video ---
        bg_video = create_animated_segment(image_path, audio_path, bg_video_path)

        # --- Step 3: Audio duration (needed for overlay timing) ---
        try:
            probe = subprocess.run(
                [
                    "ffprobe", "-v", "error",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path,
                ],
                capture_output=True, text=True, check=True,
            )
            segment_duration = float(probe.stdout.strip())
        except Exception:
            segment_duration = 10.0  # safe fallback

        # --- Step 4: Remotion combined overlay (webm with alpha) ---
        overlay_generated = None
        if self.overlay_gen:
            overlay_generated = self.overlay_gen.generate_combined_overlay(
                project, segment_duration
            )

        # --- Step 5: FFmpeg composite ---
        if overlay_generated and os.path.exists(overlay_generated):
            try:
                composite_cmd = [
                    "ffmpeg", "-y",
                    "-i", bg_video,
                    "-i", overlay_generated,
                    "-filter_complex", "[0:v][1:v]overlay=0:0",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                    "-c:a", "copy",
                    "-pix_fmt", "yuv420p",
                    output_path,
                ]
                subprocess.run(
                    composite_cmd, check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                )
                print(f"  Composited overlay → {output_path}")
            except subprocess.CalledProcessError as e:
                print(f"  ⚠️  Composite failed, using background only: {e.stderr[-200:]}")
                import shutil
                shutil.copy(bg_video, output_path)
            finally:
                # Clean up intermediate files
                for tmp in (bg_video_path, overlay_path):
                    if os.path.exists(tmp) and tmp != output_path:
                        try:
                            os.remove(tmp)
                        except OSError:
                            pass
        else:
            # No overlay — just use background video as-is
            import shutil
            shutil.copy(bg_video, output_path)
            if os.path.exists(bg_video_path) and bg_video_path != output_path:
                try:
                    os.remove(bg_video_path)
                except OSError:
                    pass

        return output_path

    def _fetch_github_stats(self, project: dict) -> tuple:
        """Fetch live star count, forks, language, topics from GitHub API."""
        import re as _re
        import requests as _req
        url = project.get('github_url', '')
        match = _re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if not match:
            return 0, 0, project.get('language', ''), project.get('topics', [])
        owner, repo = match.groups()
        repo = repo.rstrip('/')
        try:
            token = CONFIG.get('github', {}).get('api_key', '')
            headers = {'Authorization': f'token {token}'} if token else {}
            resp = _req.get(f'https://api.github.com/repos/{owner}/{repo}',
                            headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return (
                    data.get('stargazers_count', 0),
                    data.get('forks_count', 0),
                    data.get('language', '') or '',
                    data.get('topics', [])
                )
        except Exception:
            pass
        return 0, 0, project.get('language', ''), project.get('topics', [])

    def _generate_episode_intro(self):
        """
        Build a unique per-episode intro narration script and title
        from the actual project list for this run.
        Both change every episode so no two intros are identical.
        """
        names = [p['name'] for p in self.projects]
        n = len(names)
        date_str = datetime.now().strftime("%B %d")

        # Episode title: date + first two project names
        if n <= 2:
            featured = " & ".join(names)
        else:
            featured = f"{names[0]}, {names[1]} & {n - 2} More"
        episode_title = f"{date_str} — {featured}"

        # Narration: name the first three projects explicitly
        if n == 1:
            name_list = names[0]
        elif n <= 3:
            name_list = ", ".join(names[:-1]) + f" and {names[-1]}"
        else:
            name_list = f"{names[0]}, {names[1]}, {names[2]}, and {n - 3} more"

        script = (
            f"Welcome to OpenSourceScribes. "
            f"This week: {n} open source projects. "
            f"Including {name_list}. "
            f"Let's get into it."
        )

        return script, episode_title

    def assemble_longform_video(self):
        """Assemble full longform video"""
        from branding import create_outro_card

        print(f"\n🎬 Assembling Longform Video...")

        outro_path = create_outro_card(CONFIG)
        segment_files = []

        # Always regenerate intro audio — script is unique per episode
        intro_audio = Path(OUTPUT_FOLDER) / "intro_audio.mp3"
        intro_script, episode_title = self._generate_episode_intro()
        print(f"   Episode title: {episode_title}")
        self.generate_audio(intro_script, str(intro_audio))

        # Render intro via Remotion — hard dependency, no fallback
        intro_duration = self.video_settings.get('intro_duration', 6)
        intro_output = Path(OUTPUT_FOLDER) / "seg_intro.mp4"
        
        intro_props = {
            "episodeTitle": episode_title,
            "channelName": CONFIG.get('branding', {}).get('channel_name', 'OpenSourceScribes')
        }
        
        self.render_remotion_scene(
            composition="IntroScene",
            props=intro_props,
            output_path=intro_output,
            duration_seconds=intro_duration
        )
        
        segment_files.append(str(intro_output))
        
        # Generate segments using Seedream + Remotion
        for i, project in enumerate(self.projects):
            print(f"\n🎬 Processing segment {i + 1}/{len(self.projects)}: {project['name']}")
            
            # 1. Fetch live GitHub stats so star/fork counts are accurate
            stars, forks, language, topics = self._fetch_github_stats(project)

            # 2. Copy GitHub screenshot to Remotion public/ and build props
            screenshot_src = project.get('screenshot_path', '')
            segment_duration = self.video_settings.get('segment_duration', 42)
            segment_output = Path(OUTPUT_FOLDER) / f"seg_{i:03d}.mp4"

            segment_props = {
                "screenshotPath": str(Path(screenshot_src).resolve()) if screenshot_src and os.path.exists(screenshot_src) else '',
                "projectName": project['name'],
                "description": project.get('description', ''),
                "stars": stars,
                "forks": forks,
                "language": language,
                "topics": topics,
            }

            self.render_remotion_scene(
                composition="SegmentScene",
                props=segment_props,
                output_path=segment_output,
                duration_seconds=segment_duration
            )

            # 4. Merge narration audio into the Remotion segment
            audio_path = project.get('audio_path', '')
            if audio_path and os.path.exists(audio_path):
                merged = Path(OUTPUT_FOLDER) / f"seg_{i:03d}_av.mp4"
                merge_cmd = [
                    'ffmpeg', '-y',
                    '-i', str(segment_output.resolve()),
                    '-i', str(Path(audio_path).resolve()),
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                    '-shortest',
                    str(merged.resolve())
                ]
                result = subprocess.run(merge_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                if result.returncode == 0:
                    merged.replace(segment_output)
                else:
                    print(f"⚠️  Audio merge failed: {result.stderr[-200:]}")

            segment_files.append(str(segment_output))
            
            # 3. Render transition between segments (except after last)
            if i < len(self.projects) - 1:
                transition_duration = self.video_settings.get('transition_duration', 1)
                transition_output = Path(OUTPUT_FOLDER) / f"trans_{i:03d}.mp4"
                
                # Cycle through transition styles
                transition_styles = ['wipe', 'sweep', 'flash']
                transition_style = transition_styles[i % len(transition_styles)]
                
                self.render_remotion_scene(
                    composition="TransitionScene",
                    props={"style": transition_style},
                    output_path=transition_output,
                    duration_seconds=transition_duration
                )
                
                segment_files.append(str(transition_output))
            
            # Mid-roll subscribe at ~1/3 through the video
            subscribe_position = len(self.projects) // 3
            if i == subscribe_position:
                sub_card = Path(OUTPUT_FOLDER) / "subscribe_card.png"
                sub_audio = Path(OUTPUT_FOLDER) / "subscribe_audio.mp3"
                if not sub_card.exists():
                    from branding import create_subscribe_card
                    create_subscribe_card(CONFIG, str(sub_card))
                
                if sub_card.exists() and sub_audio.exists():
                    print(f"🎬 Adding mid-roll subscribe prompt at position {i + 1}/{len(self.projects)}...")
                    segment_files.append(self.create_static_segment(str(sub_card), 0, "seg_subscribe.mp4", audio_path=str(sub_audio)))
            
        if os.path.exists(outro_path):
            segment_files.append(self.create_static_segment(outro_path, 5, "seg_outro.mp4"))
            
        self.concatenate_segments(segment_files, LONGFORM_VIDEO)
        
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
            try:
                # We need to ensure we don't have overlapping event loops
                await create_single_project_video(project_id, output_path)
            except Exception as e:
                print(f"❌ Failed deep dive for {project['name']}: {e}")
            
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
            # Normalize audio to mono 48kHz to match segment format
            cmd.extend([
                '-i', audio_path,
                '-af', 'aformat=channel_layouts=mono:sample_rates=48000',
                '-shortest'
            ])
        else:
            # Use mono 48kHz silent audio to match segment format
            cmd.extend(['-f', 'lavfi', '-i', 'anullsrc=channel_layout=mono:sample_rate=48000', '-t', str(duration)])
            
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return str(output_path)

    def concatenate_segments(self, segment_files, output_name):
        """Concatenate video segments with Remotion transitions between them"""
        concat_list = Path("concat_list.txt")

        # Insert Remotion transition clips between segments when available
        all_files = list(segment_files)
        if HYBRID_AVAILABLE and len(segment_files) > 1:
            transition_gen = TransitionGenerator()
            all_files = []
            for i, seg in enumerate(segment_files):
                all_files.append(seg)
                if i < len(segment_files) - 1:
                    transition = transition_gen.select_transition(i, len(segment_files), 8.0)
                    if transition:
                        transition_path = os.path.join(transition_gen.transitions_dir, transition)
                        if os.path.exists(transition_path):
                            all_files.append(transition_path)
            if len(all_files) > len(segment_files):
                print(f"🎬 Inserted {len(all_files) - len(segment_files)} Remotion transitions")

        with open(concat_list, 'w') as outfile:
            for seg in all_files:
                outfile.write(f"file '{seg}'\n")

        print(f"🔗 Concatenating to {output_name}...")
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_list),
            '-vf', 'fps=30',           # force constant 30fps — fixes non-monotonic PTS
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-profile:v', 'high', '-level', '4.0',
            '-bf', '0',                # disable B-frames — guarantees monotonic PTS
            '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-ac', '2',
            '-movflags', '+faststart',
            output_name
        ]

        subprocess.run(cmd, check=True)
        print(f"✅ Created: {output_name}")

        if concat_list.exists():
            concat_list.unlink()

    async def run(self):
        """Main execution flow"""
        print("\n🎬 Video Suite - Automated Workflow")
        print("="*60)
        
        self.load_projects()
        if not self.projects:
            return
            
        self.auto_select()
        
        await self.prepare_assets()
        
        # Save project data AFTER assets are prepared to include enhanced_video paths
        with open(DATA_OUTPUT_FILE, 'w') as f:
            json.dump(self.projects, f, indent=4)
        print(f"\n💾 Saved longform data with asset paths to {DATA_OUTPUT_FILE}")
        
        self.assemble_longform_video()
        self.assemble_shorts()
        await self.generate_deep_dives()
        
        print("\n📝 Generating content suite (Description, Blog, Social)...")
        try:
            generate_description()
            generate_medium_post()
            generate_reddit_post()
            generate_newsletter()
            print("✨ Reformatting newsletter for Substack premium layout...")
            try:
                reformat_newsletter()
            except Exception as re_e:
                print(f"⚠️ Reformatting failed: {re_e}")
            print("✅ Content suite generated successfully")
        except Exception as e:
            print(f"⚠️ Failed to generate content suite: {e}")
        
        # Record published URLs so discovery tools never surface them again
        self._mark_published(self.projects)

        print("\n" + "="*60)
        print("✅ WORKFLOW COMPLETE")
        print("="*60)

    def _mark_published(self, projects: list, seen_file: str = "published_repos.txt") -> None:
        """Record each project's GitHub URL as published in SurrealDB (and txt fallback)."""
        urls = [p["github_url"] for p in projects if p.get("github_url")]
        if not urls:
            return

        # Primary: SurrealDB
        try:
            from db import DB
            with DB() as db:
                for p in projects:
                    url = p.get("github_url")
                    if not url:
                        continue
                    db.mark_published(url, {
                        "name":        p.get("name", ""),
                        "description": p.get("description", ""),
                        "stars":       p.get("stars"),
                        "forks":       p.get("forks"),
                        "language":    p.get("language", ""),
                        "topics":      p.get("topics", []),
                    })
            print(f"📋 Marked {len(urls)} repo(s) as published in SurrealDB")
        except Exception as e:
            print(f"[db] Warning: SurrealDB write failed ({e}), using txt fallback")
            # Fallback: plain text
            existing: set = set()
            if os.path.exists(seen_file):
                with open(seen_file, "r") as f:
                    existing = {line.strip() for line in f if line.strip()}
            new_urls = [u for u in urls if u not in existing]
            if new_urls:
                with open(seen_file, "a") as f:
                    for u in new_urls:
                        f.write(u + "\n")
                print(f"📋 Marked {len(new_urls)} repo(s) as published in {seen_file}")

if __name__ == "__main__":
    suite = VideoSuiteAutomated()

    # Log the pipeline run to SurrealDB
    run_id = None
    try:
        from db import DB
        with DB() as _db:
            run_id = _db.start_run()
    except Exception:
        pass

    import sys as _sys
    try:
        asyncio.run(suite.run())
        if run_id:
            from db import DB
            with DB() as _db:
                _db.finish_run(
                    run_id,
                    repos_count=len(suite.projects),
                    success_count=len(suite.projects),
                    error_count=0,
                )
    except Exception as _e:
        if run_id:
            try:
                from db import DB
                with DB() as _db:
                    _db.finish_run(run_id, repos_count=0, success_count=0, error_count=1)
            except Exception:
                pass
        raise
