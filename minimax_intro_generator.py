"""
MiniMax Intro Generator for OpenSourceScribes
Creates visually stunning "Code Stream" themed intros
Uses MiniMax ONLY for the intro (high impact, low cost ~$0.20-0.50 per intro)
"""

import os
import json
import random
from pathlib import Path
from typing import Optional, List

# Import MiniMax
try:
    from minimax_integration import get_minimax_generator
    MINIMAX_AVAILABLE = True
except ImportError:
    MINIMAX_AVAILABLE = False
    print("⚠️  MiniMax not available for intro generation")

# Load config
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


# ============================================================
# CODE STREAM VISUAL THEMES
# ============================================================

CODE_STREAM_THEMES = {
    "terminal_flow": {
        "name": "Terminal Flow",
        "prompts": [
            "Cinematic shot of green code characters flowing like water through a dark terminal interface, matrix-style rain effect, 4K quality, smooth motion",
            "Abstract data stream visualization, bright green code cascading down a dark screen, cinematic lighting, high-tech aesthetic",
            "Close-up of terminal window with scrolling code, depth of field blur, professional studio lighting, modern dark theme IDE"
        ],
        "colors": ["#16c79a", "#0f3460", "#1a1a2e"],
        "mood": "technical, clean, professional"
    },
    
    "code_rain": {
        "name": "Code Rain",
        "prompts": [
            "Matrix-style code rain falling through darkness, bright cyan and green characters, cinematic slow motion, 4K quality",
            "Vertical stream of programming code characters falling like digital rain, glowing text effect, futuristic atmosphere",
            "Abstract visualization of data flowing downward, code symbols and syntax floating in dark space, ethereal lighting"
        ],
        "colors": ["#00ffcc", "#16c79a", "#0d1117"],
        "mood": "mysterious, cutting-edge, dynamic"
    },
    
    "circuit_pulses": {
        "name": " Circuit Pulses",
        "prompts": [
            "Close-up of circuit board with flowing electric pulses, blue and green energy trails, macro photography style, depth of field",
            "Abstract circuit pathways with glowing data nodes, electrical impulses traveling through connections, tech infrastructure aesthetic",
            "Microscopic view of silicon chip with light pulses flowing through pathways, scientific visualization, professional documentary style"
        ],
        "colors": ["#16c79a", "#4a90e2", "#1a1a2e"],
        "mood": "innovative, precise, engineering-focused"
    },
    
    "github_universe": {
        "name": "GitHub Universe",
        "prompts": [
            "3D visualization of GitHub commit graph spreading across space, nodes and connections glowing, cosmic background, cinematic reveal",
            "Network of interconnected repositories visualized as a galaxy, stars representing projects, nebula of code contributions",
            "Abstract representation of open source ecosystem, floating repository cards connected by light beams, space environment"
        ],
        "colors": ["#16c79a", "#ffffff", "#0f3460"],
        "mood": "collaborative, expansive, community"
    },
    
    "developer_workspace": {
        "name": "Developer Workspace",
        "prompts": [
            "Cinematic shot of modern developer desk with multiple monitors showing code, warm accent lighting, depth of field, professional workspace",
            "Close-up of hands typing on mechanical keyboard in dark room, monitor glow illuminating, productivity aesthetic",
            "Artistic shot of laptop with IDE open on screen, coffee cup nearby, moody lighting, developer lifestyle scene"
        ],
        "colors": ["#16c79a", "#2d2d2d", "#f0f0f0"],
        "mood": "relatable, professional, aspirational"
    },
    
    "data_particles": {
        "name": "Data Particles",
        "prompts": [
            "Abstract 3D visualization of data particles flowing in streams, bright points of light, cinematic particle system, cosmic backdrop",
            "Swirling vortex of code characters and data symbols, hypnotic motion, digital tornado effect, mesmerizing visual",
            "Flocking behavior of data points forming shapes and patterns, collective intelligence visualization, organic tech aesthetic"
        ],
        "colors": ["#16c79a", "#00d4aa", "#1a1a2e"],
        "mood": "innovative, artistic, sophisticated"
    }
}


# ============================================================
# ENHANCED INTRO PROMPTS WITH CHANNEL BRANDING
# ============================================================

INTRO_PROMPTS_ENHANCED = [
    # Terminal/Code themes
    "[Cinematic reveal] OpenSourceScribes logo emerges from flowing green terminal code stream, dark background, professional 4K quality, smooth animation, 6 seconds",
    
    # Circuit/Tech themes  
    "[Macro shot] Circuit board pulses with energy as 'OpenSourceScribes' text glows into existence, green electric trails, tech aesthetic, cinematic depth, 6 seconds",
    
    # GitHub/Community themes
    "[3D visualization] GitHub contribution graph expands forming 'OpenSourceScribes' text, stars and connections glowing, space background, epic reveal, 6 seconds",
    
    # Code Rain themes
    "[Slow motion] Code characters rain down forming channel name, matrix-style effect, green and cyan colors, dark void background, 6 seconds",
    
    # Particle effects
    "[Abstract visualization] Data particles swirl and coalesce into OpenSourceScribes branding, flowing motion, digital cosmos environment, cinematic 4K, 6 seconds",
    
    # Developer workspace
    "[Cinematic shot] Modern developer workspace with monitors, 'OpenSourceScribes' fades in with professional motion graphics overlay, warm lighting, 6 seconds"
]


# ============================================================
# DYNAMIC INTRO GENERATION
# ============================================================

def get_code_stream_intro_prompt(episode_title: str = None, theme: str = None) -> dict:
    """
    Generate a Code Stream themed intro prompt
    
    Args:
        episode_title: Optional episode title (e.g., "12 Open Source Projects")
        theme: Specific theme name (e.g., "terminal_flow")
        
    Returns:
        dict with prompt, theme_info, and metadata
    """
    # Select random theme if not specified
    if not theme:
        theme = random.choice(list(CODE_STREAM_THEMES.keys()))
    
    theme_data = CODE_STREAM_THEMES[theme]
    
    # Build enhanced prompt
    base_prompt = random.choice(theme_data["prompts"])
    
    # Add channel branding
    branded_prompt = f"{base_prompt}, OpenSourceScribes channel branding text with smooth fade-in animation"
    
    if episode_title:
        branded_prompt += f", episode title '{episode_title}' appears below channel name"
    
    # Add quality and duration specs
    final_prompt = f"{branded_prompt}, 4K quality, professional color grading, cinematic depth of field, 6 seconds duration"
    
    return {
        "prompt": final_prompt,
        "theme": theme,
        "theme_name": theme_data["name"],
        "colors": theme_data["colors"],
        "mood": theme_data["mood"],
        "duration": 6
    }


def generate_minimax_intro(
    output_path: str = "assets/intro_minimax.mp4",
    episode_title: str = None,
    theme: str = None,
    use_predefined_prompts: bool = True
) -> Optional[str]:
    """
    Generate a MiniMax-enhanced intro video
    
    Args:
        output_path: Where to save the intro video
        episode_title: Episode title text to include
        theme: Specific visual theme to use
        use_predefined_prompts: Use curated prompts vs dynamic generation
        
    Returns:
        Path to generated intro or None if failed
    """
    if not MINIMAX_AVAILABLE:
        print("⚠️  MiniMax not available - falling back to static intro")
        return None
    
    generator = get_minimax_generator()
    if not generator or not generator.enabled:
        print("⚠️  MiniMax disabled - falling back to static intro")
        return None
    
    print("\n" + "="*60)
    print("🎬 GENERATING MINIMAX CODE STREAM INTRO")
    print("="*60)
    
    # Choose prompt strategy
    if use_predefined_prompts:
        # Use curated, tested prompts
        prompt = random.choice(INTRO_PROMPTS_ENHANCED)
        if episode_title:
            prompt = prompt.replace("OpenSourceScribes", f"OpenSourceScribes - {episode_title}")
    else:
        # Use dynamic generation
        prompt_data = get_code_stream_intro_prompt(episode_title, theme)
        prompt = prompt_data["prompt"]
        print(f"   Theme: {prompt_data['theme_name']}")
        print(f"   Mood: {prompt_data['mood']}")
    
    print(f"   Prompt: {prompt[:80]}...")
    print(f"   Cost estimate: ~$0.20-0.30")
    print(f"   Duration: 6 seconds")
    
    # Generate with MiniMax
    result = generator.generate_text_to_video(
        prompt=prompt,
        output_path=output_path,
        duration=6
    )
    
    if result:
        print(f"   ✅ Intro generated: {output_path}")
        print("="*60)
        return result
    else:
        print(f"   ❌ Intro generation failed")
        print("="*60)
        return None


def generate_intro_with_audio(
    intro_video_path: str = "assets/intro_minimax.mp4",
    intro_audio_path: str = "assets/intro_audio.mp3",
    output_path: str = "assets/seg_intro.mp4",
    episode_title: str = None,
    fallback_to_static: bool = True
) -> Optional[str]:
    """
    Generate complete intro with MiniMax video + audio narration
    
    Args:
        intro_video_path: Path for MiniMax video
        intro_audio_path: Path to existing intro audio
        output_path: Final output with audio
        episode_title: Episode title for branding
        fallback_to_static: Fall back to static card if MiniMax fails
        
    Returns:
        Path to final intro segment
    """
    import subprocess
    
    # Try MiniMax generation
    minimax_video = generate_minimax_intro(
        output_path=intro_video_path,
        episode_title=episode_title
    )
    
    if minimax_video and os.path.exists(intro_audio_path):
        # Combine MiniMax video with audio
        print("🎵 Combining MiniMax intro with audio...")
        
        cmd = [
            "ffmpeg", "-y",
            "-i", minimax_video,
            "-i", intro_audio_path,
            "-c:v", "libx264", "-preset", "medium", "-crf", "23",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"✅ Complete intro created: {output_path}")
        return output_path
    
    elif fallback_to_static:
        # Fall back to static intro card
        print("⚠️  Falling back to static intro card...")
        from branding import create_intro_card
        import json
        
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        intro_img = create_intro_card(config, episode_title or "GitHub Projects Roundup")
        
        # Create static segment
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-framerate", "24", "-i", intro_img,
            "-i", intro_audio_path,
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-c:a", "aac", "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-shortest",
            output_path
        ]
        
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        print(f"✅ Static intro created: {output_path}")
        return output_path
    
    return None


# ============================================================
# THEME SHOWCASE GENERATOR
# ============================================================

def generate_theme_showcase(output_folder: str = "assets/intro_themes"):
    """
    Generate sample intros for all themes
    Useful for testing and choosing favorites
    """
    os.makedirs(output_folder, exist_ok=True)
    
    print("\n🎨 GENERATING THEME SHOWCASE")
    print("="*60)
    
    for theme_key, theme_data in CODE_STREAM_THEMES.items():
        print(f"\nGenerating: {theme_data['name']}...")
        
        prompt_data = get_code_stream_intro_prompt(theme=theme_key)
        output_path = os.path.join(output_folder, f"intro_{theme_key}.mp4")
        
        result = generate_minimax_intro(
            output_path=output_path,
            theme=theme_key,
            use_predefined_prompts=False
        )
        
        if result:
            print(f"   ✅ Created: {output_path}")
        else:
            print(f"   ❌ Failed: {theme_data['name']}")
    
    print("\n" + "="*60)
    print("✅ Theme showcase complete!")
    print(f"   Location: {output_folder}/")


# ============================================================
# COST TRACKING
# ============================================================

def estimate_intro_cost() -> dict:
    """
    Estimate MiniMax intro costs
    """
    return {
        "per_intro": "$0.20-$0.30",
        "per_10_videos": "$2.00-$3.00",
        "per_30_videos": "$6.00-$9.00",
        "vs_full_minimax": "Saves ~$22-27 per video",
        "notes": "Using MiniMax only for intro = 95% cost savings vs. full project enhancement"
    }


if __name__ == "__main__":
    print("OpenSourceScribes - MiniMax Code Stream Intro Generator")
    print("="*60)
    
    # Show available themes
    print("\nAvailable Code Stream Themes:")
    for key, theme in CODE_STREAM_THEMES.items():
        print(f"  • {theme['name']}: {theme['mood']}")
    
    # Cost estimate
    print("\n💰 Cost Estimate:")
    costs = estimate_intro_cost()
    for key, value in costs.items():
        print(f"  {key}: {value}")
    
    # Test generation
    print("\n🧪 Test Generation:")
    result = generate_minimax_intro("test_intro.mp4")
    if result:
        print(f"\n✅ Test successful! Intro saved to: {result}")
    else:
        print("\n⚠️  Test generation requires MiniMax API access")
