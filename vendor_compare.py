from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, Optional
import math, os, yaml


def _read_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_costs() -> Dict[str, Any]:
    here = os.path.dirname(__file__)
    path = os.path.join(os.path.dirname(here), "services", "cost_book.yaml")
    # allow override path too
    if not os.path.exists(path):
        path = os.path.join(os.path.dirname(here), "services", "cost_book.yaml")
    return _read_yaml(path)


def npv(series, r):
    return sum(c / ((1 + r) ** t) for t, c in enumerate(series, start=1))


@dataclass
class Cluster:
    num_lots: int
    est_main_lf: float
    est_laterals_lf: float
    analysis_years: Optional[int] = None
    discount_rate: Optional[float] = None
    energy_rate_per_kwh: Optional[float] = None


def _f(fin, k, d):
    return fin.get(k, d) if fin else d


def estimate_vacuum(c: Cluster, costs: Dict[str, Any]) -> Dict[str, Any]:
    v = costs["vacuum"]
    fin = costs.get("finance", {})
    ny = c.analysis_years or _f(fin, "analysis_years", 30)
    dr = c.discount_rate or _f(fin, "discount_rate", 0.06)
    ek = c.energy_rate_per_kwh or _f(fin, "energy_rate_per_kwh", 0.14)
    capex = (
        c.est_main_lf * v["main_per_lf_shallow"]
        + c.est_laterals_lf * v["lateral_per_lf"]
        + math.ceil(max(1, c.num_lots) / 400) * v["station_per_400_lots_ls"]
        + math.ceil(c.num_lots / 2) * v["valve_pit_each"]
    )
    y1 = (
        c.num_lots * v["annual_om_per_conn"]
        + c.num_lots * v["energy_kwh_per_conn_day"] * 365 * ek
    )
    npv_om = npv([y1] * ny, dr)
    return {
        "system": "Vacuum",
        "capex": round(capex, 2),
        "annual_om_year1": round(y1, 2),
        "npv_om": round(npv_om, 2),
        "npv_total": round(capex + npv_om, 2),
    }


def estimate_pressure(c: Cluster, costs: Dict[str, Any]) -> Dict[str, Any]:
    p = costs["pressure"]
    fin = costs.get("finance", {})
    ny = c.analysis_years or _f(fin, "analysis_years", 30)
    dr = c.discount_rate or _f(fin, "discount_rate", 0.06)
    ek = c.energy_rate_per_kwh or _f(fin, "energy_rate_per_kwh", 0.14)
    capex = (
        c.est_main_lf * p["main_per_lf_shallow"]
        + c.est_laterals_lf * p["lateral_per_lf"]
        + c.num_lots * p["grinder_pump_package_each"]
        + (p["booster_ls"] if c.est_main_lf > 8000 else 0)
    )
    annual = (
        c.num_lots * p["annual_om_per_conn"]
        + c.num_lots * p["energy_kwh_per_conn_day"] * 365 * ek
    )
    rep_years = max(1, int(p["pump_replace_years"]))
    rep_cost = c.num_lots * p["pump_replace_cost_each"]
    series = [
        (annual + (rep_cost if (y % rep_years == 0) else 0)) for y in range(1, ny + 1)
    ]
    npv_om = npv(series, dr)
    return {
        "system": "Pressure",
        "capex": round(capex, 2),
        "annual_om_year1": round(annual, 2),
        "npv_om": round(npv_om, 2),
        "npv_total": round(capex + npv_om, 2),
    }


def compare(cluster: Dict[str, Any]) -> Dict[str, Any]:
    costs = load_costs()
    c = Cluster(**cluster)
    vac = estimate_vacuum(c, costs)
    pre = estimate_pressure(c, costs)
    pref = "Vacuum" if vac["npv_total"] < pre["npv_total"] else "Pressure"
    return {
        "vacuum": vac,
        "pressure": pre,
        "preferred": pref,
        "npv_delta": round(abs(vac["npv_total"] - pre["npv_total"]), 2),
    }
