# Cross-Platform Content Reformatting — Cost Reduction Design

**Date:** 2026-06-22
**Status:** Proposed, pending approval

## Problem

Each batch run generates three written formats from the same `posts_data.json` project list — Substack newsletter, Medium post, Reddit post — and each does its own independent full Claude Sonnet pass (1 intro call + 1 call per project + 1 outro call; Medium adds a 4th consistency-pass call). For a 15-project batch that's `generate_newsletter.py` (17 calls) + `generate_medium_post.py` (18 calls) + `generate_reddit_post.py` (17 calls) = **52 Sonnet calls per run**. Almost all of it is duplicate work: the underlying facts per project (name, URL, description) don't change between formats, only the voice does.

## Goal

Keep newsletter generation exactly as it is today — it's the flagship format and the one you've said reads very well. Replace Medium's and Reddit's independent per-project generation with a single cheap reformatting pass each, sourced from the *finished* newsletter text instead of the raw project list. Target: 52 Sonnet calls/run → ~17 Sonnet calls/run (newsletter only) + 2 Mistral calls.

## Architecture

**Today:** three parallel, independent pipelines. Each reads `posts_data.json` directly, calls Claude Sonnet for every project, and writes its own output file. `core/workflow_manager.py` runs them in the order Medium → Reddit → Newsletter, noting in a comment that they're "parallelizable" since none currently depend on the others.

**After:** newsletter generation is unchanged and becomes a hard dependency for the other two. `generate_medium_post.py` and `generate_reddit_post.py` stop reading `posts_data.json` for prose generation and stop calling Claude. Instead, each reads the finished `deliveries/{date}/SUBSTACK_NEWSLETTER.txt` (reusing the path-resolution logic already in `reformat_newsletter.py`'s `find_latest_newsletter()`) and makes one Mistral call with a platform-specific system prompt that restyles the newsletter's content into that platform's voice, while preserving every project name and URL.

This introduces a real ordering dependency that doesn't exist today: `workflow_manager.py`'s step order must change from `[Medium, Reddit, Newsletter]` to `[Newsletter, Medium, Reddit]`. Medium and Reddit remain parallelizable *with each other* once the newsletter file exists, just not before it.

## Components

- **`generate_newsletter.py`** — generation logic unchanged. One optimization added: the per-project `PROJECT_SECTION_PROMPT` calls (the only ones repeated identically, n times per run) move their shared instructions out of the inlined user-message string and into an actual `system` parameter with `cache_control` set on it. `EDITORIAL_PROMPT` and `OUTRO_PROMPT` are each called once per run and are left uncached — caching a block that's only read once costs more (cache-write premium) than it saves.
- **`generate_medium_post.py`** — rewritten. Drops `INTRO_PROMPT` / `PROJECT_SECTION_PROMPT` / `OUTRO_PROMPT` / `CONSISTENCY_PASS_PROMPT` and the `anthropic` client entirely. Adds a new system prompt instructing Mistral to restyle the newsletter text as a Medium blog post, sent via `mistral-medium-latest` (matching the model already used by `reformat_newsletter.py`, since this is the same quality bar — a polish/restyle task, not a scoring task). `get_mistral_client()` is copied into this file rather than shared from a utils module, following this codebase's existing convention of duplicating small client-init helpers per file (see `get_client()` already duplicated across all three generators today). Image insertion — currently done inline by tracking project index during generation — becomes a post-processing step: after the Mistral call returns, locate each image-slot project's name in the reformatted text and insert its image markdown immediately after. If a project name can't be matched in the rewritten text, that image is skipped rather than erroring.
- **`generate_reddit_post.py`** — same pattern as Medium, simpler (no images, no consistency pass): one Mistral call (`mistral-medium-latest`) with a Reddit-toned system prompt.
- **`reformat_newsletter.py`** — untouched. Its existing job (polishing the newsletter's own structure) is unrelated to this change. It's useful prior art only: the call pattern it already uses (read saved delivery file → single Mistral call with a system prompt → save output) is the same shape the new Medium/Reddit code reuses.

## Data Flow

1. `auto_script_generator.py` writes `posts_data.json` — unchanged.
2. `video_automated.py` runs, writes `posts_data_longform.json` — unchanged.
3. `generate_newsletter.py` runs, writes `deliveries/{date}/SUBSTACK_NEWSLETTER.txt` — unchanged content/logic.
4. `generate_medium_post.py` runs: reads that file, makes 1 Mistral call, writes `deliveries/{date}/MEDIUM_POST.md`. Still reads `posts_data.json` separately, but only for image-path lookups, not prose.
5. `generate_reddit_post.py` runs: reads the newsletter file, makes 1 Mistral call, writes `deliveries/{date}/REDDIT_POST.md`.
6. `generate_description.py` runs — unchanged.

Steps 4 and 5 no longer drive prose generation from `posts_data.json` at all.

## Error Handling

If `SUBSTACK_NEWSLETTER.txt`/`.md` doesn't exist when Medium or Reddit runs (e.g. newsletter generation failed upstream), the reformatter prints a clear error and exits without writing output, mirroring `find_latest_newsletter()`'s existing `None`-return contract. `workflow_manager.py` already logs a warning and continues to the next step on any step failure rather than aborting the whole run, so a missing newsletter file produces a missing Medium/Reddit file for that day (visible in the delivery folder and console log), not a crash.

## Testing

There's no existing automated test suite for this project, so verification is manual/comparative rather than unit-tested:

- Run the new pipeline against the most recent real `posts_data.json` batch and compare the Mistral-reformatted Medium/Reddit output side-by-side against the last Sonnet-generated versions, for tone and completeness.
- Add one cheap programmatic safety check: after each reformat call, confirm every project's `github_url` from `posts_data.json` still appears somewhere in the output text, and log a warning (don't fail the run) if any are missing — the "keep all original URLs" instruction in the system prompt is just an instruction, not a guarantee.

## Out of Scope

- `auto_script_generator.py` (Haiku) and the DeepSeek enrichment step are untouched — already appropriately cheap.
- No changes to AINewsletter/ainewstool.
- Splitting AINewsletter and opensourcescribes onto separate Anthropic API keys (for clean billing attribution) is a good follow-up but is an ops/credentials change, not a code design — not included here.
