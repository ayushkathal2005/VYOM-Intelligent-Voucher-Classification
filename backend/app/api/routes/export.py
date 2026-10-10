"""Dataset export engine generating audited Excel (.xlsx) and CSV workbooks."""

import io
import csv
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
import openpyxl

from app.api.storage import dataset_storage
from app.ml.guardrails.models import TriageDecision

router = APIRouter(prefix="/datasets/{dataset_id}/export", tags=["Export"])


@router.get("")
def export_dataset(
    dataset_id: str,
    format: str = Query("xlsx", pattern="^(xlsx|csv)$", description="Export file format ('xlsx' or 'csv')"),
    filter_triage: Optional[str] = Query(None, description="Optional triage decision filter"),
):
    """Generate and stream a complete audit workbook containing original transaction attributes and VYOM+ predictions."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    all_preds = dataset_storage.get_predictions(dataset_id)
    raw_rows = ds["raw_rows"]
    txns = ds["transactions"]

    # Build rows
    export_rows = []
    for idx, (txn, raw_dict) in enumerate(zip(txns, raw_rows), start=1):
        item = all_preds.get(txn.row_id)
        if not item:
            continue

        res = item["result"]
        ev = item["evaluation"]
        override = item.get("override")

        if filter_triage and ev.triage_decision.value != filter_triage:
            continue

        row_dict = dict(raw_dict)
        # Append audit fields with clear VYOM_ namespace
        row_dict["VYOM_Row_ID"] = txn.row_id
        row_dict["VYOM_Predicted_Category"] = res.prediction.category
        row_dict["VYOM_Calibrated_Confidence"] = f"{ev.calibrated_confidence:.4f}"
        row_dict["VYOM_Confidence_Tier"] = ev.confidence_tier.value
        row_dict["VYOM_Triage_Decision"] = ev.triage_decision.value
        row_dict["VYOM_Reasoning"] = res.prediction.reasoning
        row_dict["VYOM_Detected_Signals"] = "; ".join(res.prediction.detected_signals)
        row_dict["VYOM_Contradictions"] = "; ".join(f"[{c.severity.value}] {c.code}: {c.message}" for c in ev.contradictions)
        row_dict["VYOM_Is_Overridden"] = "YES" if override else "NO"
        row_dict["VYOM_Override_Category"] = override["new_category"] if override else ""
        row_dict["VYOM_Override_Reason"] = override["override_reason"] if override else ""

        export_rows.append(row_dict)

    if not export_rows:
        raise HTTPException(status_code=400, detail="No classified transaction records matching export criteria.")

    headers = list(export_rows[0].keys())
    base_name = ds["filename"].rsplit(".", 1)[0]

    # Generate CSV
    if format.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        for r in export_rows:
            writer.writerow(r)
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode("utf-8")),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{base_name}_vyom_classified.csv"'},
        )

    # Generate XLSX
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "VYOM+ Audit Results"
    ws.append(headers)

    for r in export_rows:
        ws.append([r.get(h) for h in headers])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{base_name}_vyom_classified.xlsx"'},
    )
