"""
Enhanced Audio Generator for OpenSourceScribes
Supports multiple AI voice services with advanced customization
"""

import os
import json
import asyncio
import subprocess
from typing import Optional, Dict, Any
import requests

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


class EnhancedVoiceGenerator:
    """Enhanced voice generator with multiple AI services"""
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.voice_cache = {}
        
    def trim_audio_silence(self, input_path: str, threshold_db: int = -50):
        """Trim silence from beginning of audio file"""
        temp_path = input_path.replace('.mp3', '_trimmed.mp3')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', input_path,
            '-af', f'silenceremove=start_periods=1:start_duration=0:start_threshold={threshold_db}dB',
            temp_path
        ]
        
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            os.replace(temp_path, input_path)
            print(f"   ✂️  Silence trimmed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"   ⚠️  Silence trimming failed: {e}")
            return False
    
    # ==================== HUME.AI (Your Current Service) ====================
    
    def generate_audio_hume_enhanced(
        self, 
        text: str, 
        output_path: str,
        voice_id: str = None,
        speed: float = 1.0,
        emotional_intensity: float = 0.5
    ) -> bool:
        """
        Generate audio using Hume.ai with enhanced options
        
        Voice options for Hume.ai:
        - Check https://dev.hume.ai/resources/docs/voices for available voices
        - Popular choices: 'default', 'lily', 'drew', 'anya'
        """
        try:
            print(f"🎙️ Hume.ai Enhanced: {text[:40]}...")
            
            from hume import HumeClient
            from hume.tts import PostedUtterance
            
            # Use configured voice_id or parameter
            voice_id = voice_id or self.config.get('hume_ai', {}).get('enhanced_voice_id', 'drew')
            
            # Initialize Hume client
            client = HumeClient(api_key=self.config['hume_ai']['api_key'])
            
            # Generate speech with options
            audio_generator = client.tts.synthesize_file(
                utterances=[
                    PostedUtterance(text=text)
                ],
                voice_id=voice_id,
                speed=speed
            )
            
            # Collect chunks
            audio_chunks = []
            for chunk in audio_generator:
                audio_chunks.append(chunk)
            
            audio_bytes = b''.join(audio_chunks)
            
            # Save
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            
            print(f"   ✅ Hume.ai voice generated (voice: {voice_id}, speed: {speed}x)")
            return True
            
        except Exception as e:
            print(f"   ⚠️  Hume.ai failed: {e}")
            return False
    
    # ==================== ELEVENLABS (Best Quality) ====================
    
    def generate_audio_elevenlabs(
        self, 
        text: str, 
        output_path: str,
        voice_id: str = "21m00Tcm4TlvDq8ikWAM",  # 'Rachel' - popular choice
        model: str = "eleven_multilingual_v2",
        stability: float = 0.5,
        similarity_boost: float = 0.75
    ) -> bool:
        """
        Generate audio using ElevenLabs (best quality AI voice)
        
        Popular voices:
        - 21m00Tcm4TlvDq8ikWAM: Rachel (female, professional)
        - AZnzlk1XvdvUeBnXmlld: Domi (male, energetic)
        - EXAVITQu4vr4xnSDxMaL: Bella (female, friendly)
        - ErXwobaYiL0O5jq8VWTr: Antoni (male, calm)
        
        Pricing: ~$0.30 per minute of generated audio
        """
        try:
            print(f"🎙️ ElevenLabs: {text[:40]}...")
            
            api_key = self.config.get('elevenlabs', {}).get('api_key')
            if not api_key:
                print("   ⚠️  ElevenLabs API key not configured")
                return False
            
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            headers = {
                "xi-api-key": api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "model_id": model,
                "voice_settings": {
                    "stability": stability,
                    "similarity_boost": similarity_boost
                }
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ ElevenLabs voice generated (voice: {voice_id})")
                return True
            else:
                print(f"   ⚠️  ElevenLabs API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  ElevenLabs failed: {e}")
            return False
    
    # ==================== OPENAI TTS (Good Value) ====================
    
    def generate_audio_openai(
        self, 
        text: str, 
        output_path: str,
        voice: str = "alloy",
        model: str = "tts-1-hd"
    ) -> bool:
        """
        Generate audio using OpenAI TTS
        
        Voice options:
        - alloy: Neutral, professional
        - echo: Male, deep
        - fable: British accent
        - onyx: Male, very deep
        - nova: Female, friendly
        - shimmer: Female, bright
        
        Pricing: ~$0.15 per minute (tts-1-hd)
        """
        try:
            print(f"🎙️ OpenAI TTS: {text[:40]}...")
            
            from openai import OpenAI
            
            api_key = self.config.get('openai', {}).get('api_key')
            if not api_key:
                print("   ⚠️  OpenAI API key not configured")
                return False
            
            client = OpenAI(api_key=api_key)
            
            response = client.audio.speech.create(
                model=model,
                voice=voice,
                input=text
            )
            
            response.stream_to_file(output_path)
            print(f"   ✅ OpenAI voice generated (voice: {voice})")
            return True
            
        except Exception as e:
            print(f"   ⚠️  OpenAI TTS failed: {e}")
            return False
    
    # ==================== PLAY.HT (Natural/Celebrity Voices) ====================
    
    def generate_audio_playht(
        self, 
        text: str, 
        output_path: str,
        voice_id: str = "s3://voice-cloning/zero_shot_thoughts/6048d4bb-d932-45b4-a9f2-c8700990748e/jennifer/manifest.json"
    ) -> bool:
        """
        Generate audio using Play.ht (natural voices, celebrity options)
        
        Popular voices:
        - Jennifer (professional female)
        - Matthew (professional male)
        - Many celebrity voices available
        
        Pricing: Freemium + paid tiers
        """
        try:
            print(f"🎙️ Play.ht: {text[:40]}...")
            
            api_key = self.config.get('playht', {}).get('api_key')
            user_id = self.config.get('playht', {}).get('user_id')
            if not api_key or not user_id:
                print("   ⚠️  Play.ht credentials not configured")
                return False
            
            url = "https://api.play.ht/api/v2/tts"
            
            headers = {
                "AUTHORIZATION": api_key,
                "X-USER-ID": user_id,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "voice": voice_id,
                "output_format": "mp3",
                "quality": "high"
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                # Play.ht returns async, need to poll for completion
                # For now, return False to fallback
                print(f"   ⚠️  Play.ht async download not implemented")
                return False
            else:
                print(f"   ⚠️  Play.ht API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Play.ht failed: {e}")
            return False
    
    # ==================== CARTES.AI (Ultra-Realistic) ====================
    
    def generate_audio_cartes(
        self, 
        text: str, 
        output_path: str,
        voice_id: str = "79a125e8-cd45-4c13-8a67-1888f38bdcd9",  # 'Will'
        model: str = "turbo"
    ) -> bool:
        """
        Generate audio using Cartes.ai (newest, ultra-realistic)
        
        Very new service, exceptional quality
        Pricing: Competitive
        """
        try:
            print(f"🎙️ Cartes.ai: {text[:40]}...")
            
            api_key = self.config.get('cartes', {}).get('api_key')
            if not api_key:
                print("   ⚠️  Cartes.ai API key not configured")
                return False
            
            url = f"https://api.cartes.ai/v1/audio/speech"
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": model,
                "input": text,
                "voice": voice_id
            }
            
            response = requests.post(url, json=data, headers=headers)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"   ✅ Cartes.ai voice generated (voice: {voice_id})")
                return True
            else:
                print(f"   ⚠️  Cartes.ai API error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"   ⚠️  Cartes.ai failed: {e}")
            return False
    
    # ==================== MAIN GENERATION FUNCTION ====================
    
    def generate_audio(
        self,
        text: str,
        output_path: str,
        preferred_service: str = None,
        fallback_chain: list = None
    ) -> bool:
        """
        Generate audio with intelligent fallback chain
        
        Args:
            text: Text to convert to speech
            output_path: Where to save the audio file
            preferred_service: 'hume', 'elevenlabs', 'openai', 'cartes', or None (auto)
            fallback_chain: List of services to try in order
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Check if already exists
        if os.path.exists(output_path):
            print(f"   ✅ Audio already exists: {output_path}")
            return True
        
        # Default fallback chain
        if fallback_chain is None:
            fallback_chain = self.config.get('voice', {}).get('fallback_chain', [
                'elevenlabs',
                'hume',
                'openai',
                'cartes',
                'gtts'
            ])
        
        # If preferred service specified, try it first
        if preferred_service:
            fallback_chain = [preferred_service] + [s for s in fallback_chain if s != preferred_service]
        
        # Try each service in order
        for service in fallback_chain:
            print(f"\n🎙️ Attempting {service.upper()}...")
            
            success = False
            
            if service == 'hume':
                voice_id = self.config.get('voice', {}).get('hume_voice_id', 'drew')
                speed = self.config.get('voice', {}).get('hume_speed', 1.0)
                success = self.generate_audio_hume_enhanced(text, output_path, voice_id, speed)
            
            elif service == 'elevenlabs':
                voice_id = self.config.get('voice', {}).get('elevenlabs_voice_id', '21m00Tcm4TlvDq8ikWAM')
                stability = self.config.get('voice', {}).get('elevenlabs_stability', 0.5)
                success = self.generate_audio_elevenlabs(text, output_path, voice_id, stability=stability)
            
            elif service == 'openai':
                voice = self.config.get('voice', {}).get('openai_voice', 'nova')
                success = self.generate_audio_openai(text, output_path, voice)
            
            elif service == 'cartes':
                voice_id = self.config.get('voice', {}).get('cartes_voice_id', '79a125e8-cd45-4c13-8a67-1888f38bdcd9')
                success = self.generate_audio_cartes(text, output_path, voice_id)
            
            elif service == 'playht':
                voice_id = self.config.get('voice', {}).get('playht_voice_id', '')
                success = self.generate_audio_playht(text, output_path, voice_id)
            
            elif service == 'gtts':
                from gtts import gTTS
                print(f"🎙️ gTTS (fallback): {text[:40]}...")
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(output_path)
                print(f"   ✅ gTTS voice generated")
                success = True
            
            if success:
                # Trim silence from successful generation
                self.trim_audio_silence(output_path)
                return True
            else:
                print(f"   ❌ {service.upper()} failed, trying next...")
        
        print(f"\n❌ All voice services failed!")
        return False
    
    def optimize_text_for_speech(self, text: str) -> str:
        """
        Optimize text for better TTS results
        
        - Add pauses with commas/periods
        - Expand abbreviations
        - Add emphasis hints
        - Fix pronunciation issues
        """
        # Common tech abbreviations to expand
        replacements = {
            'JS': 'JavaScript',
            'TS': 'TypeScript',
            'API': 'A.P.I.',
            'GitHub': 'GitHub',
            'VS Code': 'V.S. Code',
            'npm': 'N.P.M.',
            'yarn': 'Yarn',
            'AI': 'A.I.',
            'ML': 'Machine Learning',
            'DevOps': 'DevOps',
            'CI/CD': 'Continuous Integration Continuous Deployment',
            'SaaS': 'SaaS',
            'PaaS': 'PaaS',
            'IaaS': 'IaaS',
        }
        
        optimized = text
        for abbr, expansion in replacements.items():
            optimized = optimized.replace(abbr, expansion)
        
        # Add pauses before important points
        optimized = optimized.replace('. ', '. *pause* ')
        
        # Add emphasis for excitement
        optimized = optimized.replace('!', '! *excited*')
        
        return optimized


# Convenience functions for backward compatibility
def generate_audio_enhanced(text, output_path, preferred_service=None):
    """Generate audio with enhanced voice options"""
    generator = EnhancedVoiceGenerator()
    return generator.generate_audio(text, output_path, preferred_service)


if __name__ == "__main__":
    # Test the enhanced voice generator
    generator = EnhancedVoiceGenerator()
    
    test_text = "Welcome back to OpenSourceScribes! Today we're exploring an incredible new tool that will change how you work with GitHub repositories."
    
    print("="*60)
    print("ENHANCED VOICE GENERATOR TEST")
    print("="*60)
    print(f"\nTest text: {test_text}\n")
    
    # Test with different services
    print("\n" + "="*60)
    print("Testing voice generation services...")
    print("="*60)
    
    # Try with configured fallback chain
    success = generator.generate_audio(
        test_text,
        "test_enhanced_voice.mp3",
        preferred_service=None  # Use fallback chain from config
    )
    
    if success:
        print("\n✅ SUCCESS! Audio generated: test_enhanced_voice.mp3")
        print("   Play it to hear the quality difference!")
    else:
        print("\n❌ All services failed. Check your API keys.")
