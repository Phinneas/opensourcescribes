"""
Start video generation with MiniMax for your GitHub projects
"""

import asyncio
from video_suite import VideoSuite
import json


async def main():
    """Main workflow"""
    print("\n" + "="*70)
    print("🎬 MINIMAX-ENHANCED VIDEO PRODUCTION")
    print("="*70)
    print("\nThis will:")
    print("  1. Generate scripts for your GitHub projects")
    print("  2. Create MiniMax-enhanced videos (AI-generated visuals)")
    print("  3. Capture scrolling GitHub pages")
    print("  4. Assemble professional videos")
    print("\nNote: Each project takes 2-5 minutes")
    print("      MiniMax cost: ~$0.10-0.20 per project video")
    print("\n" + "="*70)
    
    # Initialize video suite
    suite = VideoSuite()
    
    # Load projects
    suite.load_projects()
    
    print(f"\n📋 Found {len(suite.projects)} projects to process")
    print("\nProjects:")
    for i, p in enumerate(suite.projects[:5], 1):
        print(f"   {i}. {p['name']}")
    if len(suite.projects) > 5:
        print(f"   ... and {len(suite.projects) - 5} more")
    
    # Interactive selection for Shorts
    suite.select_shorts()
    
    # Interactive selection for Deep Dives
    suite.select_deep_dives()
    
    # Confirm
    confirm = input("\n🎯 Start video generation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Cancelled")
        return
    
    # Save project data
    with open('posts_data_longform.json', 'w') as f:
        json.dump(suite.projects, f, indent=4)
    
    # Generate videos
    print("\n🎬 Starting video generation...")
    print("   This will take 15-40 minutes depending on MiniMax usage")
    
    await suite.run()


if __name__ == "__main__":
    print("\nNote: Make sure config.json has your MiniMax API key configured")
    print("      and your account has sufficient credits.\n")
    
    asyncio.run(main())
