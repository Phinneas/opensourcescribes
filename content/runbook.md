# OpenSourceScribes — System Runbook

## Overview

OpenSourceScribes is an automated YouTube/Substack content pipeline that discovers interesting open source GitHub repositories, generates narration scripts, produces full video content, and publishes written companion pieces (Medium, newsletter, LinkedIn, Reddit). The system is designed to run end-to-end from a single command.

---

## Architecture

```
exa_discovery.py
    → github_urls.txt (15 repos, current batch)
        → auto_script_generator.py
            → posts_data.json (repos + narration scripts)
                → video_automated.py
                    → Seedream 5 (background images per segment)
                    → MiniMax TTS (narration audio)
                    → Remotion (segment + transition video rendering)
                    → FFmpeg (video assembly)
                    → generate_medium_post.py
                    → generate_newsletter.py
                    → generate_description.py
                    → published_repos.txt (dedup log)
```

---

## Key Files

| File | Purpose |
|---|---|
| `video_automated.py` | Main orchestrator. Runs the full pipeline. |
| `exa_discovery.py` | Exa-powered repo discovery. Finds 15 fresh repos per run. |
| `auto_script_generator.py` | Fetches GitHub metadata + README, generates narration scripts via Claude. |
| `seedream_generator.py` | WaveSpeed Seedream image generation with local caching. |
| `enhanced_audio_generator.py` | TTS fallback chain (MiniMax → Hume → gTTS). |
| `config.json` | All API keys and settings. Single source of truth. |
| `github_urls.txt` | Current batch input (15 URLs). Overwritten each run. |
| `published_repos.txt` | Permanent append-only dedup history. Never cleared. |
| `posts_data.json` | Current batch with generated scripts. Input to video pipeline. |
| `discovery_sources.py` | Abstract base class for all discovery sources. |

---

## Running the Pipeline

### Full automated run (Exa discovery + everything)
```bash
python exa_discovery.py
```

### Manual run (you supply the repos)
```bash
# Edit github_urls.txt with your chosen repos, one per line
python auto_script_generator.py --input github_urls.txt --output posts_data.json
python video_automated.py
```

### Resume after a crash
Just rerun `python video_automated.py`. Audio, graphics, and Seedream images are all cached — only missing files get regenerated.

---

## Configuration (config.json)

All keys and settings live in `config.json`. Never hardcode credentials in source files.

### Key sections

**`minimax`** — Primary TTS voice service. Requires `api_key` and `group_id` from minimaxi.com.

**`wavespeed`** — Seedream image generation. Key settings:
- `api_base` — WaveSpeed API base URL (not hardcoded in code)
- `seedream_model` — Model slug. Must match what WaveSpeed actually has. Check with:
  ```bash
  curl -s -H "Authorization: Bearer YOUR_KEY" \
    https://api.wavespeed.ai/api/v3/models | python3 -m json.tool | grep seedream
  ```

**`exa`** — Exa search API key for automated repo discovery.

**`voice.fallback_chain`** — Order of TTS services to try: `minimax → hume → openai → kittentts → gtts`.

---

## Deduplication

Two files, two jobs:

- **`github_urls.txt`** — Current batch only. 15 URLs. Overwritten at the start of each discovery run. Read by `auto_script_generator.py`.
- **`published_repos.txt`** — Permanent history. Append-only. Every repo that completes the pipeline is logged here. `exa_discovery.py` checks this before returning candidates.

A repo that has been through the pipeline once will never be surfaced by auto-discovery again.

---

## Exa Discovery

Two strategies run in parallel:

1. **Keyword search** — Five neural queries scoped to `github.com`. Finds repos by semantic intent, not just keyword match.
2. **find_similar()** — Seeded from top-performing video subjects. Surfaces repos that audiences of your best videos would also want to watch.

### Updating the seed list
Edit `SEED_REPOS` at the top of `exa_discovery.py`. Update this list whenever you identify new top-performing videos.

### Discovery only (no pipeline)
```bash
python exa_discovery.py --discover-only
# writes github_urls.txt and stops
```

---

## Audio Generation

`video_automated.py` uses its own `generate_audio()` method (not `enhanced_audio_generator.py`) with this chain:

1. **MiniMax** — Primary. Requires `minimax.api_key` and `minimax.group_id` in config.
2. **Hume** — Fallback. Requires `hume_ai.use_hume: true` and valid API key.
3. **gTTS** — Last resort. No API key needed, lower quality.

Audio files are cached in `assets/`. Delete `assets/*_audio.mp3` to force regeneration.

---

## Seedream Image Generation

WaveSpeed Seedream generates one cinematic background image per project segment. Images are cached in `assets/wavespeed/` by content hash — same project won't re-generate unless `force_refresh=True`.

### Known API behaviour
- Submit returns: `{"code": 200, "data": {"id": "...", "urls": {"get": "..."}, "status": "created"}}`
- Poll the `data.urls.get` URL until `data.status == "completed"`
- Images are in `data.outputs[]` as plain URL strings

### Model names change
The model slug in config must match WaveSpeed's actual available models. `seedream-v5.0` became `seedream-v5.0-lite`. Always verify with the curl command above when the API returns 400.

---

## Remotion Rendering

Remotion renders each segment, transition, and the intro scene.

### Critical constraints
1. **`cwd` is `remotion_video/`** — all Remotion commands run from there.
2. **Output paths must be absolute** — relative paths resolve against `remotion_video/`, not the project root.
3. **Asset files must be in `remotion_video/public/`** — Remotion's `staticFile()` does not accept absolute paths. Images are copied there before each render.
4. **Composition ID must match exactly** — available compositions: `Main`, `IntroScene`, `SegmentScene`, `TransitionScene`, `OverlayGenerator`, `TransitionGenerator`.

### Entry point
```
src/index.ts  (relative to remotion_video/ cwd)
```
Not `remotion_video/src/index.ts` — that path doubles the directory.

---

## Common Errors and Fixes

### `staticFile() does not support absolute paths`
Remotion received an absolute file path in props. The render pipeline now copies images to `remotion_video/public/` and passes only the filename.

### `Could not find composition with ID remotion_video/src/index.ts`
The entry point path was doubled. Remotion interpreted the path as a composition ID. Fix: use `src/index.ts` as entry point, not `remotion_video/src/index.ts`.

### `model not found` (Seedream 400)
The model slug in `config.json > wavespeed.seedream_model` doesn't exist on WaveSpeed. Run the models curl to find the correct name.

### `No task_id in API response` (Seedream)
WaveSpeed wraps responses in a `data` envelope. The ID field is `data.id`, not `task_id`. Poll URL is `data.urls.get`.

### `status=completed` polling forever
WaveSpeed uses `completed` not `succeeded`. The poll check must accept both.

### MiniMax audio falls through to Hume
Check that `minimax.api_key` and `minimax.group_id` are set in config. The trim step (`silenceremove` via ffmpeg) failing will also cause a fallthrough if not wrapped in try/except.

### ffmpeg silenceremove exit code 183
The silenceremove filter fails on some ffmpeg builds. The trim step is non-critical — the audio is kept as-is if trim fails.

---

## Delivery Structure

Each run produces a dated folder:

```
deliveries/
  04-07/
    longform_github_roundup.mp4
    github_shorts_04-07.mp4
    deep_dives/
      ...
```

Deleting the delivery folder and rerunning is safe — cached assets (audio, images, graphics) are preserved in `assets/` and reused.

---

## Adding Repos Manually

Edit `github_urls.txt` directly before running `auto_script_generator.py`. One URL per line. The dedup system only checks `published_repos.txt`, so you can add any repo that hasn't been through the pipeline before.
