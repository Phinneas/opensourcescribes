"""
Quick test script to verify MiniMax integration setup
"""

import os
import json
from pathlib import Path


def test_config():
    """Test config.json has required fields"""
    print("🔧 Testing config.json...")
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    # Check MiniMax section
    if 'minimax' in config:
        print("   ✅ MiniMax config section found")
        if config['minimax'].get('api_key'):
            print("   ✅ MiniMax API key present")
        else:
            print("   ⚠️  MiniMax API key missing - add to config.json to enable features")
    else:
        print("   ⚠️  MiniMax config section missing")
    
    # Check video_settings
    if 'video_settings' in config:
        if config['video_settings'].get('use_minimax'):
            print("   ✅ MiniMax enabled in video_settings")
        else:
            print("   ℹ️  MiniMax not enabled (set use_minimax: true)")


def test_modules():
    """Test that modules can be imported"""
    print("\n📦 Testing module imports...")
    
    try:
        from minimax_integration import get_minimax_generator
        print("   ✅ minimax_integration module")
        
        from github_page_capture import GitHubPageCapture
        print("   ✅ github_page_capture module")
        
        from video_suite import VideoSuite
        print("   ✅ video_suite module")
        
    except ImportError as e:
        print(f"   ❌ Import failed: {e}")


def test_dependencies():
    """Test external dependencies"""
    print("\n🔍 Checking dependencies...")
    
    # Test selenium
    try:
        import selenium
        print("   ✅ selenium available (browser capture)")
    except ImportError:
        print("   ⚠️  selenium not found - GitHub capture limited")
    
    # Test webkit2png
    try:
        subprocess.run(['webkit2png', '--version'], capture_output=True, check=False)
        print("   ✅ webkit2png available (macOS fallback)")
    except FileNotFoundError:
        print("   ⚠️  webkit2png not found - install with: brew install webkit2png")


def test_videosuite():
    """Test video suite initialization"""
    print("\n🎬 Testing VideoSuite initialization...")
    
    try:
        from video_suite import VideoSuite
        suite = VideoSuite()
        print("   ✅ VideoSuite initialized")
        
        if suite.use_minimax:
            print("   ✅ MiniMax integration enabled")
        else:
            print("   ℹ️  MiniMax disabled (will use static graphics)")
        
        if suite.minimax_generator:
            if suite.minimax_generator.enabled:
                print("   ✅ MiniMax video generator ready")
            else:
                print("   ℹ️  MiniMax API key not configured")
        
    except Exception as e:
        print(f"   ❌ VideoSuite failed: {e}")


def create_assets_dir():
    """Ensure assets directory exists"""
    Path("assets").mkdir(exist_ok=True)
    Path("assets/github_captures").mkdir(exist_ok=True)
    Path("deliveries").mkdir(exist_ok=True)


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 MINIMAX INTEGRATION TEST")
    print("="*60)
    
    # Create directories
    create_assets_dir()
    print("\n📁 Created/verified asset directories")
    
    # Run tests
    test_config()
    test_modules()
    test_dependencies()
    test_videosuite()
    
    print("\n" + "="*60)
    print("✅ TEST COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("1. Add MiniMax API key to config.json (if using MiniMax)")
    print("2. Run: python enhanced_video_demo.py to test features")
    print("3. Or run: python video_suite.py for production videos")
    print("\nDocumentation: See MINIMAX_ENHANCED_GUIDE.md")


if __name__ == "__main__":
    import subprocess
    main()
