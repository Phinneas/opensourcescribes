"""
Master Workflow Manager for OpenSourceScribes
Orchestrates the full pipeline: Scripts -> Videos -> Blogs -> Social -> Delivery
"""

import subprocess
import os
import sys
from datetime import datetime

def run_step(name, command):
    print(f"\n{'='*60}")
    print(f"🚀 STEP: {name}")
    print(f"{'='*60}")
    
    try:
        # Using shell=True to handle potential path/environment issues in this setup
        result = subprocess.run(command, shell=True, check=True)
        print(f"✅ {name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} failed with exit code {e.returncode}")
        return False

def main():
    start_time = datetime.now()
    # Lock the date for the entire batch to avoid splits at midnight
    batch_date = start_time.strftime("%m-%d")
    os.environ["DELIVERY_DATE"] = batch_date
    
    print(f"🎬 Starting Full OpenSourceScribes Pipeline at {start_time}")
    
    python_exe = sys.executable
    
    # Define the sequence of operations
    steps = [
        # 1. Data Generation
        ("Generating Scripts & Metadata", f"{python_exe} auto_script_generator.py --input github_urls.txt --output posts_data.json"),
        
        # 2. Video Production (This saves posts_data_longform.json used by others)
        ("Producing Videos (Main + Shorts)", f"{python_exe} video_automated.py"),
        
        # 3. Written Content (Parallelizable, but running sequentially for cleaner logs)
        ("Generating Medium Post", f"{python_exe} generate_medium_post.py"),
        ("Generating Reddit Post", f"{python_exe} generate_reddit_post.py"),
        ("Generating Substack Newsletter", f"{python_exe} generate_newsletter.py"),
        
        # 4. Final Metadata
        ("Generating YouTube Description", f"{python_exe} generate_description.py")
    ]
    
    success_count = 0
    for name, cmd in steps:
        if run_step(name, cmd):
            success_count += 1
        else:
            print(f"⚠️  Workflow interrupted at {name}. Continuing with next steps if possible...")
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "#"*60)
    print(f"🏁 WORKFLOW SUMMARY")
    print("#"*60)
    print(f"Started:  {start_time.strftime('%H:%M:%S')}")
    print(f"Finished: {end_time.strftime('%H:%M:%S')}")
    print(f"Duration: {duration}")
    print(f"Steps:    {success_count}/{len(steps)} successful")
    
    current_date = datetime.now().strftime("%m-%d")
    print(f"\n📂 All deliverables are in: /deliveries/{current_date}/")
    print("#"*60)

if __name__ == "__main__":
    main()
