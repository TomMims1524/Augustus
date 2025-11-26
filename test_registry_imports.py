# test_registry_imports.py
from app.orchestrator.registry import AGENT_SPECS, call_llm

print("Successfully imported:")
print(f"AGENT_SPECS keys: {list(AGENT_SPECS.keys())[:3]}")
print(f"call_llm signature: {call_llm.__code__.co_varnames}")
