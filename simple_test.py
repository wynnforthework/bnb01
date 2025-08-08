#!/usr/bin/env python3
import requests

print("Testing API...")
try:
    r = requests.get('http://127.0.0.1:5000/api/spot/symbols', timeout=30)
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")
