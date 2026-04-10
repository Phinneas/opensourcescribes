# Medium to Video Data Converter

This template helps you quickly convert your Medium post content into the JSON format needed for video generation.

## 📋 Quick Copy-Paste Template

Copy this template and fill in your project data:

```
---
Project Name or Owner/Repo
Brief description of the project that will be spoken in the video.
You can write multiple sentences here.
---
Another Project Name
Another description here.
Keep it concise but informative.
---
```

## 🚀 Usage

### Method 1: Simple Text File (Recommended)

1. **Copy the template above** into a new file called `medium_input.txt`
2. **Replace with your actual projects** from your Medium post
3. **Run the converter:**
   ```bash
   python convert_medium.py
   ```
4. **This creates `posts_data.json`** ready for video generation!

### Method 2: Direct JSON (Advanced)

Edit `posts_data.json` directly:

```json
[
    {
        "id": "p1",
        "name": "Project Name",
        "github_url": "https://github.com/owner/repo",
        "script_text": "Your narration script here."
    }
]
```

## 📝 Example

**From your Medium post:**
```
---
seraui/seraui
SeraUI is a sleek UI component library built for React and Next.js. 
It leverages Tailwind CSS to deliver fast and responsive design.
---
AutoGPT
An experimental open-source application showcasing GPT-4 capabilities.
It chains together LLM thoughts to autonomously achieve goals.
---
```

**Becomes:**
```json
[
    {
        "id": "p1",
        "name": "seraui",
        "github_url": "https://github.com/seraui/seraui",
        "script_text": "SeraUI is a sleek UI component library..."
    },
    {
        "id": "p2",
        "name": "AutoGPT",
        "github_url": "https://github.com/Significant-Gravitas/AutoGPT",
        "script_text": "An experimental open-source application..."
    }
]
```

## 💡 Tips

- **Keep descriptions 2-3 sentences** (15-30 seconds of speech)
- **Use the project's actual name** from GitHub
- **Include what makes it interesting** - don't just describe features
- **Write naturally** - this will be spoken aloud
- **Test with 2-3 projects first** before doing all 9-13

## 🎬 Full Workflow

1. Write your Medium post
2. Copy project info into `medium_input.txt`
3. Run `python convert_medium.py`
4. Run `python video_maker.py`
5. Upload `final_github_roundup.mp4` to YouTube!
