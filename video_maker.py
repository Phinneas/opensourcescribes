import os
import asyncio
import json
import subprocess
from datetime import datetime
from gtts import gTTS
from branding import create_intro_card, create_outro_card, create_subscribe_card

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)

# CONFIGURATION
OUTPUT_FOLDER = "assets"
DATA_FILE = "posts_data.json"
# Generate filename with current date: github_roundup_dec10.mp4
# current_date = datetime.now().strftime("%b%d").lower()
FINAL_VIDEO_NAME = "github_roundup_jan10.mp4"

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
    
    # Check if exists
    if os.path.exists(output_path):
        print(f"🎨 Graphic already exists: {output_path}")
        return True

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
        
        # Generate speech using TTS synthesize_file (returns a generator)
        audio_generator = client.tts.synthesize_file(
            utterances=[
                PostedUtterance(text=text)
            ]
        )
        
        # Collect all chunks from the generator
        audio_chunks = []
        for chunk in audio_generator:
            audio_chunks.append(chunk)
        
        # Combine all chunks into bytes
        audio_bytes = b''.join(audio_chunks)
        
        # Save audio bytes to file
        with open(output_path, 'wb') as f:
            f.write(audio_bytes)
        
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

def trim_audio_silence(input_path):
    """Trim silence from the beginning of the audio file"""
    temp_path = input_path.replace('.mp3', '_trimmed.mp3')
    
    # ffmpeg filter: start_periods=1 (trim start), start_duration=0 (trim until non-silence), threshold=-50dB
    cmd = [
        'ffmpeg', '-y',
        '-i', input_path,
        '-af', 'silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB',
        temp_path
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # Replace original with trimmed
    os.replace(temp_path, input_path)

def generate_audio(text, output_path):
    """Generate audio - tries Hume.ai first, falls back to gTTS"""
    if os.path.exists(output_path):
        print(f"   ✅ Audio already exists: {output_path}")
        # Even if it exists, we might want to trim it if not already trimmed? 
        # But safest is to assume existing assets are 'done'. 
        # However, for this fix, we should probably force re-generation or at least trim existing ones.
        # Let's assume we will clear assets or the user wants us to fix existing ones.
        # For now, let's just trim even if it exists, to be safe, OR just return.
        # The user wants to FIX it. If I don't delete assets, I must trim them.
        trim_audio_silence(output_path)
        return

    if CONFIG['hume_ai'].get('use_hume', False):
        if generate_audio_hume(text, output_path):
            trim_audio_silence(output_path)
            return
    
    # Fallback to gTTS
    generate_audio_gtts(text, output_path)
    trim_audio_silence(output_path)

async def prepare_assets(project_data):
    """Generate all graphics and audio files"""
    tasks = []
    
    # 1. Prepare project assets
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
    
    # 2. Prepare Subscriber Solicitation Audio
    sub_audio_path = os.path.join(OUTPUT_FOLDER, "subscribe_audio.mp3")
    sub_text = "If you're finding these tools useful, please subscribe for more open source discoveries."
    generate_audio(sub_text, sub_audio_path)

    # 3. Prepare Intro Audio
    intro_audio_path = os.path.join(OUTPUT_FOLDER, "intro_audio.mp3")
    intro_text = "Welcome back, glad you could stop by! Today we're diggin into 11 incredible open source projects that you need to know about. Let's get started!"
    generate_audio(intro_text, intro_audio_path)
    
    await asyncio.gather(*tasks)

def create_segment(project, index):
    """Create a video segment for a single project using ffmpeg"""
    # Reconstruct paths if not in JSON
    if 'img_path' not in project:
         image_path = os.path.join(OUTPUT_FOLDER, f"{project['id']}_screen.png")
         audio_path = os.path.join(OUTPUT_FOLDER, f"{project['id']}_audio.mp3")
    else:
         image_path = project['img_path']
         audio_path = project['audio_path']

    output_segment = os.path.join(OUTPUT_FOLDER, f"segment_{index:03d}.mp4")
    
    print(f"🎬 Rendering segment {index}: {project['name']}...")
    
    # FFmpeg command to loop image over audio
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
        output_segment
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_segment

def create_static_segment(image_path, duration, output_name, audio_path=None):
    """Create static segment (intro/outro/subscribe)"""
    output_path = os.path.join(OUTPUT_FOLDER, output_name)
    print(f"🎬 Rendering static segment: {output_name}...")
    
    # Base command
    cmd = [
        'ffmpeg', '-y',
        '-loop', '1', '-framerate', '24',
        '-i', image_path
    ]
    
    # If custom audio is provided (like for subscribe card)
    if audio_path:
        cmd.extend(['-i', audio_path])
        shortest_flag = '-shortest'
    else:
        # Generate silent audio for specific duration
        cmd.extend(['-f', 'lavfi', '-i', f'anullsrc=channel_layout=stereo:sample_rate=44100'])
        shortest_flag = '-t' # We use duration, not shortest for silent audio clips
    
    cmd.extend([
        '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'stillimage',
        '-c:a', 'aac',
    ])
    
    if audio_path:
        cmd.append(shortest_flag)
    else:
         # For silence, we specify duration directly on output or input?
         # FFmpeg -t applies to output if placed before output filename
         cmd.extend(['-t', str(duration)])

    cmd.extend([
        '-pix_fmt', 'yuv420p',
        output_path
    ])
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_path

def assemble_video_fast(project_data, episode_title=None):
    """Assemble final video using fast FFmpeg concatenation"""
    if not project_data:
        print("❌ No project data to assemble.")
        return
    
    print("🎬 Assembling video (Fast Mode)...")
    
    # Generate cards
    intro_path = create_intro_card(CONFIG, episode_title)
    outro_path = create_outro_card(CONFIG)
    sub_card_path = create_subscribe_card(CONFIG)
    sub_audio_path = os.path.join(OUTPUT_FOLDER, "subscribe_audio.mp3")
    
    segment_files = []
    
    # 1. Intro
    intro_audio_path = os.path.join(OUTPUT_FOLDER, "intro_audio.mp3")
    if os.path.exists(intro_path):
        # Use audio if available, otherwise silent (defaults to duration from config)
        if os.path.exists(intro_audio_path):
             segment_files.append(create_static_segment(intro_path, 0, "seg_intro.mp4", audio_path=intro_audio_path))
        else:
             segment_files.append(create_static_segment(intro_path, CONFIG['video_settings']['intro_duration'], "seg_intro.mp4"))
    
    # 2. Projects (with Mid-Roll Insertion)
    midpoint = len(project_data) // 2
    
    for i, project in enumerate(project_data):
        # Ensure 'id' is present
        if 'id' not in project:
            project['id'] = f'p{i+1}'
        segment_files.append(create_segment(project, i))
        
        # INSERT SUBSCRIBE SEGMENT
        if i == midpoint - 1:
             print("🔔 Inserting Subscriber Prompt...")
             if os.path.exists(sub_card_path) and os.path.exists(sub_audio_path):
                 sub_seg = create_static_segment(sub_card_path, 0, "seg_subscribe.mp4", audio_path=sub_audio_path)
                 segment_files.append(sub_seg)
        
    # 3. Outro
    if os.path.exists(outro_path):
        segment_files.append(create_static_segment(outro_path, CONFIG['video_settings']['outro_duration'], "seg_outro.mp4"))
        
    # 4. Concatenate
    print("\n🔗 Concatenating segments...")
    concat_list_path = "concat_list.txt"
    with open(concat_list_path, 'w') as f:
        for seg in segment_files:
            f.write(f"file '{seg}'\n")
            
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', concat_list_path,
        # Remove stream copy to fix timestamp/DTS issues
        # Re-encode ensures monotonic timestamps and perfect sync
        '-c:v', 'libx264', '-preset', 'ultrafast',
        '-c:a', 'aac', '-b:a', '192k',
        FINAL_VIDEO_NAME
    ]
    
    try:
        subprocess.run(cmd, check=True)
        print(f"\n✅ DONE! Video saved to: {FINAL_VIDEO_NAME}")
    finally:
        # Cleanup
        if os.path.exists(concat_list_path):
            os.remove(concat_list_path)
        for seg in segment_files:
            if os.path.exists(seg):
                os.remove(seg)

if __name__ == "__main__":
    # Load project data
    project_data = load_project_data()
    
    if project_data:
        # You can set episode title here or extract from first project
        episode_title = "GitHub Projects Roundup"
        
        # Generate assets (Graphics + Audio)
        # Note: prepare_assets populates img_path/audio_path in project_data dicts
        asyncio.run(prepare_assets(project_data))
        
        # Assemble video
        assemble_video_fast(project_data, episode_title)
