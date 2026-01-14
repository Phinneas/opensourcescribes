# AI Presenter Prompts for OpenSourceScribes

Complete guide to generating AI presenter images for your enhanced YouTube graphics.

## 🎯 Overview

This guide provides ready-to-use prompts for creating consistent, professional presenter images using:
- **Ideogram** (text-friendly, good for consistent branding)
- **Midjourney** (best artistic quality, requires Discord)
- **Flux.1** (excellent quality, free/cheap, API available)
- **Stable Diffusion XL** (free, local or hosted)

## 📋 Quick Start

1. **Choose a style** below (Professional, Enthusiastic, or Curious)
2. **Copy the prompt** for your chosen AI service
3. **Generate your presenter** (save as transparent PNG if possible)
4. **Use in enhanced graphics**: `python video_maker.py` will integrate it automatically

---

## 🎭 Presenter Styles

### Style 1: Professional (Recommended)

**Best for:** Consistent, trustworthy, educational content

```
A friendly tech presenter in their 30s, excited expression, 
gesturing towards screen right, wearing casual smart attire 
(dark hoodie or blazer), professional headshot style, 
modern tech background, studio lighting, looking slightly 
to the right, engaging smile, dynamic pose leaning forward, 
4K portrait photography, shallow depth of field
```

**Variations:**
- **With glasses:** "...wearing modern eyeglasses, intelligent look..."
- **Different gender:** "...female tech presenter..." or "...non-binary presenter..."
- **Background:** "...colorful gradient background..." or "...minimalist tech office..."

---

### Style 2: Enthusiastic (High Energy)

**Best for:** Exciting discoveries, viral content, high-engagement thumbnails

```
An energetic developer in their 20s-30s, very excited expression, 
pointing finger forward towards viewer, wearing modern tech 
casual tshirt or hoodie, vibrant energy, dynamic pose jumping 
or leaning in, enthusiastic smile, expressive body language, 
colorful tech background, studio lighting, 4K photography
```

**Variations:**
- **Pointing at screen:** "...pointing at computer screen on right..."
- **Celebrating:** "...arms raised in celebration, excited expression..."
- **With props:** "...holding laptop, showing code on screen..."

---

### Style 3: Curious & Thoughtful

**Best for:** Deep dives, tutorials, explanation-focused content

```
A thoughtful tech explorer, curious and interested expression, 
looking at something off-screen right, hand near chin in 
thinking pose, wearing casual smart clothes, professional 
yet approachable, warm lighting, modern tech workspace 
background, 4K portrait
```

**Variations:**
- **Teaching gesture:** "...making explanatory hand gesture..."
- **With laptop:** "...working on laptop, focused expression..."
- **Note-taking:** "...holding notebook, taking notes..."

---

## 🎨 Service-Specific Prompts

### For Ideogram (2.0)

**Strengths:** Excellent text rendering, consistent style, easy API

```
[PROJECT NAME] YouTube thumbnail with presenter, friendly tech 
reviewer in 30s gesturing to screen right, wearing dark hoodie, 
modern tech background with gradient from teal to deep blue, 
professional studio lighting, 4K quality, consistent character 
design --ar 2:3 --style raw
```

**Tips for Ideogram:**
- Use `--style raw` for photorealistic results
- Add `consistent character` to maintain same presenter across videos
- Try `--stylize 250-750` for more artistic freedom

---

### For Midjourney v6

**Strengths:** Best quality, artistic, viral potential

```
A professional tech YouTuber reviewing [PROJECT NAME], excited 
expression, pointing to screen right, wearing casual smart attire, 
modern tech studio background with teal and blue lighting, dynamic 
pose leaning forward, 4K portrait photography, shallow depth of 
field, trending on artstation --ar 2:3 --v 6 --style raw --stylize 500
```

**Tips for Midjourney:**
- Use `--v 6` for latest version
- `--style raw` for realistic look
- `--stylize 0-1000` (higher = more artistic)
- `--chaos 0-100` for variety in results
- `--weird 0-3000` for experimental styles

---

### For Flux.1 (Schnell/Dev/Pro)

**Strengths:** Fast, excellent quality, affordable

```
Professional tech presenter reviewing [PROJECT NAME], friendly 
expression in 30s, gesturing towards screen right, wearing dark 
hoodie or blazer, modern tech background with teal accents, studio 
lighting, engaging smile, dynamic pose, 4K portrait photography, 
shallow depth of field
```

**Tips for Flux.1:**
- No special flags needed (simple prompting)
- Excellent at following prompts
- Great text rendering (better than most SD models)
- Use aspect ratio in prompt: "portrait aspect ratio 2:3"

**Via Replicate API:**
```python
from replicate import Client

client = Client(api_token="your_replicate_key")

output = client.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": "Professional tech presenter, excited expression, gesturing right, wearing dark hoodie, modern tech background, 4K portrait",
        "aspect_ratio": "2:3",
        "num_outputs": 4,  # Generate 4 options
    }
)

# Download your favorite
import requests
with open("presenter.png", "wb") as f:
    f.write(requests.get(output[0]).content)
```

---

### For Stable Diffusion XL (SDXL)

**Strengths:** Free, local, customizable

```
Professional tech YouTuber, excited expression, gesturing towards 
screen right, wearing casual smart attire, modern tech background, 
studio lighting, engaging smile, dynamic pose, 4K portrait photography, 
shallow depth of field, professional quality
```

**Negative prompt (what to avoid):**
```
blurry, low quality, distorted, deformed hands, extra fingers, 
bad anatomy, cartoon, illustration, painting, drawing
```

**Tips for SDXL:**
- Use negative prompts to avoid common AI issues
- Try different samplers: `DPM++ 2M Karras` or `Euler a`
- CFG scale: 7-9 for good prompt adherence
- Steps: 30-50 for quality vs speed

**Via Automatic1111/ComfyUI:**
- Resolution: 768x1024 (2:3 portrait)
- Model: SDXL Base 1.0 or Juggernaut XL
- Refiner: SDXL Refiner (optional)

---

## 🎬 Advanced Techniques

### Create a Consistent Character

**Option 1: Seed-based consistency**
- Generate with same seed: `--seed 12345` (Midjourney)
- Keep prompt mostly the same
- Vary only pose/expression

**Option 2: Train a LoRA (SDXL/Flux)**
- Collect 20-50 photos of your ideal presenter (or yourself!)
- Train a LoRA on Replicate, Together.ai, or locally
- Use in all prompts: "photo of `<your_lora_name>` tech presenter"

**Option 3: Use yourself!**
- Take high-quality photos against plain background
- Remove background (remove.bg or Photoshop)
- Use in your graphics (most authentic!)

---

## 🎨 Pose Variations

Copy these pose descriptors into your prompts:

**Gesturing Right (for split-left layout):**
```
...gesturing towards screen right with right hand, arm extended, 
pointing at content area, leaning slightly right, engaged expression...
```

**Gesturing Left (for split-right layout):**
```
...gesturing towards screen left with left hand, arm extended, 
pointing at content area, leaning slightly left, engaged expression...
```

**Headphones (tech vibe):**
```
...wearing modern over-ear headphones, tech-focused aesthetic, 
podcaster style...
```

**With Laptop/Device:**
```
...holding sleek laptop showing code on screen, developer aesthetic, 
modern tech workspace...
```

**Explaining/Gesturing:**
```
...making explanatory hand gesture, teaching pose, educator vibe, 
engaging body language...
```

---

## 🎯 Background Options

Match your presenter background to your graphic style:

**Transparent (Best):**
```
...on white background, easy to remove background, isolated subject...
```
Then use: `remove.bg` or Photoshop to make transparent

**Solid Color:**
```
...on solid #0a1628 blue background, easy to composite...
```

**Gradient (matches your brand):**
```
...on gradient background from teal #40E0D0 to deep blue #0a1628...
```

**Tech Studio:**
```
...in modern tech studio with colorful LED lights, teal and purple 
glow, professional recording setup...
```

---

## 📊 Testing Your Results

**A/B Test Approach:**

1. **Generate 3-4 presenter variations** using different styles
2. **Create test graphics** with each presenter
3. **Run polls** on Twitter/X, Discord, Reddit
4. **Measure engagement** after 1 week
5. **Stick with winner** for 10+ videos, then re-test

**Metrics to Track:**
- Click-through rate (CTR)
- Average view duration
- Subscriber conversion rate
- Comments mentioning host/presenter

---

## 🚀 Integration Workflow

### Full Automated Workflow:

```python
# 1. Generate presenter with AI
presenter_prompt = generator.create_ai_presenter_prompt(
    "React", 
    project_type="web", 
    style="professional"
)

# 2. Use Ideogram/Midjourney/Flux API to generate
presenter_image = generate_with_ai(presenter_prompt, save_as="presenter.png")

# 3. Create enhanced graphic
from codestream_graphics_enhanced import create_enhanced_graphic

create_enhanced_graphic(
    project_name="React",
    github_url="https://github.com/facebook/react",
    presenter_image_path="presenter.png",
    output_path="assets/react_enhanced.png"
)
```

### Manual Workflow:

1. Copy prompt from this guide
2. Generate presenter on Ideogram/Midjourney website
3. Download image (preferably as PNG)
4. Remove background (remove.bg or Photoshop)
5. Save as `presenter.png` in project folder
6. Run `python video_maker.py` (will use enhanced graphics)

---

## 🎨 Quick Prompt Templates

### Template 1: Quick Professional (Copy-Paste Ready)

```
Professional tech presenter in 30s, excited friendly expression, 
gesturing towards screen right, wearing dark hoodie or blazer, 
modern tech background with teal and blue gradient, studio 
lighting, engaging smile, dynamic pose leaning forward, 
4K portrait photography, shallow depth of field, professional quality
```

**Use for:** Any project, consistent branding

---

### Template 2: High-Energy Viral

```
Energetic tech YouTuber in 20s-30s, very excited expression, 
pointing finger forward at viewer, wearing modern tshirt or 
hoodie, vibrant energy, dynamic pose, enthusiastic smile, 
colorful tech background, studio lighting, 4K, viral YouTube 
thumbnail style, high contrast
```

**Use for:** Trending projects, breakthrough tools, must-see content

---

### Template 3: Tutorial/Explanation

```
Thoughtful tech educator, curious interested expression, looking 
at screen right with teaching gesture, wearing casual smart 
clothes, professional approachable, warm lighting, modern tech 
workspace background, 4K portrait, educational content style
```

**Use for:** Tutorials, deep dives, explanations

---

## 💡 Pro Tips

1. **Test different genders/ethnicities** - see what resonates with your audience
2. **Keep outfit consistent** - same hoodie/shirt across videos builds recognition
3. **Match expression to content** - excited for big features, thoughtful for tutorials
4. **Use good lighting in prompt** - "studio lighting", "soft professional lighting"
5. **Add channel branding** - "...wearing OpenSourceScribes branded hoodie..."
6. **Iterate on feedback** - ask audience which presenter style they prefer

---

## 🎯 Recommended Starting Point

**For your channel (OpenSourceScribes), I recommend:**

1. **Style:** Professional (approachable but credible)
2. **Gender:** Choose what you identify with or test both
3. **Age:** 20s-30s (relatable to tech audience)
4. **Attire:** Dark hoodie or blazer (tech-casual)
5. **AI Service:** Flux.1 Schnell (free/cheap, great quality) or Ideogram (consistent)

**First Prompt to Try:**

```
Professional tech presenter in their 30s, excited friendly expression, 
gesturing towards screen right, wearing dark casual hoodie, modern 
tech background with teal and blue gradient lighting, studio lighting, 
engaging smile, dynamic pose leaning forward, 4K portrait photography, 
shallow depth of field, YouTube content creator style
```

Generate this in Ideogram or Flux.1, then integrate with your enhanced graphics!

---

## 📞 Need Help?

- **Test generation:** Run `python codestream_graphics_enhanced.py` to see example prompts
- **Integration:** Edit `video_maker.py` to use `EnhancedCodeStreamGraphics` class
- **Feedback:** A/B test different styles and measure engagement

Happy generating! 🚀
