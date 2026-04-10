"""
Graphics Renderer - Concrete implementation of IGraphicsRenderer
Handles rendering of title cards, screenshots, and visual elements.
"""
import os
import textwrap
from pathlib import Path
from typing import Optional, Dict
from PIL import Image, ImageDraw, ImageFont

from interfaces.interfaces import IGraphicsRenderer, IGitHubClient, IFFmpegExecutor


class GraphicsRenderer(IGraphicsRenderer):
    """
    Renders visual elements for video segments.
    
    SOLID Compliance:
    ✅ SRP: Only responsible for graphics rendering
    ✅ DIP: Depends on IGitHubClient and IFFmpegExecutor abstractions
    ✅ OCP: Can add new rendering strategies without modification
    ✅ LSP: Can be substituted with any IGraphicsRenderer
    ✅ ISP: Implements only IGraphicsRenderer methods
    
    Dependencies are explicit and injected through constructor.
    """
    
    def __init__(
        self,
        github_client: Optional[IGitHubClient] = None,
        ffmpeg_executor: Optional[IFFmpegExecutor] = None,
        output_folder: str = "assets",
        width: int = 1920,
        height: int = 1080
    ):
        """
        Constructor injection - all dependencies explicitly provided.
        
        Args:
            github_client: For fetching repository stats
            ffmpeg_executor: For image processing operations
            output_folder: Directory for output files
            width: Output image width
            height: Output image height
        """
        self.github_client = github_client
        self.ffmpeg_executor = ffmpeg_executor
        self.output_folder = Path(output_folder)
        self.width = width
        self.height = height
        
        # Ensure output directory exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
    
    def render_title_card(self, project: Dict) -> Path:
        """
        Create a professional title card image for a project.
        
        Args:
            project: Project dictionary with name, description, stats, etc.
            
        Returns:
            Path to generated title card image
        """
        W, H = self.width, self.height
        
        # Colors (CodeStream branding)
        BG = (8, 12, 20)
        TEAL = (0, 212, 255)
        GREEN = (0, 255, 136)
        WHITE = (255, 255, 255)
        GRAY = (136, 153, 170)
        GOLD = (255, 215, 0)
        
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        # Subtle grid background
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
        
        # Load fonts
        mono_fonts = [
            '/System/Library/Fonts/Menlo.ttc',
            '/System/Library/Fonts/Courier.ttc',
            '/Library/Fonts/Courier New.ttf'
        ]
        bold_fonts = [
            '/System/Library/Fonts/HelveticaNeue.ttc',
            '/System/Library/Fonts/Helvetica.ttc',
            '/Library/Fonts/Arial Bold.ttf',
            '/Library/Fonts/Arial.ttf'
        ]
        
        f_label = self._try_font(mono_fonts, 30)
        f_name = self._try_font(bold_fonts, 96)
        f_desc = self._try_font(mono_fonts, 32)
        f_stats = self._try_font(mono_fonts, 30)
        f_tag = self._try_font(mono_fonts, 26)
        
        # "// OPEN SOURCE" label
        label = "// OPEN SOURCE"
        lw = draw.textlength(label, font=f_label)
        draw.text(((W - lw) / 2, 90), label, fill=TEAL, font=f_label)
        
        # Project name (auto-scale if too long)
        name = project.get('name', '')
        nw = draw.textlength(name, font=f_name)
        if nw > W - 120:
            scale = (W - 120) / nw
            f_name = self._try_font(bold_fonts, int(96 * scale))
            nw = draw.textlength(name, font=f_name)
        name_y = 220
        draw.text(((W - nw) / 2, name_y), name, fill=WHITE, font=f_name)
        
        # Divider
        div_y = name_y + 130
        draw.rectangle([(W//2 - 200, div_y), (W//2 + 200, div_y + 2)], fill=TEAL)
        
        # Description (wrapped)
        desc = project.get('description', '')
        if desc:
            dy = div_y + 36
            for line in textwrap.wrap(desc, width=65)[:2]:
                lw = draw.textlength(line, font=f_desc)
                draw.text(((W - lw) / 2, dy), line, fill=GRAY, font=f_desc)
                dy += 50
        
        # Stats (fetch from GitHub if client available)
        stars = project.get('stars', 0) or 0
        forks = project.get('forks', 0) or 0
        language = project.get('language', '') or ''
        topics = project.get('topics', []) or []
        
        if self.github_client and project.get('github_url'):
            gh_stars, gh_forks, gh_lang, gh_topics = self.github_client.get_stats_from_url(
                project['github_url']
            )
            stars = gh_stars or stars
            forks = gh_forks or forks
            language = gh_lang or language
            topics = gh_topics or topics
        
        def fmt(n):
            return f"{n/1000:.1f}k" if n >= 1000 else str(n)
        
        sy = H - 175
        draw.text((80, sy), f"★ {fmt(stars)} stars", fill=GOLD, font=f_stats)
        draw.text((360, sy), f"⑂ {fmt(forks)} forks", fill=GRAY, font=f_stats)
        
        # Tag pills
        tags = ([language] if language else []) + list(topics)[:3]
        px, py = 80, sy + 58
        for tag in tags:
            tw = int(draw.textlength(tag, font=f_tag))
            pad = 14
            pw = tw + pad * 2
            draw.rounded_rectangle(
                [(px, py), (px + pw, py + 42)],
                radius=8,
                fill=(0, 40, 60),
                outline=TEAL,
                width=1
            )
            draw.text((px + pad, py + 8), tag, fill=TEAL, font=f_tag)
            px += pw + 12
        
        # Save
        output_path = self.output_folder / f"{project.get('id', 'unknown')}_title_card.png"
        img.save(str(output_path))
        
        return output_path
    
    def capture_screenshot(self, github_url: str) -> Optional[Path]:
        """
        Capture GitHub repository screenshot using external script.
        
        Args:
            github_url: GitHub repository URL
            
        Returns:
            Path to screenshot or None if failed
        """
        import subprocess
        import sys
        
        # Use external github_screenshot.py script
        try:
            result = subprocess.run(
                [sys.executable, "github_screenshot.py", github_url],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Parse output path from script stdout
            screenshot_path = None
            for line in result.stdout.splitlines():
                if line.startswith("Screenshot saved to:"):
                    screenshot_path = line.split(":", 1)[1].strip()
                    break
            
            # If no explicit path, derive expected path
            if not screenshot_path:
                import re
                match = re.search(r"github\.com/([^/]+)/([^/]+)", github_url)
                if match:
                    slug = f"{match.group(1)}_{match.group(2).rstrip('/')}".lower().replace("-", "_")
                    screenshot_path = f"assets/screenshots/{slug}_github.png"
            
            # Verify file exists
            if screenshot_path and os.path.exists(screenshot_path):
                return Path(screenshot_path)
            
            return None
            
        except Exception as e:
            print(f"⚠️  Screenshot capture failed: {e}")
            return None
    
    def create_fallback_screenshot(self, project: Dict) -> Path:
        """
        Create a GitHub-style fallback screenshot when capture fails.
        
        Args:
            project: Project dictionary
            
        Returns:
            Path to generated fallback screenshot
        """
        W, H = 1920, 1080
        BG = (248, 248, 252)  # GitHub light gray
        WHITE = (255, 255, 255)
        BLACK = (24, 23, 23)
        GRAY = (88, 96, 105)
        GREEN = (31, 136, 61)
        BLUE = (9, 105, 218)
        
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        # Header area
        header_height = 60
        draw.rectangle([(0, 0), (W, header_height)], fill=BG, outline=(224, 224, 224))
        
        repo_name = project.get('name', 'Unknown Repo')
        desc = project.get('description', 'No description available')
        stars = project.get('stars', 0) or 0
        forks = project.get('forks', 0) or 0
        
        # Fonts
        font_large = self._try_font(['/System/Library/Fonts/Helvetica.ttc'], 48)
        font_medium = self._try_font(['/System/Library/Fonts/Helvetica.ttc'], 28)
        font_small = self._try_font(['/System/Library/Fonts/Helvetica.ttc'], 20)
        
        # Repository name
        draw.text((20, header_height + 20), repo_name, fill=BLACK, font=font_large)
        
        # Description box
        draw.rectangle(
            [(20, header_height + 80), (W - 20, header_height + 200)],
            fill=WHITE,
            outline=(224, 224, 224)
        )
        draw.text((40, header_height + 95), desc[:50] + "...", fill=GRAY, font=font_medium)
        
        # Stats
        stats_y = header_height + 220
        draw.text((40, stats_y), f"⭐ {stars} stars", fill=GREEN, font=font_medium)
        draw.text((200, stats_y), f"⑂ {forks} forks", fill=BLUE, font=font_medium)
        
        # GitHub URL
        url_text = project.get('github_url', 'github.com/owner/repo')
        draw.text((40, stats_y + 40), url_text[-60:], fill=GRAY, font=font_small)
        
        # Decorative elements (fake README sections)
        for i in range(5):
            y = stats_y + 80 + i * 60
            draw.rectangle([(40, y), (W - 40, y + 40)], fill=WHITE, outline=(224, 224, 224))
            draw.text((60, y + 10), f"GitHub README Section {i+1}", fill=BLACK, font=font_small)
        
        # Save
        fallback_path = self.output_folder / f"{project.get('id', 'unknown')}_fallback_github.png"
        img.save(str(fallback_path))
        
        return fallback_path
    
    def _try_font(self, font_paths, size):
        """Try to load a font, fall back to default if all fail."""
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                pass
        return ImageFont.load_default()


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated):

class VideoSuiteAutomated:
    def _render_title_card_image(self, project: dict) -> Path:
        # ❌ Graphics code mixed with video logic
        # ❌ Direct GitHub API calls embedded
        # ❌ Hard to test graphics separately
        # ❌ Can't reuse graphics generation
        from PIL import Image, ImageDraw, ImageFont
        W, H = 1920, 1080
        # ... 200+ lines of graphics code ...


✅ NEW APPROACH (SOLID):

class GraphicsRenderer(IGraphicsRenderer):
    def __init__(
        self,
        github_client: Optional[IGitHubClient],  # ✅ Explicit dependency
        ffmpeg_executor: Optional[IFFmpegExecutor],  # ✅ Explicit dependency
        output_folder: str = "assets"  # ✅ Configurable
    ):
        # ✅ All dependencies explicit
        # ✅ Single responsibility: graphics only
        # ✅ Can be tested in isolation
        # ✅ Can be reused by multiple components
        # ✅ Easy to substitute different implementations
    
    def render_title_card(self, project: Dict) -> Path:
        # ✅ Clean interface
        # ✅ Uses injected github_client
        # ✅ Returns path (easy to test)
"""
