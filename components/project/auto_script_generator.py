"""
Auto-Script Generator for GitHub Projects

Pipeline:
  1. GitHub API: Fetches raw metadata + README (fast, free, deterministic)
  2. DeepSeek:   Enriches API data with structured insights (features, angles, differentiator)
  3. Claude:     Writes narration script from enriched data
"""

import os
import re
import requests
import json
from typing import Dict, Optional, Tuple

# Target word count for ~39-46 second narration (~150wpm speaking pace)
MIN_WORDS = 100
MAX_WORDS = 115
TARGET_WORDS = 107


def fetch_github_data(github_url: str) -> Optional[Dict]:
    """
    Fetch repository metadata from GitHub API
    
    Args:
        github_url: Full GitHub repository URL
        
    Returns:
        Dictionary with repo data or None if failed
    """
    # Extract owner/repo from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)', github_url)
    if not match:
        print(f"❌ Invalid GitHub URL: {github_url}")
        return None
    
    owner, repo = match.groups()
    repo = repo.rstrip('/')  # Remove trailing slash if present
    
    print(f"📡 Fetching data for {owner}/{repo}...")
    
    try:
        # GitHub API endpoint
        api_url = f"https://api.github.com/repos/{owner}/{repo}"
        response = requests.get(api_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return {
                'owner': owner,
                'repo': repo,
                'name': data.get('name', repo),
                'full_name': data.get('full_name', f'{owner}/{repo}'),
                'description': data.get('description', ''),
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'language': data.get('language', 'Unknown'),
                'topics': data.get('topics', []),
                'homepage': data.get('homepage', ''),
                'created_at': data.get('created_at', ''),
                'updated_at': data.get('updated_at', ''),
                'license': (data.get('license') or {}).get('name', 'No license'),
                'github_url': github_url
            }
        elif response.status_code == 404:
            print(f"❌ Repository not found: {owner}/{repo}")
        else:
            print(f"⚠️  GitHub API error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Failed to fetch GitHub data: {e}")
    
    except Exception as e:
        print(f"❌ Failed to fetch GitHub data: {e}")
    
    return None

def fetch_generic_data(url: str) -> Optional[Dict]:
    """Fetch metadata from a generic website"""
    print(f"🌍 Fetching generic web data for {url}...")
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            return None
            
        content = response.text
        
        # Simple regex extraction since bs4 might not be everywhere (though we checked)
        # Using regex for speed and dependency-free baseline
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url.split('//')[-1].split('/')[0]
        
        desc_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', content, re.IGNORECASE)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Clean up title
        name = title.split(' - ')[0].split(' | ')[0].strip()
        
        return {
            'owner': 'web',
            'repo': name.replace(' ', '_').lower(),
            'name': name,
            'full_name': name,
            'description': description,
            'stars': 0,
            'forks': 0,
            'language': 'Web',
            'topics': ['website'],
            'homepage': url,
            'created_at': '',
            'github_url': url
        }
    except Exception as e:
        print(f"❌ Failed to fetch generic data: {e}")
        return None

def fetch_clickhouse_stats(owner: str, repo: str) -> Optional[str]:
    """
    Fetch trending/velocity metrics for a repository using the public ClickHouse GitTrends API.
    Provides nuance to the project description by pulling actual 30-day velocity.
    """
    print(f"📊 Fetching ClickHouse metrics for {owner}/{repo}...")
    try:
        query = f"""
            SELECT 
                countIf(event_type = 'PullRequestEvent') as pr_events,
                countIf(event_type = 'IssuesEvent') as issue_events,
                uniqExact(actor_login) as active_contributors
            FROM github_events 
            WHERE repo_name = '{owner}/{repo}' 
              AND created_at > now() - INTERVAL 30 DAY
            FORMAT JSON
        """
        response = requests.post(
            'https://play.clickhouse.com/?user=explorer',
            data=query.strip(),
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            if data and "data" in data and len(data["data"]) > 0:
                stats = data["data"][0]
                prs = int(stats.get("pr_events", 0))
                issues = int(stats.get("issue_events", 0))
                contributors = int(stats.get("active_contributors", 0))
                
                # If project has no recent activity, return empty to not clutter the prompt
                if prs == 0 and issues == 0:
                    return ""
                    
                context = f"Project Velocity (Last 30 Days): The project has had great momentum with {contributors} active contributors interacting with {prs} PR events and {issues} issue events recently."
                print(f"   ✅ ClickHouse stats found: {contributors} contributors, {prs} PRs")
                return context
    except Exception as e:
        print(f"   ⚠️ ClickHouse stats fetch skipped/failed (Timeout/Error: {e})")
        
    return ""



def fetch_readme(owner: str, repo: str) -> Optional[str]:
    """
    Fetch README content from GitHub repository
    
    Args:
        owner: Repository owner
        repo: Repository name
        
    Returns:
        README content as string or None if not found
    """
    print(f"📄 Fetching README for {owner}/{repo}...")
    
    # Try common README filenames
    readme_names = ['README.md', 'README.MD', 'readme.md', 'README', 'README.txt']
    
    for readme_name in readme_names:
        try:
            # Raw content URL
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{readme_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Found {readme_name}")
                return response.text
            
            # Try 'master' branch if 'main' fails
            url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{readme_name}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                print(f"✅ Found {readme_name}")
                return response.text
                
        except Exception as e:
            continue
    
    print("⚠️  README not found")
    return None


def parse_readme_sections(readme_text: str) -> Dict[str, str]:
    """
    Extract key sections from README
    
    Args:
        readme_text: Full README content
        
    Returns:
        Dictionary with extracted sections
    """
    if not readme_text:
        return {}
    
    # Limit to first 3000 characters for processing
    readme_text = readme_text[:3000]
    
    sections = {
        'intro': '',
        'features': '',
        'installation': '',
        'usage': '',
        'full_text': readme_text
    }
    
    # Clean up the text
    lines = readme_text.split('\n')
    content_lines = []
    
    for line in lines:
        # Skip badges, images, and HTML
        if any(x in line.lower() for x in ['![', '](http', '<img', '<a href', 'badge', '<p align', '</p>', '<br']):
            continue
        # Skip headers (we'll extract content only)
        if line.strip().startswith('#'):
            continue
        # Skip horizontal rules
        if line.strip().startswith('---') or line.strip().startswith('==='):
            continue
        # Skip empty lines
        if not line.strip():
            continue
            
        # Clean markdown formatting
        cleaned = line.strip()
        cleaned = re.sub(r'\*\*([^*]+)\*\*', r'\1', cleaned)  # Bold
        cleaned = re.sub(r'\*([^*]+)\*', r'\1', cleaned)  # Italic
        cleaned = re.sub(r'`([^`]+)`', r'\1', cleaned)  # Code
        cleaned = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', cleaned)  # Links
        cleaned = re.sub(r'^[•\-\*]\s+', '', cleaned)  # List markers
        cleaned = re.sub(r':\w+:', '', cleaned)  # Emoji codes like :rocket:
        
        # Skip if still contains HTML-like tags
        if '<' in cleaned and '>' in cleaned:
            continue
            
        # Collect meaningful content
        if cleaned and len(cleaned) > 10:  # Skip very short lines
            content_lines.append(cleaned)
    
    # Take first 15 meaningful lines as intro
    sections['intro'] = ' '.join(content_lines[:15])
    
    return sections


def _clean_project_name(name: str) -> str:
    """
    Strip special characters from project names so TTS never narrates
    symbols like '*', '#', '@', etc.  Keeps letters, digits, spaces,
    hyphens, and dots (e.g. 'v2.0' or 'my-project' are fine).
    """
    # Remove any character that is NOT a letter, digit, space, hyphen, or dot
    cleaned = re.sub(r'[^a-zA-Z0-9 \-\.]', '', name)
    # Collapse multiple spaces / hyphens that may result
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # Strip leading/trailing hyphens or dots
    cleaned = cleaned.strip('-.')
    return cleaned if cleaned else name  # fallback to original if cleaning emptied it


def generate_script_template(repo_data: Dict, readme_data: Dict) -> str:
    """
    Generate script using template-based approach (fallback)
    
    Args:
        repo_data: Repository metadata
        readme_data: Parsed README sections
        
    Returns:
        Generated script text
    """
    name = _clean_project_name(repo_data['name'])
    description = repo_data.get('description') or ''
    language = repo_data['language']
    stars = repo_data['stars']
    forks = repo_data['forks']
    topics = repo_data['topics'][:5] if repo_data['topics'] else []
    readme_intro = readme_data.get('intro', '')
    
    # Build comprehensive script
    script_parts = []
    
    # 1. Introduction (what it is)
    intro = f"{name} is"
    if language and language != 'Unknown':
        intro += f" a {language}-based project"
    if description:
        intro += f" that {description.lower() if description[0].isupper() else description}."
    else:
        intro += " an open-source tool available on GitHub."
    script_parts.append(intro)
    
    # 2. Detailed description from README (shortened)
    if readme_intro and len(readme_intro) > 50:
        # Add README content - much shorter excerpt
        script_parts.append(readme_intro[:300])  # Concise excerpt
    
    # 3. Key features and capabilities
    if topics:
        topics_str = ', '.join(topics)
        script_parts.append(f"This project focuses on {topics_str}, providing developers with specialized tools and capabilities in these areas.")
    
    # 4. Technical details
    tech_details = []
    if language and language != 'Unknown':
        tech_details.append(f"Built with {language}, it leverages the language's strengths to deliver reliable performance")
    
    # Forks removed per user request (displayed on screen)
    # if forks > 50:
    #     tech_details.append(f"The codebase has been forked over {forks:,} times, indicating active development and community contributions")
    
    if tech_details:
        script_parts.append('. '.join(tech_details) + '.')
    
    # 5. Community and adoption - REMOVED per user request
    # Stars and forks are displayed on screen, so no need to narrate them.
    pass
    
    # 6. Use cases and applications
    use_case = f"Developers can integrate {name} into their workflows to"
    description_lower = description.lower() if description else ''
    if 'api' in name.lower() or 'api' in description_lower:
        use_case += " build high-performance APIs and backend services."
    elif 'ui' in name.lower() or 'component' in description_lower:
        use_case += " create polished user interfaces and interactive components."
    elif 'data' in description_lower or 'database' in description_lower:
        use_case += " manage and process data more effectively."
    elif 'test' in description_lower:
        use_case += " improve their testing strategies and code quality."
    elif 'deploy' in description_lower or 'devops' in description_lower:
        use_case += " streamline their deployment and infrastructure management."
    else:
        use_case += " solve complex technical challenges more efficiently."
    script_parts.append(use_case)
    
    # 7. Conclusion (simplified)
    if stars > 5000:
        script_parts.append(f"{name} is worth exploring for your next project.")
    else:
        script_parts.append(f"Check out {name} if you're working in this space.")
    
    script = ' '.join(script_parts)
    
    # Clean up script: remove emojis and non-standard characters causing TTS artifacts
    # Keep alphanumeric, punctuation, and spaces. Remove others.
    # But we want to keep some accents maybe? For English TTS, staying ASCII compatible is safest for now,
    # or just filtering known emoji ranges. simpler: remove anything that isn't basic punctuation or allowed chars.
    
    import re
    # Remove emojis and symbols often found in GitHub descriptions
    # Keep: a-z, A-Z, 0-9, ., ,, !, ?, ', ", -, (, ), space
    # We'll replace others with space
    script = re.sub(r'[^a-zA-Z0-9\.,!\?\'"\-\(\) \n]', ' ', script)
    
    # Fix multiple spaces
    script = re.sub(r'\s+', ' ', script).strip()
    
    # Post-process to replace first-person pronouns with generalized second-person
    script = re.sub(r"\bI\b", "you", script)
    script = re.sub(r"\bI'm\b", "you're", script, flags=re.IGNORECASE)
    script = re.sub(r"\bI've\b", "you've", script, flags=re.IGNORECASE)
    script = re.sub(r"\bI'll\b", "you'll", script, flags=re.IGNORECASE)
    script = re.sub(r"\bI'd\b", "you'd", script, flags=re.IGNORECASE)
    script = re.sub(r"\b[mM]y\b", "your", script)
    script = re.sub(r"\b[wW]e\b", "you", script)
    script = re.sub(r"\b[mM]e\b", "you", script)
    
    return script


def generate_script_ai(repo_data: Dict, readme_data: Dict, enriched_data: Optional[Dict] = None) -> Optional[str]:
    """
    Generate script using Claude, using enriched data from DeepSeek for richer context.
    
    Args:
        repo_data: Repository metadata (from GitHub API)
        readme_data: Parsed README sections
        enriched_data: Optional structured insights from DeepSeek enricher
        
    Returns:
        Generated script text or None if AI unavailable
    """
    try:
        import anthropic
        
        # Check for API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                api_key = config.get('anthropic', {}).get('api_key')
            except:
                pass
                
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not set and not in config.json, using template fallback")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Prepare context — prefer enriched data if available, otherwise raw README
        if enriched_data:
            context_block = f"""
ENRICHED ANALYSIS (DeepSeek):
- One-line description: {enriched_data.get('one_line_description', '')}
- Key features: {', '.join(enriched_data.get('key_features', []))}
- Technical highlight: {enriched_data.get('technical_highlight', '')}
- Use cases: {', '.join(enriched_data.get('use_cases', []))}
- Target audience: {enriched_data.get('target_audience', '')}
- Differentiator: {enriched_data.get('differentiator', '')}
- Momentum signal: {enriched_data.get('momentum_signal', '')}
- Content angle: {enriched_data.get('content_angle', '')}
"""
        else:
            readme_content = readme_data.get('full_text', '')
            if not readme_content:
                readme_content = repo_data.get('description', '')
            readme_content = readme_content[:8000]
            context_block = f"\nSource Content:\n{readme_content}\n"
        
        # Fetch optional nuance stats from ClickHouse
        ch_stats_text = ""
        if 'owner' in repo_data and 'repo' in repo_data:
            ch_stats_text = fetch_clickhouse_stats(repo_data['owner'], repo_data['repo'])
            
        # Clean the project name of special characters before sending to AI
        cleaned_name = _clean_project_name(repo_data['name'])

        prompt = f"""
    Write a short, engineering-focused video script (approx {TARGET_WORDS} words) for a YouTube video about this project:
    
    Project Name: {cleaned_name}
    Description: {repo_data['description']}
    {ch_stats_text}
    {context_block}
    
    Requirements:
    1. Start immediately with what the project DOES. No "Hey guys" or intro.
    2. Explain the technical utility and unique implementation. If project velocity stats are provided above, weave that momentum gracefully into the script.
    3. Use a direct, informative tone. Avoid marketing hype.
    4. End with a short sentence on the primary use case.
    5. DO NOT use these words: Robust, Gems, Supercharge, Game changer, Dive in, Revolutionary, Unlock, Pique, Workflow.
    6. DO NOT mention specific star counts or fork counts.
    7. DO NOT use emojis or special characters that break TTS.
    8. KEEP IT UNDER {MAX_WORDS} WORDS.
    9. NEVER use first-person pronouns like 'I', 'me', 'my', or 'we'. Always use the generalized 'you', 'your', 'developers', or 'users' instead. The script is spoken by an impartial narrator.
   10. When naming the project, use ONLY the project name "{cleaned_name}" exactly as written. Do NOT add any prefix, suffix, or special characters (no asterisks, hashes, at-signs, or other symbols) before or after the project name.
        """
        
        print("🤖 Claude: Writing script from enriched data...")

        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        script = message.content[0].text.strip()
        
        # Post-process to aggressively catch any slipping first-person pronouns
        import re
        script = re.sub(r"\bI\b", "you", script)
        script = re.sub(r"\bI'm\b", "you're", script, flags=re.IGNORECASE)
        script = re.sub(r"\bI've\b", "you've", script, flags=re.IGNORECASE)
        script = re.sub(r"\bI'll\b", "you'll", script, flags=re.IGNORECASE)
        script = re.sub(r"\bI'd\b", "you'd", script, flags=re.IGNORECASE)
        script = re.sub(r"\b[mM]y\b", "your", script)
        script = re.sub(r"\b[wW]e\b", "you", script)
        script = re.sub(r"\b[mM]e\b", "you", script)
        
        # Validate word count
        word_count = len(script.split())
        print(f"✅ Generated {word_count} words")
        
        if word_count < MIN_WORDS or word_count > MAX_WORDS:
            print(f"⚠️  Word count outside target range ({MIN_WORDS}-{MAX_WORDS}), adjusting...")
            # Use it anyway, close enough
        
        return script
        
    except ImportError:
        print("⚠️  anthropic package not installed, using template fallback")
        return None
    except Exception as e:
        print(f"⚠️  AI generation failed: {e}")
        return None


def _run_deepseek_enrichment(repo_data: Dict, readme_text: Optional[str]) -> Optional[Dict]:
    """
    Run DeepSeek enrichment on GitHub API data + README.
    Returns structured insights dict, or None if DeepSeek unavailable.
    
    Args:
        repo_data: GitHub API metadata dict
        readme_text: Raw README content
        
    Returns:
        Enriched insights dict or None
    """
    try:
        from services.deepseek_enricher import DeepSeekEnricher
    except ImportError:
        print("⚠️  deepseek_enricher module not available, skipping enrichment")
        return None
    
    try:
        enricher = DeepSeekEnricher()
    except ValueError as e:
        print(f"⚠️  DeepSeek unavailable ({e}), skipping enrichment")
        return None
    
    print("🔍 DeepSeek: Enriching repo data...")
    
    try:
        enrichment = enricher.enrich_repo(repo_data, readme_text or "")
        
        if not enrichment:
            print("⚠️  DeepSeek enrichment returned None")
            return None
        
        print(f"   Enriched: {enrichment.get('one_line_description', 'N/A')[:80]}...")
        return enrichment
        
    except Exception as e:
        print(f"⚠️  DeepSeek enrichment failed: {e}")
        return None


def generate_script(github_url: str) -> Optional[Dict]:
    """
    Main function to generate script from GitHub URL.
    
    Pipeline:
      1. GitHub API: Fetch raw metadata + README
      2. DeepSeek:   Enrich with structured insights
      3. Claude:     Write narration script from enriched data
    
    Falls back to template if any stage fails.
    
    Args:
        github_url: Full GitHub repository URL
        
    Returns:
        Dictionary with project data and generated script
    """
    # Step 1: Fetch GitHub API data
    repo_data = fetch_github_data(github_url)
    
    # Fallback to generic if GitHub fetch failed
    if not repo_data:
        print(f"⚠️  GitHub data fetch failed for {github_url}, trying generic fetch...")
        repo_data = fetch_generic_data(github_url)
        
    if not repo_data:
        print(f"❌ Failed to fetch any data for {github_url}")
        return None
    
    # Fetch README (raw content for DeepSeek analysis)
    readme_text = None
    if 'owner' in repo_data and 'repo' in repo_data:
        readme_text = fetch_readme(repo_data['owner'], repo_data['repo'])
    else:
        print("ℹ️  Skipping README fetch as owner/repo not available from generic data.")

    readme_data = parse_readme_sections(readme_text) if readme_text else {}
    
    # Clean name of special characters for TTS-friendly output
    clean_name = _clean_project_name(repo_data['name'])

    # Step 2: DeepSeek enrichment
    enriched_data = _run_deepseek_enrichment(repo_data, readme_text)

    # Step 3: Claude writes script (uses enriched data if available)
    script = generate_script_ai(repo_data, readme_data, enriched_data=enriched_data)
    
    # Fallback to template if AI fails
    if not script:
        print("📝 Using template-based generation...")
        script = generate_script_template(repo_data, readme_data)
    
    word_count = len(script.split())
    print(f"✅ Script generated: {word_count} words (~{word_count/150:.1f} minutes)")
    
    return {
        'name': clean_name,
        'github_url': github_url,
        'script_text': script,
        'metadata': {
            'stars': repo_data['stars'],
            'language': repo_data['language'],
            'word_count': word_count
        }
    }


def generate_from_url_list(filepath: str) -> list:
    """
    Generate scripts for all URLs in a file
    
    Args:
        filepath: Path to file with GitHub URLs (one per line)
        
    Returns:
        List of project dictionaries
    """
    print(f"📖 Reading URLs from: {filepath}")
    
    try:
        urls = []
        with open(filepath, 'r') as f:
            for line in f:
                url = line.strip()
                if not url:
                    continue
                # Prepend https:// if missing
                if not url.startswith('http'):
                    if 'github.com' in url or '.' in url:
                        url = 'https://' + url
                    else:
                        continue
                urls.append(url)
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return []
    
    print(f"Found {len(urls)} URLs\n")
    
    projects = []
    processed_repo_names = set()
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(urls)}: {url}")
        print('='*60)
        
        # ERROR CHECK: Ensure it's a GitHub URL to prevent scraping personal blogs
        if 'github.com' not in url:
            print(f"⚠️  ERROR CHECK: Skipping non-GitHub URL to prevent scraping errors: {url}")
            continue
            
        # Extract repo name for duplicate fork check
        repo_name_lower = ""
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if match:
            repo_name_lower = match.group(2).lower()
            
        if repo_name_lower in processed_repo_names:
            print(f"⚠️  Skipping duplicate fork: {url}")
            continue
            
        if repo_name_lower:
            processed_repo_names.add(repo_name_lower)
        
        result = generate_script(url)
        if result:
             # Generate unique ID from URL (e.g., owner_repo)
            safe_id = re.sub(r'[^a-zA-Z0-9]', '_', result['name']).lower()
            # If repo name is generic, prepend owner? But name usually unique enough for local list.
            # Better: use full_name if available in result (it is not currently returned in root dict)
            # Let's extract from URL: github.com/owner/repo
            match = re.search(r'github\.com/([^/]+)/([^/]+)', result['github_url'])
            if match:
                owner, repo = match.groups()
                safe_id = f"{owner}_{repo}".lower().replace('-', '_')
            
            projects.append({
                'id': safe_id,
                'name': _clean_project_name(result['name']),
                'github_url': result['github_url'],
                'script_text': result['script_text']
            })
            print(f"✅ Added {result['name']} (ID: {safe_id})")
        else:
            print(f"⚠️  Failed to process {url}. Adding fallback entry.")
            # Fallback entry to ensure it's not skipped in blogs/social
            match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if match:
                owner, repo = match.groups()
                name = repo
                safe_id = f"{owner}_{repo}".lower().replace('-', '_')
            else:
                name = url.split('/')[-1] or "Unknown Project"
                safe_id = f"unknown_{i}"
                
            projects.append({
                'id': safe_id,
                'name': _clean_project_name(name),
                'github_url': url,
                'script_text': f"{_clean_project_name(name)} is an interesting open source project found on GitHub. Check out the link to learn more about its features and implementation."
            })
            print(f"✅ Added fallback for {name} (ID: {safe_id})")
    
    return projects


if __name__ == "__main__":
    import sys
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate video scripts from GitHub URLs')
    parser.add_argument('--input', '-i', default='github_urls.txt', help='Input file with GitHub URLs')
    parser.add_argument('--output', '-o', default='posts_data.json', help='Output JSON file')
    parser.add_argument('--test', action='store_true', help='Run simple test')
    
    args = parser.parse_args()
    
    if args.test:
        print("🧪 Testing with sample URL...\n")
        test_url = "https://github.com/oraios/Serena"
        result = generate_script(test_url)
        if result:
            print(f"\n{'='*60}")
            print("GENERATED SCRIPT:")
            print('='*60)
            print(result['script_text'])
            print(f"\n{'='*60}")
            print(f"Word count: {result['metadata']['word_count']}")
    else:
        # Process input file
        projects = generate_from_url_list(args.input)
        
        if projects:
            with open(args.output, 'w') as f:
                json.dump(projects, f, indent=4)
            print(f"\n✅ Successfully saved {len(projects)} projects to {args.output}")
        else:
            print("\n❌ No projects generated")
