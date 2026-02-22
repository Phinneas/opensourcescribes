# MiniMax-GitHub: Enhanced Video Generation System

## Overview

This document explains how to use the new MiniMax-integrated video generation system that creates engaging, professional videos for your GitHub projects with dynamic content, scrolling animations, and AI-enhanced visuals.

## What's New?

### 🎬 Dynamic Video Content
Instead of static images, you now get:
- ** scrolling GitHub page animations** - Smooth camera movements across repository pages
- **Animated code snippets** - Watch code being typed character-by-character with syntax highlighting
- **UI demonstrations** - Professional interface mockups and animations
- **MiniMax AI-enhanced videos** - AI-generated b-roll based on project descriptions

### 🎯 Key Features

1. **GitHub Page Capture System**
   - Captures repository overview with smooth scrolling
   - Focus on key sections: features, code files, issues
   - Creates scrolling animations automatically

2. **MiniMax Video Generation**
   - Text-to-video: Generate b-roll from descriptions
   - Image-to-video: Animate static project graphics
   - Code animations: Professional typing effects
   - UI demos: Smooth interface demonstrations

3. **Enhanced Video Suite Integration**
   - Works seamlessly with existing workflow
   - Falls back to static graphics if MiniMax unavailable
   - Configurable and customizable

## Setup

### 1. Install Dependencies

```bash
# Install selenium for browser capture
pip install selenium

# Install webkit2png (macOS)
brew install webkit2png

# Install MiniMax integration (auto-handled)
# The system will gracefully handle missing dependencies
```

### 2. Configure MiniMax API Key

Edit `config.json` and add your MiniMax API key:

```json
{
  "minimax": {
    "api_key": "YOUR_MINIMAX_API_KEY_HERE",
    "use_minimax": true,
    "model": "minimax-hailuo-2.3-fast",
    "max_video_duration": 5
  }
}
```

**How to get MiniMax API key:**
1. Visit https://platform.minimax.io/
2. Create account and navigate to API settings
3. Generate new API key
4. Add to config.json

### 3. Verify Installation

```bash
python enhanced_video_demo.py
```

This will run through available demos to verify your setup.

## Usage

### Basic Video Generation (with MiniMax)

```bash
# Generate videos for projects in posts_data.json
python video_suite.py
```

The video suite will now automatically:
1. Try to generate MiniMax-enhanced visuals
2. Fall back to static graphics if MiniMax unavailable  
3. Include GitHub page captures where configured
4. Create code animations when appropriate

### Test MiniMax Capabilities

```bash
python enhanced_video_demo.py
```

Choose an option:
- **Option 1**: MiniMax Basic - Test UI demos and code animations
- **Option 2**: GitHub Capture - Test page scrolling
- **Option 3**: Complete Workflow - Full pipeline demo
- **Option 4**: All Demos

### GitHub Page Capture Example

```bash
# Capture specific GitHub repo
python github_page_capture.py https://github.com/owner/repo

# Capture specific sections
python github_page_capture.py https://github.com/owner/repo --sections overview features code issues
```

## Integration with Existing Workflow

The enhanced system maintains full compatibility with your existing scripts:

### Enhanced video_suite.py

- Automatically uses MiniMax when available
- Falls back gracefully to static graphics
- No changes needed to existing workflow
- Configure via `config.json`

### Example Configuration

```json
{
  "video_settings": {
    "use_minimax": true,
    "capture_github_pages": true,
    "enable_captions": true
  }
}
```

## Cost Considerations

### MiniMax Pricing (Hailuo-2.3-Fast Model)

- Balanced speed and quality
- Typical cost: $0.01-0.02 per 5-second video
- Estimated: $0.10-0.20 per project video
- **Cost-saving tip**: Set `use_minimax` to `false` in config for static-only videos

### API Usage Tips

1. **Cache results**: Videos are cached by project ID
2. **Selectively enable**: Enable MiniMax for featured projects only
3. **Batch process**: Run overnight for multiple projects
4. **Monitor usage**: Check MiniMax dashboard for usage stats

## Features Breakdown

### 1. MiniMax Video Generator (`minimax_integration.py`)

**Capabilities:**
- `generate_text_to_video()` - Create video from description
- `generate_image_to_video()` - Animate static images
- `generate_code_animation()` - Animated typing effects
- `generate_ui_demonstration()` - UI mockup videos

**Example:**
```python
from minimax_integration import get_minimax_generator

generator = get_minimax_generator()

# Generate UI demo
video = generator.generate_ui_demonstration(
    "A smooth modern interface showing analytics dashboard",
    "demo.mp4"
)
```

### 2. GitHub Page Capture (`github_page_capture.py`)

**Capabilities:**
- Capture repository overview with scrolling
- Focus on README features section
- Capture code files as scrolling animations  
- Capture issues/pr sections

**Example:**
```python
from github_page_capture import GitHubPageCapture

capturer = GitHubPageCapture()

# Capture all sections
videos = capturer.capture_all_key_sections(
    "https://github.com/owner/repo"
)

# Returns: {'overview': 'path.mp4', 'features': 'path.mp4', ...}
```

### 3. Enhanced Video Suite (`video_suite.py`)

**New Methods:**
- `generate_minimax_enhancement()` - AI-enhanced video content
- `generate_captures_and_code_animations()` - GitHub + code animations
- `create_segment()` - Supports MiniMax-enhanced segments

## Troubleshooting

### MiniMax API Errors

**Problem**: "MINIMAX_API_KEY not found"
- **Solution**: Add API key to `config.json` under `minimax.api_key`

**Problem**: Video generation timeouts  
- **Solution**: Check network, verify API key, check MiniMax credit balance

### Selenium/Browser Issues

**Problem**: "selenium not installed"
- **Solution**: Run `pip install selenium` and install ChromeDriver

**Problem**: Browser capture fails
- **Solution**: System falls back to webkit2png capture

### GitHub Capture Issues

**Problem**: Repository not accessible
- **Solution**: Check repo is public, verify URL format

**Problem**: Scroll animations not smooth
- **Solution**: Slower framerate (12fps) for better scroll effect

## Best Practices

### For Project Videos

1. **Enable MiniMax for featured projects**: Set `use_minimax: true` in project-specific config
2. **Test small first**: Run demo.py before batch processing
3. **Monitor costs**: Check MiniMax dashboard regularly
4. **Quality vs Speed**: MiniMax-Hailuo-2.3-Fast offers best balance

### For GitHub Captures

1. **Focus on key sections**: Don't capture entire repo
2. **Test scrolling length**: 5-8 seconds per section is ideal
3. **Combine content**: Mix overview + features + code sections
4. **Cache results**: Captured videos are reused

### For Code Animations

1. **Keep snippets short**: 50-100 characters max
2. **Use simple examples**: Clear, readable code
3. **Specify language**: Better syntax highlighting
4. **Mix with UI demos**: Variety keeps videos engaging

## Examples

### Example 1: Basic Enhanced Video

```python
from video_suite import VideoSuite

suite = VideoSuite()
suite.load_projects()
suite.select_shorts()  # Interactive selection
suite.select_deep_dives()
await suite.run()  # Enhanced with MiniMax automatically
```

### Example 2: Custom MiniMax Content

```python
from minimax_integration import get_minimax_generator

generator = get_minimax_generator()

# Custom UI demonstration
video = generator.generate_ui_demonstration(
    "A modern coding interface showing Python development with dark theme"
    "and colorful syntax highlighting",
    "python_demo.mp4"
)
```

### Example 3: GitHub Page Capture

```python
from github_page_capture import GitHubPageCapture

capturer = GitHubPageCapture()

# Capture only specific sections
results = capturer.capture_all_key_sections(
    "https://github.com/your-username/your-repo"
)
```

## Next Steps

1. **Add your MiniMax API key** to `config.json`
2. **Run the demo**: `python enhanced_video_demo.py`
3. **Test with your first project**: Modify `github_urls.txt` and run `python video_suite.py`
4. **Review and iterate**: Check generated videos, adjust prompts as needed
5. **Scale up**: Process multiple projects and create engaging content!

## Support

For issues or questions:
1. Check this guide's Troubleshooting section
2. Review code comments in integration modules
3. Run `enhanced_video_demo.py` to test your setup
4. Check MiniMax API documentation for latest features

## Version History

- **v1.0** - Initial MiniMax integration with video generation
- **v1.1** - GitHub page capture system added
- **v1.2** - Enhanced video suite integration
- **v1.3** - Code animations and UI demonstrations

Enjoy creating more engaging videos! 🎬
