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

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import Seedream 5 Generator
from services.seedream_generator import SeedreamGenerator

# Import content generators
from content.generate_description import generate_description
from content.generate_medium_post import main as generate_medium_post
from content.generate_reddit_post import main as generate_reddit_post
from content.generate_newsletter import main as generate_newsletter
from content.reformat_newsletter import main as reformat_newsletter

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
                print(f"  [screenshot] Capturing {project['name']}...")
                result = subprocess.run(
                    [sys.executable, "services/github_screenshot.py", project['github_url']],
                    capture_output=True, text=True, timeout=60,
                    cwd=str(Path(__file__).parent.parent.parent)
                )
                
                print(f"  [screenshot] Process output:")
                print(f"      stdout preview: {result.stdout[-150:] if result.stdout else 'None'}")
                print(f"      stderr preview: {result.stderr[-150:] if result.stderr else 'None'}")
                
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
                
                print(f"  [screenshot] Derived path: {screenshot_path}")
                print(f"  [screenshot] Path exists: {os.path.exists(screenshot_path) if screenshot_path else 'N/A'}")
                
                if screenshot_path and os.path.exists(screenshot_path):
                    file_size = os.path.getsize(screenshot_path)
                    project['screenshot_path'] = screenshot_path
                    print(f"  ✅ [screenshot] {project['name']}: {screenshot_path} ({file_size//1024}KB)")
                else:
                    project['screenshot_path'] = ''
                    print(f"  ❌ [screenshot] Failed: {result.returncode}")
                    if result.stderr:
                        print(f"      Error details: {result.stderr[-300:]}")
                    print(f"  ⚠️  Will use title card fallback for {project['name']}")
            except subprocess.TimeoutExpired:
                print(f"  ⚠️  [screenshot] Timeout for {project['name']} - will use fallback")
                project['screenshot_path'] = ''
            except Exception as e:
                print(f"  ⚠️  [screenshot] Exception for {project['name']}: {e}")
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

    # ── PIL / FFmpeg renderers (main video rendering) ─────────

    def _render_title_card_image(self, project: dict) -> Path:
        """Generate a 1920x1080 codestream-aesthetic title card PNG via PIL."""
        from PIL import Image, ImageDraw, ImageFont
        import textwrap

        W, H = 1920, 1080
        BG    = (8,   12,  20)
        TEAL  = (0,   212, 255)
        GREEN = (0,   255, 136)
        WHITE = (255, 255, 255)
        GRAY  = (136, 153, 170)
        GOLD  = (255, 215, 0)

        img  = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)

        # Subtle grid
        grid = (*TEAL, 15)
        overlay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        for x in range(0, W, 60):
            od.line([(x, 0), (x, H)], fill=grid, width=1)
        for y in range(0, H, 60):
            od.line([(0, y), (W, y)], fill=grid, width=1)
        img.paste(Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB'))
        draw = ImageDraw.Draw(img)

        # Top bar
        draw.rectangle([(0, 0), (W, 3)], fill=TEAL)

        # Corner accents
        s = 40
        for cx, cy, dx, dy in [(0,0,1,1),(W-1,0,-1,1),(0,H-1,1,-1),(W-1,H-1,-1,-1)]:
            draw.line([(cx, cy), (cx + dx*s, cy)], fill=GREEN, width=2)
            draw.line([(cx, cy), (cx, cy + dy*s)], fill=GREEN, width=2)

        def try_font(paths, size):
            for p in paths:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        mono  = ['/System/Library/Fonts/Menlo.ttc',
                 '/System/Library/Fonts/Courier.ttc',
                 '/Library/Fonts/Courier New.ttf']
        bold  = ['/System/Library/Fonts/HelveticaNeue.ttc',
                 '/System/Library/Fonts/Helvetica.ttc',
                 '/Library/Fonts/Arial Bold.ttf',
                 '/Library/Fonts/Arial.ttf']

        f_label = try_font(mono, 30)
        f_name  = try_font(bold, 96)
        f_desc  = try_font(mono, 32)
        f_stats = try_font(mono, 30)
        f_tag   = try_font(mono, 26)

        # "// OPEN SOURCE"
        label = "// OPEN SOURCE"
        lw = draw.textlength(label, font=f_label)
        draw.text(((W - lw) / 2, 90), label, fill=TEAL, font=f_label)

        # Project name
        name = project.get('name', '')
        nw = draw.textlength(name, font=f_name)
        if nw > W - 120:
            f_name = try_font(bold, int(96 * (W - 120) / nw))
            nw = draw.textlength(name, font=f_name)
        name_y = 220
        draw.text(((W - nw) / 2, name_y), name, fill=WHITE, font=f_name)

        # Divider
        div_y = name_y + 130
        draw.rectangle([(W//2 - 200, div_y), (W//2 + 200, div_y + 2)], fill=TEAL)

        # Description
        desc = project.get('description', '')
        if desc:
            dy = div_y + 36
            for line in textwrap.wrap(desc, width=65)[:2]:
                lw = draw.textlength(line, font=f_desc)
                draw.text(((W - lw) / 2, dy), line, fill=GRAY, font=f_desc)
                dy += 50

        # Stars / forks
        stars    = project.get('stars', 0) or 0
        forks    = project.get('forks', 0) or 0
        language = project.get('language', '') or ''
        topics   = project.get('topics',   []) or []

        def fmt(n):
            return f"{n/1000:.1f}k" if n >= 1000 else str(n)

        sy = H - 175
        draw.text((80,  sy), f"\u2605 {fmt(stars)} stars", fill=GOLD, font=f_stats)
        draw.text((360, sy), f"\u2442 {fmt(forks)} forks", fill=GRAY, font=f_stats)

        # Tag pills
        tags = ([language] if language else []) + list(topics)[:3]
        px, py = 80, sy + 58
        for tag in tags:
            tw  = int(draw.textlength(tag, font=f_tag))
            pad = 14
            pw  = tw + pad * 2
            draw.rounded_rectangle([(px, py), (px + pw, py + 42)],
                                    radius=8, fill=(0, 40, 60), outline=TEAL, width=1)
            draw.text((px + pad, py + 8), tag, fill=TEAL, font=f_tag)
            px += pw + 12

        out = Path(OUTPUT_FOLDER) / f"{project['id']}_title_card.png"
        img.save(str(out))
        return out

    def _render_github_scroll_ffmpeg(self, screenshot_path: str,
                                      output_path: Path, duration: float = 38.0):
        """
        Zoom in (2s) → scroll top-to-bottom (duration-4s) → zoom out (2s).
        Generates frames with Pillow and pipes to FFmpeg.
        """
        from PIL import Image

        FPS       = 30
        W, H      = 1920, 1080
        BG        = (8, 12, 20)
        MIN_SCALE = 0.28
        MAX_SCROLL_PX = 2200
        ZOOM_S    = 2.0

        # Limit maximum scroll duration to prevent excessive processing
        duration = min(duration, 30.0)  # Cap at 30 seconds max

        zoom_in_f  = int(ZOOM_S * FPS)
        zoom_out_f = int(ZOOM_S * FPS)
        scroll_f   = int(duration * FPS) - zoom_in_f - zoom_out_f
        total_f    = zoom_in_f + scroll_f + zoom_out_f

        src = Image.open(screenshot_path).convert('RGB')
        sw, sh = src.size
        scaled_h = int(sh * (W / sw))
        src = src.resize((W, scaled_h), Image.LANCZOS)
        max_scroll = min(MAX_SCROLL_PX, max(0, scaled_h - H))

        cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{W}x{H}', '-pix_fmt', 'rgb24', '-r', str(FPS),
            '-i', 'pipe:0',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p',
            str(output_path),
        ]
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        try:
            for n in range(total_f):
                # Check if process is still alive before writing
                if proc.poll() is not None:
                    raise RuntimeError("FFmpeg process died during frame generation")
                
                if n < zoom_in_f:
                    t = n / zoom_in_f
                    scale    = MIN_SCALE + (1.0 - MIN_SCALE) * t
                    scroll_y = 0
                elif n < zoom_in_f + scroll_f:
                    scale    = 1.0
                    t        = (n - zoom_in_f) / max(scroll_f, 1)
                    scroll_y = int(max_scroll * t)
                else:
                    t        = (n - zoom_in_f - scroll_f) / max(zoom_out_f, 1)
                    scale    = 1.0 - (1.0 - MIN_SCALE) * t
                    scroll_y = max_scroll

                frame = Image.new('RGB', (W, H), BG)
                if scale >= 0.999:
                    cy = min(scroll_y, max(0, scaled_h - H))
                    frame.paste(src.crop((0, cy, W, cy + H)), (0, 0))
                else:
                    dw = int(W * scale)
                    dh = int(H * scale)
                    cy = min(scroll_y, max(0, scaled_h - H))
                    ch = min(H, scaled_h - cy)
                    if ch > 0 and dw > 0 and dh > 0:
                        region  = src.crop((0, cy, W, cy + ch))
                        region  = region.resize((dw, int(ch * scale)), Image.LANCZOS)
                        frame.paste(region, ((W - dw) // 2, (H - int(ch * scale)) // 2))
                
                try:
                    proc.stdin.write(frame.tobytes())
                except BrokenPipeError:
                    raise RuntimeError("FFmpeg pipe broken - process likely crashed")

            _, stderr = proc.communicate()
            if proc.returncode != 0:
                print(f"  ⚠️  Scroll encode failed: {stderr[-200:].decode(errors='replace')}")
        except Exception as e:
            if proc.poll() is None:
                proc.kill()
            print(f"  ⚠️  Scroll render error: {e}")

    def _create_fallback_screenshot(self, project: dict) -> Optional[str]:
        """Create a fallback GitHub-style screenshot when capture fails."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            fallback_path = Path(OUTPUT_FOLDER) / f"{project['id']}_fallback_github.png"
            if fallback_path.exists():
                return str(fallback_path)
            
            W, H = 1920, 1080
            BG = (248, 248, 252)  # GitHub light gray background
            WHITE = (255, 255, 255)
            BLACK = (24, 23, 23)
            GRAY = (88, 96, 105)
            GREEN = (31, 136, 61)
            BLUE = (9, 105, 218)
            
            img = Image.new('RGB', (W, H), BG)
            draw = ImageDraw.Draw(img)
            
            # GitHub-like header
            header_height = 60
            draw.rectangle([(0, 0), (W, header_height)], fill=BG, outline=(224, 224, 224))
            
            repo_name = project.get('name', 'Unknown Repo')
            desc = project.get('description', 'No description available')
            stars = project.get('stars', 0) or 0
            forks = project.get('forks', 0) or 0
            
            def try_font(size):
                fonts = [
                    "/System/Library/Fonts/Menlo.ttc",
                    "/System/Library/Fonts/Helvetica.ttc", 
                    "/Library/Fonts/Arial.ttf",
                    "/System/Library/Fonts/Courier New.ttf"
                ]
                for font in fonts:
                    try:
                        return ImageFont.truetype(font, size)
                    except:
                        pass
                return ImageFont.load_default()
            
            font_large = try_font(48)
            font_medium = try_font(28)
            font_small = try_font(20)
            
            # Repository name in header area
            draw.text((20, header_height + 20), repo_name, fill=BLACK, font=font_large)
            
            # Description area
            draw.rectangle([(20, header_height + 80), (W - 20, header_height + 200)], 
                          fill=WHITE, outline=(224, 224, 224))
            draw.text((40, header_height + 95), desc[:50] + "...", fill=GRAY, font=font_medium)
            
            # Stats area
            stats_y = header_height + 220
            draw.text((40, stats_y), f"⭐ {stars} stars", fill=GREEN, font=font_medium)
            draw.text((200, stats_y), f"🔄 {forks} forks", fill=BLUE, font=font_medium)
            
            # GitHub URL
            url_text = project.get('github_url', 'github.com/owner/repo')
            draw.text((40, stats_y + 40), url_text[-60:], fill=GRAY, font=font_small)
            
            # Add some decorative elements
            for i in range(5):
                y = stats_y + 80 + i * 60
                draw.rectangle([(40, y), (W - 40, y + 40)], fill=WHITE, outline=(224, 224, 224))
                draw.text((60, y + 10), f"GitHub README Section {i+1}", fill=BLACK, font=font_small)
            
            img.save(str(fallback_path))
            print(f"  ✅ Created fallback screenshot: {fallback_path.name}")
            return str(fallback_path)
            
        except Exception as e:
            print(f"  ⚠️  Failed to create fallback screenshot: {e}")
            return None

    def _render_segment_ffmpeg(self, project: dict, i: int, audio_path: str) -> Path:
        """Render one project segment: title card (4s) + scroll (matched to audio)."""
        FPS             = 30
        title_dur       = 4
        
        # Calculate segment duration based on actual audio length
        audio_dur = self._get_audio_duration(audio_path) if audio_path and os.path.exists(audio_path) else 42.0
        segment_dur = max(8.0, audio_dur)  # Minimum 8s total (4s title + 4s scroll)
        scroll_dur = max(4.0, segment_dur - title_dur)  # Minimum 4s scroll
        
        pid             = project['id']
        
        # Check cache for existing segment (performance optimization)
        cache_key = f"{pid}_seg_{int(audio_dur)}s"
        cached_path = Path(OUTPUT_FOLDER) / f"seg_{i:03d}.mp4"
        
        if cached_path.exists() and cached_path.stat().st_size > 100000:  # More than 100KB
            print(f"  ♻️  Using cached segment: {cached_path.name}")
            return cached_path

        print(f"  🖼️  Title card...")
        title_card = self._render_title_card_image(project)

        title_mp4 = Path(OUTPUT_FOLDER) / f"tmp_{pid}_title.mp4"
        subprocess.run([
            'ffmpeg', '-y', '-loop', '1', '-framerate', str(FPS),
            '-i', str(title_card),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-t', str(title_dur), '-r', str(FPS),
            '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,'
                   'pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
            str(title_mp4),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        scroll_mp4  = Path(OUTPUT_FOLDER) / f"tmp_{pid}_scroll.mp4"
        screenshot  = project.get('screenshot_path', '')
        
        # Enhanced screenshot debugging and validation
        print(f"  🔍 Screenshot check for {project['name']}:")
        print(f"      Path: '{screenshot}'")
        print(f"      Exists: {os.path.exists(screenshot) if screenshot else 'N/A'}")
        
        if screenshot and os.path.exists(screenshot):
            file_size = os.path.getsize(screenshot)
            print(f"      Size: {file_size} bytes ({file_size//1024}KB)")
            print(f"  📜 Scroll animation ({scroll_dur}s) using screenshot...")
            self._render_github_scroll_ffmpeg(screenshot, scroll_mp4, duration=scroll_dur)
        else:
            print(f"  ⚠️  No screenshot available — creating fallback...")
            fallback_path = self._create_fallback_screenshot(project)
            if fallback_path and os.path.exists(fallback_path):
                print(f"  📜 Scroll animation ({scroll_dur}s) using fallback...")
                self._render_github_scroll_ffmpeg(fallback_path, scroll_mp4, duration=scroll_dur)
            else:
                print(f"  ⚠️  No fallback available — extending title card")
                subprocess.run([
                    'ffmpeg', '-y', '-loop', '1', '-framerate', str(FPS),
                    '-i', str(title_card),
                    '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
                    '-t', str(scroll_dur), '-r', str(FPS),
                    '-vf', 'scale=1920:1080,format=yuv420p',
                    str(scroll_mp4),
                ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        concat_txt = Path(OUTPUT_FOLDER) / f"tmp_{pid}_concat.txt"
        videoonly  = Path(OUTPUT_FOLDER) / f"tmp_{pid}_vid.mp4"
        with open(concat_txt, 'w') as f:
            f.write(f"file '{title_mp4.resolve()}'\n")
            f.write(f"file '{scroll_mp4.resolve()}'\n")

        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', str(concat_txt),
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-r', str(FPS), '-bf', '0', '-pix_fmt', 'yuv420p',
            str(videoonly),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        seg_out = Path(OUTPUT_FOLDER) / f"seg_{i:03d}.mp4"
        if audio_path and os.path.exists(audio_path):
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(videoonly),
                '-i', str(audio_path),
                '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-ar', '48000', '-ac', '2',
                str(seg_out),
            ], capture_output=True)
            if result.returncode != 0:
                print(f"  ⚠️  Audio merge failed: {result.stderr[-100:].decode(errors='replace')}")
                # Fallback: copy video only without audio
                videoonly.rename(seg_out)
                print(f"  ⚠️  Using video-only fallback for {project['name']}")
            else:
                print(f"  ✅ Segment completed: {seg_out.name} ({seg_out.stat().st_size//1024}KB)")
        else:
            videoonly.rename(seg_out)
            print(f"  ⚠️  No audio, video-only segment for {project['name']}")

        for f in [title_card, title_mp4, scroll_mp4, concat_txt, videoonly]:
            try:
                Path(f).unlink(missing_ok=True)
            except Exception:
                pass

        return seg_out

    def _render_intro_ffmpeg(self, episode_title: str,
                              audio_path: str, output_path: Path):
        """
        Enhanced animated intro: dramatic gradient + prominent particles + 
        channel name reveal + typing effect for episode title + logo branding.
        Pillow frames → FFmpeg pipe.
        Audio is normalized to 48 kHz stereo to match all other segments.
        Falls back to static branding card if PIL fails.
        """
        from PIL import Image, ImageDraw, ImageFont

        FPS = 30
        W, H = 1920, 1080
        BG   = (5, 8, 20)  # Darker, richer background

        audio_dur = (self._get_audio_duration(audio_path)
                     if audio_path and os.path.exists(audio_path) else 6.0)
        dur     = max(6.0, audio_dur)
        total_f = int(dur * FPS)

        channel_name = CONFIG.get('branding', {}).get('channel_name', 'OpenSourceScribes')

        def try_font(size):
            candidates = [
                "/System/Library/Fonts/HelveticaNeue.ttc",
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "/System/Library/Fonts/Helvetica.ttc",
            ]
            for p in candidates:
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
            return ImageFont.load_default()

        f_channel = try_font(96)
        f_title   = try_font(42)
        f_logo    = try_font(28)

        # Enhanced prominent particles (more, larger, brighter)
        import random as _rng
        rng = _rng.Random(42)
        particles = [
            (rng.randint(40, W - 40), rng.randint(40, H - 40),
             rng.randint(25, 80),      rng.uniform(0.15, 0.35))
            for _ in range(40)  # More particles
        ]

        # Logo/welcome text that appears at the bottom
        welcome_text = "Prepared by AI Early Signal"

        vid_only = output_path.with_suffix('.vid.mp4')

        encode_cmd = [
            'ffmpeg', '-y',
            '-f', 'rawvideo', '-vcodec', 'rawvideo',
            '-s', f'{W}x{H}', '-pix_fmt', 'rgb24', '-r', str(FPS),
            '-i', 'pipe:0',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p', str(vid_only),
        ]
        proc = subprocess.Popen(encode_cmd, stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        animated_ok = True
        try:
            for n in range(total_f):
                # Check process health
                if proc.poll() is not None:
                    raise RuntimeError("FFmpeg process died during intro animation")
                
                img  = Image.new('RGB', (W, H), BG)
                draw = ImageDraw.Draw(img)

                # More dramatic gradient with vibrant colors
                for y in range(0, H, 2):
                    t = y / H
                    gradient_color = (
                        int(5 + 25 * t),
                        int(8 + 30 * t), 
                        int(20 + 50 * t + 20 * (1 - abs(t - 0.5) * 2))
                    )
                    draw.line([(0, y), (W, y)], fill=gradient_color)

                # Subtle tech grid background — animate slightly
                for gx in range(0, W, 40):
                    alpha = int(60 + 40 * (gx / W))
                    draw.line([(gx, 0), (gx, H)], fill=(alpha, int(alpha * 1.5), alpha * 3))
                for gy in range(0, H, 40):
                    alpha = int(60 + 40 * (gy / H))
                    draw.line([(0, gy), (W, gy)], fill=(alpha, int(alpha * 1.5), alpha * 3))

                # Enhanced prominent particles — fade in faster and brighter
                p_alpha = min(1.0, n / (FPS * 0.5))  # Faster fade-in
                for px, py, pr, pop in particles:
                    pa = pop * p_alpha
                    # Brighter, vibrant colors
                    base_c = (int(BG[0] + (200 - BG[0]) * pa),
                              int(BG[1] + (220 - BG[1]) * pa),
                              int(BG[2] + (255 - BG[2]) * pa))
                    # Add glow effect
                    glow_color = (min(255, base_c[0] + 30), min(255, base_c[1] + 30), min(255, base_c[2] + 30))
                    draw.ellipse([(px - pr, py - pr), (px + pr, py + pr)], fill=base_c)
                    
                    # Outer glow for larger particles
                    if pr > 50:
                        draw.ellipse([(px - pr+8, py - pr+8), (px + pr+8, py + pr+8)], 
                                    outline=glow_color, width=2)

                # Channel name — enhanced reveal with scale effect
                ch_t = min(1.0, n / (FPS * 1.2))  # Longer reveal
                if ch_t > 0:
                    scale = 0.8 + 0.2 * ch_t  # Scale up effect
                    drift = int(60 * (1.0 - ch_t))
                    ch_y  = int(H * 0.4 - 130 + drift)
                    
                    # Vibrant color gradient for text
                    cr = int(100 + 150 * ch_t)
                    cg = int(170 + 85 * ch_t)
                    cb = 255
                    
                    try:
                        cw_scaled = int(draw.textlength(channel_name, font=f_channel) * scale)
                    except Exception:
                        cw_scaled = int(len(channel_name) * 48 * scale)
                    
                    # Position with scaling effect
                    ch_x = (W - cw_scaled) // 2
                    
                    # Enhanced shadow for depth
                    try:
                        draw.text(((W - cw_scaled) // 2, ch_y + 4), channel_name,
                                  fill=(0, 0, 0), font=f_channel)
                    except:
                        pass
                    
                    draw.text((ch_x, ch_y), channel_name,
                              fill=(cr, cg, cb), font=f_channel)
                    
                    # Enhanced underline with gradient effect
                    uw = int(250 * ch_t)
                    ul_c = (int(cr * 0.9), int(cg * 0.9), 240)
                    draw.rectangle([(W//2 - uw//2, ch_y + 122),
                                    (W//2 + uw//2, ch_y + 126)], fill=ul_c)

                # Episode title — typing effect reveal
                et_raw = max(0.0, n / FPS - 2.0)  # Start after channel name
                et_t   = min(1.0, et_raw / 1.2)
                if et_t > 0:
                    # Typing effect - reveal characters progressively
                    chars_to_show = int(len(episode_title) * et_t)
                    visible_text = episode_title[:max(1, chars_to_show)]
                    
                    er, eg, eb = int(200 + 55 * et_t), int(210 + 45 * et_t), 255
                    
                    try:
                        tw = int(draw.textlength(visible_text, font=f_title))
                    except Exception:
                        tw = int(len(visible_text) * 20)
                    
                    draw.text(((W - tw) // 2, int(H * 0.5 + 90)),
                              visible_text, fill=(er, eg, eb), font=f_title)
                    
                    # Blinking cursor effect
                    if chars_to_show < len(episode_title) and n % 20 < 10:
                        cursor_x = ((W - tw) // 2) + tw + 8
                        draw.rectangle([(cursor_x, int(H * 0.5 + 85)),
                                      (cursor_x + 8, int(H * 0.5 + 125))], fill=(er, eg, eb))

                # Logo/welcome text — fade in later
                logo_raw = max(0.0, n / FPS - 3.5)
                logo_t = min(1.0, logo_raw / 1.5)
                if logo_t > 0:
                    lr, lg, lb = int(180 * logo_t), int(190 * logo_t), 220
                    
                    try:
                        lw = int(draw.textlength(welcome_text, font=f_logo))
                    except Exception:
                        lw = int(len(welcome_text) * 16)
                    
                    draw.text(((W - lw) // 2, H - 80), welcome_text,
                              fill=(lr, lg, lb), font=f_logo)

                try:
                    proc.stdin.write(img.tobytes())
                except BrokenPipeError:
                    raise RuntimeError("FFmpeg pipe broken - process likely crashed")

            _, stderr = proc.communicate()
            if proc.returncode != 0:
                animated_ok = False
                print(f"  ⚠️  Intro animation encode failed: "
                      f"{stderr[-120:].decode(errors='replace')}")
        except Exception as exc:
            if proc.poll() is None:
                proc.kill()
            animated_ok = False
            print(f"  ⚠️  Intro animation failed ({exc}), using static card")

        if not animated_ok:
            from components.graphics.branding import create_intro_card
            card = create_intro_card(CONFIG)
            subprocess.run([
                'ffmpeg', '-y', '-loop', '1', '-framerate', str(FPS),
                '-i', str(card),
                '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
                '-t', str(dur), '-r', str(FPS),
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,'
                       'pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
                str(vid_only),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

        # Merge audio — normalize to 48 kHz stereo so concat demuxer
        # never sees mismatched sample rates between segments.
        if audio_path and os.path.exists(audio_path):
            subprocess.run([
                'ffmpeg', '-y',
                '-i', str(vid_only), '-i', str(audio_path),
                '-map', '0:v:0', '-map', '1:a:0',
                '-c:v', 'copy', '-c:a', 'aac', '-b:a', '192k',
                '-ar', '48000', '-ac', '2',
                str(output_path),
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            vid_only.unlink(missing_ok=True)
        else:
            vid_only.rename(output_path)

    # ── end PIL / FFmpeg renderers ──────────────────────────────────────────

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
        from components.graphics.codestream_graphics import CodeStreamGraphics
        
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
         from components.graphics.codestream_graphics import CodeStreamGraphics
         
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
        from components.graphics.codestream_graphics import COLORS
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

        # Full pipeline: Generate video segment

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

    def _render_fade_transition(self, output_path: Path, duration: float = 1.0):
        """Render a short dark-frame fade transition using FFmpeg lavfi with vignette effect."""
        subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=0x080c14:s=1920x1080:r=30:d={duration}',
            '-f', 'lavfi',
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-t', str(duration),
            '-vf', 'fade=in:0:15, fade=out:15:15, eq=contrast=1.1:brightness=0.95:saturation=0.9',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k',
            str(output_path),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    def assemble_longform_video(self):
        """Assemble full longform video using FFmpeg + PIL."""
        from components.graphics.branding import create_outro_card

        print(f"\n🎬 Assembling Longform Video...")

        outro_path = create_outro_card(CONFIG)
        segment_files = []

        # ── Intro ─────────────────────────────────────────────────────────────
        intro_audio  = Path(OUTPUT_FOLDER) / "intro_audio.mp3"
        intro_output = Path(OUTPUT_FOLDER) / "seg_intro.mp4"
        intro_script, episode_title = self._generate_episode_intro()
        print(f"   Episode title: {episode_title}")
        self.generate_audio(intro_script, str(intro_audio))
        print(f"   Rendering intro...")
        self._render_intro_ffmpeg(episode_title, str(intro_audio), intro_output)
        segment_files.append(str(intro_output))

        # ── Project segments ──────────────────────────────────────────────────
        subscribe_position = max(0, len(self.projects) // 3)

        for i, project in enumerate(self.projects):
            print(f"\n🎬 Segment {i + 1}/{len(self.projects)}: {project['name']}")

            # Refresh GitHub stats directly onto project dict for title card
            stars, forks, language, topics = self._fetch_github_stats(project)
            project['stars']    = stars
            project['forks']    = forks
            project['language'] = language
            project['topics']   = topics

            audio_path = project.get('audio_path', '')
            seg_out = self._render_segment_ffmpeg(project, i, audio_path)
            segment_files.append(str(seg_out))

            # Dark-frame fade between segments (not after the last one)
            if i < len(self.projects) - 1:
                trans_out = Path(OUTPUT_FOLDER) / f"trans_{i:03d}.mp4"
                self._render_fade_transition(trans_out, duration=1.0)
                segment_files.append(str(trans_out))

            # Mid-roll subscribe card at ~1/3 through
            if i == subscribe_position:
                sub_card  = Path(OUTPUT_FOLDER) / "subscribe_card.png"
                sub_audio = Path(OUTPUT_FOLDER) / "subscribe_audio.mp3"
                if not sub_card.exists():
                    from components.graphics.branding import create_subscribe_card
                    create_subscribe_card(CONFIG, str(sub_card))
                if sub_card.exists() and sub_audio.exists():
                    print(f"🎬 Mid-roll subscribe card...")
                    segment_files.append(
                        self.create_static_segment(str(sub_card), 0,
                                                   "seg_subscribe.mp4",
                                                   audio_path=str(sub_audio)))

        # ── Outro ─────────────────────────────────────────────────────────────
        if os.path.exists(outro_path):
            segment_files.append(self.create_static_segment(outro_path, 5, "seg_outro.mp4"))

        self.concatenate_segments(segment_files, LONGFORM_VIDEO)

        for seg in segment_files:
            try:
                if os.path.exists(seg):
                    os.remove(seg)
            except Exception:
                pass
                
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
        
        from components.video.single_project_video import create_single_project_video
        
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
            # Normalize audio to stereo 48kHz to match segment format
            cmd.extend([
                '-i', audio_path,
                '-af', 'aresample=48000:aformat=channel_layouts=stereo',
            ])
        else:
            # Use stereo 48kHz silent audio to match segment format
            cmd.extend(['-f', 'lavfi', '-i', 'anullsrc=channel_layout=stereo:sample_rate=48000', '-t', str(duration)])
            
        cmd.extend([
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
            '-c:a', 'aac',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        return str(output_path)

    def concatenate_segments(self, segment_files, output_name):
        """Concatenate video segments with dark-frame transitions between them"""
        concat_list = Path("concat_list.txt")

        all_files = list(segment_files)

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
            '-af', 'aresample=48000,aformat=channel_layouts=stereo',  # ensure consistent stereo 48kHz
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
            from core.db import DB
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
        from core.db import DB
        with DB() as _db:
            run_id = _db.start_run()
    except Exception:
        pass

    import sys as _sys
    try:
        asyncio.run(suite.run())
        if run_id:
            from core.db import DB
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
                from core.db import DB
                with DB() as _db:
                    _db.finish_run(run_id, repos_count=0, success_count=0, error_count=1)
            except Exception:
                pass
        raise
