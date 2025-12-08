"""
OpenSourceScribes MCP Server
Simplified queue and video generation management
Leverages GitHub MCP server for all repo/search operations
"""

import json
import os
from datetime import datetime
from typing import Any

class OpenSourceScribesQueueManager:
    """Manages video generation queue and coordinates with GitHub MCP"""
    
    def __init__(self):
        self.queue_file = "repo_queue.json"
        self.history_file = "repo_history.json"
        self.repo_queue = self._load_file(self.queue_file, [])
        self.repo_history = self._load_file(self.history_file, [])
    
    def _load_file(self, filename: str, default: Any) -> Any:
        """Load JSON file or return default"""
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    return json.load(f)
            except:
                return default
        return default
    
    def _save_file(self, filename: str, data: Any) -> None:
        """Save data to JSON file"""
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add_to_queue(self, repo_url: str, repo_data: dict, priority: str = "normal", notes: str = "") -> dict:
        """
        Add a repo to the queue.
        repo_data comes from GitHub MCP (contains stats, description, etc.)
        """
        # Check if already in queue
        for item in self.repo_queue:
            if item['url'] == repo_url:
                return {"error": f"Repo already in queue at position {self.repo_queue.index(item) + 1}"}
        
        # Add to queue
        queue_item = {
            "url": repo_url,
            "owner": repo_data.get('owner'),
            "repo": repo_data.get('repo'),
            "priority": priority,
            "notes": notes,
            "added_at": datetime.now().isoformat(),
            "repo_data": repo_data,  # Full data from GitHub MCP
            "status": "queued"
        }
        
        self.repo_queue.append(queue_item)
        self._sort_queue()
        self._save_file(self.queue_file, self.repo_queue)
        
        return {
            "success": True,
            "message": f"Added {repo_data.get('owner')}/{repo_data.get('repo')} to queue",
            "position": len(self.repo_queue),
            "stars": repo_data.get('stars', 0),
            "language": repo_data.get('language', 'Unknown')
        }
    
    def _sort_queue(self):
        """Sort queue by priority (high > normal > low)"""
        priority_order = {"high": 0, "normal": 1, "low": 2}
        self.repo_queue.sort(key=lambda x: priority_order.get(x['priority'], 1))
    
    def get_queue(self) -> dict:
        """Get current queue"""
        return {
            "queue": self.repo_queue,
            "total": len(self.repo_queue),
            "next": self.repo_queue[0] if self.repo_queue else None
        }
    
    def remove_from_queue(self, repo_url: str) -> dict:
        """Remove repo from queue"""
        original_length = len(self.repo_queue)
        self.repo_queue = [item for item in self.repo_queue if item['url'] != repo_url]
        
        if len(self.repo_queue) < original_length:
            self._save_file(self.queue_file, self.repo_queue)
            return {
                "success": True,
                "message": f"Removed {repo_url} from queue",
                "queue_length": len(self.repo_queue)
            }
        else:
            return {"error": f"Repo {repo_url} not found in queue"}
    
    def update_priority(self, repo_url: str, new_priority: str) -> dict:
        """Update priority of a queued repo"""
        for item in self.repo_queue:
            if item['url'] == repo_url:
                item['priority'] = new_priority
                self._sort_queue()
                self._save_file(self.queue_file, self.repo_queue)
                return {
                    "success": True,
                    "message": f"Updated {repo_url} priority to {new_priority}",
                    "new_position": self.repo_queue.index(item) + 1
                }
        
        return {"error": f"Repo {repo_url} not found in queue"}
    
    def get_queue_status(self) -> dict:
        """Get queue statistics"""
        total = len(self.repo_queue)
        high_priority = sum(1 for item in self.repo_queue if item['priority'] == 'high')
        total_stars = sum(item.get('repo_data', {}).get('stars', 0) for item in self.repo_queue)
        
        return {
            "total_queued": total,
            "high_priority": high_priority,
            "normal_priority": sum(1 for item in self.repo_queue if item['priority'] == 'normal'),
            "low_priority": sum(1 for item in self.repo_queue if item['priority'] == 'low'),
            "total_stars_in_queue": total_stars,
            "average_stars": total_stars // total if total > 0 else 0,
            "generated_videos": len(self.repo_history)
        }
    
    def mark_generated(self, repo_url: str) -> dict:
        """Mark a repo as generated and move to history"""
        for item in self.repo_queue:
            if item['url'] == repo_url:
                item['status'] = 'generated'
                item['generated_at'] = datetime.now().isoformat()
                
                # Move to history
                self.repo_history.append(item)
                self.repo_queue.remove(item)
                
                self._save_file(self.queue_file, self.repo_queue)
                self._save_file(self.history_file, self.repo_history)
                
                return {
                    "success": True,
                    "message": f"Marked {repo_url} as generated",
                    "queue_length": len(self.repo_queue)
                }
        
        return {"error": f"Repo {repo_url} not found in queue"}
    
    def get_history(self, limit: int = 10) -> dict:
        """Get generation history"""
        return {
            "total_generated": len(self.repo_history),
            "recent": self.repo_history[-limit:],
            "history_limit": limit
        }
    
    def get_next_to_generate(self, count: int = 1) -> dict:
        """Get next N repos to generate videos for"""
        to_generate = self.repo_queue[:count]
        
        return {
            "count": len(to_generate),
            "repos": to_generate,
            "command": f"python3 video_maker.py --queue {count}"
        }
    
    def clear_queue(self) -> dict:
        """Clear entire queue"""
        count = len(self.repo_queue)
        self.repo_queue = []
        self._save_file(self.queue_file, self.repo_queue)
        
        return {
            "success": True,
            "message": f"Cleared {count} items from queue",
            "queue_length": 0
        }


# Export for use as a library
queue_manager = OpenSourceScribesQueueManager()


def handle_queue_operation(operation: str, **kwargs) -> dict:
    """
    Handle queue operations from Claude via GitHub MCP integration
    
    Operations:
    - add: Add repo to queue (requires repo_url, repo_data from GitHub MCP)
    - get: Get current queue
    - remove: Remove from queue (requires repo_url)
    - priority: Update priority (requires repo_url, new_priority)
    - status: Get queue statistics
    - generated: Mark as generated (requires repo_url)
    - history: Get history (optional: limit)
    - next: Get next N to generate (optional: count)
    - clear: Clear entire queue
    """
    
    if operation == "add":
        return queue_manager.add_to_queue(
            kwargs.get('repo_url'),
            kwargs.get('repo_data'),
            kwargs.get('priority', 'normal'),
            kwargs.get('notes', '')
        )
    
    elif operation == "get":
        return queue_manager.get_queue()
    
    elif operation == "remove":
        return queue_manager.remove_from_queue(kwargs.get('repo_url'))
    
    elif operation == "priority":
        return queue_manager.update_priority(
            kwargs.get('repo_url'),
            kwargs.get('new_priority')
        )
    
    elif operation == "status":
        return queue_manager.get_queue_status()
    
    elif operation == "generated":
        return queue_manager.mark_generated(kwargs.get('repo_url'))
    
    elif operation == "history":
        return queue_manager.get_history(kwargs.get('limit', 10))
    
    elif operation == "next":
        return queue_manager.get_next_to_generate(kwargs.get('count', 1))
    
    elif operation == "clear":
        return queue_manager.clear_queue()
    
    else:
        return {"error": f"Unknown operation: {operation}"}


if __name__ == "__main__":
    # Test operations
    print("OpenSourceScribes Queue Manager initialized")
    print(f"Queue status: {queue_manager.get_queue_status()}")
