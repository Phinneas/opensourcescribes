#!/usr/bin/env python3
"""
Re-render video only using existing audio files.
Skips audio generation and screenshot capture - just re-renders the video segments.
"""

import os
import json
from pathlib import Path
from video_automated import VideoSuiteAutomated

def re_render_video_only():
    """Re-render video using existing audio files and project data."""
    
    # Load existing project data with audio paths
    data_file = "posts_data_longform.json"
    if not os.path.exists(data_file):
        print(f"❌ No project data found at {data_file}")
        print("   Run the full pipeline first to generate audio files")
        return
    
    with open(data_file, 'r') as f:
        projects = json.load(f)
    
    print(f"✅ Loaded {len(projects)} projects with existing audio")
    
    # Create video suite instance
    suite = VideoSuiteAutomated()
    suite.projects = projects
    
    # Skip audio generation and screenshot capture
    # Just re-render the video assembly
    print("\n🎬 Re-rendering video segments only...")
    
    # Re-render each segment
    for i, project in enumerate(projects):
        audio_path = project.get('audio_path', '')
        if not audio_path or not os.path.exists(audio_path):
            print(f"⚠️  No audio for {project['name']} - skipping")
            continue
        
        print(f"\n📹 Rendering segment {i+1}/{len(projects)}: {project['name']}")
        suite._render_segment_ffmpeg(project, i, audio_path)
    
    # Assemble the full video
    print("\n🎬 Assembling final video...")
    suite.assemble_longform_video()
    
    print("\n✅ Video re-render complete!")

if __name__ == "__main__":
    re_render_video_only()
