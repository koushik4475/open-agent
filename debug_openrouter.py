import requests
import json
import os

# Settings from user
API_KEY = "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"
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "deepseek/deepseek-r1" # Trying non-free version or standard ID

print(f"Testing OpenRouter...\nURL: {BASE_URL}/chat/completions\nModel: {MODEL}")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "http://localhost:5000",
    "X-Title": "OpenAgent Debugger"
}

payload = {
    "model": MODEL,
    "messages": [
        {"role": "user", "content": "hi"}
    ],
    "stream": False
}

try:
    resp = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json=payload,
        timeout=30
    )
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
