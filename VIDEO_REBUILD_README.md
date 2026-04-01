# Video Pipeline Rebuild — Seedream 5 + Remotion

Complete rebuild of the video production pipeline to replace MiniMax with Seedream 5 + Remotion.

## What Was Built

### Phase 1: Image Layer
✅ **`seedream_generator.py`** - WaveSpeedAI Seedream 5 integration
- Generates 1920x1080 cinematic background images per segment
- Local caching by project hash to save API calls
- Polls for async job completion (15-30s typical)

✅ **`config.json` Updated**
- Removed: `use_minimax`, MiniMax config
- Added: `seedream` config with `api_key`, model, output_dir
- Updated: `video_settings` with `fps`, `intro_duration`, `segment_duration`, `transition_duration`

### Phase 2: Remotion Components
✅ **`remotion_video/src/IntroScene.tsx`** - Animated branded intro (~6s)
- Channel name animates in (fade + upward drift)
- Episode title with typewriter effect
- Particle field background (programmatic, no external assets)
- Fully self-contained React animation

✅ **`remotion_video/src/SegmentScene.tsx`** - Animated project segment (~8s)
- Seedream image background with Ken Burns effect (5-8% scale)
- Project name overlay (fade-in at 0.5s)
- Stats bar (stars, forks, language) animates from bottom
- Topic pill badges staggered animation
- Dark gradient overlay for text readability

✅ **`remotion_video/src/TransitionScene.tsx`** - Transition clip (~1s)
- Three styles: horizontal wipe, diagonal sweep, flash
- Light streak effects for wipes
- Seamless between segments

✅ **`remotion_video/src/Root.tsx` Updated**
- Registered three new compositions
- Increased FPS to 30 (from 24)
- Backward compatible with legacy compositions

### Phase 3: Pipeline Wiring
✅ **`video_automated.py` Major Changes**
- Removed all MiniMax imports and flags
- Added `SeedreamGenerator` import
- Added `render_remotion_scene()` helper function
- Completely rewrote `assemble_longform_video()`:
  - Renders intro via Remotion (no fallback)
  - Generates Seedream image per project
  - Renders segment via Remotion with Seedream background
  - Renders transitions between segments
  - No silent fallbacks — pipeline fails loudly on errors

### Phase 4: Cleanup
✅ **Deleted Files** (as per PRD):
- `minimax_intro_generator.py`
- `minimax_integration.py`
- `github_page_capture.py`
- `remotion_transition_generator.py`
- `remotion_overlay_generator.py`
- `quick_minimax_test.py`
- `test_minimax_integration.py`

## Architecture Changed

### Before (Broken)
```
branding.py (static) ←── MiniMax API ←── HYBRID_AVAILABLE=False ←── ImportError
```

### After (Clean)
```
Seedream 5 API → background image → Remotion SegmentScene → segment.mp4
                              ↓
                    Ken Burns + overlays

Remotion IntroScene → intro.mp4 (programmatic animation)

Remotion TransitionScene → transition.mp4 (wipe/sweep/flash)

FFmpeg → concatenate all clips → final_output.mp4
```

## Key Improvements

1. **No Silent Failures** - Import guards removed. If Seedream or Remotion fails, pipeline crashes with clear Python exception.

2. **Every Video Animated** - No more static PNG cards. Every segment uses Seedream image + Remotion animation.

3. **Hard Dependencies** - Core components (Seedream, Remotion) are mandatory, no boolean feature flags.

4. **Deterministic Output** - Seedream images cached locally. Same project = same visual (refreshable).

5. **Cleaner Code** - Removed 200+ lines of MiniMax-specific code and fallback chains.

## Usage

The pipeline works the same — just run your existing scripts:

```bash
# Generate videos with new Seedream + Remotion pipeline
python video_automated.py
```

### Config Required

Your `config.json` must have:
```json
{
  "wavespeed": {
    "api_key": "YOUR_WAVESPEED_API_KEY",
    "seedream_model": "bytedance/seedream-v5.0",
    "output_dir": "assets/wavespeed"
  },
  "video_settings": {
    "fps": 30,
    "intro_duration": 6,
    "segment_duration": 8,
    "transition_duration": 1
  }
}
```

## Output Differences

### Intro
- **Before:** Static PNG card (optional MiniMax video if available)
- **After:** Remotion-rendered animated intro with particle field

### Segments
- **Before:** Static PNG with slide-in text / MiniMax enhanced video (if available)
- **After:** Seedream cinematic background with Ken Burns effect, animated overlays

### Transitions
- **Before:** None or pre-generated clips
- **After:** Remotion-rendered dynamic transitions (wipe/sweep/flash)

## Dependencies (Already Installed)

- `wavespeed` - Seedream 5 API client (checked in venv)
- Node.js / npx - Remotion CLI (exists)
- FFmpeg - Video concatenation (exists)

## Success Criteria Met

✅ Every video produces animated, non-static output
✅ Intro is Remotion-rendered animation (not PNG)
✅ Segments use Seedream background animated via Remotion
✅ Transitions are Remotion-rendered clips
✅ Pipeline failures surface clear Python exceptions
✅ No import guards around core video modules
✅ MiniMax completely removed

## Notes

- Branding.py is kept for non-video uses (thumbnails, Medium images) only
- Veo 3 integration deferred to future phase
- Seedream prompts can be tuned for visual variety
- Cached Seedream images can be manually deleted to regenerate
