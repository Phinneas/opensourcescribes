# YouTube Shorts Generator Guide

## Overview

The YouTube Shorts feature **extracts vertical clips from your existing main video** (created by `video_maker.py`). It takes your horizontal 16:9 video and converts it to vertical 9:16 format optimized for YouTube Shorts.

**This does NOT regenerate content** - it reuses your existing video with the same graphics, voice, and branding you already created.

## How It Works

### From Horizontal to Vertical

```
Main Video (16:9)         →         YouTube Short (9:16)
┌─────────────────────┐              ┌──────────┐
│                     │              │          │
│   1920x1080         │   Extract    │   1080   │
│   Your existing     │  + Convert   │   x      │
│   graphics & voice  │    Crop      │  1920    │
│                     │              │          │
└─────────────────────┘              └──────────┘
```

### Conversion Strategy

1. **Extract Segment** - Takes a 30-59 second clip from your main video
2. **Crop Center** - Extracts the center 1080px (square crop)
3. **Add Letterboxing** - Adds padding top/bottom to make 1080x1920
4. **Keep Audio** - Preserves original Hume.ai voice and audio

## Key Features

### ✅ No Content Regeneration
- Uses your existing video exactly as created
- Same graphics, same voice, same branding
- No additional API calls or rendering time

### 📱 Vertical Format
- **Resolution:** 1080x1920 (9:16 aspect ratio)
- **Center crop:** Focuses on the most important content
- **Branded padding:** Uses Code Stream dark blue (#0a1628) for letterboxing

### ⏱️ Smart Segmentation
- **Distributed clips:** Spreads Shorts evenly throughout video
- **Auto-duration:** Ensures each Short is ≤59 seconds (YouTube limit)
- **Configurable:** Choose how many Shorts and their duration

### 🎬 Multiple Output Options
- **Individual files:** Each Short saved separately
- **Compilation reel:** All Shorts combined into one video

## Usage

### Basic Workflow

```bash
# Step 1: Create your main video (as usual)
python video_maker.py

# Step 2: Generate Shorts from the main video
python shorts_generator.py
```

### Interactive Prompts

When you run `shorts_generator.py`, you'll see:

```
📱 YouTube Shorts Generator for OpenSourceScribes
============================================================
This tool extracts vertical clips from your existing main video
to create YouTube Shorts (9:16 aspect ratio)

✅ Found video: github_roundup_jan14.mp4

How many Shorts to generate? (default=3): 3
Target duration per Short? (default=45s): 45
```

**Recommendations:**
- **Number of Shorts:** 2-4 (good variety without repetition)
- **Duration:** 30-45 seconds (sweet spot for engagement)

### Output Structure

```
opensourcescribes/
├── github_roundup_jan14.mp4          # Your original main video
├── shorts/                            # Extracted Shorts
│   ├── short_000.mp4                  # Short #1 (45s clip)
│   ├── short_001.mp4                  # Short #2 (45s clip)
│   └── short_002.mp4                  # Short #3 (45s clip)
└── github_shorts_jan14.mp4            # Compiled reel (all combined)
```

## How Segments Are Chosen

### Automatic Distribution

The script automatically distributes Shorts throughout your video:

**Example:** 10-minute video, 3 Shorts requested
```
Timeline:  0s ──────────────────────────────────── 600s
Short 1:          ↑ (~3 min mark)
Short 2:                     ↑ (~6 min mark)
Short 3:                               ↑ (~9 min mark)
```

### Calculation Logic

```python
# Available time (excluding intro/outro buffers)
available_time = total_duration - (num_shorts × short_duration) - 20

# Evenly distribute start times
for each_short:
    start_time = (available_time / (num_shorts + 1)) × position + 10
```

**Benefits:**
- Avoids intro/outro (first/last 10 seconds)
- Spreads content evenly
- No overlap between Shorts

## Customization Options

### Change Number of Shorts

Edit `shorts_generator.py` line 280:

```python
# Default: User input
num_shorts = int(input("How many Shorts? (default=3): ").strip() or "3")

# Always generate 2 Shorts
num_shorts = 2

# Always generate 5 Shorts
num_shorts = 5
```

### Adjust Duration

Edit `shorts_generator.py` line 282:

```python
# Default: User input
target_duration = int(input("Duration? (default=45s): ").strip() or "45")

# Always use 30 seconds
target_duration = 30

# Always use 60 seconds (max safe)
target_duration = 59
```

### Change Letterbox Color

Edit `shorts_generator.py` line 75:

```python
# Current: Code Stream dark blue
filter_complex = "...color=#0a1628[vertical]"

# Pure black
filter_complex = "...color=#000000[vertical]"

# Dark gray
filter_complex = "...color=#1a1a1a[vertical]"

# Match your branding
filter_complex = "...color=#0a1628[vertical]"
```

### Modify Crop Strategy

Edit `shorts_generator.py` line 71:

```python
# Current: Center crop (1080x1080)
filter_complex = "[0:v]crop=1080:1080:(1920-1080)/2:0[square]"

# Left-focused crop
filter_complex = "[0:v]crop=1080:1080:0:0[square]"

# Right-focused crop
filter_complex = "[0:v]crop=1080:1080:1920-1080:0[square]"

# Slightly larger crop with scaling
filter_complex = "[0:v]crop=1200:1080:360:0[square]"
```

## Advanced: Custom Segment Selection

### Specify Exact Timestamps

Create a custom script to extract specific segments:

```python
from shorts_generator import ShortsFromVideoExtractor

extractor = ShortsFromVideoExtractor()

# Extract specific segments
segments = [
    (45, 90),    # Start at 45s, duration 90s
    (180, 60),   # Start at 3min, duration 60s
    (420, 45),   # Start at 7min, duration 45s
]

for i, (start, duration) in enumerate(segments):
    output = f"shorts/custom_short_{i:03d}.mp4"
    extractor.create_vertical_crop(
        input_video="github_roundup_jan14.mp4",
        start_time=start,
        duration=duration,
        output_path=Path(output)
    )
```

### Extract from Specific Video

```python
extractor.generate_shorts_from_video(
    input_video="github_roundup_jan14.mp4",  # Specific video
    num_shorts=2,
    short_duration=30
)
```

## Workflow Examples

### Workflow 1: Standard Production
```bash
# 1. Build main video from GitHub URLs
python video_maker.py

# 2. Generate 3 Shorts (45s each)
python shorts_generator.py
   > Enter: 3
   > Enter: 45

# 3. Upload individual Shorts to YouTube
#    - shorts/short_000.mp4
#    - shorts/short_001.mp4
#    - shorts/short_002.mp4
```

### Workflow 2: Quick Content Repurposing
```bash
# Use existing video from yesterday
python shorts_generator.py
   > Auto-finds: github_roundup_jan13.mp4
   > Enter: 2
   > Enter: 30

# Result: 2 quick Shorts for same-day posting
```

### Workflow 3: Batch Production
```bash
# Create multiple videos
python video_maker.py  # Creates github_roundup_jan14.mp4
python shorts_generator.py  # Creates 3 Shorts

# ...later...

python video_maker.py  # Creates github_roundup_jan15.mp4
python shorts_generator.py  # Creates 3 more Shorts

# Result: 6 Shorts from 2 main videos
```

## Best Practices

### ✅ DO:
- **Create main video first** - Shorts depend on it
- **Use 2-4 Shorts** - Good variety without repetition
- **Keep 30-45 seconds** - Optimal for engagement
- **Check content** - Ensure cropped area shows important info
- **Space them out** - Let the auto-distribution pick varied segments

### ❌ DON'T:
- **Skip main video creation** - Shorts extractor needs the source
- **Make Shorts too long** - 60+ seconds will be rejected by YouTube
- **Extract from same area** - Each Short should be unique
- **Ignore letterboxing** - Some content may be cut off at edges
- **Over-produce** - More than 5 Shorts from one video is excessive

## Understanding the Crop

### What Gets Cut

When cropping from 1920x1080 to 1080x1080:

```
Before (1920x1080)        After (1080x1080)
┌─────────────────────┐   ┌─────────────┐
│  420px (cut)        │   │             │
│   ┌──────────────┐  │   │             │
│   │   1080px     │  │ → │   CROP      │
│   │   (KEPT)     │  │   │   AREA      │
│   └──────────────┘  │   │             │
│  420px (cut)        │   │             │
└─────────────────────┘   └─────────────┘
```

**Important:** Side content (420px on each side) is lost in the crop.

### Optimize Your Main Video for Shorts

When designing graphics in `codestream_graphics.py`:

```python
# Keep important content in center "safe zone"
# (1080px centered in 1920px width)

SAFE_ZONE_LEFT = 420
SAFE_ZONE_RIGHT = 1500

# Place important text/elements here
draw.text((540, 300), "Important Text", ...)  # Center-aligned
```

## Troubleshooting

### Issue: "Could not find github_roundup_*.mp4"
**Solution:** Run `video_maker.py` first to create the main video.

### Issue: Text is cut off in Short
**Solution:** Your graphics have text on the sides. Redesign with centered layout.

### Issue: Shorts look too zoomed in
**Solution:** The crop is extracting too closely. Try a different crop strategy in line 71.

### Issue: Audio out of sync
**Solution:** This is rare with extraction, but if it happens, check the original video first.

### Issue: Letterboxing looks odd
**Solution:** Change the color in line 75 to match your brand or use pure black (#000000).

### Issue: Wrong segments extracted
**Solution:** The auto-distribution may not pick the best moments. Use custom timestamp selection instead.

## Performance

### Processing Times

| Video Length | 1 Short | 3 Shorts | 5 Shorts |
|--------------|---------|----------|----------|
| 5 minutes    | ~10s    | ~30s     | ~50s     |
| 10 minutes   | ~15s    | ~45s     | ~75s     |
| 15 minutes   | ~20s    | ~60s     | ~100s    |

### Storage Requirements

- **1 Short (45s):** ~8-15 MB
- **3 Shorts:** ~25-45 MB
- **Compilation reel:** ~25-45 MB (same total size)

## Uploading to YouTube

### Recommended Upload Strategy

1. **Upload individual Shorts** (not the compilation)
   - Better for YouTube's algorithm
   - Can be scheduled separately
   - Individual analytics per Short

2. **Use compilation reel** for:
   - Other platforms (TikTok, Instagram Reels)
   - Archive purposes
   - Testing/previewing

### Title Templates

```
"Amazing GitHub Tool You Need! #shorts #opensource"
"This Open Source Project is Insane! 🔥 #shorts"
"Best Dev Tool I Found This Week #shorts"
"Revolutionize Your Workflow with This! #shorts"
```

### Description Template

```
Discover [Project Name] - an incredible open source tool!

🔗 GitHub: [link from your video]

Full video on our channel!

#opensource #github #developer #coding #shorts
```

## Integration with Existing Workflow

### Before Shorts Generator
```
github_urls.txt → video_maker.py → github_roundup_jan14.mp4
                                        (16:9 horizontal)
```

### After Shorts Generator
```
github_urls.txt → video_maker.py → github_roundup_jan14.mp4
                                           ↓
                                    shorts_generator.py
                                           ↓
                                ┌──────────┴──────────┐
                                ↓                     ↓
                        shorts/short_000.mp4   github_shorts_jan14.mp4
                        shorts/short_001.mp4        (compilation)
                        shorts/short_002.mp4
```

### Key Point
**The Shorts generator does NOT affect your main video creation workflow.** It's an optional post-processing step that extracts clips from the already-created video.

## Future Enhancements

Possible improvements:
- [ ] Smart segment selection (based on scene changes)
- [ ] Auto-detect best segments (using audio levels)
- [ ] Add custom intros/outros for Shorts
- [ ] Overlay text/hashtags on Shorts
- [ ] Square format (1:1) for Facebook/LinkedIn
- [ ] Auto-scheduling via YouTube API

## Support

For issues:
1. Ensure `video_maker.py` completed successfully
2. Check that `github_roundup_*.mp4` exists
3. Verify ffmpeg is working: `ffmpeg -version`
4. Review timestamps don't exceed video duration

---

**Happy Short-making! 📱✨**

Remember: These Shorts are repurposed clips from your existing content - no regeneration needed!
