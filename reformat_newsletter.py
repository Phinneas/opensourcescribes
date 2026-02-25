"""
reformat_newsletter.py
Standalone post-processing script for Substack newsletters.
Re-formats the technical content into a highly structured Substack-friendly layout using Mistral.
"""

import json
import os
import datetime
from pathlib import Path
try:
    from mistralai import Mistral
except ImportError:
    print("⚠️  mistralai SDK not found. Install with: pip install mistralai")
    Mistral = None

# --- CONFIG & CONSTANTS ---
SYSTEM_PROMPT = """You are a Substack post formatter. Reformat the newsletter provided below. 
Keep ALL original content and ALL original URLs — do not invent or remove anything.
Apply this exact structure:

1. TITLE: "Open-Source Tool Roundup: [short theme phrase derived from the content]"
2. INTRO: 2 sentences summarizing the edition's theme
3. HEADER: "Featured Projects"
4. For each project, use this format:
      N. [Project Name]: [Short Descriptor]
      TL;DR: [one sentence]
      Why it matters: [2-3 sentences — this replaces "Technical Utility"]
      Stack: [comma-separated values, same line]
      🔗 GitHub  (or 🔗 Website if not a GitHub link)
5. SECTION: "Implementation Pick: [Name]" — 1-2 sentences
6. SECTION: "Closing Thoughts" — 1-2 sentences of practical advice
7. CLOSING LINE: "Which tool excites you most? Let us know in the comments!"

STRICT RULES:
- No --- dividers between projects
- No markdown # headers or ** asterisks
- Do NOT write out the full URL as text — the link emoji 🔗 + platform word is sufficient (e.g. [🔗 GitHub](URL))
- Replace all "Technical Utility:" labels with "Why it matters:"
- Replace all "View on GitHub:" with 🔗 GitHub
- Do NOT use: Robust, Supercharge, Game changer, Revolutionary, Dive in, Unlock, Gems
- Output must be plain text suitable for pasting directly into Substack
"""

def get_mistral_client():
    """Reads config.json, returns a Mistral client. Supports optional Cloudflare gateway."""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('mistral', {}).get('api_key')
        gateway_url = config.get('mistral', {}).get('cloudflare_gateway_url')
    except Exception:
        api_key = os.environ.get('MISTRAL_API_KEY')
        gateway_url = os.environ.get('MISTRAL_GATEWAY_URL')
    
    if not api_key or api_key == "YOUR_MISTRAL_API_KEY":
        print("❌ Mistral API key not found or still set to placeholder")
        return None
    
    if Mistral is None:
        return None

    # If gateway_url is not provided or empty, Mistral client uses default server_url
    if gateway_url:
        return Mistral(api_key=api_key, server_url=gateway_url)
    else:
        return Mistral(api_key=api_key)

def find_latest_newsletter():
    """Resolves deliveries/{date}/SUBSTACK_NEWSLETTER.md (using .md per recent update)"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = Path("deliveries") / current_date
    
    # Try .md first, then .txt for backward compatibility
    paths = [
        delivery_folder / "SUBSTACK_NEWSLETTER.md",
        delivery_folder / "SUBSTACK_NEWSLETTER.txt"
    ]
    
    for path in paths:
        if path.exists():
            return path
    
    return None

def reformat_with_mistral(client, raw_content):
    """Sends the raw content to Mistral with the system prompt"""
    print("🤖 Reformatting newsletter with Mistral...")
    try:
        response = client.chat.complete(
            model="mistral-medium-latest",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": f"Reformat this newsletter:\n\n{raw_content}"}
            ],
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Mistral API Error: {e}")
        return None

def save_reformatted(content, source_path):
    """Writes to deliveries/{date}/SUBSTACK_NEWSLETTER_REFORMATTED.txt"""
    output_path = source_path.parent / "SUBSTACK_NEWSLETTER_REFORMATTED.txt"
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Saved reformatted newsletter to: {output_path}")
    return output_path

def main():
    source_file = find_latest_newsletter()
    if not source_file:
        print("❌ Could not find SUBSTACK_NEWSLETTER file in today's delivery folder")
        return

    print(f"📖 Found source newsletter: {source_file}")
    
    with open(source_file, 'r', encoding='utf-8') as f:
        raw_content = f.read()

    client = get_mistral_client()
    if not client:
        print("❌ Failed to initialize Mistral client. Check config.json.")
        return

    reformatted = reformat_with_mistral(client, raw_content)
    if reformatted:
        save_reformatted(reformatted, source_file)

if __name__ == "__main__":
    main()
