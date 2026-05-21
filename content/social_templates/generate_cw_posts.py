"""
OpenSourceScribes — Client Whisperer Post Card Generator
Generates 5 filled-in Instagram cards (1080x1080) from author pain point source material.
All use Pillar 1 (Client Whisperer) brand: teal accent on deep navy.
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── Brand Colors ──────────────────────────────────────────────────────────────
DEEP_NAVY  = (10, 22, 40)
DARK_GRAY  = (26, 26, 46)
TEAL       = (64, 224, 208)
WHITE      = (255, 255, 255)
SOFT_GRAY  = (204, 204, 204)
TEAL_DIM   = (30, 90, 84)

W, H   = 1080, 1080
SAFE   = 72
OUT_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Font Loader ───────────────────────────────────────────────────────────────
def load_font(size, bold=True):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()

def load_mono(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return load_font(size, bold=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_grid(draw, spacing=54):
    for x in range(0, W, spacing):
        draw.line([(x, 0), (x, H)], fill=(64, 224, 208, 18), width=1)
    for y in range(0, H, spacing):
        draw.line([(0, y), (W, y)], fill=(64, 224, 208, 18), width=1)

def draw_accent_bar(draw, y, thickness=6):
    draw.rectangle([(0, y), (W, y + thickness)], fill=TEAL)

def draw_left_rule(draw, y_start=160, y_end=None):
    if y_end is None:
        y_end = H - SAFE - 130
    draw.rectangle([(SAFE, y_start), (SAFE + 4, y_end)], fill=TEAL)

def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines, current = [], []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines

def draw_wrapped(draw, text, font, x, y, max_width, fill, line_height=None):
    lines = wrap_text(text, font, max_width, draw)
    if line_height is None:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_height = (bbox[3] - bbox[1]) + 10
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y

def draw_bracket_box(draw, x0, y0, x1, y1, thickness=2):
    corner = 28
    c = TEAL
    draw.line([(x0, y0), (x0 + corner, y0)], fill=c, width=thickness)
    draw.line([(x0, y0), (x0, y0 + corner)], fill=c, width=thickness)
    draw.line([(x1, y0), (x1 - corner, y0)], fill=c, width=thickness)
    draw.line([(x1, y0), (x1, y0 + corner)], fill=c, width=thickness)
    draw.line([(x0, y1), (x0 + corner, y1)], fill=c, width=thickness)
    draw.line([(x0, y1), (x0, y1 - corner)], fill=c, width=thickness)
    draw.line([(x1, y1), (x1 - corner, y1)], fill=c, width=thickness)
    draw.line([(x1, y1), (x1, y1 - corner)], fill=c, width=thickness)

def make_card(filename, headline, sub, body_lines, cta):
    """Render a single Client Whisperer card."""
    img = Image.new("RGBA", (W, H), DEEP_NAVY + (255,))
    draw = ImageDraw.Draw(img)

    draw_grid(draw)
    draw_accent_bar(draw, y=0)
    draw_left_rule(draw)

    # Pillar tag
    tag_font = load_mono(22)
    draw.text((SAFE, 28), "// PILLAR 01  ·  CLIENT WHISPERER", font=tag_font, fill=TEAL)

    # Headline
    h_font = load_font(62, bold=True)
    y = draw_wrapped(draw, headline, h_font,
                     x=SAFE + 22, y=162,
                     max_width=W - SAFE * 2 - 30,
                     fill=WHITE, line_height=74)

    y += 22

    # Sub-claim
    s_font = load_font(30, bold=False)
    y = draw_wrapped(draw, sub, s_font,
                     x=SAFE + 22, y=y,
                     max_width=W - SAFE * 2 - 30,
                     fill=SOFT_GRAY, line_height=42)

    y += 28

    # Body lines
    b_font = load_font(26, bold=False)
    for line in body_lines:
        y = draw_wrapped(draw, line, b_font,
                         x=SAFE + 22, y=y,
                         max_width=W - SAFE * 2 - 30,
                         fill=SOFT_GRAY, line_height=36)
        y += 10

    # CTA box
    cta_y = H - SAFE - 110
    draw_bracket_box(draw, SAFE, cta_y, W - SAFE, H - SAFE)

    cta_font = load_font(26, bold=True)
    draw.text((SAFE + 20, cta_y + 18), cta, font=cta_font, fill=TEAL)

    handle_font = load_mono(22)
    draw.text((SAFE + 20, cta_y + 62), "@opensourcescribes", font=handle_font, fill=SOFT_GRAY)

    draw_accent_bar(draw, y=H - 6)

    path = os.path.join(OUT_DIR, filename)
    img.convert("RGB").save(path, quality=95)
    print(f"✅  Saved: {path}")
    return path


# ── Post Definitions ──────────────────────────────────────────────────────────
POSTS = [
    {
        "filename": "cw_post_01_time_starved.png",
        "headline": "Writing happens in stolen moments.",
        "sub": "Most authors think they just need to hustle harder. Here is what is actually happening.",
        "body": [
            "You are competing against people who treat content creation as their career.",
            "This costs you the one thing you do not have: time.",
            "You cannot fix this by batching more social posts on the weekend.",
        ],
        "cta": "Stop playing the content game.",
    },
    {
        "filename": "cw_post_02_ad_burner.png",
        "headline": "You are burning cash on Amazon ads.",
        "sub": "Most authors think they just need better targeting. Here is what is actually happening.",
        "body": [
            "The entire author marketing economy operates like a slot machine.",
            "You get 50 clicks a day, zero sales, and feel like a mark.",
            "You cannot fix this by tweaking your keywords or raising your daily budget.",
        ],
        "cta": "Stop feeding the machine.",
    },
    {
        "filename": "cw_post_03_performance.png",
        "headline": "Authors want depth, not clout.",
        "sub": "Most authors think they must become content creators to be read. Here is what is actually happening.",
        "body": [
            "You are forced into a performative chase for likes and relevance.",
            "This turns you into someone you do not recognize.",
            "You cannot fix this by hiring a social media manager to post memes for you.",
        ],
        "cta": "Write, don't perform.",
    },
    {
        "filename": "cw_post_04_algorithm.png",
        "headline": "Algorithms don't care about your craft.",
        "sub": "Most authors think they need thicker skin for public criticism. Here is what is actually happening.",
        "body": [
            "Platforms demand volume and punish nuance with bad-faith criticism.",
            "Your book becomes a target instead of an expression.",
            "You cannot fix this by turning off comments or hiding behind a pen name.",
        ],
        "cta": "Protect your work.",
    },
    {
        "filename": "cw_post_05_private_person.png",
        "headline": "Publishing success is not reserved for extroverts.",
        "sub": "Most authors think the game is rigged against introverts and parents. Here is what is actually happening.",
        "body": [
            "The current marketing playbook was built for people with unlimited time and a public persona.",
            "It was not built for parents, introverts, or people with day jobs.",
            "You cannot fix this by forcing yourself to go viral.",
        ],
        "cta": "There is a quieter way.",
    },
]


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    for post in POSTS:
        make_card(
            filename=post["filename"],
            headline=post["headline"],
            sub=post["sub"],
            body_lines=post["body"],
            cta=post["cta"],
        )
    print("\n✅  All 5 Client Whisperer cards generated.")
