from types import SimpleNamespace
from pprint import pprint
from app.agents.sewer_expert_agent import SewerExpertAgent, SewerExpertConfig


def _mk_site(n=3):
    lot = lambda i: SimpleNamespace(
        id=f"L{i}", pad_target_ft=1.0, elevation_ft=0.0, sewer_distance_ft=50.0
    )
    topo = SimpleNamespace(flood_prone=False, max_cut_fill_ft=2.0)
    return SimpleNamespace(
        lots=[lot(i) for i in range(n)],
        borings=[SimpleNamespace(uscs="CL")],
        topo=topo,
        high_water_table=False,
        jurisdiction=SimpleNamespace(county_state="Polk County, FL"),
    )


def _mk_constraints():
    return SimpleNamespace(
        budget_limit_usd=500_000.0,
        code_overrides={"min_cover_in": 24},
        power_backup_required=True,
    )


agent = SewerExpertAgent(config=SewerExpertConfig())
res = agent.run(_mk_site(), _mk_constraints())
print("keys:", list(res.keys()))
print("recommendation:", res["recommendation"])
pprint(res["extras"]["maintenance_plan"])
