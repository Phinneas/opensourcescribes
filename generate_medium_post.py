"""
Generate Medium blog post from project data using Claude API
Processes projects individually to ensure none are skipped.
"""

import json
import os
import datetime
import anthropic

# --- PROMPT TEMPLATES ---

CLICHE_FILTER = """
Vary sentence length — some short, some longer and more specific. Banned words: robust, streamline, supercharge, game-changer, revolutionary, seamless, dive in, hidden gems, powerful, cutting-edge, leverage, utilize. Banned constructions: "Designed for...", "Whether you're a X, Y, or Z", "Key features include:", three-part lists where everything sounds equally important. Not everything needs to sound exciting. Match enthusiasm to actual interestingness.
"""

INTRO_PROMPT = """Write an opening for a developer tools roundup on Medium called OpenSourceScribes.
Skip any thesis statement about open source or developer productivity — get straight to what's interesting about this particular batch of tools.
One specific observation is better than a general one.
Include these promo links naturally in the text, not as a list:
{promo_links}

Projects in this batch:
{project_summaries}

{cliche_filter}

100 words maximum. Editorial tone — opinionated, direct, not promotional. Do not use '#' or '*' symbols."""

PROJECT_SECTION_PROMPT = """Write a short description of this GitHub project for a developer tools roundup on Medium.

Project details:
Name: {name}
GitHub: {url}
Description: {description}

Rules:
- Length should reflect how interesting the tool actually is. A niche or early-stage tool gets 2-3 sentences. A genuinely useful one gets 4-5.
- Say what problem it actually solves, not what category it belongs to
- If it has a meaningful limitation or caveat, mention it
- No headers, no feature lists, no asterisks
- Don't start with the project name as the subject of the sentence
- End with: View on GitHub: {url}

{cliche_filter}

Tone: a knowledgeable colleague who has looked at a lot of tools and has a calibrated sense of what's actually worth attention. Do not use '#' or '*' symbols."""

OUTRO_PROMPT = """Write a closing paragraph for this developer tools roundup.
Don't summarize trends in open source software generally.
Instead, make 1-2 specific observations about what stands out in this particular batch of tools — what problem they're collectively solving, or what surprised you, or what feels early but worth watching.
3-4 sentences maximum. No hype. No universal statements about the future of software engineering.

Projects covered:
{project_names}

{cliche_filter}

Do not use '#' or '*' symbols."""

CONSISTENCY_PASS_PROMPT = """Below are sections of a developer tools roundup written separately.
Lightly edit for consistent tone and varied rhythm without rewriting the substance.
Flag any two sections that sound identical in structure and vary one of them.
Do not add headers, asterisks, or markdown formatting. Return the full edited text only.

{content}"""

# --- FUNCTIONS ---

def get_client():
    """Initialize Anthropic client"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            api_key = config.get('anthropic', {}).get('api_key')
        except:
            pass
    
    if not api_key:
        print("❌ Anthropic API key not found")
        return None
    
    return anthropic.Anthropic(api_key=api_key)

def load_projects():
    """Load project data from JSON"""
    data_file = 'posts_data_longform.json'
    if not os.path.exists(data_file):
        data_file = 'posts_data.json'
        
    if not os.path.exists(data_file):
        return None

    with open(data_file, 'r') as f:
        projects = json.load(f)
    return projects

def call_claude(client, prompt, model="claude-sonnet-4-6"):
    """Helper to call Claude API"""
    try:
        message = client.messages.create(
            model=model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return ""

def _find_project_image(project: dict) -> str:
    """
    Return the best available image path for a project (relative to repo root).
    Priority: Gemini abstract background → static card → empty string.
    """
    project_id = project.get('id', '')
    gemini_path = os.path.join('assets', f"bg_{project_id}.png")
    if os.path.exists(gemini_path):
        return gemini_path
    card_path = project.get('img_path', '')
    if card_path and os.path.exists(card_path):
        return card_path
    return ''


def generate_full_post(projects):
    """Generate post by assembling sections"""
    client = get_client()
    if not client: return None

    project_summaries = "\n".join([f"- {p['name']}: {p.get('script_text', '')[:100]}..." for p in projects])
    n_projects = len(projects)

    full_content = []

    PROMO_LINKS = (
        "Featured Newsletters & Resources\n\n"
        "* [Subscribe to my Medium](https://chesterbeard.medium.com/subscribe)\n"
        "* [FinOps Weekly](https://newsletter.finopsweekly.com/subscribe?ref=UkXVFz6Kl3)\n"
        "* [The Multiverse School](https://themultiverseschool.substack.com?r=ykyfl)\n"
        "* [Earth Conscious Life](https://earthconsciouslife.org/subscribe?ref=24gXUoAEbr)\n"
        "* [My MCP Shelf Directory](https://www.mymcpshelf.com/)\n"
        "* [Pikapods with AWS Hosting Tutorial](https://www.salishseaconsulting.com/blog/pikapods/)\n"
        "* [Firecrawl MCP Server](https://www.salishseaconsulting.com/blog/firecrawl-mcp-server/)\n"
    )

    # 1. Introduction
    print(f"🖋️  Generating Introduction for {n_projects} projects...")
    intro = call_claude(client, INTRO_PROMPT.format(
        n_projects=n_projects,
        project_summaries=project_summaries,
        cliche_filter=CLICHE_FILTER,
        promo_links=PROMO_LINKS
    ))
    full_content.append(f"{n_projects} Open-Source Projects for Your Dev Stack\n")
    full_content.append(intro)
    full_content.append("\n---\n")

    # 2. Project Sections — insert up to 3 images spread evenly across the post
    n = len(projects)
    image_slots = set()
    if n >= 1: image_slots.add(0)           # first project
    if n >= 3: image_slots.add(n // 2)      # middle project
    if n >= 2: image_slots.add(n - 1)       # last project
    image_slots = sorted(image_slots)[:3]   # cap at 3, ascending order

    images_used = 0
    for i, project in enumerate(projects):
        print(f"📦 [{i+1}/{n_projects}] Generating section for: {project['name']}...")
        section = call_claude(client, PROJECT_SECTION_PROMPT.format(
            name=project['name'],
            url=project['github_url'],
            description=project.get('script_text', project.get('description', '')),
            cliche_filter=CLICHE_FILTER
        ))
        full_content.append(section)

        # Insert image for designated slots — path relative to repo root
        # Medium users: upload this file when you see the placeholder
        if i in image_slots and images_used < 3:
            img_path = _find_project_image(project)
            if img_path:
                # ../../ makes the path resolvable from deliveries/MM-DD/
                full_content.append(f"\n![{project['name']}](../../{img_path})\n")
                images_used += 1

        full_content.append("\n---\n")

    # 3. Conclusion
    print("🏁 Generating Patterns & Conclusion...")
    outro = call_claude(client, OUTRO_PROMPT.format(project_names=project_summaries, cliche_filter=CLICHE_FILTER))
    full_content.append(outro)

    # 4. Consistency pass — smooth register differences across sections
    print("✏️  Running consistency pass...")
    raw_text = "\n".join(full_content)
    smoothed = call_claude(client, CONSISTENCY_PASS_PROMPT.format(content=raw_text))
    if smoothed:
        raw_text = smoothed

    # 5. Final Cleanup: Remove any lingering bare hashtags or asterisks
    # Note: image markdown ![alt](path) is intentionally preserved
    clean_text = raw_text.replace('#', '').replace('*', '')

    return clean_text

def save_post(content):
    """Save Medium post to delivery folder"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = os.path.join("deliveries", current_date)
    os.makedirs(delivery_folder, exist_ok=True)
    
    output_path = os.path.join(delivery_folder, 'MEDIUM_POST.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Saved to {output_path}")
    return output_path

def main():
    projects = load_projects()
    if not projects:
        print("❌ No projects found to process")
        return
    
    print(f"🚀 Starting Medium post generation for {len(projects)} projects...")
    content = generate_full_post(projects)
    
    if content:
        save_post(content)
        # Show a snippet
        print("\n" + "="*30 + " PREVIEW " + "="*30)
        print(content[:500] + "...")
        print("="*69)

if __name__ == "__main__":
    main()
