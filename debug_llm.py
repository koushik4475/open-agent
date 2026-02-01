import requests
import json

url = "http://localhost:11434/api/generate"
payload = {
    "model": "phi3:mini",
    "prompt": "hi",
    "options": {
        "temperature": 0.7,
        "num_predict": 1024
    },
    "stream": False,
    "system": "You are OpenAgent, a helpful offline-first AI assistant.\nYou are honest, concise, and practical. You do NOT make up information.\nIf you don't know something, say so clearly.\nWhen given context from files or memory, use it to answer accurately.\nKeep responses under 300 words unless the user asks for more detail."
}

print(f"Sending payload: {json.dumps(payload, indent=2)}")

try:
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
    resp.raise_for_status()
except Exception as e:
    print(f"Error: {e}")
