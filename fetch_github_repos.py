#!/usr/bin/env python3
"""
fetch_github_repos.py - Search GitHub for trending open-source repositories.

This script uses the GitHub API to find interesting repositories based on topics,
stars count, and recency. It filters out duplicates and saves results to a JSON file
for manual review before including in roundups.

Requires:
- GITHUB_TOKEN environment variable set with a valid GitHub personal access token
- Python 3.x
- requests library

Example usage:
    python fetch_github_repos.py --topics "ai,webdev,python" --min-stars 100 --days 7
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Set
import argparse
import requests


def load_existing_urls(data_dir: str = "data") -> Set[str]:
    """Load all existing GitHub URLs from previous roundup files and github_urls.txt."""
    existing_urls = set()
    
    # Load from github_urls.txt if it exists
    if os.path.exists("github_urls.txt"):
        with open("github_urls.txt", "r") as f:
            for line in f:
                url = line.strip()
                if url and url.startswith("https://github.com/"):
                    existing_urls.add(url)
        print(f"Loaded {len(existing_urls)} URLs from github_urls.txt")
    
    # Load from existing data/roundup_*.json files
    data_path = Path(data_dir)
    if data_path.exists():
        for json_file in data_path.glob("roundup_*.json"):
            try:
                with open(json_file, "r") as f:
                    data = json.load(f)
                    for repo in data:
                        if "url" in repo:
                            existing_urls.add(repo["url"])
                print(f"Loaded URLs from {json_file.name}")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Warning: Could not parse {json_file.name}: {e}")
    
    return existing_urls


def fetch_github_repos(
    topics: List[str],
    min_stars: int = 100,
    days: int = 7,
    max_results: int = 10
) -> List[Dict]:
    """Fetch trending repositories from GitHub API.
    
    Args:
        topics: List of topics to search for
        min_stars: Minimum star count
        days: Number of days to look back for recent updates
        max_results: Maximum number of repos to return
        
    Returns:
        List of repository dictionaries
    """
    # GitHub API setup
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set")
        print("Please set it with: export GITHUB_TOKEN='your_token_here'")
        sys.exit(1)
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Calculate date cutoff
    date_cutoff = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    print(f"Searching for repos updated after {date_cutoff}")
    
    # Build search query - search for repos with ANY of the specified topics
    # Using topic:topic1 OR topic:topic2 syntax for GitHub search
    topic_query = " OR ".join([f"topic:{topic}" for topic in topics])
    query = f"({topic_query}) stars:>{min_stars} pushed:>{date_cutoff}"
    
    url = f"https://api.github.com/search/repositories"
    params = {
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": 50  # Fetch more to filter duplicates
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        result = response.json()
        repos = result.get("items", [])
        
        print(f"Found {len(repos)} repositories from GitHub API")
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from GitHub API: {e}")
        sys.exit(1)
    
    if not repos:
        print("No repositories found matching criteria")
        return []
    
    return repos


def filter_repos(repos: List[Dict], existing_urls: Set[str], max_results: int = 10) -> List[Dict]:
    """Filter out duplicate repositories from fetched results.
    
    Args:
        repos: List of repositories from GitHub API
        existing_urls: Set of URLs already seen
        max_results: Maximum number of repos to return
        
    Returns:
        Filtered list of repositories
    """
    output = []
    skipped_count = 0
    
    for repo in repos:
        repo_url = repo["html_url"]
        
        # Skip if already seen
        if repo_url in existing_urls:
            skipped_count += 1
            continue
        
        # Extract repo data
        repo_data = {
            "name": repo["name"],
            "url": repo_url,
            "stars": repo["stargazers_count"],
            "topics": repo.get("topics", []),
            "description": repo.get("description") or "",
            "last_updated": repo["pushed_at"].split("T")[0]
        }
        
        output.append(repo_data)
        
        # Stop when we have enough results
        if len(output) >= max_results:
            break
    
    print(f"Filtered: {len(output)} new repos, {skipped_count} duplicates skipped")
    return output


def save_results(repos: List[Dict], output_dir: str = "data") -> str:
    """Save fetched repositories to JSON file.
    
    Args:
        repos: List of repository dictionaries
        output_dir: Directory to save the output file
        
    Returns:
        Path to the saved file
    """
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename with current date
    filename = f"roundup_{datetime.now().strftime('%Y-%m-%d')}.json"
    filepath = os.path.join(output_dir, filename)
    
    # Save to JSON
    with open(filepath, "w") as f:
        json.dump(repos, f, indent=2)
    
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Fetch trending GitHub repositories for open-source roundups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search for AI and webdev repos with 100+ stars updated in last 7 days
  python fetch_github_repos.py --topics "ai,webdev" --min-stars 100 --days 7
  
  # Search with different criteria
  python fetch_github_repos.py --topics "python,machine-learning" --min-stars 500 --days 14
  
  # Get more results (up to 20)
  python fetch_github_repos.py --topics "open-source,devtools" --max-results 20
        """
    )
    
    parser.add_argument(
        "--topics",
        type=str,
        default="open-source,ai,webdev",
        help="Comma-separated list of topics to search for (default: open-source,ai,webdev)"
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        default=100,
        help="Minimum star count required (default: 100)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to look back for recent updates (default: 7)"
    )
    parser.add_argument(
        "--max-results",
        type=int,
        default=10,
        help="Maximum number of repositories to return (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Parse topics
    topics = [topic.strip() for topic in args.topics.split(",")]
    print(f"Topics: {topics}")
    print(f"Minimum stars: {args.min_stars}")
    print(f"Days: {args.days}")
    print(f"Max results: {args.max_results}")
    print("-" * 50)
    
    # Load existing URLs to avoid duplicates
    existing_urls = load_existing_urls()
    print("-" * 50)
    
    # Fetch repositories from GitHub API
    repos = fetch_github_repos(
        topics=topics,
        min_stars=args.min_stars,
        days=args.days
    )
    
    if not repos:
        print("No repositories found. Exiting.")
        return
    
    # Filter out duplicates
    filtered_repos = filter_repos(
        repos=repos,
        existing_urls=existing_urls,
        max_results=args.max_results
    )
    
    if not filtered_repos:
        print("No new repositories found after filtering duplicates.")
        return
    
    # Save results
    filepath = save_results(filtered_repos)
    
    print("-" * 50)
    print(f"Successfully saved {len(filtered_repos)} repositories to:")
    print(f"  {filepath}")
    print("")
    print("Next steps:")
    print("  1. Review the JSON file manually")
    print("  2. Select repos to include in your roundup")
    print("  3. Add selected URLs to github_urls.txt")


if __name__ == "__main__":
    main()
