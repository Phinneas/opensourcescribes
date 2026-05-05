"""
Generate Substack newsletter from project data using Claude API.
Outputs clean, Substack-native plain text — paste directly, no reformatting needed.
"""

import json
import os
import datetime
import anthropic

# --- PROMPT TEMPLATES ---

CLICHE_FILTER = """
BANNED WORDS (do not use any of these): Robust, Gems, Hidden Gems, Supercharge, Dive in, Game changer, Revolutionary, Look no further, Unlock the potential, Elevate your workflow, Buckle up, Pique your interest, Treasure trove, Innovative, Cutting-edge, State of the art, Seamlessly integrate, Tired of X? Meet Y, Workflow.

WRITING STYLE:
- Direct Technical Analysis. No marketing hype.
- Short sentences (max 15 words each).
- ROI focus: explain time or effort this saves.
- DO NOT use any markdown: no #, *, **, ---, or backticks.
"""

EDITORIAL_PROMPT = """You are the lead editor for OpenSourceScribes, a developer-focused newsletter.
Write an opening editorial for this edition: "The Scribe's Digest: {n_projects} Open Source Discoveries."

{cliche_filter}

Projects in this edition:
{project_summaries}

RULES:
- 150-200 words maximum.
- Plain text only. No markdown, no bullet points, no dashes, no symbols.
- Opinionated and direct. One concrete observation beats a general one.
- Do NOT write a thesis about open source. Get straight to what's interesting about this specific batch.
- End with a single punchy line that sets up the project sections.
"""

PROJECT_SECTION_PROMPT = """You are the lead editor for OpenSourceScribes.
Write a project spotlight section for this GitHub project.

{cliche_filter}

Project details:
Name: {name}
GitHub: {url}
Description: {description}

OUTPUT FORMAT (use exactly this layout, plain text):
{name}
TL;DR: [one sentence technical summary]
Why it matters: [2-3 sentences of direct technical analysis — specific problem it solves, what makes it worth using]
Stack: [primary language/tech stack, comma-separated]
GitHub: {url}

RULES:
- Use the exact field labels above.
- No markdown, no asterisks, no dashes, no bullet points.
- Do not add headers or section titles beyond the project name on the first line.
- Write ONLY this section, nothing else.
"""

OUTRO_PROMPT = """You are the lead editor for OpenSourceScribes.
Write the closing section for this newsletter edition.

{cliche_filter}

Projects covered this edition:
{project_names}

OUTPUT FORMAT (plain text, no markdown):
Write two paragraphs:
1. "Implementation Pick:" — Name ONE tool from the list as the most practical for immediate production use. Give 2-3 specific reasons why.
2. "Closing Thoughts:" — 1-2 sentences of concrete, practical advice for the reader.

Then end with exactly this line:
Which tool are you trying first? Let us know in the comments.

RULES:
- No markdown, no asterisks, no dashes, no headers.
- Write ONLY these two paragraphs and the closing line.
"""

PROMO_LINKS = """\
---

Featured Newsletters and Resources

FinOps Weekly — https://newsletter.finopsweekly.com/subscribe?ref=UkXVFz6Kl3
The Multiverse School — https://themultiverseschool.substack.com?r=ykyfl
Earth Conscious Life — https://earthconsciouslife.org/subscribe?ref=24gXUoAEbr
My MCP Shelf Directory — https://www.mymcpshelf.com/
Pikapods with AWS Hosting Tutorial — https://www.salishseaconsulting.com/blog/pikapods/
Firecrawl MCP Server — https://www.salishseaconsulting.com/blog/firecrawl-mcp-server/

---\
"""

# --- FUNCTIONS ---

def get_client():
    """Initialize Anthropic client from env or config.json."""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            api_key = config.get('anthropic', {}).get('api_key')
        except Exception:
            pass
    if not api_key:
        print("❌ Anthropic API key not found")
        return None
    return anthropic.Anthropic(api_key=api_key)

def load_projects():
    """Load project data from JSON."""
    for data_file in ['posts_data.json', 'posts_data_longform.json']:
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                return json.load(f)
    return None

def call_claude(client, prompt, model="claude-sonnet-4-6"):
    """Call Claude API and return text response."""
    try:
        message = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️  API Error: {e}")
        return ""

def generate_full_newsletter(projects):
    """Assemble the full newsletter as Substack-ready plain text."""
    client = get_client()
    if not client:
        return None

    n_projects = len(projects)
    project_summaries = "\n".join(
        [f"- {p['name']}: {p.get('script_text', p.get('description', ''))[:100]}..." for p in projects]
    )
    project_names = ", ".join([p['name'] for p in projects])

    sections = []

    # Title — plain text, no markdown header
    sections.append(f"The Scribe's Digest: {n_projects} Open Source Discoveries\n")

    # 1. Editorial
    print("🖋️  Generating editorial...")
    editorial = call_claude(client, EDITORIAL_PROMPT.format(
        n_projects=n_projects,
        project_summaries=project_summaries,
        cliche_filter=CLICHE_FILTER
    ))
    sections.append(editorial)

    # 2. Promo links block (plain text, copy-paste friendly)
    sections.append(f"\n{PROMO_LINKS}\n")

    # 3. Project sections
    for i, project in enumerate(projects):
        print(f"📦  [{i+1}/{n_projects}] {project['name']}...")
        section = call_claude(client, PROJECT_SECTION_PROMPT.format(
            name=project['name'],
            url=project['github_url'],
            description=project.get('script_text', project.get('description', '')),
            cliche_filter=CLICHE_FILTER
        ))
        sections.append(section)
        sections.append("")  # blank line between projects

    # 4. Outro
    print("🏁  Generating outro...")
    outro = call_claude(client, OUTRO_PROMPT.format(
        project_names=project_names,
        cliche_filter=CLICHE_FILTER
    ))
    sections.append(outro)

    full_text = "\n\n".join(sections).strip()

    if len(full_text.split('\n')) < 5:
        print("⚠️  Warning: Newsletter seems too short — check API responses")

    return full_text

def save_post(content):
    """Save newsletter as a plain .txt file ready for Substack copy-paste."""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = os.path.join("deliveries", current_date)
    os.makedirs(delivery_folder, exist_ok=True)

    output_path = os.path.join(delivery_folder, 'SUBSTACK_NEWSLETTER.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅  Saved to {output_path}")
    return output_path

def main():
    projects = load_projects()
    if not projects:
        print("❌ No projects found in posts_data.json")
        return

    print(f"🚀  Generating newsletter for {len(projects)} projects...")
    content = generate_full_newsletter(projects)

    if content:
        save_post(content)

if __name__ == "__main__":
    main()
