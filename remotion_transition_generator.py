"""
Remotion Transition Generator for OpenSourceScribes
Generates transition clips using Remotion CLI for smooth video transitions
"""

import os
import json
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import time

# Configuration
REMOTION_DIR = "remotion_video"
TRANSITIONS_DIR = "assets/transitions"


class TransitionGenerator:
    """Main class for generating Remotion transitions"""
    
    def __init__(self, remotion_dir: str = REMOTION_DIR):
        self.remotion_dir = remotion_dir
        self.transitions_dir = TRANSITIONS_DIR
        
        # Ensure output directory exists
        os.makedirs(self.transitions_dir, exist_ok=True)
    
    def _normalize_audio(self, video_path: str) -> bool:
        """Normalize audio to mono 48kHz to match segment audio format.
        This prevents FFmpeg concat from extending video duration."""
        tmp_path = video_path.replace('.mp4', '_normalized.mp4')
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-c:v', 'copy',  # Keep video as-is
            '-af', 'aformat=channel_layouts=mono:sample_rates=48000',  # Mono 48kHz
            '-c:a', 'aac',
            tmp_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            os.replace(tmp_path, video_path)
            return True
        except Exception as e:
            print(f"  Warning: Audio normalization failed: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False
    
    def _normalize_timestamps(self, video_path: str) -> bool:
        """Re-encode to fix DTS (Decoding Time Stamp) discontinuity.
        Remotion outputs can have timestamps that cause FFmpeg concat to extend video."""
        tmp_path = video_path.replace('.mp4', '_ts_fixed.mp4')
        cmd = [
            'ffmpeg', '-y', '-i', video_path,
            '-c:v', 'libx264', '-preset', 'ultrafast',
            '-c:a', 'aac',
            '-fflags', '+bitexact',
            '-map_metadata', '-1',  # Remove metadata for clean timestamps
            tmp_path
        ]
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            os.replace(tmp_path, video_path)
            return True
        except Exception as e:
            print(f"  Warning: Timestamp normalization failed: {e}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False
    
    def get_remotion_cli_command(self, props: Dict, output_path: str) -> str:
        """Generate Remotion CLI command for transition rendering"""
        props_json = json.dumps(props)
        return f'cd {self.remotion_dir} && npx remotion render TransitionGenerator --props=\'{props_json}\' --output={output_path}'
    
    def generate_transition(self, transition_type: str, duration: float, **kwargs) -> bool:
        """Generate transition using Remotion CLI"""
        props = {
            "transitionType": transition_type,
            "duration": duration,
            "overlayColor": kwargs.get('overlay_color', '#1a1a2e'),
        }
        
        # Add type-specific props
        if transition_type == 'wipe':
            props['direction'] = kwargs.get('direction', 'left')
        elif transition_type == 'zoom':
            props['zoomIn'] = kwargs.get('zoom_in', True)
        elif transition_type == 'loader':
            props['textColor'] = kwargs.get('text_color', '#ffffff')
        
        output_filename = f"{transition_type}_{duration}s"
        if transition_type == 'wipe':
            output_filename += f"_{props['direction']}"
        if transition_type == 'zoom':
            output_filename += f"_{'in' if props['zoomIn'] else 'out'}"
        
        output_filename += ".mp4"
        output_path = f"../{self.transitions_dir}/{output_filename}"
        
        props_json = json.dumps(props)
        cmd = f'cd {self.remotion_dir} && npx remotion render TransitionGenerator --props=\'{props_json}\' --output={output_path}'
        
        try:
            start_time = time.time()
            result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
            elapsed = time.time() - start_time
            
            # Check if output file exists
            actual_output = output_path.replace('../', '')
            success = os.path.exists(actual_output)
            
            # Normalize audio to mono 48kHz to match segment audio format
            if success:
                self._normalize_audio(actual_output)
                self._normalize_timestamps(actual_output)
            
            print(f"  Transition generated: {output_filename} ({elapsed:.1f}s)" if success else f"  Failed: {output_filename}")
            return success
        except subprocess.CalledProcessError as e:
            print(f"  Error generating transition: {e.stderr}")
            return False
    
    def batch_generate_transitions(self) -> Dict[str, List[str]]:
        """Generate a library of transitions"""
        results = {
            'wipe': [],
            'zoom': [],
            'dissolve': [],
            'loader': []
        }
        
        print(f"\nGenerating transition library in {self.transitions_dir}/")
        
        # Wipe transitions
        print("\nGenerating wipe transitions...")
        for duration in [0.5, 1.0, 1.5]:
            for direction in ['left', 'right', 'up', 'down']:
                filename = f"wipe_{duration}s_{direction}.mp4"
                success = self.generate_transition('wipe', duration, direction=direction)
                if success:
                    results['wipe'].append(f"{self.transitions_dir}/{filename}")
        
        # Zoom transitions
        print("\nGenerating zoom transitions...")
        for duration in [0.8, 1.2]:
            for zoom_in in [True, False]:
                filename = f"zoom_{duration}s_{'in' if zoom_in else 'out'}.mp4"
                success = self.generate_transition('zoom', duration, zoom_in=zoom_in)
                if success:
                    results['zoom'].append(f"{self.transitions_dir}/{filename}")
        
        # Dissolve transitions
        print("\nGenerating dissolve transitions...")
        for duration in [0.6, 1.0, 1.4]:
            filename = f"dissolve_{duration}s.mp4"
            success = self.generate_transition('dissolve', duration)
            if success:
                results['dissolve'].append(f"{self.transitions_dir}/{filename}")
        
        # Loader transitions
        print("\nGenerating loader transitions...")
        for duration in [0.8, 1.2, 1.6]:
            filename = f"loader_{duration}s.mp4"
            success = self.generate_transition('loader', duration)
            if success:
                results['loader'].append(f"{self.transitions_dir}/{filename}")
        
        return results
    
    def select_transition(self, project_index: int, total_projects: int, segment_duration: float) -> Optional[str]:
        """Select appropriate transition based on context"""
        import random
        
        # Determine transition type based on position
        if project_index % 3 == 0:
            # Every 3rd transition, use loader for variety
            transition_type = 'loader'
        elif segment_duration < 5:
            # Short segments get quick wipes
            transition_type = 'wipe'
        elif segment_duration > 10:
            # Long segments can handle dissolve
            transition_type = 'dissolve'
        else:
            # Default to wipe with zoom mixed in
            transition_type = random.choice(['wipe', 'zoom'])
        
        # Get available transitions of selected type
        matching_files = [
            f for f in os.listdir(self.transitions_dir)
            if f.startswith(transition_type) and f.endswith('.mp4')
        ]
        
        if matching_files:
            return random.choice(matching_files)
        
        # Fallback to default
        default_file = f"wipe_1.0s_left.mp4"
        if os.path.exists(os.path.join(self.transitions_dir, default_file)):
            return default_file
        
        return None


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Generate Remotion transitions for OpenSourceScribes')
    parser.add_argument('--type', type=str, 
                      choices=['wipe', 'zoom', 'dissolve', 'loader'],
                      help='Type of transition to generate (default: batch generate all)')
    parser.add_argument('--duration', type=float, default=1.0,
                      help='Transition duration in seconds')
    parser.add_argument('--batch', action='store_true', default=True,
                      help='Batch generate all transitions (default: True)')
    
    args = parser.parse_args()
    
    generator = TransitionGenerator()
    
    if args.type:
        # Generate single transition type
        print(f"Generating {args.type} transitions...")
        if args.type == 'wipe':
            for direction in ['left', 'right', 'up', 'down']:
                generator.generate_transition(args.type, args.duration, direction=direction)
        elif args.type == 'zoom':
            for zoom_in in [True, False]:
                generator.generate_transition(args.type, args.duration, zoom_in=zoom_in)
        else:
            generator.generate_transition(args.type, args.duration)
    elif args.batch:
        # Batch generate all transitions
        results = generator.batch_generate_transitions()
        
        # Summary
        total_generated = sum(len(files) for files in results.values())
        print(f"\n{'='*60}")
        print(f"TRANSITION GENERATION COMPLETE")
        print(f"{'='*60}")
        for trans_type, files in results.items():
            print(f"{trans_type}: {len(files)} transitions")
        print(f"Total: {total_generated} transitions")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
