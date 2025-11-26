from __future__ import annotations
import os, requests
from typing import Dict, Any

APS_BASE = "https://developer.api.autodesk.com"


def _token() -> str:
    cid = os.getenv("APS_CLIENT_ID")
    secret = os.getenv("APS_CLIENT_SECRET")
    if not cid or not secret:
        raise RuntimeError("APS_CLIENT_ID/APS_CLIENT_SECRET not set")
    r = requests.post(
        f"{APS_BASE}/authentication/v2/token",
        data={
            "grant_type": "client_credentials",
            "scope": "data:read data:write bucket:create bucket:read code:all",
        },
        auth=(cid, secret),
        timeout=30,
    )
    r.raise_for_status()
    return r.json()["access_token"]


def submit_design_automation_job(
    activity_id: str, workitem: Dict[str, Any]
) -> Dict[str, Any]:
    t = _token()
    r = requests.post(
        f"{APS_BASE}/da/us-east/v3/workitems",
        json={"activityId": activity_id, **workitem},
        headers={"Authorization": f"Bearer {t}"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json()
