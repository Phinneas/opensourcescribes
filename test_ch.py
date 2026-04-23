import requests
import json

def test():
    query = """
    SELECT count() as prs 
    FROM github_events 
    WHERE event_type = 'PullRequestEvent' 
      AND repo_name = 'ClickHouse/gitTrends' 
      AND created_at > now() - INTERVAL 30 DAY
    """
    try:
        response = requests.post(
            'https://play.clickhouse.com/?user=explorer',
            data=query,
            timeout=5
        )
        print(response.text)
    except Exception as e:
        print(e)
        
test()
