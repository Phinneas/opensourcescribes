# GitHub Video Automation

Automatically generate YouTube videos from your Medium posts about GitHub projects.

## 🎬 Quick Start

### Option A: Auto-Generate Scripts (Recommended)

1. **Create URL list** - Just paste GitHub URLs:
```bash
echo "https://github.com/owner/repo1" > github_urls.txt
echo "https://github.com/owner/repo2" >> github_urls.txt
```

2. **Generate scripts automatically**:
```bash
python3 simple_parser.py github_urls.txt
```

3. **Create video**:
```bash
python3 video_maker.py
```

The system automatically generates 2-4 minute narration scripts from GitHub data!

### Option B: Manual Scripts

### 1. Install Dependencies
```bash
pip install moviepy playwright gtts feedparser
playwright install firefox
```

### 2. Create Your Project Data
Edit `posts_data.json` with your GitHub projects:

```json
[
    {
        "id": "p1",
        "name": "Project Name",
        "github_url": "https://github.com/owner/repo",
        "script_text": "Your narration script for this project."
    }
]
```

### 3. Generate Video
```bash
python video_maker.py
```

The script will:
- 📸 Take screenshots of each GitHub project page
- 🎙️ Generate audio narration from your script text
- 🎬 Combine everything into `final_github_roundup.mp4`

## 📁 Project Structure

```
opensourcescribes/
├── video_maker.py          # Main video generation script
├── posts_data.json         # Your project data (edit this!)
├── assets/                 # Generated screenshots and audio
└── final_github_roundup.mp4 # Output video
```

## 🔧 Configuration

Edit these variables in `video_maker.py`:

```python
OUTPUT_FOLDER = "assets"              # Where to save temp files
FINAL_VIDEO_NAME = "final_github_roundup.mp4"  # Output filename
DATA_FILE = "posts_data.json"         # Input data file
```

## 📝 JSON Format

Each project needs:
- `id`: Unique identifier (e.g., "p1", "p2")
- `name`: Project display name
- `github_url`: Full GitHub repository URL
- `script_text`: Narration text (will be converted to speech)

## 🎯 Workflow for Medium Posts

1. **Write your Medium post** with GitHub projects
2. **Copy project info** into `posts_data.json`:
   - Project name
   - GitHub URL
   - Description/narration
3. **Run the script**: `python video_maker.py`
4. **Upload to YouTube**: Use the generated MP4

## 🚀 Next Steps

### Planned Enhancements
- [ ] Text overlays showing project names
- [ ] Intro/outro cards with branding
- [ ] Hume.ai integration for better voice quality
- [ ] Background music
- [ ] Smooth transitions between projects
- [ ] GitHub stats overlay (stars, forks)

## 🛠️ Technical Details

- **Browser**: Firefox (via Playwright)
- **Video Library**: MoviePy 2.x
- **Voice**: gTTS (Google Text-to-Speech)
- **Resolution**: 1920x1080 (1080p)
- **Format**: MP4 (H.264 video, AAC audio)

## 💡 Tips

- Keep script text concise (30-60 seconds per project)
- Use clear, engaging descriptions
- Test with 2-3 projects first before doing all 9-13
- Screenshots are taken at 1920x1080 resolution

## 📦 Files Generated

- `assets/p1_screen.png` - Screenshot of first project
- `assets/p1_audio.mp3` - Audio narration for first project
- `final_github_roundup.mp4` - Final compiled video

## 🐛 Troubleshooting

**"Data file not found"**
- Make sure `posts_data.json` exists in the same folder

**"Module not found"**
- Run: `pip install moviepy playwright gtts`
- Run: `playwright install firefox`

**Video quality issues**
- Adjust resolution in `take_screenshot()` function
- Change FPS in `write_videofile()` call

## 📄 License

MIT License - Feel free to use and modify!
