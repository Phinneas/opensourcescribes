# Medium to Video - Quick Copy-Paste Template

## Option 1: Simple Text Format (Easiest!)

Just copy your Medium post and paste it here in this format:

```
---
Project Name or owner/repo
Description paragraph goes here.
Can be multiple lines.
---
Another Project or owner/repo2
Another description here.
---
```

Then run: `python simple_parser.py` to convert it to JSON.

---

## Option 2: Direct JSON (More Control)

Copy this template and fill in your projects:

```json
[
    {
        "id": "p1",
        "name": "Project Display Name",
        "github_url": "https://github.com/owner/repo",
        "script_text": "Your narration script here. This is what will be spoken in the video."
    },
    {
        "id": "p2",
        "name": "Second Project",
        "github_url": "https://github.com/owner/repo2",
        "script_text": "Second project description and narration."
    }
]
```

Save as `posts_data.json`

---

## Option 3: From Medium HTML (Advanced)

1. Open your Medium post in browser
2. Right-click → Inspect
3. Find the `<article>` element
4. Right-click → Copy → Copy outerHTML
5. Paste into `medium_raw.html`
6. Run: `python parse_medium_html.py`

---

## Quick Workflow:

**For a typical "9 Trending GitHub Repos" post:**

1. **Copy from Medium** - Select all project sections
2. **Paste into template** - Use Option 1 or 2 above
3. **Run video maker** - `python video_maker.py`
4. **Done!** - Upload to YouTube

---

## Example: Real Medium Post Format

If your Medium post looks like this:

```
SeraUI
https://github.com/seraui/seraui
SeraUI is a sleek UI component library built for React...

LangChain  
https://github.com/langchain-ai/langchain
LangChain is a framework for developing applications...
```

Just format it as:

```
---
seraui/seraui
SeraUI is a sleek UI component library built for React...
---
langchain-ai/langchain
LangChain is a framework for developing applications...
---
```

Then run `python simple_parser.py` and it creates `posts_data.json` automatically!
