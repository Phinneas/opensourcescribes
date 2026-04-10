"""
GitHub Client - Concrete implementation of IGitHubClient
Handles GitHub API interactions for repository data.
"""
import re
from typing import Optional, List, Tuple
import requests

from interfaces.interfaces import IGitHubClient


class GitHubClient(IGitHubClient):
    """
    Interacts with GitHub API for repository information.
    
    SOLID Compliance:
    ✅ SRP: Only handles GitHub API interactions
    ✅ DIP: No dependencies (foundational service)
    ✅ OCP: Can be extended with new GitHub API features
    ✅ LSP: Can be substituted with mock for testing
    ✅ ISP: Implements only IGitHubClient methods
    """
    
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        """
        Constructor injection - configuration is explicit.
        
        Args:
            api_key: Optional GitHub API key for higher rate limits
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.timeout = timeout
        self.base_url = "https://api.github.com"
        self.headers = {}
        
        if api_key:
            self.headers['Authorization'] = f'token {api_key}'
    
    def get_repository_stats(
        self, 
        owner: str, 
        repo: str
    ) -> Tuple[int, int, str, List[str]]:
        """
        Get repository statistics (stars, forks, language, topics).
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Tuple of (stars, forks, language, topics)
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                stars = data.get('stargazers_count', 0)
                forks = data.get('forks_count', 0)
                language = data.get('language', '') or ''
                topics = data.get('topics', [])
                
                return stars, forks, language, topics
            else:
                print(f"⚠️  GitHub API error: {response.status_code}")
                return 0, 0, '', []
                
        except requests.Timeout:
            print(f"⚠️  GitHub API timeout for {owner}/{repo}")
            return 0, 0, '', []
        except Exception as e:
            print(f"⚠️  GitHub API error: {e}")
            return 0, 0, '', []
    
    def get_readme(self, owner: str, repo: str) -> Optional[str]:
        """
        Get repository README content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            README content as string or None if not found
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/readme"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # README is base64 encoded
                import base64
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            else:
                return None
                
        except Exception as e:
            print(f"⚠️  Failed to get README for {owner}/{repo}: {e}")
            return None
    
    def parse_github_url(self, url: str) -> Optional[Tuple[str, str]]:
        """
        Parse GitHub URL to extract owner and repo.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (owner, repo) or None if invalid URL
        """
        match = re.search(r'github\.com/([^/]+)/([^/]+)', url)
        
        if match:
            owner = match.group(1)
            repo = match.group(2).rstrip('/')
            return owner, repo
        
        return None
    
    def get_stats_from_url(self, url: str) -> Tuple[int, int, str, List[str]]:
        """
        Convenience method: Get stats directly from URL.
        
        Args:
            url: GitHub repository URL
            
        Returns:
            Tuple of (stars, forks, language, topics)
        """
        parsed = self.parse_github_url(url)
        
        if parsed:
            owner, repo = parsed
            return self.get_repository_stats(owner, repo)
        
        return 0, 0, '', []
    
    def check_rate_limit(self) -> dict:
        """
        Check GitHub API rate limit status.
        
        Returns:
            Dictionary with rate limit information
        """
        url = f"{self.base_url}/rate_limit"
        
        try:
            response = requests.get(
                url, 
                headers=self.headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "limit": data['resources']['core']['limit'],
                    "remaining": data['resources']['core']['remaining'],
                    "reset": data['resources']['core']['reset']
                }
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": str(e)}


# ═══════════════════════════════════════════════════════════════════════
# COMPARISON: OLD vs NEW approach
# ═══════════════════════════════════════════════════════════════════════

"""
❌ OLD APPROACH (From VideoSuiteAutomated):

class VideoSuiteAutomated:
    def _fetch_github_stats(self, project: dict) -> tuple:
        # ❌ GitHub logic embedded in video class
        # ❌ Direct API calls, no abstraction
        # ❌ Hard to test (requires real GitHub API)
        # ❌ Duplicated in multiple places
        import re as _re
        import requests as _req
        url = project.get('github_url', '')
        match = _re.search(r'github\.com/([^/]+)/([^/]+)', url)
        if not match:
            return 0, 0, '', []
        owner, repo = match.groups()
        try:
            token = CONFIG.get('github', {}).get('api_key', '')  # ❌ Global config
            headers = {'Authorization': f'token {token}'} if token else {}
            resp = _req.get(f'https://api.github.com/repos/{owner}/{repo}',
                            headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                return (...)


✅ NEW APPROACH (SOLID):

class GitHubClient(IGitHubClient):
    def __init__(self, api_key: Optional[str] = None, timeout: int = 10):
        # ✅ All configuration explicit
        # ✅ Single responsibility: GitHub API only
        # ✅ Easy to mock for testing
        # ✅ Can be reused by multiple components
    
    def get_repository_stats(self, owner: str, repo: str):
        # ✅ Clean API
        # ✅ Consistent error handling
        # ✅ Type hints for clarity

# Usage in other components:
class GraphicsRenderer:
    def __init__(self, github_client: IGitHubClient):
        self.github = github_client  # ✅ Explicit dependency
    
    def render_title_card(self, project: dict):
        url = project.get('github_url')
        stars, forks, lang, topics = self.github.get_stats_from_url(url)
        # ✅ Use stats for rendering
"""
