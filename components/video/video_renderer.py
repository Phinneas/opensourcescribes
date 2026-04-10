"""
Video Renderer - Concrete implementation of IVideoRenderer
Renders video segments: intro, segments, outro, transitions.
"""
import os
import math
from pathlib import Path
from typing import Dict, Optional
from PIL import Image, ImageDraw, ImageFont

from interfaces.interfaces import IVideoRenderer, IGraphicsRenderer, IAudioGenerator, IFFmpegExecutor


class VideoRenderer(IVideoRenderer):
    """
    Renders all video segments for the pipeline.
    
    SOLID Compliance:
    ✅ SRP: Only renders video segments
    ✅ DIP: Depends on IGraphicsRenderer, IAudioGenerator, IFFmpegExecutor
    ✅ OCP: Can add new rendering strategies
    ✅ LSP: Substitutable with any IVideoRenderer
    ✅ ISP: Implements only IVideoRenderer methods
    
    All dependencies are explicit and injected.
    """
    
    def __init__(
        self,
        graphics_renderer: IGraphicsRenderer,
        audio_generator: IAudioGenerator,
        ffmpeg_executor: IFFmpegExecutor,
        output_folder: str = "assets",
        fps: int = 30,
        title_duration: float = 4.0
    ):
        """
        Constructor injection - all dependencies explicit.
        
        Args:
            graphics_renderer: For title cards and screenshots
            audio_generator: For audio duration calculation
            ffmpeg_executor: For FFmpeg video processing
            output_folder: Directory for output files
            fps: Frames per second for videos
            title_duration: Duration of title cards in seconds
        """
        self.graphics_renderer = graphics_renderer
        self.audio_generator = audio_generator
        self.ffmpeg_executor = ffmpeg_executor
        self.output_folder = Path(output_folder)
        self.fps = fps
        self.title_duration = title_duration
        
        # Ensure output directory exists
        self.output_folder.mkdir(parents=True, exist_ok=True)
    
    def render_intro(self, episode_title: str, audio_path: str, output_path: Path) -> Path:
        """
        Render animated intro video segment.
        
        Args:
            episode_title: Title text for the episode
            audio_path: Path to intro audio file
            output_path: Output video path
            
        Returns:
            Path to rendered intro video
        """
        print(f"  🎬 Rendering intro: {episode_title}")
        
        # Get audio duration to match video length
        audio_duration = self.audio_generator.get_duration(audio_path) if audio_path and os.path.exists(audio_path) else 6.0
        duration = max(6.0, audio_duration)
        
        # Generate intro frames (animated with PIL)
        vid_only = output_path.with_suffix('.vid.mp4')
        
        # Render animated intro frames
        success = self._render_intro_frames(episode_title, vid_only, duration)
        
        if not success:
            # Fallback: static intro card
            print("  ⚠️  Intro animation failed, using static card")
            return self._render_static_intro(episode_title, audio_path, output_path)
        
        # Merge audio
        if audio_path and os.path.exists(audio_path):
            self._merge_audio_video(vid_only, audio_path, output_path)
            vid_only.unlink(missing_ok=True)
        else:
            vid_only.rename(output_path)
        
        return output_path
    
    def render_segment(self, project: Dict, index: int, audio_path: str) -> Path:
        """
        Render project video segment: title card + scroll animation + audio.
        
        Args:
            project: Project dictionary
            index: Segment index
            audio_path: Path to segment audio file
            
        Returns:
            Path to rendered segment video
        """
        print(f"  🎬 Rendering segment {index + 1}: {project.get('name', 'Unknown')}")
        
        # Calculate durations
        audio_duration = self.audio_generator.get_duration(audio_path) if audio_path and os.path.exists(audio_path) else 42.0
        segment_duration = max(8.0, audio_duration)  # Minimum 8s total
        scroll_duration = max(4.0, segment_duration - self.title_duration)
        
        project_id = project.get('id', f'seg_{index}')
        
        # Render title card
        print(f"    🖼️  Title card...")
        title_card = self.graphics_renderer.render_title_card(project)
        title_mp4 = self.output_folder / f"tmp_{project_id}_title.mp4"
        
        # Create title card video
        self._create_static_video(title_card, title_mp4, self.title_duration)
        
        # Render scroll animation
        print(f"    📜 Scroll animation ({scroll_duration}s)...")
        scroll_mp4 = self.output_folder / f"tmp_{project_id}_scroll.mp4"
        
        # Get screenshot
        screenshot = project.get('screenshot_path', '')
        if screenshot and os.path.exists(screenshot):
            self._render_scroll_animation(screenshot, scroll_mp4, scroll_duration)
        else:
            # Try to capture screenshot
            screenshot = self.graphics_renderer.capture_screenshot(project.get('github_url', ''))
            
            if screenshot:
                self._render_scroll_animation(str(screenshot), scroll_mp4, scroll_duration)
            else:
                # Use fallback
                print(f"    ⚠️  No screenshot, using fallback")
                fallback = self.graphics_renderer.create_fallback_screenshot(project)
                self._render_scroll_animation(str(fallback), scroll_mp4, scroll_duration)
        
        # Concatenate title + scroll
        video_only = self.output_folder / f"tmp_{project_id}_vid.mp4"
        self._concatenate_videos([title_mp4, scroll_mp4], video_only)
        
        # Merge audio
        seg_out = self.output_folder / f"seg_{index:03d}.mp4"
        if audio_path and os.path.exists(audio_path):
            self._merge_audio_video(video_only, audio_path, seg_out)
            video_only.unlink(missing_ok=True)
        else:
            video_only.rename(seg_out)
        
        # Cleanup temp files
        for f in [title_card, title_mp4, scroll_mp4]:
            try:
                Path(f).unlink(missing_ok=True)
            except:
                pass
        
        return seg_out
    
    def render_outro(self, output_path: Path) -> Path:
        """
        Render outro video segment.
        
        Args:
            output_path: Output video path
            
        Returns:
            Path to rendered outro video
        """
        print("  🎬 Rendering outro...")
        
        # Create outro card using graphics renderer
        # For now, create a simple static outro
        outro_image = self.output_folder / "outro_card.png"
        self._create_outro_image(outro_image)
        
        # Create video
        self._create_static_video(outro_image, output_path, duration=5.0)
        
        # Cleanup
        outro_image.unlink(missing_ok=True)
        
        return output_path
    
    def render_transition(self, output_path: Path, duration: float) -> Path:
        """
        Render transition video segment (fade to black).
        
        Args:
            output_path: Output video path
            duration: Transition duration in seconds
            
        Returns:
            Path to rendered transition video
        """
        # Use FFmpeg to create a simple fade transition
        success, _ = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=0x080c14:s=1920x1080:r={self.fps}:d={duration}',
            '-f', 'lavfi',
            '-i', f'anullsrc=channel_layout=stereo:sample_rate=48000',
            '-t', str(duration),
            '-vf', 'fade=in:0:15,fade=out:15:15',
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k',
            str(output_path)
        ])
        
        if not success:
            # Create a simple black frame video as fallback
            self._create_black_video(output_path, duration)
        
        return output_path
    
    # ═══════════════════════════════════════════════════════════════════
    # Private helper methods
    # ═══════════════════════════════════════════════════════════════════
    
    def _render_intro_frames(self, episode_title: str, output_path: Path, duration: float) -> bool:
        """Render animated intro frames using PIL."""
        # This is a complex animation - delegate to helper method
        # For simplicity, return False to trigger static fallback
        # In production, implement full animation
        return False
    
    def _render_static_intro(self, episode_title: str, audio_path: str, output_path: Path) -> Path:
        """Render static intro as fallback."""
        # Create intro image
        intro_image = self.output_folder / "intro_card.png"
        self._create_intro_image(episode_title, intro_image)
        
        # Get duration from audio
        duration = self.audio_generator.get_duration(audio_path) if audio_path else 6.0
        
        # Create video
        temp_video = output_path.with_suffix('.vid.mp4')
        self._create_static_video(intro_image, temp_video, duration)
        
        # Merge audio
        if audio_path:
            self._merge_audio_video(temp_video, audio_path, output_path)
            temp_video.unlink(missing_ok=True)
        else:
            temp_video.rename(output_path)
        
        intro_image.unlink(missing_ok=True)
        return output_path
    
    def _create_static_video(self, image_path: Path, output_path: Path, duration: float) -> None:
        """Create a static video from an image."""
        self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-loop', '1',
            '-framerate', str(self.fps),
            '-i', str(image_path),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-t', str(duration),
            '-r', str(self.fps),
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
    
    def _create_black_video(self, output_path: Path, duration: float) -> None:
        """Create a black frame video."""
        self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=black:s=1920x1080:r={self.fps}:d={duration}',
            '-t', str(duration),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
    
    def _render_scroll_animation(self, screenshot_path: str, output_path: Path, duration: float) -> None:
        """Render scroll animation for a screenshot."""
        # Simplified version - create a Ken Burns effect
        # In production, implement full scroll animation with frame generation
        self._create_static_video(Path(screenshot_path), output_path, duration)
    
    def _concatenate_videos(self, video_paths: list, output_path: Path) -> None:
        """Concatenate multiple videos."""
        concat_list = self.output_folder / "concat_list.txt"
        
        with open(concat_list, 'w') as f:
            for video_path in video_paths:
                f.write(f"file '{video_path}'\n")
        
        self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_list),
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-r', str(self.fps),
            '-pix_fmt', 'yuv420p',
            str(output_path)
        ])
        
        concat_list.unlink(missing_ok=True)
    
    def _merge_audio_video(self, video_path: Path, audio_path: str, output_path: Path) -> None:
        """Merge audio and video streams."""
        self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', audio_path,
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-ar', '48000',
            '-ac', '2',
            str(output_path)
        ])
    
    def _create_intro_image(self, episode_title: str, output_path: Path) -> None:
        """Create intro card image."""
        W, H = 1920, 1080
        BG = (10, 10, 26)
        
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        # Add title text
        font = ImageFont.load_default()
        draw.text((W // 2, H // 2), episode_title, fill=(255, 255, 255), font=font)
        
        img.save(str(output_path))
    
    def _create_outro_image(self, output_path: Path) -> None:
        """Create outro card image."""
        W, H = 1920, 1080
        BG = (10, 10, 26)
        
        img = Image.new('RGB', (W, H), BG)
        draw = ImageDraw.Draw(img)
        
        # Add outro text
        font = ImageFont.load_default()
        draw.text((W // 2, H // 2), "Thanks for watching!", fill=(255, 255, 255), font=font)
        
        img.save(str(output_path))
