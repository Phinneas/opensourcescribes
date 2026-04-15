#!/usr/bin/env python3
"""
One-command full pipeline: Discovery → Scripts → Videos → Content
Usage: python run_full_pipeline.py
"""

import sys
import os
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

def run_step(name, command, cwd=None):
    """Run a pipeline step with clear feedback"""
    print(f"\n{'='*60}")
    print(f"🚀 {name}")
    print(f"{'='*60}")
    
    cmd_list = command.split() if isinstance(command, str) else command
    # Replace 'python' with current Python executable
    if cmd_list and cmd_list[0] == 'python':
        cmd_list[0] = sys.executable
    
    print(f"Running: {' '.join(cmd_list)}")
    
    if cwd is None:
        cwd = Path(__file__).parent
    
    result = subprocess.run(
        cmd_list,
        cwd=cwd,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ FAILED: {name}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        return False
    
    print(f"✅ COMPLETED: {name}")
    return True

def main():
    print("🎬 OPENSOURCE SCRIBES - FULL PIPELINE")
    print("="*60)
    
    project_root = Path(__file__).parent
    
    # Step 1: Discovery
    if not run_step(
        "STEP 1: Discover GitHub Repos",
        ["python", "-m", "discovery.exa_discovery"],
        cwd=project_root
    ):
        print("Discovery failed - stopping here")
        return
    
    # Step 2: Generate Scripts
    if not run_step(
        "STEP 2: Generate Narration Scripts", 
        ["python", "components/project/auto_script_generator.py", "--input", "github_urls.txt", "--output", "posts_data.json"],
        cwd=project_root
    ):
        print("Script generation failed - stopping here")
        return
    
    # Step 3: Full Video + Content Pipeline
    if not run_step(
        "STEP 3: Generate Videos & Content",
        ["python", "components/video/video_automated.py"],
        cwd=project_root
    ):
        print("Video pipeline failed")
        return
    
    print("\n" + "="*60)
    print("🎉 FULL PIPELINE COMPLETE!")
    print("="*60)
    print("✅ Disscovered repos")
    print("✅ Generated scripts")  
    print("✅ Created videos (longform + shorts + deep dives)")
    print("✅ Generated content (Medium + Reddit + Substack)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
