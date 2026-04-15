#!/usr/bin/env python3
"""
exa_discovery.py - Exa-powered repository auto-discovery for OpenSourceScribes.

Finds 15 fresh repos, writes them to github_urls.txt, then runs the full pipeline.

Usage:
    python exa_discovery.py              # discover + run full pipeline
    python exa_discovery.py --discover-only  # write github_urls.txt, stop there
    python exa_discovery.py --mode keyword   # keyword search only (default: both)
    python exa_discovery.py --mode similar
    python exa_discovery.py --count 10       # override batch size (default: 15)

Files:
    github_urls.txt     — current batch input (overwritten each run with fresh repos)
    published_repos.txt — permanent append-only history used for dedup
"""

import json
import os
import re
import subprocess
import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import List, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from discovery.discovery_sources import DiscoverySource, RepoCandidate
from core.db import DB

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(_CONFIG_PATH) as _f:
    _CONFIG = json.load(_f)

EXA_API_KEY: str = _CONFIG.get("exa", {}).get("api_key", "")

BATCH_SIZE = 15                          # repos per run
GITHUB_URLS_FILE = "github_urls.txt"    # current batch — read by auto_script_generator.py
PUBLISHED_FILE = "published_repos.txt"  # permanent dedup history
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # project root directory

# ---------------------------------------------------------------------------
# Seed repos for find_similar()
# Update this list as new top-performing videos emerge.
# ---------------------------------------------------------------------------

SEED_REPOS: List[str] = [
    "https://github.com/mvschwarz/openrig",
    "https://github.com/666ghj/MiroFish",
    "https://github.com/humanlayer/humanlayer",
    "https://github.com/juspay/neurolink",
    "https://github.com/LogicStamp/logicstamp-context",
    "https://github.com/volcengine/OpenViking",
]

# ---------------------------------------------------------------------------
# Keyword queries for broad discovery
# ---------------------------------------------------------------------------

SEARCH_QUERIES: List[str] = [
    "novel open source approach to browser automation and AI agents github",
    "newly released open source RAG framework or developer tool github",
    "under the radar AI developer tools open source launch github",
    "Y Combinator backed or Hacker News trending open source launch github",
    "high quality developer focused open source projects launched in 2025 github",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GITHUB_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+")


def _extract_github_url(url: str) -> Optional[str]:
    """Normalise to clean github.com/owner/repo, or None."""
    m = _GITHUB_RE.search(url)
    if not m:
        return None
    parts = m.group(0).rstrip("/").split("/")
    if len(parts) < 5:
        return None
    return "/".join(parts[:5])


def _load_published_fallback() -> set:
    """Fallback: load from published_repos.txt if DB unavailable."""
    seen = set()
    if os.path.exists(PUBLISHED_FILE):
        with open(PUBLISHED_FILE) as f:
            for line in f:
                u = line.strip()
                if u:
                    seen.add(u.rstrip("/").lower())
    return seen


def _migrate_published_txt(db: DB) -> None:
    """One-time import of published_repos.txt into SurrealDB (safe to call repeatedly)."""
    if not os.path.exists(PUBLISHED_FILE):
        return
    count = db.import_published_txt(PUBLISHED_FILE)
    if count:
        print(f"[db] Migrated {count} URLs from {PUBLISHED_FILE} into SurrealDB")


# ---------------------------------------------------------------------------
# Discovery sources
# ---------------------------------------------------------------------------

class ExaKeywordSource(DiscoverySource):
    def __init__(self, api_key: str, num_results_per_query: int = 10):
        self._api_key = api_key
        self._num_results = num_results_per_query

    @property
    def source_name(self) -> str:
        return "exa_keyword"

    def fetch(self, seen: set) -> List[RepoCandidate]:
        from exa_py import Exa  # type: ignore
        client = Exa(api_key=self._api_key)
        candidates: List[RepoCandidate] = []
        found_urls: set = set()

        for query in SEARCH_QUERIES:
            print(f"  [keyword] {query!r}")
            try:
                results = client.search(
                    query,
                    num_results=self._num_results,
                    include_domains=["github.com"],
                    start_published_date="2025-10-01",
                    type="neural",
                )
                for r in results.results:
                    clean = _extract_github_url(r.url)
                    if not clean:
                        continue
                    key = clean.lower()
                    if key in seen or key in found_urls:
                        continue
                    found_urls.add(key)
                    candidates.append(RepoCandidate(
                        url=clean,
                        source_name=self.source_name,
                        discovered_at=datetime.now(),
                    ))
            except Exception as e:
                print(f"  [keyword] failed ({query!r}): {e}")

        return candidates


class ExaSimilarSource(DiscoverySource):
    def __init__(self, api_key: str, seed_urls: Optional[List[str]] = None,
                 num_results_per_seed: int = 20):
        self._api_key = api_key
        self._seeds = seed_urls or SEED_REPOS
        self._num_results = num_results_per_seed

    @property
    def source_name(self) -> str:
        return "exa_similar"

    def fetch(self, seen: set) -> List[RepoCandidate]:
        from exa_py import Exa  # type: ignore
        client = Exa(api_key=self._api_key)
        candidates: List[RepoCandidate] = []
        found_urls: set = set()

        for seed_url in self._seeds:
            print(f"  [similar] seeded from {seed_url}")
            try:
                results = client.find_similar(
                    url=seed_url,
                    num_results=self._num_results,
                    exclude_source_domain=False,
                    start_published_date="2025-10-01",
                    include_domains=["github.com"],
                )
                for r in results.results:
                    clean = _extract_github_url(r.url)
                    if not clean:
                        continue
                    if clean.lower() == seed_url.rstrip("/").lower():
                        continue
                    key = clean.lower()
                    if key in seen or key in found_urls:
                        continue
                    found_urls.add(key)
                    candidates.append(RepoCandidate(
                        url=clean,
                        source_name=self.source_name,
                        discovered_at=datetime.now(),
                    ))
            except Exception as e:
                print(f"  [similar] failed ({seed_url}): {e}")

        return candidates


# ---------------------------------------------------------------------------
# Main discovery class
# ---------------------------------------------------------------------------

class ExaDiscovery:

    def __init__(self, api_key: Optional[str] = None, seed_urls: Optional[List[str]] = None):
        self._api_key = api_key or EXA_API_KEY
        if not self._api_key:
            raise ValueError(
                "Exa API key missing. Add to config.json: { \"exa\": { \"api_key\": \"...\" } }"
            )
        self._seeds = seed_urls or SEED_REPOS

    def discover(self, mode: str = "both", count: int = BATCH_SIZE) -> List[str]:
        """
        Run discovery and return up to `count` new repo URLs, deduplicated
        against SurrealDB (falls back to published_repos.txt if DB unavailable).
        """
        try:
            with DB() as db:
                _migrate_published_txt(db)
                seen = {u.lower() for u in db.get_published_urls()}
                seen |= {u.lower() for u in (db.get_pending_repos(limit=500) and
                         [r["url"] for r in db.get_pending_repos(limit=500)])}
        except Exception as e:
            print(f"[db] Warning: could not load from SurrealDB ({e}), falling back to txt")
            seen = _load_published_fallback()

        all_candidates: List[RepoCandidate] = []

        if mode in ("keyword", "both"):
            all_candidates.extend(ExaKeywordSource(self._api_key).fetch(seen))

        if mode in ("similar", "both"):
            all_candidates.extend(ExaSimilarSource(self._api_key, self._seeds).fetch(seen))

        # Global dedup across both strategies
        seen_keys: set = set()
        deduped: List[str] = []
        for c in all_candidates:
            key = c.url.lower()
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(c.url)

        batch = deduped[:count]
        duplicates = len(all_candidates) - len(deduped)
        print(f"\n[ExaDiscovery] {len(deduped)} candidates found ({duplicates} dupes), taking {len(batch)}")

        # Log candidates to DB and record discovery event
        try:
            with DB() as db:
                for url in deduped:
                    name = url.rstrip("/").split("/")[-1]
                    db.upsert_repo(url, name, source=mode)
                db.log_discovery(mode, found=len(all_candidates),
                                 new_repos=len(deduped), duplicates=duplicates)
        except Exception as e:
            print(f"[db] Warning: could not save candidates ({e})")

        return batch

    def run(self, mode: str = "both", count: int = BATCH_SIZE,
            discover_only: bool = False) -> None:
        """
        Full flow:
          1. Discover `count` fresh repos (DB-deduplicated)
          2. Write them to github_urls.txt
          3. Unless --discover-only: run auto_script_generator + video_automated
        """
        batch = self.discover(mode=mode, count=count)

        if not batch:
            print("[ExaDiscovery] No new repos found. Exiting.")
            return

        # Overwrite github_urls.txt with this batch
        with open(GITHUB_URLS_FILE, "w") as f:
            for url in batch:
                f.write(url + "\n")
        print(f"[ExaDiscovery] Wrote {len(batch)} URLs to {GITHUB_URLS_FILE}")
        for url in batch:
            print(f"  {url}")

        if discover_only:
            print("\n[ExaDiscovery] --discover-only set, stopping here.")
            return

        # Run auto_script_generator
        print("\n[ExaDiscovery] Running auto_script_generator...")
        result = subprocess.run(
            [sys.executable, "auto_script_generator.py",
             "--input", GITHUB_URLS_FILE, "--output", "posts_data.json"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode != 0:
            print("[ExaDiscovery] auto_script_generator failed. Stopping.")
            return

        # Run video pipeline
        print("\n[ExaDiscovery] Running video pipeline...")
        result = subprocess.run(
            [sys.executable, "video_automated.py"],
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        if result.returncode != 0:
            print("[ExaDiscovery] video_automated.py failed.")
            return

        print("\n[ExaDiscovery] Done.")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Exa auto-discovery → full pipeline")
    p.add_argument("--mode", choices=["keyword", "similar", "both"], default="both")
    p.add_argument("--count", type=int, default=BATCH_SIZE,
                   help=f"Repos per batch (default: {BATCH_SIZE})")
    p.add_argument("--discover-only", action="store_true",
                   help="Write github_urls.txt and stop — don't run the pipeline")
    p.add_argument("--api-key", default="")
    args = p.parse_args()

    api_key = args.api_key or EXA_API_KEY
    if not api_key:
        print("ERROR: No Exa API key. Add to config.json under exa.api_key")
        sys.exit(1)

    ExaDiscovery(api_key=api_key).run(
        mode=args.mode,
        count=args.count,
        discover_only=args.discover_only,
    )
