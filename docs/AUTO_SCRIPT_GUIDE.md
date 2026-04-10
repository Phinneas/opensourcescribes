# Auto-Script Generation Guide

## Overview

The auto-script generator automatically creates **2-4 minute narration scripts** from GitHub repository URLs. No manual script writing required!

## Quick Start

### 1. Create a URL List

Create a text file with GitHub URLs (one per line):

```
https://github.com/owner/repo1
https://github.com/owner/repo2
https://github.com/owner/repo3
```

Save as `github_urls.txt` or any filename.

### 2. Generate Scripts

```bash
python3 simple_parser.py github_urls.txt
```

The tool will:
- ✅ Fetch repository data from GitHub API
- ✅ Download and parse README files
- ✅ Generate 300-600 word scripts (2-4 minutes)
- ✅ Create `posts_data.json` ready for video generation

### 3. Create Video

```bash
python3 video_maker.py
```

## How It Works

### Data Collection

For each GitHub URL, the system fetches:
- Repository name, description, stars, forks
- Primary programming language
- Topics/tags
- README content (first 3000 characters)

### Script Generation

**Two modes available:**

#### AI Mode (Recommended)
- Uses Claude AI for natural, engaging scripts
- Requires `ANTHROPIC_API_KEY` environment variable
- Produces high-quality, varied narration

**Setup AI mode:**
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
pip3 install anthropic
```

#### Template Mode (Fallback)
- Automatic fallback if AI unavailable
- Uses structured template with repo data
- Produces consistent, informative scripts
- No API key required

### Script Structure

Generated scripts include:
1. **Introduction** - What the project is
2. **Detailed Description** - From README content
3. **Key Features** - Based on topics and capabilities
4. **Technical Details** - Language, community stats
5. **Use Cases** - Practical applications
6. **Why It Matters** - Value proposition
7. **Getting Started** - How to use it
8. **Conclusion** - Call to action

### Script Length

- **Target**: 300-600 words (2-4 minutes spoken)
- **Actual**: Typically 310-400 words
- **Speaking rate**: ~150 words per minute

## Usage Examples

### Example 1: Simple URL List

**File: `my_projects.txt`**
```
https://github.com/oraios/Serena
https://github.com/coder/httpjail
https://github.com/Project-HAMi/HAMi
```

**Command:**
```bash
python3 simple_parser.py my_projects.txt
```

### Example 2: Auto-Detection

If your `medium_input.txt` contains only URLs, auto-script mode activates automatically:

```bash
python3 simple_parser.py medium_input.txt
```

### Example 3: Force Auto-Script Mode

```bash
python3 simple_parser.py --auto-script your_file.txt
```

### Example 4: Test Single URL

```bash
python3 auto_script_generator.py --test
```

## Manual Script Editing

After generation, you can edit `posts_data.json` to:
- Refine script text
- Adjust project names
- Modify descriptions

## Traditional Format Still Works

You can still use the manual format:

```
---
owner/repo
Your custom script text here.
Can be multiple lines.
---
```

The parser auto-detects which format you're using.

## Tips for Best Results

### 1. Choose Popular Projects
Projects with more stars get richer scripts with community stats.

### 2. Well-Documented READMEs
Projects with clear READMEs produce better scripts.

### 3. Use AI Mode
Set `ANTHROPIC_API_KEY` for highest quality narration.

### 4. Review Generated Scripts
Check `posts_data.json` before video generation.

### 5. Batch Processing
Process 5-10 projects at once for efficiency.

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
- **Normal**: System falls back to template mode
- **Fix**: Set API key for AI-generated scripts

### "Repository not found"
- Check URL is correct
- Ensure repository is public
- Verify GitHub is accessible

### "README not found"
- Script still generates using repo description
- Quality may be lower without README

### Scripts Too Short
- Template mode ensures minimum 300 words
- Add more projects with detailed READMEs

### Scripts Too Long
- Rare, but scripts are capped at ~600 words
- AI mode respects word count limits

## File Reference

### Input Files
- `github_urls.txt` - URL list (one per line)
- `medium_input.txt` - Traditional or URL format

### Output Files
- `posts_data.json` - Generated project data + scripts

### Scripts
- `auto_script_generator.py` - Core generation logic
- `simple_parser.py` - Parser with auto-detection

## Advanced Usage

### Custom Script Generation

Import and use programmatically:

```python
from auto_script_generator import generate_script

result = generate_script("https://github.com/owner/repo")
print(result['script_text'])
print(f"Word count: {result['metadata']['word_count']}")
```

### Batch Processing

```python
from auto_script_generator import generate_from_url_list

projects = generate_from_url_list("my_urls.txt")
for project in projects:
    print(f"{project['name']}: {len(project['script_text'].split())} words")
```

## Next Steps

After generating scripts:
1. Review `posts_data.json`
2. Run `python3 video_maker.py`
3. Upload `final_github_roundup.mp4` to YouTube

## Example Output

**Input URL:**
```
https://github.com/oraios/Serena
```

**Generated Script (335 words):**
> serena is a Python-based project that provides a powerful coding agent toolkit with semantic retrieval and editing capabilities. Serena is a powerful coding agent toolkit capable of turning an LLM into a fully-featured agent that works directly on your codebase...
> 
> [Full script in posts_data.json]

**Video Segment:** ~2.2 minutes
