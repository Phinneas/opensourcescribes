"""
OpenSourceScribes — Social Template Generator
Generates 3 branded Instagram/Threads template images:
  1. Client Whisperer (Pillar 1) — teal accent
  2. Exposé (Pillar 2) — red accent
  3. Educational (Pillar 3) — green accent
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ── Brand Colors ──────────────────────────────────────────────────────────────
DEEP_NAVY     = (10, 22, 40)       # #0a1628
DARK_GRAY     = (26, 26, 46)       # #1a1a2e
TEAL          = (64, 224, 208)     # #40E0D0  — Pillar 1
RED           = (230, 57, 70)      # #e63946  — Pillar 2
GREEN         = (0, 255, 65)       # #00FF41  — Pillar 3
WHITE         = (255, 255, 255)
SOFT_GRAY     = (204, 204, 204)
DARK_TEAL     = (20, 80, 75)       # subtle teal for grid lines
DARK_RED      = (90, 20, 25)
DARK_GREEN    = (0, 80, 20)

# ── Canvas ────────────────────────────────────────────────────────────────────
W, H = 1080, 1080
SAFE = 72  # safe zone inset

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
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return load_font(size, bold=True)

# ── Helpers ───────────────────────────────────────────────────────────────────
def draw_grid(draw, color, alpha=30, spacing=60):
    """Subtle background grid."""
    r, g, b = color
    line_color = (r, g, b, alpha)
    for x in range(0, W, spacing):
        draw.line([(x, 0), (x, H)], fill=line_color, width=1)
    for y in range(0, H, spacing):
        draw.line([(0, y), (W, y)], fill=line_color, width=1)

def draw_accent_bar(draw, accent, y=0, thickness=6):
    """Full-width horizontal accent bar."""
    draw.rectangle([(0, y), (W, y + thickness)], fill=accent)

def draw_left_rule(draw, accent, x=SAFE, y_start=160, y_end=None, thickness=4):
    """Vertical left rule for content block."""
    if y_end is None:
        y_end = H - SAFE - 120
    draw.rectangle([(x, y_start), (x + thickness, y_end)], fill=accent)

def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width pixels."""
    words = text.split()
    lines = []
    current = []
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
    """Draw wrapped text, return final y."""
    lines = wrap_text(text, font, max_width, draw)
    if line_height is None:
        bbox = draw.textbbox((0, 0), "Ag", font=font)
        line_height = (bbox[3] - bbox[1]) + 10
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += line_height
    return y

def draw_pill(draw, text, font, x, y, accent, text_color=None):
    """Draw a rounded pill label."""
    if text_color is None:
        text_color = DEEP_NAVY
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 18, 10
    rx0 = x
    ry0 = y
    rx1 = x + tw + pad_x * 2
    ry1 = y + th + pad_y * 2
    draw.rounded_rectangle([rx0, ry0, rx1, ry1], radius=8, fill=accent)
    draw.text((rx0 + pad_x, ry0 + pad_y), text, font=font, fill=text_color)
    return rx1  # returns right edge for chaining

def draw_bracket_box(draw, x0, y0, x1, y1, accent, thickness=2):
    """Draw corner-bracket style box (not solid border)."""
    corner = 28
    # top-left
    draw.line([(x0, y0), (x0 + corner, y0)], fill=accent, width=thickness)
    draw.line([(x0, y0), (x0, y0 + corner)], fill=accent, width=thickness)
    # top-right
    draw.line([(x1, y0), (x1 - corner, y0)], fill=accent, width=thickness)
    draw.line([(x1, y0), (x1, y0 + corner)], fill=accent, width=thickness)
    # bottom-left
    draw.line([(x0, y1), (x0 + corner, y1)], fill=accent, width=thickness)
    draw.line([(x0, y1), (x0, y1 - corner)], fill=accent, width=thickness)
    # bottom-right
    draw.line([(x1, y1), (x1 - corner, y1)], fill=accent, width=thickness)
    draw.line([(x1, y1), (x1, y1 - corner)], fill=accent, width=thickness)

# ── Template 1: Client Whisperer (Pillar 1 — Teal) ───────────────────────────
def make_client_whisperer():
    img = Image.new("RGBA", (W, H), DEEP_NAVY + (255,))
    draw = ImageDraw.Draw(img)

    # Grid
    draw_grid(draw, TEAL, alpha=18, spacing=54)

    # Top accent bar
    draw_accent_bar(draw, TEAL, y=0, thickness=6)

    # Pillar tag
    tag_font = load_mono(22)
    draw.text((SAFE, 28), "// PILLAR 01  ·  CLIENT WHISPERER", font=tag_font, fill=TEAL)

    # Left rule
    draw_left_rule(draw, TEAL, x=SAFE, y_start=160, y_end=H - SAFE - 130)

    # Pain hook headline
    headline_font = load_font(68, bold=True)
    sub_font = load_font(34, bold=False)
    body_font = load_font(28, bold=False)
    label_font = load_mono(20)

    hook_text = "[AUTHOR PAIN POINT IN ONE LINE]"
    y = draw_wrapped(draw, hook_text, headline_font,
                     x=SAFE + 22, y=165,
                     max_width=W - SAFE * 2 - 30,
                     fill=WHITE, line_height=78)

    y += 24
    # Sub-claim
    sub_text = "Most authors don't realize [specific problem]. Here's what's actually happening."
    y = draw_wrapped(draw, sub_text, sub_font,
                     x=SAFE + 22, y=y,
                     max_width=W - SAFE * 2 - 30,
                     fill=SOFT_GRAY, line_height=44)

    y += 32
    # Body copy block
    body_text = "[Concrete observation about the author's situation. One sentence. Name the specific thing.]\n\n[Second observation — what it costs them. Specific, not abstract.]"
    for para in body_text.split("\n\n"):
        y = draw_wrapped(draw, para.strip(), body_font,
                         x=SAFE + 22, y=y,
                         max_width=W - SAFE * 2 - 30,
                         fill=SOFT_GRAY, line_height=38)
        y += 16

    # Bracket box around CTA area
    cta_y = H - SAFE - 110
    draw_bracket_box(draw, SAFE, cta_y, W - SAFE, H - SAFE, TEAL, thickness=2)

    # CTA text
    cta_font = load_font(26, bold=True)
    cta_text = "[CTA — what they should do next]"
    draw.text((SAFE + 20, cta_y + 18), cta_text, font=cta_font, fill=TEAL)

    # Handle
    handle_font = load_mono(22)
    draw.text((SAFE + 20, cta_y + 62), "@opensourcescribes", font=handle_font, fill=SOFT_GRAY)

    # Bottom accent bar
    draw_accent_bar(draw, TEAL, y=H - 6, thickness=6)

    path = os.path.join(OUT_DIR, "template_01_client_whisperer.png")
    img.convert("RGB").save(path, quality=95)
    print(f"✅  Saved: {path}")
    return path


# ── Template 2: Exposé (Pillar 2 — Red) ──────────────────────────────────────
def make_expose():
    img = Image.new("RGBA", (W, H), DEEP_NAVY + (255,))
    draw = ImageDraw.Draw(img)

    # Grid
    draw_grid(draw, RED, alpha=14, spacing=54)

    # Top accent bar
    draw_accent_bar(draw, RED, y=0, thickness=6)

    # Pillar tag
    tag_font = load_mono(22)
    draw.text((SAFE, 28), "// PILLAR 02  ·  EXPOSÉ", font=tag_font, fill=RED)

    # Tension bar — diagonal stripe block top-right
    # Simple: filled rectangle in dark red, top-right corner
    draw.rectangle([(W - 180, 0), (W, 90)], fill=(60, 10, 15, 200))
    insider_font = load_mono(18)
    draw.text((W - 162, 32), "INSIDER", font=insider_font, fill=RED)

    # Left rule
    draw_left_rule(draw, RED, x=SAFE, y_start=160, y_end=H - SAFE - 130)

    headline_font = load_font(68, bold=True)
    sub_font = load_font(34, bold=False)
    body_font = load_font(28, bold=False)
    label_font = load_mono(20)

    # Tension headline
    hook_text = "What [industry] doesn't want you to know about [topic]."
    y = draw_wrapped(draw, hook_text, headline_font,
                     x=SAFE + 22, y=165,
                     max_width=W - SAFE * 2 - 30,
                     fill=WHITE, line_height=78)

    y += 24
    # Sub-claim
    sub_text = "[The specific thing that is hidden, misrepresented, or actively obscured.]"
    y = draw_wrapped(draw, sub_text, sub_font,
                     x=SAFE + 22, y=y,
                     max_width=W - SAFE * 2 - 30,
                     fill=SOFT_GRAY, line_height=44)

    y += 32
    # Evidence block — 3 short claims
    claims = [
        "① [Specific fact or stat that proves the claim]",
        "② [Second piece of evidence — name the source or mechanism]",
        "③ [Third point — the implication for the reader]",
    ]
    claim_font = load_font(26, bold=False)
    for claim in claims:
        y = draw_wrapped(draw, claim, claim_font,
                         x=SAFE + 22, y=y,
                         max_width=W - SAFE * 2 - 30,
                         fill=SOFT_GRAY, line_height=38)
        y += 12

    # Bracket box around CTA area
    cta_y = H - SAFE - 110
    draw_bracket_box(draw, SAFE, cta_y, W - SAFE, H - SAFE, RED, thickness=2)

    cta_font = load_font(26, bold=True)
    cta_text = "[Thread continues ↓ / Save this]"
    draw.text((SAFE + 20, cta_y + 18), cta_text, font=cta_font, fill=RED)

    handle_font = load_mono(22)
    draw.text((SAFE + 20, cta_y + 62), "@opensourcescribes", font=handle_font, fill=SOFT_GRAY)

    # Bottom accent bar
    draw_accent_bar(draw, RED, y=H - 6, thickness=6)

    path = os.path.join(OUT_DIR, "template_02_expose.png")
    img.convert("RGB").save(path, quality=95)
    print(f"✅  Saved: {path}")
    return path


# ── Template 3: Educational (Pillar 3 — Green) ───────────────────────────────
def make_educational():
    img = Image.new("RGBA", (W, H), DEEP_NAVY + (255,))
    draw = ImageDraw.Draw(img)

    # Grid
    draw_grid(draw, GREEN, alpha=14, spacing=54)

    # Top accent bar
    draw_accent_bar(draw, GREEN, y=0, thickness=6)

    # Pillar tag
    tag_font = load_mono(22)
    draw.text((SAFE, 28), "// PILLAR 03  ·  EDUCATIONAL", font=tag_font, fill=GREEN)

    # Left rule
    draw_left_rule(draw, GREEN, x=SAFE, y_start=160, y_end=H - SAFE - 130)

    headline_font = load_font(68, bold=True)
    sub_font = load_font(34, bold=False)
    body_font = load_font(28, bold=False)
    step_font = load_font(26, bold=True)
    label_font = load_mono(20)

    # Lesson headline
    hook_text = "How [specific thing] works on an author website."
    y = draw_wrapped(draw, hook_text, headline_font,
                     x=SAFE + 22, y=165,
                     max_width=W - SAFE * 2 - 30,
                     fill=WHITE, line_height=78)

    y += 24
    # Sub-claim
    sub_text = "[One sentence: what the reader will understand or be able to do after this post.]"
    y = draw_wrapped(draw, sub_text, sub_font,
                     x=SAFE + 22, y=y,
                     max_width=W - SAFE * 2 - 30,
                     fill=SOFT_GRAY, line_height=44)

    y += 32
    # Numbered steps / concepts
    steps = [
        "① [Step or concept — concrete, named specifically]",
        "② [Second step — what it does, not what it 'enables']",
        "③ [Third step — the outcome or result]",
    ]
    for step in steps:
        # Green dot marker
        dot_x = SAFE + 22
        bbox = draw.textbbox((0, 0), "Ag", font=step_font)
        dot_r = (bbox[3] - bbox[1]) // 2
        draw_wrapped(draw, step, step_font,
                     x=dot_x, y=y,
                     max_width=W - SAFE * 2 - 30,
                     fill=WHITE, line_height=38)
        y += 50

    # Bracket box around CTA area
    cta_y = H - SAFE - 110
    draw_bracket_box(draw, SAFE, cta_y, W - SAFE, H - SAFE, GREEN, thickness=2)

    cta_font = load_font(26, bold=True)
    cta_text = "[Save / share if this helped]"
    draw.text((SAFE + 20, cta_y + 18), cta_text, font=cta_font, fill=GREEN)

    handle_font = load_mono(22)
    draw.text((SAFE + 20, cta_y + 62), "@opensourcescribes", font=handle_font, fill=SOFT_GRAY)

    # Bottom accent bar
    draw_accent_bar(draw, GREEN, y=H - 6, thickness=6)

    path = os.path.join(OUT_DIR, "template_03_educational.png")
    img.convert("RGB").save(path, quality=95)
    print(f"✅  Saved: {path}")
    return path


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs(OUT_DIR, exist_ok=True)
    make_client_whisperer()
    make_expose()
    make_educational()
    print("\n✅  All 3 templates generated.")
