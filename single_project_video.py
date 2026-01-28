"""
Single Project Video Generator for OpenSourceScribes
Creates a focused 2-3 minute video for a specific GitHub project
"""

import os
import asyncio
import json
import subprocess
from datetime import datetime
from gtts import gTTS
from branding import create_intro_card, create_outro_card

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

OUTPUT_FOLDER = "assets"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Organized delivery structure
current_date_mmdd = datetime.now().strftime("%m-%d")
DELIVERIES_ROOT = "deliveries"
DEEP_DIVES_FOLDER = os.path.join(DELIVERIES_ROOT, current_date_mmdd, "deep_dives")
os.makedirs(DEEP_DIVES_FOLDER, exist_ok=True)

def load_project_by_id(project_id):
    """Load a specific project from JSON by ID"""
    try:
        with open('posts_data.json', 'r') as f:
            projects = json.load(f)
            for project in projects:
                if project.get('id') == project_id:
                    return project
        print(f"❌ Project with ID '{project_id}' not found")
        return None
    except Exception as e:
        print(f"❌ Error loading projects: {e}")
        return None

async def create_project_visual(project_name, github_url, output_path):
    """Create custom graphic using Code Stream branding"""
    from codestream_graphics import create_project_graphic
    
    if os.path.exists(output_path):
        print(f"🎨 Graphic already exists: {output_path}")
        return True

    print(f"🎨 Creating Code Stream graphic for: {project_name}")
    try:
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
        print(f"🎙️ Hume.ai: {text[:50]}...")
        
        from hume import HumeClient
        from hume.tts import PostedUtterance
        
        client = HumeClient(api_key=CONFIG['hume_ai']['api_key'])
        
        audio_generator = client.tts.synthesize_file(
            utterances=[
                PostedUtterance(text=text)
            ]
        )
        
        audio_chunks = []
        for chunk in audio_generator:
            audio_chunks.append(chunk)
        
        audio_bytes = b''.join(audio_chunks)
        
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
        
        print(f"   ✅ Hume.ai voice generated successfully")
        return True
    except Exception as e:
        print(f"⚠️  Hume.ai failed: {e}")
        return False

def generate_audio_gtts(text, output_path):
    """Fallback: Generate audio using gTTS"""
    print(f"🎙️ gTTS: {text[:50]}...")
    tts = gTTS(text=text, lang='en')
    tts.save(output_path)
    print(f"   ✅ Audio generated")
    return True

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds"""
    if not os.path.exists(audio_path):
        return 0
    
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return float(result.stdout.strip())
    except:
        return 0

def create_static_segment(image_path, duration, output_name, audio_path=None):
    """Create video segment from static image"""
    if audio_path and os.path.exists(audio_path):
        duration = get_audio_duration(audio_path)
        cmd = [
            'ffmpeg', '-y', '-loop', '1', '-i', image_path,
            '-i', audio_path, '-c:v', 'libx264', '-preset', 'ultrafast',
            '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
            '-pix_fmt', 'yuv420p', '-shortest', output_name
        ]
    else:
        cmd = [
            'ffmpeg', '-y', '-loop', '1', '-i', image_path,
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-pix_fmt', 'yuv420p', '-t', str(duration), output_name
        ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return output_name

def create_segment(project):
    """Create video segment for a project"""
    project_id = project.get('id', 'project')
    project_name = project.get('name', 'Unknown')
    github_url = project.get('github_url', '')
    script_text = project.get('script_text', '')
    
    print(f"\n🎬 Processing: {project_name}")
    
    # Generate audio
    audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_audio.mp3")
    if not os.path.exists(audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(script_text, audio_path):
                generate_audio_gtts(script_text, audio_path)
        else:
            generate_audio_gtts(script_text, audio_path)
    
    # Generate graphic
    graphic_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_graphic.png")
    asyncio.run(create_project_visual(project_name, github_url, graphic_path))
    
    # Create segment
    duration = get_audio_duration(audio_path)
    segment_name = f"seg_{project_id}.mp4"
    
    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', graphic_path,
        '-i', audio_path, '-c:v', 'libx264', '-preset', 'ultrafast',
        '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p', '-shortest', segment_name
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return segment_name

def create_single_project_video(project_id, output_filename=None):
    """Create a focused video for a single project"""
    
    # Load project
    project = load_project_by_id(project_id)
    if not project:
        return False
    
    project_name = project.get('name', 'Project')
    
    # Generate output filename in deep_dives folder
    if not output_filename:
        output_filename = os.path.join(DEEP_DIVES_FOLDER, f"{project_id}_focused.mp4")
    
    print(f"\n{'='*60}")
    print(f"📹 Creating Single Project Video: {project_name}")
    print(f"{'='*60}")
    
    # Generate intro and outro with project-specific title
    print("\n🎨 Generating intro/outro cards...")
    intro_path = create_intro_card(CONFIG, f"Deep Dive: {project_name}")
    outro_path = create_outro_card(CONFIG)
    
    segment_files = []
    
    # 1. Intro (2-3 seconds)
    intro_audio_path = os.path.join(OUTPUT_FOLDER, "intro_audio_single.mp3")
    intro_text = f"Welcome to OpenSourceScribes. Today we're diving deep into {project_name}."
    
    if not os.path.exists(intro_audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(intro_text, intro_audio_path):
                generate_audio_gtts(intro_text, intro_audio_path)
        else:
            generate_audio_gtts(intro_text, intro_audio_path)
    
    if os.path.exists(intro_path):
        segment_files.append(create_static_segment(intro_path, 0, "seg_intro_single.mp4", audio_path=intro_audio_path))
    
    # 2. Main project segment
    segment_files.append(create_segment(project))
    
    # 3. Outro
    if os.path.exists(outro_path):
        segment_files.append(create_static_segment(outro_path, CONFIG['video_settings']['outro_duration'], "seg_outro_single.mp4"))
    
    # 4. Concatenate segments
    print("\n🔗 Concatenating segments...")
    concat_list_path = "concat_list_single.txt"
    with open(concat_list_path, 'w') as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
    
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        '-c:v', 'libx264', '-preset', 'ultrafast',
        '-c:a', 'aac', '-b:a', '192k',
        output_filename
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ VIDEO CREATED! Saved to: {output_filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to create video: {e}")
        return False
    finally:
        # Cleanup
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        for seg in segment_files:
            if os.path.exists(seg):
                os.remove(seg)

if __name__ == "__main__":
    # Create SmartCommit focused video
    project_id = "arpxspace_smartcommit"
    output_filename = "smartcommit_focused.mp4"
    
    success = create_single_project_video(project_id, output_filename)
    
    if success:
        print(f"\n🎉 Your SmartCommit video is ready!")
        print(f"   File: {output_filename}")
