# GitHub Repo Fetcher

`fetch_github_repos.py` is a Python script that searches GitHub for trending open-source repositories based on topics, stars, and recency. It filters out duplicates from previous fetches and saves results to a JSON file for manual review.

## What It Does

- Searches GitHub API for repositories matching specified topics
- Filters by minimum star count and recency (days since last update)
- Automatically skips repositories already in your `github_urls.txt` or previous `data/roundup_*.json` files (idempotent)
- Saves results to `data/roundup_YYYY-MM-DD.json` for manual review

## Requirements

- Python 3.x
- GitHub personal access token (stored as `GITHUB_TOKEN` environment variable)
- `requests` library (already installed in venv)

## Setup

1. Get a GitHub personal access token:
   - Go to https://github.com/settings/tokens
   - Generate a new token with `public_repo` scope
   - Save it securely

2. Set the environment variable:
   ```bash
   export GITHUB_TOKEN='your_token_here'
   ```

   Or add it to your shell profile (`.zshrc` or `.bashrc`):
   ```bash
   echo 'export GITHUB_TOKEN="your_token_here"' >> ~/.zshrc
   source ~/.zshrc
   ```

## Usage

### Basic Usage

```bash
python fetch_github_repos.py --topics "ai,webdev" --min-stars 100 --days 7
```

### Examples

```bash
# Search for AI and webdev repos with 100+ stars updated in last 7 days
python fetch_github_repos.py --topics "ai,webdev" --min-stars 100 --days 7

# Search for Python and machine-learning repos with 500+ stars
python fetch_github_repos.py --topics "python,machine-learning" --min-stars 500 --days 14

# Search for more results (up to 20)
python fetch_github_repos.py --topics "open-source,devtools" --max-results 20

# Use default topics (open-source,ai,webdev)
python fetch_github_repos.py
```

### Arguments

- `--topics`: Comma-separated list of topics to search for (default: "open-source,ai,webdev")
- `--min-stars`: Minimum star count required (default: 100)
- `--days`: Number of days to look back for recent updates (default: 7)
- `--max-results`: Maximum number of repositories to return (default: 10)

## Output

The script saves results to `data/roundup_YYYY-MM-DD.json` with the following structure:

```json
[
  {
    "name": "repo-name",
    "url": "https://github.com/owner/repo-name",
    "stars": 123,
    "topics": ["ai", "open-source"],
    "description": "Brief description...",
    "last_updated": "2026-02-13"
  }
]
```

## Workflow

1. Run the script to fetch trending repos
2. Manually review the JSON output in `data/roundup_YYYY-MM-DD.json`
3. Select repositories to include in your roundup
4. Add selected URLs to `github_urls.txt` for your existing workflow

## Idempotent Behavior

The script automatically filters out duplicates by checking:
- Existing `github_urls.txt` file
- All previous `data/roundup_*.json` files

This means you can run the script multiple times without getting the same repositories repeatedly.

## Example Output

```
Topics: ['ai', 'webdev']
Minimum stars: 100
Days: 7
Max results: 10
--------------------------------------------------
Loaded 12 URLs from github_urls.txt
Loaded URLs from roundup_2026-02-05.json
--------------------------------------------------
Searching for repos updated after 2026-02-02
Found 22 repositories from GitHub API
Filtered: 8 new repos, 4 duplicates skipped
--------------------------------------------------
Successfully saved 8 repositories to:
  data/roundup_2026-02-09.json

Next steps:
  1. Review the JSON file manually
  2. Select repos to include in your roundup
  3. Add selected URLs to github_urls.txt
```

## Troubleshooting

**"GITHUB_TOKEN environment variable not set"**
- Make sure you've set the `GITHUB_TOKEN` environment variable before running the script

**"No repositories found"**
- Try increasing the `--days` parameter to look further back
- Try lowering the `--min-stars` threshold
- Check if your topics are valid GitHub topics

**Rate limiting**
- GitHub API has rate limits (60 requests/hour for unauthenticated, 5000/hour with token)
- If you hit the limit, wait an hour before running again
