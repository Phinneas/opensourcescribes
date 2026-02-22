import os
import requests
import json
from pathlib import Path

def test_upload():
    api_key = os.getenv('MINIMAX_API_KEY')
    if not api_key:
        with open('config.json', 'r') as f:
            api_key = json.load(f).get('minimax', {}).get('api_key')
    
    base_url = "https://api.minimax.io/v1"
    image_path = "assets/webmcp_real_page.png"
    
    if not os.path.exists(image_path):
        print(f"File not found: {image_path}")
        return

    with open(image_path, 'rb') as f:
        response = requests.post(
            f"{base_url}/files/upload",
            headers={"Authorization": f"Bearer {api_key}"},
            files={'file': f}
        )
    
    print(f"Status: {response.status_code}")
    print(f"Body: {response.text}")

if __name__ == "__main__":
    test_upload()
