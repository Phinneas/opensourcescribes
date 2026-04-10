"""
Enhanced Code Stream Graphics Generator with AI Presenters
Combines your brand aesthetic with AI-generated human presenters
For integration with Ideogram, Midjourney, Flux.1, or similar services
"""

import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime, timedelta
import re

# Enhanced Code Stream Brand Colors (updated for 2026)
COLORS = {
    'deep_blue': (10, 22, 40),           # #0a1628 - Primary background
    'electric_teal': (64, 224, 208),     # #40E0D0 - Primary accent
    'electric_green': (0, 255, 65),      # #00FF41 - Secondary accent
    'dark_gray': (26, 26, 46),           # #1a1a2e - Secondary background
    'dark_purple': (26, 0, 51),          # #1a0033 - Gradient/depth
    'white': (255, 255, 255),            # #FFFFFF - Primary text
    'soft_gray': (204, 204, 204),        # #CCCCCC - Secondary text
    'vibrant_orange': (255, 140, 0),     # #FF8C00 - New accent for energy
    'hot_pink': (255, 20, 147),          # #FF1493 - New accent for highlights
}

STATS_CACHE_FILE = "github_stats_cache.json"
CACHE_EXPIRY_HOURS = 24


class EnhancedCodeStreamGraphics:
    """Enhanced graphics generator with human presenters and modern aesthetic"""
    
    def __init__(self, output_dir="assets"):
        self.output_dir = output_dir
        self.width = 1920
        self.height = 1080
        self.stats_cache = self._load_stats_cache()
        self.fonts = self._load_fonts()
        os.makedirs(output_dir, exist_ok=True)
    
    def _load_stats_cache(self):
        """Load cached GitHub stats"""
        if os.path.exists(STATS_CACHE_FILE):
            try:
                with open(STATS_CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_stats_cache(self):
        """Save GitHub stats cache"""
        with open(STATS_CACHE_FILE, 'w') as f:
            json.dump(self.stats_cache, f, indent=2)
    
    def _is_cache_valid(self, cached_entry):
        """Check if cached entry is still fresh"""
        if 'timestamp' not in cached_entry:
            return False
        cached_time = datetime.fromisoformat(cached_entry['timestamp'])
        return datetime.now() - cached_time < timedelta(hours=CACHE_EXPIRY_HOURS)
    
    def _load_fonts(self):
        """Load fonts with cross-platform fallback"""
        fonts = {}
        font_sizes = {
            'title': 120,           # Slightly smaller for text with presenter
            'label': 45,
            'stats': 40,
            'description': 28,
            'tag': 24,
            'watermark': 32,
        }
        
        font_candidates = [
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "C:\\Windows\\Fonts\\arial.ttf",
        ]
        
        available_font = None
        for font_path in font_candidates:
            if os.path.exists(font_path):
                available_font = font_path
                break
        
        for style, size in font_sizes.items():
            try:
                if available_font:
                    fonts[style] = ImageFont.truetype(available_font, size)
                else:
                    fonts[style] = ImageFont.load_default()
            except:
                fonts[style] = ImageFont.load_default()
        
        return fonts
    
    def get_github_stats(self, github_url):
        """Fetch GitHub stats with caching"""
        match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
        if not match:
            return None
        
        owner, repo = match.groups()
        cache_key = f"{owner}/{repo}"
        
        if cache_key in self.stats_cache and self._is_cache_valid(self.stats_cache[cache_key]):
            print(f"📦 Using cached stats for {cache_key}")
            return self.stats_cache[cache_key]['data']
        
        try:
            url = f"https://api.github.com/repos/{owner}/{repo}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                stats = {
                    'owner': owner,
                    'repo': repo,
                    'stars': data.get('stargazers_count', 0),
                    'forks': data.get('forks_count', 0),
                    'language': data.get('language', 'Unknown'),
                    'description': data.get('description', ''),
                    'topics': data.get('topics', [])[:4],
                    'url': github_url,
                    'timestamp': datetime.now().isoformat()
                }
                
                self.stats_cache[cache_key] = {'data': stats, 'timestamp': datetime.now().isoformat()}
                self._save_stats_cache()
                
                print(f"✅ Fetched fresh stats for {cache_key}")
                return stats
        except Exception as e:
            print(f"⚠️  Failed to fetch stats: {e}")
        
        return None
    
    def format_number(self, num):
        """Format large numbers"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}k"
        return str(num)
    
    def create_gradient_background(self, style="modern"):
        """Create modern gradient background (more dynamic than old grid)"""
        img = Image.new('RGB', (self.width, self.height), color=COLORS['deep_blue'])
        draw = ImageDraw.Draw(img)
        
        if style == "modern":
            # Diagonal gradient from deep blue to purple (more dynamic)
            for y in range(self.height):
                ratio = y / self.height
                x_offset = int(ratio * 200)
                r = int(COLORS['deep_blue'][0] + (COLORS['dark_purple'][0] - COLORS['deep_blue'][0]) * ratio)
                g = int(COLORS['deep_blue'][1] + (COLORS['dark_purple'][1] - COLORS['deep_blue'][1]) * ratio)
                b = int(COLORS['deep_blue'][2] + (COLORS['dark_purple'][2] - COLORS['deep_blue'][2]) * ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        elif style == "vibrant":
            # Multi-color gradient (teal to blue to purple)
            for y in range(self.height):
                ratio = y / self.height
                if ratio < 0.5:
                    # Teal to blue
                    local_ratio = ratio * 2
                    r = int(COLORS['electric_teal'][0] + (COLORS['deep_blue'][0] - COLORS['electric_teal'][0]) * local_ratio)
                    g = int(COLORS['electric_teal'][1] + (COLORS['deep_blue'][1] - COLORS['electric_teal'][1]) * local_ratio)
                    b = int(COLORS['electric_teal'][2] + (COLORS['deep_blue'][2] - COLORS['electric_teal'][2]) * local_ratio)
                else:
                    # Blue to purple
                    local_ratio = (ratio - 0.5) * 2
                    r = int(COLORS['deep_blue'][0] + (COLORS['dark_purple'][0] - COLORS['deep_blue'][0]) * local_ratio)
                    g = int(COLORS['deep_blue'][1] + (COLORS['dark_purple'][1] - COLORS['deep_blue'][1]) * local_ratio)
                    b = int(COLORS['deep_blue'][2] + (COLORS['dark_purple'][2] - COLORS['deep_blue'][2]) * local_ratio)
                draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        return img
    
    def add_circuit_pattern(self, img):
        """Add subtle circuit pattern (replaces old grid - more tech-focused)"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Circuit-like connections
        circuit_color = (*COLORS['electric_teal'], 25)  # Very subtle
        
        # Horizontal lines with dots (circuit nodes)
        for y in range(100, self.height, 150):
            draw.line([(50, y), (self.width - 50, y)], fill=circuit_color, width=1)
            # Add nodes
            for x in range(100, self.width, 200):
                draw.ellipse([(x-3, y-3), (x+3, y+3)], fill=circuit_color)
        
        # Vertical lines
        for x in range(100, self.width, 200):
            draw.line([(x, 100), (x, self.height - 100)], fill=circuit_color, width=1)
        
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    def add_glow_orb(self, img, position, color, size=150):
        """Add glowing orb accent (modern tech vibe)"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        x, y = position
        
        # Multiple layers for glow effect
        for i in range(10):
            opacity = int(30 - i * 3)
            orb_size = size - i * (size // 10)
            glow_color = (*color, opacity)
            draw.ellipse(
                [(x - orb_size//2, y - orb_size//2), (x + orb_size//2, y + orb_size//2)],
                fill=glow_color
            )
        
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    def draw_text_with_glow(self, draw, text, position, font, glow_color, text_color, glow_offset=3):
        """Draw text with glow effect"""
        x, y = position
        
        # Draw glow layers
        for offset in [glow_offset * 2, glow_offset, glow_offset // 2]:
            if offset > 0:
                draw.text((x + offset, y + offset), text, font=font, fill=glow_color)
        
        # Draw main text
        draw.text((x, y), text, font=font, fill=text_color)
    
    def wrap_text(self, text, max_width, font):
        """Wrap text to fit within max width"""
        if not text:
            return []
        
        wrapped = []
        words = text.split()
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = self.fonts['description'].getbbox(test_line)
            line_width = bbox[2] - bbox[0]
            
            if line_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    wrapped.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            wrapped.append(' '.join(current_line))
        
        return wrapped
    
    def create_ai_presenter_prompt(self, project_name, project_type="web", style="professional"):
        """
        Generate AI prompt for creating presenter image
        For use with Ideogram, Midjourney, Flux.1, etc.
        """
        
        presenter_prompts = {
            "professional": f"""A friendly tech presenter in their 30s, excited expression, 
            gesturing towards screen right, wearing casual smart attire (dark hoodie or blazer), 
            professional headshot style, modern tech background, studio lighting, 
            looking slightly to the right, engaging smile, dynamic pose leaning forward, 
            4K portrait photography, shallow depth of field, --ar 2:3 --style raw""",
            
            "enthusiastic": f"""An energetic developer in their 20s-30s, very excited expression, 
            pointing finger forward, wearing modern tech casual tshirt, vibrant energy, 
            dynamic pose jumping or leaning in, enthusiastic smile, expressive body language, 
            colorful tech background, studio lighting, 4K photography, --ar 2:3 --stylize 500""",
            
            "curious": f"""A thoughtful tech explorer, curious and interested expression, 
            looking at something off-screen right, hand near chin in thinking pose, 
            wearing casual smart clothes, professional yet approachable, warm lighting, 
            modern tech workspace background, 4K portrait, --ar 2:3 --style raw""",
        }
        
        return presenter_prompts.get(style, presenter_prompts["professional"])
    
    def create_project_graphic_with_presenter(
        self, 
        project_name, 
        github_url, 
        presenter_image_path=None,
        output_path=None,
        layout="split_right"  # "split_right" or "split_left"
    ):
        """
        Create enhanced project graphic with AI-generated presenter
        
        Args:
            project_name: Name of the project
            github_url: GitHub repository URL
            presenter_image_path: Path to AI-generated presenter image (transparent PNG ideally)
            output_path: Where to save the final graphic
            layout: "split_right" = presenter on right, content on left
                   "split_left" = presenter on left, content on right
        """
        
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"{project_name.lower().replace(' ', '_')}_enhanced.png")
        
        print(f"\n🎨 Creating ENHANCED graphic for {project_name}...")
        
        # Fetch stats
        stats = self.get_github_stats(github_url)
        if not stats:
            print(f"⚠️  Could not fetch stats, creating fallback")
            self._create_fallback_graphic_enhanced(project_name, presenter_image_path, output_path)
            return output_path
        
        # Create modern gradient background
        img = self.create_gradient_background(style="vibrant")
        
        # Add subtle circuit pattern
        img = self.add_circuit_pattern(img)
        
        # Add glow orbs for visual interest
        img = self.add_glow_orb(img, (200, 200), COLORS['electric_teal'], size=200)
        img = self.add_glow_orb(img, (1720, 880), COLORS['vibrant_orange'], size=180)
        
        draw = ImageDraw.Draw(img)
        
        # Layout dimensions
        if layout == "split_right":
            content_x = 100
            content_width = 1100  # Left side for content
            presenter_x = 1300   # Right side for presenter
        else:
            content_x = 720     # Right side for content
            content_width = 1100
            presenter_x = 100   # Left side for presenter
        
        # === ADD PRESENTER (if provided) ===
        if presenter_image_path and os.path.exists(presenter_image_path):
            try:
                presenter_img = Image.open(presenter_image_path)
                # Resize presenter to fit in their section
                presenter_height = 900
                presenter_width = int(presenter_img.width * (presenter_height / presenter_img.height))
                presenter_img = presenter_img.resize((presenter_width, presenter_height), Image.Resampling.LANCZOS)
                
                # Position presenter
                presenter_y = (self.height - presenter_height) // 2
                if layout == "split_right":
                    paste_x = max(presenter_x, self.width - presenter_width - 50)
                else:
                    paste_x = min(presenter_x, 50)
                
                # Paste with transparency handling
                if presenter_img.mode == 'RGBA':
                    img.paste(presenter_img, (paste_x, presenter_y), presenter_img)
                else:
                    img.paste(presenter_img, (paste_x, presenter_y))
                
                print(f"✅ Added presenter from {presenter_image_path}")
            except Exception as e:
                print(f"⚠️  Could not add presenter: {e}")
        
        # === PROJECT TITLE ===
        project_display = stats['repo'].replace('-', ' ').replace('_', ' ').title()
        
        # Glow effect for title
        glow_color = (
            int(COLORS['electric_teal'][0] * 0.4),
            int(COLORS['electric_teal'][1] * 0.4),
            int(COLORS['electric_teal'][2] * 0.4),
        )
        
        self.draw_text_with_glow(
            draw,
            project_display,
            (content_x, 120),
            self.fonts['title'],
            glow_color,
            COLORS['electric_teal']
        )
        
        # === DESCRIPTION ===
        if stats.get('description'):
            desc_lines = self.wrap_text(stats['description'], content_width - 50, self.fonts['description'])
            desc_y = 280
            
            for line in desc_lines[:3]:  # Max 3 lines
                # Add subtle shadow for readability
                draw.text((content_x + 2, desc_y + 2), line, font=self.fonts['description'], fill=(0, 0, 0, 128))
                draw.text(
                    (content_x, desc_y),
                    line,
                    font=self.fonts['description'],
                    fill=COLORS['white']
                )
                desc_y += 40
        
        # === STATS (horizontal layout) ===
        stats_y = 500
        stat_box_width = 220
        stat_box_height = 100
        stat_spacing = 20
        
        stat_items = [
            (f"⭐ {self.format_number(stats['stars'])}", "Stars"),
            (f"🍴 {self.format_number(stats['forks'])}", "Forks"),
            (f"📝 {stats['language']}", "Language"),
        ]
        
        total_stats_width = (stat_box_width * len(stat_items)) + (stat_spacing * (len(stat_items) - 1))
        stats_start_x = content_x
        
        for i, (stat_value, stat_label) in enumerate(stat_items):
            box_x = stats_start_x + (i * (stat_box_width + stat_spacing))
            box_y = stats_y
            
            # Semi-transparent background for stat box
            stat_bg_color = (*COLORS['dark_gray'], 200)
            stat_overlay = Image.new('RGBA', (stat_box_width, stat_box_height), stat_bg_color)
            stat_overlay_draw = ImageDraw.Draw(stat_overlay)
            
            # Border with gradient effect (Electric Teal)
            stat_overlay_draw.rectangle(
                [(0, 0), (stat_box_width - 2, stat_box_height - 2)],
                outline=COLORS['electric_teal'],
                width=2
            )
            
            # Draw stat value
            bbox = stat_overlay_draw.textbbox((0, 0), stat_value, font=self.fonts['stats'])
            value_width = bbox[2] - bbox[0]
            stat_overlay_draw.text(
                ((stat_box_width - value_width) // 2, 15),
                stat_value,
                font=self.fonts['stats'],
                fill=COLORS['electric_green']
            )
            
            # Draw stat label
            bbox = stat_overlay_draw.textbbox((0, 0), stat_label, font=self.fonts['label'])
            label_width = bbox[2] - bbox[0]
            stat_overlay_draw.text(
                ((stat_box_width - label_width) // 2, 55),
                stat_label,
                font=self.fonts['label'],
                fill=COLORS['soft_gray']
            )
            
            # Composite onto main image
            img.paste(Image.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, 0)), stat_overlay), (box_x, box_y), stat_overlay)
        
        # === TOPICS (modern pill tags) ===
        if stats.get('topics'):
            tag_y = 650
            tag_x = content_x
            
            for topic in stats['topics'][:5]:
                topic_text = f"#{topic}"
                bbox = draw.textbbox((0, 0), topic_text, font=self.fonts['tag'])
                tag_width = bbox[2] - bbox[0] + 25
                
                # Check if tag fits
                if tag_x + tag_width > content_x + content_width:
                    tag_y += 45
                    tag_x = content_x
                
                # Draw tag background (gradient effect)
                tag_overlay = Image.new('RGBA', (tag_width, 40), (0, 0, 0, 0))
                tag_draw = ImageDraw.Draw(tag_overlay)
                
                # Gradient from Electric Teal to Electric Green
                for x in range(tag_width):
                    ratio = x / tag_width
                    r = int(COLORS['electric_teal'][0] + (COLORS['electric_green'][0] - COLORS['electric_teal'][0]) * ratio)
                    g = int(COLORS['electric_teal'][1] + (COLORS['electric_green'][1] - COLORS['electric_teal'][1]) * ratio)
                    b = int(COLORS['electric_teal'][2] + (COLORS['electric_green'][2] - COLORS['electric_teal'][2]) * ratio)
                    tag_draw.line([(x, 0), (x, 40)], fill=(r, g, b, 200))
                
                # Rounded corners effect
                tag_draw.ellipse([(0, 0), (10, 10)], fill=(r, g, b, 200))
                tag_draw.ellipse([(tag_width - 10, 0), (tag_width, 10)], fill=(r, g, b, 200))
                tag_draw.ellipse([(0, 30), (10, 40)], fill=(r, g, b, 200))
                tag_draw.ellipse([(tag_width - 10, 30), (tag_width, 40)], fill=(r, g, b, 200))
                
                # Tag text
                tag_draw.text(
                    (12, 8),
                    topic_text,
                    font=self.fonts['tag'],
                    fill=COLORS['deep_blue']
                )
                
                # Composite onto main image
                img.paste(Image.alpha_composite(Image.new('RGBA', img.size, (0, 0, 0, 0)), tag_overlay), (tag_x, tag_y), tag_overlay)
                
                tag_x += tag_width + 15
        
        # === WATERMARK / CHANNEL BRANDING ===
        watermark = "OpenSourceScribes"
        bbox = draw.textbbox((0, 0), watermark, font=self.fonts['watermark'])
        watermark_width = bbox[2] - bbox[0]
        
        # Bottom right corner
        draw.text(
            (self.width - watermark_width - 30, self.height - 50),
            watermark,
            font=self.fonts['watermark'],
            fill=(*COLORS['electric_teal'], 180)
        )
        
        # Save
        img.save(output_path)
        print(f"✅ Enhanced graphic saved: {output_path}")
        
        return output_path
    
    def _create_fallback_graphic_enhanced(self, project_name, presenter_image_path, output_path):
        """Create fallback graphic when API fails"""
        img = self.create_gradient_background(style="vibrant")
        img = self.add_circuit_pattern(img)
        img = self.add_glow_orb(img, (960, 540), COLORS['electric_teal'], size=300)
        
        draw = ImageDraw.Draw(img)
        
        # Draw project name (centered, larger without presenter)
        bbox = draw.textbbox((0, 0), project_name, font=self.fonts['title'])
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        y = 430  # Slightly higher to center vertically
        
        glow_color = (
            int(COLORS['electric_teal'][0] * 0.4),
            int(COLORS['electric_teal'][1] * 0.4),
            int(COLORS['electric_teal'][2] * 0.4),
        )
        
        self.draw_text_with_glow(
            draw,
            project_name,
            (x, y),
            self.fonts['title'],
            glow_color,
            COLORS['electric_teal']
        )
        
        # Add presenter if available
        if presenter_image_path and os.path.exists(presenter_image_path):
            try:
                presenter_img = Image.open(presenter_image_path)
                # Scale down presenter for background
                presenter_height = 600
                presenter_width = int(presenter_img.width * (presenter_height / presenter_img.height))
                presenter_img = presenter_img.resize((presenter_width, presenter_height), Image.Resampling.LANCZOS)
                
                # Add transparency for background effect
                if presenter_img.mode == 'RGBA':
                    # Reduce opacity
                    presenter_img = presenter_img.copy()
                    presenter_alpha = presenter_img.split()[3]
                    presenter_alpha = presenter_img.point(lambda p: p * 0.3)
                    presenter_img.putalpha(presenter_alpha)
                
                presenter_x = (self.width - presenter_width) // 2
                presenter_y = (self.height - presenter_height) // 2
                
                img.paste(presenter_img, (presenter_x, presenter_y), presenter_img if presenter_img.mode == 'RGBA' else None)
            except Exception as e:
                print(f"⚠️  Could not add presenter to fallback: {e}")
        
        img.save(output_path)
        print(f"✅ Fallback enhanced graphic: {output_path}")


# Convenience function
def create_enhanced_graphic(project_name, github_url, presenter_image_path=None, output_path=None):
    """Create enhanced graphic with presenter"""
    generator = EnhancedCodeStreamGraphics()
    return generator.create_project_graphic_with_presenter(
        project_name, 
        github_url, 
        presenter_image_path,
        output_path
    )


if __name__ == "__main__":
    # Test enhanced graphics
    generator = EnhancedCodeStreamGraphics()
    
    # Example: Generate AI presenter prompts
    print("\n=== AI PRESENTER PROMPTS ===\n")
    print("Professional Style:")
    print(generator.create_ai_presenter_prompt("React", "web", "professional"))
    
    print("\n" + "="*60 + "\n")
    
    print("Enthusiastic Style:")
    print(generator.create_ai_presenter_prompt("Kubernetes", "devops", "enthusiastic"))
    
    print("\n" + "="*60 + "\n")
    
    print("Curious Style:")
    print(generator.create_ai_presenter_prompt("TensorFlow", "ai", "curious"))
    
    print("\n" + "="*60)
    print("\n✅ Run with a presenter image to create full enhanced graphics!")
