#!/usr/bin/env python3
"""
GitHub API fetcher for enriched repository data.
Handles rate limiting, caching, and star velocity calculations.
"""

import json
import os
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from discovery.discovery_sources import RepoCandidate


class GitHubAPIClient:
    """Client for fetching GitHub repository data with rate limiting."""
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub API client.
        
        Args:
            token: GitHub personal access token. Falls back to GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN not set. Provide token or set environment variable.")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make a GitHub API request with error handling."""
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code == 401:
                raise ValueError("Invalid GitHub token. Check GITHUB_TOKEN.")
            elif response.status_code == 403:
                # Rate limited
                reset_time = response.headers.get('X-RateLimit-Reset')
                if reset_time:
                    reset_datetime = datetime.fromtimestamp(int(reset_time))
                    raise ValueError(
                        f"GitHub API rate limited. Resets at {reset_datetime}"
                    )
                raise ValueError("GitHub API rate limited.")
            elif response.status_code == 404:
                return {}
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"GitHub API request failed: {e}")
    
    def fetch_repo_data(self, owner: str, repo: str) -> Dict:
        """
        Fetch repository metadata from GitHub REST API.
        
        Args:
            owner: Repository owner/organization name
            repo: Repository name
            
        Returns:
            Dictionary containing repository metadata
        """
        endpoint = f"repos/{owner}/{repo}"
        return self._make_request(endpoint, {})
    
    def fetch_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Fetch and decode README content from GitHub API.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Decoded README content or None if not found
        """
        endpoint = f"repos/{owner}/{repo}/readme"
        try:
            data = self._make_request(endpoint, {})
            if data and "content" in data:
                import base64
                return base64.b64decode(data["content"]).decode("utf-8")
        except Exception as e:
            print(f"Note: Could not fetch README for {owner}/{repo}: {e}")
        return None


class StarVelocityCalculator:
    """Calculates star velocity using github_stats_cache.json as baseline."""
    
    CACHE_FILE = "github_stats_cache.json"
    
    def __init__(self, cache_file: Optional[str] = None):
        """Initialize with custom cache file path."""
        self.cache_file = cache_file or self.CACHE_FILE
        self._cache_data = None
        self._load_cache()
    
    def _load_cache(self):
        """Load cache data from file."""
        if not os.path.exists(self.cache_file):
            self._cache_data = {}
            return
        
        try:
            with open(self.cache_file, 'r') as f:
                self._cache_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            self._cache_data = {}
    
    def calculate_velocity(
        self, 
        full_name: str, 
        current_stars: int
    ) -> Tuple[Optional[float], bool]:
        """
        Calculate star velocity (stars/day) over approximately 30 days.
        
        Args:
            full_name: Repository full name (owner/repo)
            current_stars: Current star count
            
        Returns:
            Tuple of (velocity, has_cached_data)
            - velocity: stars/day, or None if no cached data
            - has_cached_data: whether repo existed in cache
        """
        if full_name not in self._cache_data:
            return None, False
        
        cached_entry = self._cache_data[full_name]
        
        # Extract cached star count and timestamp
        if "data" in cached_entry:
            cached_stars = cached_entry["data"].get("stars")
            cached_timestamp = cached_entry["data"].get("timestamp")
        else:
            cached_stars = cached_entry.get("stars")
            cached_timestamp = cached_entry.get("timestamp")
        
        if not cached_stars or not cached_timestamp:
            return None, False
        
        try:
            # Parse timestamp
            if isinstance(cached_timestamp, str):
                cached_date = datetime.fromisoformat(cached_timestamp.replace('Z', '+00:00'))
            elif isinstance(cached_timestamp, (int, float)):
                cached_date = datetime.fromtimestamp(cached_timestamp)
            else:
                return None, False
            
            # Calculate days elapsed
            current_date = datetime.now()
            days_elapsed = (current_date - cached_date).total_seconds() / 86400
            
            if days_elapsed <= 0:
                return None, False
            
            # Calculate velocity
            velocity = (current_stars - cached_stars) / days_elapsed
            
            return velocity, True
            
        except Exception as e:
            print(f"Warning: Velocity calculation error for {full_name}: {e}")
            return None, False
    
    def get_cached_repos(self) -> set:
        """Get set of all repo full names in cache."""
        return set(self._cache_data.keys())


class GitHubSearchAPISource:
    """
    GitHub Search API discovery source.
    Searches by stars + recency, targeting AI-adjacent topics.
    """
    
    def __init__(self, api_client: GitHubAPIClient, velocity_calc: StarVelocityCalculator):
        """
        Initialize GitHub Search API source.
        
        Args:
            api_client: GitHubAPIClient instance
            velocity_calc: StarVelocityCalculator instance
        """
        self.client = api_client
        self.velocity_calc = velocity_calc
    
    @property
    def source_name(self) -> str:
        return "GitHub Search API"
    
    def fetch(
        self, 
        per_page: int = 10,
        days_back: int = 30
    ) -> List[RepoCandidate]:
        """
        Fetch candidates using GitHub Search API.
        
        Args:
            per_page: Results per query (default: 10)
            days_back: Look back period for recent repos (default: 30)
            
        Returns:
            List of RepoCandidate objects
        """
        candidates = []
        
        # Search queries targeting AI-adjacent topics
        queries = [
            f"topic:llm stars:>100 pushed:>{self._days_ago(days_back)}",
            f"topic:ai stars:>100 pushed:>{self._days_ago(days_back)}",
            f"topic:agents stars:>100 pushed:>{self._days_ago(days_back)}",
            f"topic:ml stars:>100 pushed:>{self._days_ago(days_back)}",
            f"topic:rag stars:>100 pushed:>{self._days_ago(days_back)}",
            f"stars:>500 pushed:>{self._days_ago(days_back)}",  # General high-star repos
        ]
        
        for query in queries:
            print(f"Searching: {query}")
            
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page
            }
            
            try:
                results = self.client._make_request("search/repositories", params)
                items = results.get("items", [])
                
                for item in items:
                    candidates.append(RepoCandidate(
                        url=item["html_url"],
                        source_name=self.source_name,
                        discovered_at=datetime.now()
                    ))
                
                print(f"  Found {len(items)} repos")
                
            except Exception as e:
                print(f"  Search failed: {e}")
        
        # Deduplicate within source
        seen_urls = set()
        unique_candidates = []
        for candidate in candidates:
            if candidate.url not in seen_urls:
                seen_urls.add(candidate.url)
                unique_candidates.append(candidate)
        
        return unique_candidates
    
    @staticmethod
    def _days_ago(days: int) -> str:
        """Return date string for N days ago in GitHub search format."""
        return (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")


def demo():
    """Demo function to test GitHub API components."""
    try:
        client = GitHubAPIClient()
        velocity_calc = StarVelocityCalculator()
        search_source = GitHubSearchAPISource(client, velocity_calc)
        
        print("GitHub Search API Source Demo")
        print("=" * 50)
        
        candidates = search_source.fetch(per_page=5, days_back=30)
        
        print(f"\nTotal candidates found: {len(candidates)}")
        for i, candidate in enumerate(candidates[:3], 1):
            print(f"{i}. {candidate.url} (from {candidate.source_name})")
            
    except Exception as e:
        print(f"Demo failed: {e}")
        print("\nTo run this demo properly:")
        print("1. Set GITHUB_TOKEN environment variable")
        print("2. Ensure github_stats_cache.json exists")


if __name__ == "__main__":
    demo()
