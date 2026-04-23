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
import random
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from discovery.discovery_sources import DiscoverySource, RepoCandidate
from discovery.clickhouse_discovery import ClickHouseGitTrendsSource
from core.db import DB

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")
with open(_CONFIG_PATH) as _f:
    _CONFIG = json.load(_f)

EXA_API_KEY: str = _CONFIG.get("exa", {}).get("api_key", "")

BATCH_SIZE = 17                          # repos per run
GITHUB_URLS_FILE = "github_urls.txt"    # current batch — read by auto_script_generator.py
PUBLISHED_FILE = "published_repos.txt"  # permanent dedup history
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))  # project root directory
QUEUE_THRESHOLD = 50                    # minimum repos needed before running discovery
QUERIES_PER_RUN = 10                    # number of queries to run when discovery is needed

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
# Keyword queries for broad discovery (numbered for random selection)
# ---------------------------------------------------------------------------

SEARCH_QUERIES: Dict[int, str] = {
    # General / Broad (1-4)
    1: "novel open source approach to browser automation and AI agents github",
    2: "newly released open source RAG framework or developer tool github",
    3: "under the radar AI developer tools open source launch github",
    4: "high quality developer focused open source projects launched in 2025 github",

    # Browser/Web Automation (5-7)
    5: "innovative open source web scraping or browser automation tool github",
    6: "headless browser automation framework for developers github",
    7: "playwright puppeteer alternative open source github",

    # Databases & Storage (8-10)
    8: "new open source vector database or time-series database github",
    9: "edge database open source launch github",
    10: "columnar storage format or OLAP database open source github",

    # DevOps & Infrastructure - Cloud Native & Kubernetes (11-16)
    11: "open source infrastructure as code tool or github action github",
    12: "container orchestration or kubernetes tool open source github",
    13: "Kubernetes operator or controller framework github",
    14: "service mesh or microservices networking github",
    15: "container registry or signing tool open source github",
    16: "Helm chart or kubernetes deployment tool github",
    
    # DevOps & Infrastructure - Automation & Serverless (17-21)
    17: "serverless framework or edge computing open source github",
    18: "infrastructure provisioning or Terraform alternative github",
    19: "configuration management or Chef Puppet Ansible alternative github",
    20: "CI/CD pipeline tool or GitHub Actions alternative github",
    21: "release automation or deployment orchestration github",
    
    # DevOps & Infrastructure - Observability & Edge (22-26)
    22: "function runtime or serverless runtime github",
    23: "distributed tracing or APM open source github",
    24: "log aggregation or log management tool github",
    25: "metrics collection or time-series metrics tool github",
    26: "dashboard or visualization platform open source github",

    # Security & Cryptography (27-29)
    27: "open source security tool or vulnerability scanner github",
    28: "homomorphic encryption or zero-knowledge proof library github",
    29: "supply chain security or dependency integrity tool github",

    # Testing & Code Quality (30-32)
    30: "novel testing framework or property-based testing tool github",
    31: "code coverage or mutation testing tool open source github",
    32: "linting or static analysis tool for developers github",

    # Developer Tools & CLI (33-35)
    33: "innovative command-line tool or terminal productivity github",
    34: "API client or graphql testing tool open source github",
    35: "developer documentation generator or open source github",
    
    # Coding - Programming Languages & Runtimes (36-40)
    36: "innovative programming language or runtime compiled language github",
    37: "JavaScript or TypeScript framework github",
    38: "Rust web framework or tooling github",
    39: "Python packaging or dependency management tool github",
    40: "Go framework or tooling github",
    
    # Coding - Developer Experience (41-44)
    41: "code editor or IDE plugin open source github",
    42: "git workflow tool or git extension github",
    43: "code review automation or PR bot github",
    44: "hot reload or live reload framework github",
    
    # Coding - Code Quality & Analysis (45-48)
    45: "semantic code search or code intelligence tool github",
    46: "code generation or AI assisted coding tool github",
    47: "refactoring or code transformation tool github",
    48: "debugger or runtime introspection tool github",

    # Media & Graphics (49-51)
    49: "open source image processing or video editing library github",
    50: "3D rendering or game engine tool open source github",
    51: "audio processing or speech recognition library github",

    # Trending Topics (52-54)
    52: "Y Combinator W24 batch open source projects github",
    53: "Hacker News trending open source tools github",
    54: "AngelList or Product Hunt featured open source github",

    # Emerging Tech (55-57)
    55: "WebAssembly runtime or WASI tool open source github",
    56: "Blockchain or web3 developer tool open source github",
    57: "IoT or embedded systems framework open source github",

    # Performance & Monitoring (58-60)
    58: "open source APM tool or performance profiler github",
    59: "observability or tracing framework github",
    60: "distributed tracing or logging aggregation github",

    # Data Engineering - Pipeline & Orchestration (61-67)
    61: "open source data pipeline orchestrator alternative to airflow github",
    62: "real-time data streaming platform or event streaming tool github",
    63: "batch ETL framework for data engineering github",
    64: "change data capture or CDC tool open source github",
    65: "data lake or lakehouse framework open source github",
    66: "feature store or MLOps pipeline tool github",
    67: "data catalog or lineage tracking tool open source github",
    
    # Data Engineering - Transformation Integration (68-73)
    68: "data transformation framework or dbt alternative github",
    69: "data modeling or schema mapping tool open source github",
    70: "data quality validation or testing framework github",
    71: "API data connector or data ingestion tool open source github",
    72: "database replication or data migration tool github",
    73: "reverse ETL or warehouse-to-action tool github",

    # Specific Innovations (74-78)
    74: "language server protocol implementation or LSP tool github",
    75: "local-first database or offline-first framework github",
    76: "privacy-focused authentication or oauth tool open source github",
    77: "code-to-image or diagram generation tool github",
    78: "markdown-based documentation site generator github",
}

# Get total number of queries for random selection
TOTAL_QUERIES = len(SEARCH_QUERIES)

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
    def __init__(self, api_key: str, num_results_per_query: int = 30, num_queries: int = QUERIES_PER_RUN):
        self._api_key = api_key
        self._num_results = num_results_per_query
        self._num_queries = num_queries

    @property
    def source_name(self) -> str:
        return "exa_keyword"

    def fetch(self, seen: set) -> List[RepoCandidate]:
        from exa_py import Exa  # type: ignore
        client = Exa(api_key=self._api_key)
        candidates: List[RepoCandidate] = []
        found_urls: set = set()

        # Randomly select queries to run
        selected_queries = random.sample(list(SEARCH_QUERIES.keys()), 
                                        min(self._num_queries, TOTAL_QUERIES))
        print(f"  [keyword] Running {len(selected_queries)} random queries: {selected_queries}")

        for query_id in selected_queries:
            query = SEARCH_QUERIES[query_id]
            print(f"  [keyword] Query {query_id}: {query!r}")
            try:
                results = client.search(
                    query,
                    num_results=self._num_results,
                    include_domains=["github.com"],
                    start_published_date="2025-01-01",
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
                 num_results_per_seed: int = 50):
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
                    start_published_date="2025-01-01",
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
        Uses queue-first logic: checks pending repos before running discovery.
        """
        try:
            with DB() as db:
                _migrate_published_txt(db)
                seen = {u.lower() for u in db.get_published_urls()}
                
                # Queue-first logic: Check pending repos before running discovery
                pending_repos = db.get_pending_repos(limit=200)
                pending_count = len(pending_repos)
                
                print(f"[ExaDiscovery] Queue check: {pending_count} pending repos (threshold: {QUEUE_THRESHOLD})")
                
                # If we have enough pending repos, use them instead of running discovery
                if pending_count >= QUEUE_THRESHOLD:
                    print(f"[ExaDiscovery] ✓ Queue has sufficient repos. Skipping discovery, using pending queue.")
                    batch = []
                    for p in pending_repos[:count]:
                        p_url = p.get("url")
                        if p_url and p_url not in batch:
                            batch.append(p_url)
                    print(f"[ExaDiscovery] Selected {len(batch)} repos from pending queue.")
                    return batch
                
                print(f"[ExaDiscovery] ✗ Queue below threshold. Running discovery with {QUERIES_PER_RUN} random queries.")
                
                seen |= {u.lower() for u in (pending_repos and
                         [r["url"] for r in pending_repos])}
        except Exception as e:
            print(f"[db] Warning: could not load from SurrealDB ({e}), falling back to txt")
            seen = _load_published_fallback()

        all_candidates: List[RepoCandidate] = []

        if mode in ("keyword", "both", "all"):
            all_candidates.extend(ExaKeywordSource(self._api_key).fetch(seen))

        if mode in ("similar", "both", "all"):
            all_candidates.extend(ExaSimilarSource(self._api_key, self._seeds).fetch(seen))
            
        if mode in ("clickhouse", "both", "all"):
            all_candidates.extend(ClickHouseGitTrendsSource().fetch(seen))

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
                                 
                # Top up batch from pending repos if necessary
                if len(batch) < count:
                    needed = count - len(batch)
                    pending_repos = db.get_pending_repos(limit=needed + 20)
                    added = 0
                    for p in pending_repos:
                        p_url = p.get("url")
                        if p_url and p_url not in batch:
                            batch.append(p_url)
                            added += 1
                        if len(batch) >= count:
                            break
                    if added > 0:
                        print(f"[ExaDiscovery] Added {added} pending repos from DB to reach batch size of {len(batch)}.")
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
    p.add_argument("--mode", choices=["keyword", "similar", "clickhouse", "both", "all"], default="all")
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
