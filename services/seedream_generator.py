#!/usr/bin/env python3
"""
Seedream 5 Image Generator for OpenSourceScribes
Generates cinematic background images per segment using WaveSpeedAI API.

Replaces: minimax_integration.py, Gemini image generation calls
"""

import json
import os
import time
import hashlib
import requests
from pathlib import Path
from typing import Dict, Optional


class SeedreamGenerator:
    """
    Wrapper for WaveSpeedAI Seedream 5 API.
    Generates high-quality background images with local caching.
    """
    
    DEFAULT_WIDTH = 1920
    DEFAULT_HEIGHT = 1080
    POLL_INTERVAL = 15
    MAX_POLL_ATTEMPTS = 20

    def __init__(self, config: Optional[Dict] = None):
        if config is None:
            with open('config.json', 'r') as f:
                self.config = json.load(f)
        else:
            self.config = config

        ws = self.config.get('wavespeed', {})
        self.api_key = ws.get('api_key')
        if not self.api_key:
            raise ValueError("wavespeed.api_key not found in config.json")

        api_base = ws.get('api_base', 'https://api.wavespeed.ai/api/v3')
        self.model = ws.get('seedream_model', 'bytedance/seedream-v5.0-lite')
        self.API_ENDPOINT = f"{api_base}/{self.model}"
        self.output_dir = Path(ws.get('output_dir', 'assets/wavespeed'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, project: Dict) -> str:
        """
        Generate a cache key for a project.
        
        Args:
            project: Project dict with name, description, etc.
            
        Returns:
            Cache key string
        """
        # Use a combination of repo full name and description
        cache_data = {
            'name': project.get('name', ''),
            'description': project.get('description', ''),
            'language': project.get('language', ''),
        }
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _get_cache_path(self, project: Dict) -> Path:
        """
        Get the cached image path for a project.
        
        Args:
            project: Project dict
            
        Returns:
            Path to cached image
        """
        cache_key = self._get_cache_key(project)
        return self.output_dir / f"{cache_key}_seedream.png"
    
    def _build_prompt(self, project: Dict) -> str:
        """
        Build a cinematic prompt for Seedream 5.
        
        Args:
            project: Project dict with name, description, languages, topics
            
        Returns:
            Prompt string
        """
        name = project.get('name', 'Unknown')
        description = project.get('description', '')
        language = project.get('language', '')
        topics = project.get('topics', [])
        
        # Build abstract tech prompt — no figurative elements
        tech_context = description[:120] if description else name
        lang_hint = f"{language} " if language else ""
        topic_hint = ', '.join(topics[:3]) + ' ' if topics else ''

        prompt = (
            f"Abstract {lang_hint}technology visualization: {tech_context}. "
            f"{topic_hint}"
            "Dark deep-space aesthetic, electric blues and purples, glowing data streams, "
            "floating geometric nodes, circuit lattice patterns, particle networks, "
            "volumetric light rays through dark void. "
            "Completely abstract — no people, no characters, no humans, no faces, "
            "no astronauts, no suits, no animals, no figures of any kind. "
            "Pure abstract digital art only. No text, no logos, no UI. "
            "Cinematic 4K quality."
        )
        
        return prompt
    
    def _submit_generation_request(self, prompt: str) -> Dict:
        """
        Submit a generation request to Seedream 5 API.
        
        Args:
            prompt: The image generation prompt
            
        Returns:
            API response with task ID
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "width": self.DEFAULT_WIDTH,
            "height": self.DEFAULT_HEIGHT,
        }

        response = requests.post(self.API_ENDPOINT, headers=headers, json=payload)
        if not response.ok:
            print(f"  ✗ Seedream API error {response.status_code}: {response.text[:300]}")
        response.raise_for_status()

        # Response shape: {"code":200, "data": {"id": "...", "urls": {"get": "..."}, ...}}
        return response.json().get('data', {})

    def _poll_task_status(self, poll_url: str) -> Dict:
        """Poll the result URL until succeeded/failed or timeout."""
        headers = {"Authorization": f"Bearer {self.api_key}"}

        for attempt in range(self.MAX_POLL_ATTEMPTS):
            try:
                response = requests.get(poll_url, headers=headers)
                response.raise_for_status()
                data = response.json().get('data', {})

                status = data.get('status', '').lower()

                if status in ('succeeded', 'completed'):
                    return data
                elif status == 'failed':
                    raise RuntimeError(f"Seedream generation failed: {data.get('error', 'Unknown error')}")

                print(f"  Polling ({attempt + 1}/{self.MAX_POLL_ATTEMPTS}): status={status}")
                time.sleep(self.POLL_INTERVAL)

            except requests.RequestException as e:
                if attempt == self.MAX_POLL_ATTEMPTS - 1:
                    raise
                print(f"  Poll attempt {attempt + 1} failed: {e}")
                time.sleep(self.POLL_INTERVAL)

        raise TimeoutError(f"Seedream generation timeout after {self.MAX_POLL_ATTEMPTS} attempts")
    
    def _download_image(self, image_url: str, output_path: Path):
        """
        Download the generated image to local cache.
        
        Args:
            image_url: URL of generated image
            output_path: Local path to save image
        """
        response = requests.get(image_url, stream=True)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
    
    def generate(self, project: Dict, force_refresh: bool = False) -> Path:
        """
        Generate or retrieve a cached Seedream image for a project.
        
        Args:
            project: Project dict with name, description, topics, etc.
            force_refresh: Force regeneration even if cached
            
        Returns:
            Path to generated/cached image
        """
        cache_path = self._get_cache_path(project)
        
        # Check cache
        if not force_refresh and cache_path.exists():
            print(f"  Using cached image: {cache_path.name}")
            return cache_path
        
        # Generate new image
        print(f"  Generating Seedream 5 image for {project.get('name', 'Unknown')}...")
        
        try:
            # Build prompt
            prompt = self._build_prompt(project)
            
            # Submit request
            print("  Submitting to Seedream 5 API...")
            submit_response = self._submit_generation_request(prompt)
            task_id = submit_response.get('id')
            poll_url = submit_response.get('urls', {}).get('get')

            if not task_id or not poll_url:
                raise RuntimeError(f"Unexpected API response: {submit_response}")

            # Poll for completion
            print("  Waiting for generation...")
            result = self._poll_task_status(poll_url)

            # outputs is a list of image URLs (strings)
            outputs = result.get('outputs', [])
            if not outputs:
                raise RuntimeError("No outputs in API response")

            image_url = outputs[0] if isinstance(outputs[0], str) else outputs[0].get('url')
            if not image_url:
                raise RuntimeError("No image URL in API response")
            
            # Download image
            print(f"  Downloading image to {cache_path.name}...")
            self._download_image(image_url, cache_path)
            
            print("  ✓ Image generated successfully")
            return cache_path
            
        except Exception as e:
            print(f"  ✗ Seedream generation failed: {e}")
            raise


def demo():
    """Demo function to test Seedream generator."""
    print("Seedream 5 Generator Demo")
    print("=" * 60)
    
    mock_project = {
        'name': 'openclaw/openclaw',
        'description': 'Your own personal AI assistant. Any OS. Any Platform. The lobster way.',
        'language': 'TypeScript',
        'topics': ['ai', 'assistant', 'crustacean', 'molty'],
    }
    
    try:
        generator = SeedreamGenerator()
        image_path = generator.generate(mock_project)
        
        print(f"\nGenerated image: {image_path}")
        print(f"Image exists: {image_path.exists()}")
        
    except Exception as e:
        print(f"\nDemo failed: {e}")
        print("\nRequirements:")
        print("1. Set wavespeed.api_key in config.json")
        print("2. Install requests: pip install requests")


if __name__ == "__main__":
    demo()
