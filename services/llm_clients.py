"""
LLM Clients - Concrete implementations of ILLMClient
TTS service clients for MiniMax and Hume AI.
"""
import requests
from typing import Optional
from abc import ABC

from interfaces.interfaces import ILLMClient


class BaseLLMClient(ABC):
    """Base class with common functionality for LLM clients."""
    
    def __init__(self, timeout: int = 60):
        self.timeout = timeout
    
    def _handle_error(self, service_name: str, error: Exception) -> None:
        """Common error handling."""
        print(f"⚠️  {service_name} error: {error}")


class MiniMaxClient(BaseLLMClient, ILLMClient):
    """
    MiniMax TTS client - Primary TTS service.
    
    SOLID Compliance:
    ✅ SRP: Only handles MiniMax TTS
    ✅ DIP: Implements ILLMClient interface
    ✅ OCP: Can be extended for new MiniMax features
    ✅ LSP: Substitutable with any ILLMClient
    ✅ ISP: Implements only ILLMClient methods
    """
    
    def __init__(
        self,
        api_key: str,
        group_id: str,
        voice_id: str = "male-qn-qingse",
        speed: float = 1.0,
        timeout: int = 60
    ):
        """
        Constructor injection - all configuration explicit.
        
        Args:
            api_key: MiniMax API key
            group_id: MiniMax group ID
            voice_id: Voice identifier
            speed: Speech speed (0.5 - 2.0)
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.api_key = api_key
        self.group_id = group_id
        self.voice_id = voice_id
        self.speed = speed
        self.base_url = "https://api.minimax.io"
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate speech from text using MiniMax T2A v2 API.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (uses default if not provided)
            output_path: Optional path to save audio (returns bytes if None)
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key or not self.group_id:
            raise ValueError("MiniMax API key and group ID are required")
        
        voice_id = voice_id or self.voice_id
        url = f"{self.base_url}/v1/t2a_v2?GroupId={self.group_id}"
        
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "speech-02-hd",
                    "text": text,
                    "stream": False,
                    "voice_setting": {
                        "voice_id": voice_id,
                        "speed": self.speed,
                        "vol": 1.0,
                        "pitch": 0,
                    },
                    "audio_setting": {
                        "sample_rate": 32000,
                        "bitrate": 128000,
                        "format": "mp3",
                        "channel": 1,
                    },
                },
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for API errors
                if data.get("base_resp", {}).get("status_code") != 0:
                    error_msg = data.get("base_resp", {}).get("status_msg", "Unknown error")
                    print(f"⚠️  MiniMax API error: {error_msg}")
                    return None
                
                # Extract audio data (returned as hex string)
                audio_hex = data.get("data", {}).get("audio", "")
                if audio_hex:
                    audio_bytes = bytes.fromhex(audio_hex)
                    
                    # Save to file if path provided
                    if output_path:
                        with open(output_path, "wb") as f:
                            f.write(audio_bytes)
                    
                    return audio_bytes
                else:
                    print("⚠️  MiniMax: No audio data in response")
                    return None
            else:
                print(f"⚠️  MiniMax HTTP {response.status_code}: {response.text[:120]}")
                return None
                
        except requests.Timeout:
            self._handle_error("MiniMax", Exception("Request timeout"))
            return None
        except Exception as e:
            self._handle_error("MiniMax", e)
            return None


class HumeClient(BaseLLMClient, ILLMClient):
    """
    Hume AI TTS client - Fallback TTS service.
    
    SOLID Compliance:
    ✅ SRP: Only handles Hume TTS
    ✅ DIP: Implements ILLMClient interface
    ✅ OCP: Can be extended for new Hume features
    ✅ LSP: Substitutable with any ILLMClient
    ✅ ISP: Implements only ILLMClient methods
    """
    
    def __init__(
        self,
        api_key: str,
        voice_id: str = "drew",
        speed: float = 1.0,
        timeout: int = 60
    ):
        """
        Constructor injection - all configuration explicit.
        
        Args:
            api_key: Hume API key
            voice_id: Voice identifier
            speed: Speech speed
            timeout: Request timeout in seconds
        """
        super().__init__(timeout)
        self.api_key = api_key
        self.voice_id = voice_id
        self.speed = speed
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """
        Generate speech from text using Hume TTS API.
        
        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (uses default if not provided)
            output_path: Optional path to save audio (returns bytes if None)
            
        Returns:
            Audio bytes or None if failed
        """
        if not self.api_key:
            raise ValueError("Hume API key is required")
        
        voice_id = voice_id or self.voice_id
        
        try:
            # Hume requires their SDK
            from hume import HumeClient
            from hume.tts import PostedUtterance
            
            client = HumeClient(api_key=self.api_key)
            
            # Generate audio
            audio_generator = client.tts.synthesize_file(
                utterances=[PostedUtterance(text=text)]
            )
            
            # Collect audio bytes
            audio_bytes = b''.join(chunk for chunk in audio_generator)
            
            if len(audio_bytes) < 1000:
                print(f"⚠️  Hume returned only {len(audio_bytes)} bytes")
                return None
            
            # Save to file if path provided
            if output_path:
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
            
            return audio_bytes
            
        except ImportError:
            print("⚠️  Hume SDK not installed. Install with: pip install hume")
            return None
        except Exception as e:
            self._handle_error("Hume", e)
            return None


class MockLLMClient(ILLMClient):
    """
    Mock TTS client for testing - returns dummy audio data.
    
    SOLID Benefits:
    - Easy to test without real API keys
    - Fast, predictable tests
    - No network dependencies
    """
    
    def generate_speech(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        output_path: Optional[str] = None
    ) -> Optional[bytes]:
        """Return mock audio data."""
        # Create a small dummy MP3 header
        mock_audio = b'ID3' + b'\x00' * 100  # Dummy MP3 data
        
        if output_path:
            with open(output_path, "wb") as f:
                f.write(mock_audio)
        
        return mock_audio


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated.generate_audio):

def generate_audio(self, text, output_path):
    # ❌ TTS logic embedded in large class
    # ❌ Multiple TTS services mixed together
    
    # 1. MiniMax T2A v2 — international platform
    minimax_key = CONFIG.get('minimax', {}).get('api_key', '')  # ❌ Global config
    minimax_group = CONFIG.get('minimax', {}).get('group_id', '')
    if minimax_key and minimax_group:
        try:
            import requests as _req
            # ... 50+ lines of MiniMax code ...
        except Exception as e:
            print(f"⚠️  MiniMax failed: {e}")
    
    # 2. Hume (fallback)
    hume_key = CONFIG.get('hume_ai', {}).get('api_key', '')  # ❌ Global config
    if hume_key:
        try:
            from hume import HumeClient
            # ... 20+ lines of Hume code ...
        except Exception as e:
            print(f"⚠️  Hume failed: {e}")
    
    # 3. gTTS (last resort)
    # ... gTTS code ...


✅ NEW APPROACH (SOLID):

# Each TTS service has its own focused class
class MiniMaxClient(ILLMClient):
    # ✅ Single responsibility: MiniMax TTS only
    # ✅ All config in constructor
    # ✅ Easy to test in isolation
    # ✅ Can mock for testing

class HumeClient(ILLMClient):
    # ✅ Single responsibility: Hume TTS only
    # ✅ All config in constructor
    # ✅ Easy to test in isolation

class AudioGenerator:
    def __init__(
        self,
        primary_llm_client: ILLMClient,  # ✅ Explicit dependency
        fallback_llm_client: Optional[ILLMClient] = None
    ):
        # ✅ Flexible: can use any ILLMClient
        # ✅ No hardcoded TTS services
        # ✅ Easy to swap implementations
"""
