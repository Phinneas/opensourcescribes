"""
Prefect Wrapper for SOLID Architecture
Orchestrates SOLID components with Prefect's retry logic, monitoring UI,
and concurrency control. This is the modern pipeline using composition root.

Run with: ./run_with_prefect.sh solid
Or: python core/pipeline_solid.py
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Configure Prefect
os.environ.setdefault('PREFECT_API_URL', 'http://127.0.0.1:4200/api')

from prefect import flow, task, get_run_logger
from prefect.task_runners import ThreadPoolTaskRunner

# Import SOLID architecture
from interfaces.dependency_injection import CompositionRoot
from interfaces.interfaces import IVideoPipeline, IProjectProvider, IAudioGenerator, IGraphicsRenderer, IVideoRenderer


# ═══════════════════════════════════════════════════════════════════════
# Prefect Tasks - Wrapping SOLID Components
# ═══════════════════════════════════════════════════════════════════════

@task(name="load-projects", retries=2, retry_delay_seconds=5, log_prints=True)
def load_projects_task(project_provider: IProjectProvider) -> List[Dict]:
    """
    Load projects using SOLID ProjectProvider.
    
    Args:
        project_provider: Injected project provider from composition root
        
    Returns:
        List of project dictionaries
    """
    logger = get_run_logger()
    logger.info("Loading projects...")
    
    projects = project_provider.load_projects()
    
    if not projects:
        raise Exception("No projects loaded - check posts_data.json")
    
    logger.info(f"✅ Loaded {len(projects)} projects")
    return projects


@task(name="auto-select-projects", retries=1, log_prints=True)
def auto_select_task(project_provider: IProjectProvider) -> tuple:
    """
    Auto-select projects for Shorts and Deep Dives.
    
    Args:
        project_provider: Injected project provider
        
    Returns:
        Tuple of (shorts_selection, deep_dive_selection)
    """
    logger = get_run_logger()
    logger.info("Auto-selecting projects...")
    
    shorts, deep_dives = project_provider.auto_select_shorts_and_deep_dives()
    
    logger.info(f"✅ Selected {len(shorts)} for shorts, {len(deep_dives)} for deep dives")
    return shorts, deep_dives


@task(name="generate-audio", retries=3, retry_delay_seconds=10, log_prints=True)
def generate_audio_task(
    audio_generator: IAudioGenerator,
    project: Dict,
    output_folder: str
) -> str:
    """
    Generate audio for a single project using SOLID AudioGenerator.
    
    Args:
        audio_generator: Injected audio generator
        project: Project dictionary
        output_folder: Output directory
        
    Returns:
        Path to generated audio file
    """
    logger = get_run_logger()
    project_id = project.get('id', 'unknown')
    audio_path = os.path.join(output_folder, f"{project_id}_audio.mp3")
    
    # Check cache
    if os.path.exists(audio_path):
        file_size = os.path.getsize(audio_path)
        if file_size > 1000:  # Valid audio file
            logger.info(f"✅ Using cached audio: {audio_path} ({file_size//1024}KB)")
            return audio_path
        else:
            logger.warning(f"⚠️  Invalid cached audio, regenerating...")
            os.remove(audio_path)
    
    # Generate audio
    logger.info(f"🎙️ Generating audio for {project.get('name', project_id)}")
    
    try:
        result = audio_generator.generate_audio(
            project.get('script_text', ''),
            audio_path
        )
        
        logger.info(f"✅ Audio generated: {audio_path}")
        return audio_path
        
    except Exception as e:
        logger.error(f"❌ Audio generation failed: {e}")
        raise


@task(name="capture-screenshot", retries=2, retry_delay_seconds=5, log_prints=True)
def capture_screenshot_task(
    graphics_renderer: IGraphicsRenderer,
    project: Dict
) -> Optional[str]:
    """
    Capture GitHub screenshot using SOLID GraphicsRenderer.
    
    Args:
        graphics_renderer: Injected graphics renderer
        project: Project dictionary with github_url
        
    Returns:
        Path to screenshot or None if failed
    """
    logger = get_run_logger()
    github_url = project.get('github_url', '')
    project_name = project.get('name', 'Unknown')
    
    if not github_url:
        logger.warning(f"⚠️  No GitHub URL for {project_name}")
        return None
    
    logger.info(f"📸 Capturing screenshot for {project_name}")
    
    try:
        screenshot_path = graphics_renderer.capture_screenshot(github_url)
        
        if screenshot_path:
            logger.info(f"✅ Screenshot captured: {screenshot_path}")
            return str(screenshot_path)
        else:
            logger.warning(f"⚠️  Screenshot capture failed, will use fallback")
            return None
            
    except Exception as e:
        logger.error(f"❌ Screenshot capture error: {e}")
        return None


@task(name="render-segment", retries=2, retry_delay_seconds=10, log_prints=True)
def render_segment_task(
    video_renderer: IVideoRenderer,
    project: Dict,
    index: int,
    audio_path: str
) -> str:
    """
    Render video segment using SOLID VideoRenderer.
    
    Args:
        video_renderer: Injected video renderer
        project: Project dictionary
        index: Segment index
        audio_path: Path to audio file
        
    Returns:
        Path to rendered segment
    """
    logger = get_run_logger()
    project_name = project.get('name', 'Unknown')
    
    logger.info(f"🎬 Rendering segment {index + 1}: {project_name}")
    
    try:
        segment_path = video_renderer.render_segment(project, index, audio_path)
        logger.info(f"✅ Segment rendered: {segment_path}")
        return str(segment_path)
        
    except Exception as e:
        logger.error(f"❌ Segment rendering failed: {e}")
        raise


@task(name="render-intro", retries=2, log_prints=True)
def render_intro_task(
    video_renderer: IVideoRenderer,
    episode_title: str,
    audio_path: str,
    output_folder: str
) -> str:
    """
    Render intro segment using SOLID VideoRenderer.
    
    Args:
        video_renderer: Injected video renderer
        episode_title: Episode title text
        audio_path: Path to intro audio
        output_folder: Output directory
        
    Returns:
        Path to rendered intro
    """
    logger = get_run_logger()
    logger.info(f"🎬 Rendering intro: {episode_title}")
    
    intro_path = Path(output_folder) / "seg_intro.mp4"
    
    try:
        result = video_renderer.render_intro(episode_title, audio_path, intro_path)
        logger.info(f"✅ Intro rendered: {result}")
        return str(result)
        
    except Exception as e:
        logger.error(f"❌ Intro rendering failed: {e}")
        raise


@task(name="assemble-video", retries=2, log_prints=True)
def assemble_video_task(segment_files: List[str], output_path: str) -> str:
    """
    Note: Video assembly is handled by VideoPipeline internally.
    This task is a placeholder for future enhancements.
    
    Args:
        segment_files: List of segment paths
        output_path: Final video output path
        
    Returns:
        Path to final video
    """
    logger = get_run_logger()
    logger.info(f"🔗 Assembly handled by VideoPipeline")
    logger.info(f"✅ Final video: {output_path}")
    return output_path


@task(name="mark-published", retries=2, log_prints=True)
def mark_published_task(
    project_provider: IProjectProvider,
    projects: List[Dict]
) -> None:
    """
    Mark projects as published using SOLID ProjectProvider.
    
    Args:
        project_provider: Injected project provider
        projects: List of projects to mark
    """
    logger = get_run_logger()
    logger.info("Marking projects as published...")
    
    try:
        project_provider.mark_published(projects)
        logger.info(f"✅ Marked {len(projects)} projects as published")
    except Exception as e:
        logger.error(f"⚠️  Failed to mark published: {e}")


# ═══════════════════════════════════════════════════════════════════════
# Main Prefect Flow - Orchestrates SOLID Pipeline
# ═══════════════════════════════════════════════════════════════════════

@flow(
    name="video-generation-solid",
    task_runner=ThreadPoolTaskRunner(max_workers=4),
    log_prints=True
)
async def video_generation_flow(config_path: str = "config.json") -> str:
    """
    Main Prefect flow that orchestrates the SOLID video generation pipeline.
    
    This flow uses the Composition Root to create all SOLID components
    and then executes them with Prefect's orchestration capabilities:
    - Automatic retries on failures
    - Concurrency control (4 parallel workers)
    - Monitoring UI at localhost:4200
    - Persistent job state
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Path to final generated video
    """
    logger = get_run_logger()
    
    logger.info("="*60)
    logger.info("🎬 SOLID Video Generation Pipeline with Prefect")
    logger.info("="*60)
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create SOLID pipeline through composition root
    logger.info("🏗️  Creating SOLID components via Composition Root...")
    pipeline = CompositionRoot.create_video_pipeline(config)
    
    # Setup directories
    output_folder = "assets"
    delivery_folder = os.path.join("deliveries", datetime.now().strftime("%m-%d"))
    os.makedirs(output_folder, exist_ok=True)
    os.makedirs(delivery_folder, exist_ok=True)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 1: Load Projects
    # ═══════════════════════════════════════════════════════════════
    projects = load_projects_task(pipeline.project_provider)
    auto_select_task(pipeline.project_provider)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 2: Generate Audio (Parallel)
    # ═══════════════════════════════════════════════════════════════
    logger.info("🎙️ Generating audio for all projects...")
    
    audio_paths = []
    for project in projects:
        audio_path = generate_audio_task.submit(
            pipeline.audio_generator,
            project,
            output_folder
        )
        audio_paths.append(audio_path)
    
    # Wait for all audio generation to complete
    audio_results = [ap.result() for ap in audio_paths]
    
    # Update projects with audio paths
    for i, project in enumerate(projects):
        project['audio_path'] = audio_results[i]
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 3: Capture Screenshots (Parallel)
    # ═══════════════════════════════════════════════════════════════
    logger.info("📸 Capturing screenshots...")
    
    for project in projects:
        screenshot_path = capture_screenshot_task.submit(
            pipeline.graphics_renderer,
            project
        )
        project['screenshot_path'] = screenshot_path.result() or ''
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 4: Render Video Segments (Parallel)
    # ═══════════════════════════════════════════════════════════════
    logger.info("🎬 Rendering video segments...")
    
    segment_futures = []
    
    # Render intro
    episode_title = generate_episode_title(projects)
    intro_audio_path = os.path.join(output_folder, "intro_audio.mp3")
    pipeline.audio_generator.generate_audio(
        generate_intro_script(projects),
        intro_audio_path
    )
    
    intro_future = render_intro_task.submit(
        pipeline.video_renderer,
        episode_title,
        intro_audio_path,
        output_folder
    )
    segment_futures.append(intro_future)
    
    # Render project segments
    for i, project in enumerate(projects):
        segment_future = render_segment_task.submit(
            pipeline.video_renderer,
            project,
            i,
            project['audio_path']
        )
        segment_futures.append(segment_future)
    
    # Wait for all segments
    segment_files = [sf.result() for sf in segment_futures]
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 5: Assemble Final Video
    # ═══════════════════════════════════════════════════════════════
    final_video = os.path.join(delivery_folder, "longform_github_roundup.mp4")
    
    # Use VideoAssembler to concatenate
    pipeline.video_assembler.concatenate_segments(segment_files, final_video)
    
    # ═══════════════════════════════════════════════════════════════
    # STEP 6: Mark Published
    # ═══════════════════════════════════════════════════════════════
    mark_published_task(pipeline.project_provider, projects)
    
    logger.info("="*60)
    logger.info("✅ PIPELINE COMPLETE")
    logger.info("="*60)
    logger.info(f"Final video: {final_video}")
    
    return final_video


# ═══════════════════════════════════════════════════════════════════════
# Helper Functions
# ═══════════════════════════════════════════════════════════════════════

def generate_episode_title(projects: List[Dict]) -> str:
    """Generate episode title from projects."""
    from datetime import datetime
    
    date_str = datetime.now().strftime("%B %d")
    names = [p.get('name', '') for p in projects[:2]]
    
    if len(projects) <= 2:
        featured = " & ".join(names)
    else:
        featured = f"{names[0]}, {names[1]} & {len(projects) - 2} More"
    
    return f"{date_str} — {featured}"


def generate_intro_script(projects: List[Dict]) -> str:
    """Generate intro narration script."""
    names = [p.get('name', '') for p in projects]
    n = len(names)
    
    if n == 1:
        name_list = names[0]
    elif n <= 3:
        name_list = ", ".join(names[:-1]) + f" and {names[-1]}"
    else:
        name_list = f"{names[0]}, {names[1]}, {names[2]}, and {n - 3} more"
    
    return (
        f"Welcome to OpenSourceScribes. "
        f"This week: {n} open source projects. "
        f"Including {name_list}. "
        f"Let's get into it."
    )


# ═══════════════════════════════════════════════════════════════════════
# Entry Point
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Run the flow
    final_video = asyncio.run(video_generation_flow())
    print(f"\n✅ Final video: {final_video}")
