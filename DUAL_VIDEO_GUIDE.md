# Dual Video Creator Guide

## Overview

The **Dual Video Creator** generates both a longform video AND YouTube Shorts **simultaneously** from your `github_urls.txt` file. 

### Key Difference from Before

**❌ Old approach:** Extract Shorts from existing main video (summary clips)  
**✅ New approach:** Create separate Shorts from randomly selected projects (independent content)

## How It Works

### URL Distribution

```
github_urls.txt (10 URLs)
         ↓
    Random Shuffle
         ↓
    ┌────────┴────────┐
    ↓                 ↓
Shorts (2 URLs)   Longform (8 URLs)
    ↓                 ↓
Short Video 1     Longform Video
Short Video 2     (with all 8 projects)
    ↓
Compilation Reel
```

### Example Workflow

**Input:** `github_urls.txt` with 10 project URLs

**Output:**
```
github_roundup_jan14.mp4        # Longform: 8 projects
shorts/short_000.mp4             # Short #1: Project A
shorts/short_001.mp4             # Short #2: Project B
github_shorts_jan14.mp4          # Compilation: Both Shorts
```

### Random Selection

Each time you run the script, it **randomly selects** different URLs for Shorts:

```
Run 1: Shorts = [project-3, project-7]
Run 2: Shorts = [project-1, project-5]
Run 3: Shorts = [project-8, project-2]
```

**This ensures variety** - you get different Shorts each time!

## Usage

### Basic Usage

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes
python video_maker_with_shorts.py
```

### Interactive Prompts

```
🎬 Dual Video Creator - Longform + Shorts
============================================================

How many YouTube Shorts to create? (default=2): 2

📱 Configuration:
   YouTube Shorts: 2
   Longform video: All remaining projects
```

### Output Example

```
🎬 Dual Video Creator for OpenSourceScribes
============================================================

📊 URL Distribution:
   Total URLs: 10
   Shorts: 2
   Longform: 8

🎲 Randomly selected for Shorts:
   1. https://github.com/owner/project-three
   2. https://github.com/owner/project-seven

📝 Creating project data...
   Shorts: 2 projects
   Longform: 8 projects

🎨 Generating graphics and audio...
🎙️ Hume.ai: Project-three is an incredible...
   ✅ Hume.ai audio generated
🎨 Creating Shorts graphic: project-three
   ✅ Shorts graphic saved
[... repeats for all projects ...]

🎬 Assembling videos...

============================================================
✅ Both videos created successfully!

📹 Longform Video:
   - github_roundup_jan14.mp4
   - 8 projects

📱 YouTube Shorts:
   - github_shorts_jan14.mp4 (compilation)
   - shorts/short_000.mp4
   - shorts/short_001.mp4

🎉 Ready to upload!
============================================================
```

## Video Specifications

### Longform Video (16:9 Horizontal)
- **Resolution:** 1920x1080
- **Format:** Standard YouTube video
- **Duration:** Depends on number of projects (typically 5-15 minutes)
- **Content:** All projects not selected for Shorts
- **Graphics:** Horizontal Code Stream branding
- **Voice:** Hume.ai "Comforting Male Conversationalist"

### YouTube Shorts (9:16 Vertical)
- **Resolution:** 1080x1920
- **Format:** YouTube Shorts (also works on TikTok/Instagram)
- **Duration:** ~30-45 seconds per Short
- **Content:** Randomly selected projects (independent from longform)
- **Graphics:** Vertical Code Stream branding
- **Voice:** Same Hume.ai voice

## URL Allocation Rules

### Smart Distribution

The script automatically balances URLs:

```
Total URLs | Shorts | Longform
-----------|--------|----------
5 URLs     | 2      | 3
10 URLs    | 2      | 8
15 URLs    | 3      | 12
20 URLs    | 4      | 16
```

### Rules

1. **Minimum 2 Shorts** - Ensures variety
2. **Minimum 3 longform** - Ensures main video has substance
3. **Maximum 5 Shorts** - Prevents over-fragmentation
4. **Random selection** - Different projects each run

### Manual Control

Edit `video_maker_with_shorts.py` line 265:

```python
# Default: User input
num_shorts = int(input("How many Shorts? ").strip() or "2")

# Always create 3 Shorts
num_shorts = 3

# Always create 1 Short
num_shorts = 1
```

## Customization

### Change Default Script

The default script is very basic. Edit line 115:

```python
# Current
'script_text': f"{project_name} is an incredible open source project. Check it out on GitHub!"

# More descriptive
'script_text': f"Check out {project_name}! This amazing open source project is making waves in the developer community. Link in the description!"

# Short & punchy
'script_text': f"You need to see {project_name}! This open source tool is incredible. #opensource #github"
```

### Use posts_data.json for Scripts

If you want custom scripts for each project, edit line 115 to read from JSON:

```python
def create_project_data_for_urls(self, urls, prefix='p'):
    projects = []
    
    # Load existing scripts
    with open('posts_data.json', 'r') as f:
        existing_data = json.load(f)
    
    # Map URLs to scripts
    script_map = {p['github_url']: p['script_text'] for p in existing_data}
    
    for i, url in enumerate(urls):
        project_name = self.extract_project_name(url)
        
        # Use custom script if available, otherwise default
        script_text = script_map.get(url, f"{project_name} is an incredible open source project...")
        
        projects.append({
            'id': f'{prefix}{i+1}',
            'name': project_name,
            'github_url': url,
            'script_text': script_text
        })
    
    return projects
```

### Adjust Vertical Graphics Layout

Edit `create_shorts_graphic()` method (line 175):

```python
# Font sizes (line 210)
title_font = ImageFont.truetype("Arial Bold.ttf", 80)  # Increase to 90

# Positioning (line 206)
margin = 80  # Increase to 100 for more padding
title_y = 300  # Move to 400 to lower title

# Description lines (line 250)
for i, line in enumerate(lines[:3]):  # Change to [:2] for max 2 lines
```

### Change Shorts Compilation Behavior

Edit line 396:

```python
# Current: Always compile if >1 Short
if len(short_files) > 1:
    self.concatenate_segments(short_files, SHORTS_REEL, output_dir=SHORTS_FOLDER)

# Option 1: Never compile (individual files only)
# Comment out the compilation

# Option 2: Always compile (even 1 Short)
if len(short_files) >= 1:
    self.concatenate_segments(short_files, SHORTS_REEL, output_dir=SHORTS_FOLDER)
```

## Workflow Examples

### Workflow 1: Standard Production
```bash
# Run once, get both videos
python video_maker_with_shorts.py
   > Enter: 2

# Result:
# - github_roundup_jan14.mp4 (8 projects)
# - shorts/short_000.mp4 (project A)
# - shorts/short_001.mp4 (project B)
# - github_shorts_jan14.mp4 (compilation)
```

### Workflow 2: Multiple Shorts Runs
```bash
# First run: Get 2 Shorts + longform
python video_maker_with_shorts.py
   > Randomly selects: [project-3, project-7]

# Second run: Get 2 DIFFERENT Shorts + longform
python video_maker_with_shorts.py
   > Randomly selects: [project-1, project-5]

# Result: 4 unique Shorts, 2 longform videos
# Each run features different projects!
```

### Workflow 3: Maximize Shorts
```bash
# From 20 URLs, create 5 Shorts
python video_maker_with_shorts.py
   > Enter: 5

# Result:
# - Longform: 15 projects
# - Shorts: 5 individual projects
# - Compilation: All 5 Shorts combined
```

## File Structure

### Input Files
```
github_urls.txt          # List of GitHub project URLs
config.json              # Hume.ai API key, voice settings
```

### Output Files
```
opensourcescribes/
├── github_roundup_jan14.mp4          # Longform video
├── github_shorts_jan14.mp4           # Shorts compilation
├── assets/                           # Longform assets
│   ├── p1_screen.png
│   ├── p1_audio.mp3
│   ├── p2_screen.png
│   ├── p2_audio.mp3
│   └── ...
└── shorts/                           # Shorts assets
    ├── s1_short.png
    ├── s1_short_audio.mp3
    ├── s2_short.png
    ├── s2_short_audio.mp3
    ├── short_000.mp4                 # Individual Short #1
    ├── short_001.mp4                 # Individual Short #2
    └── ...
```

## Best Practices

### ✅ DO:
- **Use 2-3 Shorts** - Good balance without fragmenting content too much
- **Run multiple times** - Different random selections each time = variety
- **Upload individual Shorts** - Better for YouTube's algorithm
- **Use compilation for other platforms** - TikTok, Instagram Reels
- **Keep URLs fresh** - Update github_urls.txt regularly

### ❌ DON'T:
- **Request too many Shorts** - >5 Shorts fragments longform too much
- **Skip the compilation** - Useful for cross-platform posting
- **Forget to check randomness** - Same URLs might be selected occasionally
- **Upload compilation to YouTube** - Individual Shorts perform better
- **Ignore the longform** - Still your main content piece

## Comparison: Old vs New

### Old Approach (Extraction)
```
github_urls.txt → longform video → extract clips → Shorts
                       ↓
                 Already created
                       ↓
          Extracted from existing
```
**Pro:** One rendering pass  
**Con:** Shorts are just clips from main video (summary content)

### New Approach (Parallel Creation)
```
github_urls.txt
       ↓
   Split URLs
       ↓
┌──────┴──────┐
↓             ↓
Shorts    Longform
↓             ↓
Create      Create
↓             ↓
Independent  Independent
```
**Pro:** Shorts feature completely different projects  
**Con:** Two rendering passes (but runs in parallel)

## Advanced: Selective Shorts

### Manually Specify Shorts

Edit line 72 to use specific URLs:

```python
def split_urls(self, all_urls):
    """Manually select specific URLs for Shorts"""
    
    # Your chosen Short URLs
    short_urls = [
        'https://github.com/owner/specific-project-1',
        'https://github.com/owner/specific-project-2',
    ]
    
    # Everything else goes to longform
    longform_urls = [url for url in all_urls if url not in short_urls]
    
    print(f"\n📊 URL Distribution:")
    print(f"   Total URLs: {len(all_urls)}")
    print(f"   Shorts: {len(short_urls)} (manually selected)")
    print(f"   Longform: {len(longform_urls)}")
    
    return short_urls, longform_urls
```

### Priority-Based Selection

Add a `priority` field to your URLs:

```python
# In github_urls.txt, use comments:
https://github.com/owner/project-1  # priority:shorts
https://github.com/owner/project-2
https://github.com/owner/project-3  # priority:shorts
https://github.com/owner/project-4

# Then edit split_urls():
def split_urls(self, all_urls):
    short_urls = []
    longform_urls = []
    
    for url in all_urls:
        if 'priority:shorts' in url:
            # Extract clean URL
            clean_url = url.split('#')[0].strip()
            short_urls.append(clean_url)
        else:
            longform_urls.append(url)
    
    return short_urls, longform_urls
```

## Troubleshooting

### Issue: "Not enough URLs for longform"
**Solution:** You need at least 5 URLs total (2 for Shorts, 3 for longform)

### Issue: "Same projects selected every time"
**Solution:** Random means occasional repeats. Run again for different selection.

### Issue: "Shorts graphics look stretched"
**Solution:** Check `create_shorts_graphic()` - ensure width=1080, height=1920

### Issue: "Audio out of sync"
**Solution:** Check that silence trimming is working (line 160)

### Issue: "Hume.ai quota exceeded"
**Solution:** Script falls back to gTTS automatically

### Issue: "Compilation video has wrong order"
**Solution:** Shorts are assembled in the order they were randomly selected

## Performance

### Rendering Times (Approximate)

| Total URLs | Shorts | Longform | Total Time |
|------------|--------|----------|------------|
| 5 URLs     | 2      | 3        | ~3 minutes |
| 10 URLs    | 2      | 8        | ~8 minutes |
| 15 URLs    | 3      | 12       | ~12 minutes |
| 20 URLs    | 4      | 16       | ~15 minutes |

**Note:** Graphics and audio generation happen in parallel, so it's faster than running twice!

### Storage Requirements

- **1 longform video (10 projects):** ~200-400 MB
- **1 Short:** ~8-15 MB
- **Compilation:** ~15-30 MB
- **Total (10 URLs + 2 Shorts):** ~250-450 MB

## Uploading Strategy

### Recommended Approach

1. **Upload longform video** to your main channel
2. **Upload individual Shorts** (not compilation) as Shorts
3. **Schedule strategically:**
   - Longform: Tuesday/Thursday (optimal for longer content)
   - Shorts: Daily spread (Mon, Wed, Fri)

### Title Templates

**Longform:**
```
"8 Incredible Open Source Projects You Need to Know (January 2025)"
"GitHub Roundup: Best New Developer Tools This Week"
"Top 10 Open Source Projects for [Month]"
```

**Shorts:**
```
"This Open Source Tool is INSANE! 🔥 #shorts"
"Best GitHub Discovery This Week! #opensource"
"You Need This Developer Tool! #shorts"
```

### Description Templates

**Longform:**
```
Discover the best open source projects this week!

🔗 Projects mentioned:
- Project 1: https://github.com/...
- Project 2: https://github.com/...
[... all projects ...]

👨‍💻 Voice: Hume.ai AI Text-to-Speech
🎨 Graphics: Custom Code Stream Branding

#opensource #github #developer #programming
```

**Shorts:**
```
Check out [Project Name]!

🔗 GitHub: [link]

Full roundup on our channel!

#opensource #github #developer #shorts
```

## Integration with Existing Workflows

### Before Dual Video Creator
```
github_urls.txt → video_maker.py → github_roundup_jan14.mp4
```

### After Dual Video Creator
```
github_urls.txt → video_maker_with_shorts.py
                                              ↓
                                ┌──────────────┴──────────────┐
                                ↓                             ↓
                    github_roundup_jan14.mp4         github_shorts_jan14.mp4
                    (8 projects, horizontal)         (2 projects, vertical)
```

### Replace Old Script?

**Option 1: Replace completely**
```bash
# Delete or rename old script
mv video_maker.py video_maker_old.py

# Use new script as default
python video_maker_with_shorts.py
```

**Option 2: Keep both**
```bash
# Use for different purposes:
video_maker.py              # When you only want longform
video_maker_with_shorts.py  # When you want both
```

## Future Enhancements

Possible improvements:
- [ ] Intelligent selection (pick most interesting projects for Shorts)
- [ ] Auto-generate better scripts based on GitHub description
- [ ] Add transitions between Shorts in compilation
- [ ] Background music option for Shorts
- [ ] Square format (1:1) for Facebook/LinkedIn
- [ ] Auto-upload via YouTube API
- [ ] A/B test different Short durations

## Quick Reference

### Commands

```bash
# Create both videos (default 2 Shorts)
python video_maker_with_shorts.py

# Create both videos (3 Shorts)
python video_maker_with_shorts.py
> Enter: 3

# Create only longform (use old script)
python video_maker.py
```

### File Locations

```
Longform video:    github_roundup_jan14.mp4
Shorts reel:       github_shorts_jan14.mp4
Individual Shorts: shorts/short_000.mp4, short_001.mp4, etc.
Assets:            assets/ (longform), shorts/ (shorts)
```

### Configuration

```python
# Number of Shorts
num_shorts = 2  # Default

# Default script text
script_text = f"{project_name} is an incredible open source project..."

# Voice
CONFIG['hume_ai']['use_hume'] = True
CONFIG['hume_ai']['voice_id'] = 'd35ae770-3c1c-4afd-9e1c-6e7e9ab84251'  # Conversationalist
```

---

**Happy video making! 🎬✨**

Remember: Each run creates DIFFERENT Shorts (random selection) for variety!
