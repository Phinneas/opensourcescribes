"""
Enhanced Medium Post Parser
Converts simple text format to posts_data.json for video generation
"""

import json
import re
import sys

def parse_simple_format(filepath='medium_input.txt'):
    """
    Parse from simple --- separated format:
    
    ---
    owner/repo or Project Name
    Description text here.
    Can be multiple lines.
    ---
    """
    print(f"📖 Reading from: {filepath}")
    
    try:
        with open(filepath, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ File not found: {filepath}")
        print("\n💡 Creating example template...")
        create_example_template()
        return []
    
    # Split by separator
    sections = re.split(r'\n---+\n', content)
    
    projects = []
    
    for i, section in enumerate(sections):
        section = section.strip()
        if not section or section == '---':
            continue
        
        lines = section.split('\n', 1)
        
        if len(lines) < 2:
            print(f"⚠️  Skipping incomplete section {i+1}")
            continue
        
        first_line = lines[0].strip()
        description = lines[1].strip() if len(lines) > 1 else ""
        
        # Try to extract owner/repo from first line
        # Format: "owner/repo" or "Project Name (owner/repo)"
        repo_match = re.search(r'([a-zA-Z0-9_-]+)/([a-zA-Z0-9_.-]+)', first_line)
        
        if repo_match:
            owner, repo = repo_match.groups()
            project_name = repo.replace('-', ' ').replace('_', ' ').title()
            github_url = f"https://github.com/{owner}/{repo}"
        else:
            # No owner/repo found, use first line as name
            project_name = first_line
            github_url = f"https://github.com/OWNER/REPO_{i+1}"
            print(f"⚠️  No GitHub URL found for: {project_name}")
        
        # Clean description - remove any remaining owner/repo references
        clean_description = re.sub(r'\([a-zA-Z0-9_-]+/[a-zA-Z0-9_.-]+\)', '', description).strip()
        
        if not clean_description:
            clean_description = f"{project_name} is an interesting GitHub project."
        
        projects.append({
            "id": f"p{len(projects)+1}",
            "name": project_name,
            "github_url": github_url,
            "script_text": clean_description
        })
    
    return projects

def create_example_template():
    """Create an example template file"""
    template = """---
seraui/seraui
SeraUI is a sleek UI component library built for React and Next.js. It leverages Tailwind CSS to deliver fast and responsive design out of the box.
---
langchain-ai/langchain
LangChain is a framework for developing applications powered by language models. It enables applications that are context-aware and can reason.
---
owner/repo-name
Your project description goes here.
You can write multiple lines.
Just keep it between the --- separators.
---
"""
    
    with open('medium_input_template.txt', 'w') as f:
        f.write(template)
    
    print("✅ Created: medium_input_template.txt")
    print("\n📝 Next steps:")
    print("1. Edit medium_input_template.txt with your Medium post content")
    print("2. Save as medium_input.txt")
    print("3. Run: python simple_parser.py")

def detect_url_only_format(filepath):
    """
    Check if file contains only GitHub URLs (auto-script mode)
    
    Returns:
        True if file contains only URLs, False otherwise
    """
    try:
        with open(filepath, 'r') as f:
            lines = [line.strip() for line in f if line.strip()]
        
        # Check if all non-empty lines are GitHub URLs
        if not lines:
            return False
        
        url_count = sum(1 for line in lines if line.startswith('https://github.com/'))
        
        # If 80%+ are GitHub URLs, treat as URL-only format
        return url_count / len(lines) >= 0.8
        
    except Exception:
        return False


def main():
    import os
    
    # Check for input file
    input_file = 'medium_input.txt'
    auto_script_mode = '--auto-script' in sys.argv
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"❌ {input_file} not found!")
        print("\n📝 Creating template...")
        create_example_template()
        return
    
    # Auto-detect URL-only format or use flag
    if auto_script_mode or detect_url_only_format(input_file):
        print("🤖 Auto-script mode detected!")
        print("📡 Generating scripts from GitHub URLs...\n")
        
        try:
            from auto_script_generator import generate_from_url_list
            projects = generate_from_url_list(input_file)
        except ImportError:
            print("❌ auto_script_generator.py not found!")
            print("Make sure auto_script_generator.py is in the same directory.")
            return
        except Exception as e:
            print(f"❌ Auto-script generation failed: {e}")
            return
    else:
        # Parse the file using traditional format
        projects = parse_simple_format(input_file)
    
    if not projects:
        print("\n❌ No projects found!")
        return
    
    print("\n" + "=" * 60)
    print("EXTRACTED PROJECTS:")
    print("=" * 60)
    
    for project in projects:
        print(f"\n🔹 {project['name']}")
        print(f"   URL: {project['github_url']}")
        print(f"   Script: {project['script_text'][:80]}...")
    
    # Save to JSON
    with open('posts_data.json', 'w') as f:
        json.dump(projects, f, indent=2)
    
    print(f"\n✅ Saved {len(projects)} projects to posts_data.json")
    print("\n🎬 Ready to create video! Run: python video_maker.py")

if __name__ == "__main__":
    main()
