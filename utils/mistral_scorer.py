#!/usr/bin/env python3
"""
Mistral scoring agent for repository ranking.
Uses structured output to score repos on momentum, content potential, and AI relevance.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from discovery.repo_filter import EnrichedRepo


# Mistral schema for structured output
SCORING_SCHEMA = {
    "type": "object",
    "properties": {
        "repo": {"type": "string"},
        "score": {"type": "number", "minimum": 1, "maximum": 10},
        "reason": {"type": "string"}
    },
    "required": ["repo", "score", "reason"],
    "additionalProperties": False
}


@dataclass
class ScoredRepo:
    """Repository with Mistral score and reasoning."""
    repo: str
    score: float
    reason: str


class MistralScorer:
    """
    Mistral agent for scoring and ranking repositories.
    Uses structured output to ensure JSON responses.
    """
    
    def __init__(self, model: str = "mistral-small"):
        """
        Initialize Mistral scorer.
        
        Args:
            model: Mistral model to use (default: mistral-small)
        """
        self.model = model
        self.client = self._init_client()
    
    def _init_client(self):
        """Initialize Mistral client from config.json or environment."""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            api_key = config.get('mistral', {}).get('api_key')
        except Exception:
            api_key = os.environ.get('MISTRAL_API_KEY')
        
        if not api_key or api_key == 'YOUR_MISTRAL_API_KEY':
            raise ValueError("Mistral API key not found. Check config.json or MISTRAL_API_KEY")
        
        try:
            from mistralai import Mistral
            return Mistral(api_key=api_key)
        except ImportError:
            raise ImportError(
                "mistralai package not installed. Install with: pip install mistralai"
            )
    
    def _create_repo_summary(self, repo: EnrichedRepo) -> str:
        """Create a concise summary of repo for Mistral to score."""
        readme_excerpt = repo.readme[:2000] if repo.readme else ""
        
        return f"""Repo: {repo.full_name}
Description: {repo.description}
Language: {repo.language}
Topics: {', '.join(repo.topics) if repo.topics else 'None'}
Stars: {repo.stars}
Star velocity (30d): {repo.velocity:.2f} stars/day
Last commit: {repo.pushed_at[:10] if repo.pushed_at else 'N/A'}
README (excerpt):
{readme_excerpt}"""
    
    def _build_batch_prompt(self, repos: List[EnrichedRepo]) -> str:
        """Build a prompt with multiple repos for batch scoring."""
        repo_summaries = []
        
        for i, repo in enumerate(repos, 1):
            repo_summaries.append(f"""

--- Repository {i}: {repo.full_name} ---
{self._create_repo_summary(repo)}
""")
        
        return """You are evaluating open-source repositories for a developer-focused content platform (like OpenSourceScribes).

Score each repository on a scale of 1-10 based on:
1. **Momentum**: Star velocity and recency of activity (is this trending?)
2. **Content Potential**: How interesting/explicable is this to a developer/tech audience?
3. **AI/Tooling Relevance**: Does this relate to AI, agents, LLMs, or modern dev tooling? (Soft preference, not a hard gate)

Scoring guidelines:
- Score 9-10: High-growth, AI-ish, novel, highly explainer-worthy
- Score 7-8: Strong growth, interesting, good fit for content
- Score 5-6: Moderate activity, somewhat interesting, acceptable
- Score 1-4: Low growth, boring, or already covered elsewhere

 {{repo_summaries}}

Please return valid JSON for each repository in this exact format:
{{
  "repo": "owner/repo",
  "score": 8.2,
  "reason": "One-sentence reason why this is worth covering"
}}

Score all the repositories above. Return valid JSON array with objects for each repo.""".replace("{{repo_summaries}}", "\n".join(repo_summaries))
    
    def score_repos(self, repos: List[EnrichedRepo]) -> List[ScoredRepo]:
        """
        Score a list of repositories using Mistral with structured output.
        
        Args:
            repos: List of enriched repos to score
            
        Returns:
            List of ScoredRepo objects
        """
        if not repos:
            return []
        
        print(f"\nScoring {len(repos)} repositories with Mistral {self.model}...")
        
        prompt = self._build_batch_prompt(repos)
        
        try:
            response = self.client.chat.complete(
                model=self.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                response_format={
                    "type": "json_object",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "scores": {
                                "type": "array",
                                "items": SCORING_SCHEMA
                            }
                        },
                        "required": ["scores"],
                        "additionalProperties": False
                    }
                },
                temperature=0.3,
                max_tokens=8192
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                parsed = json.loads(content)
                scored_list = parsed.get("scores", [])
                
                scored_repos = []
                for item in scored_list:
                    if isinstance(item, dict) and "repo" in item and "score" in item:
                        scored_repos.append(ScoredRepo(
                            repo=item["repo"],
                            score=float(item.get("score", 0)),
                            reason=item.get("reason", "")
                        ))
                
                print(f"  Mistral scored {len(scored_repos)} repos")
                return scored_repos
                
            except json.JSONDecodeError as e:
                print(f"  Warning: Could not parse Mistral response as JSON: {e}")
                print(f"  Raw response: {content[:500]}...")
                return []
                
        except Exception as e:
            print(f"  Error scoring repos with Mistral: {e}")
            return []
    
    def get_top_repos(
        self, 
        repos: List[EnrichedRepo], 
        top_n: int = 15
    ) -> List[tuple]:
        """
        Score repos and return top N by score.
        
        Args:
            repos: List of enriched repos
            top_n: Number of top repos to return
            
        Returns:
            List of (EnrichedRepo, ScoredRepo) tuples, sorted by score descending
        """
        # Get scores from Mistral
        scored = self.score_repos(repos)
        
        # Map scores back to enriched repos
        score_map = {s.repo: s for s in scored}
        
        # Combine and sort
        combined = []
        for repo in repos:
            if repo.full_name in score_map:
                combined.append((repo, score_map[repo.full_name]))
        
        # Sort by score descending
        combined.sort(key=lambda x: x[1].score, reverse=True)
        
        return combined[:top_n]


def demo():
    """Demo function to test Mistral scorer."""
    print("Mistral Scorer Demo")
    print("=" * 50)
    
    # Create mock enriched repos
    from datetime import datetime
    
    mocks = [
        EnrichedRepo(
            url="https://github.com/example/awesome-ai",
            owner="example",
            repo="awesome-ai",
            full_name="example/awesome-ai",
            stars=5000,
            forks=200,
            language="Python",
            description="AI-powered framework for building agents",
            topics=["ai", "agents", "llm"],
            pushed_at=datetime.now().isoformat(),
            archived=False,
            fork=False,
            created_at=datetime.now().isoformat(),
            homepage="https://example.com",
            readme="# Awesome AI\nBuild amazing AI agents with this framework.",
            velocity=25.0,
            source_name="GitHub Search API",
            discovered_at=datetime.now()
        ),
        EnrichedRepo(
            url="https://github.com/example/simple-tool",
            owner="example",
            repo="simple-tool",
            full_name="example/simple-tool",
            stars=100,
            forks=5,
            language="Go",
            description="A simple CLI tool",
            topics=["cli"],
            pushed_at=datetime.now().isoformat(),
            archived=False,
            fork=False,
            created_at=datetime.now().isoformat(),
            homepage="",
            readme="# Simple Tool\nA command line tool.",
            velocity=0.5,
            source_name="GitHub Trending",
            discovered_at=datetime.now()
        )
    ]
    
    try:
        scorer = MistralScorer()
        
        top_repos = scorer.get_top_repos(mocks, top_n=5)
        
        print(f"\nTop {len(top_repos)} scored repos:")
        for i, (repo, score_repo) in enumerate(top_repos, 1):
            print(f"{i}. {repo.full_name}")
            print(f"   Score: {score_repo.score}")
            print(f"   Reason: {score_repo.reason}")
        
        print("\nDemo completed successfully!")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nRequirements for this demo:")
        print("1. Set Mistral API key in config.json or MISTRAL_API_KEY env var")
        print("2. Install mistralai package: pip install mistralai")


if __name__ == "__main__":
    demo()
