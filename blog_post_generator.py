"""
Blog Post Generator for Multiple Platforms
Generates Medium, Substack, and Reddit posts from posts_data.json using Claude API
"""

import os
import json
import datetime
import argparse
from pathlib import Path


def load_prompt(platform: str) -> str:
    """
    Load the writing prompt for a specific platform.

    Args:
        platform: One of 'medium', 'substack', 'reddit'

    Returns:
        The prompt text
    """
    prompt_map = {
        'medium': 'MEDIUM_POST_PROMPT.md',
        'substack': 'SUBSTACK_POST_PROMPT.md',
        'reddit': 'REDDIT_POST_PROMPT.md'
    }

    if platform not in prompt_map:
        raise ValueError(f"Unknown platform: {platform}. Choose from: {list(prompt_map.keys())}")

    prompt_path = Path(__file__).parent / 'prompts' / prompt_map[platform]

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    with open(prompt_path, 'r') as f:
        return f.read()


def load_projects(data_file: str = 'posts_data.json') -> list:
    """
    Load projects from JSON file.

    Args:
        data_file: Path to the posts_data.json file

    Returns:
        List of project dictionaries
    """
    if not os.path.exists(data_file):
        raise FileNotFoundError(f"Data file not found: {data_file}")

    with open(data_file, 'r') as f:
        return json.load(f)


def generate_blog_post(platform: str, projects: list) -> str:
    """
    Generate a blog post using Claude API.

    Args:
        platform: Target platform (medium, substack, reddit)
        projects: List of project dictionaries

    Returns:
        Generated blog post text
    """
    try:
        import anthropic
    except ImportError:
        print("❌ anthropic package not installed. Run: pip install anthropic")
        return None

    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set")
        return None

    # Load the platform-specific prompt
    prompt_template = load_prompt(platform)

    # Prepare project data as JSON
    projects_json = json.dumps(projects, indent=2)

    # Combine prompt with project data
    full_prompt = f"""{prompt_template}

## PROJECT DATA

```json
{projects_json}
```

Generate the {platform.title()} post now.
"""

    print(f"🤖 Generating {platform.title()} post with Claude...")
    print(f"   Processing {len(projects)} projects...")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {"role": "user", "content": full_prompt}
        ]
    )

    post_content = message.content[0].text.strip()
    word_count = len(post_content.split())

    print(f"✅ Generated {word_count} words")

    return post_content


def save_post(content: str, platform: str, output_dir: str = None) -> str:
    """
    Save the generated post to a file.

    Args:
        content: The blog post content
        platform: Target platform name
        output_dir: Optional output directory

    Returns:
        Path to the saved file
    """
    # Default to deliveries/MM-DD folder
    if output_dir is None:
        current_date = datetime.datetime.now().strftime("%m-%d")
        output_dir = os.path.join("deliveries", current_date)

    os.makedirs(output_dir, exist_ok=True)

    filename = f"{platform.upper()}_POST.md"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w') as f:
        f.write(content)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='Generate blog posts for Medium, Substack, or Reddit from posts_data.json'
    )
    parser.add_argument(
        'platform',
        choices=['medium', 'substack', 'reddit', 'all'],
        help='Target platform for the blog post'
    )
    parser.add_argument(
        '--input', '-i',
        default='posts_data.json',
        help='Input JSON file with project data (default: posts_data.json)'
    )
    parser.add_argument(
        '--output', '-o',
        default=None,
        help='Output directory (default: deliveries/MM-DD/)'
    )
    parser.add_argument(
        '--print', '-p',
        action='store_true',
        help='Print the generated post to stdout'
    )

    args = parser.parse_args()

    # Load projects
    try:
        projects = load_projects(args.input)
        print(f"📖 Loaded {len(projects)} projects from {args.input}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return 1

    if not projects:
        print("❌ No projects found in data file")
        return 1

    # Determine which platforms to generate for
    platforms = ['medium', 'substack', 'reddit'] if args.platform == 'all' else [args.platform]

    for platform in platforms:
        print(f"\n{'='*60}")
        print(f"Generating {platform.upper()} post")
        print('='*60)

        try:
            content = generate_blog_post(platform, projects)

            if content:
                filepath = save_post(content, platform, args.output)
                print(f"💾 Saved to: {filepath}")

                if args.print:
                    print(f"\n{'-'*60}")
                    print(content)
                    print(f"{'-'*60}\n")
            else:
                print(f"❌ Failed to generate {platform} post")

        except Exception as e:
            print(f"❌ Error generating {platform} post: {e}")

    print("\n✅ Done!")
    return 0


if __name__ == "__main__":
    exit(main())
