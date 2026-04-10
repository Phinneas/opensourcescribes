"""
Video Pipeline - Concrete implementation of IVideoPipeline
Orchestrates the entire video generation process.
"""
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict

from interfaces.interfaces import (
    IVideoPipeline, IProjectProvider, IAudioGenerator,
    IGraphicsRenderer, IVideoRenderer, IVideoAssembler, IDatabaseClient
)


class VideoPipeline(IVideoPipeline):
    """
    Main orchestrator for video generation pipeline.
    
    SOLID Compliance:
    ✅ SRP: Only orchestrates the pipeline flow
    ✅ DIP: Depends on all component interfaces (not implementations)
    ✅ OCP: Can add new pipeline steps without modification
    ✅ LSP: Substitutable with any IVideoPipeline
    ✅ ISP: Implements only IVideoPipeline methods
    
    All dependencies are explicit and injected through constructor.
    No component is created or looked up - everything is provided.
    """
    
    def __init__(
        self,
        project_provider: IProjectProvider,
        audio_generator: IAudioGenerator,
        graphics_renderer: IGraphicsRenderer,
        video_renderer: IVideoRenderer,
        video_assembler: IVideoAssembler,
        database_client: Optional[IDatabaseClient] = None,
        output_folder: str = "assets",
        delivery_folder: str = "deliveries"
    ):
        """
        Constructor injection - ALL dependencies explicit.
        
        Args:
            project_provider: Provides project data
            audio_generator: Generates audio from text
            graphics_renderer: Renders graphics and screenshots
            video_renderer: Renders video segments
            video_assembler: Assembles final videos
            database_client: Optional database for persistence
            output_folder: Directory for temporary files
            delivery_folder: Directory for final videos
        """
        # Core components - ALL explicitly provided
        self.project_provider = project_provider
        self.audio_generator = audio_generator
        self.graphics_renderer = graphics_renderer
        self.video_renderer = video_renderer
        self.video_assembler = video_assembler
        self.database_client = database_client
        
        # Configuration
        self.output_folder = Path(output_folder)
        self.delivery_folder = Path(delivery_folder)
        
        # Ensure directories exist
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.delivery_folder.mkdir(parents=True, exist_ok=True)
        
        # State
        self.projects = []
        self.segment_files = []
    
    async def run(self) -> str:
        """
        Execute complete video generation pipeline.
        
        Returns:
            Path to final generated video
        """
        print("\n🎬 Video Generation Pipeline - SOLID Architecture")
        print("="*60)
        
        # Step 1: Load projects
        self.projects = self.project_provider.load_projects()
        if not self.projects:
            raise Exception("No projects loaded")
        
        # Step 2: Auto-select shorts and deep dives
        shorts, deep_dives = self.project_provider.auto_select_shorts_and_deep_dives()
        
        # Step 3: Prepare assets
        self.prepare_assets()
        
        # Step 4: Render video
        final_video = self.render_video()
        
        # Step 5: Mark published
        self.project_provider.mark_published(self.projects)
        
        print("\n" + "="*60)
        print("✅ PIPELINE COMPLETE")
        print("="*60)
        
        return final_video
    
    def prepare_assets(self) -> None:
        """
        Prepare all assets (audio, graphics, screenshots).
        """
        print("\n📦 Preparing Assets...")
        
        # Generate audio for each project
        print("\n🎙️ Generating audio...")
        for project in self.projects:
            audio_path = self.output_folder / f"{project.get('id', 'unknown')}_audio.mp3"
            project['audio_path'] = str(audio_path)
            
            # Generate audio
            self.audio_generator.generate_audio(
                project.get('script_text', ''),
                str(audio_path)
            )
        
        # Capture screenshots for each project
        print("\n📸 Capturing screenshots...")
        for project in self.projects:
            github_url = project.get('github_url', '')
            
            if github_url:
                screenshot = self.graphics_renderer.capture_screenshot(github_url)
                project['screenshot_path'] = str(screenshot) if screenshot else ''
            else:
                project['screenshot_path'] = ''
        
        print("✅ Assets prepared")
    
    def render_video(self) -> str:
        """
        Render final video.
        
        Returns:
            Path to final video
        """
        print("\n🎬 Rendering Video...")
        
        # Generate episode intro
        episode_title = self._generate_episode_title()
        intro_script = self._generate_intro_script()
        
        # Render intro
        intro_audio = self.output_folder / "intro_audio.mp3"
        self.audio_generator.generate_audio(intro_script, str(intro_audio))
        
        intro_video = self.output_folder / "seg_intro.mp4"
        self.video_renderer.render_intro(
            episode_title,
            str(intro_audio),
            intro_video
        )
        self.segment_files.append(str(intro_video))
        
        # Render each segment
        for i, project in enumerate(self.projects):
            audio_path = project.get('audio_path', '')
            
            segment = self.video_renderer.render_segment(
                project,
                i,
                audio_path
            )
            self.segment_files.append(str(segment))
            
            # Add transition (not after last segment)
            if i < len(self.projects) - 1:
                transition = self.output_folder / f"trans_{i:03d}.mp4"
                self.video_renderer.render_transition(transition, duration=1.0)
                self.segment_files.append(str(transition))
        
        # Render outro
        outro_video = self.output_folder / "seg_outro.mp4"
        self.video_renderer.render_outro(outro_video)
        self.segment_files.append(str(outro_video))
        
        # Concatenate all segments
        final_video = self.delivery_folder / "final_video.mp4"
        self.video_assembler.concatenate_segments(
            self.segment_files,
            str(final_video)
        )
        
        # Cleanup
        self._cleanup_temp_files()
        
        return str(final_video)
    
    def _generate_episode_title(self) -> str:
        """Generate episode title from projects."""
        from datetime import datetime
        
        date_str = datetime.now().strftime("%B %d")
        names = [p.get('name', '') for p in self.projects[:2]]
        
        if len(self.projects) <= 2:
            featured = " & ".join(names)
        else:
            featured = f"{names[0]}, {names[1]} & {len(self.projects) - 2} More"
        
        return f"{date_str} — {featured}"
    
    def _generate_intro_script(self) -> str:
        """Generate intro narration script."""
        names = [p.get('name', '') for p in self.projects]
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
    
    def _cleanup_temp_files(self) -> None:
        """Clean up temporary files."""
        for segment in self.segment_files:
            try:
                Path(segment).unlink(missing_ok=True)
            except:
                pass
        
        # Clean concat list if exists
        concat_list = self.output_folder / "concat_list.txt"
        concat_list.unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (VideoSuiteAutomated):

class VideoSuiteAutomated:
    def __init__(self):
        self.projects = []
        self.seedream_generator = SeedreamGenerator()  # ❌ Creates own dependency
        self.video_settings = CONFIG.get('video_settings', {})  # ❌ Global config
        
        # ❌ 30+ methods doing everything:
        # - Project loading
        # - Audio generation
        # - Graphics rendering
        # - Video rendering
        # - Assembly
        # - Database operations
        # - GitHub API calls
        # - FFmpeg commands
        
        # ❌ 1500+ lines in one class
        # ❌ Hard to test (needs all dependencies)
        # ❌ Hard to extend (must modify class)
        # ❌ Hard to understand (too many responsibilities)


✅ NEW APPROACH (SOLID):

class VideoPipeline(IVideoPipeline):
    def __init__(
        self,
        project_provider: IProjectProvider,      # ✅ Explicit dependency
        audio_generator: IAudioGenerator,        # ✅ Explicit dependency
        graphics_renderer: IGraphicsRenderer,    # ✅ Explicit dependency
        video_renderer: IVideoRenderer,          # ✅ Explicit dependency
        video_assembler: IVideoAssembler,        # ✅ Explicit dependency
        database_client: Optional[IDatabaseClient] = None  # ✅ Optional dependency
    ):
        # ✅ Only orchestrates - doesn't do the work
        # ✅ Delegates to injected components
        # ✅ Easy to test (can mock all dependencies)
        # ✅ Easy to extend (add new components without modification)
        # ✅ Easy to understand (clear responsibilities)
        
    async def run(self) -> str:
        # ✅ Clean pipeline flow
        projects = self.project_provider.load_projects()
        self.prepare_assets()
        video = self.render_video()
        return video
"""
