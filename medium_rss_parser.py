import feedparser
import re
import json
from html import unescape

def parse_medium_rss(rss_url):
    """
    Parse Medium RSS feed to extract GitHub projects.
    Medium RSS URL format: https://medium.com/feed/@username
    or for publications: https://medium.com/feed/publication-name
    """
    print(f"🔍 Fetching RSS feed: {rss_url}")
    
    # Parse the RSS feed
    feed = feedparser.parse(rss_url)
    
    if not feed.entries:
        print("❌ No entries found in RSS feed")
        return []
    
    print(f"📰 Found {len(feed.entries)} posts in feed")
    
    # Let user select which post to parse
    print("\nAvailable posts:")
    for i, entry in enumerate(feed.entries[:10]):  # Show first 10
        print(f"{i+1}. {entry.title}")
    
    return feed.entries

def extract_github_projects_from_post(entry):
    """
    Extract GitHub projects from a single Medium post entry.
    """
    print(f"\n📝 Parsing: {entry.title}")
    
    # Get the content (Medium uses content or summary)
    content = entry.get('content', [{}])[0].get('value', '') or entry.get('summary', '')
    
    # Save raw content for debugging
    with open('rss_raw_content.html', 'w') as f:
        f.write(content)
    print(f"💾 Saved raw RSS content to rss_raw_content.html")
    
    # Clean HTML tags but keep text
    content_text = re.sub('<[^<]+?>', '\n', content)
    content_text = unescape(content_text)
    
    # Save cleaned text for debugging
    with open('rss_cleaned_content.txt', 'w') as f:
        f.write(content_text)
    print(f"💾 Saved cleaned content to rss_cleaned_content.txt")
    
    # Find all GitHub URLs - try multiple patterns
    github_pattern = r'https?://github\.com/([^/\s<>"\']+)/([^/\s<>"\']+)'
    matches = re.findall(github_pattern, content)
    
    print(f"🔗 Found {len(matches)} GitHub repositories")
    
    projects = []
    
    # Split content into sections (usually separated by headings or multiple newlines)
    sections = re.split(r'\n{2,}', content_text)
    
    for i, (owner, repo) in enumerate(matches):
        github_url = f"https://github.com/{owner}/{repo}"
        project_name = repo
        
        # Try to find description near the GitHub link
        description = ""
        for section in sections:
            if project_name in section or github_url in section:
                # Clean up the section
                clean_section = section.strip()
                # Remove the GitHub URL itself from description
                clean_section = re.sub(r'https?://\S+', '', clean_section)
                clean_section = ' '.join(clean_section.split())  # Normalize whitespace
                
                if len(clean_section) > 30:  # Only use substantial descriptions
                    description = clean_section
                    break
        
        if not description:
            description = f"{project_name} is a trending GitHub repository worth exploring."
        
        projects.append({
            "id": f"p{i+1}",
            "name": project_name,
            "url": github_url,
            "script": description[:500]  # Limit description length
        })
    
    return projects

def main():
    # Medium RSS feed for sourcescribes publication
    rss_url = "https://medium.com/feed/sourcescribes"
    
    # Get all posts
    entries = parse_medium_rss(rss_url)
    
    if not entries:
        return
    
    # Parse the first post (or let user choose)
    # For now, we'll look for the "9 Trending GitHub Repos" post
    target_post = None
    for entry in entries:
        if "trending github" in entry.title.lower():
            target_post = entry
            break
    
    if not target_post:
        print("\n⚠️  Couldn't find '9 Trending GitHub Repos' post")
        print("Using the first post instead...")
        target_post = entries[0]
    
    # Extract projects
    projects = extract_github_projects_from_post(target_post)
    
    print("\n" + "=" * 60)
    print("EXTRACTED PROJECTS:")
    print("=" * 60)
    
    for project in projects:
        print(f"\n🔹 {project['name']}")
        print(f"   URL: {project['url']}")
        print(f"   Script: {project['script'][:100]}...")
    
    # Save to JSON
    with open('parsed_projects.json', 'w') as f:
        json.dump(projects, f, indent=2)
    
    print(f"\n✅ Saved {len(projects)} projects to parsed_projects.json")

if __name__ == "__main__":
    main()
