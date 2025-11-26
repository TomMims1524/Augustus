import requests, json

print("GET /health ->", requests.get("http://127.0.0.1:8000/health").json())
resp = requests.post(
    "http://127.0.0.1:8000/run/ask", json={"question": "ping test", "k": 2}
)
print("POST /run/ask ->", resp.json())
