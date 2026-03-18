"""
Remotion Overlay Generator for OpenSourceScribes
Generates animated overlays using Remotion CLI to enhance video segments
"""

import os
import re
import json
import subprocess
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Optional
import time

# Configuration
REMOTION_DIR = "remotion_video"
OUTPUT_FOLDER = "assets"
DATA_FILE = "posts_data.json"


class OverlayGenerator:
    """Main class for generating Remotion overlays"""
    
    def __init__(self, remotion_dir: str = REMOTION_DIR):
        self.remotion_dir = remotion_dir
        self.output_folder = OUTPUT_FOLDER
        
    def get_remotion_cli_command(self, overlay_type: str, props: Dict, output_path: str) -> str:
        """Generate Remotion CLI command for overlay rendering"""
        props_json = json.dumps(props)
        return f'cd {self.remotion_dir} && npx remotion render OverlayGenerator --props=\'{props_json}\' --output={output_path}'
    
    def generate_overlay(self, overlay_type: str, props: Dict, output_path: str) -> bool:
        """Generate overlay using Remotion CLI"""
        props_json = json.dumps(props)
        cmd = f'cd {self.remotion_dir} && npx remotion render OverlayGenerator --props=\'{props_json}\' --output={output_path}'
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            elapsed = time.time() - start_time
            
            # Check if output file exists (REMOTION_DIR is relative, so the file is actually in main project dir)
            actual_output = output_path.replace('../', '')
            success = os.path.exists(actual_output)
            
            print(f"  Overlay generated: {output_path} ({elapsed:.1f}s)" if success else f"  Failed: {output_path}")
            return success
        except subprocess.CalledProcessError as e:
            print(f"  Error generating overlay: {e.stderr}")
            return False
    
    def generate_project_overlay(self, project: Dict, duration: float = 8.0, delay: float = 1.0) -> Optional[str]:
        """Generate project information overlay"""
        props = {
            "overlayType": "project",
            "name": project.get('name', ''),
            "url": project.get('url', ''),
            "description": project.get('description', ''),
            "category": project.get('category', 'Development'),
            "lastUpdated": project.get('last_updated', ''),
            "duration": duration,
            "delay": delay
        }
        
        project_id = project.get('id', '')
        output_path = f"../assets/overlay_{project_id}.mp4"
        
        success = self.generate_overlay("project", props, output_path)
        return output_path.replace('../', '') if success else None
    
    def generate_stats_overlay(self, project: Dict, duration: float = 6.0, delay: float = 1.0) -> Optional[str]:
        """Generate statistics overlay"""
        props = {
            "overlayType": "stats",
            "stars": project.get('stars', 0),
            "forks": project.get('forks', 0),
            "issues": project.get('issues', 0),
            "commits": project.get('commits', 0),
            "duration": duration,
            "delay": delay
        }
        
        project_id = project.get('id', '')
        output_path = f"../assets/overlay_{project_id}_stats.mp4"
        
        success = self.generate_overlay("stats", props, output_path)
        return output_path.replace('../', '') if success else None
    
    def generate_combined_overlay(self, project: Dict, duration: float) -> Optional[str]:
        """
        Generate the combined terminal-style overlay for a project segment.
        Renders as webm with VP8 alpha channel so FFmpeg can composite it
        transparently over the Ken Burns background video.

        Args:
            project: Project dict (needs at least id, name, github_url, script_text)
            duration: Segment duration in seconds (must match audio length)

        Returns:
            Path to overlay_{id}.webm, or None on failure
        """
        project_id = project.get('id', 'unknown')
        output_path = f"../assets/overlay_{project_id}.webm"
        actual_output = output_path.replace('../', '')

        # Fetch live GitHub stats
        stats = _fetch_github_stats(project.get('github_url', ''))

        # Extract 3 bullet points from the script narration text
        bullets = _extract_bullets(project.get('script_text', ''))

        props = {
            "overlayType": "combined",
            "name": project.get('name', ''),
            "language": stats.get('language', project.get('language', '')),
            "license": stats.get('license', project.get('license', '')),
            "stars": stats.get('stars', project.get('stars', 0)),
            "forks": stats.get('forks', project.get('forks', 0)),
            "bullet1": bullets[0],
            "bullet2": bullets[1],
            "bullet3": bullets[2],
            "duration": duration,
        }

        props_json = json.dumps(props)
        # vp8 codec → webm with alpha channel transparency
        cmd = (
            f"cd {self.remotion_dir} && npx remotion render OverlayGenerator "
            f"--props='{props_json}' "
            f"--output={output_path} "
            f"--codec=vp8"
        )

        try:
            start_time = time.time()
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            elapsed = time.time() - start_time
            success = os.path.exists(actual_output)
            if success:
                print(f"  Combined overlay: {actual_output} ({elapsed:.1f}s)")
            else:
                print(f"  Combined overlay render failed (file not found): {actual_output}")
            return actual_output if success else None
        except subprocess.CalledProcessError as e:
            print(f"  Combined overlay error: {e.stderr[-300:] if e.stderr else 'unknown'}")
            return None

    def batch_generate_overlays(self, projects: List[Dict], overlay_type: str = 'project') -> Dict[str, str]:
        """Generate overlays for all projects"""
        print(f"\nGenerating {overlay_type} overlays for {len(projects)} projects...")
        results = {}
        
        for i, project in enumerate(projects, 1):
            project_id = project.get('id', '')
            project_name = project.get('name', 'Unknown')
            
            print(f"[{i}/{len(projects)}] {project_name}...")
            
            if overlay_type == 'project':
                result = self.generate_project_overlay(project)
            elif overlay_type == 'stats':
                result = self.generate_stats_overlay(project)
            else:
                result = None
                
            results[project_id] = result
        
        return results


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------

def _fetch_github_stats(github_url: str) -> Dict:
    """
    Fetch stars, forks, language, and license from the GitHub REST API.
    No auth required for public repos (60 req/hour unauthenticated).
    Returns empty dict on any failure so callers degrade gracefully.
    """
    if not github_url:
        return {}
    match = re.match(r'https?://github\.com/([^/]+)/([^/\s]+)', github_url.strip().rstrip('/'))
    if not match:
        return {}
    owner, repo = match.group(1), match.group(2)
    # Strip .git suffix if present
    repo = repo.rstrip('.git') if repo.endswith('.git') else repo
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}",
            timeout=6,
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 200:
            data = resp.json()
            license_info = data.get('license') or {}
            return {
                'stars': data.get('stargazers_count', 0),
                'forks': data.get('forks_count', 0),
                'language': data.get('language') or '',
                'license': license_info.get('spdx_id') or '',
            }
    except Exception:
        pass
    return {}


def _extract_bullets(script_text: str, n: int = 3, max_chars: int = 72) -> List[str]:
    """
    Extract n bullet points from the narration script text.
    Splits on sentence boundaries, picks the first n substantive sentences,
    and truncates each to max_chars with ellipsis.
    """
    if not script_text:
        return ['', '', '']

    # Strip markdown-ish formatting
    cleaned = re.sub(r'\*\*|__|\*|_|#+', '', script_text)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', cleaned.strip())

    bullets: List[str] = []
    for s in sentences:
        s = s.strip()
        # Skip very short fragments and lines that are just headers/labels
        if len(s) < 25 or s.endswith(':'):
            continue
        if len(s) > max_chars:
            s = s[:max_chars - 3].rsplit(' ', 1)[0] + '...'
        bullets.append(s)
        if len(bullets) >= n:
            break

    # Pad to exactly n
    while len(bullets) < n:
        bullets.append('')

    return bullets


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate Remotion overlays for OpenSourceScribes')
    parser.add_argument('--type', type=str, default='project', choices=['project', 'stats'], 
                      help='Type of overlay to generate')
    parser.add_argument('--projects', type=str, default=DATA_FILE, 
                      help='Path to projects JSON file')
    parser.add_argument('--single', type=str, help='Generate overlay for single project ID')
    
    args = parser.parse_args()
    
    # Load project data
    if not os.path.exists(args.projects):
        print(f"Error: Projects file not found: {args.projects}")
        return
    
    with open(args.projects, 'r') as f:
        projects = json.load(f)
    
    # Generate overlays
    generator = OverlayGenerator()
    
    if args.single:
        # Generate overlay for single project
        project = next((p for p in projects if p.get('id') == args.single), None)
        if project:
            print(f"Generating overlay for single project: {project.get('name')}")
            result = generator.generate_project_overlay(project) if args.type == 'project' else generator.generate_stats_overlay(project)
            print(f"Result: {result}")
        else:
            print(f"Error: Project '{args.single}' not found")
    else:
        # Batch generate
        results = generator.batch_generate_overlays(projects, args.type)
        
        # Summary
        successful = sum(1 for r in results.values() if r is not None)
        print(f"\n{'='*60}")
        print(f"OVERLAY GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Successful: {successful}/{len(projects)}")
        print(f"Failed: {len(projects) - successful}")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()