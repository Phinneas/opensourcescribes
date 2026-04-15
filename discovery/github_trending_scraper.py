#!/usr/bin/env python3
"""
GitHub Trending scraper using Selenium for client-side rendered pages.
Scrapes weekly and monthly trending repos.
"""

from datetime import datetime
from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from discovery.discovery_sources import DiscoverySource, RepoCandidate


class GitHubTrendingSource(DiscoverySource):
    """
    GitHub Trending discovery source using Selenium.
    Scrape weekly and monthly trending repositories.
    """
    
    BASE_URL = "https://github.com/trending"
    TIMEOUT = 10  # seconds
    
    def __init__(self, headless: bool = True):
        """
        Initialize GitHub Trending scraper.
        
        Args:
            headless: Run browser in headless mode (default: True)
        """
        self.headless = headless
        self._driver = None
    
    @property
    def source_name(self) -> str:
        return "GitHub Trending"
    
    def _init_driver(self):
        """Initialize and configure Chrome WebDriver."""
        if self._driver:
            return
        
        options = Options()
        
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        
        try:
            self._driver = webdriver.Chrome(options=options)
        except Exception as e:
            raise RuntimeError(
                f"Failed to initialize Chrome WebDriver: {e}\n"
                "Install chrome driver or ensure Chrome browser is available."
            )
    
    def _cleanup_driver(self):
        """Close and cleanup WebDriver."""
        if self._driver:
            try:
                self._driver.quit()
            except Exception:
                pass
            self._driver = None
    
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
        
        # Build URL with timeframe parameter
        url = f"{self.BASE_URL}?since={timeframe}"
        
        print(f"Fetching {timeframe} trending...")
        
        try:
            self._driver.get(url)
            
            # Wait for repository cards to load
            WebDriverWait(self._driver, self.TIMEOUT).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "article.Box-row"))
            )
            
            # Find all repository cards
            repo_cards = self._driver.find_elements(By.CSS_SELECTOR, "article.Box-row")
            
            for card in repo_cards:
                try:
                    # Find the repository link
                    link_elem = card.find_element(By.CSS_SELECTOR, "h2 a")
                    repo_url = link_elem.get_attribute("href")
                    
                    if repo_url and repo_url.startswith("https://github.com/"):
                        urls.append(repo_url)
                
                except NoSuchElementException:
                    continue
            
            print(f"  Found {len(urls)} repos")
            
        except TimeoutException:
            print(f"  Timeout: Could not load trending page for {timeframe}")
        except Exception as e:
            print(f"  Error scraping {timeframe} trending: {e}")
        
        return urls
    
    def fetch(self) -> List[RepoCandidate]:
        """
        Fetch trending repository candidates from both weekly and monthly lists.
        
        Returns:
            List of RepoCandidate objects (deduplicated)
        """
        self._init_driver()
        
        try:
            # Fetch both weekly and monthly
            weekly_urls = self._fetch_trending_page("weekly")
            monthly_urls = self._fetch_trending_page("monthly")
            
            # Combine and deduplicate
            all_urls = weekly_urls + monthly_urls
            seen_urls = set()
            unique_urls = []
            
            for url in all_urls:
                if url not in seen_urls:
                    seen_urls.add(url)
                    unique_urls.append(url)
            
            # Convert to RepoCandidate objects
            candidates = [
                RepoCandidate(
                    url=url,
                    source_name=self.source_name,
                    discovered_at=datetime.now()
                )
                for url in unique_urls
            ]
            
            return candidates
            
        finally:
            self._cleanup_driver()


def demo():
    """Demo function to test GitHub Trending scraper."""
    print("GitHub Trending Scraper Demo")
    print("=" * 50)
    
    try:
        scraper = GitHubTrendingSource(headless=True)
        candidates = scraper.fetch()
        
        print(f"\nTotal candidates found: {len(candidates)}")
        
        # Show first few results
        for i, candidate in enumerate(candidates[:5], 1):
            print(f"{i}. {candidate.url}")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nRequirements for this demo:")
        print("1. Install Selenium: pip install selenium")
        print("2. Install Chrome browser and chromedriver")
        print("3. Optional: Set headless=False in constructor to see browser")


if __name__ == "__main__":
    demo()
