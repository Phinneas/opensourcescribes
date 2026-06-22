# Content Reformat Cost Reduction Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut Sonnet API calls per run from ~52 to ~17 by making Medium and Reddit posts cheap Mistral reformats of the finished newsletter instead of independent full Claude generations.

**Architecture:** `generate_newsletter.py` keeps writing on Sonnet unchanged (plus one caching optimization on its per-project loop). `generate_medium_post.py` and `generate_reddit_post.py` stop calling Claude per-project and instead read the finished newsletter file and make one Mistral call each to restyle it. `core/workflow_manager.py`'s step order changes so Newsletter runs before Medium/Reddit.

**Tech Stack:** Python, `anthropic` SDK, `mistralai` SDK, `unittest` (stdlib, no new dependency).

Spec: `docs/superpowers/specs/2026-06-22-content-reformat-cost-reduction-design.md`

---

## File Structure

- Modify: `content/generate_newsletter.py` — add a cacheable system-prompt call path, used only by the per-project loop.
- Modify: `content/generate_reddit_post.py` — full rewrite: generation → reformat.
- Create: `content/test_generate_reddit_post.py` — unit test for the new `find_missing_urls` helper.
- Modify: `content/generate_medium_post.py` — full rewrite: generation → reformat, plus image insertion as post-processing.
- Create: `content/test_generate_medium_post.py` — unit tests for `find_missing_urls` and `insert_images`.
- Modify: `core/workflow_manager.py` — reorder 3 lines in the `steps` list.

All commands below assume `cd /Users/chesterbeard/Desktop/opensourcescribes` first (the repo root — this is where `posts_data.json` and `deliveries/` live, matching the relative paths already used by `reformat_newsletter.py`).

---

### Task 1: Add prompt caching to `generate_newsletter.py`'s per-project loop

**Files:**
- Modify: `content/generate_newsletter.py`

Only the per-project section loop repeats an identical prompt (n times per run) — the editorial and outro prompts are each called once, where caching would cost more (cache-write premium) than it saves. So only the section loop gets a cacheable `system` block.

- [ ] **Step 1: Replace `PROJECT_SECTION_PROMPT` with a split system/user pair**

In `content/generate_newsletter.py`, replace the existing `PROJECT_SECTION_PROMPT` constant (currently lines 39-61) with:

```python
PROJECT_SECTION_SYSTEM = """You are the lead editor for OpenSourceScribes.
Write a project spotlight section for the GitHub project described in the user message.

{cliche_filter}

OUTPUT FORMAT (use exactly this layout, plain text):
[Project Name]
TL;DR: [one sentence technical summary]
Why it matters: [2-3 sentences of direct technical analysis — specific problem it solves, what makes it worth using]
Stack: [primary language/tech stack, comma-separated]
GitHub: [project URL]

RULES:
- Use the exact field labels above.
- No markdown, no asterisks, no dashes, no bullet points.
- Do not add headers or section titles beyond the project name on the first line.
- Write ONLY this section, nothing else.
""".format(cliche_filter=CLICHE_FILTER)

PROJECT_SECTION_USER = """Project details:
Name: {name}
GitHub: {url}
Description: {description}"""
```

- [ ] **Step 2: Add a caching-aware call helper**

Add this function next to the existing `call_claude` (keep `call_claude` itself unchanged — editorial/outro still use it):

```python
def call_claude_cached_system(client, system_text, user_text, model="claude-sonnet-4-6", max_tokens=4096):
    """Call Claude with a cacheable system prompt. Only worth using when the
    same system_text is sent across multiple calls in one run (e.g. the
    per-project loop) — caching a block read only once costs more than it saves."""
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral"}
                }
            ],
            messages=[{"role": "user", "content": user_text}]
        )
        usage = message.usage
        print(f"   cache: {usage.cache_creation_input_tokens} created, {usage.cache_read_input_tokens} read")
        return message.content[0].text.strip()
    except Exception as e:
        print(f"  ⚠️  API Error: {e}")
        return ""
```

- [ ] **Step 3: Update the per-project loop to use the new helper**

In `generate_full_newsletter`, replace:

```python
        section = call_claude(client, PROJECT_SECTION_PROMPT.format(
            name=project['name'],
            url=project['github_url'],
            description=project.get('script_text', project.get('description', '')),
            cliche_filter=CLICHE_FILTER
        ))
```

with:

```python
        section = call_claude_cached_system(
            client,
            PROJECT_SECTION_SYSTEM,
            PROJECT_SECTION_USER.format(
                name=project['name'],
                url=project['github_url'],
                description=project.get('script_text', project.get('description', ''))
            )
        )
```

- [ ] **Step 4: Verify caching actually engages (real API call, costs a few cents)**

Run:

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes/content && python3 -c "
from generate_newsletter import get_client, call_claude_cached_system, PROJECT_SECTION_SYSTEM, PROJECT_SECTION_USER

client = get_client()
projects = [
    {'name': 'TestProjectA', 'github_url': 'https://github.com/test/a', 'script_text': 'A test CLI tool.'},
    {'name': 'TestProjectB', 'github_url': 'https://github.com/test/b', 'script_text': 'Another test tool.'},
]
for p in projects:
    user_text = PROJECT_SECTION_USER.format(name=p['name'], url=p['github_url'], description=p['script_text'])
    call_claude_cached_system(client, PROJECT_SECTION_SYSTEM, user_text)
"
```

Expected output: two `cache:` lines. The first shows `created` > 0 and `read` 0. The second shows `created` 0 and `read` > 0 — confirming the second call hit the cache written by the first.

- [ ] **Step 5: Commit**

```bash
git add content/generate_newsletter.py
git commit -m "perf: cache shared system prompt in newsletter's per-project loop"
```

---

### Task 2: Rewrite `generate_reddit_post.py` as a newsletter reformatter

**Files:**
- Modify: `content/generate_reddit_post.py`
- Test: `content/test_generate_reddit_post.py`

- [ ] **Step 1: Write the failing test**

Create `content/test_generate_reddit_post.py`:

```python
import unittest
from generate_reddit_post import find_missing_urls


class TestFindMissingUrls(unittest.TestCase):
    def test_all_urls_present(self):
        projects = [
            {"name": "Foo", "github_url": "https://github.com/a/foo"},
            {"name": "Bar", "github_url": "https://github.com/b/bar"},
        ]
        text = "Check out Foo at https://github.com/a/foo and Bar at https://github.com/b/bar"
        self.assertEqual(find_missing_urls(projects, text), [])

    def test_one_url_missing(self):
        projects = [
            {"name": "Foo", "github_url": "https://github.com/a/foo"},
            {"name": "Bar", "github_url": "https://github.com/b/bar"},
        ]
        text = "Check out Foo at https://github.com/a/foo"
        self.assertEqual(find_missing_urls(projects, text), ["Bar"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd /Users/chesterbeard/Desktop/opensourcescribes && python content/test_generate_reddit_post.py -v`
Expected: `ImportError: cannot import name 'find_missing_urls' from 'generate_reddit_post'`

- [ ] **Step 3: Replace the entire file content**

Replace all of `content/generate_reddit_post.py` with:

```python
"""
Generate Reddit post from a finished newsletter using Mistral.
Reformats the newsletter's content into Reddit's voice instead of
generating each project section independently.
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

REDDIT_SYSTEM_PROMPT = """You are a community manager for OpenSourceScribes, reformatting a finished newsletter into a Reddit post.

Keep every project name and every GitHub/website URL from the source newsletter — do not invent, drop, or alter any of them.

## WRITING STYLE
- Casual, direct community tone — like a developer posting to r/programming, not a press release.
- SHORT sentences (max 15 words).
- Keep the structure simple: a short intro, one paragraph per project, a short outro.

## BANNED PHRASES (CRITICAL)
Do NOT use: Robust, Gems, Hidden Gems, Supercharge, Dive in, Game changer, Revolutionary, Look no further, Unlock the potential, Elevate your workflow, Buckle up, Pique your interest, Treasure trove, Innovative, Cutting-edge, State of the art, Seamlessly integrate, Tired of X? Meet Y, Workflow.

## OUTPUT FORMAT
Plain text only. No markdown headers, no asterisks, no hashtags.
End with a line asking readers for technical feedback or similar tool recommendations, and mention the YouTube channel "OpenSourceScribes" for video walkthroughs.
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
    if gateway_url:
        return Mistral(api_key=api_key, server_url=gateway_url)
    return Mistral(api_key=api_key)


def find_latest_newsletter():
    """Resolves deliveries/{date}/SUBSTACK_NEWSLETTER.md or .txt"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = Path("deliveries") / current_date
    for path in [delivery_folder / "SUBSTACK_NEWSLETTER.md", delivery_folder / "SUBSTACK_NEWSLETTER.txt"]:
        if path.exists():
            return path
    return None


def load_projects():
    """Load project data from JSON, used only for the URL safety check below."""
    for data_file in ['posts_data.json', 'posts_data_longform.json']:
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                return json.load(f)
    return None


def find_missing_urls(projects, output_text):
    """Return the names of any projects whose github_url is missing from output_text."""
    return [p['name'] for p in projects if p['github_url'] not in output_text]


def reformat_with_mistral(client, newsletter_text):
    """Sends the finished newsletter to Mistral to restyle as a Reddit post."""
    print("🤖 Reformatting newsletter as Reddit post with Mistral...")
    try:
        response = client.chat.complete(
            model="mistral-medium-latest",
            messages=[
                {"role": "system", "content": REDDIT_SYSTEM_PROMPT},
                {"role": "user", "content": f"Reformat this newsletter as a Reddit post:\n\n{newsletter_text}"}
            ],
            max_tokens=2048,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Mistral API Error: {e}")
        return None


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
    newsletter_path = find_latest_newsletter()
    if not newsletter_path:
        print("❌ Could not find SUBSTACK_NEWSLETTER file in today's delivery folder")
        return

    print(f"📖 Found source newsletter: {newsletter_path}")
    with open(newsletter_path, 'r', encoding='utf-8') as f:
        newsletter_text = f.read()

    client = get_mistral_client()
    if not client:
        print("❌ Failed to initialize Mistral client. Check config.json.")
        return

    content = reformat_with_mistral(client, newsletter_text)
    if not content:
        return

    projects = load_projects()
    if projects:
        missing = find_missing_urls(projects, content)
        if missing:
            print(f"⚠️  Warning: these projects' URLs are missing from the Reddit post: {', '.join(missing)}")

    save_post(content)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd /Users/chesterbeard/Desktop/opensourcescribes && python content/test_generate_reddit_post.py -v`
Expected: `OK` with 2 tests passing.

- [ ] **Step 5: Manual verification against a real newsletter file**

Find the most recent delivery folder and confirm a newsletter file exists there:

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes && ls deliveries/
```

Pick the most recent date folder (e.g. `06-19`), then run:

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes && DELIVERY_DATE=06-19 python content/generate_reddit_post.py
```

Expected: console shows "Found source newsletter", then "Reformatting...", then "Saved to deliveries/06-19/REDDIT_POST.md". Open that file and confirm it reads as a coherent Reddit post and contains the project names/URLs from that day's newsletter.

- [ ] **Step 6: Commit**

```bash
git add content/generate_reddit_post.py content/test_generate_reddit_post.py
git commit -m "refactor: reformat Reddit post from newsletter via Mistral instead of generating per-project on Claude"
```

---

### Task 3: Rewrite `generate_medium_post.py` as a newsletter reformatter

**Files:**
- Modify: `content/generate_medium_post.py`
- Test: `content/test_generate_medium_post.py`

Medium needs two new pure functions beyond Reddit's: the same `find_missing_urls` safety check, and `insert_images` (image placement is currently driven by which project section is being generated; once generation is replaced by a single reformat call, image placement becomes a post-processing step that locates each selected project's name in the rewritten text).

- [ ] **Step 1: Write the failing tests**

Create `content/test_generate_medium_post.py`:

```python
import unittest
from unittest.mock import patch
from generate_medium_post import find_missing_urls, insert_images


class TestFindMissingUrls(unittest.TestCase):
    def test_all_urls_present(self):
        projects = [
            {"name": "Foo", "github_url": "https://github.com/a/foo"},
            {"name": "Bar", "github_url": "https://github.com/b/bar"},
        ]
        text = "Foo: https://github.com/a/foo. Bar: https://github.com/b/bar."
        self.assertEqual(find_missing_urls(projects, text), [])

    def test_one_url_missing(self):
        projects = [
            {"name": "Foo", "github_url": "https://github.com/a/foo"},
            {"name": "Bar", "github_url": "https://github.com/b/bar"},
        ]
        text = "Foo: https://github.com/a/foo."
        self.assertEqual(find_missing_urls(projects, text), ["Bar"])


class TestInsertImages(unittest.TestCase):
    def test_inserts_image_after_matching_paragraph(self):
        text = "Intro paragraph.\n\nFoo is a great tool.\n\nOutro paragraph."
        projects = [{"name": "Foo", "github_url": "https://github.com/a/foo", "id": "foo123"}]
        with patch('generate_medium_post._find_project_image', return_value='assets/bg_foo123.png'):
            result = insert_images(text, projects)
        self.assertIn("![Foo](../../assets/bg_foo123.png)", result)

    def test_skips_image_when_name_not_found(self):
        text = "Intro paragraph.\n\nSomething else entirely.\n\nOutro paragraph."
        projects = [{"name": "Foo", "github_url": "https://github.com/a/foo", "id": "foo123"}]
        with patch('generate_medium_post._find_project_image', return_value='assets/bg_foo123.png'):
            result = insert_images(text, projects)
        self.assertNotIn("![Foo]", result)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd /Users/chesterbeard/Desktop/opensourcescribes && python content/test_generate_medium_post.py -v`
Expected: `ImportError: cannot import name 'find_missing_urls' from 'generate_medium_post'`

- [ ] **Step 3: Replace the entire file content**

Replace all of `content/generate_medium_post.py` with:

```python
"""
Generate Medium post from a finished newsletter using Mistral.
Reformats the newsletter's content into Medium's voice instead of
generating each project section independently.
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

MEDIUM_SYSTEM_PROMPT = """You are restyling a finished developer newsletter into a Medium blog post for OpenSourceScribes.

Keep every project name and every GitHub/website URL from the source newsletter — do not invent, drop, or alter any of them.

## WRITING STYLE
- Editorial blog tone — opinionated, direct, not promotional.
- Vary sentence length, but keep it technical. No narrative fluff, no "Imagine a world where...".
- Banned words: robust, streamline, supercharge, game-changer, revolutionary, seamless, dive in, hidden gems, powerful, cutting-edge, leverage, utilize.

## OUTPUT FORMAT
Plain text only. No '#' or '*' symbols. Structure: a short opening, one paragraph per project, a short closing paragraph with one practical recommendation.
"""

MEDIUM_SUBSCRIBE_LINK = "\n\n---\n\n[Subscribe to my Medium](https://chesterbeard.medium.com/subscribe) for more developer tool roundups.\n"


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
    if gateway_url:
        return Mistral(api_key=api_key, server_url=gateway_url)
    return Mistral(api_key=api_key)


def find_latest_newsletter():
    """Resolves deliveries/{date}/SUBSTACK_NEWSLETTER.md or .txt"""
    current_date = os.environ.get("DELIVERY_DATE", datetime.datetime.now().strftime("%m-%d"))
    delivery_folder = Path("deliveries") / current_date
    for path in [delivery_folder / "SUBSTACK_NEWSLETTER.md", delivery_folder / "SUBSTACK_NEWSLETTER.txt"]:
        if path.exists():
            return path
    return None


def load_projects():
    """Load project data from JSON, used for the URL safety check and image lookups."""
    data_file = 'posts_data.json'
    if not os.path.exists(data_file):
        return None
    with open(data_file, 'r') as f:
        return json.load(f)


def find_missing_urls(projects, output_text):
    """Return the names of any projects whose github_url is missing from output_text."""
    return [p['name'] for p in projects if p['github_url'] not in output_text]


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


def insert_images(content_text, projects):
    """Insert up to 3 project images into the reformatted text, after the
    paragraph mentioning each selected project's name. Skips a project's
    image if its name can't be found in the text."""
    n = len(projects)
    image_slots = set()
    if n >= 1: image_slots.add(0)
    if n >= 3: image_slots.add(n // 2)
    if n >= 2: image_slots.add(n - 1)
    image_slots = sorted(image_slots)[:3]

    for idx in image_slots:
        project = projects[idx]
        img_path = _find_project_image(project)
        if not img_path:
            continue

        name = project['name']
        pos = content_text.find(name)
        if pos == -1:
            continue

        paragraph_end = content_text.find('\n\n', pos)
        if paragraph_end == -1:
            paragraph_end = len(content_text)

        image_markdown = f"\n\n![{name}](../../{img_path})\n"
        content_text = content_text[:paragraph_end] + image_markdown + content_text[paragraph_end:]

    return content_text


def reformat_with_mistral(client, newsletter_text):
    """Sends the finished newsletter to Mistral to restyle as a Medium post."""
    print("🤖 Reformatting newsletter as Medium post with Mistral...")
    try:
        response = client.chat.complete(
            model="mistral-medium-latest",
            messages=[
                {"role": "system", "content": MEDIUM_SYSTEM_PROMPT},
                {"role": "user", "content": f"Reformat this newsletter as a Medium post:\n\n{newsletter_text}"}
            ],
            max_tokens=4096,
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Mistral API Error: {e}")
        return None


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
    newsletter_path = find_latest_newsletter()
    if not newsletter_path:
        print("❌ Could not find SUBSTACK_NEWSLETTER file in today's delivery folder")
        return

    print(f"📖 Found source newsletter: {newsletter_path}")
    with open(newsletter_path, 'r', encoding='utf-8') as f:
        newsletter_text = f.read()

    client = get_mistral_client()
    if not client:
        print("❌ Failed to initialize Mistral client. Check config.json.")
        return

    content = reformat_with_mistral(client, newsletter_text)
    if not content:
        return

    projects = load_projects()
    if projects:
        missing = find_missing_urls(projects, content)
        if missing:
            print(f"⚠️  Warning: these projects' URLs are missing from the Medium post: {', '.join(missing)}")
        content = insert_images(content, projects)

    content = content + MEDIUM_SUBSCRIBE_LINK
    save_post(content)
    print("\n" + "="*30 + " PREVIEW " + "="*30)
    print(content[:500] + "...")
    print("="*69)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd /Users/chesterbeard/Desktop/opensourcescribes && python content/test_generate_medium_post.py -v`
Expected: `OK` with 4 tests passing.

- [ ] **Step 5: Manual verification against a real newsletter file**

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes && DELIVERY_DATE=06-19 python content/generate_medium_post.py
```

Expected: console shows "Found source newsletter", "Reformatting...", "Saved to deliveries/06-19/MEDIUM_POST.md". Open that file and confirm coherent Medium-style prose, the subscribe link at the bottom, and (if `assets/bg_*.png` files exist for that batch) at least one image markdown line.

- [ ] **Step 6: Commit**

```bash
git add content/generate_medium_post.py content/test_generate_medium_post.py
git commit -m "refactor: reformat Medium post from newsletter via Mistral instead of generating per-project on Claude"
```

---

### Task 4: Reorder `core/workflow_manager.py` so Newsletter runs first

**Files:**
- Modify: `core/workflow_manager.py:43-46`

Medium and Reddit now depend on the newsletter's output file existing, which didn't used to be true. The step order must change to put Newsletter first.

- [ ] **Step 1: Reorder the steps list**

In `core/workflow_manager.py`, replace:

```python
        # 3. Written Content (Parallelizable, but running sequentially for cleaner logs)
        ("Generating Medium Post", f"{python_exe} generate_medium_post.py"),
        ("Generating Reddit Post", f"{python_exe} generate_reddit_post.py"),
        ("Generating Substack Newsletter", f"{python_exe} generate_newsletter.py"),
```

with:

```python
        # 3. Written Content — Newsletter must run first now: Medium and Reddit
        # reformat its finished output instead of generating independently.
        ("Generating Substack Newsletter", f"{python_exe} generate_newsletter.py"),
        ("Generating Medium Post", f"{python_exe} generate_medium_post.py"),
        ("Generating Reddit Post", f"{python_exe} generate_reddit_post.py"),
```

- [ ] **Step 2: Verify the file parses and the list order is correct**

Run: `cd /Users/chesterbeard/Desktop/opensourcescribes && python3 -c "
from core.workflow_manager import main
import core.workflow_manager as wm
import inspect
src = inspect.getsource(wm.main)
medium_idx = src.index('Generating Medium')
reddit_idx = src.index('Generating Reddit')
newsletter_idx = src.index('Generating Substack')
assert newsletter_idx < medium_idx < reddit_idx, 'order is wrong'
print('order OK: Newsletter -> Medium -> Reddit')
"`

Expected: `order OK: Newsletter -> Medium -> Reddit`

- [ ] **Step 3: Commit**

```bash
git add core/workflow_manager.py
git commit -m "fix: run newsletter generation before Medium/Reddit, which now depend on its output"
```

---

### Task 5: End-to-end verification of the full reordered pipeline

**Files:** none (verification only)

- [ ] **Step 1: Run the three written-content steps in sequence against a real batch**

Pick an existing batch date with a `posts_data.json`-backed delivery, or use today's if a fresh batch has been run. Set `DELIVERY_DATE` once and run all three in the new order manually (this mirrors what `workflow_manager.py` will now do):

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes
export DELIVERY_DATE=06-19
python content/generate_newsletter.py
python content/generate_medium_post.py
python content/generate_reddit_post.py
```

- [ ] **Step 2: Confirm Sonnet call volume dropped**

While Step 1 runs, watch the console: Sonnet/Claude calls (`📦` lines) should appear **only** during the `generate_newsletter.py` run. The Medium and Reddit runs should show `🤖 Reformatting newsletter as ... with Mistral...` instead of any per-project `📦` lines.

- [ ] **Step 3: Confirm output files**

```bash
ls -la deliveries/06-19/
```

Expected: `SUBSTACK_NEWSLETTER.txt`, `MEDIUM_POST.md`, `REDDIT_POST.md` all present, all with recent timestamps from this run, all non-empty.

- [ ] **Step 4: Spot-check content quality**

Open `MEDIUM_POST.md` and `REDDIT_POST.md` and confirm: every project from that day's `SUBSTACK_NEWSLETTER.txt` is mentioned, no banned marketing words leaked in, tone matches the platform (Medium = blog voice, Reddit = casual community voice), and no warning about missing URLs was printed in Step 1's console output.

- [ ] **Step 5: Run the full orchestrator for real (optional, costs a full batch run)**

Once the above looks right, run the complete pipeline including script/video generation to confirm `workflow_manager.py`'s new order works unattended:

```bash
cd /Users/chesterbeard/Desktop/opensourcescribes && python core/workflow_manager.py
```

Expected: `WORKFLOW SUMMARY` at the end shows `7/7` (or however many steps exist) successful, in the new order (Newsletter before Medium before Reddit in the printed step log).

---

## Self-Review

**Spec coverage:** Task 1 covers the newsletter caching optimization. Tasks 2-3 cover replacing Medium/Reddit generation with Mistral reformatting (including the image-insertion and URL-safety-check details called out in the spec's Components section). Task 4 covers the `workflow_manager.py` reordering called out in the spec's Architecture section. Task 5 covers the spec's Testing section (manual/comparative verification + the URL-presence safety check exercised live). The spec's "Out of Scope" items (`auto_script_generator.py`, DeepSeek, AINewsletter, API key splitting) are correctly not touched by any task.

**Placeholder scan:** No TBD/TODO; all code blocks are complete, runnable file contents, not fragments described in prose.

**Type/signature consistency:** `find_missing_urls(projects, output_text)` has the same signature and behavior in both `generate_reddit_post.py` and `generate_medium_post.py`. `save_post(content)`, `find_latest_newsletter()`, and `get_mistral_client()` keep identical signatures to their existing counterparts in `reformat_newsletter.py` and the pre-rewrite files, so no caller elsewhere in the codebase breaks. `_find_project_image(project)` keeps its exact original signature from the pre-rewrite `generate_medium_post.py`, since Task 3's test mocks it by that exact name.

