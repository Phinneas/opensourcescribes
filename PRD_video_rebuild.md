# PRD: Video Pipeline Rebuild — Seedream 5 + Remotion

**Status:** Draft
**Date:** 2026-03-31
**Working dir:** `/Users/chesterbeard/Desktop/opensourcescribes`

---

## Problem

The current video pipeline has never produced the intended enhanced output despite 7+ commits attempting to wire MiniMax and Remotion into it. The root causes are structural:

1. **Config conflict** — `video_settings.use_minimax: false` silently disables MiniMax while `minimax.use_minimax: true` is ignored; code reads the wrong key
2. **Silent import guard failures** — `HYBRID_AVAILABLE` and `MINIMAX_AVAILABLE` flags collapse to `False` if any single import fails, bypassing the entire enhanced pipeline with no diagnostic output
3. **Nested silent fallbacks** — failures at every layer (MiniMax API, module import, file existence) all resolve to `create_intro_card()` (the static PNG) with no logging of which path was taken
4. **MiniMax is a poor fit** — async job polling (60–120s/clip), non-deterministic output, not designed for repeatable branded video production

The result: every run produces the same static-looking video regardless of what code changes have been made.

---

## Goal

Replace MiniMax entirely with a clean two-layer stack:

- **Seedream 5** (WaveSpeedAI API) — generates high-quality background images per segment
- **Remotion** — animates those images into video clips, renders the branded intro, applies overlays and transitions

Remove the import guard architecture entirely. Every component is a hard dependency — if it fails, the pipeline fails loudly with a clear error, not silently with a static fallback.

---

## Non-Goals

- Keeping MiniMax in any capacity (remove completely)
- Keeping the `HYBRID_AVAILABLE` / `MINIMAX_AVAILABLE` flag pattern
- Silent fallbacks to static cards (branding.py static cards are end-of-life for video use)
- Veo 3 integration in this phase (deferred — Remotion covers animation needs for now)

---

## Success Criteria

- Every video run produces animated, non-static output
- Intro sequence is a Remotion-rendered branded animation, not a static PNG card
- Each project segment uses a Seedream 5 background image animated via Remotion
- Transitions between segments are Remotion-rendered clips
- A pipeline failure surfaces a clear Python exception, not silent degradation
- `video_automated.py` import section has no try/except guards around core video modules

---

## Architecture

### Current (broken)

```
branding.py (static)  ←── silent fallback ←── MiniMax API (fails)
                                                     ↑
                                          HYBRID_AVAILABLE=False
                                                     ↑
                                          ImportError (any module)
```

### New (clean)

```
github_urls.txt
      │
      ▼
video_automated.py
      │
      ├── Seedream 5 API (WaveSpeedAI)
      │     └── background image per segment  ──────────┐
      │                                                  ▼
      ├── Remotion CLI                            segment_N.mp4
      │     ├── IntroScene component  ──────► intro.mp4
      │     ├── SegmentScene component ──────► segment_N.mp4
      │     └── TransitionScene component ──► transition_N.mp4
      │
      └── FFmpeg
            └── concatenate all clips ──────► final_output.mp4
```

---

## Components

### 1. Seedream 5 Image Generator (`seedream_generator.py`) — New File

Replaces: `minimax_integration.py`, Gemini image generation calls in `video_automated.py`

**Responsibilities:**
- Accept a project dict (name, description, language, stars, topics)
- Build a cinematic prompt describing the visual aesthetic for that project
- Call WaveSpeedAI Seedream 5 API, poll for completion
- Return local path to downloaded image

**API details:**
- SDK: `wavespeed-python` (`pip install wavespeed`)
- Endpoint: `https://api.wavespeed.ai/api/v3/bytedance/seedream-v5.0`
- Auth: `Authorization: Bearer <WAVESPEED_API_KEY>`
- Output: 1920×1080, 16:9, cinematic framing

**Prompt strategy per segment:**
```
Cinematic, high-detail digital artwork representing {project_name}:
{description}. Dark tech aesthetic, deep blues and purples, subtle
code/circuit motifs, dramatic lighting. 4K, photorealistic, no text.
```

Text is kept off the source image — Remotion handles all text overlays so Seedream output is purely visual.

**Config additions to `config.json`:**
```json
"seedream": {
    "api_key": "",
    "model": "bytedance/seedream-v5.0",
    "width": 1920,
    "height": 1080,
    "output_dir": "assets/seedream"
}
```

**Caching:** Images are cached by `{owner}_{repo}_seedream.png` in `assets/seedream/`. If the cache file exists, skip the API call. Cache is invalidated manually.

---

### 2. Remotion Components (in `remotion_video/` submodule)

Three React components to build or extend in the existing Remotion project:

#### 2a. `IntroScene`

Replaces: `branding.py create_intro_card()` + `minimax_intro_generator.py`

A branded animated intro sequence (~6 seconds). Design:
- Channel name/logo animates in (fade + slight upward drift)
- Episode title appears below with a typewriter effect
- Background: dark gradient with subtle animated particle field or grid
- No external image dependency — fully programmatic React animation

Props:
```ts
{ episodeTitle: string, channelName: string, durationInFrames: number }
```

#### 2b. `SegmentScene`

Replaces: `_create_segment_with_overlay()` + Remotion overlay logic in current code

Takes a Seedream-generated image and animates it with overlays. Layers:
1. Seedream image background — Ken Burns zoom/pan (slow, 5–8% scale over segment duration)
2. Project name — bold, top-left or bottom-left, fade in at 0.5s
3. Stats bar — stars, forks, language — animates in from bottom
4. Optional topic pill badges

Props:
```ts
{
  imagePath: string,
  projectName: string,
  stars: number,
  forks: number,
  language: string,
  topics: string[],
  durationInFrames: number
}
```

#### 2c. `TransitionScene`

Replaces: `remotion_transition_generator.py` pre-generated clips

Short (~1s) animated transition between segments. Options:
- Horizontal wipe with light streak
- Diagonal sweep
- Flash cut with brand color

Props:
```ts
{ style: 'wipe' | 'sweep' | 'flash', durationInFrames: number }
```

**Remotion render call pattern** (from Python via subprocess):
```python
subprocess.run([
    "npx", "remotion", "render",
    "remotion_video/src/index.ts",
    "SegmentScene",
    "--props", json.dumps(props),
    "--output", output_path,
    "--frames", f"0-{duration_frames}"
])
```

---

### 3. `video_automated.py` — Simplified

**Remove entirely:**
- `MINIMAX_AVAILABLE` flag and its try/except block
- `HYBRID_AVAILABLE` flag and its try/except block
- `generate_intro_with_audio()` call and MiniMax fallback chain
- `_create_segment_with_overlay()` MiniMax/overlay conditional logic
- All references to `minimax_intro_generator`, `minimax_integration`, `github_page_capture`

**Replace with:**
```python
from seedream_generator import SeedreamGenerator
# Remotion called via subprocess — no Python import needed
```

**`assemble_longform_video()` new intro logic:**
```python
# Render intro via Remotion — hard dependency, no fallback
intro_path = render_remotion_scene(
    composition="IntroScene",
    props={"episodeTitle": episode_title, "channelName": CHANNEL_NAME},
    output=OUTPUT_FOLDER / "intro.mp4",
    duration_frames=180  # 6s at 30fps
)
```

**Per-segment loop new logic:**
```python
for project in projects:
    # 1. Get Seedream image (cached or fresh API call)
    image_path = seedream.generate(project)
    # 2. Render animated segment via Remotion
    segment_path = render_remotion_scene(
        composition="SegmentScene",
        props={...},
        output=OUTPUT_FOLDER / f"seg_{i}.mp4",
        duration_frames=segment_frames
    )
    # 3. Render transition
    transition_path = render_remotion_scene(
        composition="TransitionScene",
        props={"style": "wipe"},
        output=OUTPUT_FOLDER / f"trans_{i}.mp4",
        duration_frames=30
    )
```

---

### 4. `config.json` — Cleanup

**Remove:**
```json
"minimax": { ... },
"video_settings": { "use_minimax": false }
```

**Add:**
```json
"seedream": { "api_key": "", "model": "bytedance/seedream-v5.0", ... },
"video_settings": { "fps": 30, "resolution": "1920x1080" }
```

No more boolean feature flags for core pipeline components. If a component is broken, the run fails.

---

### 5. Files to Delete / Deprecate

| File | Action |
|---|---|
| `minimax_intro_generator.py` | Delete |
| `minimax_integration.py` | Delete |
| `github_page_capture.py` | Delete (was only used by MINIMAX_AVAILABLE block) |
| `remotion_transition_generator.py` | Delete (replaced by `TransitionScene` component) |
| `remotion_overlay_generator.py` | Delete (replaced by `SegmentScene` component) |
| `ffmpeg_enhancements.py` | Keep — FFmpeg still used for final concatenation |
| `branding.py` | Keep for non-video uses (thumbnails, Medium images) — remove from video path |

---

## Implementation Order

**Phase 1 — Image layer**
1. Create `seedream_generator.py` with WaveSpeedAI integration and local cache
2. Add `seedream` block to `config.json`, add API key
3. Smoke test: generate one image for one project, confirm output

**Phase 2 — Remotion components**
4. Build `IntroScene` component in `remotion_video/`
5. Build `SegmentScene` component with Ken Burns + overlay layers
6. Build `TransitionScene` component
7. Smoke test each with `npx remotion render` directly

**Phase 3 — Pipeline wiring**
8. Add `render_remotion_scene()` helper to `video_automated.py`
9. Replace intro generation with `IntroScene` render call
10. Replace segment loop with Seedream → `SegmentScene` → `TransitionScene` pattern
11. Remove all MiniMax imports, flags, and fallback chains
12. Clean `config.json`

**Phase 4 — Cleanup**
13. Delete deprecated files
14. Full end-to-end test run with 2–3 projects
15. Verify no static card output anywhere in final video

---

## Dependencies

| Dependency | Install | Purpose |
|---|---|---|
| `wavespeed` | `pip install wavespeed` | Seedream 5 API client |
| Node.js / npx | already installed (Remotion submodule exists) | Remotion render |
| `@remotion/cli` | already in `remotion_video/` package.json | Remotion render |
| FFmpeg | already installed | Final video assembly |

---

## Open Questions / Future

- **Veo 3 integration (future phase):** Once Remotion intro is stable, Veo 3 could optionally generate a 6s cinematic clip as the `IntroScene` background instead of the programmatic particle animation — layered under Remotion text/overlays
- **Seedream prompt tuning:** Initial prompts should be tested across several project types (CLI tools, ML libraries, DevOps infra) to ensure visual variety
- **Audio sync:** Remotion renders silent video; audio is handled separately and merged via FFmpeg as currently done — no change needed

## Resolved Decisions

| Question | Decision |
|---|---|
| MiniMax | Remove entirely, no fallback |
| Silent fallbacks | Eliminated — pipeline fails loudly on error |
| Feature flags for core components | Removed — no `HYBRID_AVAILABLE` pattern |
| Image generation | Seedream 5 via WaveSpeedAI, cached locally |
| Animation / intro | Remotion React components, subprocess render call |
| Veo 3 | Deferred to future phase |
