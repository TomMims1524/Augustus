from __future__ import annotations
from typing import Dict, Any, List


def compute_fill_volume(
    lot_elev_ft: float,
    pad_target_ft: float,
    area_sqft: float,
    compaction_factor: float = 1.15,
) -> float:
    delta = max(0.0, pad_target_ft - lot_elev_ft)
    raw_cy = (delta * area_sqft) / 27.0
    return raw_cy * compaction_factor


def estimate_fill_cost(volume_cy: float, unit_cost: float) -> float:
    return volume_cy * unit_cost


def evaluate_lot_viability(
    fill_cost: float, annual_rent: float, threshold_ratio: float = 0.15
) -> str:
    if annual_rent <= 0:
        return "Redesign"
    return "Viable" if (fill_cost / annual_rent) <= threshold_ratio else "Redesign"


def tag_layout(
    lots: List[Dict[str, Any]], viability: Dict[str, str], sewer_ok: Dict[str, bool]
) -> List[Dict[str, Any]]:
    for lot in lots:
        fid = lot["id"]
        lot["status"] = (
            "Needs Redesign"
            if (viability.get(fid) == "Redesign" or not sewer_ok.get(fid, True))
            else "OK"
        )
    return lots
