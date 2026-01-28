# Timestamped Shorts Extractor Guide

## Overview

The **Timestamped Shorts Extractor** creates multiple individual YouTube Shorts from your longform video using the timestamps in `YOUTUBE_DESCRIPTION.md`. 

### Key Difference

**❌ Old approach:** Randomly select projects for Shorts  
**✅ New approach:** Extract each project segment as an individual Short based on timestamps

## How It Works

### From Longform to Multiple Shorts

```
Longform Video (10 minutes)
├── 0:07 - lighthouse (29s)      → short_01_lighthouse.mp4
├── 0:36 - kosmos (42s)          → short_02_kosmos.mp4
├── 1:18 - pipelex (55s)         → short_03_pipelex.mp4
├── 2:13 - claude-code-router    → short_04_claude-code-router.mp4
├── 3:05 - shimmy (68s)          → short_05_shimmy.mp4
└── ... etc                      → ... etc
```

### Example from Your YOUTUBE_DESCRIPTION.md

```markdown
0:07 - **lighthouse**
🔗 https://github.com/submariner-io/lighthouse

0:36 - **kosmos**
🔗 https://github.com/kosmos-io/kosmos

1:18 - **pipelex**
🔗 https://github.com/pipelex/pipelex
```

**Extracts:**
```
short_01_lighthouse.mp4      (0:07 to 0:36 = 29 seconds)
short_02_kosmos.mp4          (0:36 to 1:18 = 42 seconds)
short_03_pipelex.mp4         (1:18 to 2:13 = 55 seconds)
```

## Usage

### Basic Workflow

```bash
# Step 1: Create your longform video (as usual)
python video_maker.py

# Step 2: Extract Shorts from timestamps
python extract_timestamped_shorts.py
```

### Interactive Prompts

```
📱 YouTube Shorts Extractor (Timestamp-Based)
============================================================
Extracts individual Shorts from YOUTUBE_DESCRIPTION.md timestamps

✅ Found video: github_roundup_jan14.mp4

📐 Choose conversion method:
   1. Center Crop (default) - Crops sides, keeps center focused
   2. Pillar Box - Scales down, adds side bars (keeps everything)

Enter choice (default=1): 1
```

### Output Example

```
📱 YouTube Shorts Extractor
============================================================
📹 Source video: github_roundup_jan14.mp4
📖 Description: YOUTUBE_DESCRIPTION.md
⏱️  Video duration: 480.5 seconds

📖 Parsing YOUTUBE_DESCRIPTION.md...
✅ Found 10 projects with timestamps

📋 Projects to extract:
   1. lighthouse
      Start: 0:07 | Duration: 29s
   2. kosmos
      Start: 0:36 | Duration: 42s
   3. pipelex
      Start: 1:18 | Duration: 55s
   [... etc ...]

🎬 Extracting 10 Shorts...
   Method: crop
============================================================

🎬 Creating Short: lighthouse
   ⏱️  Timestamp: 7s | Duration: 29s
   ✅ Short created: short_01_lighthouse.mp4

🎬 Creating Short: kosmos
   ⏱️  Timestamp: 36s | Duration: 42s
   ✅ Short created: short_02_kosmos.mp4

[... continues for all projects ...]

============================================================
✅ Extracted 10 YouTube Shorts!

📁 Shorts location: shorts/
📝 Upload guide: shorts/upload_list.txt

🎉 Ready to upload to YouTube!
============================================================
```

## Conversion Methods

### Method 1: Center Crop (Default)

**Best for:** Content with centered text/graphics

```
Before (1920x1080)          After (1080x1920)
┌─────────────────────┐      ┌──────┐
│  ████ cropped ████  │  →   │      │
│   ┌──────────┐      │      │ CROP │
│   │  KEEP    │      │      │ AREA │
│   │  CENTER  │      │      │      │
│   └──────────┘      │      │      │
│  ████ cropped ████  │      └──────┘
└─────────────────────┘
```

**Pros:**
- Text stays large and readable
- Focused on center content
- No black bars

**Cons:**
- Side content is cropped
- May cut off important elements

### Method 2: Pillar Box

**Best for:** Content with important elements on sides

```
Before (1920x1080)          After (1080x1920)
┌─────────────────────┐      ┌╌─────╌┐
│                     │      │║     ║│
│   ALL CONTENT       │  →   │║ FIT ║│
│   KEPT              │      │║     ║│
│                     │      │╌─────╌┘
└─────────────────────┘      └╌─────╌┘
   ║ = black bars
```

**Pros:**
- Everything visible
- No content loss
- Better for side-heavy layouts

**Cons:**
- Text appears smaller
- Black bars on sides
- Less "cinematic"

## YOUTUBE_DESCRIPTION.md Format

### Required Format

Your `YOUTUBE_DESCRIPTION.md` must follow this pattern:

```markdown
## ⏱️ **Timestamps & Links**

0:07 - **project-name**
🔗 https://github.com/owner/repo

0:36 - **another-project**
🔗 https://github.com/owner/repo2

1:18 - **third-project**
🔗 https://github.com/owner/repo3
```

### Pattern Requirements

✅ **Must have:**
- Timestamp in `MM:SS` format
- Project name in `**bold**`
- GitHub URL on next line with `🔗` prefix

❌ **Common mistakes:**
```
❌ 0:07 - project-name (missing bold)
❌ **0:07** - project-name (timestamp not bold)
❌ 0:07 - project-name (missing URL)
❌ 07 - **project-name** (missing colon)
```

### Valid Examples

```markdown
# ✅ Correct
0:07 - **lighthouse**
🔗 https://github.com/submariner-io/lighthouse

# ✅ Correct (with leading zero)
0:36 - **kosmos**
🔗 https://github.com/kosmos-io/kosmos

# ✅ Correct (double-digit minutes)
10:45 - **my-project**
🔗 https://github.com/owner/my-project
```

## Output Structure

### Files Created

```
opensourcescribes/
├── github_roundup_jan14.mp4          # Original longform
├── YOUTUBE_DESCRIPTION.md            # Source timestamps
└── shorts/
    ├── short_01_lighthouse.mp4       # Extracted Short #1
    ├── short_02_kosmos.mp4           # Extracted Short #2
    ├── short_03_pipelex.mp4          # Extracted Short #3
    ├── short_04_claude-code-router.mp4
    ├── short_05_shimmy.mp4
    ├── short_06_codebuff.mp4
    ├── short_07_eslint-plugin.mp4
    ├── short_08_handy.mp4
    ├── short_09_edge264.mp4
    ├── short_10_mirrord.mp4
    └── upload_list.txt               # Upload guide
```

### upload_list.txt

The script creates a helpful upload guide:

```
YouTube Shorts Upload List
========================================

1. lighthouse
   File: short_01_lighthouse.mp4
   Suggested Title: "lighthouse - Amazing Open Source Project! #shorts"
   Description: Check out lighthouse! 🔗 https://github.com/submariner-io/lighthouse

2. kosmos
   File: short_02_kosmos.mp4
   Suggested Title: "kosmos - Amazing Open Source Project! #shorts"
   Description: Check out kosmos! 🔗 https://github.com/kosmos-io/kosmos

[... continues for all projects ...]
```

## Customization

### Change Output Filenames

Edit line 216:

```python
# Current: short_01_lighthouse.mp4
safe_name = re.sub(r'[^\w\-_]', '_', project['name'].lower())
output_path = self.shorts_dir / f"short_{i+1:02d}_{safe_name}.mp4"

# Option 1: Just numbers
output_path = self.shorts_dir / f"short_{i+1:02d}.mp4"

# Option 2: With timestamp
output_path = self.shorts_dir / f"short_{start_min}{start_sec:02d}_{safe_name}.mp4"

# Option 3: Include date
date_str = datetime.now().strftime("%m%d")
output_path = self.shorts_dir / f"{date_str}_{safe_name}.mp4"
```

### Adjust Duration Calculation

Edit line 87:

```python
# Current: Use time until next project
projects[i]['duration'] = projects[i + 1]['start'] - projects[i]['start']

# Option 1: Fixed duration (30 seconds)
projects[i]['duration'] = 30

# Option 2: Max 45 seconds
projects[i]['duration'] = min(projects[i + 1]['start'] - projects[i]['start'], 45)

# Option 3: Last project gets 60 seconds
if i < len(projects) - 1:
    projects[i]['duration'] = projects[i + 1]['start'] - projects[i]['start']
else:
    projects[i]['duration'] = 60
```

### Modify Conversion Filters

Edit line 128 (Center Crop):

```python
# Current: Crop 960x1080
filter_complex = (
    f"[0:v]crop=960:1080:(1920-960)/2:0[square];"
    f"[square]scale=1080:1920:force_original_aspect_ratio=increase[scaled];"
    f"[scaled]crop=1080:1920:(1080-1080)/2:(1920-1920)/2[vertical]"
)

# Option 1: Wider crop (1200x1080)
filter_complex = (
    f"[0:v]crop=1200:1080:(1920-1200)/2:0[square];"
    f"[square]scale=1080:1920:force_original_aspect_ratio=increase[scaled];"
    f"[scaled]crop=1080:1920:(1080-1080)/2:(1920-1920)/2[vertical]"
)

# Option 2: Add subtle zoom
filter_complex = (
    f"[0:v]crop=960:1080:(1920-960)/2:0,"
    f"scale=1080:2160,crop=1080:1920:0:120[vertical]"
)
```

## Workflow Examples

### Workflow 1: Standard Production
```bash
# Create longform video
python video_maker.py
# → Creates github_roundup_jan14.mp4

# Extract all Shorts
python extract_timestamped_shorts.py
# → Creates 10 individual Shorts in shorts/

# Upload each Short individually to YouTube
```

### Workflow 2: Batch Processing Multiple Videos
```bash
# Process today's video
python video_maker.py
python extract_timestamped_shorts.py

# ... later ...

# Create another video
python video_maker.py
python extract_timestamped_shorts.py
# (detects and processes the new video automatically)
```

### Workflow 3: Re-extract with Different Method
```bash
# First: Extract with center crop
python extract_timestamped_shorts.py
> Enter: 1

# Test results, don't like them...

# Delete old Shorts and re-extract with pillar box
rm shorts/*.mp4
python extract_timestamped_shorts.py
> Enter: 2
```

## Best Practices

### ✅ DO:
- **Keep timestamps updated** - Edit YOUTUBE_DESCRIPTION.md before extracting
- **Use Center Crop** if your text is centered in the graphics
- **Use Pillar Box** if you have side elements that matter
- **Test one Short first** - Upload one to YouTube before processing all
- **Check durations** - Ensure no Short exceeds 59 seconds
- **Keep upload list** - Use it for tracking what you've uploaded

### ❌ DON'T:
- **Skip timestamps** - The script won't work without proper format
- **Mix methods** - Stick to one method per batch
- **Upload compilation** - Each Short should be uploaded separately
- **Forget to backup** - Keep your longform video safe
- **Ignore safe zones** - Your original graphics should account for crop

## Optimizing Your Graphics for Shorts

### Current Code Stream Graphics

Your `codestream_graphics.py` creates horizontal graphics (1920x1080). When cropped:

```
┌────────────────────────────────────┐
│  CROP ZONE (1080px)                │
│  ╔═════════════════════════════╗   │
│  ║                               ║   │
│  ║   IMPORTANT TEXT HERE        ║   │
│  ║   (stays visible in Short)   ║   │
│  ║                               ║   │
│  ╚═════════════════════════════╝   │
│                                    │
│  LEFT CROPPED (420px)    RIGHT CROPPED (420px)
└────────────────────────────────────┘
```

### Recommendations for Centered Content

Edit your `codestream_graphics.py` to ensure important content is centered:

```python
# In create_project_graphic()

# Define safe zone (center 1080px)
SAFE_ZONE_LEFT = 420
SAFE_ZONE_RIGHT = 1500
CENTER_X = 960  # (1920 / 2)

# Position important text at center
draw.text((CENTER_X, 300), project_name, font=title_font, anchor="mm")
```

### Test Before Extracting

```bash
# Create test graphic with safe zone marked
python -c "
from PIL import Image, ImageDraw
img = Image.new('RGB', (1920, 1080), '#0a1628')
draw = ImageDraw.Draw(img)
# Draw safe zone
draw.rectangle([420, 0, 1500, 1080], outline='red', width=5)
img.save('test_safe_zone.png')
print('Created test_safe_zone.png - check your graphics fit inside')
"
```

## Troubleshooting

### Issue: "No timestamp patterns found"
**Solution:** Check YOUTUBE_DESCRIPTION.md format:
- Must be `MM:SS - **projectname**`
- URL on next line with `🔗` prefix
- Check for extra spaces or formatting

### Issue: "Text cut off in Short"
**Solution:** 
- Center text is cropped → Your graphics have text on sides
- Use "Pillar Box" method instead
- Or redesign graphics with centered layout

### Issue: "Duration too long (>59s)"
**Solution:** Edit line 87 to cap duration:
```python
projects[i]['duration'] = min(projects[i + 1]['start'] - projects[i]['start'], 55)
```

### Issue: "Audio out of sync"
**Solution:** This is rare with extraction. Check original video first.

### Issue: "Wrong timestamp detected"
**Solution:** Manual timestamps in YOUTUBE_DESCRIPTION.md. Format must be exact.

### Issue: "Skips existing files"
**Solution:** Delete Shorts you want to re-extract:
```bash
rm shorts/short_03_*.mp4
python extract_timestamped_shorts.py
```

## Uploading Strategy

### Recommended Approach

1. **Upload one test Short** first
2. **Check quality and formatting** on mobile
3. **Upload remaining Shorts** over several days
4. **Use suggested titles** from upload_list.txt
5. **Schedule strategically:** 1-2 Shorts per day

### Title Templates

```
"{Project Name} - Amazing Open Source Tool! 🔥 #shorts"
"You Need This GitHub Project! {Project Name} #opensource"
"Best Dev Tool: {Project Name} #shorts #github"
"{Project Name} Changed My Workflow! #shorts"
```

### Description Template

```
Check out {Project Name}! 

🔗 GitHub: {URL}

Full roundup on our channel: "Open Source Scribes"

#opensource #github #developer #programming #shorts
```

### Scheduling

```
Day 1: short_01_lighthouse.mp4
Day 2: short_02_kosmos.mp4
Day 3: [skip day]
Day 4: short_03_pipelex.mp4
Day 5: short_04_claude-code-router.mp4
[... continue ...]
```

## Performance

### Extraction Times

| Number of Shorts | Center Crop | Pillar Box |
|------------------|-------------|------------|
| 5 Shorts         | ~1 minute   | ~1.5 minutes |
| 10 Shorts        | ~2 minutes  | ~3 minutes |
| 15 Shorts        | ~3 minutes  | ~4.5 minutes |

### Storage Requirements

- **1 Short (30-60s):** ~5-12 MB
- **10 Shorts:** ~50-120 MB
- **Total with longform:** ~300-500 MB

## Integration with Workflow

### Complete Workflow

```
github_urls.txt
        ↓
   video_maker.py
        ↓
github_roundup_jan14.mp4
        ↓
extract_timestamped_shorts.py
        ↓
┌───────────────┴───────────────┐
↓                               ↓
github_roundup_jan14.mp4    shorts/
(keep for channel)            short_01_*.mp4
                            short_02_*.mp4
                            [... etc ...]
                            upload_list.txt
```

### Replacing Other Methods

**Before:**
- `video_maker_with_shorts.py` - Random Shorts from different projects

**After:**
- `video_maker.py` - Create longform
- `extract_timestamped_shorts.py` - Extract ALL projects as Shorts

**Advantage:** Every project gets a Short, not just randomly selected ones!

## Quick Reference

### Commands

```bash
# Create longform video
python video_maker.py

# Extract Shorts from timestamps
python extract_timestamped_shorts.py

# Choose method: 1 (crop) or 2 (pillar)

# Output: shorts/short_XX_projectname.mp4
```

### Files

```
Input:  github_roundup_jan14.mp4 + YOUTUBE_DESCRIPTION.md
Output: shorts/short_*.mp4 (one per project)
Guide:  shorts/upload_list.txt
```

### Configuration

```python
# Max duration
MAX_SHORT_DURATION = 59

# Method choice
method = "crop"  # or "pillar"

# Filename format
f"short_{i+1:02d}_{safe_name}.mp4"
```

## Advanced: Custom Timestamp Patterns

### Different Format in YOUTUBE_DESCRIPTION.md

If your description uses a different format, edit line 47:

```python
# Current pattern
pattern = r'(\d+):(\d+)\s*-\s*\*\*([^*]+)\*\*\s*\n\s*🔗\s*(https://github\.com/[^\s]+)'

# Alternative 1: Without emoji
pattern = r'(\d+):(\d+)\s*-\s*\*\*([^*]+)\*\*\s*\n\s*Link:\s*(https://github\.com/[^\s]+)'

# Alternative 2: Different timestamp format
pattern = r'(\d{1,2}):(\d{2})\s+-\s+\*\*([^*]+)\*\*.*?https://github\.com/[^\s]+'

# Alternative 3: Simple format (project name only)
pattern = r'(\d+):(\d+)\s*-\s*\*\*([^*]+)\*\*'
```

---

**Happy Short extracting! 📱✨**

Remember: Each project from your longform video becomes an individual YouTube Short!
