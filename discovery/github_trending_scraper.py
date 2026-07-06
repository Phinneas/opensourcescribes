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
