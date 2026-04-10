"""
Check and download completed MiniMax video task
"""

import time
import json
from minimax_integration import get_minimax_generator


def download_completed_task(task_id: str = None):
    """Check task status and download if complete"""
    
    # Get generator
    generator = get_minimax_generator()
    
    # Use provided task ID or ask for it
    if not task_id:
        task_id = input("Enter MiniMax task ID: ").strip()
        if not task_id:
            print("❌ No task ID provided")
            return
    
    print(f"\n📡 Checking task: {task_id}")
    print("   (This may take 60-180 seconds for completion)")
    
    # Poll for completion
    video_url = generator._poll_task_completion(task_id, max_wait=300)
    
    if video_url:
        print(f"\n✅ Video is ready!")
        print(f"   Download URL: {video_url}")
        
        # Download
        output_path = "assets/completed_minimax_video.mp4"
        success = generator._download_video(video_url, output_path)
        
        if success:
            import os
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"\n🎉 Video downloaded successfully!")
            print(f"   File: {output_path}")
            print(f"   Size: {size_mb:.2f} MB")
        else:
            print("❌ Failed to download video")
    else:
        print("\n❌ Task failed or is still processing")
        print("   Try again in a few minutes")


if __name__ == "__main__":
    # Check if we have the task ID from the previous test
    print("MiniMax Video Task Status Checker")
    print("="*50)
    
    # Use the task ID from the earlier test
    task_id = "367622429188378"
    
    print(f"Using task ID: {task_id}")
    confirm = input("Press Enter to check, or type a different task ID: ").strip()
    
    if confirm:
        task_id = confirm
    
    download_completed_task(task_id)
