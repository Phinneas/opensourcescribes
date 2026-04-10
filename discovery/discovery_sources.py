#!/usr/bin/env python3
"""
Base discovery source interface for automated OSS discovery.
All discovery sources must implement the DiscoverySource interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class RepoCandidate:
    """Represents a raw repository candidate from any discovery source."""
    url: str
    source_name: str
    discovered_at: datetime


class DiscoverySource(ABC):
    """Base interface for all discovery sources."""
    
    @abstractmethod
    def fetch(self) -> List[RepoCandidate]:
        """
        Fetch repository candidates from this source.
        
        Returns:
            List of RepoCandidate objects with URLs and metadata.
        """
        pass
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the name of this discovery source."""
        pass


def demo():
    """Demo function to show the interface usage."""
    print("Discovery Source Interface")
    print("Implementations include:")
    print("  - GitHubTrendingSource")
    print("  - GitHubSearchAPISource")
    print("\nAll sources return RepoCandidate objects with:")
    print("  - url (str)")
    print("  - source_name (str)")  
    print("  - discovered_at (datetime)")


if __name__ == "__main__":
    demo()
