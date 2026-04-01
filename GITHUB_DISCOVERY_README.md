# GitHub Discovery System

Automated OSS discovery and queueing for OpenSourceScribes. discovers 15 high-signal open-source repositories weekly using GitHub Trending and GitHub Search API, ranks them with Mistral, and writes to the processing queue.

## Features

- **Dual Discovery Sources**: GitHub Trending (weekly + monthly) + GitHub Search API
- **Star Velocity Tracking**: Calculates growth rates using existing `github_stats_cache.json`
- **Hard Filtering**: Excludes archived, stale (>30d), forks, no-description, and duplicates
- **AI-Powered Ranking**: Mistral agent scores repos on momentum, content potential, and AI relevance
- **Deduplication**: Permanent history in `repo_history.json` prevents repeats
- **Run Artifacts**: Detailed audit logs in `discovery_runs/YYYY-MM-DD.json`

## Installation

### Dependencies

The project uses a virtual environment. Dependencies are already installed:

```bash
venv/bin/python -m pip install selenium mistralai requests
```

### Configuration

#### 1. GitHub Token (Required)

Set your GitHub personal access token as an environment variable:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Token must have `public_repo` scope. Create one at:
https://github.com/settings/tokens

#### 2. Mistral API Key (Required)

Your Mistral API key is already in `config.json`. Verify:

```bash
cat config.json | grep -A2 mistral
```

Should show: `api_key: "your_mistral_key"`

## Quick Start

### Dry Run (Test without writing)

Test the pipeline without modifying files:

```bash
venv/bin/python github_discovery.py --dry-run --search-only
```

### Standard Run (Discovery + Writing)

Full pipeline with all sources:

```bash
venv/bin/python github_discovery.py
```

This will:
1. Discover candidates from GitHub Trending and Search API
2. Enrich data via GitHub REST API
3. Filter out archived/stale/duplicate repos
4. Score with Mistral and rank by score
5. Write 15 URLs to `github_urls.txt`
6. Update dedup history in `repo_history.json`
7. Save artifact to `discovery_runs/YYYY-MM-DD.json`

## CLI Options

```bash
# Standard run (all sources)
venv/bin/python github_discovery.py

# Preview without writing
venv/bin/python github_discovery.py --dry-run

# Skip GitHub Trending (faster, no Selenium)
venv/bin/python github_discovery.py --no-trending

# Use only Search API
venv/bin/python github_discovery.py --search-only

# Visible browser for debugging
venv/bin/python github_discovery.py --no-headless

# Custom target count
venv/bin/python github_discovery.py --target 10
```

## Pipeline Architecture

```
┌─────────────────────────────────────┐
│         Discovery Layer             │
│  ┌──────────────┐ ┌───────────────┐ │
│  │ GitHub       │ │ GitHub Search │ │
│  │ Trending     │ │ API           │ │
│  │ (wk + mo)    │ │ (30d window)  │ │
│  └──────┬───────┘ └───────┬───────┘ │
│         └────────┬─────────┘        │
└──────────────────┼──────────────────┘
                   │ raw candidate URLs
                   ▼
        ┌──────────────────────┐
        │  GitHub REST API     │
        │  Data Fetcher        │
        │  (stats + README)    │
        └──────────┬───────────┘
                   │ enriched candidates
                   ▼
        ┌──────────────────────┐
        │  Hard Filter         │
        │  (archived, stale,   │
        │   dedup, no desc)    │
        └──────────┬───────────┘
                   │ filtered candidates
                   ▼
        ┌──────────────────────┐
        │  Mistral Agent       │
        │  Score + Rank + Reason│
        └──────────┬───────────┘
                   │ top 15
                   ▼
        ┌──────────────────────┐
        │  Output Writer       │
        │  github_urls.txt     │
        │  repo_history.json   │
        │  discovery_runs/     │
        └──────────────────────┘
```

## Output Files

### github_urls.txt
Active processing queue. Script appends 15 new URLs each run.

### repo_history.json
Permanent append-only dedup history. Never truncated.

```json
{
  "owner/repo": {
    "url": "https://github.com/owner/repo",
    "added_at": "2026-03-31T00:00:00Z",
    "run_id": "2026-03-31"
  }
}
```

### discovery_runs/YYYY-MM-DD.json
Detailed run artifact for auditability.

```json
{
  "run_id": "2026-03-31",
  "timestamp": "2026-03-31T12:00:00Z",
  "summary": {
    "candidates_before_filtering": 45,
    "candidates_after_filtering": 22,
    "repos_scored": 22,
    "repos_selected": 15
  },
  "all_scored_repos": [
    {
      "full_name": "owner/repo",
      "url": "https://github.com/owner/repo",
      "score": 8.5,
      "reason": "High-growth AI framework",
      "stars": 5000,
      "velocity": 25.0,
      "language": "Python",
      "description": "..."
    }
  ],
  "selected_repos": [...]
}
```

## Module Files

- `github_discovery.py` - Main orchestration script
- `discovery_sources.py` - Discovery source interface
- `github_trending_scraper.py` - GitHub Trending via Selenium
- `github_api_fetcher.py` - GitHub API client + velocity calculator
- `repo_filter.py` - Hard filtering logic
- `mistral_scorer.py` - Mistral scoring agent
- `output_writer.py` - Output writing logic

## Troubleshooting

### "GITHUB_TOKEN not set"
```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

### "Mistral API key not found"
Check `config.json` has valid `mistral.api_key`:
```bash
cat config.json
```

### Selenium/chromedriver issues
Skip trending and use only search API:
```bash
venv/bin/python github_discovery.py --search-only
```

### No repositories found
This is normal if:
- All candidates are archived/stale/forks
- All candidates already in history/queue
- No candidates have velocity data in cache

Run without velocity requirement to test:
Edit `repo_filter.py`, set `require_velocity=False` in `filter_candidates()` call.

## Integration with Existing System

The discovery system integrates with existing OpenSourceScribes files:

- **Uses**: `config.json` (Mistral API key), `github_stats_cache.json` (velocity baseline)
- **Writes**: `github_urls.txt` (queue), `repo_history.json` (new), `discovery_runs/` (new)

## Weekly Workflow

1. Clear consumed repos from `github_urls.txt` manually:
   ```bash
   # Or keep adding new ones, script deduplicates
   ```

2. Run discovery:
   ```bash
   venv/bin/python github_discovery.py
   ```

3. Review artifact in `discovery_runs/` for transparency

4. Process queue as normal (videos, newsletters, etc.)

## Success Criteria

✓ Each weekly run adds exactly 15 net-new repos to queue
✓ No repo appears that has been covered before
✓ No archived or unmaintained repo (last commit > 30 days)
✓ Mistral provides scored + annotated candidate list as artifact
