"""
Video Assembler - Concrete implementation of IVideoAssembler
Handles concatenation and final assembly of video segments.
"""
from pathlib import Path
from typing import List

from interfaces.interfaces import IVideoAssembler, IFFmpegExecutor


class VideoAssembler(IVideoAssembler):
    """
    Assembles final videos by concatenating segments.
    
    SOLID Compliance:
    ✅ SRP: Only assembles videos
    ✅ DIP: Depends on IFFmpegExecutor abstraction
    ✅ OCP: Can add new assembly strategies
    ✅ LSP: Substitutable with any IVideoAssembler
    ✅ ISP: Implements only IVideoAssembler methods
    
    Dependencies are explicit and injected.
    """
    
    def __init__(
        self,
        ffmpeg_executor: IFFmpegExecutor,
        fps: int = 30,
        output_folder: str = "assets"
    ):
        """
        Constructor injection - all dependencies explicit.
        
        Args:
            ffmpeg_executor: For FFmpeg video processing
            fps: Frames per second for output videos
            output_folder: Directory for temporary files
        """
        self.ffmpeg_executor = ffmpeg_executor
        self.fps = fps
        self.output_folder = Path(output_folder)
        
        # Ensure output directory exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
    
    def concatenate_segments(
        self, 
        segment_files: List[str], 
        output_path: str
    ) -> str:
        """
        Concatenate video segments into final video.
        
        Args:
            segment_files: List of segment file paths in order
            output_path: Path for final output video
            
        Returns:
            Path to concatenated video
        """
        if not segment_files:
            raise ValueError("No segment files provided")
        
        print(f"🔗 Concatenating {len(segment_files)} segments to {output_path}...")
        
        # Create concat list file
        concat_list = self.output_folder / "concat_list.txt"
        
        with open(concat_list, 'w') as f:
            for segment in segment_files:
                # Use absolute paths to avoid issues
                abs_path = Path(segment).resolve()
                f.write(f"file '{abs_path}'\n")
        
        # Execute FFmpeg concatenation
        success, stderr = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-vf', f'fps={self.fps}',  # Force constant FPS
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-profile:v', 'high',
            '-level', '4.0',
            '-bf', '0',  # Disable B-frames for monotonic PTS
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            '-movflags', '+faststart',
            output_path
        ])
        
        # Cleanup
        concat_list.unlink(missing_ok=True)
        
        if not success:
            raise Exception(f"Video concatenation failed: {stderr}")
        
        print(f"✅ Created: {output_path}")
        return output_path
    
    def add_audio_to_video(
        self, 
        video_path: str, 
        audio_path: str, 
        output_path: str
    ) -> str:
        """
        Add audio track to video.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_path: Path for output video
            
        Returns:
            Path to video with audio
        """
        print(f"🎵 Adding audio to video...")
        
        success, stderr = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_path,
            '-map', '0:v:0',  # Use video from first input
            '-map', '1:a:0',  # Use audio from second input
            '-c:v', 'copy',   # Copy video stream
            '-c:a', 'aac',    # Encode audio as AAC
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            output_path
        ])
        
        if not success:
            raise Exception(f"Audio merge failed: {stderr}")
        
        return output_path
    
    def normalize_audio(
        self, 
        video_path: str, 
        output_path: str,
        sample_rate: int = 48000,
        channels: int = 2
    ) -> str:
        """
        Normalize audio in video to consistent format.
        
        Args:
            video_path: Path to video file
            output_path: Path for output video
            sample_rate: Target sample rate (default: 48000)
            channels: Target number of channels (default: 2)
            
        Returns:
            Path to normalized video
        """
        print(f"🔊 Normalizing audio...")
        
        success, stderr = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-i', video_path,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', str(sample_rate),
            '-ac', str(channels),
            output_path
        ])
        
        if not success:
            raise Exception(f"Audio normalization failed: {stderr}")
        
        return output_path
    
    def add_transitions(
        self,
        segment_files: List[str],
        transition_duration: float = 1.0,
        output_path: str = None
    ) -> str:
        """
        Add fade transitions between segments.
        
        Args:
            segment_files: List of segment file paths
            transition_duration: Duration of each transition in seconds
            output_path: Path for output video (optional)
            
        Returns:
            Path to video with transitions
        """
        if len(segment_files) < 2:
            return segment_files[0] if segment_files else None
        
        print(f"✨ Adding transitions between segments...")
        
        # Create transitions
        segments_with_transitions = []
        
        for i, segment in enumerate(segment_files):
            segments_with_transitions.append(segment)
            
            # Add transition between segments (not after last)
            if i < len(segment_files) - 1:
                trans_path = self.output_folder / f"trans_{i:03d}.mp4"
                
                # Create transition video (fade to black and back)
                self._create_fade_transition(trans_path, transition_duration)
                segments_with_transitions.append(str(trans_path))
        
        # Concatenate with transitions
        if output_path is None:
            output_path = str(self.output_folder / "final_with_transitions.mp4")
        
        return self.concatenate_segments(segments_with_transitions, output_path)
    
    def extract_clip(
        self,
        video_path: str,
        start_time: float,
        duration: float,
        output_path: str
    ) -> str:
        """
        Extract a clip from a video.
        
        Args:
            video_path: Path to source video
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Path for output clip
            
        Returns:
            Path to extracted clip
        """
        success, stderr = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-i', video_path,
            '-ss', str(start_time),
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-c:a', 'aac',
            output_path
        ])
        
        if not success:
            raise Exception(f"Clip extraction failed: {stderr}")
        
        return output_path
    
    def _create_fade_transition(self, output_path: Path, duration: float) -> None:
        """Create a fade transition video."""
        self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=0x080c14:s=1920x1080:r={self.fps}:d={duration}',
            '-f', 'lavfi',
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-t', str(duration),
            '-vf', 'fade=in:0:15,fade=out:15:15',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '128k',
            str(output_path)
        ])


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated):

class VideoSuiteAutomated:
    def concatenate_segments(self, segment_files, output_name):
        # ❌ FFmpeg logic embedded in large class
        # ❌ No abstraction, hard to test
        # ❌ Error handling scattered
        concat_list = Path("concat_list.txt")
        
        # ❌ Hardcoded FFmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', str(concat_list),
            '-vf', 'fps=30',
            '-c:v', 'libx264', ...
        ]
        
        subprocess.run(cmd, check=True)  # ❌ Direct subprocess call


✅ NEW APPROACH (SOLID):

class VideoAssembler(IVideoAssembler):
    def __init__(self, ffmpeg_executor: IFFmpegExecutor):
        # ✅ Explicit dependency on FFmpegExecutor
        # ✅ Can mock for testing
        # ✅ Single responsibility: video assembly
    
    def concatenate_segments(self, segment_files: List[str], output_path: str):
        # ✅ Clean interface
        # ✅ Uses injected ffmpeg_executor
        # ✅ Consistent error handling
        # ✅ Easy to test with mock executor
"""
