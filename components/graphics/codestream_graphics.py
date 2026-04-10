"""
Code Stream Branded Graphics Generator
Implements full brand identity with glow effects, grid patterns, and data flow aesthetic
Designed for use with Google Antigravity for real-time development and iteration
"""

import os
import json
import requests
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime, timedelta
import re
import random

# Code Stream Brand Colors
COLORS = {
    'deep_blue': (10, 22, 40),           # #0a1628 - Primary background
    'electric_teal': (64, 224, 208),     # #40E0D0 - Primary accent
    'electric_green': (0, 255, 65),      # #00FF41 - Secondary accent
    'dark_gray': (26, 26, 46),           # #1a1a2e - Secondary background
    'dark_purple': (26, 0, 51),          # #1a0033 - Gradient/depth
    'white': (255, 255, 255),            # #FFFFFF - Primary text
    'soft_gray': (204, 204, 204),        # #CCCCCC - Secondary text
}

STATS_CACHE_FILE = "github_stats_cache.json"
CACHE_EXPIRY_HOURS = 24

class CodeStreamGraphics:
    """Code Stream branded graphics generator"""
    
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
            'title': 140,
            'label': 50,
            'stats': 45,
            'description': 32,
            'tag': 28,
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
    
    def create_base_image(self):
        """Create base image with Code Stream aesthetic - now with varied gradients"""
        # Start with Deep Blue background
        img = Image.new('RGB', (self.width, self.height), color=COLORS['deep_blue'])
        
        # Randomize gradient intensity and direction
        gradient_intensity = random.uniform(0.2, 0.5)  # Was fixed at 0.3
        reverse_gradient = random.choice([True, False])
        
        draw = ImageDraw.Draw(img)
        
        for y in range(self.height):
            if reverse_gradient:
                # Reverse: purple to blue
                ratio = 1 - (y / self.height)
            else:
                # Normal: blue to purple
                ratio = y / self.height
            
            r = int(COLORS['deep_blue'][0] + (COLORS['dark_purple'][0] - COLORS['deep_blue'][0]) * ratio * gradient_intensity)
            g = int(COLORS['deep_blue'][1] + (COLORS['dark_purple'][1] - COLORS['deep_blue'][1]) * ratio * gradient_intensity)
            b = int(COLORS['deep_blue'][2] + (COLORS['dark_purple'][2] - COLORS['deep_blue'][2]) * ratio * gradient_intensity)
            draw.line([(0, y), (self.width, y)], fill=(r, g, b))
        
        return img
    
    def add_grid_pattern(self, img):
        """Add Code Stream grid pattern with randomized spacing and optional skip"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Randomize grid spacing
        grid_spacing = random.choice([60, 80, 100, 120])
        
        # Randomize accent color (sometimes teal, sometimes green, sometimes purple mix)
        color_choice = random.choice(['teal', 'green', 'purple'])
        if color_choice == 'teal':
            grid_color = (*COLORS['electric_teal'], random.randint(25, 50))
        elif color_choice == 'green':
            grid_color = (*COLORS['electric_green'], random.randint(25, 50))
        else:  # purple - mix of blue and teal
            grid_color = (int((COLORS['deep_blue'][0] + COLORS['electric_teal'][0])/2),
                         int((COLORS['deep_blue'][1] + COLORS['electric_teal'][1])/2),
                         int((COLORS['deep_blue'][2] + COLORS['electric_teal'][2])/2),
                         random.randint(25, 50))
        
        # Randomly decide to skip grid pattern entirely for cleaner look (30% chance)
        if random.random() < 0.3:
            return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        # Horizontal grid lines
        for y in range(0, self.height, grid_spacing):
            # Randomly skip some lines for variety (20% chance per line)
            if random.random() > 0.2:
                draw.line([(0, y), (self.width, y)], fill=grid_color, width=1)
        
        # Vertical grid lines
        for x in range(0, self.width, grid_spacing):
            # Randomly skip some lines for variety (20% chance per line)
            if random.random() > 0.2:
                draw.line([(x, 0), (x, self.height)], fill=grid_color, width=1)
        
        # Add circuit nodes at some grid intersections
        node_size = random.randint(3, 6)
        for y in range(0, self.height, grid_spacing * 2):
            for x in range(0, self.width, grid_spacing * 2):
                # 40% chance to add a node at each intersection
                if random.random() < 0.4:
                    draw.ellipse([(x - node_size, y - node_size), (x + node_size, y + node_size)], 
                                fill=grid_color)
        
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    def add_data_flow_lines(self, img):
        """Add diagonal data flow lines with randomized spacing and optional skip"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Randomize flow line spacing
        flow_spacing = random.choice([150, 200, 250])
        
        # Randomize flow line color
        color_choice = random.choice(['teal', 'green'])
        if color_choice == 'teal':
            flow_color = (*COLORS['electric_teal'], random.randint(30, 60))
        else:
            flow_color = (*COLORS['electric_green'], random.randint(30, 60))
        
        # Randomly decide to skip flow lines entirely (40% chance)
        if random.random() < 0.4:
            return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
        
        # Diagonal lines flowing top-left to bottom-right
        for i in range(-self.height, self.width, flow_spacing):
            # Randomly skip some lines (25% chance)
            if random.random() > 0.25:
                draw.line(
                    [(i, 0), (i + self.height, self.height)],
                    fill=flow_color,
                    width=random.randint(1, 3)
                )
        
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    def add_glow_accents(self, img):
        """Add horizontal glow lines at top and bottom with randomized colors"""
        overlay = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Randomize glow color (teal or green)
        glow_choice = random.choice(['teal', 'green'])
        if glow_choice == 'teal':
            glow_base_color = COLORS['electric_teal']
        else:
            glow_base_color = COLORS['electric_green']
        
        # Randomly decide glow position
        top_glow_y = random.randint(80, 120)
        bottom_glow_y = random.randint(920, 980)
        
        # Top glow accent
        for i in range(6):
            opacity = int(80 - i * 12)
            glow_color = (*glow_base_color, opacity)
            draw.line([(0, top_glow_y + i), (self.width, top_glow_y + i)], fill=glow_color, width=2)
        
        # Bottom glow accent
        for i in range(6):
            opacity = int(80 - i * 12)
            glow_color = (*glow_base_color, opacity)
            draw.line([(0, bottom_glow_y + i), (self.width, bottom_glow_y + i)], fill=glow_color, width=2)
        
        # Add random decorative glow orbs (1-3 orbs)
        num_orbs = random.randint(1, 3)
        for _ in range(num_orbs):
            orb_x = random.randint(200, self.width - 200)
            orb_y = random.randint(200, self.height - 200)
            orb_size = random.randint(100, 200)
            
            # Random orb color
            orb_color_choice = random.choice(['teal', 'green', 'purple'])
            if orb_color_choice == 'teal':
                orb_color = COLORS['electric_teal']
            elif orb_color_choice == 'green':
                orb_color = COLORS['electric_green']
            else:  # purple mix
                orb_color = (int((COLORS['deep_blue'][0] + COLORS['electric_teal'][0])/2),
                           int((COLORS['deep_blue'][1] + COLORS['electric_teal'][1])/2),
                           int((COLORS['deep_blue'][2] + COLORS['electric_teal'][2])/2))
            
            # Draw orb with multiple glow layers
            for i in range(10):
                opacity = int(40 - i * 4)
                current_orb_size = orb_size - (i * (orb_size // 10))
                glow_color = (*orb_color, opacity)
                draw.ellipse(
                    [(orb_x - current_orb_size//2, orb_y - current_orb_size//2), 
                     (orb_x + current_orb_size//2, orb_y + current_orb_size//2)],
                    fill=glow_color
                )
        
        return Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    
    def draw_text_with_glow(self, draw, text, position, font, glow_color, text_color, glow_offset=3):
        """Draw text with glow effect"""
        x, y = position
        
        # Draw glow layers (multiple offsets for stronger effect)
        for offset in [6, 4, 2]:
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
    
    def create_project_graphic(self, project_name, github_url, output_path=None):
        """Create Code Stream branded project graphic"""
        
        if output_path is None:
            output_path = os.path.join(self.output_dir, f"{project_name.lower().replace(' ', '_')}.png")
        
        print(f"\n🎨 Creating Code Stream graphic for {project_name}...")
        
        # Fetch stats
        stats = self.get_github_stats(github_url)
        if not stats:
            print(f"⚠️  Could not fetch stats, creating fallback")
            self._create_fallback_graphic(project_name, output_path)
            return output_path
        
        # Create base image
        img = self.create_base_image()
        
        # Add patterns
        img = self.add_grid_pattern(img)
        img = self.add_data_flow_lines(img)
        img = self.add_glow_accents(img)
        
        draw = ImageDraw.Draw(img)
        
        # Draw "Tool:" label
        draw.text(
            (100, 150),
            "Tool:",
            font=self.fonts['label'],
            fill=COLORS['soft_gray']
        )
        
        # Draw project name with glow
        project_display = stats['repo'].replace('-', ' ').replace('_', ' ').upper()
        glow_color = (
            int(COLORS['electric_teal'][0] * 0.3),
            int(COLORS['electric_teal'][1] * 0.3),
            int(COLORS['electric_teal'][2] * 0.3),
        )
        
        self.draw_text_with_glow(
            draw,
            project_display,
            (100, 200),
            self.fonts['title'],
            glow_color,
            COLORS['electric_teal']
        )
        
        # Draw description if available
        if stats.get('description'):
            desc_lines = self.wrap_text(stats['description'], 1700, self.fonts['description'])
            desc_y = 380
            
            for line in desc_lines[:2]:  # Max 2 lines
                draw.text(
                    (100, desc_y),
                    line,
                    font=self.fonts['description'],
                    fill=COLORS['soft_gray']
                )
                desc_y += 45
        
        # Draw stats in boxes
        stats_y = 750
        stat_box_width = 380
        stat_box_height = 120
        
        stat_items = [
            (f"⭐ {self.format_number(stats['stars'])}", "Stars"),
            (f"🍴 {self.format_number(stats['forks'])}", "Forks"),
            (f"📝 {stats['language']}", "Language"),
        ]
        
        total_width = (stat_box_width * len(stat_items)) + (20 * (len(stat_items) - 1))
        start_x = (self.width - total_width) // 2
        
        for i, (stat_value, stat_label) in enumerate(stat_items):
            box_x = start_x + (i * (stat_box_width + 20))
            
            # Draw box outline with Electric Teal
            box_coords = [
                (box_x, stats_y),
                (box_x + stat_box_width, stats_y + stat_box_height)
            ]
            draw.rectangle(box_coords, outline=COLORS['electric_teal'], width=2)
            
            # Draw stat value
            bbox = draw.textbbox((0, 0), stat_value, font=self.fonts['stats'])
            value_width = bbox[2] - bbox[0]
            draw.text(
                (box_x + (stat_box_width - value_width) // 2, stats_y + 15),
                stat_value,
                font=self.fonts['stats'],
                fill=COLORS['white']
            )
            
            # Draw stat label
            bbox = draw.textbbox((0, 0), stat_label, font=self.fonts['label'])
            label_width = bbox[2] - bbox[0]
            draw.text(
                (box_x + (stat_box_width - label_width) // 2, stats_y + 70),
                stat_label,
                font=self.fonts['label'],
                fill=COLORS['soft_gray']
            )
        
        # Draw topics as tags
        if stats.get('topics'):
            tag_y = 950
            tag_x = 100
            
            for topic in stats['topics'][:4]:
                topic_text = f"#{topic}"
                bbox = draw.textbbox((0, 0), topic_text, font=self.fonts['tag'])
                tag_width = bbox[2] - bbox[0] + 20
                
                # Draw tag background with Electric Green
                draw.rectangle(
                    [(tag_x, tag_y - 5), (tag_x + tag_width, tag_y + 35)],
                    fill=COLORS['electric_green'],
                    outline=COLORS['electric_teal'],
                    width=1
                )
                
                # Draw tag text
                draw.text(
                    (tag_x + 10, tag_y),
                    topic_text,
                    font=self.fonts['tag'],
                    fill=COLORS['deep_blue']
                )
                
                tag_x += tag_width + 15
        
        # Save
        img.save(output_path)
        print(f"✅ Code Stream graphic saved: {output_path}")
        
        return output_path
    
    def _create_fallback_graphic(self, project_name, output_path):
        """Create fallback graphic when API fails"""
        img = self.create_base_image()
        img = self.add_grid_pattern(img)
        img = self.add_glow_accents(img)
        
        draw = ImageDraw.Draw(img)
        
        # Draw project name
        bbox = draw.textbbox((0, 0), project_name, font=self.fonts['title'])
        text_width = bbox[2] - bbox[0]
        x = (self.width - text_width) // 2
        
        glow_color = (
            int(COLORS['electric_teal'][0] * 0.3),
            int(COLORS['electric_teal'][1] * 0.3),
            int(COLORS['electric_teal'][2] * 0.3),
        )
        
        self.draw_text_with_glow(
            draw,
            project_name,
            (x, 490),
            self.fonts['title'],
            glow_color,
            COLORS['electric_teal']
        )
        
        img.save(output_path)
        print(f"✅ Fallback Code Stream graphic: {output_path}")


# Simple wrapper function for backward compatibility
def create_project_graphic(project_name, github_url, output_path):
    """Create a Code Stream branded graphic"""
    generator = CodeStreamGraphics()
    return generator.create_project_graphic(project_name, github_url, output_path)


if __name__ == "__main__":
    # Test with sample projects
    test_projects = [
        ("Serena", "https://github.com/oraios/Serena"),
        ("React", "https://github.com/facebook/react"),
        ("Kubernetes", "https://github.com/kubernetes/kubernetes"),
    ]
    
    generator = CodeStreamGraphics()
    
    for name, url in test_projects:
        print(f"\n{'='*60}")
        generator.create_project_graphic(name, url)
