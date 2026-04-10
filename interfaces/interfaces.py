"""
SOLID Interfaces - Contracts for all components
These define WHAT each component does, not HOW.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Optional, Tuple


# ═══════════════════════════════════════════════════════════════════════
# DOMAIN INTERFACES - Core business logic
# ═══════════════════════════════════════════════════════════════════════

class IProjectProvider(ABC):
    """Provides project data - could be from JSON, database, API, etc."""
    
    @abstractmethod
    def load_projects(self) -> List[Dict]:
        """Load all projects"""
        pass
    
    @abstractmethod
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """Get a specific project by ID"""
        pass


class IAudioGenerator(ABC):
    """Generates audio from text - TTS services"""
    
    @abstractmethod
    def generate_audio(self, text: str, output_path: str) -> str:
        """Generate audio file from text"""
        pass
    
    @abstractmethod
    def get_duration(self, audio_path: str) -> float:
        """Get duration of audio file in seconds"""
        pass
    
    @abstractmethod
    def trim_silence(self, audio_path: str) -> str:
        """Remove silence from beginning of audio"""
        pass


class IGraphicsRenderer(ABC):
    """Renders graphics and screenshots"""
    
    @abstractmethod
    def render_title_card(self, project: Dict) -> Path:
        """Create title card image for project"""
        pass
    
    @abstractmethod
    def capture_screenshot(self, github_url: str) -> Optional[Path]:
        """Capture GitHub repository screenshot"""
        pass
    
    @abstractmethod
    def create_fallback_screenshot(self, project: Dict) -> Path:
        """Create fallback screenshot when capture fails"""
        pass


class IVideoRenderer(ABC):
    """Renders video segments"""
    
    @abstractmethod
    def render_intro(self, episode_title: str, audio_path: str, output_path: Path) -> Path:
        """Render intro video segment"""
        pass
    
    @abstractmethod
    def render_segment(self, project: Dict, index: int, audio_path: str) -> Path:
        """Render project video segment"""
        pass
    
    @abstractmethod
    def render_outro(self, output_path: Path) -> Path:
        """Render outro video segment"""
        pass
    
    @abstractmethod
    def render_transition(self, output_path: Path, duration: float) -> Path:
        """Render transition video segment"""
        pass


class IVideoAssembler(ABC):
    """Assembles video segments into final video"""
    
    @abstractmethod
    def concatenate_segments(self, segment_files: List[str], output_path: str) -> str:
        """Concatenate video segments into final video"""
        pass
    
    @abstractmethod
    def add_audio_to_video(self, video_path: str, audio_path: str, output_path: str) -> str:
        """Add audio track to video"""
        pass


# ═══════════════════════════════════════════════════════════════════════
# EXTERNAL SERVICE INTERFACES - External APIs and services
# ═══════════════════════════════════════════════════════════════════════

class ILLMClient(ABC):
    """Client for LLM services (MiniMax, Hume, etc.)"""
    
    @abstractmethod
    def generate_speech(self, text: str, voice_id: str, output_path: str) -> str:
        """Generate speech from text"""
        pass


class IGitHubClient(ABC):
    """Client for GitHub API interactions"""
    
    @abstractmethod
    def get_repository_stats(self, owner: str, repo: str) -> Tuple[int, int, str, List[str]]:
        """Get stars, forks, language, topics"""
        pass
    
    @abstractmethod
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """Get repository README content"""
        pass


class IFFmpegExecutor(ABC):
    """Executor for FFmpeg commands"""
    
    @abstractmethod
    def execute(self, args: List[str], timeout: int = 60) -> Tuple[bool, str]:
        """Execute FFmpeg command"""
        pass


# ═══════════════════════════════════════════════════════════════════════
# ORCHESTRATION INTERFACES - High-level coordination
# ═══════════════════════════════════════════════════════════════════════

class IVideoPipeline(ABC):
    """Main video generation pipeline"""
    
    @abstractmethod
    async def run(self) -> str:
        """Execute complete video generation pipeline"""
        pass
    
    @abstractmethod
    def prepare_assets(self) -> None:
        """Prepare all assets (audio, graphics, screenshots)"""
        pass
    
    @abstractmethod
    def render_video(self) -> str:
        """Render final video"""
        pass


class IDatabaseClient(ABC):
    """Client for database operations"""
    
    @abstractmethod
    def mark_published(self, url: str, metadata: Dict) -> None:
        """Mark repository as published"""
        pass
    
    @abstractmethod
    def is_published(self, url: str) -> bool:
        """Check if repository has been published"""
        pass
