"""
Generate Reddit post from project data using Claude API
Processes projects individually to ensure none are skipped.
"""

import json
import os
import datetime
import anthropic

# --- PROMPT TEMPLATES ---

CLICHE_FILTER = """
## 🚫 BANNED PHRASES (CRITICAL)
Do NOT use: Robust, Gems, Hidden Gems, Supercharge, Dive in, Game changer, Revolutionary, Look no further, Unlock the potential, Elevate your workflow, Buckle up, Pique your interest, Treasure trove, Innovative, Cutting-edge, State of the art, Seamlessly integrate, Tired of X? Meet Y.

## ✍️ WRITING STYLE
- Engineering Focus: No marketing "hype". Focus on utility and technical implementation.
- Direct & Concise: Bullet points should be technical.
- SHORT sentences (max 15 words). 
"""

INTRO_PROMPT = """You are a community manager for OpenSourceScribes. 
Write a direct, helpful INTRODUCTION for a Reddit post titled "{n_projects} Trending Open-Source Projects ({month_year})".

{cliche_filter}

## PROJECTS IN THIS LIST (STRICTLY USE THESE):
{project_summaries}

Write ONLY the introduction (50-100 words). NO headers or special formatting symbols. Do not use '#' or '*'.
"""

PROJECT_SECTION_PROMPT = """You are a community manager for OpenSourceScribes.
Write a concise technical showcase for this project.

{cliche_filter}

## PROJECT DATA
Name: {name}
GitHub: {url}
Description: {description}

## FORMATTING RULES
1. Format: {name} - [Technical Purpose]
2. Content: 2 SHORT sentences on utility and implementation.
3. Repo: {url}
4. NO labels like "Description:" or "Repo:".
5. NO hashtags, headers, or asterisks (no #, **, or *). Use plain text only.

Write ONLY this snippet.
"""

OUTRO_PROMPT = """You are a community manager for OpenSourceScribes. 
Write a short, direct outro.

{cliche_filter}

## PROJECTS COVERED:
{project_summaries}

## TASK
1. Ask for technical feedback or similar tools.
2. Mention the YouTube channel "OpenSourceScribes" for walkthroughs.
3. NO hashtags, headers, or asterisks formatting. Do not use '#' or '*'.

Write ONLY the outro.
"""

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
    # Prefer posts_data.json as the direct output of the URL parser
    data_file = 'posts_data.json'
    if not os.path.exists(data_file):
        data_file = 'posts_data_longform.json'
        
    if not os.path.exists(data_file):
        return None

    with open(data_file, 'r') as f:
        projects = json.load(f)
    return projects

def call_claude(client, prompt, model="claude-3-haiku-20240307"):
    """Helper to call Claude API"""
    try:
        message = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    except Exception as e:
        print(f"⚠️ API Error: {e}")
        return ""

def generate_full_post(projects):
    """Generate post by assembling sections"""
    client = get_client()
    if not client: return None
    
    project_summaries = "\n".join([f"- {p['name']}: {p.get('script_text', '')[:80]}..." for p in projects])
    n_projects = len(projects)
    month_year = datetime.datetime.now().strftime("%B %Y")
    
    full_content = []
    
    # Header Title
    full_content.append(f"# {n_projects} Trending Open-Source Projects ({month_year})\n")
    
    # 1. Introduction
    print(f"🖋️  Generating Reddit Intro...")
    intro = call_claude(client, INTRO_PROMPT.format(
        n_projects=n_projects, 
        month_year=month_year, 
        project_summaries=project_summaries, 
        cliche_filter=CLICHE_FILTER
    ))
    full_content.append(intro)
    full_content.append("\n")
    
    # 2. Project Sections
    for i, project in enumerate(projects):
        print(f"📦 [{i+1}/{n_projects}] Generating Reddit snippet for: {project['name']}...")
        section = call_claude(client, PROJECT_SECTION_PROMPT.format(
            name=project['name'],
            url=project['github_url'],
            description=project.get('script_text', project.get('description', '')),
            cliche_filter=CLICHE_FILTER
        ))
        full_content.append(section)
        full_content.append("\n")
        
    # 3. Conclusion
    print("🏁 Generating Reddit Outro...")
    outro = call_claude(client, OUTRO_PROMPT.format(project_summaries=project_summaries, cliche_filter=CLICHE_FILTER))
    full_content.append(outro)
    
    # 4. Final Cleanup: Remove any lingering hashtags or asterisks
    raw_text = "\n".join(full_content)
    clean_text = raw_text.replace('#', '').replace('*', '')
    
    return clean_text

def save_post(content):
    """Save Reddit post to delivery folder"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = os.path.join("deliveries", current_date)
    os.makedirs(delivery_folder, exist_ok=True)
    
    output_path = os.path.join(delivery_folder, 'REDDIT_POST.md')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Saved to {output_path}")
    return output_path

def main():
    projects = load_projects()
    if not projects:
        print("❌ No projects found to process")
        return
    
    print(f"🚀 Starting Reddit post generation for {len(projects)} projects...")
    content = generate_full_post(projects)
    
    if content:
        save_post(content)

if __name__ == "__main__":
    main()
