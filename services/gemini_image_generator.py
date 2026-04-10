"""
Gemini Imagen 3 — Abstract/artistic background image generator
for OpenSourceScribes project segments.

Replaces the static project card with a unique AI-generated image per project.
Visual style: abstract dark tech art (no text, cinematic, dark blue/teal palette).

API key priority:
  1. GEMINI_API_KEY environment variable
  2. config.json > gemini > api_key

Fallback chain on failure:
  project['img_path'] (existing screenshot/card) → None
"""

import os
import json
import re
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

def _load_api_key() -> str:
    key = os.environ.get('GEMINI_API_KEY', '')
    if key:
        return key
    try:
        with open('config.json') as f:
            return json.load(f).get('gemini', {}).get('api_key', '')
    except Exception:
        return ''


GEMINI_API_KEY = _load_api_key()

PROMPT_TEMPLATE = (
    "Abstract dark technology artwork for a software project called \"{name}\". "
    "Theme: {theme}. "
    "Style: cinematic dark background, glowing neon data streams and circuit patterns, "
    "deep space blues and electric teals with bright accent highlights, "
    "flowing particles, abstract code visualization, professional digital art. "
    "No text, no letters, no words, no logos. "
    "Widescreen 16:9 composition. 4K quality. Photorealistic rendering."
)

# Short thematic phrase extracted from the first sentence of the description
_THEME_MAX = 120


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class GeminiImageGenerator:
    """
    Generates abstract/artistic background images via Gemini Imagen 3.
    One image per project, saved to assets/bg_{project_id}.png.
    """

    def __init__(self, output_dir: str = "assets"):
        self.output_dir = output_dir
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        if not GEMINI_API_KEY:
            print("  GeminiImageGen: no API key found — image generation disabled")
            return
        try:
            from google import genai
            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._available = True
        except ImportError:
            print("  GeminiImageGen: google-genai not installed (pip install google-genai) — disabled")
        except Exception as e:
            print(f"  GeminiImageGen: init failed — {e}")

    @property
    def available(self) -> bool:
        return self._available

    def generate_project_image(self, project: dict, fallback_path: Optional[str] = None) -> Optional[str]:
        """
        Generate an abstract background image for the given project.

        Args:
            project: Project dict with at least 'id', 'name', 'script_text'
            fallback_path: Path to return if generation fails (e.g. project['img_path'])

        Returns:
            Path to the generated PNG, or fallback_path on failure.
        """
        project_id = project.get('id', 'unknown')
        output_path = os.path.join(self.output_dir, f"bg_{project_id}.png")

        # Return cached image if already generated this run
        if os.path.exists(output_path):
            return output_path

        if not self._available:
            return fallback_path

        prompt = self._build_prompt(project)

        try:
            from google.genai import types

            response = self._client.models.generate_images(
                model='imagen-3.0-generate-001',
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=1,
                    aspect_ratio='16:9',
                    output_mime_type='image/png',
                    safety_filter_level='block_only_high',
                ),
            )

            if not response.generated_images:
                print(f"  GeminiImageGen: no images returned for {project.get('name')}")
                return fallback_path

            image_data = response.generated_images[0].image
            # image_data is a google.genai.types.Image — save via its .save() or raw bytes
            if hasattr(image_data, 'save'):
                image_data.save(output_path)
            else:
                # Fallback: raw bytes
                raw = getattr(image_data, '_raw_bytes', None) or getattr(image_data, 'data', None)
                if raw:
                    with open(output_path, 'wb') as f:
                        f.write(raw)
                else:
                    print(f"  GeminiImageGen: cannot extract image bytes for {project.get('name')}")
                    return fallback_path

            print(f"  GeminiImageGen: {output_path}")
            return output_path

        except Exception as e:
            print(f"  GeminiImageGen: generation failed for {project.get('name')} — {e}")
            return fallback_path

    # ---------------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------------

    def _build_prompt(self, project: dict) -> str:
        name = project.get('name', 'software project')
        script = project.get('script_text', '')

        # Pull a thematic phrase from the first sentence of the description
        first_sentence = re.split(r'(?<=[.!?])\s', script.strip())[0] if script else ''
        # Keep nouns/concepts, drop common filler
        theme = first_sentence[:_THEME_MAX].strip() if first_sentence else name

        return PROMPT_TEMPLATE.format(name=name, theme=theme)


# ---------------------------------------------------------------------------
# Module-level convenience — matches the pattern used by other generators
# ---------------------------------------------------------------------------

_default_generator: Optional[GeminiImageGenerator] = None


def get_gemini_generator() -> GeminiImageGenerator:
    global _default_generator
    if _default_generator is None:
        _default_generator = GeminiImageGenerator()
    return _default_generator


def generate_project_image(project: dict, fallback_path: Optional[str] = None) -> Optional[str]:
    """Module-level convenience wrapper."""
    return get_gemini_generator().generate_project_image(project, fallback_path)


# ---------------------------------------------------------------------------
# CLI test
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import sys
    test_project = {
        'id': 'test_project',
        'name': sys.argv[1] if len(sys.argv) > 1 else 'TestProject',
        'script_text': (
            sys.argv[2] if len(sys.argv) > 2
            else 'A powerful open-source tool for developers that automates complex workflows.'
        ),
    }
    result = generate_project_image(test_project)
    if result:
        print(f"Generated: {result}")
    else:
        print("Generation failed or no API key configured.")
