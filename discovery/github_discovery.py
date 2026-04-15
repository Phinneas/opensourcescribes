#!/usr/bin/env python3
"""
GitHub Discovery: Automated OSS Discovery & Queueing

Main orchestration script for discovering high-signal open-source repositories.
Runs discovery sources, filters candidates, scores with Mistral, and writes to queue.

Usage:
    python github_discovery.py                    # Run with defaults
    python github_discovery.py --dry-run          # Preview without writing
    python github_discovery.py --no-trending       # Skip GitHub Trending
    python github_discovery.py --search-only      # Search API only

Configuration:
    - Set GITHUB_TOKEN in environment or config.json
    - Set Mistral API key in config.json or MISTRAL_API_KEY
    
Output:
    - github_urls.txt: 15 new URLs appended
    - repo_history.json: Permanent dedup history
    - discovery_runs/YYYY-MM-DD.json: Detailed run artifact
"""

import sys
import argparse
from datetime import datetime
from pathlib import Path

# Local modules
try:
    from discovery.discovery_sources import RepoCandidate
    from discovery.github_api_fetcher import GitHubAPIClient, StarVelocityCalculator, GitHubSearchAPISource
    from discovery.github_trending_scraper import GitHubTrendingSource
    from discovery.repo_filter import RepoFilter, EnrichedRepo
    from utils.mistral_scorer import MistralScorer
    from content.output_writer import OutputWriter
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Ensure you're running from the opensourcescribes directory.")
    sys.exit(1)


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
    
    TARGET_REPOS = 15
    SEARCH_RESULTS_PER_QUERY = 10
    SEARCH_DAYS_BACK = 30
    
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
    
    def discover_candidates(self) -> list[RepoCandidate]:
        """
        Run all discovery sources and return combined candidates.
        
        Returns:
            List of RepoCandidate objects (deduplicated)
        """
        print("\n" + "=" * 60)
        print("DISCOVERY PHASE: Fetching candidates")
        print("=" * 60)
        
        all_candidates = []
        
        for source in self.sources:
            source_name = source.source_name
            print(f"\nRunning {source_name}...")
            
            try:
                if hasattr(source, 'fetch'):
                    if isinstance(source, GitHubSearchAPISource):
                        # Search API needs parameters
                        candidates = source.fetch(
                            per_page=self.SEARCH_RESULTS_PER_QUERY,
                            days_back=self.SEARCH_DAYS_BACK
                        )
                    else:
                        # Trending uses default
                        candidates = source.fetch()
                    
                    print(f"  {source_name}: found {len(candidates)} candidates")
                    all_candidates.extend(candidates)
                
            except Exception as e:
                print(f"  {source_name} failed: {e}")
        
        # Deduplicate candidates
        seen_urls = set()
        unique_candidates = []
        for candidate in all_candidates:
            if candidate.url not in seen_urls:
                seen_urls.add(candidate.url)
                unique_candidates.append(candidate)
        
        print(f"\nTotal unique candidates: {len(unique_candidates)}")
        
        return unique_candidates
    
    def enrich_candidates(self, candidates: list[RepoCandidate]) -> list[EnrichedRepo]:
        """
        Fetch enriched data from GitHub API for all candidates.
        
        Args:
            candidates: List of RepoCandidate objects
            
        Returns:
            List of EnrichedRepo objects
        """
        print("\n" + "=" * 60)
        print("ENRICHMENT PHASE: Fetching enriched data")
        print("=" * 60)
        
        enriched_repos = []
        
        for i, candidate in enumerate(candidates, 1):
            # Parse owner/repo from URL
            url_parts = candidate.url.rstrip('/').split('/')
            if len(url_parts) < 2:
                continue
            
            owner = url_parts[-2]
            repo = url_parts[-1]
            
            print(f"[{i}/{len(candidates)}] Fetching {owner}/{repo}... ", end="", flush=True)
            
            try:
                # Fetch repo data
                api_data = self.api_client.fetch_repo_data(owner, repo)
                
                if not api_data or "message" in api_data:
                    print("ERROR")
                    continue
                
                # Calculate velocity
                velocity, has_cache = self.velocity_calc.calculate_velocity(
                    f"{owner}/{repo}",
                    api_data.get("stargazers_count", 0)
                )
                
                # Fetch README
                readme = self.api_client.fetch_readme(owner, repo)
                
                # Create enriched repo
                enriched = self.repo_filter.enrich_repo(
                    candidate=candidate,
                    api_data=api_data,
                    readme=readme,
                    velocity=velocity
                )
                
                enriched_repos.append(enriched)
                v_str = "None" if velocity is None else f"{velocity:.2f}"
                print(f"OK (velocity={v_str}, cached={has_cache})")

                
            except Exception as e:
                print(f"ERROR: {e}")
        
        print(f"\nSuccessfully enriched {len(enriched_repos)} repositories")
        
        return enriched_repos
    
    def filter_candidates(self, enriched_repos: list[EnrichedRepo]) -> list[EnrichedRepo]:
        """
        Apply hard filters to enriched candidates.
        
        Args:
            enriched_repos: List of EnrichedRepo objects
            
        Returns:
            Filtered list of EnrichedRepo objects
        """
        print("\n" + "=" * 60)
        print("FILTERING PHASE: Applying hard filters")
        print("=" * 60)
        
        # Apply filters with velocity requirement (hard filter)
        filtered = self.repo_filter.filter_candidates(
            enriched_repos,
            require_velocity=True
        )
        
        print(f"Pre-filter count: {len(enriched_repos)}")
        print(f"Post-filter count: {len(filtered)}")
        
        if len(filtered) == 0:
            print("\nWarning: No repositories passed filters!")
            print("This might mean:")
            print("  - All candidates were archived/forks/stale")
            print("  - All candidates already in history/queue")
            print("  - No candidates have velocity data in cache")
        
        return filtered
    
    def score_and_rank(self, repos: list[EnrichedRepo]) -> list:
        """
        Score repositories with Mistral and return top-ranked.
        
        Args:
            repos: List of EnrichedRepo objects
            
        Returns:
            List of (EnrichedRepo, ScoredRepo) tuples, ranked by score
        """
        print("\n" + "=" * 60)
        print("SCORING PHASE: Ranking with Mistral")
        print("=" * 60)
        
        if not repos:
            print("No repos to score.")
            return []
        
        scorer = MistralScorer()
        
        top_repos = scorer.get_top_repos(repos, top_n=self.TARGET_REPOS)
        
        print(f"\nTop {len(top_repos)} ranked repositories:")
        for i, (repo, score) in enumerate(top_repos, 1):
            print(f"{i}. {repo.full_name} (score: {score.score:.1f})")
            print(f"   {score.reason}")
        
        return top_repos
    
    def write_outputs(
        self,
        selected_repos: list,
        pre_filter_count: int,
        post_filter_count: int,
        all_scored: list = None
    ):
        """
        Write all output files.
        
        Args:
            selected_repos: Top N selected repos to write to queue
            pre_filter_count: Stats for artifact
            post_filter_count: Stats for artifact
            all_scored: All scored repos for artifact
        """
        print("\n" + "=" * 60)
        print("OUTPUT PHASE: Writing queue and artifacts")
        print("=" * 60)
        
        if self.dry_run:
            print("DRY RUN MODE - Skipping output writes")
            print("\nWould write:")
            print(f"  - {len(selected_repos)} URLs to github_urls.txt")
            print(f"  - {len(selected_repos)} entries to repo_history.json")
            print(f"  - Run artifact to discovery_runs/")
            return
        
        run_id = datetime.now().strftime("%Y-%m-%d")
        
        self.output_writer.write_all(
            selected_repos=selected_repos,
            run_id=run_id,
            pre_filter_count=pre_filter_count,
            post_filter_count=post_filter_count,
            all_scored=all_scored
        )
    
    def run(self):
        """Execute the full discovery pipeline."""
        print("\nStarting GitHub Discovery Pipeline...")
        print(f"Target: {self.TARGET_REPOS} repositories")
        
        # Phase 1: Discovery
        candidates = self.discover_candidates()
        if not candidates:
            print("\nNo candidates found. Exiting.")
            return
        
        # Phase 2: Enrichment
        pre_filter_repos = self.enrich_candidates(candidates)
        if not pre_filter_repos:
            print("\nNo repos could be enriched. Exiting.")
            return
        
        # Phase 3: Filtering
        filtered_repos = self.filter_candidates(pre_filter_repos)
        if not filtered_repos:
            print("\nNo repos passed filters. Exiting.")
            return
        
        # Phase 4: Scoring
        top_repos = self.score_and_rank(filtered_repos)
        if not top_repos:
            print("\nNo repos scored successfully. Exiting.")
            return
        
        # Phase 5: Output
        self.write_outputs(
            selected_repos=top_repos,
            pre_filter_count=len(pre_filter_repos),
            post_filter_count=len(filtered_repos),
            all_scored=top_repos
        )
        
        print("\n" + "=" * 60)
        print("DISCOVERY PIPELINE COMPLETE")
        print("=" * 60)
        print(f"\nSuccessfully discovered {len(top_repos)} high-signal repositories!")


def main():
    """Main entry point with CLI argument handling."""
    parser = argparse.ArgumentParser(
        description="Automated GitHub Discovery Pipeline for OpenSourceScribes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard run with all sources
  python github_discovery.py
  
  # Preview without writing (dry run)
  python github_discovery.py --dry-run
  
  # Skip GitHub Trending (no Selenium needed)
  python github_discovery.py --no-trending
  
  # Use only Search API
  python github_discovery.py --search-only
  
  # Run with visible browser (debugging)
  python github_discovery.py --no-headless
        """
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview results without writing to files"
    )
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
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run Selenium with visible browser (for debugging)"
    )
    parser.add_argument(
        "--target",
        type=int,
        default=15,
        help="Number of repos to select (default: 15)"
    )
    
    args = parser.parse_args()
    
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
        
        pipeline.run()
        
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nPipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
