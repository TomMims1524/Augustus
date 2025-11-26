from fastapi import APIRouter, Response
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
import csv, io, html
from app.agents.vendor_compare import compare, load_costs

router = APIRouter()


class Cluster(BaseModel):
    num_lots: int = Field(..., gt=0)
    est_main_lf: float = Field(..., ge=0)
    est_laterals_lf: float = Field(..., ge=0)
    analysis_years: Optional[int] = 30
    discount_rate: Optional[float] = 0.06
    energy_rate_per_kwh: Optional[float] = 0.14


class CompareReq(BaseModel):
    cluster: Cluster
    fmt: Optional[str] = "json"
    filename: Optional[str] = None


@router.get("/vendors/costs")
def vendors_costs() -> Dict[str, Any]:
    return load_costs()


def _as_rows(res: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        {
            "System": "Vacuum",
            "CapEx ($)": f"{res['vacuum']['capex']:,.2f}",
            "Year1 O&M ($/yr)": f"{res['vacuum']['annual_om_year1']:,.2f}",
            "NPV O&M (30y) ($)": f"{res['vacuum']['npv_om']:,.2f}",
            "NPV Total (30y) ($)": f"{res['vacuum']['npv_total']:,.2f}",
        },
        {
            "System": "Pressure",
            "CapEx ($)": f"{res['pressure']['capex']:,.2f}",
            "Year1 O&M ($/yr)": f"{res['pressure']['annual_om_year1']:,.2f}",
            "NPV O&M (30y) ($)": f"{res['pressure']['npv_om']:,.2f}",
            "NPV Total (30y) ($)": f"{res['pressure']['npv_total']:,.2f}",
        },
    ]


def _to_markdown(res: Dict[str, Any]) -> str:
    rows = _as_rows(res)
    headers = list(rows[0].keys())
    md = "| " + " | ".join(headers) + " |\n"
    md += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for r in rows:
        md += "| " + " | ".join(r[h] for h in headers) + " |\n"
    md += f"\n**Preferred:** {res['preferred']} &nbsp;&nbsp; **NPV Δ:** ${res['npv_delta']:,.2f}\n"
    return md


def _to_html(res: Dict[str, Any]) -> str:
    rows = _as_rows(res)
    headers = list(rows[0].keys())

    def esc(x):
        return html.escape(str(x))

    ths = "".join(f"<th>{esc(h)}</th>" for h in headers)
    trs = "".join(
        "<tr>" + "".join(f"<td>{esc(r[h])}</td>" for h in headers) + "</tr>"
        for r in rows
    )
    note = f"<p><strong>Preferred:</strong> {esc(res['preferred'])} &nbsp;&nbsp; <strong>NPV Δ:</strong> ${res['npv_delta']:,.2f}</p>"
    style = """
    <style>
    table {border-collapse: collapse; font-family: Arial, sans-serif; font-size: 14px;}
    th, td {border: 1px solid #ccc; padding: 8px 10px;}
    th {background: #f3f3f3; text-align: left;}
    </style>
    """
    return f"<!doctype html><html><head><meta charset='utf-8'>{style}</head><body><table><thead><tr>{ths}</tr></thead><tbody>{trs}</tbody></table>{note}</body></html>"


def _to_csv_bytes(res: Dict[str, Any]) -> bytes:
    rows = _as_rows(res)
    headers = list(rows[0].keys())
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers)
    w.writeheader()
    [w.writerow(r) for r in rows]
    buf.write(f"\nPreferred,{res['preferred']}\n")
    buf.write(f"NPV Delta (USD),{res['npv_delta']:,.2f}\n")
    return buf.getvalue().encode("utf-8")


@router.post("/vendors/compare")
def vendors_compare(req: CompareReq):
    res = compare(req.cluster.model_dump())
    fmt = (req.fmt or "json").lower()
    if fmt == "json":
        return res
    if fmt == "markdown":
        return Response(_to_markdown(res), media_type="text/markdown")
    if fmt == "html":
        html_str = _to_html(res)
        headers = {
            "Content-Disposition": f'attachment; filename="{req.filename or "vendor_compare.html"}"'
        }
        return Response(html_str, media_type="text/html", headers=headers)
    if fmt == "csv":
        csv_bytes = _to_csv_bytes(res)
        headers = {
            "Content-Disposition": f'attachment; filename="{req.filename or "vendor_compare.csv"}"'
        }
        return Response(csv_bytes, media_type="text/csv", headers=headers)
    return {"error": f"Unknown format '{req.fmt}'. Use json|markdown|html|csv"}
