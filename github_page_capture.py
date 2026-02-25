"""
GitHub Page Capture Module
Captures and creates scrolling animations of GitHub repository pages
Focused on key sections: features, code files, issues
"""

import os
import re
import json
import subprocess
import asyncio
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

# Load configuration
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


class GitHubPageCapture:
    """Captures screenshots and creates scrolling animations of GitHub pages"""
    
    def __init__(self, output_dir="assets/github_captures"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Check for browser capture tools
        self.browser_available = self._check_browser_tools()
        
    def _check_browser_tools(self) -> bool:
        """Check if selenium + browser is available"""
        try:
            import selenium
            from selenium import webdriver
            return True
        except ImportError:
            print("⚠️  selenium not installed - will use fallback capture method")
            return False
    
    def capture_github_overview(self, github_url: str, output_path: str = None) -> Optional[str]:
        """Capture scrolling animation of GitHub repository overview"""
        if not output_path:
            project_id = self._get_project_id_from_url(github_url)
            output_path = str(self.output_dir / f"{project_id}_overview_scroll.mp4")
        
        print(f"🎬 Capturing page scroll for: {github_url}")
        
        if self.browser_available:
            return self._capture_with_selenium(github_url, output_path, capture_type='overview')
        else:
            return self._capture_with_webkit2png(github_url, output_path, capture_type='overview')

    def take_screenshot(self, url: str, output_path: str, scroll_to: int = 0) -> bool:
        """Take a single high-quality screenshot of a URL at a specific scroll position"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            import time
            time.sleep(3)
            
            if scroll_to > 0:
                driver.execute_script(f"window.scrollTo(0, {scroll_to});")
                time.sleep(1)
                
            driver.save_screenshot(output_path)
            driver.quit()
            return True
        except Exception as e:
            print(f"❌ Screenshot failed: {e}")
            return False

    def take_multi_screenshots(self, url: str, project_id: str, num_screenshots: int = 3) -> List[str]:
        """Capture multiple points of interest on a page distributed by height"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=options)
            driver.get(url)
            import time
            time.sleep(3)
            
            # Get total height
            total_height = driver.execute_script("return document.body.scrollHeight")
            
            # Distribute points across the page (0% to 80% to avoid potential footer/empty space issues)
            points = []
            if num_screenshots == 1:
                points = [0]
            else:
                for i in range(num_screenshots):
                    # Progress from 0 to 0.8 weight
                    pos = int(total_height * (0.8 * i / (num_screenshots - 1)))
                    points.append(pos)
            
            screenshot_paths = []
            
            for i, pos in enumerate(points):
                driver.execute_script(f"window.scrollTo(0, {pos});")
                time.sleep(1)
                path = str(self.output_dir / f"{project_id}_pos_{i}.png")
                driver.save_screenshot(path)
                screenshot_paths.append(path)
                
            driver.quit()
            return screenshot_paths
        except Exception as e:
            print(f"❌ Multi-screenshot failed: {e}")
            return []
    
    def capture_features_section(self, github_url: str, output_path: str = None) -> Optional[str]:
        """Capture scrolling animation of features section"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = self._get_project_id_from_url(github_url)
            output_path = str(self.output_dir / f"{project_id}_features_scroll.mp4")
        
        print(f"🎬 Capturing features section...")
        
        # Scroll down to features section (typically in README)
        feature_url = f"{github_url}/blob/main/README.md"
        
        if self.browser_available:
            return self._capture_with_selenium(feature_url, output_path, capture_type='README')
        else:
            return self._capture_with_webkit2png(feature_url, output_path, capture_type='README')
    
    def capture_code_files(self, github_url: str, file_paths: List[str], output_path: str = None) -> Optional[str]:
        """
        Capture scrolling animation of code files
        
        Args:
            github_url: GitHub repository URL
            file_paths: List of file paths to capture (e.g., ['src/main.py', 'README.md'])
            output_path: Where to save the video
            
        Returns:
            Path to captured video or None if failed
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = self._get_project_id_from_url(github_url)
            output_path = str(self.output_dir / f"{project_id}_code_scroll.mp4")
        
        print(f"🎬 Capturing code files: {file_paths[:2]}...")
        
        # Capture only first 2 files to keep video length reasonable
        files_to_capture = file_paths[:2]
        
        return self._capture_multiple_pages(github_url, files_to_capture, output_path)
    
    def capture_issues_section(self, github_url: str, output_path: str = None) -> Optional[str]:
        """Capture scrolling animation of issues section"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_id = self._get_project_id_from_url(github_url)
            output_path = str(self.output_dir / f"{project_id}_issues_scroll.mp4")
        
        print(f"🎬 Capturing issues section...")
        
        issues_url = f"{github_url}/issues"
        
        if self.browser_available:
            return self._capture_with_selenium(issues_url, output_path, capture_type='general')
        else:
            return self._capture_with_webkit2png(issues_url, output_path, capture_type='general')
    
    def capture_all_key_sections(self, github_url: str) -> Dict[str, str]:
        """
        Capture all key sections for a GitHub repository
        
        Returns:
            Dictionary mapping section names to video file paths
        """
        project_id = self._get_project_id_from_url(github_url)
        
        print(f"\n🎬 Capturing all key sections for {project_id}...")
        print("="*60)
        
        results = {}
        
        # 1. Overview (main repo page)
        overview = self.capture_github_overview(github_url)
        if overview:
            results['overview'] = overview
        
        # 2. Features (README)
        features = self.capture_features_section(github_url)
        if features:
            results['features'] = features
        
        # 3. Issues
        issues = self.capture_issues_section(github_url)
        if issues:
            results['issues'] = issues
        
        # 4. Try to find a main code file
        # Look at repo data to find typical entry point
        try:
            with open('posts_data.json', 'r') as f:
                projects = json.load(f)
                for project in projects:
                    if project.get('github_url') == github_url:
                        # Find main code file based on language
                        language = project.get('metadata', {}).get('language', '').lower()
                        
                        typical_files = {
                            'python': ['main.py', 'app.py', '__init__.py', 'setup.py'],
                            'javascript': ['index.js', 'app.js', 'src/index.ts'],
                            'rust': ['src/main.rs', 'lib.rs'],
                            'go': ['main.go', 'main_test.go'],
                            'java': ['src/main/java/Main.java', 'Main.java'],
                            'default': ['README.md', 'LICENSE']
                        }
                        
                        files = typical_files.get(language, typical_files['default'])
                        code_video = self.capture_code_files(github_url, files)
                        if code_video:
                            results['code'] = code_video
                        break
        except Exception as e:
            print(f"⚠️  Could not capture code files: {e}")
        
        print("\n" + "="*60)
        print(f"✅ Captured {len(results)} sections")
        print("="*60)
        
        return results
    
    def _get_project_id_from_url(self, url: str) -> str:
        """Extract project ID from any URL"""
        if 'github.com' in url:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
            if match:
                owner, repo = match.groups()
                return f"{owner}_{repo}".replace('-', '_').replace('.', '_')
        
        # Generic URL handling
        clean_url = url.replace('https://', '').replace('http://', '').strip('/')
        parts = clean_url.split('/')
        if len(parts) > 1:
            return parts[-1].replace('-', '_').replace('.', '_')
        return parts[0].replace('.', '_')
    
    def _capture_with_selenium(
        self, 
        url: str, 
        output_path: str, 
        capture_type: str = 'general'
    ) -> Optional[str]:
        """Capture page scroll using Selenium"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            
            # Setup Chrome options
            options = Options()
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            driver = webdriver.Chrome(options=options)
            
            print(f"   Loading page...")
            driver.get(url)
            time.sleep(3)  # Wait for page to load
            
            # Scroll page
            print(f"   Capturing scroll animation...")
            
            # Get page height
            page_height = driver.execute_script("return document.body.scrollHeight")
            viewport_height = 1080
            
            # Capture series of images during scroll
            temp_images = []
            scroll_steps = min(10, int(page_height / viewport_height) + 2)
            
            for i in range(scroll_steps):
                scroll_position = min(i * viewport_height, page_height - viewport_height)
                driver.execute_script(f"window.scrollTo(0, {scroll_position});")
                time.sleep(0.5)
                
                # Capture screenshot
                screenshot_path = f"temp_scroll_{i}.png"
                driver.save_screenshot(screenshot_path)
                temp_images.append(screenshot_path)
            
            driver.quit()
            
            # Create video from images
            return self._images_to_video(temp_images, output_path)
            
        except Exception as e:
            print(f"❌ Selenium capture failed: {e}")
            return None
    
    def _capture_with_webkit2png(
        self, 
        url: str, 
        output_path: str, 
        capture_type: str = 'general'
    ) -> Optional[str]:
        """Fallback: capture screenshots using webkit2png"""
        try:
            # Install webkit2png if not available: brew install webkit2png
            # Capture a series of page scrolls
            temp_images = []
            
            # Capture overview at different scroll positions
            for offset in [0, 500, 1000]:
                img_path = f"temp_scroll_{offset}.png"
                cmd = [
                    'webkit2png',
                    '-F',  # Full size
                    '--clipwidth=1920',
                    '--clipheight=1080',
                    '--clipx=0',
                    f'--clipy={offset}',
                    '-o', img_path,
                    url
                ]
                
                try:
                    subprocess.run(cmd, check=True, capture_output=True)
                    if os.path.exists(img_path):
                        temp_images.append(img_path)
                except:
                    # webkit2png might not be available
                    continue
            
            if temp_images:
                return self._images_to_video(temp_images, output_path)
            else:
                return None
                
        except Exception as e:
            print(f"❌ webkit2png capture failed: {e}")
            return None
    
    def _capture_multiple_pages(
        self, 
        base_url: str, 
        file_paths: List[str], 
        output_path: str
    ) -> Optional[str]:
        """Capture multiple code files as a scrolling sequence"""
        temp_images = []
        
        try:
            owner_repo_match = re.search(r'github\.com/([^/]+)/([^/]+)', base_url)
            if not owner_repo_match:
                return None
            
            owner, repo = owner_repo_match.groups()
            
            for i, file_path in enumerate(file_paths):
                code_url = f"https://github.com/{owner}/{repo}/blob/main/{file_path}"
                img_path = f"temp_code_{i}.png"
                
                print(f"   Capturing: {file_path}")
                
                if self.browser_available:
                    # Use selenium for code files
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    
                    options = Options()
                    options.add_argument('--headless=new')
                    options.add_argument('--window-size=1920,1080')
                    
                    driver = webdriver.Chrome(options=options)
                    driver.get(code_url)
                    time.sleep(2)
                    driver.save_screenshot(img_path)
                    driver.quit()
                else:
                    # Fallback capture
                    try:
                        cmd = ['webkit2png', '-F', '-o', img_path, code_url]
                        subprocess.run(cmd, check=True, capture_output=True)
                    except:
                        continue
                
                if os.path.exists(img_path):
                    temp_images.append(img_path)
            
            if temp_images:
                return self._images_to_video(temp_images, output_path)
            else:
                return None
                
        except Exception as e:
            print(f"❌ Multi-page capture failed: {e}")
            return None
    
    def _images_to_video(self, image_paths: List[str], output_path: str) -> Optional[str]:
        """Convert series of images to scrolling video"""
        try:
            # Create concat list for ffmpeg
            concat_list = "temp_images_concat.txt"
            with open(concat_list, 'w') as f:
                for img in image_paths:
                    f.write(f"file '{img}'\n")
            
            # Create scrolling video
            cmd = [
                'ffmpeg', '-y',
                '-loglevel', 'error',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_list,
                '-framerate', '12',  # Slower framerate for scrolling effect
                '-r', '24',
                '-c:v', 'libx264', '-preset', 'fast',
                '-pix_fmt', 'yuv420p',
                '-filter_complex', 'fps=30,scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                output_path
            ]
            
            subprocess.run(cmd, check=True)
            
            # Cleanup
            for img in image_paths:
                if os.path.exists(img):
                    os.remove(img)
            if os.path.exists(concat_list):
                os.remove(concat_list)
            
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to create video from images: {e}")
            return None


if __name__ == "__main__":
    # Test the capture system
    import argparse
    
    parser = argparse.ArgumentParser(description='Capture GitHub page scrolling animations')
    parser.add_argument('url', help='GitHub repository URL')
    parser.add_argument('--sections', nargs='+', 
                       choices=['all', 'overview', 'features', 'code', 'issues'],
                       default=['all'],
                       help='Sections to capture')
    
    args = parser.parse_args()
    
    capturer = GitHubPageCapture()
    
    if 'all' in args.sections:
        results = capturer.capture_all_key_sections(args.url)
        print("\nCaptured videos:")
        for section, path in results.items():
            print(f"  {section}: {path}")
    else:
        for section in args.sections:
            if section == 'overview':
                path = capturer.capture_github_overview(args.url)
            elif section == 'features':
                path = capturer.capture_features_section(args.url)
            elif section == 'code':
                path = capturer.capture_code_files(args.url, ['README.md'])
            elif section == 'issues':
                path = capturer.capture_issues_section(args.url)
            
            if path:
                print(f"✅ {section}: {path}")
