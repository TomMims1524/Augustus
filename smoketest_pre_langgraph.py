import json, os, sys, pathlib, requests

BASE = "http://127.0.0.1:8000"


def need_server():
    print("ERROR: API not reachable. Start it like this:")
    print(
        '  python -m uvicorn --app-dir "C:\\Users\\tmims\\ProjectAnalysis" app.main:app --reload --port 8000'
    )
    sys.exit(1)


# 1) /health
try:
    h = requests.get(f"{BASE}/health", timeout=5)
except Exception:
    need_server()
print("GET /health ->", h.status_code, h.text[:200])
if h.status_code != 200:
    sys.exit(1)

# 2) Prepare sample RAG doc
docs = pathlib.Path(os.path.join(os.environ["USERPROFILE"], "Documents", "RAGDocs"))
docs.mkdir(parents=True, exist_ok=True)
(docs / "stormwater.txt").write_text(
    "Stormwater approach:\n"
    "- Detention with staged outlets sized for the 2-, 10-, and 25-year events.\n"
    "- Water quality treatment via media filters upstream of detention.\n"
    "- Post-development peak flow not to exceed pre-development for the 10-year storm.\n",
    encoding="utf-8",
)

# 3) /rag/index
idx_body = {"folder": str(docs), "chunk_size": 800, "overlap": 100}
r = requests.post(f"{BASE}/rag/index", json=idx_body, timeout=10)
print("POST /rag/index ->", r.status_code, r.text[:200])
r.raise_for_status()
data = r.json()
assert data.get("indexed_chunks", 0) > 0, "No chunks indexed"

# 4) /rag/search
s = requests.post(
    f"{BASE}/rag/search",
    json={"query": "stormwater detention and water quality", "k": 5},
    timeout=10,
)
print("POST /rag/search ->", s.status_code, s.text[:200])
s.raise_for_status()
hits = s.json().get("results") or []
assert len(hits) > 0, "No search results"

# 5) /run/ask (stub or LLM-backed depending on your keys)
a = requests.post(
    f"{BASE}/run/ask",
    json={"question": "Summarize our stormwater approach", "k": 5},
    timeout=15,
)
print("POST /run/ask ->", a.status_code, a.text[:200])
a.raise_for_status()

# 6) Check if orchestrator routes exist yet (they’ll be absent before we add LangGraph)
spec = requests.get(f"{BASE}/openapi.json", timeout=5).json()
paths = set(spec.get("paths", {}).keys())
have_orch = {p for p in paths if p.startswith("/orchestrate")}
print("Orchestrator routes present?:", bool(have_orch), sorted(have_orch))

print("\nALL PRE-LANGGRAPH CHECKS PASSED ✅")
