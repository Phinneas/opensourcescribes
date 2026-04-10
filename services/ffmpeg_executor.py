"""
FFmpeg Executor - Concrete implementation of IFFmpegExecutor
Centralized FFmpeg command execution with error handling and logging.
"""
import subprocess
from typing import List, Tuple, Optional

from interfaces.interfaces import IFFmpegExecutor


class FFmpegExecutor(IFFmpegExecutor):
    """
    Executes FFmpeg commands with consistent error handling.
    
    SOLID Compliance:
    ✅ SRP: Only executes FFmpeg commands
    ✅ DIP: No dependencies (foundational service)
    ✅ OCP: Can be extended with new execution strategies
    ✅ LSP: Can be substituted with mock for testing
    ✅ ISP: Implements only IFFmpegExecutor methods
    
    Benefits:
    - Centralized FFmpeg error handling
    - Consistent timeout management
    - Easy to mock for testing
    - Single place for FFmpeg configuration
    """
    
    def __init__(self, default_timeout: int = 60, verbose: bool = False):
        """
        Constructor injection - configuration is explicit.
        
        Args:
            default_timeout: Default timeout for FFmpeg commands (seconds)
            verbose: Whether to print detailed command output
        """
        self.default_timeout = default_timeout
        self.verbose = verbose
    
    def execute(self, args: List[str], timeout: Optional[int] = None) -> Tuple[bool, str]:
        """
        Execute FFmpeg command with error handling.
        
        Args:
            args: FFmpeg command arguments (e.g., ['-y', '-i', 'input.mp4', 'output.mp4'])
            timeout: Command timeout in seconds (uses default if not specified)
            
        Returns:
            Tuple of (success: bool, output: str)
            - success: True if command completed successfully
            - output: stdout if successful, stderr if failed
        """
        if not args:
            return False, "No arguments provided"
        
        # Ensure 'ffmpeg' or 'ffprobe' is first argument
        if args[0] not in ['ffmpeg', 'ffprobe']:
            args = ['ffmpeg'] + args
        
        timeout = timeout or self.default_timeout
        
        try:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            if self.verbose:
                print(f"FFmpeg command: {' '.join(args)}")
                print(f"Return code: {result.returncode}")
                if result.stderr:
                    print(f"Stderr: {result.stderr[:200]}")
            
            return success, output
            
        except subprocess.TimeoutExpired:
            error_msg = f"FFmpeg command timed out after {timeout}s"
            print(f"⚠️  {error_msg}")
            return False, error_msg
            
        except FileNotFoundError:
            error_msg = "FFmpeg not found. Please install FFmpeg."
            print(f"❌ {error_msg}")
            return False, error_msg
            
        except Exception as e:
            error_msg = f"FFmpeg execution error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def execute_with_input(
        self, 
        args: List[str], 
        input_data: bytes,
        timeout: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        Execute FFmpeg command with stdin input (for pipe-based operations).
        
        Args:
            args: FFmpeg command arguments
            input_data: Binary data to pass to stdin
            timeout: Command timeout in seconds
            
        Returns:
            Tuple of (success: bool, output: str)
        """
        if not args:
            return False, "No arguments provided"
        
        # Ensure 'ffmpeg' is first argument
        if args[0] != 'ffmpeg':
            args = ['ffmpeg'] + args
        
        timeout = timeout or self.default_timeout
        
        try:
            result = subprocess.run(
                args,
                input=input_data,
                capture_output=True,
                timeout=timeout
            )
            
            success = result.returncode == 0
            output = result.stderr.decode('utf-8', errors='replace') if result.stderr else ""
            
            return success, output
            
        except subprocess.TimeoutExpired:
            error_msg = f"FFmpeg command timed out after {timeout}s"
            return False, error_msg
        except Exception as e:
            error_msg = f"FFmpeg execution error: {str(e)}"
            return False, error_msg
    
    def get_video_info(self, video_path: str) -> Optional[dict]:
        """
        Get video information using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info or None if failed
        """
        success, output = self.execute([
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            video_path
        ])
        
        if not success:
            return None
        
        try:
            import json
            return json.loads(output)
        except json.JSONDecodeError:
            return None
    
    def get_duration(self, media_path: str) -> Optional[float]:
        """
        Get duration of media file (video or audio).
        
        Args:
            media_path: Path to media file
            
        Returns:
            Duration in seconds or None if failed
        """
        success, output = self.execute([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            media_path
        ])
        
        if not success:
            return None
        
        try:
            return float(output.strip())
        except ValueError:
            return None
    
    def get_dimensions(self, video_path: str) -> Optional[Tuple[int, int]]:
        """
        Get video dimensions (width, height).
        
        Args:
            video_path: Path to video file
            
        Returns:
            Tuple of (width, height) or None if failed
        """
        success, output = self.execute([
            'ffprobe',
            '-v', 'error',
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'csv=p=0:s=x',
            video_path
        ])
        
        if not success:
            return None
        
        try:
            width_str, height_str = output.strip().split('x')
            return int(width_str), int(height_str)
        except (ValueError, AttributeError):
            return None


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (Scattered throughout VideoSuiteAutomated):

class VideoSuiteAutomated:
    def _render_segment_ffmpeg(self, ...):
        # ❌ FFmpeg commands scattered everywhere
        cmd = ['ffmpeg', '-y', '-i', ...]  # ❌ No error handling
        subprocess.run(cmd, check=True)  # ❌ No timeout control
        # ❌ Each method handles FFmpeg differently
        
    def _get_audio_duration(self, audio_path):
        # ❌ Duplicated FFmpeg logic
        cmd = ['ffprobe', '-v', 'error', ...]
        result = subprocess.run(cmd, ...)  # ❌ Different error handling


✅ NEW APPROACH (SOLID):

class FFmpegExecutor(IFFmpegExecutor):
    def execute(self, args: List[str], timeout: Optional[int] = None):
        # ✅ Centralized error handling
        # ✅ Consistent timeout management
        # ✅ Single place for FFmpeg configuration
        # ✅ Easy to mock for testing
        # ✅ All components use same interface

# Usage in other components:
class VideoRenderer:
    def __init__(self, ffmpeg_executor: IFFmpegExecutor):
        self.ffmpeg = ffmpeg_executor  # ✅ Explicit dependency
    
    def render_segment(self, ...):
        success, output = self.ffmpeg.execute([...])  # ✅ Consistent
        if not success:
            raise Exception(f"FFmpeg failed: {output}")
"""
