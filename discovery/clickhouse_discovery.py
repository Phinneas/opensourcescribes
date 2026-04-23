#!/usr/bin/env python3
import requests
import json
from datetime import datetime
from typing import List
from discovery.discovery_sources import DiscoverySource, RepoCandidate

class ClickHouseGitTrendsSource(DiscoverySource):
    """
    Finds trending repositories using ClickHouse's public GitTrends dataset.
    Queries the last 7 days for repos with the most active event momentum.
    """
    
    @property
    def source_name(self) -> str:
        return "clickhouse_gittrends"

    def fetch(self, seen: set = None) -> List[RepoCandidate]:
        if seen is None:
            seen = set()
            
        candidates = []
        print(f"🌍 Fetching trending repos from ClickHouse...")
        
        query = """
            SELECT 
                repo_name,
                countIf(event_type = 'PullRequestEvent') as pr_events,
                countIf(event_type = 'IssuesEvent') as issue_events,
                uniqExact(actor_login) as active_contributors
            FROM github_events 
            WHERE created_at > now() - INTERVAL 7 DAY
              AND event_type IN ('PullRequestEvent', 'IssuesEvent')
              AND action IN ('opened', 'closed')
              AND actor_login NOT LIKE '%bot%'
              AND actor_login != 'dependabot[bot]'
            GROUP BY repo_name
            HAVING active_contributors >= 15 AND pr_events >= 5 AND pr_events + issue_events < 5000
            ORDER BY pr_events + issue_events DESC
            LIMIT 100
            FORMAT JSON
        """
        
        try:
            response = requests.post(
                'https://play.clickhouse.com/?user=explorer',
                data=query.strip(),
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                rows = data.get("data", [])
                
                added = 0
                for row in rows:
                    repo_name = row.get("repo_name")
                    if repo_name:
                        url = f"https://github.com/{repo_name}"
                        # Dedup check
                        if url.lower() in seen:
                            continue
                            
                        seen.add(url.lower())
                        candidates.append(RepoCandidate(
                            url=url,
                            source_name=self.source_name,
                            discovered_at=datetime.now()
                        ))
                        added += 1
                        if added >= 50:  # Only take top 50 new ones
                            break
                            
                print(f"   ✅ ClickHouse found {added} high-velocity new repos")
            else:
                print(f"   ⚠️ ClickHouse API error: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠️ ClickHouse fetch failed (Timeout/Error: {e})")
            
        return candidates

if __name__ == "__main__":
    source = ClickHouseGitTrendsSource()
    repos = source.fetch({"https://github.com/microsoft/vscode"})
    for r in repos[:5]:
        print(r)
