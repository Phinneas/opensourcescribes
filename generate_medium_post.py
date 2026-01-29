"""
Generate Medium blog post from project data using Claude API
"""

import json
import os
import datetime
import anthropic

MEDIUM_PROMPT = """You are a technical writer for OpenSourceScribes, writing engaging Medium posts about trending open-source GitHub projects. Your posts help developers discover useful tools and libraries.

## INPUT FORMAT

You will receive a JSON array of GitHub projects with this structure:
[
  {
    "id": "owner_repo",
    "name": "repo-name",
    "github_url": "https://github.com/owner/repo",
    "script_text": "Brief description of the project..."
  }
]

## YOUR TASK

Write a Medium blog post titled "This Week's GitHub Gems: [N] Open-Source Projects You Should Know About" where N is the number of projects.

## WRITING STYLE

- **Tone**: Enthusiastic but professional. You're a developer excited to share discoveries
- **Length**: 1500-2500 words total
- **Reading level**: Accessible to intermediate developers
- **Voice**: First person plural ("we found", "we love")

## POST STRUCTURE

### 1. INTRODUCTION (100-150 words)
- Hook: Start with a compelling statement about this week's discoveries
- Context: Briefly mention what kinds of projects you're featuring
- Promise: What value will readers get from this post

### 2. PROJECT SECTIONS

For EACH project, you MUST follow this exact format:

**Subheading**: Use the project name + a catchy tagline
Example: "## Claude-Mem: Never Lose Your AI Coding Context Again"

**Introduction Paragraph**: Write exactly 4-5 sentences that:
- Sentence 1: Hook the reader with why this project matters
- Sentence 2: Explain what the project does at a high level
- Sentence 3: Describe the core technology or approach
- Sentence 4: Mention who built it or the ecosystem it belongs to
- Sentence 5 (optional): Add context about the problem it solves

**Bullet Point List**: Immediately after the introduction, include exactly 3 bullet points that further explain the project:
- Bullet 1: A key feature or capability
- Bullet 2: A technical detail or integration worth noting
- Bullet 3: A use case or benefit for developers

**Link**: End with the GitHub URL prominently displayed

### 3. PATTERNS & THEMES (100-150 words)
- What trends do you notice across these projects?
- What does this tell us about where development is heading?

### 4. CONCLUSION (75-100 words)
- Summarize the value of these discoveries
- Call to action: Star repos, try them out, share the post
- Tease next week's roundup

## FORMATTING REQUIREMENTS

- Use ## for main section headers
- Use ### for project names
- Use bullet points (-, not *) for the 3-point feature lists
- Include GitHub links as: **[Project Name](github_url)**
- Add relevant emojis sparingly (1-2 per section max)
- Break up long paragraphs

## TAGS TO INCLUDE AT BOTTOM
Suggest 5 Medium tags like: Open Source, GitHub, Developer Tools, Programming, Software Development

## EXAMPLE PROJECT SECTION

### Claude-Mem: Never Lose Your AI Coding Context Again 🧠

Ever had Claude forget everything from your last coding session? Claude-Mem solves this frustration elegantly by giving your AI assistant a persistent memory. This TypeScript plugin automatically captures everything Claude does during your coding sessions, compresses it with AI, and injects relevant context back into future sessions. Built on Anthropic's official Agent SDK, it integrates seamlessly into existing Claude Code workflows. If you're tired of re-explaining your codebase every time you start a new session, this is the tool you've been waiting for.

- **Automatic session capture** — No manual notes needed; it records everything Claude does in the background
- **AI-powered compression** — Uses Claude itself to distill sessions into relevant context, keeping memories useful without bloat
- **Seamless injection** — Relevant context automatically appears in future sessions, making Claude feel like it actually remembers you

**[Check out Claude-Mem on GitHub](https://github.com/thedotmack/claude-mem)**

---

## CRITICAL REQUIREMENTS

1. Every project MUST have a 4-5 sentence introduction paragraph
2. Every project MUST have exactly 3 bullet points after the introduction
3. Do not skip or combine projects
4. Do not add extra bullet points or reduce to fewer than 3

## NOW WRITE THE POST

Generate the complete Medium post using the projects provided. Make each project section engaging and informative. Find genuine connections between projects where they exist, but don't force themes that aren't there."""


def load_projects():
    """Load project data from JSON"""
    data_file = 'posts_data_longform.json'
    if not os.path.exists(data_file):
        print(f"ℹ️  {data_file} not found, falling back to posts_data.json")
        data_file = 'posts_data.json'
        
    if not os.path.exists(data_file):
        print(f"❌ {data_file} not found")
        return None

    with open(data_file, 'r') as f:
        projects = json.load(f)
    
    print(f"✅ Loaded {len(projects)} projects from {data_file}")
    return projects


def generate_medium_post(projects):
    """Generate Medium post using Claude API"""
    
    # Load API key from config or environment
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('anthropic', {}).get('api_key')
    
    if not api_key:
        print("❌ Anthropic API key not found in config.json or ANTHROPIC_API_KEY env var")
        return None
    
    client = anthropic.Anthropic(api_key=api_key)
    
    project_json = json.dumps(projects, indent=2)
    
    print("🤖 Generating Medium post with Claude...")
    
    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"{MEDIUM_PROMPT}\n\n## PROJECTS DATA\n\n```json\n{project_json}\n```"
            }
        ]
    )
    
    return message.content[0].text


def save_post(content):
    """Save Medium post to delivery folder"""
    current_date_mmdd = datetime.datetime.now().strftime("%m-%d")
    delivery_folder = os.path.join("deliveries", current_date_mmdd)
    output_path = os.path.join(delivery_folder, 'MEDIUM_POST.md')
    
    os.makedirs(delivery_folder, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"\n✅ Generated {output_path}")
    return output_path


def main():
    """Main execution"""
    projects = load_projects()
    if not projects:
        return
    
    content = generate_medium_post(projects)
    if not content:
        return
    
    output_path = save_post(content)
    
    print("-" * 60)
    print(content[:1000] + "..." if len(content) > 1000 else content)
    print("-" * 60)


if __name__ == "__main__":
    main()
