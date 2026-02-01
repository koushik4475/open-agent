import requests
import json

url = "http://localhost:5000/api/chat"
payload = {"message": "hi"}

try:
    print(f"Sending to {url}...")
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text}")
except Exception as e:
    print(f"Error: {e}")
