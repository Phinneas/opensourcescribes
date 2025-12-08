import os
import asyncio
import json
from playwright.async_api import async_playwright
from moviepy import *
from gtts import gTTS
from branding import create_intro_card, create_outro_card

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# CONFIGURATION
OUTPUT_FOLDER = "assets"
FINAL_VIDEO_NAME = "final_github_roundup.mp4"
DATA_FILE = "posts_data.json"

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def load_project_data():
    """Load project data from JSON file"""
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Data file '{DATA_FILE}' not found.")
        return []
    except json.JSONDecodeError:
        print("❌ Error: Could not read JSON file. Check syntax.")
        return []

async def create_project_visual(project_name, github_url, output_path):
    """Create custom graphic using Code Stream branding"""
    from codestream_graphics import create_project_graphic
    
    print(f"🎨 Creating Code Stream graphic for: {project_name}")
    try:
        # Run in thread pool to avoid blocking
        import asyncio
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            create_project_graphic,
            project_name,
            github_url,
            output_path
        )
        return True
    except Exception as e:
        print(f"❌ Failed to create graphic: {e}")
        return False

def generate_audio_hume(text, output_path):
    """Generate audio using Hume.ai (premium voice)"""
    try:
        print(f"🎙️ Hume.ai: {text[:30]}...")
        
        from hume import HumeClient
        from hume.tts import PostedUtterance
        
        # Initialize Hume client with API key
        client = HumeClient(api_key=CONFIG['hume_ai']['api_key'])
        
        # Generate speech using TTS synthesize_json with utterances
        response = client.tts.synthesize_json(
            utterances=[
                PostedUtterance(text=text)
            ]
        )
        
        # Extract audio data from response
        # Response is a ReturnTts object with audio_url or audio_data
        if hasattr(response, 'audio_url'):
            # Download from URL
            import requests
            audio_data = requests.get(response.audio_url).content
        elif hasattr(response, 'audio'):
            audio_data = response.audio
        else:
            # Try to get the raw bytes
            audio_data = bytes(response)
        
        # Save audio
        with open(output_path, 'wb') as f:
            f.write(audio_data)
        
        print(f"   ✅ Hume.ai voice generated successfully")
        return True
    except Exception as e:
        print(f"⚠️  Hume.ai failed: {e}")
        print("   Falling back to gTTS...")
        return False

def generate_audio_gtts(text, output_path):
    """Fallback: Generate audio using gTTS"""
    print(f"🎙️ gTTS: {text[:30]}...")
    tts = gTTS(text=text, lang='en')
    tts.save(output_path)

def generate_audio(text, output_path):
    """Generate audio - tries Hume.ai first, falls back to gTTS"""
    if CONFIG['hume_ai'].get('use_hume', False):
        if generate_audio_hume(text, output_path):
            return
    
    # Fallback to gTTS
    generate_audio_gtts(text, output_path)

async def prepare_assets(project_data):
    """Generate all graphics and audio files"""
    tasks = []
    for i, project in enumerate(project_data):
        project_id = project.get('id', f'p{i+1}')
        
        img_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_screen.png")
        audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_audio.mp3")
        project['img_path'] = img_path
        project['audio_path'] = audio_path
        
        # Generate audio
        generate_audio(project['script_text'], audio_path)
        
        # Queue graphic creation task
        tasks.append(create_project_visual(
            project['name'],
            project['github_url'],
            img_path
        ))
    
    await asyncio.gather(*tasks)

def create_text_overlay(text, duration, size=(1920, 1080)):
    """Create a text overlay clip with semi-transparent background"""
    from moviepy.video.VideoClip import TextClip, ColorClip
    from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
    
    # Create text clip with correct MoviePy 2.x parameters
    txt_clip = TextClip(
        text=text,
        font_size=CONFIG['video_settings']['font_size'],
        color=CONFIG['video_settings']['text_color'],
        method='caption',
        size=(1800, None),  # Max width, auto height
        text_align='center'
    )
    
    # Set duration and position
    txt_clip = txt_clip.with_duration(duration).with_position(('center', 900))
    
    # Create semi-transparent background bar
    bg_height = 120
    bg_clip = ColorClip(
        size=(1920, bg_height),
        color=(0, 0, 0)
    ).with_opacity(0.7).with_duration(duration).with_position(('center', 880))
    
    # Composite background and text
    overlay = CompositeVideoClip([bg_clip, txt_clip], size=size)
    
    return overlay

def assemble_video(project_data, episode_title=None):
    """Assemble final video with intro, content, and outro"""
    if not project_data:
        print("❌ No project data to assemble.")
        return
    
    print("🎬 Assembling video...")
    
    # Generate intro/outro cards
    intro_path = create_intro_card(CONFIG, episode_title)
    outro_path = create_outro_card(CONFIG)
    
    clips = []
    
    # INTRO CARD
    intro_duration = CONFIG['video_settings']['intro_duration']
    intro_clip = ImageClip(intro_path).with_duration(intro_duration)
    clips.append(intro_clip)
    
    # PROJECT CLIPS
    for project in project_data:
        audio = AudioFileClip(project['audio_path'])
        duration = audio.duration
        
        # Base image clip
        img = (ImageClip(project['img_path'])
               .resized(height=1080)
               .cropped(x_center=960, y_center=540, width=1920, height=1080)
               .with_duration(duration))
        
        # Add text overlay with project name
        text_overlay = create_text_overlay(project['name'], duration)
        
        # Composite image + text overlay
        from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
        video_with_text = CompositeVideoClip([img, text_overlay])
        
        # Add audio
        clip = video_with_text.with_audio(audio)
        clips.append(clip)
    
    # OUTRO CARD
    outro_duration = CONFIG['video_settings']['outro_duration']
    outro_clip = ImageClip(outro_path).with_duration(outro_duration)
    clips.append(outro_clip)
    
    # Concatenate all clips
    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(FINAL_VIDEO_NAME, fps=24, codec="libx264", audio_codec="aac")
    print(f"✅ DONE! Video saved to: {FINAL_VIDEO_NAME}")

if __name__ == "__main__":
    # Load project data
    project_data = load_project_data()
    
    if project_data:
        # You can set episode title here or extract from first project
        episode_title = "GitHub Projects Roundup"
        
        # Generate assets
        asyncio.run(prepare_assets(project_data))
        
        # Assemble video
        assemble_video(project_data, episode_title)
