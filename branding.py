"""
Branding and Graphics Generator for OpenSourceScribes Videos
Creates intro/outro cards and handles text overlays
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_intro_card(config, episode_title=None, output_path="assets/intro_card.png"):
    """Create branded intro card"""
    # Create 1920x1080 image
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 120)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Draw channel name
    channel_name = config['branding']['channel_name']
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), channel_name, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (1920 - text_width) // 2
    y = 400
    
    # Draw text with shadow for depth
    draw.text((x+3, y+3), channel_name, font=title_font, fill='#0f3460')
    draw.text((x, y), channel_name, font=title_font, fill='#16c79a')
    
    # Draw episode title if provided
    if episode_title:
        bbox = draw.textbbox((0, 0), episode_title, font=subtitle_font)
        text_width = bbox[2] - bbox[0]
        x = (1920 - text_width) // 2
        y = 600
        draw.text((x, y), episode_title, font=subtitle_font, fill='#ffffff')
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"✅ Created intro card: {output_path}")
    return output_path

def create_outro_card(config, output_path="assets/outro_card.png"):
    """Create branded outro card with subscribe prompt"""
    # Create 1920x1080 image
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 100)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 50)
        small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Main message
    message = "Thanks for Watching!"
    bbox = draw.textbbox((0, 0), message, font=title_font)
    text_width = bbox[2] - bbox[0]
    x = (1920 - text_width) // 2
    y = 300
    draw.text((x, y), message, font=title_font, fill='#16c79a')
    
    # Subscribe prompt
    subscribe = "Subscribe to OpenSourceScribes"
    bbox = draw.textbbox((0, 0), subscribe, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (1920 - text_width) // 2
    y = 500
    draw.text((x, y), subscribe, font=subtitle_font, fill='#ffffff')
    
    # Social handles
    social_y = 650
    socials = [
        f"Medium: {config['branding']['medium']}",
        f"Reddit: {config['branding']['reddit']}",
    ]
    
    for social in socials:
        bbox = draw.textbbox((0, 0), social, font=small_font)
        text_width = bbox[2] - bbox[0]
        x = (1920 - text_width) // 2
        draw.text((x, social_y), social, font=small_font, fill='#cccccc')
        social_y += 60
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"✅ Created outro card: {output_path}")
    return output_path

def create_subscribe_card(config, output_path="assets/subscribe_card.png"):
    """Create a dedicated Subscribe call-to-action card"""
    # Create 1920x1080 image
    img = Image.new('RGB', (1920, 1080), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font
    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 110)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
    
    # Draw simple, bold message
    message = "Enjoying these tools?"
    bbox = draw.textbbox((0, 0), message, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (1920 - text_width) // 2
    y = 350
    draw.text((x, y), message, font=subtitle_font, fill='#cccccc')
    
    cta = "SUBSCRIBE"
    bbox = draw.textbbox((0, 0), cta, font=title_font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (1920 - text_width) // 2
    y = 500
    
    # Draw simple button background
    padding = 40
    button_coords = [x - padding, y - padding, x + text_width + padding, y + text_height + padding]
    draw.rectangle(button_coords, fill='#e63946', outline=None)
    
    draw.text((x, y), cta, font=title_font, fill='#ffffff')
    
    # Subtext
    sub = "for more Open Source discoveries"
    bbox = draw.textbbox((0, 0), sub, font=subtitle_font)
    text_width = bbox[2] - bbox[0]
    x = (1920 - text_width) // 2
    y = 700
    draw.text((x, y), sub, font=subtitle_font, fill='#cccccc')
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    img.save(output_path)
    print(f"✅ Created subscribe card: {output_path}")
    return output_path

if __name__ == "__main__":
    # Test the card generation
    import json
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    create_intro_card(config, "9 Trending GitHub Repos")
    create_outro_card(config)
    print("✅ Test cards created successfully!")
