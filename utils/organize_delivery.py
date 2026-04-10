"""
Delivery Organizer
Organizes video deliverables into dated folders (MM-DD format).

Usage:
    python organize_delivery.py              # Auto-detect latest delivery
    python organize_delivery.py 01-26        # Organize to specific date folder
    python organize_delivery.py --from jan26 # Organize from specific source folder
"""

import os
import shutil
import sys
import glob
import re
from datetime import datetime
from pathlib import Path

# Base directories
PROJECT_ROOT = Path(__file__).parent
DELIVERIES_ROOT = PROJECT_ROOT / "deliveries"


def get_current_date_folder():
    """Get folder name in MM-DD format for today"""
    return datetime.now().strftime("%m-%d")


def find_latest_delivery_folder():
    """Find the most recent delivery_* folder"""
    pattern = PROJECT_ROOT / "delivery_*"
    folders = glob.glob(str(pattern))
    
    if not folders:
        return None
    
    # Sort by modification time, most recent first
    folders.sort(key=os.path.getmtime, reverse=True)
    return Path(folders[0])


def find_deep_dive_videos():
    """Find extended/focused project videos in root"""
    deep_dives = []
    
    patterns = ["*_extended.mp4", "*_focused.mp4"]
    for pattern in patterns:
        deep_dives.extend(glob.glob(str(PROJECT_ROOT / pattern)))
    
    return [Path(p) for p in deep_dives]


def parse_delivery_date(folder_name):
    """Extract date from delivery folder name like 'delivery_jan26'"""
    match = re.search(r'delivery_(\w{3})(\d{1,2})', folder_name)
    if match:
        month_str, day = match.groups()
        months = {
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
            'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
            'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        month = months.get(month_str.lower(), '01')
        return f"{month}-{int(day):02d}"
    return None


def organize_delivery(source_folder=None, target_date=None):
    """
    Organize deliverables into a dated folder.
    
    Args:
        source_folder: Path to source delivery folder (auto-detect if None)
        target_date: Target folder name in MM-DD format (auto-detect if None)
    """
    # Find source folder
    if source_folder is None:
        source_folder = find_latest_delivery_folder()
        if source_folder is None:
            print("No delivery_* folder found.")
            return False
    else:
        source_folder = Path(source_folder)
        if not source_folder.exists():
            source_folder = PROJECT_ROOT / f"delivery_{source_folder}"
            if not source_folder.exists():
                print(f"Source folder not found: {source_folder}")
                return False
    
    print(f"Source: {source_folder}")
    
    # Determine target date
    if target_date is None:
        target_date = parse_delivery_date(source_folder.name)
        if target_date is None:
            target_date = get_current_date_folder()
    
    # Create target folder
    target_folder = DELIVERIES_ROOT / target_date
    target_folder.mkdir(parents=True, exist_ok=True)
    print(f"Target: {target_folder}")
    
    # Track what we organize
    organized = {
        'longform': None,
        'description': None,
        'shorts': [],
        'deep_dives': []
    }
    
    # 1. Move longform video
    longform_patterns = ["github_roundup_*.mp4", "roundup_*.mp4"]
    for pattern in longform_patterns:
        for video in source_folder.glob(pattern):
            dest = target_folder / "longform_github_roundup.mp4"
            shutil.move(str(video), str(dest))
            organized['longform'] = dest
            print(f"  Moved longform: {video.name}")
            break
    
    # 2. Move YouTube description
    desc_file = source_folder / "YOUTUBE_DESCRIPTION.md"
    if desc_file.exists():
        dest = target_folder / "YOUTUBE_DESCRIPTION.md"
        shutil.move(str(desc_file), str(dest))
        organized['description'] = dest
        print(f"  Moved description: YOUTUBE_DESCRIPTION.md")
    
    # 3. Move shorts folder
    shorts_source = source_folder / "shorts"
    if shorts_source.exists() and shorts_source.is_dir():
        shorts_dest = target_folder / "shorts"
        if shorts_dest.exists():
            shutil.rmtree(str(shorts_dest))
        shutil.move(str(shorts_source), str(shorts_dest))
        short_count = len(list(shorts_dest.glob("short_*.mp4")))
        organized['shorts'] = list(shorts_dest.glob("short_*.mp4"))
        print(f"  Moved shorts folder: {short_count} videos")
    
    # 4. Find and move deep dive videos (from project root)
    deep_dives = find_deep_dive_videos()
    if deep_dives:
        deep_dive_folder = target_folder / "deep_dives"
        deep_dive_folder.mkdir(exist_ok=True)
        
        for video in deep_dives:
            dest = deep_dive_folder / video.name
            shutil.move(str(video), str(dest))
            organized['deep_dives'].append(dest)
            print(f"  Moved deep dive: {video.name}")
    
    # 5. Clean up source folder if empty
    try:
        # Remove any remaining empty subdirs
        for item in source_folder.iterdir():
            if item.is_dir() and not any(item.iterdir()):
                item.rmdir()
        
        # Remove source if empty
        if not any(source_folder.iterdir()):
            source_folder.rmdir()
            print(f"  Cleaned up empty source folder")
    except OSError:
        pass
    
    # Summary
    print("\n" + "=" * 50)
    print(f"DELIVERY ORGANIZED: {target_date}")
    print("=" * 50)
    print(f"  Location: {target_folder}")
    print(f"  Longform: {'Yes' if organized['longform'] else 'No'}")
    print(f"  Description: {'Yes' if organized['description'] else 'No'}")
    print(f"  Shorts: {len(organized['shorts'])} videos")
    print(f"  Deep Dives: {len(organized['deep_dives'])} videos")
    
    return True


def list_deliveries():
    """List all organized deliveries"""
    if not DELIVERIES_ROOT.exists():
        print("No deliveries folder found.")
        return
    
    print("\nOrganized Deliveries:")
    print("=" * 50)
    
    for folder in sorted(DELIVERIES_ROOT.iterdir()):
        if folder.is_dir() and re.match(r'\d{2}-\d{2}', folder.name):
            longform = folder / "longform_github_roundup.mp4"
            shorts_dir = folder / "shorts"
            deep_dives_dir = folder / "deep_dives"
            desc = folder / "YOUTUBE_DESCRIPTION.md"
            
            short_count = len(list(shorts_dir.glob("short_*.mp4"))) if shorts_dir.exists() else 0
            deep_dive_count = len(list(deep_dives_dir.glob("*.mp4"))) if deep_dives_dir.exists() else 0
            
            status = []
            if longform.exists():
                status.append("longform")
            if desc.exists():
                status.append("description")
            if short_count > 0:
                status.append(f"{short_count} shorts")
            if deep_dive_count > 0:
                status.append(f"{deep_dive_count} deep dives")
            
            print(f"  {folder.name}: {', '.join(status) if status else 'empty'}")


def main():
    args = sys.argv[1:]
    
    if not args:
        # Auto-organize latest delivery
        organize_delivery()
    elif args[0] == "--list":
        list_deliveries()
    elif args[0] == "--from" and len(args) > 1:
        organize_delivery(source_folder=args[1])
    elif args[0] == "--help":
        print(__doc__)
    else:
        # Assume it's a target date
        organize_delivery(target_date=args[0])


if __name__ == "__main__":
    main()
