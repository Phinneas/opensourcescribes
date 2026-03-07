"""
FFmpeg-based video enhancements - FREE alternative to MiniMax
Provides Ken Burns effect, smooth transitions, and professional motion
"""

import os
import subprocess
import random
from pathlib import Path


# Ken Burns motion presets (smooth pan/zoom effects)
KEN_BURNS_PRESETS = [
    {"zoom": "1.0:1.2", "x": "iw/2-iw/2*(in/200)": "x", "y": "ih/2-ih/2*(in/200)"},  # Slow zoom in center
    {"zoom": "1.2:1.0", "x": "iw/2-iw/2*(1-in/200)": "x", "y": "ih/2-ih/2*(1-in/200)"},  # Slow zoom out center
    {"zoom": "1.0:1.15", "x": "0", "y": "ih-(ih*in/200)"},  # Pan down with zoom
    {"zoom": "1.0:1.15", "x": "0", "y": "0+(ih*in/200)"},  # Pan up with zoom
    {"zoom": "1.0:1.1", "x": "iw-(iw*in/200)", "y": "ih/2"},  # Pan left with zoom
    {"zoom": "1.0:1.1", "x": "0+(iw*in/200)", "y": "ih/2"},  # Pan right with zoom
]


def apply_ken_burns(input_image: str, output_video: str, duration: float = 6.0) -> str:
    """
    Apply Ken Burns effect (smooth pan/zoom) to static image
    Uses FFmpeg zoompan filter - completely FREE
    
    Args:
        input_image: Path to input image
        output_video: Path to output video
        duration: Duration in seconds
        
    Returns:
        Path to generated video
    """
    # Random Ken Burns preset
    preset = random.choice(KEN_BURNS_PRESETS)
    
    fps = 24
    frames = int(duration * fps)
    
    # FFmpeg zoompan filter for Ken Burns effect
    # d=duration in frames, z=zoom factor, x/y=pan position
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", input_image,
        "-vf", f"zoompan=z='min(zoom+0.0015,1.2)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_video
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_video


def apply_smooth_zoom(input_image: str, output_video: str, duration: float = 6.0, style: str = "in") -> str:
    """
    Apply smooth zoom effect to static image
    
    Args:
        input_image: Path to input image
        output_video: Path to output video
        duration: Duration in seconds
        style: "in", "out", or "center"
        
    Returns:
        Path to generated video
    """
    fps = 24
    frames = int(duration * fps)
    
    if style == "in":
        zoom_expr = "1.0+0.2*on/200"  # Zoom from 1.0 to 1.2
    elif style == "out":
        zoom_expr = "1.2-0.2*on/200"  # Zoom from 1.2 to 1.0
    else:
        zoom_expr = "1.0+0.1*sin(on/50)"  # Gentle pulse
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", input_image,
        "-vf", f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1920x1080:fps={fps}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_video
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_video


def apply_pan_effect(input_image: str, output_video: str, duration: float = 6.0, direction: str = "left") -> str:
    """
    Apply smooth pan effect across image
    
    Args:
        input_image: Path to input image
        output_video: Path to output video
        duration: Duration in seconds
        direction: "left", "right", "up", or "down"
        
    Returns:
        Path to generated video
    """
    fps = 24
    frames = int(duration * fps)
    
    pan_expressions = {
        "left": f"x='min(0\,iw-iw*on/{frames})':y='ih/2'",
        "right": f"x='max(iw-iw\,iw*on/{frames}-iw)':y='ih/2'",
        "up": f"x='iw/2':y='max(0\,ih*on/{frames}-ih)'",
        "down": f"x='iw/2':y='min(ih\,ih-ih*on/{frames})'"
    }
    
    pan_expr = pan_expressions.get(direction, pan_expressions["left"])
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", input_image,
        "-vf", f"crop=1920:1080:{pan_expr},scale=1920:1080,fps={fps}",
        "-t", str(duration),
        "-c:v", "libx264", "-preset", "medium", "-crf", "23",
        "-pix_fmt", "yuv420p",
        output_video
    ]
    
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_video


def create_animated_segment(image_path: str, audio_path: str, output_path: str) -> str:
    """
    Create animated video segment with Ken Burns effect + audio
    Complete replacement for MiniMax - 100% FREE
    
    Args:
        image_path: Path to project screenshot
        audio_path: Path to audio narration
        output_path: Path to output video segment
        
    Returns:
        Path to generated video segment
    """
    # Get audio duration
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
        capture_output=True, text=True, check=True
    )
    duration = float(result.stdout.strip())
    
    # Create Ken Burns animated video
    animated_video = output_path.replace(".mp4", "_animated.mp4")
    apply_ken_burns(image_path, animated_video, duration)
    
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
    
    # Cleanup temp file
    if os.path.exists(animated_video):
        os.remove(animated_video)
    
    return output_path


# Convenience function for drop-in replacement
def get_enhanced_video(project_id: str, image_path: str, audio_path: str, output_folder: str = "assets") -> str:
    """
    Drop-in replacement for MiniMax - creates enhanced video with Ken Burns effect
    Completely FREE using FFmpeg
    
    Args:
        project_id: Project identifier
        image_path: Path to screenshot
        audio_path: Path to audio
        output_folder: Output directory
        
    Returns:
        Path to enhanced video segment
    """
    output_path = os.path.join(output_folder, f"{project_id}_enhanced.mp4")
    return create_animated_segment(image_path, audio_path, output_path)


if __name__ == "__main__":
    # Test with a sample image
    test_image = "test_graphic.png"
    test_output = "test_ken_burns.mp4"
    
    if os.path.exists(test_image):
        print("Testing Ken Burns effect...")
        result = apply_ken_burns(test_image, test_output, duration=6.0)
        print(f"✅ Created: {result}")
    else:
        print(f"Test image {test_image} not found")
