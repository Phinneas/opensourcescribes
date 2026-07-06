# ClickHouse GitTrends + Scrapling Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `ClickHouseGitTrendsSource` as a third discovery source in the legacy `github_discovery.py` pipeline, and replace the Selenium-based `GitHubTrendingSource` scraper with Scrapling so it no longer depends on a local Chrome/chromedriver install.

**Architecture:** `github_discovery.py`'s `GitHubDiscoveryPipeline` already loops over a list of `DiscoverySource` objects and calls `.fetch()` on each (falling back to a generic branch unless the source is `GitHubSearchAPISource`, which needs extra kwargs). `ClickHouseGitTrendsSource.fetch(self, seen: set = None)` already matches that generic-branch signature (its `seen` param defaults to `None`), so it can be added to `self.sources` with zero changes to the dispatch loop. Deduplication against previously-published repos already happens downstream in `RepoFilter` via `repo_history.json`, so no new dedup plumbing is needed. Separately, `GitHubTrendingSource` (`discovery/github_trending_scraper.py`) is rewritten to use Scrapling's `StealthyFetcher` instead of raw Selenium/chromedriver, keeping the exact same `DiscoverySource` interface (`fetch() -> List[RepoCandidate]`, `source_name` property, `headless` constructor arg) so `github_discovery.py` needs no changes to consume it.

**Tech Stack:** Python 3.13 (project venv at `venv/`), `scrapling[fetchers]` (new dependency, replaces `selenium`), existing `requests`-based `ClickHouseGitTrendsSource`.

**Assumption to confirm before starting:** this plan targets `github_discovery.py` — the older pipeline that still uses Selenium and doesn't yet call ClickHouse. The currently-active automation (`run_full_pipeline.py`) actually runs `exa_discovery.py`, which already wires in `ClickHouseGitTrendsSource`. If you intended to change `exa_discovery.py` instead, stop and say so — the tasks below don't touch it.

**No test framework exists in this repo** (no `pytest.ini`/`pyproject.toml`/`tests/` dir). The established verification convention here is each module's own `demo()` / `if __name__ == "__main__"` block plus `github_discovery.py --dry-run`. This plan follows that convention instead of introducing pytest.

---

## File Structure

- **Modify:** `discovery/github_trending_scraper.py` — full rewrite of `GitHubTrendingSource`, Selenium → Scrapling. Same public interface, so no caller changes needed.
- **Modify:** `discovery/github_discovery.py` — add `ClickHouseGitTrendsSource` as a third source: one new import, one new constructor param + `self.sources.append(...)` block, one new CLI flag. No changes to `discover_candidates()`'s dispatch logic (see Architecture above).
- **No changes needed:** `discovery/clickhouse_discovery.py` (already correct, reused as-is), `discovery/discovery_sources.py` (base interface already compatible).

---

### Task 1: Install Scrapling into the project venv

**Files:** none (environment setup only)

- [ ] **Step 1: Install Scrapling's fetcher extras**

```bash
cd ~/Desktop/opensourcescribes
venv/bin/pip install "scrapling[fetchers]"
```

Expected: pip resolves and installs `scrapling` plus its fetcher dependencies (playwright/camoufox and friends) without errors.

- [ ] **Step 2: Download Scrapling's browser binaries**

```bash
venv/bin/scrapling install
```

Expected: downloads browser binaries + fingerprint-manipulation dependencies. Takes a few minutes on first run. Exits 0.

- [ ] **Step 3: Verify the import works**

```bash
venv/bin/python -c "from scrapling.fetchers import StealthyFetcher; print('scrapling ok')"
```

Expected output: `scrapling ok`

- [ ] **Step 4: Commit the dependency change**

This repo has no `requirements.txt`/`pyproject.toml` to update (dependencies are installed ad hoc into `venv/`, which is gitignored via no explicit rule but never committed — confirm with `git status` that `venv/` doesn't show up). Nothing to commit for this task; skip straight to Task 2.

---

### Task 2: Replace Selenium with Scrapling in `GitHubTrendingSource`

**Files:**
- Modify (full rewrite): `discovery/github_trending_scraper.py`

- [ ] **Step 1: Replace the entire file contents**

Replace all of `discovery/github_trending_scraper.py` with:

```python
#!/usr/bin/env python3
"""
GitHub Trending scraper using Scrapling for client-side rendered pages.
Scrapes weekly and monthly trending repos.
"""

from datetime import datetime
from typing import List
from scrapling.fetchers import StealthyFetcher
from discovery.discovery_sources import DiscoverySource, RepoCandidate

# Let Scrapling re-locate the repo card selector automatically if GitHub
# changes its markup (see: https://scrapling.readthedocs.io/en/latest/parsing/adaptive.html)
StealthyFetcher.adaptive = True


class GitHubTrendingSource(DiscoverySource):
    """
    GitHub Trending discovery source using Scrapling.
    Scrape weekly and monthly trending repositories.
    """

    BASE_URL = "https://github.com/trending"
    CARD_SELECTOR = "article.Box-row"

    def __init__(self, headless: bool = True):
        """
        Initialize GitHub Trending scraper.

        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless

    @property
    def source_name(self) -> str:
        return "GitHub Trending"

    def _fetch_trending_page(self, timeframe: str) -> List[str]:
        """
        Fetch trending repository URLs for a specific timeframe.

        Args:
            timeframe: 'weekly' or 'monthly'

        Returns:
            List of repository URLs
        """
        urls = []

        if timeframe not in ['weekly', 'monthly']:
            raise ValueError("timeframe must be 'weekly' or 'monthly'")

        url = f"{self.BASE_URL}?since={timeframe}"

        print(f"Fetching {timeframe} trending...")

        try:
            page = StealthyFetcher.fetch(
                url,
                headless=self.headless,
                wait_selector=self.CARD_SELECTOR,
                wait_selector_state="visible",
            )

            repo_cards = page.css(self.CARD_SELECTOR, auto_save=True)
            if not repo_cards:
                # Selector didn't match (GitHub changed its markup) — let
                # Scrapling's adaptive matcher find the relocated element.
                repo_cards = page.css(self.CARD_SELECTOR, adaptive=True)

            for card in repo_cards:
                links = card.css("h2 a")
                if not links:
                    continue

                href = links[0].attrib.get("href")
                if not href:
                    continue

                repo_url = page.urljoin(href)

                if repo_url.startswith("https://github.com/"):
                    urls.append(repo_url)

            print(f"  Found {len(urls)} repos")

        except Exception as e:
            print(f"  Error scraping {timeframe} trending: {e}")

        return urls

    def fetch(self) -> List[RepoCandidate]:
        """
        Fetch trending repository candidates from both weekly and monthly lists.

        Returns:
            List of RepoCandidate objects (deduplicated)
        """
        weekly_urls = self._fetch_trending_page("weekly")
        monthly_urls = self._fetch_trending_page("monthly")

        all_urls = weekly_urls + monthly_urls
        seen_urls = set()
        unique_urls = []

        for url in all_urls:
            if url not in seen_urls:
                seen_urls.add(url)
                unique_urls.append(url)

        candidates = [
            RepoCandidate(
                url=url,
                source_name=self.source_name,
                discovered_at=datetime.now()
            )
            for url in unique_urls
        ]

        return candidates


def demo():
    """Demo function to test GitHub Trending scraper."""
    print("GitHub Trending Scraper Demo")
    print("=" * 50)

    try:
        scraper = GitHubTrendingSource(headless=True)
        candidates = scraper.fetch()

        print(f"\nTotal candidates found: {len(candidates)}")

        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate.url}")

        print("\nDemo completed successfully!")

    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nRequirements for this demo:")
        print('1. Install Scrapling: pip install "scrapling[fetchers]"')
        print("2. Run: scrapling install")


if __name__ == "__main__":
    demo()
```

This removes the `_init_driver`/`_cleanup_driver`/Selenium-options plumbing entirely — Scrapling's `StealthyFetcher.fetch()` spins up and tears down its own browser per call, so there's no driver lifecycle to manage for just two fetches (weekly + monthly).

- [ ] **Step 2: Run the module's demo to verify it works standalone**

```bash
cd ~/Desktop/opensourcescribes
venv/bin/python -m discovery.github_trending_scraper
```

Expected: prints "Fetching weekly trending...", "Found N repos", "Fetching monthly trending...", "Found N repos", then lists up to 5 candidate URLs starting with `https://github.com/`. N should be > 0 (GitHub's trending page always has repos). If N is 0 for both, re-check `CARD_SELECTOR` against the live page HTML before proceeding.

- [ ] **Step 3: Commit**

```bash
git add discovery/github_trending_scraper.py
git commit -m "refactor: replace Selenium with Scrapling in GitHubTrendingSource"
```

---

### Task 3: Wire `ClickHouseGitTrendsSource` into `github_discovery.py`

**Files:**
- Modify: `discovery/github_discovery.py:30-105` (imports + `__init__`)
- Modify: `discovery/github_discovery.py:384-426` (CLI args + source-usage flags)

- [ ] **Step 1: Add the import**

In `discovery/github_discovery.py`, find this block near the top (around line 31):

```python
try:
    from discovery.discovery_sources import RepoCandidate
    from discovery.github_api_fetcher import GitHubAPIClient, StarVelocityCalculator, GitHubSearchAPISource
    from discovery.github_trending_scraper import GitHubTrendingSource
    from discovery.repo_filter import RepoFilter, EnrichedRepo
    from utils.mistral_scorer import MistralScorer
    from content.output_writer import OutputWriter
except ImportError as e:
```

Replace with:

```python
try:
    from discovery.discovery_sources import RepoCandidate
    from discovery.github_api_fetcher import GitHubAPIClient, StarVelocityCalculator, GitHubSearchAPISource
    from discovery.github_trending_scraper import GitHubTrendingSource
    from discovery.clickhouse_discovery import ClickHouseGitTrendsSource
    from discovery.repo_filter import RepoFilter, EnrichedRepo
    from utils.mistral_scorer import MistralScorer
    from content.output_writer import OutputWriter
except ImportError as e:
```

- [ ] **Step 2: Update the pipeline docstring**

Find (around line 44-54):

```python
class GitHubDiscoveryPipeline:
    """
    Main orchestration class for automated OSS discovery.
    
    Pipeline:
    1. Discovery sources → raw candidate URLs
    2. GitHub API → enriched repo data + velocity
    3. Hard filters →_filtered candidates
    4. Mistral scoring → ranked repos
    5. Output writer → queue + history + artifacts
    """
```

Replace the `Pipeline:` line with:

```python
    Pipeline:
    1. Discovery sources (GitHub Search API + GitHub Trending + ClickHouse GitTrends) → raw candidate URLs
    2. GitHub API → enriched repo data + velocity
    3. Hard filters →_filtered candidates
    4. Mistral scoring → ranked repos
    5. Output writer → queue + history + artifacts
    """
```

- [ ] **Step 3: Add the `use_clickhouse` constructor param and source registration**

Find the full `__init__` method:

```python
    def __init__(
        self,
        use_trending: bool = True,
        use_search: bool = True,
        dry_run: bool = False,
        headless: bool = True
    ):
        """
        Initialize discovery pipeline.
        
        Args:
            use_trending: Include GitHub Trending scraper (Selenium required)
            use_search: Include GitHub Search API
            dry_run: Preview without writing outputs
            headless: Run Selenium in headless mode
        """
        self.use_trending = use_trending
        self.use_search = use_search
        self.dry_run = dry_run
        
        print("Initializing GitHub Discovery Pipeline...")
        print("=" * 60)
        
        # Initialize components
        self.api_client = GitHubAPIClient()
        self.velocity_calc = StarVelocityCalculator()
        self.repo_filter = RepoFilter()
        self.output_writer = OutputWriter()
        
        # Initialize sources
        self.sources = []
        
        if use_search:
            print("Configuring GitHub Search API source...")
            self.search_source = GitHubSearchAPISource(self.api_client, self.velocity_calc)
            self.sources.append(self.search_source)
        
        if use_trending:
            print("Configuring GitHub Trending scraper...")
            try:
                self.trending_source = GitHubTrendingSource(headless=headless)
                self.sources.append(self.trending_source)
            except Exception as e:
                print(f"Warning: Could not initialize Trending scraper: {e}")
                print("Continuing with Search API only.")
                self.use_trending = False
```

Replace with:

```python
    def __init__(
        self,
        use_trending: bool = True,
        use_search: bool = True,
        use_clickhouse: bool = True,
        dry_run: bool = False,
        headless: bool = True
    ):
        """
        Initialize discovery pipeline.
        
        Args:
            use_trending: Include GitHub Trending scraper (Scrapling required)
            use_search: Include GitHub Search API
            use_clickhouse: Include ClickHouse GitTrends source
            dry_run: Preview without writing outputs
            headless: Run the trending scraper's browser in headless mode
        """
        self.use_trending = use_trending
        self.use_search = use_search
        self.use_clickhouse = use_clickhouse
        self.dry_run = dry_run
        
        print("Initializing GitHub Discovery Pipeline...")
        print("=" * 60)
        
        # Initialize components
        self.api_client = GitHubAPIClient()
        self.velocity_calc = StarVelocityCalculator()
        self.repo_filter = RepoFilter()
        self.output_writer = OutputWriter()
        
        # Initialize sources
        self.sources = []
        
        if use_search:
            print("Configuring GitHub Search API source...")
            self.search_source = GitHubSearchAPISource(self.api_client, self.velocity_calc)
            self.sources.append(self.search_source)
        
        if use_trending:
            print("Configuring GitHub Trending scraper...")
            try:
                self.trending_source = GitHubTrendingSource(headless=headless)
                self.sources.append(self.trending_source)
            except Exception as e:
                print(f"Warning: Could not initialize Trending scraper: {e}")
                print("Continuing without it.")
                self.use_trending = False
        
        if use_clickhouse:
            print("Configuring ClickHouse GitTrends source...")
            self.clickhouse_source = ClickHouseGitTrendsSource()
            self.sources.append(self.clickhouse_source)
```

Note: no changes are needed in `discover_candidates()`. Its dispatch loop already does:
```python
if isinstance(source, GitHubSearchAPISource):
    candidates = source.fetch(per_page=..., days_back=...)
else:
    candidates = source.fetch()
```
`ClickHouseGitTrendsSource.fetch(self, seen: set = None)` falls into the `else` branch and works with zero args since `seen` defaults to `None`.

- [ ] **Step 4: Add the `--no-clickhouse` CLI flag**

Find (around line 389-398):

```python
    parser.add_argument(
        "--no-trending",
        action="store_true",
        help="Skip GitHub Trending scraper (no Selenium needed)"
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Use only GitHub Search API (implies --no-trending)"
    )
```

Replace with:

```python
    parser.add_argument(
        "--no-trending",
        action="store_true",
        help="Skip GitHub Trending scraper"
    )
    parser.add_argument(
        "--no-clickhouse",
        action="store_true",
        help="Skip ClickHouse GitTrends source"
    )
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Use only GitHub Search API (implies --no-trending and --no-clickhouse)"
    )
```

- [ ] **Step 5: Wire the flag into pipeline construction**

Find (around line 413-426):

```python
    # Determine source usage
    use_trending = not args.no_trending and not args.search_only
    use_search = True
    
    # Headless mode
    headless = not args.no_headless
    
    try:
        pipeline = GitHubDiscoveryPipeline(
            use_trending=use_trending,
            use_search=use_search,
            dry_run=args.dry_run,
            headless=headless
        )
```

Replace with:

```python
    # Determine source usage
    use_trending = not args.no_trending and not args.search_only
    use_clickhouse = not args.no_clickhouse and not args.search_only
    use_search = True
    
    # Headless mode
    headless = not args.no_headless
    
    try:
        pipeline = GitHubDiscoveryPipeline(
            use_trending=use_trending,
            use_search=use_search,
            use_clickhouse=use_clickhouse,
            dry_run=args.dry_run,
            headless=headless
        )
```

- [ ] **Step 6: Verify with a dry run**

```bash
cd ~/Desktop/opensourcescribes
venv/bin/python -m discovery.github_discovery --dry-run
```

Expected: console output shows all three sources configured ("Configuring GitHub Search API source...", "Configuring GitHub Trending scraper...", "Configuring ClickHouse GitTrends source..."), then the DISCOVERY PHASE section shows `Running GitHub Search API...`, `Running GitHub Trending...`, and `Running clickhouse_gittrends...` each reporting a candidate count, then proceeds through enrichment/filtering/scoring and ends with `DRY RUN MODE - Skipping output writes` (no files written).

- [ ] **Step 7: Verify `--no-clickhouse` and `--search-only` still work**

```bash
venv/bin/python -m discovery.github_discovery --dry-run --no-clickhouse
venv/bin/python -m discovery.github_discovery --dry-run --search-only
```

Expected: first command's output configures Search API + Trending only (no "Configuring ClickHouse..." line). Second command's output configures Search API only.

- [ ] **Step 8: Commit**

```bash
git add discovery/github_discovery.py
git commit -m "feat: wire ClickHouseGitTrendsSource into github_discovery pipeline"
```

---

### Task 4: Remove the now-unused Selenium dependency

**Files:** none (environment cleanup only)

- [ ] **Step 1: Confirm nothing else imports selenium**

```bash
cd ~/Desktop/opensourcescribes
grep -rln "import selenium\|from selenium" --include="*.py" . | grep -v venv
```

Expected: no output (empty). If anything prints, stop — something else still depends on selenium and it shouldn't be removed.

- [ ] **Step 2: Uninstall selenium from the venv**

```bash
venv/bin/pip uninstall -y selenium
```

Expected: uninstalls cleanly.

- [ ] **Step 3: Final full pipeline smoke test**

```bash
venv/bin/python -m discovery.github_discovery --dry-run
```

Expected: same as Task 3 Step 6 — all three sources run successfully with selenium no longer installed, proving the trending source no longer depends on it.

- [ ] **Step 4: Commit**

No source files change in this task (only the venv, which isn't tracked in git) — nothing to commit. Confirm with `git status` that the working tree is clean aside from the two commits already made in Tasks 2 and 3.

---

## Self-Review Notes

- **Spec coverage:** "wire in the clickhouse tool" → Task 3. "switch the selenium code to use scrapling instead" → Tasks 1, 2, 4 (install, rewrite, remove old dep). Both halves of the request covered.
- **No placeholders:** every step has literal code, exact commands, and expected output — no "add error handling" or "similar to Task N" hand-waving.
- **Interface consistency:** `GitHubTrendingSource.fetch()` keeps the same zero-arg signature and `source_name`/`headless` members it had before, so `github_discovery.py`'s dispatch loop and constructor call (`GitHubTrendingSource(headless=headless)`) needed no changes. `ClickHouseGitTrendsSource.fetch(seen=None)` matches the loop's generic `else: source.fetch()` branch without modification.
