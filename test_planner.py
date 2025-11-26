# tests/test_planner.py
from __future__ import annotations

import importlib


def test_planner_import():
    # Imports should not raise; assert modules are present
    m1 = importlib.import_module("app.orchestrator.planner")
    m2 = importlib.import_module("app.orchestrator.schemas")
    m3 = importlib.import_module("app.orchestrator.registry")
    assert m1 is not None and m2 is not None and m3 is not None


def test_planner_functionality():
    # Plan should contain at least one step with expected attributes
    from app.orchestrator.planner import draft_plan
    from app.orchestrator.schemas import TaskSpec

    task = TaskSpec(
        question="What is the estimated cost for site preparation?",
        constraints={"budget_limit": "100000", "timeline": "3 months"},
    )
    plan = draft_plan(task)

    assert hasattr(plan, "steps")
    assert len(plan.steps) >= 1

    step0 = plan.steps[0]
    assert hasattr(step0, "id")
    assert hasattr(step0, "agent")
    assert hasattr(step0, "objective")
    assert isinstance(step0.inputs, dict)


def test_tool_registry():
    # Ensure registry is bootstrapped
    try:
        from app.agents.bootstrap import bootstrap

        bootstrap()
    except Exception:
        pass

    from app.orchestrator.registry import TOOL_REGISTRY

    assert isinstance(TOOL_REGISTRY, dict)
    for name in ["RAG.search", "Validate.basic", "Report.summarize", "Report.export"]:
        assert name in TOOL_REGISTRY, f"Missing tool: {name}"


def test_agent_registry():
    from app.orchestrator.registry import AGENTS, AGENT_SPECS, pick_model

    # Core runtime agents (callables)
    for a in ["retriever", "executor", "validator", "reporter"]:
        assert a in AGENTS, f"Missing core agent callable: {a}"

    # Model routing should work for a spec-defined agent (planner)
    assert "planner" in AGENT_SPECS, "Planner spec not found in AGENT_SPECS"
    route = pick_model("planner")
    assert "provider" in route and "model" in route
