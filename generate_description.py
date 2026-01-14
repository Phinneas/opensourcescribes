import json
import os
import subprocess
import datetime

def get_duration(filepath):
    """Get duration of a video file in seconds using ffprobe"""
    if not os.path.exists(filepath):
        return 0
    
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'default=noprint_wrappers=1:nokey=1', 
        filepath
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return float(result.stdout.strip())
    except (ValueError, subprocess.SubprocessError):
        return 0

def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    m, s = divmod(int(seconds), 60)
    return f"{m}:{s:02d}"

def generate_description():
    """Generate YouTube description from posts_data.json and video assets"""
    
    # Load project data
    if not os.path.exists('posts_data.json'):
        print("❌ posts_data.json not found")
        return

    with open('posts_data.json', 'r') as f:
        projects = json.load(f)
        
    print(f"found {len(projects)} projects")

    # Start constructing description
    output = []
    
    # --- HEADER ---
    today = datetime.date.today().strftime("%b %Y")
    output.append(f"# {len(projects)} Trending Open Source Projects ({today})")
    output.append("")
    output.append("In this episode of Open Source Scribes, we uncover incredible open source tools that will supercharge your development workflow. From new frameworks to essential dev tools, here are the hidden gems of GitHub you should know about.")
    output.append("")
    output.append(f"🔥 **Subscribe for more open source discoveries:** https://youtube.com/@opensourcescribes?sub_confirmation=1")
    output.append("")
    output.append("---")
    output.append("")
    output.append("## ⏱️ **Timestamps & Links**")
    output.append("")

    # --- TIMESTAMPS ---
    current_time = 0.0
    
    # 1. Intro
    # Use intro_audio.mp3 duration if it exists, otherwise default to config (usually 3s) or estimate
    intro_audio_path = "assets/intro_audio.mp3"
    intro_dur = get_duration(intro_audio_path)
    if intro_dur == 0:
        intro_dur = 3.0 # Fallback estimate
        
    output.append(f"{format_timestamp(current_time)} - Intro")
    current_time += intro_dur
    
    # 2. Projects
    midpoint = len(projects) // 2
    
    for i, project in enumerate(projects):
        # Calculate start time for this project
        output.append(f"{format_timestamp(current_time)} - **{project['name']}**")
        output.append(f"🔗 {project['github_url']}")
        output.append("")
        
        # Get audio duration for this project
        # ID is usually in posts_data, or we construct it?
        # simple_parser saves 'id' in posts_data.json
        project_id = project.get('id', '')
        if not project_id:
             # Fallback logic from video_maker if ID missing (shouldn't happen with current parser)
             safe_id = re.sub(r'[^a-zA-Z0-9]', '_', project['name']).lower()
             project_id = safe_id
             
        audio_path = f"assets/{project_id}_audio.mp3"
        seg_dur = get_duration(audio_path)
        
        # Add duration to current time
        current_time += seg_dur
        
        # Check for mid-roll subscribe
        if i == midpoint - 1:
            sub_path = "assets/subscribe_audio.mp3"
            sub_dur = get_duration(sub_path)
            if sub_dur > 0:
                current_time += sub_dur

        # Add light spacing
        # output.append("")
        
    # --- FOOTER ---
    output.append("---")
    output.append("")
    output.append("## 🏷️ **Tags**")
    output.append("#opensource #github #programming #webdevelopment #coding #tech #softwareengineering #python #javascript #devtools")
    output.append("")
    output.append("---")
    output.append("")
    output.append("**Disclaimer:** This video is for educational purposes. All project information corresponds to the state of the repositories at the time of recording.")

    # Write to file
    final_content = "\n".join(output)
    
    with open('YOUTUBE_DESCRIPTION.md', 'w') as f:
        f.write(final_content)
        
    print("\n✅ Generated YOUTUBE_DESCRIPTION.md")
    print("-" * 40)
    print(final_content)
    print("-" * 40)

if __name__ == "__main__":
    generate_description()
