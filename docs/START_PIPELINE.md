# Pipeline Command - Quick Start

## Running the Full Pipeline

### Simple Command
```bash
python run_pipeline.py
```

This will:
1. Parse repos from `github_urls.txt` → `posts_data.json`
2. Run Prefect orchestration → videos in `deliveries/MM-DD/`

### Options

**Use different input file:**
```bash
python run_pipeline.py --input my_repos.txt
```

**Skip parsing (use existing posts_data.json):**
```bash
python run_pipeline.py --skip-parse
```

**Custom delivery folder date:**
```bash
python run_pipeline.py --date 04-01
```

**Dry run (validate without running):**
```bash
python run_pipeline.py --dry-run
```

### Help
```bash
python run_pipeline.py --help
```

## What the Pipeline Does

**Phase 1: Parsing**
- Reads GitHub URLs from input file
- Fetches repo data and READMEs via API
- Generates AI narration scripts → `posts_data.json`

**Phase 2: Video Production (Prefect)**
- Generates Seedream background images
- Renders Remotion animations for each repo
- Creates intro, segments, transitions
- Builds YouTube Shorts and Deep Dives
- Produces content suite (Medium, Reddit, newsletter)
- All output → `deliveries/MM-DD/`

## Prerequisites

1. **Input file exists:** `github_urls.txt` with GitHub URLs (one per line)
2. **Prefect server running:** Should be started before running
3. **Dependencies installed:** All Python packages and Node modules

## Complete Example

```bash
# 1. Add repos to process
echo "https://github.com/owner/repo1" >> github_urls.txt
echo "https://github.com/owner/repo2" >> github_urls.txt

# 2. Run full pipeline
python run_pipeline.py

# 3. Find output
ls deliveries/03-31/
```

## Alternative: Manual Command Chaining

If you prefer the original approach:
```bash
python3 simple_parser.py github_urls.txt && ./run_with_prefect.sh orchestration
```

But `run_pipeline.py` is recommended for better error handling and validation.
