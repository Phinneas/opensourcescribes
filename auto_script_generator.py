"""
Auto-Script Generator for GitHub Projects
Fetches GitHub data and generates 2-4 minute narration scripts automatically
"""

import os
import re
import requests
import json
from typing import Dict, Optional, Tuple

# Target word count for 1 minute narration (50% shorter)
MIN_WORDS = 150
MAX_WORDS = 170
TARGET_WORDS = 160


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


def generate_script_template(repo_data: Dict, readme_data: Dict) -> str:
    """
    Generate script using template-based approach (fallback)
    
    Args:
        repo_data: Repository metadata
        readme_data: Parsed README sections
        
    Returns:
        Generated script text
    """
    name = repo_data['name']
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
        tech_details.append(f"Built with {language}, it leverages the language's strengths to deliver robust performance")
    
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
        use_case += " build robust APIs and backend services."
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
    
    return script


def generate_script_ai(repo_data: Dict, readme_data: Dict) -> Optional[str]:
    """
    Generate script using AI (Claude via API)
    
    Args:
        repo_data: Repository metadata
        readme_data: Parsed README sections
        
    Returns:
        Generated script text or None if AI unavailable
    """
    try:
        import anthropic
        
        # Check for API key
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            print("⚠️  ANTHROPIC_API_KEY not set, using template fallback")
            return None
        
        client = anthropic.Anthropic(api_key=api_key)
        
        # Prepare context
        readme_content = readme_data.get('full_text', '')
        if not readme_content:
            print("⚠️  No README content available, using description only")
            readme_content = repo_data.get('description', '')
        
        # Trim README to prevent token overflow (approx 8000 chars)
        readme_content = readme_content[:8000]
        
        prompt = f"""
    Write a short, engaging video script (approx {TARGET_WORDS} words) for a YouTube video about this project:
    
    Project Name: {repo_data['name']}
    Description: {repo_data['description']}
    
    Source Content:
    {readme_content}
    
    Requirements:
    1. Start immediately with what the project DOES. No "Hey guys" or intro.
    2. Explain the key features and why it's useful.
    3. Use a conversational, enthusiastic tone.
    4. End with a short sentence on who should use it.
    5. DO NOT mention specific star counts or fork counts.
    6. DO NOT use emojis or special characters that break TTS.
    7. KEEP IT UNDER {MAX_WORDS} WORDS.
    """

        print("🤖 Generating script with Claude...")
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        script = message.content[0].text.strip()
        
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


def generate_script(github_url: str) -> Optional[Dict]:
    """
    Main function to generate script from GitHub URL
    
    Args:
        github_url: Full GitHub repository URL
        
    Returns:
        Dictionary with project data and generated script
    """
    # Fetch GitHub data
    repo_data = fetch_github_data(github_url)
    
    # Fallback to generic if GitHub fetch failed
    if not repo_data:
        print(f"⚠️  GitHub data fetch failed for {github_url}, trying generic fetch...")
        repo_data = fetch_generic_data(github_url)
        
    if not repo_data:
        print(f"❌ Failed to fetch any data for {github_url}")
        return None
    
    # Fetch README
    # For generic data, owner/repo might not be available or meaningful for README fetch
    readme_text = None
    if 'owner' in repo_data and 'repo' in repo_data:
        readme_text = fetch_readme(repo_data['owner'], repo_data['repo'])
    else:
        print("ℹ️  Skipping README fetch as owner/repo not available from generic data.")

    readme_data = parse_readme_sections(readme_text) if readme_text else {}
    
    # Try AI generation first
    script = generate_script_ai(repo_data, readme_data)
    
    # Fallback to template if AI fails
    if not script:
        print("📝 Using template-based generation...")
        script = generate_script_template(repo_data, readme_data)
    
    word_count = len(script.split())
    print(f"✅ Script generated: {word_count} words (~{word_count/150:.1f} minutes)")
    
    return {
        'name': repo_data['name'],
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
        with open(filepath, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and line.strip().startswith('http')]
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        return []
    
    print(f"Found {len(urls)} URLs\n")
    
    projects = []
    
    for i, url in enumerate(urls, 1):
        print(f"\n{'='*60}")
        print(f"Processing {i}/{len(urls)}: {url}")
        print('='*60)
        
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
                'name': result['name'],
                'github_url': result['github_url'],
                'script_text': result['script_text']
            })
            print(f"✅ Added {result['name']} (ID: {safe_id})")
        else:
            print(f"❌ Failed to process {url}")
    
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
