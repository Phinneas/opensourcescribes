"""
Generate Substack/Newsletter post from project data using Claude API
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
- ROI Focus: Explain how much time or effort this tool saves.
- Direct Technical Analysis: Avoid marketing hype.
- SHORT sentences (max 15 words). 
"""

EDITORIAL_PROMPT = """You are the lead editor for the OpenSourceScribes Newsletter. 
Write a technical editorial for "The Scribe's Digest: {n_projects} Open Source Discoveries".

{cliche_filter}

## PROJECTS IN THIS EDITION (STRICTLY USE THESE):
{project_summaries}

Write ONLY the editorial (150-200 words). NO headers or special formatting symbols. Do not use '#' or '*'.
"""

PROJECT_SECTION_PROMPT = """You are the lead editor for OpenSourceScribes.
Write a technical curation section for this project.

{cliche_filter}

## PROJECT DATA
Name: {name}
GitHub: {url}
Description: {description}

## FORMATTING RULES
1. Title: Project: {name}
2. The TL;DR: (One-sentence technical summary)
3. Technical Utility: (2-3 sentences of analysis)
4. Stack: (Primary Language/Tech)
5. Link: View on GitHub: {url}
6. NO hashtags, headers, or asterisks (no #, **, or *). Use plain text only.

Write ONLY this section.
"""

OUTRO_PROMPT = """You are the lead editor for OpenSourceScribes. 
Write the technical closing sections.

{cliche_filter}

## TASK
1. Implementation Pick: Highlight ONE tool from this list as the most practical for production: {project_names}.
2. Closing: 1-2 sentences of practical advice.
3. NO hashtags, headers, or asterisks formatting. Do not use '#' or '*'.

Write ONLY this ending part."""

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
    data_file = 'posts_data.json'
    if not os.path.exists(data_file):
        data_file = 'posts_data_longform.json'
    if not os.path.exists(data_file):
        return None
    with open(data_file, 'r') as f:
        return json.load(f)

def call_claude(client, prompt, model="claude-3-haiku-20240307"):
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

def generate_full_newsletter(projects):
    """Generate newsletter by assembling sections"""
    client = get_client()
    if not client: return None
    
    project_summaries = "\n".join([f"- {p['name']}: {p.get('script_text', '')[:100]}..." for p in projects])
    n_projects = len(projects)
    
    full_content = []
    
    # Title
    full_content.append(f"# The Scribe's Digest: {n_projects} Open Source Discoveries to Supercharge Your Week\n")
    
    # 1. Editorial
    print(f"🖋️  Generating Newsletter Editorial...")
    editorial = call_claude(client, EDITORIAL_PROMPT.format(
        n_projects=n_projects, 
        project_summaries=project_summaries, 
        cliche_filter=CLICHE_FILTER
    ))
    full_content.append(editorial)
    full_content.append("\n---\n")
    
    # 2. Project Sections
    for i, project in enumerate(projects):
        print(f"📦 [{i+1}/{n_projects}] Generating newsletter section for: {project['name']}...")
        section = call_claude(client, PROJECT_SECTION_PROMPT.format(
            name=project['name'],
            url=project['github_url'],
            description=project.get('script_text', project.get('description', '')),
            cliche_filter=CLICHE_FILTER
        ))
        full_content.append(section)
        full_content.append("\n---\n")
        
    # 3. Outro
    print("🏁 Generating Newsletter Outro...")
    outro = call_claude(client, OUTRO_PROMPT.format(project_names=project_summaries, cliche_filter=CLICHE_FILTER))
    full_content.append(outro)
    
    # 4. Final Cleanup: Remove any lingering hashtags or asterisks
    raw_text = "\n".join(full_content)
    clean_text = raw_text.replace('#', '').replace('*', '')
    
    return clean_text

def save_post(content):
    """Save Newsletter to delivery folder"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = os.path.join("deliveries", current_date)
    os.makedirs(delivery_folder, exist_ok=True)
    
    output_path = os.path.join(delivery_folder, 'SUBSTACK_NEWSLETTER.txt')
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Saved to {output_path}")
    return output_path

def main():
    projects = load_projects()
    if not projects:
        print("❌ No projects found to process")
        return
    
    print(f"🚀 Starting Newsletter generation for {len(projects)} projects...")
    content = generate_full_newsletter(projects)
    
    if content:
        save_post(content)

if __name__ == "__main__":
    main()
