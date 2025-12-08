"""
Custom Graphics Generator for GitHub Projects
Creates visually appealing backgrounds instead of plain screenshots
"""

import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random
import re

def get_github_stats(owner, repo):
    """Fetch GitHub repository stats"""
    try:
        url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'language': data.get('language', 'Unknown'),
                'description': data.get('description', ''),
                'topics': data.get('topics', [])[:3]  # First 3 topics
            }
    except Exception as e:
        print(f"⚠️  Failed to fetch stats for {owner}/{repo}: {e}")
    
    return {
        'stars': 0,
        'forks': 0,
        'language': 'Unknown',
        'description': '',
        'topics': []
    }

def format_number(num):
    """Format large numbers (e.g., 15200 -> 15.2k)"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.1f}k"
    return str(num)

def get_gradient_colors(language):
    """Get gradient colors based on programming language"""
    language_colors = {
        'Python': ('#3776ab', '#ffd343'),
        'JavaScript': ('#f7df1e', '#323330'),
        'TypeScript': ('#3178c6', '#235a97'),
        'Go': ('#00add8', '#00758d'),
        'Rust': ('#ce422b', '#f74c00'),
        'Java': ('#b07219', '#5382a1'),
        'C++': ('#f34b7d', '#00599c'),
        'Ruby': ('#cc342d', '#701516'),
        'PHP': ('#4f5d95', '#8892bf'),
        'Swift': ('#ffac45', '#f05138'),
        'Kotlin': ('#a97bff', '#7f52ff'),
        'C#': ('#178600', '#239120'),
        'Shell': ('#89e051', '#4eaa25'),
        'HTML': ('#e34c26', '#f06529'),
        'CSS': ('#563d7c', '#264de4'),
    }
    
    return language_colors.get(language, ('#667eea', '#764ba2'))

def create_project_graphic(project_name, github_url, output_path):
    """Create a custom graphic in OpenSourceScribes Code Stream aesthetic"""
    
    # Extract owner/repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if not match:
        print(f"⚠️  Invalid GitHub URL: {github_url}")
        create_fallback_graphic(project_name, output_path)
        return
    
    owner, repo = match.groups()
    
    # Fetch GitHub stats
    print(f"📊 Fetching stats for {owner}/{repo}...")
    stats = get_github_stats(owner, repo)
    
    # Create image with dark blue background
    width, height = 1920, 1080
    img = Image.new('RGB', (width, height), color='#0a1628')
    draw = ImageDraw.Draw(img)
    
    # Create teal/cyan gradient overlay (matching your style)
    gradient = Image.new('RGB', (width, height))
    gradient_draw = ImageDraw.Draw(gradient)
    
    for y in range(height):
        ratio = y / height
        # Deep blue to electric teal gradient
        r = int(10 + (64 - 10) * ratio)
        g = int(22 + (224 - 22) * ratio)
        b = int(40 + (208 - 40) * ratio)
        gradient_draw.rectangle([(0, y), (width, y + 1)], fill=(r, g, b))
    
    # Blend gradient with base (40% opacity)
    img = Image.blend(img, gradient, 0.4)
    draw = ImageDraw.Draw(img)
    
    # Add glowing grid pattern
    grid_color = (64, 224, 208, 30)  # Electric teal with transparency
    overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    
    # Horizontal lines
    for y in range(0, height, 80):
        overlay_draw.line([(0, y), (width, y)], fill=grid_color, width=1)
    
    # Vertical lines
    for x in range(0, width, 80):
        overlay_draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    
    # Add some diagonal lines for "data flow" effect
    for i in range(-height, width, 200):
        overlay_draw.line([(i, 0), (i + height, height)], fill=(64, 224, 208, 15), width=2)
    
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 140)
        label_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
        stats_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 45)
    except:
        title_font = ImageFont.load_default()
        label_font = ImageFont.load_default()
        stats_font = ImageFont.load_default()
    
    # Draw "Tool:" label at top
    tool_label = "Tool:"
    bbox = draw.textbbox((0, 0), tool_label, font=label_font)
    label_width = bbox[2] - bbox[0]
    draw.text((100, 150), tool_label, font=label_font, fill=(100, 200, 255))
    
    # Draw project name prominently (matching your style)
    project_display = repo.replace('-', ' ').replace('_', ' ').upper()
    bbox = draw.textbbox((0, 0), project_display, font=title_font)
    text_width = bbox[2] - bbox[0]
    
    # Center the project name
    x = (width - text_width) // 2
    y = 400
    
    # Draw with glow effect (multiple layers)
    for offset in [6, 4, 2]:
        draw.text((x + offset, y + offset), project_display, font=title_font, fill=(0, 100, 120))
    
    # Main text in electric teal
    draw.text((x, y), project_display, font=title_font, fill='#40E0D0')
    
    # Draw stats bar at bottom
    stats_y = 850
    stats_spacing = 400
    
    # Stars
    stars_text = f"⭐ {format_number(stats['stars'])}"
    draw.text((width // 2 - stats_spacing, stats_y), stars_text, font=stats_font, fill='white')
    
    # Forks
    forks_text = f"🍴 {format_number(stats['forks'])}"
    bbox = draw.textbbox((0, 0), forks_text, font=stats_font)
    forks_width = bbox[2] - bbox[0]
    draw.text((width // 2 - forks_width // 2, stats_y), forks_text, font=stats_font, fill='white')
    
    # Language
    lang_text = f"📝 {stats['language']}"
    bbox = draw.textbbox((0, 0), lang_text, font=stats_font)
    lang_width = bbox[2] - bbox[0]
    draw.text((width // 2 + stats_spacing - lang_width, stats_y), lang_text, font=stats_font, fill='white')
    
    # Add subtle glow lines at top and bottom
    glow_overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_overlay)
    
    # Top glow line
    for i in range(5):
        glow_draw.line([(0, 100 + i), (width, 100 + i)], fill=(64, 224, 208, 50 - i * 10), width=2)
    
    # Bottom glow line
    for i in range(5):
        glow_draw.line([(0, 950 + i), (width, 950 + i)], fill=(64, 224, 208, 50 - i * 10), width=2)
    
    img = Image.alpha_composite(img.convert('RGBA'), glow_overlay).convert('RGB')
    
    # Save
    img.save(output_path)
    print(f"✅ Created Code Stream graphic: {output_path}")

def create_fallback_graphic(project_name, output_path):
    """Create a simple fallback graphic if GitHub API fails"""
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
    except:
        font = ImageFont.load_default()
    
    bbox = draw.textbbox((0, 0), project_name, font=font)
    text_width = bbox[2] - bbox[0]
    x = (1920 - text_width) // 2
    draw.text((x, 490), project_name, font=font, fill='white')
    
    img.save(output_path)
    print(f"✅ Created fallback graphic: {output_path}")

if __name__ == "__main__":
    # Test
    create_project_graphic(
        "Test Project",
        "https://github.com/oraios/Serena",
        "test_graphic.png"
    )
