#!/usr/bin/env python3
"""
Reddit Auto-Publisher for OpenSourceScribes
 Automatically publishes generated Reddit posts to Reddit.
"""

import json
import os
import praw
from datetime import datetime

def load_config():
    """Load Reddit credentials from config.json"""
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
            return config.get('reddit', {})
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}

def init_reddit_client():
    """Initialize Reddit API client"""
    reddit_config = load_config()
    
    required_fields = ['client_id', 'client_secret', 'user_agent', 'username', 'password']
    missing_fields = [field for field in required_fields if not reddit_config.get(field)]
    
    if missing_fields:
        print(f"Missing required Reddit credentials: {missing_fields}")
        print("Please add your Reddit API credentials to config.json under 'reddit' section")
        return None
    
    return praw.Reddit(
        client_id=reddit_config['client_id'],
        client_secret=reddit_config['client_secret'],
        user_agent=reddit_config['user_agent'],
        username=reddit_config['username'],
        password=reddit_config['password']
    )

def publish_to_reddit(content, subreddit):
    """Publish content to Reddit"""
    reddit = init_reddit_client()
    if not reddit:
        return False
    
    try:
        subreddit_obj = reddit.subreddit(subreddit)
        submission = subreddit_obj.submit(
            title=f"{datetime.now().strftime('%B %Y')} Trending Open-Source Projects",
            selftext=content,
            flair=None
        )
        print(f"Successfully published to Reddit!")
        print(f"Post URL: {submission.url}")
        return True
    except Exception as e:
        print(f"Error publishing to Reddit: {e}")
        return False

def load_latest_reddit_post():
    """Load the most recently generated Reddit post"""
    current_date = datetime.now().strftime("%m-%d")
    
    delivery_folder = os.path.join("deliveries", current_date)
    post_path = os.path.join(delivery_folder, "REDDIT_POST.md")
    
    if not os.path.exists(post_path):
        # Try to find any post in the deliveries folder
        for root, dirs, files in os.walk("deliveries"):
            for file in files:
                if file == "REDDIT_POST.md":
                    post_path = os.path.join(root, file)
                    break
            if post_path:
                break
    
    if not os.path.exists(post_path):
        print("Could not find any Reddit post to publish")
        return None
    
    with open(post_path, 'r') as f:
        return f.read()

def main():
    print("Reddit Auto-Publisher")
    print("=" * 40)
    
    # Check if auto-publish is enabled
    reddit_config = load_config()
    if not reddit_config.get('auto_publish', False):
        print("Auto-publishing is disabled in config.json")
        print("To enable, set reddit.auto_publish to true")
        return
    
    # Load the latest Reddit post
    content = load_latest_reddit_post()
    if not content:
        print("No Reddit post content found")
        return
    
    # Get subreddit from config
    subreddit = reddit_config.get('subreddit', 'opensourcescribes')
    print(f"Publishing to r/{subreddit}...")
    
    # Publish to Reddit
    success = publish_to_reddit(content, subreddit)
    
    if success:
        print("Reddit publishing complete!")
    else:
        print("Failed to publish to Reddit")

if __name__ == "__main__":
    main()
