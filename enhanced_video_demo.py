"""
Enhanced Video Demo Script
Demonstrates the new MiniMax-integrated video generation with:
- Animated code snippets
- UI demonstrations  
- GitHub page scrolling
- Dynamic content
"""

import os
import asyncio
import json
from pathlib import Path
from minimax_integration import get_minimax_generator
from github_page_capture import GitHubPageCapture
from video_suite import VideoSuite


async def demo_minimax_basic():
    """Demonstrate basic MiniMax text-to-video generation"""
    print("\n" + "="*60)
    print("🎬 MINIMAX BASIC DEMO")
    print("="*60)
    
    generator = get_minimax_generator()
    
    # Test UI demonstration
    test_prompt = "A smooth professional interface demonstrating a modern developer tool with clean animations and intuitive controls"
    
    print("\n1️⃣  Generating UI demonstration...")
    result = generator.generate_ui_demonstration(test_prompt, "demo_ui.mp4")
    
    if result:
        print(f"   ✅ Demo UI video: {result}")
    
    # Test code animation
    test_code = "import numpy as np\n\ndef process_data(input_array):\n    # Transform and normalize data\n    result = input_array * 2\n    return np.where(result > 0, result, 0)"
    
    print("\n2️⃣  Generating code animation...")
    result = generator.generate_code_animation(test_code, "python", "demo_code.mp4")
    
    if result:
        print(f"   ✅ Code animation: {result}")


async def demo_github_capture():
    """Demonstrate GitHub page capture with scrolling"""
    print("\n" + "="*60)
    print("🎬 GITHUB CAPTURE DEMO")
    print("="*60)
    
    capturer = GitHubPageCapture()
    
    # Test URL
    test_url = "https://github.com/mrdoob/three.js"
    
    print(f"\nCapturing sections from: {test_url}")
    
    # Capture overview
    print("\n1️⃣  Capturing overview...")
    overview = capturer.capture_github_overview(test_url)
    if overview:
        print(f"   ✅ Overview: {overview}")
    
    # Capture features
    print("\n2️⃣  Capturing features...")
    features = capturer.capture_features_section(test_url)
    if features:
        print(f"   ✅ Features: {features}")
    
    # Capture issues
    print("\n3️⃣  Capturing issues...")
    issues = capturer.capture_issues_section(test_url)
    if issues:
        print(f"   ✅ Issues: {issues}")


async def demo_enhanced_workflow():
    """Demonstrate the complete enhanced video workflow"""
    print("\n" + "="*60)
    print("🎬 ENHANCED VIDEO SUITE DEMO")
    print("="*60)
    
    # Create a test project
    test_project = {
        'id': 'demo_test_repo',
        'name': 'Test Project',
        'github_url': 'https://github.com/mrdoob/three.js',
        'script_text': 'A powerful JavaScript 3D library that makes WebGL accessible and easy to use. Three.js provides a complete scene graph, post-processing effects, and utilities for creating stunning 3D experiences on the web.',
        'metadata': {
            'stars': 100000,
            'language': 'JavaScript'
        }
    }
    
    # Load existing projects if available
    try:
        with open('posts_data.json', 'r') as f:
            projects = json.load(f)
            if projects:
                test_project = projects[0]
                print(f"\n📋 Using first project from posts_data.json: {test_project['name']}")
    except:
        pass
    
    # Initialize video suite
    suite = VideoSuite()
    
    # 1. Generate MiniMax enhanced content
    print("\n1️⃣  Generating MiniMax enhanced video content...")
    enhanced_video = await suite.generate_minimax_enhancement(test_project)
    
    if enhanced_video:
        print(f"   ✅ Enhanced video: {enhanced_video}")
    else:
        print("   ⚠️  MiniMax not available or disabled")
    
    # 2. Generate GitHub captures and code animations
    print("\n2️⃣  Generating GitHub captures and code animations...")
    captures = await suite.generate_captures_and_code_animations(test_project)
    
    if captures:
        print(f"   ✅ Generated {len(captures)} section captures")
    
    print("\n" + "="*60)
    print("✅ ENHANCED DEMO COMPLETE")
    print("="*60)
    print("\nGenerated assets:")
    for file in Path("assets").glob("*demo*.mp4"):
        print(f"   📹 {file.name}")
    
    for file in Path("assets/github_captures").glob("*.mp4"):
        print(f"   📹 github_captures/{file.name}")


async def main():
    """Main demo orchestration"""
    print("\n🎬 ENHANCED VIDEO GENERATION SYSTEM")
    print("  Demonstrating MiniMax integration for engaging videos")
    print("="*60)
    
    # Create assets directory
    Path("assets").mkdir(exist_ok=True)
    Path("assets/github_captures").mkdir(exist_ok=True)
    
    # Ask user which demo to run
    print("\nAvailable Demos:")
    print("  1. MiniMax Basic (UI demos, code animations)")
    print("  2. GitHub Page Capture (scrolling animations)")  
    print("  3. Complete Enhanced Workflow")
    print("  4. All Demos")
    
    choice = input("\nSelect demo (1-4, default=3): ").strip() or '3'
    
    if choice == '1':
        await demo_minimax_basic()
    elif choice == '2':
        await demo_github_capture()
    elif choice == '3':
        await demo_enhanced_workflow()
    elif choice == '4':
        await demo_minimax_basic()
        await demo_github_capture()
        await demo_enhanced_workflow()
    
    print("\n\n🎉 Demo complete! Check the assets/ folder for generated videos.")


if __name__ == "__main__":
    asyncio.run(main())
