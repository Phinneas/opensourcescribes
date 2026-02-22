"""
Quick test to verify MiniMax video generation is working
"""

import os
from minimax_integration import get_minimax_generator


def test_minimax_video_generation():
    """Test actual video generation with MiniMax"""
    print("\n" + "="*60)
    print("🎬 Testing MiniMax Video Generation")
    print("="*60)
    
    generator = get_minimax_generator()
    
    if not generator.enabled:
        print("❌ MiniMax not enabled. Check your API key in config.json")
        return False
    
    print("\n📝 Generating test video...")
    print("   (This will take 30-60 seconds)")
    
    # Simple test prompt
    test_prompt = "A smooth modern coding interface showing a developer working with a dark theme IDE and colorful syntax highlighting"
    output_path = "test_minimax_video.mp4"
    
    result = generator.generate_text_to_video(test_prompt, output_path, duration=5)
    
    if result:
        print(f"\n✅ Test video created: {result}")
        if os.path.exists(result):
            size_mb = os.path.getsize(result) / (1024 * 1024)
            print(f"   Size: {size_mb:.2f} MB")
            return True
    else:
        print("\n❌ Video generation failed or timed out")
        print("   This could be due to:")
        print("   - Network connectivity issues")
        print("   - MiniMax API rate limits")
        print("   - Insufficient API credits")
        return False


if __name__ == "__main__":
    success = test_minimax_video_generation()
    
    if success:
        print("\n🎉 MiniMax is working! You can now generate enhanced videos.")
    else:
        print("\n⚠️  MiniMax test failed. Check your API key and try again.")
