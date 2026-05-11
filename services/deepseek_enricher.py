#!/usr/bin/env python3
"""
DeepSeek Enricher - Enriches GitHub API data with deep content analysis.

Takes the structured metadata from GitHub API (stars, language, description)
plus the raw README content, and extracts structured insights that raw
API data cannot provide: key features, use cases, technical highlights,
differentiators, and content angles.

Pipeline role: Enrichment (between GitHub API ingestion and Claude writing)
- GitHub API fetches the raw data (fast, free, deterministic)
- DeepSeek enriches it with deeper analysis
- Claude writes the narration script from the enriched data
"""

import json
import os
import requests
from typing import Dict, Optional, List


REPO_ENRICHMENT_SCHEMA = {
    "type": "object",
    "properties": {
        "project_name": {"type": "string"},
        "one_line_description": {"type": "string"},
        "key_features": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 5
        },
        "technical_highlight": {"type": "string"},
        "use_cases": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3
        },
        "target_audience": {"type": "string"},
        "differentiator": {"type": "string"},
        "momentum_signal": {"type": "string"},
        "content_angle": {"type": "string"}
    },
    "required": [
        "project_name", "one_line_description", "key_features",
        "technical_highlight", "use_cases", "differentiator", "content_angle"
    ],
    "additionalProperties": False
}


class DeepSeekEnricher:
    """
    DeepSeek-based content enricher for repository analysis.

    Takes GitHub API data + README and produces structured insights
    (features, use cases, differentiator, content angle) that feed
    directly into Claude for script writing.
    """

    def __init__(self, model: str = "deepseek-chat", api_base: str = "https://api.deepseek.com"):
        self.model = model
        self.api_base = api_base
        self.api_key = self._load_api_key()
        self.timeout = 60

    def _load_api_key(self) -> str:
        """Load DeepSeek API key from config.json or environment."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                'config.json'
            )
            with open(config_path, 'r') as f:
                config = json.load(f)
            key = config.get('deepseek', {}).get('api_key')
            if key:
                return key
        except Exception:
            pass

        key = os.environ.get('DEEPSEEK_API_KEY')
        if key:
            return key

        raise ValueError(
            "DeepSeek API key not found. Add to config.json under deepseek.api_key "
            "or set DEEPSEEK_API_KEY environment variable."
        )

    def _build_enrichment_prompt(self, repo_data: Dict, readme_content: str,
                                  velocity_data: str = "") -> str:
        """Build prompt for DeepSeek to enrich repo data with structured insights."""
        readme_excerpt = readme_content[:4000] if readme_content else "No README available."

        return f"""You are a technical content analyst evaluating open-source repositories for a developer-focused content platform.

Analyze this repository and extract structured data for content production.

REPOSITORY DATA (from GitHub API):
- Name: {repo_data.get('name', 'Unknown')}
- Full name: {repo_data.get('full_name', 'Unknown')}
- Description: {repo_data.get('description', 'No description')}
- Language: {repo_data.get('language', 'Unknown')}
- Stars: {repo_data.get('stars', 0)}
- Topics: {', '.join(repo_data.get('topics', [])[:10])}
- License: {repo_data.get('license', 'Unknown')}
{velocity_data}

README CONTENT (excerpt):
{readme_excerpt}

Extract the following structured information. Be specific and technical — no marketing fluff.

1. project_name: The repo name as-is
2. one_line_description: What it DOES in one concrete sentence (not what it "aims to" do)
3. key_features: 3-5 specific technical capabilities (not generic buzzwords)
4. technical_highlight: The single most interesting technical implementation detail
5. use_cases: 2-3 concrete scenarios where developers would use this
6. target_audience: Who should care about this (be specific, e.g. "Backend engineers building event-driven systems")
7. differentiator: What makes this different from alternatives (name them if possible)
8. momentum_signal: Why this project is worth covering NOW (recent growth, new feature, timing)
9. content_angle: The most compelling narrative angle for a 60-second video segment

BANNED WORDS: robust, seamless, game-changer, revolutionary, cutting-edge, leverage, supercharge, unlock, hidden gem, dive in

Return ONLY valid JSON matching this schema:
{json.dumps(REPO_ENRICHMENT_SCHEMA, indent=2)}"""

    def enrich_repo(self, repo_data: Dict, readme_content: str,
                     velocity_data: str = "") -> Optional[Dict]:
        """
        Enrich GitHub API data with DeepSeek analysis.

        Args:
            repo_data: GitHub API metadata dict
            readme_content: Raw README text
            velocity_data: Optional velocity/momentum stats string

        Returns:
            Structured dict with enriched content, or None if failed
        """
        prompt = self._build_enrichment_prompt(repo_data, readme_content, velocity_data)

        try:
            response = requests.post(
                f"{self.api_base}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a technical content analyst. Always respond with valid JSON only. No markdown, no code fences, just the raw JSON object."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2048,
                    "response_format": {"type": "json_object"}
                },
                timeout=self.timeout
            )

            if response.status_code != 200:
                print(f"  DeepSeek HTTP {response.status_code}: {response.text[:200]}")
                return None

            data = response.json()
            content = data["choices"][0]["message"]["content"]

            parsed = json.loads(content)

            # Validate required fields exist
            required = REPO_ENRICHMENT_SCHEMA["required"]
            missing = [f for f in required if f not in parsed]
            if missing:
                print(f"  DeepSeek enrichment missing fields: {missing}")
                for f in missing:
                    if f in ("key_features", "use_cases"):
                        parsed[f] = []
                    else:
                        parsed[f] = ""

            return parsed

        except json.JSONDecodeError as e:
            print(f"  DeepSeek returned invalid JSON: {e}")
            return None
        except requests.Timeout:
            print(f"  DeepSeek request timed out")
            return None
        except Exception as e:
            print(f"  DeepSeek enrichment error: {e}")
            return None

    def enrich_repos_batch(self, repos: List[Dict]) -> List[Dict]:
        """
        Enrich multiple repos, returning structured extractions.

        Args:
            repos: List of dicts with 'repo_data', 'readme', and optional 'velocity' keys

        Returns:
            List of enriched dicts (failed repos are skipped)
        """
        results = []
        total = len(repos)

        for i, repo_info in enumerate(repos, 1):
            name = repo_info.get('repo_data', {}).get('name', 'unknown')
            print(f"  [{i}/{total}] DeepSeek enriching: {name}...")

            enrichment = self.enrich_repo(
                repo_data=repo_info.get('repo_data', {}),
                readme_content=repo_info.get('readme', ''),
                velocity_data=repo_info.get('velocity', '')
            )

            if enrichment:
                enrichment['_source_url'] = repo_info.get('repo_data', {}).get('github_url', '')
                results.append(enrichment)
                print(f"    Enriched: {enrichment.get('one_line_description', 'N/A')[:80]}...")
            else:
                print(f"    Skipped {name} — enrichment failed")

        print(f"\n  DeepSeek enriched {len(results)}/{total} repos successfully")
        return results
