"""
OpenSourceScribes — Master Orchestration Pipeline
A complete Prefect workflow that manages:
1. Longform Video (MiniMax animations + Audio + Graphics)
2. YouTube Shorts (Precise vertical crops)
3. Deep Dive Videos (Focused 2-3 min videos for top projects)
4. Content Suite (Medium, Reddit, Substack, YouTube Description)

Usage:
  # Start dedicated server first:
  prefect server start
  
  # Then run orchestration:
  export PREFECT_API_URL="http://127.0.0.1:4200/api"
  python orchestration.py
  
  # Or use the provided script:
  ./run_with_prefect.sh
"""

import asyncio
import json
import math
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List

# Configure for dedicated Prefect server
os.environ.setdefault('PREFECT_API_URL', 'http://127.0.0.1:4200/api')

from prefect import flow, task, get_run_logger
from prefect.concurrency.sync import concurrency

# ── Import existing logic ──
# We import the main functions to wrap them as tasks
from generate_description import generate_description
from generate_medium_post import main as generate_medium_post
from generate_reddit_post import main as generate_reddit_post
from generate_newsletter import main as generate_newsletter
from reformat_newsletter import main as reformat_newsletter
from shorts_generator import ShortsFromVideoExtractor
from single_project_video import create_single_project_video

# ── Config ────────────────────────────────────────────────────────────────────

with open("config.json", "r") as f:
    CONFIG = json.load(f)

DATA_FILE = "posts_data.json"
OUTPUT_FOLDER = "assets"
current_date_mmdd = datetime.now().strftime("%m-%d")
DELIVERY_FOLDER = os.path.join("deliveries", current_date_mmdd)
SHORTS_FOLDER = os.path.join(DELIVERY_FOLDER, "shorts")
DEEP_DIVES_FOLDER = os.path.join(DELIVERY_FOLDER, "deep_dives")
LONGFORM_VIDEO = os.path.join(DELIVERY_FOLDER, "longform_github_roundup.mp4")

for d in [OUTPUT_FOLDER, DELIVERY_FOLDER, SHORTS_FOLDER, DEEP_DIVES_FOLDER]:
    os.makedirs(d, exist_ok=True)

MOTION_LIBRARY = [
    "Smooth cinematic camera scroll down revealing features.",
    "Slow pan across the interface showing technical details.",
    "Tilt up shot revealing the bottom sections of the page.",
    "Cinematic zoom-in on the main repository header.",
    "Dolly sweep from left to right across the code files.",
    "Perspective tilt showing the page in a 3D workspace.",
    "Slow rotation around the center of the UI.",
    "Fast tracking shot down the sidebar and into the content.",
    "Glide over the interface with a soft bokeh background effect.",
    "Rack focus from the foreground text to the background code.",
    "Dynamic crane shot descending from the top of the repository.",
    "Slow push-in on a specific set of features.",
    "Arresting side-scrolling shot showing the project evolution.",
    "Floating camera effect mimicking a handheld walkthrough.",
    "Sharp cinematic pull-back revealing the full page layout.",
]

# ── Video Tasks (Legacy from pipeline.py) ──────────────────────────────────────

@task(name="generate-audio", retries=2, retry_delay_seconds=10)
def generate_audio_task(text: str, output_path: str) -> str:
    """Generate audio using EnhancedVoiceGenerator with full fallback chain"""
    logger = get_run_logger()
    if os.path.exists(output_path):
        return output_path

    try:
        from enhanced_audio_generator import EnhancedVoiceGenerator
        generator = EnhancedVoiceGenerator()
        
        # Apply text preprocessing for better pronunciation
        import re
        pronunciation_map = {"webmcp": "Web M C P", "sqlite": "sequel lite", "github": "git hub", "osmnx": "O S M N X"}
        processed = text
        for term, phonetic in pronunciation_map.items():
            processed = re.sub(rf"\b{term}\b", phonetic, processed, flags=re.IGNORECASE)
        
        success = generator.generate_audio(processed, output_path)
        if success:
            return output_path
        else:
            logger.error("All voice services failed - this should never happen with gTTS fallback")
            raise RuntimeError("Audio generation failed completely")
            
    except Exception as e:
        logger.error(f"Audio generation task failed: {e}")
        raise

def _trim_silence(path: str):
    tmp = path.replace(".mp3", "_trimmed.mp3")
    subprocess.run(["ffmpeg", "-y", "-i", path, "-af", "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB", tmp], 
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    os.replace(tmp, path)

@task(name="generate-graphic")
def generate_graphic_task(project_name: str, github_url: str, output_path: str):
    if os.path.exists(output_path): return output_path
    from codestream_graphics import CodeStreamGraphics
    graphics = CodeStreamGraphics(output_dir=Path(output_path).parent)
    graphics.create_project_graphic(project_name, github_url, output_path)
    return output_path

@task(name="minimax-enhancement", retries=3, retry_delay_seconds=30)
def minimax_enhancement_task(project: dict) -> Optional[str]:
    logger = get_run_logger()
    final_path = str(Path(OUTPUT_FOLDER) / f"{project['id']}_minimax_enhanced.mp4")
    if os.path.exists(final_path): return final_path

    try:
        from minimax_integration import get_minimax_generator
        from github_page_capture import GitHubPageCapture
        generator = get_minimax_generator()
        if not generator or not generator.enabled: return None
    except ImportError:
        logger.warning("MiniMax modules not available — skipping enhancement")
        return None

    with concurrency("minimax", occupy=1):
        duration = _get_audio_duration(project["audio_path"])
        num_clips = max(1, math.ceil(duration / 6))
        capture = GitHubPageCapture()
        screenshots = capture.take_multi_screenshots(project.get("github_url"), project["id"], num_clips)
        
        if not screenshots:
            return generator.generate_ui_demonstration(f"A professional demonstration of {project['name']}.", final_path)

        motions = random.sample(MOTION_LIBRARY, min(num_clips, len(MOTION_LIBRARY)))
        if num_clips > len(motions): motions += random.choices(MOTION_LIBRARY, k=num_clips - len(motions))
        
        clip_paths = []
        for i, (shot, motion) in enumerate(zip(screenshots, motions)):
            seg_path = str(Path(OUTPUT_FOLDER) / f"{project['id']}_enh_seg_{i}.mp4")
            prompt = f"{motion} Modern professional studio lighting. Clean interface for {project['name']}."
            res = generator.generate_image_to_video(shot, prompt, seg_path)
            if res: clip_paths.append(res)

        if len(clip_paths) >= 1:
            if len(clip_paths) == 1:
                # Single clip — copy directly to final_path so cache guard works on retries
                import shutil
                shutil.copy2(clip_paths[0], final_path)
            else:
                # Multiple clips — concat with absolute paths to avoid ffmpeg resolution issues
                concat_list = Path(OUTPUT_FOLDER) / f"{project['id']}_concat.txt"
                abs_clip_paths = [str(Path(p).resolve()) for p in clip_paths]
                concat_list.write_text("\n".join(f"file '{p}'" for p in abs_clip_paths))
                result = subprocess.run(
                    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", final_path],
                    stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT
                )
                if result.returncode != 0:
                    logger.warning(f"⚠️  ffmpeg concat failed for {project['id']} — falling back to first clip")
                    shutil.copy2(clip_paths[0], final_path)
            return final_path
    return None

def _get_audio_duration(path: str) -> float:
    try:
        res = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path], 
                             capture_output=True, text=True, check=True)
        return float(res.stdout.strip())
    except: return 6.0

@task(name="render-segment")
def render_segment_task(project: dict, index: int) -> str:
    output_path = str(Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4")
    
    audio_dur = _get_audio_duration(project["audio_path"])
    
    if "enhanced_video" in project:
        subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", project["enhanced_video"], "-i", project["audio_path"], 
                        "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "192k", "-pix_fmt", "yuv420p", 
                        "-map", "0:v:0", "-map", "1:a:0", "-t", str(audio_dur), output_path], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    else:
        subprocess.run(["ffmpeg", "-y", "-loop", "1", "-framerate", "24", "-i", project["img_path"], "-i", project["audio_path"], 
                        "-r", "24", "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-c:a", "aac", 
                        "-b:a", "192k", "-pix_fmt", "yuv420p", "-t", str(audio_dur), output_path], 
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_path

@task(name="render-static-segment")
def render_static_segment_task(image_path: str, duration: int, output_name: str, audio_path: Optional[str] = None) -> str:
    output_path = str(Path(OUTPUT_FOLDER) / output_name)
    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "24", "-i", image_path]
    if audio_path: cmd += ["-i", audio_path, "-shortest"]
    else: cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100", "-t", str(duration)]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage", "-c:a", "aac", "-pix_fmt", "yuv420p", output_path]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_path

@task(name="concatenate-segments")
def concatenate_task(segment_files: List[str], output_path: str) -> str:
    concat_list = Path("concat_list.txt")
    concat_list.write_text("\n".join(f"file '{s}'" for s in segment_files))
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c:v", "libx264", 
                    "-preset", "ultrafast", "-c:a", "aac", "-b:a", "192k", output_path], check=True)
    concat_list.unlink(missing_ok=True)
    return output_path

@task(name="render-remotion-video", log_prints=True)
def render_remotion_video_task(composition_id: str, props: dict, output_path: str) -> str:
    """Invokes the local Remotion project to render a video."""
    logger = get_run_logger()
    remotion_dir = str(Path(__file__).parent / "remotion_video")
    output_path = str(Path(output_path).resolve())
    
    logger.info(f"🎥 Rendering Remotion composition '{composition_id}' to: {output_path}")
    
    # Save props to a temporary JSON file to pass to Remotion
    props_fp = str(Path(remotion_dir) / f"props_{composition_id}.json")
    with open(props_fp, "w") as f:
        json.dump(props, f)
        
    try:
        # Run Remotion CLI inside remotion_video/.
        # --public-dir points to the project root so Remotion's HTTP server
        # serves assets/ through http://localhost:PORT/assets/... 
        # This avoids Chromium's file:// protocol security block on staticFile().
        project_root = str(Path(__file__).parent)
        cmd = [
            "npx", "remotion", "render", composition_id, output_path,
            "--props", f"props_{composition_id}.json",
            "--public-dir", str(Path(project_root) / "assets"),
            "--log", "error",
        ]
        subprocess.run(cmd, cwd=remotion_dir, check=True)
        logger.info(f"✅ Remotion render complete: {output_path}")
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Remotion render failed")
        raise
    finally:
        pass # dont delete so we can debug

# ── New Content & Derivative Tasks ──────────────────────────────────────────

@task(name="generate-content-suite", log_prints=True)
def content_suite_task():
    logger = get_run_logger()
    logger.info("📝 Generating content suite (YouTube, Medium, Reddit, Substack)...")
    
    try:
        logger.info("   🔹 YouTube Description")
        generate_description()
        
        logger.info("   🔹 Medium Post")
        generate_medium_post()
        
        logger.info("   🔹 Reddit Post")
        generate_reddit_post()
        
        logger.info("   🔹 Substack Newsletter")
        generate_newsletter()
        
        logger.info("   🪄 Reformatting Newsletter for Substack...")
        reformat_newsletter()
        
        return True
    except Exception as e:
        logger.error(f"❌ Failed to generate content suite: {e}")
        return False

@task(name="generate-shorts", log_prints=True)
def generate_shorts_task(longform_video_path: str):
    logger = get_run_logger()
    logger.info(f"📱 Extracting YouTube Shorts from {longform_video_path}...")
    try:
        extractor = ShortsFromVideoExtractor()
        # Move to delivery folder shorts
        extractor.shorts_dir = Path(SHORTS_FOLDER)
        extractor.generate_shorts_from_video(longform_video_path)
        return True
    except Exception as e:
        logger.error(f"❌ Failed to generate shorts: {e}")
        return False

@task(name="generate-deep-dives", log_prints=True)
def deep_dives_task(projects: List[dict]):
    logger = get_run_logger()
    # Select 3 random deep dives if not already selected
    selection = random.sample(projects, min(3, len(projects)))
    logger.info(f"🔍 Generating {len(selection)} Deep Dive videos...")
    
    results = []
    for p in selection:
        output_path = os.path.join(DEEP_DIVES_FOLDER, f"{p['id']}_deep_dive.mp4")
        logger.info(f"   🎥 Deep Dive: {p['name']}")
        try:
            # create_single_project_video is async
            success = asyncio.run(create_single_project_video(p['id'], output_path))
            results.append(success)
        except Exception as e:
            logger.error(f"   ❌ Failed deep dive for {p['name']}: {e}")
            results.append(False)
    return results

# ── Master Flow ────────────────────────────────────────────────────────────────

@flow(name="OpenSourceScribes-Master-Production", log_prints=True)
def production_pipeline():
    logger = get_run_logger()
    logger.info("🚀 STARTING FULL PRODUCTION PIPELINE")

    # 1. Load data
    with open(DATA_FILE, "r") as f:
        projects = json.load(f)
    for i, p in enumerate(projects):
        if "id" not in p: p["id"] = f"p{i+1}"

    # 2. Phase 1: Core Assets (Parallel)
    logger.info("⚡ PHASE 1: CORE ASSETS")
    audio_futures = []
    for p in projects:
        audio_path = str(Path(OUTPUT_FOLDER) / f"{p['id']}_audio.mp3")
        p["audio_path"] = audio_path
        audio_futures.append(generate_audio_task.submit(p["script_text"], audio_path))

    intro_audio = str(Path(OUTPUT_FOLDER) / "intro_audio.mp3")
    sub_audio = str(Path(OUTPUT_FOLDER) / "subscribe_audio.mp3")
    audio_futures.append(generate_audio_task.submit("Welcome back! Today we have a fresh lineup of open source projects.", intro_audio))
    audio_futures.append(generate_audio_task.submit("Subscribe for more open source discoveries.", sub_audio))

    # Wait for audio
    for f in audio_futures: f.result()

    # 3. Phase 2: Visuals (MiniMax & Graphics)
    logger.info("⚡ PHASE 2: VISUAL ENHANCEMENT")
    minimax_futures = {p["id"]: minimax_enhancement_task.submit(p) for p in projects}
    for p in projects:
        res = minimax_futures[p["id"]].result()
        if res: p["enhanced_video"] = res
        else:
            img_path = str(Path(OUTPUT_FOLDER) / f"{p['id']}_screen.png")
            p["img_path"] = img_path
            generate_graphic_task(p["name"], p["github_url"], img_path)

    # 4. Phase 3: Assembly (Longform)
    logger.info("⚡ PHASE 3: VIDEO ASSEMBLY")
    from branding import create_intro_card, create_outro_card, create_subscribe_card
    intro_img = create_intro_card(CONFIG, "GitHub Projects Roundup")
    outro_img = create_outro_card(CONFIG)
    sub_img = create_subscribe_card(CONFIG)

    intro_seg = render_static_segment_task(intro_img, 0, "seg_intro.mp4", audio_path=intro_audio)
    outro_seg = render_static_segment_task(outro_img, 5, "seg_outro.mp4")
    sub_seg = render_static_segment_task(sub_img, 0, "seg_subscribe.mp4", audio_path=sub_audio)

    segment_files = [intro_seg]
    props = {"clips": []}
    
    # helper for precise lengths
    def add_clip(src, dur, ctype, name="", url="", img="", stats=None):
        props["clips"].append({
            "src": f"{os.path.basename(src)}",
            "durationInSeconds": dur,
            "type": ctype,
            "name": name,
            "url": url,
            "img": f"{os.path.basename(img)}" if img else "",
            "stats": stats or {}
        })

    add_clip(intro_seg, _get_audio_duration(intro_audio), "intro")

    mid = len(projects) // 2
    
    # Load stats cache for SegmentScene
    stats_cache = {}
    stats_fp = Path(__file__).parent / "github_stats_cache.json"
    if stats_fp.exists():
        with open(stats_fp) as sf:
            stats_cache = json.load(sf)

    for i, p in enumerate(projects):
        seg = render_segment_task(p, i)
        segment_files.append(seg)
        
        # Get repo metadata from github_url
        repo_id = p.get("github_url", "").replace("https://github.com/", "").strip("/")
        repo_stats = stats_cache.get(repo_id, {}).get("data", {})
        
        add_clip(seg, _get_audio_duration(p["audio_path"]), "project", p.get("name", ""), p.get("github_url", ""), p.get("img_path", ""), repo_stats)
        
        if i == mid - 1:
            segment_files.append(sub_seg)
            add_clip(sub_seg, _get_audio_duration(sub_audio), "subscribe")
            
    segment_files.append(outro_seg)
    add_clip(outro_seg, 5.0, "outro")

    # longform_video = concatenate_task(segment_files, LONGFORM_VIDEO)
    longform_video = render_remotion_video_task("Main", props, LONGFORM_VIDEO)

    # 5. Phase 4: Derivative Content (Parallel)
    logger.info("⚡ PHASE 4: CONTENT SUITE & DERIVATIVES")
    
    # These can run in parallel now that the video is ready
    suite_future = content_suite_task.submit()
    shorts_future = generate_shorts_task.submit(longform_video)
    deep_dives_future = deep_dives_task.submit(projects)

    # Wait for final results
    suite_future.result()
    shorts_future.result()
    deep_dives_future.result()

    logger.info(f"\n✨ PRODUCTION COMPLETE ✨\n📍 Assets located in: {DELIVERY_FOLDER}")
    return True

if __name__ == "__main__":
    production_pipeline()
