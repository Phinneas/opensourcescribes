"""
Audio Generator - Concrete implementation of IAudioGenerator
Demonstrates SOLID principles:
- Single Responsibility: Only generates audio
- Dependency Inversion: Depends on ILLMClient and IFFmpegExecutor (not concrete classes)
- Open/Closed: Can add new TTS providers without modification
"""
from pathlib import Path
from typing import Optional
from gtts import gTTS  # Fallback library

from interfaces.interfaces import IAudioGenerator, ILLMClient, IFFmpegExecutor


class AudioGenerator(IAudioGenerator):
    """
    Generates audio from text using TTS services.
    
    SOLID Compliance:
    ✅ SRP: Only responsible for audio generation
    ✅ DIP: Receives ILLMClient and IFFmpegExecutor through constructor
    ✅ OCP: Can add new TTS providers without modification
    ✅ LSP: Can be substituted with any IAudioGenerator implementation
    ✅ ISP: Implements only IAudioGenerator methods
    
    NO hidden dependencies - everything is explicitly provided.
    """
    
    def __init__(
        self,
        primary_llm_client: ILLMClient,
        fallback_llm_client: Optional[ILLMClient] = None,
        ffmpeg_executor: Optional[IFFmpegExecutor] = None
    ):
        """
        Constructor injection - all dependencies are EXPLICITLY provided.
        
        Args:
            primary_llm_client: Primary TTS service (e.g., MiniMax)
            fallback_llm_client: Fallback TTS service (e.g., Hume)
            ffmpeg_executor: FFmpeg for audio processing
        """
        # Dependencies are RECEIVED, not created or looked up
        self.primary_llm_client = primary_llm_client
        self.fallback_llm_client = fallback_llm_client
        self.ffmpeg_executor = ffmpeg_executor
    
    def generate_audio(self, text: str, output_path: str) -> str:
        """
        Generate audio from text using TTS services with fallback chain.
        
        Dependency Flow:
        1. Try primary LLM client (MiniMax)
        2. Try fallback LLM client (Hume) if primary fails
        3. Use gTTS as final fallback
        
        All dependencies are used - no hidden lookups.
        """
        import os
        import re
        
        # Check cache
        if os.path.exists(output_path):
            if os.path.getsize(output_path) < 1000:
                os.remove(output_path)  # Invalid cached file
                print(f"⚠️  Removed invalid cached audio at {output_path}")
            else:
                print(f"♻️  Using cached audio: {output_path}")
                return output_path
        
        # Phonetic corrections
        pronunciation_map = {
            "webmcp": "Web M C P",
            "sqlite": "sequel lite",
            "github": "git hub",
            "substack": "sub stack",
            "osmnx": "O S M N X"
        }
        processed_text = text
        for term, phonetic in pronunciation_map.items():
            processed_text = re.sub(rf'\b{term}\b', phonetic, processed_text, flags=re.IGNORECASE)
        
        # Try primary TTS service
        audio_bytes = self._try_primary_tts(processed_text)
        
        # Try fallback TTS service if primary failed
        if not audio_bytes and self.fallback_llm_client:
            audio_bytes = self._try_fallback_tts(processed_text)
        
        # Use gTTS as final fallback
        if not audio_bytes:
            audio_bytes = self._try_gtts(processed_text)
        
        # Save audio
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            
            # Trim silence using FFmpeg executor
            if self.ffmpeg_executor:
                self.trim_silence(output_path)
            
            return output_path
        
        raise Exception("All TTS services failed")
    
    def _try_primary_tts(self, text: str) -> Optional[bytes]:
        """Try primary TTS service"""
        try:
            print(f"🎙️ Primary TTS: {text[:50]}...")
            return self.primary_llm_client.generate_speech(text, voice_id="", output_path="")
        except Exception as e:
            print(f"⚠️  Primary TTS failed: {e}")
            return None
    
    def _try_fallback_tts(self, text: str) -> Optional[bytes]:
        """Try fallback TTS service"""
        try:
            print(f"🎙️ Fallback TTS: {text[:50]}...")
            return self.fallback_llm_client.generate_speech(text, voice_id="", output_path="")
        except Exception as e:
            print(f"⚠️  Fallback TTS failed: {e}")
            return None
    
    def _try_gtts(self, text: str) -> Optional[bytes]:
        """Final fallback: gTTS"""
        import tempfile
        
        try:
            print(f"🎙️ gTTS: {text[:50]}...")
            tts = gTTS(text=text, lang='en')
            
            # gTTS doesn't return bytes, save to temp file and read
            with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
                tmp_path = tmp.name
            
            tts.save(tmp_path)
            
            with open(tmp_path, 'rb') as f:
                audio_bytes = f.read()
            
            os.remove(tmp_path)
            return audio_bytes
            
        except Exception as e:
            print(f"⚠️  gTTS failed: {e}")
            return None
    
    def get_duration(self, audio_path: str) -> float:
        """Get audio duration using FFmpeg"""
        if not self.ffmpeg_executor:
            return 6.0  # Default
        
        import os
        if not os.path.exists(audio_path):
            return 6.0
        
        # Use FFmpeg to get duration
        success, output = self.ffmpeg_executor.execute([
            'ffprobe', '-v', 'error', 
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', 
            audio_path
        ])
        
        if success:
            try:
                return float(output.strip())
            except:
                pass
        
        return 6.0
    
    def trim_silence(self, audio_path: str) -> str:
        """Remove silence from beginning using FFmpeg"""
        if not self.ffmpeg_executor:
            return audio_path
        
        temp_path = audio_path.replace('.mp3', '_trimmed.mp3')
        
        success, _ = self.ffmpeg_executor.execute([
            'ffmpeg', '-y',
            '-i', audio_path,
            '-af', 'silenceremove=start_periods=1:start_duration=0:start_threshold=-50dB',
            temp_path
        ])
        
        if success:
            import shutil
            shutil.move(temp_path, audio_path)
        
        return audio_path


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated):

class VideoSuiteAutomated:
    def __init__(self):
        self.seedream_generator = SeedreamGenerator()  # Direct creation
        self.video_settings = CONFIG.get('video_settings', {})  # Global lookup
        
    def generate_audio(self, text, output_path):
        # ❌ Creates dependencies internally
        minimax_key = CONFIG.get('minimax', {}).get('api_key', '')  # Global lookup
        if minimax_key:
            # Use MiniMax
        hume_key = CONFIG.get('hume_ai', {}).get('api_key', '')  # Global lookup
        if hume_key:
            # Use Hume
        # ❌ Hard to test - can't mock dependencies
        # ❌ Hard to extend - must modify class to add new TTS
        # ❌ Hidden dependencies - not clear what this class needs


✅ NEW APPROACH (SOLID):

class AudioGenerator(IAudioGenerator):
    def __init__(
        self,
        primary_llm_client: ILLMClient,  # ✅ Explicit dependency
        fallback_llm_client: Optional[ILLMClient] = None,  # ✅ Explicit dependency
        ffmpeg_executor: Optional[IFFmpegExecutor] = None  # ✅ Explicit dependency
    ):
        self.primary_llm_client = primary_llm_client
        self.fallback_llm_client = fallback_llm_client
        self.ffmpeg_executor = ffmpeg_executor
        # ✅ All dependencies are visible in constructor
        # ✅ No global lookups or hidden dependencies
        # ✅ Easy to test - can inject mocks
        # ✅ Easy to extend - just add new ILLMClient implementation
        # ✅ Follows SOLID principles
"""
