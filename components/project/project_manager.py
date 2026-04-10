"""
Project Manager - Concrete implementation of IProjectProvider
Handles loading, filtering, and selecting projects from various sources.
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Optional

from interfaces.interfaces import IProjectProvider, IDatabaseClient


class ProjectManager(IProjectProvider):
    """
    Manages project data - loading, selection, and persistence.
    
    SOLID Compliance:
    ✅ SRP: Only manages project data lifecycle
    ✅ DIP: Depends on IDatabaseClient abstraction
    ✅ OCP: Can add new data sources without modification
    ✅ LSP: Can be substituted with any IProjectProvider
    ✅ ISP: Implements only IProjectProvider methods
    """
    
    def __init__(
        self,
        database_client: Optional[IDatabaseClient] = None,
        data_file: str = "posts_data.json",
        max_deep_dives: int = 3
    ):
        """
        Constructor injection - all dependencies explicitly provided.
        
        Args:
            database_client: Optional database for persistence
            data_file: Path to JSON file containing projects
            max_deep_dives: Maximum number of deep dive projects to select
        """
        self.database_client = database_client
        self.data_file = data_file
        self.max_deep_dives = max_deep_dives
        self.projects: List[Dict] = []
        self.shorts_selection: List[Dict] = []
        self.deep_dive_selection: List[Dict] = []
    
    def load_projects(self) -> List[Dict]:
        """
        Load projects from JSON file.
        
        Dependency Flow:
        1. Try to load from JSON file
        2. Ensure all projects have IDs
        3. Store in memory for later use
        
        Returns:
            List of project dictionaries
        """
        try:
            with open(self.data_file, 'r') as f:
                self.projects = json.load(f)
            
            print(f"✅ Loaded {len(self.projects)} projects from {self.data_file}")
            
            # Ensure IDs
            for i, project in enumerate(self.projects):
                if 'id' not in project:
                    project['id'] = f"p{i+1}"
            
            return self.projects
            
        except FileNotFoundError:
            print(f"❌ Error: {self.data_file} not found. Run auto_script_generator.py first.")
            self.projects = []
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON in {self.data_file}: {e}")
            self.projects = []
            return []
    
    def get_project_by_id(self, project_id: str) -> Optional[Dict]:
        """
        Get a specific project by ID.
        
        Args:
            project_id: Unique identifier for project
            
        Returns:
            Project dictionary or None if not found
        """
        for project in self.projects:
            if project.get('id') == project_id:
                return project
        return None
    
    def auto_select_shorts_and_deep_dives(self) -> tuple:
        """
        Automatically select projects for Shorts and Deep Dives.
        
        Selection Strategy:
        - Shorts: ALL projects
        - Deep Dives: Random selection up to max_deep_dives
        
        Returns:
            Tuple of (shorts_selection, deep_dive_selection)
        """
        print("\n" + "="*60)
        print("🤖 AUTOMATIC SELECTION")
        print("="*60)
        
        # Shorts: Select ALL
        self.shorts_selection = self.projects
        print(f"✅ Selected ALL {len(self.projects)} projects for Shorts")
        
        # Deep Dives: Randomly select
        if len(self.projects) <= self.max_deep_dives:
            self.deep_dive_selection = self.projects
        else:
            self.deep_dive_selection = random.sample(self.projects, self.max_deep_dives)
        
        print(f"✅ Selected {len(self.deep_dive_selection)} random projects for Deep Dives:")
        for project in self.deep_dive_selection:
            print(f"   - {project['name']}")
        
        return self.shorts_selection, self.deep_dive_selection
    
    def mark_published(self, projects: List[Dict]) -> None:
        """
        Mark projects as published to avoid re-discovery.
        
        Dependency Flow:
        1. Use database client if available (preferred)
        2. Fall back to text file if no database
        
        Args:
            projects: List of projects to mark as published
        """
        urls = [p.get("github_url") for p in projects if p.get("github_url")]
        
        if not urls:
            return
        
        # Primary: Use database client
        if self.database_client:
            try:
                for project in projects:
                    url = project.get("github_url")
                    if not url:
                        continue
                    
                    self.database_client.mark_published(url, {
                        "name": project.get("name", ""),
                        "description": project.get("description", ""),
                        "stars": project.get("stars"),
                        "forks": project.get("forks"),
                        "language": project.get("language", ""),
                        "topics": project.get("topics", []),
                    })
                
                print(f"📋 Marked {len(urls)} repo(s) as published in database")
                return
            except Exception as e:
                print(f"[database] Warning: Database write failed ({e}), using file fallback")
        
        # Fallback: Plain text file
        seen_file = "published_repos.txt"
        existing: set = set()
        
        if Path(seen_file).exists():
            with open(seen_file, "r") as f:
                existing = {line.strip() for line in f if line.strip()}
        
        new_urls = [url for url in urls if url not in existing]
        
        if new_urls:
            with open(seen_file, "a") as f:
                for url in new_urls:
                    f.write(url + "\n")
            print(f"📋 Marked {len(new_urls)} repo(s) as published in {seen_file}")
    
    def filter_projects(self, criteria: Dict) -> List[Dict]:
        """
        Filter projects based on criteria.
        
        Args:
            criteria: Dictionary of filter criteria
                - min_stars: Minimum star count
                - language: Programming language
                - exclude_published: Exclude already published repos
                
        Returns:
            Filtered list of projects
        """
        filtered = self.projects.copy()
        
        if 'min_stars' in criteria:
            min_stars = criteria['min_stars']
            filtered = [p for p in filtered if p.get('stars', 0) >= min_stars]
        
        if 'language' in criteria:
            language = criteria['language'].lower()
            filtered = [p for p in filtered 
                       if p.get('language', '').lower() == language]
        
        if criteria.get('exclude_published') and self.database_client:
            filtered = [p for p in filtered 
                       if not self.database_client.is_published(p.get('github_url', ''))]
        
        return filtered
    
    def get_project_stats(self) -> Dict:
        """
        Get statistics about loaded projects.
        
        Returns:
            Dictionary with project statistics
        """
        if not self.projects:
            return {
                "total": 0,
                "with_stars": 0,
                "with_screenshots": 0,
                "languages": {},
                "avg_stars": 0
            }
        
        total = len(self.projects)
        with_stars = sum(1 for p in self.projects if p.get('stars'))
        with_screenshots = sum(1 for p in self.projects if p.get('screenshot_path'))
        
        languages = {}
        for project in self.projects:
            lang = project.get('language', 'Unknown')
            languages[lang] = languages.get(lang, 0) + 1
        
        stars = [p.get('stars', 0) for p in self.projects]
        avg_stars = sum(stars) / len(stars) if stars else 0
        
        return {
            "total": total,
            "with_stars": with_stars,
            "with_screenshots": with_screenshots,
            "languages": languages,
            "avg_stars": avg_stars
        }


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated):

class VideoSuiteAutomated:
    def __init__(self):
        self.projects = []  # ❌ Manages projects internally
        # ❌ Mixed responsibilities: projects, audio, video, database
    
    def load_projects(self):
        # ❌ Hardcoded file path
        # ❌ No flexibility in data source
        with open(DATA_FILE, 'r') as f:  # ❌ Global variable
            self.projects = json.load(f)
    
    def auto_select(self):
        # ❌ Tied to class state
        # ❌ Can't customize selection strategy
        self.shorts_selection = self.projects
        if len(self.projects) <= MAX_DEEP_DIVES:  # ❌ Global variable
            self.deep_dive_selection = self.projects


✅ NEW APPROACH (SOLID):

class ProjectManager(IProjectProvider):
    def __init__(
        self,
        database_client: Optional[IDatabaseClient] = None,  # ✅ Explicit dependency
        data_file: str = "posts_data.json",  # ✅ Configurable
        max_deep_dives: int = 3  # ✅ Configurable
    ):
        # ✅ All dependencies and config are explicit
        # ✅ Single responsibility: project management only
        # ✅ Easy to test with mock database
        # ✅ Flexible: can change data source or selection strategy
"""
