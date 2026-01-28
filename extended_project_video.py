"""
Extended Project Video Generator for OpenSourceScribes
Creates longer 2-3 minute focused videos with multiple content segments
Fetches expanded content from GitHub README and generates rich, detailed videos
"""

import os
import asyncio
import json
import subprocess
import re
from datetime import datetime
from gtts import gTTS
from branding import create_intro_card, create_outro_card
import urllib.request

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

def fetch_github_readme(github_url):
    """Fetch README content from GitHub repository"""
    try:
        # Convert https://github.com/owner/repo to raw GitHub URL
        parts = github_url.rstrip('/').split('/')
        owner, repo = parts[-2], parts[-1]
        
        readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/README.md"
        
        with urllib.request.urlopen(readme_url, timeout=5) as response:
            content = response.read().decode('utf-8')
            return content
    except:
        # Try master branch if main doesn't exist
        try:
            readme_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/README.md"
            with urllib.request.urlopen(readme_url, timeout=5) as response:
                content = response.read().decode('utf-8')
                return content
        except:
            return None

def extract_readme_sections(readme_content):
    """Extract key sections from README"""
    sections = {
        'overview': '',
        'features': '',
        'installation': '',
        'usage': ''
    }
    
    if not readme_content:
        return sections
    
    content = readme_content.lower()
    lines = readme_content.split('\n')
    
    # Extract overview (first paragraph before any headers)
    overview_lines = []
    for line in lines:
        if line.startswith('#'):
            break
        if line.strip() and not line.startswith('!'):
            overview_lines.append(line.strip())
    sections['overview'] = ' '.join(overview_lines[:3])
    
    # Extract features section
    if 'feature' in content:
        for i, line in enumerate(lines):
            if 'feature' in line.lower() and '#' in line:
                features = []
                for j in range(i+1, min(i+10, len(lines))):
                    if lines[j].startswith('#') and j > i:
                        break
                    if lines[j].strip().startswith('-') or lines[j].strip().startswith('*'):
                        features.append(lines[j].strip()[2:])
                sections['features'] = ' '.join(features[:3])
                break
    
    # Extract installation section
    if 'install' in content:
        for i, line in enumerate(lines):
            if 'install' in line.lower() and '#' in line:
                install_lines = []
                for j in range(i+1, min(i+8, len(lines))):
                    if lines[j].startswith('#') and j > i:
                        break
                    if lines[j].strip():
                        install_lines.append(lines[j].strip())
                sections['installation'] = ' '.join(install_lines[:2])
                break
    
    return sections

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

def create_segment_with_text(project, segment_type, script_text, segment_id):
    """Create video segment for a specific content section"""
    segment_name = f"seg_{segment_id}.mp4"
    audio_path = os.path.join(OUTPUT_FOLDER, f"{segment_id}_audio.mp3")
    graphic_path = os.path.join(OUTPUT_FOLDER, f"{segment_id}_graphic.png")
    
    # Generate audio
    if not os.path.exists(audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(script_text, audio_path):
                generate_audio_gtts(script_text, audio_path)
        else:
            generate_audio_gtts(script_text, audio_path)
    
    # Generate graphic
    if not os.path.exists(graphic_path):
        asyncio.run(create_project_visual(project.get('name', 'Project'), 
                                         project.get('github_url', ''), 
                                         graphic_path))
    
    # Create segment
    cmd = [
        'ffmpeg', '-y', '-loop', '1', '-i', graphic_path,
        '-i', audio_path, '-c:v', 'libx264', '-preset', 'ultrafast',
        '-tune', 'stillimage', '-c:a', 'aac', '-b:a', '192k',
        '-pix_fmt', 'yuv420p', '-shortest', segment_name
    ]
    
    subprocess.run(cmd, check=True, capture_output=True)
    return segment_name

def create_extended_project_video(project_id, output_filename=None):
    """Create an extended 2-3 minute focused video for a project"""
    
    # Load project
    project = load_project_by_id(project_id)
    if not project:
        return False
    
    project_name = project.get('name', 'Project')
    github_url = project.get('github_url', '')
    
    # Generate output filename in deep_dives folder
    if not output_filename:
        output_filename = os.path.join(DEEP_DIVES_FOLDER, f"{project_id}_extended.mp4")
    
    print(f"\n{'='*60}")
    print(f"📹 Creating Extended Project Video: {project_name}")
    print(f"{'='*60}")
    
    # Fetch GitHub README for enhanced content
    print(f"\n🔍 Fetching GitHub README...")
    readme_content = fetch_github_readme(github_url)
    readme_sections = extract_readme_sections(readme_content) if readme_content else {}
    
    # Generate intro and outro
    print("\n🎨 Generating intro/outro cards...")
    intro_path = create_intro_card(CONFIG, f"Deep Dive: {project_name}")
    outro_path = create_outro_card(CONFIG)
    
    segment_files = []
    
    # 1. INTRO SEGMENT (~10-15 seconds)
    print("\n📝 Creating intro segment...")
    intro_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_intro_audio.mp3")
    intro_text = f"Welcome to OpenSourceScribes. Today we're diving deep into {project_name}. This powerful open source project is changing the way developers work."
    
    if not os.path.exists(intro_audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(intro_text, intro_audio_path):
                generate_audio_gtts(intro_text, intro_audio_path)
        else:
            generate_audio_gtts(intro_text, intro_audio_path)
    
    if os.path.exists(intro_path):
        segment_files.append(create_static_segment(intro_path, 0, "seg_extended_intro.mp4", audio_path=intro_audio_path))
    
    # 2. OVERVIEW SEGMENT (~30-40 seconds)
    print("📝 Creating overview segment...")
    overview_text = project.get('script_text', 'This is an amazing open source project.')
    overview_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_overview_audio.mp3")
    
    if not os.path.exists(overview_audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(overview_text, overview_audio_path):
                generate_audio_gtts(overview_text, overview_audio_path)
        else:
            generate_audio_gtts(overview_text, overview_audio_path)
    
    segment_files.append(create_segment_with_text(project, 'overview', overview_text, f"{project_id}_overview"))
    
    # 3. FEATURES SEGMENT (~30-40 seconds) - if README content available
    if readme_sections.get('features'):
        print("📝 Creating features segment...")
        features_text = f"{project_name} includes impressive features: {readme_sections['features']} These capabilities make it stand out in the open source ecosystem."
        features_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_features_audio.mp3")
        
        if not os.path.exists(features_audio_path):
            use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
            if use_hume and CONFIG['hume_ai']['api_key']:
                if not generate_audio_hume(features_text, features_audio_path):
                    generate_audio_gtts(features_text, features_audio_path)
            else:
                generate_audio_gtts(features_text, features_audio_path)
        
        segment_files.append(create_segment_with_text(project, 'features', features_text, f"{project_id}_features"))
    
    # 4. USE CASES SEGMENT (~25-35 seconds)
    print("📝 Creating use cases segment...")
    use_cases_text = f"Developers use {project_name} to build better solutions, streamline workflows, and solve complex technical challenges. Whether you're working on production systems or experimental projects, this tool adapts to your needs."
    use_cases_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_usecases_audio.mp3")
    
    if not os.path.exists(use_cases_audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(use_cases_text, use_cases_audio_path):
                generate_audio_gtts(use_cases_text, use_cases_audio_path)
        else:
            generate_audio_gtts(use_cases_text, use_cases_audio_path)
    
    segment_files.append(create_segment_with_text(project, 'usecases', use_cases_text, f"{project_id}_usecases"))
    
    # 5. INSTALLATION SEGMENT (~15-25 seconds) - if README content available
    if readme_sections.get('installation'):
        print("📝 Creating installation segment...")
        install_text = f"Getting started with {project_name} is straightforward. Visit the GitHub repository for detailed installation instructions. The project provides excellent documentation to help you get up and running quickly."
        install_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_install_audio.mp3")
        
        if not os.path.exists(install_audio_path):
            use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
            if use_hume and CONFIG['hume_ai']['api_key']:
                if not generate_audio_hume(install_text, install_audio_path):
                    generate_audio_gtts(install_text, install_audio_path)
            else:
                generate_audio_gtts(install_text, install_audio_path)
        
        segment_files.append(create_segment_with_text(project, 'installation', install_text, f"{project_id}_install"))
    
    # 6. CTA SEGMENT (~10-15 seconds)
    print("📝 Creating call-to-action segment...")
    cta_text = f"Check out {project_name} on GitHub today. Subscribe to OpenSourceScribes for more deep dives into amazing open source projects. Thanks for watching!"
    cta_audio_path = os.path.join(OUTPUT_FOLDER, f"{project_id}_cta_audio.mp3")
    
    if not os.path.exists(cta_audio_path):
        use_hume = CONFIG.get('hume_ai', {}).get('use_hume', False)
        if use_hume and CONFIG['hume_ai']['api_key']:
            if not generate_audio_hume(cta_text, cta_audio_path):
                generate_audio_gtts(cta_text, cta_audio_path)
        else:
            generate_audio_gtts(cta_text, cta_audio_path)
    
    if os.path.exists(outro_path):
        segment_files.append(create_static_segment(outro_path, 0, "seg_extended_outro.mp4", audio_path=cta_audio_path))
    
    # 7. Concatenate all segments
    print("\n🔗 Concatenating segments...")
    concat_list_path = "concat_list_extended.txt"
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
        print(f"\n✅ EXTENDED VIDEO CREATED! Saved to: {output_filename}")
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
    import sys
    
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        output_filename = sys.argv[2] if len(sys.argv) > 2 else None
    else:
        # Default to smartcommit
        project_id = "arpxspace_smartcommit"
        output_filename = None
    
    success = create_extended_project_video(project_id, output_filename)
    
    if success:
        print(f"\n🎉 Your extended video is ready!")
