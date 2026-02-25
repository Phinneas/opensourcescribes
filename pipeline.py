"""
OpenSourceScribes — Prefect Orchestration Pipeline
Wraps video_automated.py with retry logic, concurrency control,
persistent job state, and a live UI at localhost:4200.

Run once:        python pipeline.py
Run with UI:     prefect server start  (in a separate terminal)
                 python pipeline.py
"""

import asyncio
import json
import math
import os
import random
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

from prefect import flow, task, get_run_logger
from prefect.concurrency.sync import concurrency
from prefect.task_runners import ThreadPoolTaskRunner


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


# ── Tasks: Audio ──────────────────────────────────────────────────────────────

@task(name="generate-audio", retries=2, retry_delay_seconds=10, log_prints=True)
def generate_audio_task(text: str, output_path: str) -> str:
    """Generate TTS audio — Hume.ai with gTTS fallback. Retries twice."""
    logger = get_run_logger()

    if os.path.exists(output_path):
        logger.info(f"✅ Audio already exists: {output_path}")
        return output_path

    import re
    pronunciation_map = {
        "webmcp": "Web M C P",
        "sqlite": "sequel lite",
        "github": "git hub",
        "substack": "sub stack",
        "osmnx": "O S M N X",
    }
    processed = text
    for term, phonetic in pronunciation_map.items():
        processed = re.sub(rf"\b{term}\b", phonetic, processed, flags=re.IGNORECASE)

    # Try Hume.ai
    if CONFIG.get("hume_ai", {}).get("use_hume", False):
        try:
            from hume import HumeClient
            from hume.tts import PostedUtterance

            logger.info(f"🎙️ Hume.ai: {text[:40]}…")
            client = HumeClient(api_key=CONFIG["hume_ai"]["api_key"])
            gen = client.tts.synthesize_file(utterances=[PostedUtterance(text=processed)])
            audio_bytes = b"".join(gen)
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            _trim_silence(output_path)
            logger.info("   ✅ Hume.ai done")
            return output_path
        except Exception as e:
            logger.warning(f"⚠️ Hume.ai failed: {e} — falling back to gTTS")

    # Fallback: gTTS
    logger.info(f"🎙️ gTTS: {processed[:40]}…")
    from gtts import gTTS
    gTTS(text=processed, lang="en").save(output_path)
    _trim_silence(output_path)
    return output_path


def _trim_silence(path: str) -> None:
    """Remove leading silence from an mp3."""
    tmp = path.replace(".mp3", "_trimmed.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-i", path,
         "-af", "silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB",
         tmp],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    os.replace(tmp, path)


# ── Tasks: Graphics ───────────────────────────────────────────────────────────

@task(name="generate-graphic", retries=1, retry_delay_seconds=5, log_prints=True)
def generate_graphic_task(project_name: str, github_url: str, output_path: str) -> str:
    """Render a PIL project graphic. Retries once on failure."""
    logger = get_run_logger()

    if os.path.exists(output_path):
        logger.info(f"✅ Graphic exists: {output_path}")
        return output_path

    logger.info(f"🎨 Rendering graphic: {project_name}")
    from codestream_graphics import CodeStreamGraphics

    graphics = CodeStreamGraphics(output_dir=Path(output_path).parent)
    graphics.create_project_graphic(project_name, github_url, output_path)
    return output_path


# ── Tasks: MiniMax ────────────────────────────────────────────────────────────

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


@task(
    name="minimax-enhancement",
    retries=3,
    retry_delay_seconds=30,
    log_prints=True,
)
def minimax_enhancement_task(project: dict) -> Optional[str]:
    """
    Generate cinematic MiniMax clips for a project.
    Rate-limited to 2 concurrent calls via the 'minimax' concurrency slot.
    Retries 3× with 30s back-off.
    """
    logger = get_run_logger()
    project_id = project["id"]
    audio_path = project.get("audio_path", "")
    final_path = str(Path(OUTPUT_FOLDER) / f"{project_id}_minimax_enhanced.mp4")

    if os.path.exists(final_path):
        logger.info(f"✅ MiniMax clip exists: {final_path}")
        return final_path

    try:
        from minimax_integration import get_minimax_generator
        from github_page_capture import GitHubPageCapture
    except ImportError:
        logger.warning("MiniMax modules not available — skipping enhancement")
        return None

    generator = get_minimax_generator()
    if not generator or not generator.enabled:
        logger.warning("MiniMax disabled in config — skipping")
        return None

    # Concurrency limit: only N simultaneous MiniMax calls
    with concurrency("minimax", occupy=1):
        logger.info(f"🎬 MiniMax: {project['name']}")

        duration = _get_audio_duration(audio_path)
        num_clips = max(1, math.ceil(duration / 6))
        logger.info(f"   ⏱ Audio {duration:.1f}s → {num_clips} clips needed")

        capture = GitHubPageCapture()
        screenshots = capture.take_multi_screenshots(
            project.get("github_url"), project_id, num_clips
        )

        if not screenshots:
            logger.warning("   ⚠️ Screenshot capture failed — using UI demo fallback")
            return generator.generate_ui_demonstration(
                f"A professional demonstration of {project['name']}.", final_path
            )

        motions = random.sample(MOTION_LIBRARY, min(num_clips, len(MOTION_LIBRARY)))
        if num_clips > len(motions):
            motions += random.choices(MOTION_LIBRARY, k=num_clips - len(motions))

        clip_paths = []
        for i, (shot, motion) in enumerate(zip(screenshots, motions)):
            seg_path = str(Path(OUTPUT_FOLDER) / f"{project_id}_enh_seg_{i}.mp4")
            prompt = (
                f"{motion} Modern professional studio lighting. "
                f"Clean interface for {project['name']}."
            )
            logger.info(f"   🪄 Clip {i+1}/{num_clips}: {motion[:45]}…")
            result = generator.generate_image_to_video(shot, prompt, seg_path)
            if result:
                clip_paths.append(result)

        if len(clip_paths) > 1:
            concat_list = Path(OUTPUT_FOLDER) / f"{project_id}_concat.txt"
            concat_list.write_text("\n".join(f"file '{p}'" for p in clip_paths))
            subprocess.run(
                ["ffmpeg", "-y", "-f", "concat", "-safe", "0",
                 "-i", str(concat_list), "-c", "copy", final_path],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            )
            return final_path
        elif clip_paths:
            return clip_paths[0]

    return None


def _get_audio_duration(audio_path: str) -> float:
    if not os.path.exists(audio_path):
        return 6.0
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            capture_output=True, text=True, check=True,
        )
        return float(result.stdout.strip())
    except Exception:
        return 6.0


# ── Tasks: FFmpeg Segments ─────────────────────────────────────────────────────

@task(name="render-segment", retries=1, retry_delay_seconds=5, log_prints=True)
def render_segment_task(project: dict, index: int) -> str:
    """Render a single project video segment."""
    logger = get_run_logger()
    output_path = str(Path(OUTPUT_FOLDER) / f"segment_{index:03d}.mp4")

    # Enhanced (MiniMax) path
    if "enhanced_video" in project:
        logger.info(f"🎬 Merging MiniMax + audio: {project['name']}")
        subprocess.run(
            ["ffmpeg", "-y",
             "-stream_loop", "-1", "-i", project["enhanced_video"],
             "-i", project["audio_path"],
             "-c:v", "libx264", "-preset", "ultrafast",
             "-c:a", "aac", "-b:a", "192k",
             "-pix_fmt", "yuv420p",
             "-map", "0:v:0", "-map", "1:a:0",
             "-shortest", output_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
        )
        return output_path

    # Static image path
    logger.info(f"🎬 Rendering segment: {project['name']}")
    subprocess.run(
        ["ffmpeg", "-y",
         "-loop", "1", "-framerate", "24", "-i", project["img_path"],
         "-i", project["audio_path"],
         "-r", "24",
         "-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
         "-c:a", "aac", "-b:a", "192k",
         "-pix_fmt", "yuv420p",
         "-shortest", output_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    return output_path


@task(name="render-static-segment", retries=1, log_prints=True)
def render_static_segment_task(
    image_path: str, duration: int, output_name: str, audio_path: Optional[str] = None
) -> str:
    """Render an intro/outro/subscribe static segment."""
    output_path = str(Path(OUTPUT_FOLDER) / output_name)

    cmd = ["ffmpeg", "-y", "-loop", "1", "-framerate", "24", "-i", image_path]
    if audio_path:
        cmd += ["-i", audio_path, "-shortest"]
    else:
        cmd += ["-f", "lavfi", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
                "-t", str(duration)]
    cmd += ["-c:v", "libx264", "-preset", "ultrafast", "-tune", "stillimage",
            "-c:a", "aac", "-pix_fmt", "yuv420p", output_path]

    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return output_path


@task(name="concatenate-segments", retries=1, log_prints=True)
def concatenate_task(segment_files: list[str], output_path: str) -> str:
    """Concatenate all segments into the final video."""
    logger = get_run_logger()
    concat_list = Path("concat_list.txt")
    concat_list.write_text("\n".join(f"file '{s}'" for s in segment_files))

    logger.info(f"🔗 Concatenating {len(segment_files)} segments → {output_path}")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list),
         "-c:v", "libx264", "-preset", "ultrafast",
         "-c:a", "aac", "-b:a", "192k", output_path],
        check=True,
    )
    concat_list.unlink(missing_ok=True)

    # Clean up intermediate segments
    for seg in segment_files:
        if os.path.exists(seg):
            os.remove(seg)

    logger.info(f"✅ Final video: {output_path}")
    return output_path


# ── Flow ──────────────────────────────────────────────────────────────────────

@flow(
    name="opensourcescribes-pipeline",
    description="Full video production pipeline: audio → graphics → MiniMax → assemble",
    log_prints=True,
)
def run_pipeline(data_file: str = DATA_FILE):
    logger = get_run_logger()

    # 1. Load projects
    with open(data_file, "r") as f:
        projects: list[dict] = json.load(f)

    for i, p in enumerate(projects):
        if "id" not in p:
            p["id"] = f"p{i+1}"

    logger.info(f"📋 Loaded {len(projects)} projects from {data_file}")

    # 2. Generate all audio in parallel (ThreadPool handles sync tasks)
    logger.info("🎙️ Generating audio for all projects…")
    audio_futures = []
    for p in projects:
        audio_path = str(Path(OUTPUT_FOLDER) / f"{p['id']}_audio.mp3")
        p["audio_path"] = audio_path
        audio_futures.append(generate_audio_task.submit(p["script_text"], audio_path))

    # Shared audio clips
    intro_audio = str(Path(OUTPUT_FOLDER) / "intro_audio.mp3")
    sub_audio = str(Path(OUTPUT_FOLDER) / "subscribe_audio.mp3")
    intro_audio_future = generate_audio_task.submit(
        "Welcome back, glad you could stop by! Today we're diggin into "
        f"{len(projects)} incredible open source projects that you need to know about. "
        "Let's get started!",
        intro_audio,
    )
    sub_audio_future = generate_audio_task.submit(
        "If you're finding these tools useful, please subscribe for more open source discoveries.",
        sub_audio,
    )

    # Wait for all audio
    for f in audio_futures:
        f.result()
    intro_audio_future.result()
    sub_audio_future.result()
    logger.info("✅ All audio ready")

    # 3. MiniMax enhancement (concurrency-limited via 'minimax' slot)
    use_minimax = CONFIG.get("video_settings", {}).get("use_minimax", True)
    if use_minimax:
        logger.info("🎬 Running MiniMax enhancements…")
        minimax_futures = {
            p["id"]: minimax_enhancement_task.submit(p) for p in projects
        }
        for p in projects:
            result = minimax_futures[p["id"]].result()
            if result:
                p["enhanced_video"] = result

    # 4. Generate static graphics for any project without a MiniMax clip
    logger.info("🎨 Generating static graphics for remaining projects…")
    graphic_futures = []
    for p in projects:
        if "enhanced_video" not in p:
            img_path = str(Path(OUTPUT_FOLDER) / f"{p['id']}_screen.png")
            p["img_path"] = img_path
            graphic_futures.append(generate_graphic_task.submit(p["name"], p["github_url"], img_path))
    for f in graphic_futures:
        f.result()

    # 5. Render intro/outro/subscribe cards
    logger.info("🎬 Rendering intro / outro / subscribe segments…")
    from branding import create_intro_card, create_outro_card, create_subscribe_card

    intro_img = create_intro_card(CONFIG, "GitHub Projects Roundup")
    outro_img = create_outro_card(CONFIG)
    sub_img = create_subscribe_card(CONFIG)

    intro_seg = render_static_segment_task(intro_img, 0, "seg_intro.mp4", audio_path=intro_audio)
    outro_seg = render_static_segment_task(outro_img, CONFIG["video_settings"]["outro_duration"], "seg_outro.mp4")
    sub_seg = render_static_segment_task(sub_img, 0, "seg_subscribe.mp4", audio_path=sub_audio)

    # 6. Render project segments
    logger.info("🎬 Rendering project segments…")
    segment_files = [intro_seg]
    midpoint = len(projects) // 2

    for i, p in enumerate(projects):
        seg = render_segment_task(p, i)
        segment_files.append(seg)
        if i == midpoint - 1:
            segment_files.append(sub_seg)

    segment_files.append(outro_seg)

    # 7. Concatenate
    concatenate_task(segment_files, LONGFORM_VIDEO)

    logger.info(f"\n🎉 Pipeline complete → {LONGFORM_VIDEO}")
    return LONGFORM_VIDEO


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_pipeline()
