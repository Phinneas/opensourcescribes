"""
Generate Medium blog post from project data using Claude API
"""

import json
import os
import datetime
import anthropic

MEDIUM_PROMPT = """You are a technical writer for OpenSourceScribes. You write engaging Medium posts about trending GitHub projects.

## INPUT FORMAT

JSON array of projects:
[
  {
    "id": "owner_repo",
    "name": "repo-name", 
    "github_url": "https://github.com/owner/repo",
    "script_text": "Brief description..."
  }
]

## YOUR TASK

Write a Medium post titled "This Week's GitHub Gems: [N] Open-Source Projects You Should Know About"

## WRITING STYLE

- Enthusiastic but professional
- 1500-2500 words total
- First person plural ("we found", "we love")
- **CRITICAL: Keep sentences SHORT. Max 15-20 words per sentence. No run-ons.**
- Vary sentence length for rhythm
- One idea per sentence

## POST STRUCTURE

### 1. INTRODUCTION (100-150 words)
- Hook the reader
- Preview the types of projects featured
- Promise value

### 2. PROJECT SECTIONS

For EACH project, follow this format:

**Subheading**: Project name + catchy tagline
Example: "### Claude-Mem: Persistent Memory for Your AI Assistant"

**Introduction**: Write 4-5 SHORT sentences:
- Sentence 1: Why this matters (max 15 words)
- Sentence 2: What it does (max 20 words)
- Sentence 3: How it works (max 20 words)
- Sentence 4: Who built it / ecosystem (max 15 words)
- Sentence 5 (optional): The problem it solves (max 15 words)

**Bullet Points**: Exactly 3 bullets after the intro:
- Key feature (one line)
- Technical detail (one line)
- Use case or benefit (one line)

**Link**: GitHub URL at the end

### 3. PATTERNS & THEMES (100-150 words)
- What trends appear across projects?
- Where is development heading?

### 4. CONCLUSION (75-100 words)
- Summarize value
- Call to action
- Tease next week

## FORMATTING

- Use ## for sections, ### for projects
- Use - for bullets (not *)
- Links as plain text: [Project Name](url)
- 1-2 emojis per section max
- NO asterisks for bold or emphasis. Write plain text only.
- Do not use ** or * for any formatting

## TAGS
Include 5 Medium tags at bottom

## EXAMPLE PROJECT SECTION

### Claude-Mem: Persistent Memory for Your AI Assistant 🧠

Tired of Claude forgetting your last session? Claude-Mem fixes that. It gives your AI assistant a persistent memory across coding sessions. The TypeScript plugin captures context and compresses it automatically. It's built on Anthropic's official Agent SDK. No more re-explaining your codebase every time.

- Automatic capture — Records everything Claude does in the background
- Smart compression — Distills sessions into relevant context without bloat  
- Seamless injection — Context appears automatically in future sessions

[Check out Claude-Mem on GitHub](https://github.com/thedotmack/claude-mem)

---

## CRITICAL RULES

1. Every project gets 4-5 SHORT sentences (max 20 words each)
2. Every project gets exactly 3 bullet points
3. NO run-on sentences
4. NO sentences over 25 words
5. Do not skip or combine projects
6. NO asterisks anywhere. No ** or * for formatting.

Write the complete post now."""


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
