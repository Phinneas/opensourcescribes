import asyncio
from playwright.async_api import async_playwright
import json
import re

async def parse_medium_post(url):
    """
    Parses a Medium post and extracts GitHub project information.
    Returns a list of projects with name, url, and description.
    """
    print(f"🔍 Parsing Medium post: {url}")
    
    async with async_playwright() as p:
        browser = await p.firefox.launch(headless=True)
        page = await browser.new_page()
        
        try:
            # Load the Medium post
            print("⏳ Loading page...")
            await page.goto(url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)
            
            # Scroll down to load all content
            print("📜 Scrolling to load dynamic content...")
            for _ in range(5):
                await page.evaluate("window.scrollBy(0, window.innerHeight)")
                await page.wait_for_timeout(1000)
            
            # Wait for article content
            await page.wait_for_selector('article', timeout=10000)
            
            # Extract all text content
            content = await page.inner_text('article')
            
            # Extract GitHub links using multiple methods
            # Method 1: Direct GitHub links
            github_links_elements = await page.query_selector_all('a[href*="github.com"]')
            links = []
            for element in github_links_elements:
                url = await element.get_attribute('href')
                text = await element.inner_text()
                if url and 'github.com' in url:
                    links.append({'url': url, 'text': text})
            
            # Get all paragraphs and headings for context
            paragraphs = await page.eval_on_selector_all(
                'article p, article h1, article h2, article h3',
                'elements => elements.map(el => el.textContent)'
            )
            
            await browser.close()
            
            # Process the extracted data
            projects = []
            github_links = [link for link in links if 'github.com' in link['url']]
            
            print(f"\n📊 Found {len(github_links)} GitHub links")
            print(f"📝 Found {len(paragraphs)} paragraphs\n")
            
            # Try to match GitHub links with their descriptions
            for i, link in enumerate(github_links):
                github_url = link['url']
                
                # Extract project name from URL
                match = re.search(r'github\.com/([^/]+)/([^/\?#]+)', github_url)
                if match:
                    owner, repo = match.groups()
                    project_name = repo
                    
                    # Find the description (look for paragraphs near this link)
                    # This is a simple heuristic - we'll improve it based on your post structure
                    description = ""
                    for para in paragraphs:
                        if project_name.lower() in para.lower() or repo.lower() in para.lower():
                            # Clean up the paragraph
                            clean_para = para.strip()
                            if len(clean_para) > 20:  # Skip very short paragraphs
                                description = clean_para
                                break
                    
                    if not description and i < len(paragraphs):
                        # Fallback: use a nearby paragraph
                        description = paragraphs[min(i, len(paragraphs)-1)]
                    
                    projects.append({
                        "id": f"p{i+1}",
                        "name": project_name,
                        "url": github_url,
                        "script": description or f"{project_name} is an interesting GitHub project worth checking out."
                    })
            
            return projects, content, paragraphs
            
        except Exception as e:
            print(f"❌ Error parsing Medium post: {e}")
            await browser.close()
            return [], "", []

async def main():
    # Test with your Medium post
    url = "https://medium.com/sourcescribes/9-trending-github-repos-672c1d76f28b"
    
    projects, full_content, paragraphs = await parse_medium_post(url)
    
    print("=" * 60)
    print("EXTRACTED PROJECTS:")
    print("=" * 60)
    
    for project in projects:
        print(f"\n🔹 {project['name']}")
        print(f"   URL: {project['url']}")
        print(f"   Script: {project['script'][:100]}...")
    
    # Save to JSON for inspection
    with open('parsed_projects.json', 'w') as f:
        json.dump(projects, f, indent=2)
    
    print(f"\n✅ Saved {len(projects)} projects to parsed_projects.json")
    
    # Also save raw content for debugging
    with open('medium_content.txt', 'w') as f:
        f.write(full_content)
    
    print("✅ Saved full content to medium_content.txt for inspection")

if __name__ == "__main__":
    asyncio.run(main())
