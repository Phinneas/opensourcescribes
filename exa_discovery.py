#!/usr/bin/env python3
"""
exa_discovery.py - Exa-powered repository discovery for OpenSourceScribes.

Two discovery strategies:
  1. Keyword search  — broad queries for trending OSS repos in AI/dev tooling
  2. find_similar()  — seeded from top-performing repo URLs to surface similar content

Implements the DiscoverySource interface from discovery_sources.py.

Usage (standalone):
    python exa_discovery.py                    # run both strategies, print results
    python exa_discovery.py --mode keyword     # keyword search only
    python exa_discovery.py --mode similar     # find_similar only
    python exa_discovery.py --append           # append new finds to posts_data.json queue file
"""

import json
import os
import re
import sys
import argparse
from datetime import datetime
from typing import List, Optional

from discovery_sources import DiscoverySource, RepoCandidate

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Load config for API key
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(_CONFIG_PATH) as _f:
    _CONFIG = json.load(_f)

EXA_API_KEY: str = _CONFIG.get("exa", {}).get("api_key", "")

# Dedup sources — URLs in these files are considered already seen
POSTS_DATA_FILE = "posts_data.json"
REPO_HISTORY_FILE = "repo_history.json"

# ---------------------------------------------------------------------------
# Seed repos for find_similar() — top-performing videos by audience signal
# ---------------------------------------------------------------------------

SEED_REPOS: List[str] = [
    # Your top-performing video subjects — Exa finds repos that audiences of these
    # would also want to watch. Update this list as new top performers emerge.
    "https://github.com/AgenTool/Hermes-Agent",            # top performer (update slug if needed)
    "https://github.com/karpathy/nanoGPT",                  # Karpathy / high-authority AI signal
    "https://github.com/OpenVikings/openviking",            # OpenViking
    "https://github.com/anthropics/anthropic-sdk-python",  # agent tooling signal
]

# ---------------------------------------------------------------------------
# Keyword queries for broad discovery
# ---------------------------------------------------------------------------

SEARCH_QUERIES: List[str] = [
    "open source AI agent framework github",
    "new github repository LLM tool developer 2024 2025",
    "open source coding assistant github stars trending",
    "AI developer tools open source launch",
    "github.com python AI agent autonomous",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_GITHUB_RE = re.compile(r"https?://github\.com/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+")


def _extract_github_url(url: str) -> Optional[str]:
    """Normalise a URL to a clean github.com/owner/repo form, or None."""
    m = _GITHUB_RE.search(url)
    if not m:
        return None
    # Strip trailing slashes / extra path segments beyond owner/repo
    parts = m.group(0).rstrip("/").split("/")
    if len(parts) < 5:
        return None
    return "/".join(parts[:5])


GITHUB_URLS_FILE = "github_urls.txt"  # canonical published-URL log


def _load_seen_urls() -> set:
    """Collect all GitHub URLs already published or in-pipeline so we can skip them."""
    seen = set()

    # github_urls.txt — canonical seen-list, updated after every pipeline run
    if os.path.exists(GITHUB_URLS_FILE):
        with open(GITHUB_URLS_FILE) as f:
            for line in f:
                u = line.strip()
                if u:
                    seen.add(u.rstrip("/").lower())

    # posts_data.json — current batch queued for the next run
    if os.path.exists(POSTS_DATA_FILE):
        try:
            with open(POSTS_DATA_FILE) as f:
                for item in json.load(f):
                    u = item.get("github_url", "")
                    if u:
                        seen.add(u.rstrip("/").lower())
        except Exception:
            pass

    # repo_history.json — legacy history (may be a list or dict)
    if os.path.exists(REPO_HISTORY_FILE):
        try:
            with open(REPO_HISTORY_FILE) as f:
                data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    u = item.get("url", item.get("github_url", ""))
                    if u:
                        seen.add(u.rstrip("/").lower())
            elif isinstance(data, dict):
                for u in data.keys():
                    seen.add(u.rstrip("/").lower())
        except Exception:
            pass

    return seen


# ---------------------------------------------------------------------------
# DiscoverySource implementations
# ---------------------------------------------------------------------------

class ExaKeywordSource(DiscoverySource):
    """Discovers repos via Exa keyword/neural search queries."""

    def __init__(self, api_key: str, num_results_per_query: int = 10):
        self._api_key = api_key
        self._num_results = num_results_per_query

    @property
    def source_name(self) -> str:
        return "exa_keyword"

    def fetch(self) -> List[RepoCandidate]:
        from exa_py import Exa  # type: ignore
        client = Exa(api_key=self._api_key)
        seen = _load_seen_urls()
        candidates: List[RepoCandidate] = []
        found_urls: set = set()

        for query in SEARCH_QUERIES:
            print(f"  [exa_keyword] Searching: {query!r}")
            try:
                results = client.search(
                    query,
                    num_results=self._num_results,
                    include_domains=["github.com"],
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
                print(f"  [exa_keyword] Query failed ({query!r}): {e}")

        print(f"  [exa_keyword] Found {len(candidates)} new candidates")
        return candidates


class ExaSimilarSource(DiscoverySource):
    """Discovers repos via Exa find_similar() seeded from top-performing videos."""

    def __init__(self, api_key: str, seed_urls: Optional[List[str]] = None,
                 num_results_per_seed: int = 20):
        self._api_key = api_key
        self._seeds = seed_urls or SEED_REPOS
        self._num_results = num_results_per_seed

    @property
    def source_name(self) -> str:
        return "exa_similar"

    def fetch(self) -> List[RepoCandidate]:
        from exa_py import Exa  # type: ignore
        client = Exa(api_key=self._api_key)
        seen = _load_seen_urls()
        candidates: List[RepoCandidate] = []
        found_urls: set = set()

        for seed_url in self._seeds:
            print(f"  [exa_similar] find_similar seeded from: {seed_url}")
            try:
                results = client.find_similar(
                    url=seed_url,
                    num_results=self._num_results,
                    exclude_source_domain=False,
                    include_domains=["github.com"],
                )
                for r in results.results:
                    clean = _extract_github_url(r.url)
                    if not clean:
                        continue
                    # Skip the seed itself
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
                print(f"  [exa_similar] Seed failed ({seed_url}): {e}")

        print(f"  [exa_similar] Found {len(candidates)} new candidates")
        return candidates


# ---------------------------------------------------------------------------
# Combined runner
# ---------------------------------------------------------------------------

class ExaDiscovery:
    """
    Runs both Exa strategies and returns a deduplicated list of RepoCandidate.

    Usage:
        discovery = ExaDiscovery()
        candidates = discovery.run()   # -> List[RepoCandidate]
    """

    def __init__(self, api_key: Optional[str] = None,
                 seed_urls: Optional[List[str]] = None):
        self._api_key = api_key or EXA_API_KEY
        if not self._api_key:
            raise ValueError(
                "Exa API key not found. Add it to config.json under exa.api_key "
                "or pass it directly."
            )
        self._seeds = seed_urls or SEED_REPOS

    def run(self, mode: str = "both") -> List[RepoCandidate]:
        """
        Args:
            mode: 'keyword', 'similar', or 'both'
        Returns:
            Deduplicated list of RepoCandidate sorted by source then URL.
        """
        all_candidates: List[RepoCandidate] = []

        if mode in ("keyword", "both"):
            src = ExaKeywordSource(self._api_key)
            all_candidates.extend(src.fetch())

        if mode in ("similar", "both"):
            src = ExaSimilarSource(self._api_key, seed_urls=self._seeds)
            all_candidates.extend(src.fetch())

        # Final global dedup across both strategies
        seen_keys: set = set()
        deduped: List[RepoCandidate] = []
        for c in all_candidates:
            key = c.url.lower()
            if key not in seen_keys:
                seen_keys.add(key)
                deduped.append(c)

        print(f"\n[ExaDiscovery] Total new candidates: {len(deduped)}")
        return deduped

    def run_and_print(self, mode: str = "both") -> List[RepoCandidate]:
        candidates = self.run(mode=mode)
        print("\n--- Discovered Repos ---")
        for i, c in enumerate(candidates, 1):
            print(f"  {i:3d}. [{c.source_name}] {c.url}")
        return candidates

    def run_and_append_queue(self, queue_file: str = "exa_discovery_queue.json",
                              mode: str = "both") -> List[RepoCandidate]:
        """
        Discover repos and write them to a JSON queue file for review.
        Does NOT write directly to posts_data.json — keeps human in the loop.
        """
        candidates = self.run(mode=mode)

        # Load existing queue to avoid double-adding
        existing: List[dict] = []
        if os.path.exists(queue_file):
            try:
                with open(queue_file) as f:
                    existing = json.load(f)
            except Exception:
                pass

        existing_urls = {e["url"].lower() for e in existing}
        new_entries = []
        for c in candidates:
            if c.url.lower() not in existing_urls:
                new_entries.append({
                    "url": c.url,
                    "source": c.source_name,
                    "discovered_at": c.discovered_at.isoformat(),
                    "status": "pending",
                })

        combined = existing + new_entries
        with open(queue_file, "w") as f:
            json.dump(combined, f, indent=2)

        print(f"\n[ExaDiscovery] Appended {len(new_entries)} new repos to {queue_file}")
        print(f"               Total queue size: {len(combined)}")
        return candidates


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _parse_args():
    p = argparse.ArgumentParser(description="Exa-powered OSS repo discovery")
    p.add_argument(
        "--mode", choices=["keyword", "similar", "both"], default="both",
        help="Which Exa strategy to run (default: both)"
    )
    p.add_argument(
        "--append", action="store_true",
        help="Append results to exa_discovery_queue.json for review"
    )
    p.add_argument(
        "--queue-file", default="exa_discovery_queue.json",
        help="Queue file path (default: exa_discovery_queue.json)"
    )
    p.add_argument(
        "--api-key", default="",
        help="Exa API key (overrides config.json)"
    )
    return p.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    api_key = args.api_key or EXA_API_KEY

    if not api_key:
        print("ERROR: No Exa API key found.")
        print("  Add it to config.json: { \"exa\": { \"api_key\": \"YOUR_KEY\" } }")
        print("  Or pass --api-key YOUR_KEY")
        sys.exit(1)

    discovery = ExaDiscovery(api_key=api_key)

    if args.append:
        discovery.run_and_append_queue(queue_file=args.queue_file, mode=args.mode)
    else:
        discovery.run_and_print(mode=args.mode)
