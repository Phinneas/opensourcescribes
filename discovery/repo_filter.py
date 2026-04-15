#!/usr/bin/env python3
"""
Hard filtering logic for repository candidates.
Applies non-negotiable filters before Mistral scoring.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Set, Optional
from pathlib import Path
from dataclasses import dataclass
from discovery.discovery_sources import RepoCandidate


@dataclass
class EnrichedRepo:
    """Enriched repository data with stats and metadata."""
    url: str
    owner: str
    repo: str
    full_name: str
    stars: int
    forks: int
    language: str
    description: str
    topics: List[str]
    pushed_at: str
    archived: bool
    fork: bool
    created_at: str
    homepage: str
    readme: str
    velocity: float
    source_name: str
    discovered_at: datetime


class RepoFilter:
    """
    Hard filter for repository candidates.
    Applies multiple filters to ensure high-signal repos.
    """
    
    STALE_DAYS = 30
    HISTORY_FILE = "repo_history.json"
    QUEUE_FILE = "github_urls.txt"
    
    def __init__(self, history_file: Optional[str] = None, queue_file: Optional[str] = None):
        """Initialize filter with custom file paths."""
        self.history_file = history_file or self.HISTORY_FILE
        self.queue_file = queue_file or self.QUEUE_FILE
        
        self._history_data = self._load_history()
        self._queued_urls = self._load_queue()
        self._cached_repos = self._load_cache()
    
    def _load_history(self) -> Dict:
        """Load repo history JSON file."""
        if not os.path.exists(self.history_file):
            return {}
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Could not load {self.history_file}")
            return {}
    
    def _load_queue(self) -> Set[str]:
        """Load currently queued URLs from github_urls.txt."""
        if not os.path.exists(self.queue_file):
            return set()
        
        try:
            with open(self.queue_file, 'r') as f:
                return {
                    line.strip() 
                    for line in f 
                    if line.strip().startswith("https://github.com/")
                }
        except IOError:
            print(f"Warning: Could not load {self.queue_file}")
            return set()
    
    def _load_cache(self) -> Set[str]:
        """Load cached repo names from github_stats_cache.json."""
        cache_file = "github_stats_cache.json"
        if not os.path.exists(cache_file):
            return set()
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                return set(data.keys()) if data else set()
        except (json.JSONDecodeError, IOError):
            return set()
    
    def enrich_repo(
        self, 
        candidate: RepoCandidate, 
        api_data: Dict,
        readme: Optional[str],
        velocity: float
    ) -> EnrichedRepo:
        """
        Convert API data to EnrichedRepo object.
        
        Args:
            candidate: Raw candidate from discovery
            api_data: Data from GitHub API
            readme: README content
            velocity: Calculated star velocity
            
        Returns:
            EnrichedRepo object
        """
        # Parse URL to get owner/repo
        url_parts = candidate.url.rstrip('/').split('/')
        owner = url_parts[-2]
        repo = url_parts[-1]
        
        return EnrichedRepo(
            url=candidate.url,
            owner=owner,
            repo=repo,
            full_name=f"{owner}/{repo}",
            stars=api_data.get("stargazers_count", 0),
            forks=api_data.get("forks_count", 0),
            language=api_data.get("language") or "",
            description=api_data.get("description") or "",
            topics=api_data.get("topics", []),
            pushed_at=api_data.get("pushed_at", ""),
            archived=api_data.get("archived", False),
            fork=api_data.get("fork", False),
            created_at=api_data.get("created_at", ""),
            homepage=api_data.get("homepage") or "",
            readme=readme or "",
            velocity=velocity if velocity is not None else 0.0,
            source_name=candidate.source_name,
            discovered_at=candidate.discovered_at
        )
    
    def passes_filters(self, enriched_repo: EnrichedRepo) -> bool:
        """
        Check if a repository passes all hard filters.
        
        Args:
            enriched_repo: Enriched repo data
            
        Returns:
            True if repo passes all filters
        """
        # Filter 1: Archived repos
        if enriched_repo.archived:
            return False
        
        # Filter 2: Forks
        if enriched_repo.fork:
            return False
        
        # Filter 3: No description
        if not enriched_repo.description:
            return False
        
        # Filter 4: Stale repos (last commit > STALE_DAYS ago)
        if enriched_repo.pushed_at:
            try:
                pushed_date = datetime.fromisoformat(enriched_repo.pushed_at.replace('Z', '+00:00'))
                stale_threshold = datetime.now() - timedelta(days=self.STALE_DAYS)
                if pushed_date < stale_threshold:
                    return False
            except (ValueError, TypeError):
                # Invalid date, skip
                return False
        
        # Filter 5: Already covered (in repo_history.json)
        if enriched_repo.full_name in self._history_data:
            return False
        
        # Filter 6: Already queued (in github_urls.txt)
        if enriched_repo.url in self._queued_urls:
            return False
        
        return True
    
    def has_velocity_data(self, full_name: str) -> bool:
        """
        Check if repo has velocity data (exists in cache).
        
        Args:
            full_name: Repository full name
            
        Returns:
            True if repo is in cache (has velocity baseline)
        """
        return full_name in self._cached_repos
    
    def filter_candidates(
        self, 
        enriched_repos: List[EnrichedRepo],
        require_velocity: bool = True
    ) -> List[EnrichedRepo]:
        """
        Apply all filters to a list of enriched repos.
        
        Args:
            enriched_repos: List of enriched repos to filter
            require_velocity: If True, hard-filter repos without velocity data
            
        Returns:
            Filtered list of repos that pass all checks
        """
        passed = []
        
        for repo in enriched_repos:
            # Pre-filter: velocity data requirement
            if require_velocity and not self.has_velocity_data(repo.full_name):
                continue
            
            # Apply hard filters
            if self.passes_filters(repo):
                passed.append(repo)
        
        return passed


def demo():
    """Demo function to test filtering logic."""
    print("Repo Filter Demo")
    print("=" * 50)
    
    # Create a mock enriched repo
    from datetime import datetime
    
    # Good repo (should pass)
    good_repo = EnrichedRepo(
        url="https://github.com/example/good-repo",
        owner="example",
        repo="good-repo",
        full_name="example/good-repo",
        stars=1000,
        forks=50,
        language="Python",
        description="A great example repository",
        topics=["ai", "ml"],
        pushed_at=datetime.now().isoformat(),
        archived=False,
        fork=False,
        created_at=datetime.now().isoformat(),
        homepage="https://example.com",
        readme="# Good Repo\nThis is a great repo.",
        velocity=5.0,
        source_name="GitHub Search API",
        discovered_at=datetime.now()
    )
    
    # Bad repos (should fail various filters)
    archived_repo = EnrichedRepo(
        url="https://github.com/example/archived-repo",
        owner="example",
        repo="archived-repo",
        full_name="example/archived-repo",
        stars=100,
        forks=10,
        language="JavaScript",
        description="Archived repo",
        topics=[],
        pushed_at=datetime.now().isoformat(),
        archived=True,  # FAIL: archived
        fork=False,
        created_at=datetime.now().isoformat(),
        homepage="",
        readme="",
        velocity=0.1,
        source_name="GitHub Trending",
        discovered_at=datetime.now()
    )
    
    stale_repo = EnrichedRepo(
        url="https://github.com/example/stale-repo",
        owner="example",
        repo="stale-repo",
        full_name="example/stale-repo",
        stars=100,
        forks=10,
        language="Go",
        description="Stale repo",
        topics=[],
        pushed_at=(datetime.now() - timedelta(days=60)).isoformat(),  # FAIL: stale
        archived=False,
        fork=False,
        created_at=datetime.now().isoformat(),
        homepage="",
        readme="",
        velocity=0.1,
        source_name="GitHub Search API",
        discovered_at=datetime.now()
    )
    
    test_filter = RepoFilter()
    
    # Test filters
    print("\nTesting filters:")
    print(f"  Good repo: {test_filter.passes_filters(good_repo)} (expected: True)")
    print(f"  Archived repo: {test_filter.passes_filters(archived_repo)} (expected: False)")
    print(f"  Stale repo: {test_filter.passes_filters(stale_repo)} (expected: False)")
    
    # Test velocity check
    print(f"\nVelocity check for example/good-repo: {test_filter.has_velocity_data('example/good-repo')} (likely: False)")


if __name__ == "__main__":
    demo()
