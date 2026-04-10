"""
Composition Root - SINGLE PLACE where all dependencies are wired together.
This is the ONLY place that knows about concrete implementations.

NO component creates its own dependencies or looks them up globally.
ALL dependencies are explicitly passed through constructors.
"""
from pathlib import Path
from typing import Dict

# Import interfaces
from interfaces.interfaces import (
    IProjectProvider, IAudioGenerator, IGraphicsRenderer, 
    IVideoRenderer, IVideoAssembler, IVideoPipeline,
    ILLMClient, IGitHubClient, IFFmpegExecutor, IDatabaseClient
)

# Import concrete implementations
from components.project.project_manager import ProjectManager
from components.audio.audio_generator import AudioGenerator
from components.graphics.graphics_renderer import GraphicsRenderer
from components.video.video_renderer import VideoRenderer
from components.video.video_assembler import VideoAssembler
from components.video.video_pipeline import VideoPipeline
from services.llm_clients import MiniMaxClient, HumeClient
from services.github_client import GitHubClient
from services.ffmpeg_executor import FFmpegExecutor
from core.db import DB


class CompositionRoot:
    """
    SINGLE ENTRY POINT - Wires all dependencies explicitly.
    
    This is where A knows that B is provided by D (not C).
    Each component receives only what it needs - no hidden dependencies.
    """
    
    @staticmethod
    def create_video_pipeline(config: Dict) -> IVideoPipeline:
        """
        Create the complete video generation pipeline with all dependencies.
        
        Dependency Flow:
        VideoPipeline
            ├── IProjectProvider (ProjectManager)
            │       └── IDatabaseClient (DB)
            │
            ├── IAudioGenerator (AudioGenerator)
            │       ├── ILLMClient (MiniMaxClient) → fallback: HumeClient
            │       └── IFFmpegExecutor (FFmpegExecutor)
            │
            ├── IGraphicsRenderer (GraphicsRenderer)
            │       ├── IGitHubClient (GitHubClient)
            │       └── IFFmpegExecutor (FFmpegExecutor)
            │
            ├── IVideoRenderer (VideoRenderer)
            │       ├── IGraphicsRenderer (same instance as above)
            │       ├── IAudioGenerator (same instance as above)
            │       └── IFFmpegExecutor (same instance as above)
            │
            └── IVideoAssembler (VideoAssembler)
                    └── IFFmpegExecutor (same instance as above)
        """
        
        # ═══════════════════════════════════════════════════════════════
        # Step 1: Create foundational services (no dependencies)
        # ═══════════════════════════════════════════════════════════════
        
        # Database client - no dependencies
        database_client: IDatabaseClient = DB()
        
        # FFmpeg executor - no dependencies
        ffmpeg_executor: IFFmpegExecutor = FFmpegExecutor()
        
        # GitHub client - needs config
        github_client: IGitHubClient = GitHubClient(
            api_key=config.get('github', {}).get('api_key', '')
        )
        
        # ═══════════════════════════════════════════════════════════════
        # Step 2: Create LLM clients (for audio generation)
        # ═══════════════════════════════════════════════════════════════
        
        # Primary TTS client
        minimax_client: ILLMClient = MiniMaxClient(
            api_key=config.get('minimax', {}).get('api_key', ''),
            group_id=config.get('minimax', {}).get('group_id', ''),
            voice_id=config.get('voice', {}).get('minimax_voice_id', 'male-qn-qingse')
        )
        
        # Fallback TTS client  
        hume_client: ILLMClient = HumeClient(
            api_key=config.get('hume_ai', {}).get('api_key', ''),
            voice_id=config.get('voice', {}).get('hume_voice_id', 'drew')
        )
        
        # ═══════════════════════════════════════════════════════════════
        # Step 3: Create domain services (depend on foundational services)
        # ═══════════════════════════════════════════════════════════════
        
        # Project provider - needs database
        project_provider: IProjectProvider = ProjectManager(
            database_client=database_client
        )
        
        # Audio generator - needs LLM clients and FFmpeg
        audio_generator: IAudioGenerator = AudioGenerator(
            primary_llm_client=minimax_client,
            fallback_llm_client=hume_client,
            ffmpeg_executor=ffmpeg_executor
        )
        
        # Graphics renderer - needs GitHub client and FFmpeg
        graphics_renderer: IGraphicsRenderer = GraphicsRenderer(
            github_client=github_client,
            ffmpeg_executor=ffmpeg_executor
        )
        
        # ═══════════════════════════════════════════════════════════════
        # Step 4: Create video rendering services
        # ═══════════════════════════════════════════════════════════════
        
        # Video renderer - needs graphics, audio, and FFmpeg
        video_renderer: IVideoRenderer = VideoRenderer(
            graphics_renderer=graphics_renderer,
            audio_generator=audio_generator,
            ffmpeg_executor=ffmpeg_executor
        )
        
        # Video assembler - needs FFmpeg
        video_assembler: IVideoAssembler = VideoAssembler(
            ffmpeg_executor=ffmpeg_executor
        )
        
        # ═══════════════════════════════════════════════════════════════
        # Step 5: Create main pipeline (orchestrates everything)
        # ═══════════════════════════════════════════════════════════════
        
        # Main video pipeline - needs all services
        video_pipeline: IVideoPipeline = VideoPipeline(
            project_provider=project_provider,
            audio_generator=audio_generator,
            graphics_renderer=graphics_renderer,
            video_renderer=video_renderer,
            video_assembler=video_assembler,
            database_client=database_client
        )
        
        return video_pipeline


# ═══════════════════════════════════════════════════════════════════════
# USAGE EXAMPLE - This is how you use the composition root
# ═══════════════════════════════════════════════════════════════════════

def main():
    """Main entry point - creates pipeline through composition root"""
    import json
    
    # Load configuration
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Create pipeline through composition root
    # This is the ONLY place where dependencies are wired
    pipeline = CompositionRoot.create_video_pipeline(config)
    
    # Run pipeline
    import asyncio
    final_video = asyncio.run(pipeline.run())
    
    print(f"✅ Video created: {final_video}")


if __name__ == "__main__":
    main()
