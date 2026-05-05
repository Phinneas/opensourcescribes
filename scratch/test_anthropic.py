import os
import anthropic
import json

def get_client():
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        api_key = config.get('anthropic', {}).get('api_key')
        return anthropic.Anthropic(api_key=api_key)
    except:
        return None

client = get_client()
if not client:
    print("No client")
    exit()

models = ["claude-haiku-4-5", "claude-sonnet-4-6", "claude-3-haiku-20240307"]

for model in models:
    print(f"Testing model: {model}")
    try:
        message = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        print(f"Success: {message.content[0].text}")
    except Exception as e:
        print(f"Error: {e}")
