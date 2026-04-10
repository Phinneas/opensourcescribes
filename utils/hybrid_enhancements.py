"""
Hybrid Video Enhancement - Best of Both Worlds
• MiniMax for intro (high impact, ~$0.25)
• FFmpeg Ken Burns for projects (free, professional)
"""

import os
import subprocess
from pathlib import Path
from typing import Optional

# Import both systems
from minimax_intro_generator import generate_intro_with_audio
from ffmpeg_enhancements import get_random_effect


def create_hybrid_intro(
    intro_audio_path: str = "assets/intro_audio.mp3",
    episode_title: str = "GitHub Projects Roundup",
    output_path: str = "assets/seg_intro.mp4"
) -> str:
    """
    Create intro using MiniMax (with fallback to static)
    
    Args:
        intro_audio_path: Path to intro narration audio
        episode_title: Title to display
        output_path: Output video path
        
    Returns:
        Path to generated intro
    """
    print("\n🎬 CREATING INTRO (MiniMax + Audio)")
    print("-" * 40)
    
    result = generate_intro_with_audio(
        intro_audio_path=intro_audio_path,
        output_path=output_path,
        episode_title=episode_title,
        fallback_to_static=True
    )
    
    return result


def create_project_segment_ffmpeg(
    image_path: str,
    audio_path: str,
    output_path: str
) -> str:
    """
    Create project segment using FREE FFmpeg Ken Burns effect
    
    Args:
        image_path: Project screenshot
        audio_path: Project narration
        output_path: Output video
        
    Returns:
        Path to generated segment
    """
    print(f"   🎨 FFmpeg enhancement: {Path(image_path).stem}")
    
    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True
    )
    duration = float(result.stdout.strip())
    
    # Apply random FFmpeg effect
    animated_video = output_path.replace(".mp4", "_temp.mp4")
    get_random_effect(image_path, animated_video, duration)
    
    # Combine with audio
    cmd = [
        "ffmpeg", "-y",
        "-i", animated_video, "-i", audio_path,
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    
    # Cleanup temp
    if os.path.exists(animated_video):
        os.remove(animated_video)
    
    return output_path


def enhance_project_hybrid(
    project: dict,
    use_minimax_intro: bool = True
) -> dict:
    """
    Apply hybrid enhancement to a project:
    - If intro: use MiniMax
    - If project segment: use FFmpeg
    
    Args:
        project: Project dict with image/audio paths
        use_minimax_intro: Whether to use MiniMax for intro
        
    Returns:
        Updated project dict
    """
    is_intro = project.get("type") == "intro"
    
    if is_intro and use_minimax_intro:
        # Use MiniMax for intro
        print("   ✨ Using MiniMax for intro")
        result = create_hybrid_intro(
            intro_audio_path=project.get("audio_path"),
            episode_title=project.get("name", "GitHub Projects Roundup"),
            output_path=project.get("output_path", "assets/seg_intro.mp4")
        )
        project["enhanced_video"] = result
    else:
        # Use FFmpeg for projects
        print("   🎨 Using FFmpeg for project segment")
        result = create_project_segment_ffmpeg(
            image_path=project["img_path"],
            audio_path=project["audio_path"],
            output_path=project.get("output_path", f"assets/segment_{project.get('id', 'unknown')}.mp4")
        )
        project["enhanced_video"] = result
    
    return project


# ============================================================
# COST COMPARISON
# ============================================================

def print_cost_comparison():
    """Show cost comparison of hybrid vs full MiniMax"""
    print("\n💰 COST COMPARISON")
    print("="*60)
    print("Full MiniMax (old approach):")
    print("  • 12 projects × 10 clips × $0.20 = ~$24.00 per video")
    print("  • Intro: included in above")
    print("  • Total: ~$24-30 per video")
    print()
    print("Hybrid Approach (new):")
    print("  • MiniMax intro only: $0.25")
    print("  • FFmpeg for 12 projects: $0.00")
    print("  • Total: ~$0.25 per video")
    print()
    print("💵 Savings: $23-30 per video (96% cost reduction)")
    print("="*60)


if __name__ == "__main__":
    print("Hybrid Video Enhancement System")
    print("MiniMax Intro + FFmpeg Projects = Best Value")
    print_cost_comparison()
