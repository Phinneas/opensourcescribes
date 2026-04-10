#!/usr/bin/env python3
"""
Quick Audio Setup Verification Script
Tests all configured audio services in sequence
"""

import os
import sys
from enhanced_audio_generator import EnhancedVoiceGenerator

def test_audio_services():
    """Test all audio services and report status"""
    
    print("="*70)
    print("🔊 AUDIO SERVICE VERIFICATION")
    print("="*70)
    
    generator = EnhancedVoiceGenerator()
    
    test_text = "Welcome to OpenSourceScribes. Testing audio generation."
    output_file = "test_audio_verification.mp3"
    
    # Clean up old test file
    if os.path.exists(output_file):
        os.remove(output_file)
    
    print(f"\nTest text: {test_text}")
    print(f"Output file: {output_file}\n")
    
    # Test the full fallback chain
    print("Testing complete fallback chain...")
    print("-" * 70)
    
    success = generator.generate_audio(test_text, output_file)
    
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    if success:
        print(f"✅ SUCCESS! Audio generated: {output_file}")
        print(f"📊 File size: {os.path.getsize(output_file)} bytes")
        
        # Try to play the file (macOS)
        if sys.platform == "darwin":
            print(f"\n🔊 Playing audio...")
            os.system(f"afplay {output_file}")
        elif sys.platform == "linux":
            print(f"\n🔊 Playing audio...")
            os.system(f"mpg321 {output_file} 2>/dev/null || aplay {output_file} 2>/dev/null")
        elif sys.platform == "win32":
            print(f"\n🔊 Playing audio...")
            os.system(f"start {output_file}")
            
    else:
        print("❌ FAILED! All audio services failed.")
        print("\nTroubleshooting:")
        print("1. Check config.json has correct API keys")
        print("2. Verify KittenTTS is running (if using): kittentts-server")
        print("3. Check internet connection")
        print("4. Review error messages above")
    
    print("\n" + "="*70)
    print("SERVICE STATUS CHECK")
    print("="*70)
    
    # Check config for each service
    config = generator.config
    
    services = [
        ("minimax", "api_key"),
        ("hume_ai", "api_key"),
        ("openai", "api_key"),
        ("kittentts", "base_url"),
    ]
    
    for service_name, key_name in services:
        service_config = config.get(service_name, {})
        if key_name in service_config and service_config[key_name]:
            if "YOUR" in str(service_config[key_name]) or not service_config[key_name]:
                print(f"⚠️  {service_name.upper()}: Configured but needs setup")
            else:
                print(f"✅ {service_name.upper()}: Configured")
        else:
            print(f"❌ {service_name.upper()}: Not configured")
    
    print("\n" + "="*70)
    print("CURRENT FALLBACK CHAIN")
    print("="*70)
    
    fallback_chain = config.get('voice', {}).get('fallback_chain', [])
    if fallback_chain:
        for i, service in enumerate(fallback_chain, 1):
            print(f"{i}. {service.upper()}")
    else:
        print("1. MINIMAX")
        print("2. HUME")
        print("3. OPENAI")
        print("4. KITTENTTS")
        print("5. GTTS")
    
    print("\n" + "="*70)
    print("RECOMMENDED SETUP")
    print("="*70)
    print("✅ Primary: Minimax (uses video tokens)")
    print("✅ Fallback 1: Hume.ai (paid, reliable)")
    print("✅ Fallback 2: OpenAI TTS (paid, good value)")
    print("✅ Free Option: KittenTTS (self-hosted)")
    print("✅ Emergency: gTTS (always works)")
    print("\n📖 See AUDIO_SETUP_GUIDE.md for detailed instructions")
    print("="*70)

if __name__ == "__main__":
    test_audio_services()
