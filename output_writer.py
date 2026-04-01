#!/usr/bin/env python3
"""
Output writer for GitHub discovery results.
Handles writing to github_urls.txt, repo_history.json, and run artifacts.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
from repo_filter import EnrichedRepo
from mistral_scorer import ScoredRepo


class OutputWriter:
    """
    Writes discovery results to multiple output locations:
    - github_urls.txt: Active processing queue
    - repo_history.json: Permanent dedup history
    - discovery_runs/YYYY-MM-DD.json: Run artifacts
    """
    
    QUEUE_FILE = "github_urls.txt"
    HISTORY_FILE = "repo_history.json"
    RUNS_DIR = "discovery_runs"
    
    def __init__(
        self,
        queue_file: Optional[str] = None,
        history_file: Optional[str] = None,
        runs_dir: Optional[str] = None
    ):
        """Initialize writer with custom paths."""
        self.queue_file = queue_file or self.QUEUE_FILE
        self.history_file = history_file or self.HISTORY_FILE
        self.runs_dir = runs_dir or self.RUNS_DIR
        
        # Ensure runs directory exists
        Path(self.runs_dir).mkdir(parents=True, exist_ok=True)
    
    def _load_history(self) -> Dict:
        """Load existing repo history."""
        if not os.path.exists(self.history_file):
            return {}
        
        try:
            with open(self.history_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def write_to_queue(self, repos: List[EnrichedRepo]) -> int:
        """
        Append new repo URLs to github_urls.txt.
        
        Args:
            repos: List of repos to add
            
        Returns:
            Number of URLs written
        """
        urls = [repo.url for repo in repos]
        
        with open(self.queue_file, 'a') as f:
            for url in urls:
                f.write(url + '\n')
        
        print(f"  Appended {len(urls)} URLs to {self.queue_file}")
        return len(urls)
    
    def update_history(self, repos: List[EnrichedRepo], run_id: str) -> int:
        """
        Update repo_history.json with new entries.
        This is append-only - history never shrinks.
        
        Args:
            repos: List of repos to add to history
            run_id: Run identifier (usually date)
            
        Returns:
            Number of entries added
        """
        history = self._load_history()
        added_count = 0
        timestamp = datetime.now().isoformat() + "Z"
        
        for repo in repos:
            # Only add if not already in history
            if repo.full_name not in history:
                history[repo.full_name] = {
                    "url": repo.url,
                    "added_at": timestamp,
                    "run_id": run_id
                }
                added_count += 1
        
        # Write updated history
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
        
        print(f"  Added {added_count} entries to {self.history_file}")
        return added_count
    
    def save_run_artifact(
        self,
        run_id: str,
        pre_filter_count: int,
        post_filter_count: int,
        all_scored: List[tuple],  # (EnrichedRepo, ScoredRepo)
        selected_repos: List[tuple],  # Top N
        stats: Dict = None
    ):
        """
        Save detailed run artifact for auditability.
        
        Args:
            run_id: Run identifier (usually date)
            pre_filter_count: Number of candidates before filtering
            post_filter_count: Number of candidates after filtering
            all_scored: All scored repos with (repo, score) tuples
            selected_repos: Top N selected repos
            stats: Optional additional statistics
        """
        timestamp = datetime.now().isoformat()
        
        # Build artifact structure
        artifact = {
            "run_id": run_id,
            "timestamp": timestamp,
            "summary": {
                "candidates_before_filtering": pre_filter_count,
                "candidates_after_filtering": post_filter_count,
                "repos_scored": len(all_scored),
                "repos_selected": len(selected_repos)
            },
            "statistics": stats or {},
            "all_scored_repos": [
                {
                    "full_name": repo.full_name,
                    "url": repo.url,
                    "score": score.score,
                    "reason": score.reason,
                    "stars": repo.stars,
                    "velocity": repo.velocity,
                    "language": repo.language,
                    "description": repo.description
                }
                for repo, score in all_scored
            ],
            "selected_repos": [
                {
                    "full_name": repo.full_name,
                    "url": repo.url,
                    "score": score.score,
                    "reason": score.reason,
                    "stars": repo.stars,
                    "velocity": repo.velocity,
                    "language": repo.language
                }
                for repo, score in selected_repos
            ]
        }
        
        # Write artifact to discovery_runs/
        filename = f"{run_id}.json"
        filepath = os.path.join(self.runs_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump(artifact, f, indent=2)
        
        print(f"  Saved run artifact to {filepath}")
        return filepath
    
    def write_all(
        self,
        selected_repos: List[tuple],  # (EnrichedRepo, ScoredRepo)
        run_id: str,
        pre_filter_count: int = 0,
        post_filter_count: int = 0,
        all_scored: List[tuple] = None
    ):
        """
        Write all outputs in one call.
        
        Args:
            selected_repos: Top N selected repos to add to queue
            run_id: Run identifier
            pre_filter_count: Stats for artifact
            post_filter_count: Stats for artifact
            all_scored: All scored repos for artifact
        """
        print(f"\nWriting outputs for run {run_id}...")
        
        # Extract enriched repos from tuples
        enriched_selected = [repo for repo, _ in selected_repos]
        
        # Write to queue
        self.write_to_queue(enriched_selected)
        
        # Update history
        self.update_history(enriched_selected, run_id)
        
        # Save artifact
        if all_scored is None:
            all_scored = selected_repos
        
        self.save_run_artifact(
            run_id=run_id,
            pre_filter_count=pre_filter_count,
            post_filter_count=post_filter_count,
            all_scored=all_scored,
            selected_repos=selected_repos
        )
        
        print(f"  Output writing complete")


def demo():
    """Demo function to test output writer."""
    print("Output Writer Demo")
    print("=" * 50)
    
    from datetime import datetime
    from repo_filter import EnrichedRepo
    from mistral_scorer import ScoredRepo
    
    # Mock data
    mock_repo = EnrichedRepo(
        url="https://github.com/example/demo-repo",
        owner="example",
        repo="demo-repo",
        full_name="example/demo-repo",
        stars=1000,
        forks=50,
        language="Python",
        description="Demo repository for testing",
        topics=["api"],
        pushed_at=datetime.now().isoformat(),
        archived=False,
        fork=False,
        created_at=datetime.now().isoformat(),
        homepage="",
        readme="# Demo Repository",
        velocity=5.0,
        source_name="GitHub Search API",
        discovered_at=datetime.now()
    )
    
    mock_score = ScoredRepo(
        repo="example/demo-repo",
        score=8.5,
        reason="High-growth AI framework with clear value prop"
    )
    
    writer = OutputWriter()
    
    print("\nPreparing to write outputs...")
    print("  Note: This will modify real files in your project!")
    print("  - github_urls.txt")
    print("  - repo_history.json")
    print("  - discovery_runs/<date>.json")
    print("\nTo actually write files, uncomment the write_all() call.")
    
    # To actually write files:
    # writer.write_all(
    #     selected_repos=[(mock_repo, mock_score)],
    #     run_id=datetime.now().strftime("%Y-%m-%d"),
    #     pre_filter_count=5,
    #     post_filter_count=2,
    #     all_scored=[(mock_repo, mock_score)]
    # )
    
    print("\nDemo setup complete!")


if __name__ == "__main__":
    demo()
