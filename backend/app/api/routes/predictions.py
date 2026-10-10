"""Predictions query, triage filtering, and human reviewer override endpoints."""

import math
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from app.ml.taxonomy import is_valid_voucher_label, normalize_voucher_label
from app.ml.guardrails.models import ConfidenceTier, TriageDecision
from app.api.storage import dataset_storage
from app.api.schemas import (
    PredictionRecordResponse,
    PaginatedPredictionsResponse,
    HumanOverrideRequest,
    HumanOverrideResponse,
)

router = APIRouter(prefix="/datasets/{dataset_id}/predictions", tags=["Predictions & Review"])


@router.get("", response_model=PaginatedPredictionsResponse)
def get_dataset_predictions(
    dataset_id: str,
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
    triage_decision: Optional[TriageDecision] = Query(None, description="Filter by triage decision"),
    confidence_tier: Optional[ConfidenceTier] = Query(None, description="Filter by confidence tier"),
    category: Optional[str] = Query(None, description="Filter by predicted category"),
    search: Optional[str] = Query(None, description="Free text search over document no and counterparties"),
):
    """Query paginated prediction records with multi-dimensional audit filtering."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    all_preds = dataset_storage.get_predictions(dataset_id)
    txns_by_row = {t.row_id: t for t in ds["transactions"]}

    filtered_items = []
    # Sort by row_id ascending
    for row_id in sorted(all_preds.keys()):
        item = all_preds[row_id]
        res = item["result"]
        ev = item["evaluation"]
        override = item.get("override")
        txn = txns_by_row.get(row_id)

        # Apply triage_decision filter
        if triage_decision and ev.triage_decision != triage_decision:
            continue

        # Apply confidence_tier filter
        if confidence_tier and ev.confidence_tier != confidence_tier:
            continue

        # Apply category filter
        if category and res.prediction.category.lower() != category.strip().lower():
            continue

        # Apply free-text search
        if search:
            query = search.strip().lower()
            text_match = False
            if txn:
                if (txn.invoice_number and query in txn.invoice_number.lower()) or \
                   (txn.seller_supplier and query in txn.seller_supplier.lower()) or \
                   (txn.buyer_customer and query in txn.buyer_customer.lower()):
                    text_match = True
            if query in res.prediction.category.lower() or query in res.prediction.reasoning.lower():
                text_match = True
            if not text_match:
                continue

        filtered_items.append((row_id, item, txn))

    total_records = len(all_preds)
    filtered_records = len(filtered_items)
    total_pages = max(1, math.ceil(filtered_records / page_size))

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    page_slice = filtered_items[start_idx:end_idx]

    records = []
    for row_id, item, txn in page_slice:
        res = item["result"]
        ev = item["evaluation"]
        override = item.get("override")

        records.append(
            PredictionRecordResponse(
                row_id=row_id,
                doc_no=txn.invoice_number if txn else None,
                invoice_date=str(txn.invoice_date) if txn and txn.invoice_date else None,
                seller_supplier=txn.seller_supplier if txn else None,
                buyer_customer=txn.buyer_customer if txn else None,
                total_amount=txn.total_amount if txn else None,
                predicted_category=res.prediction.category,
                confidence=ev.calibrated_confidence,
                confidence_tier=ev.confidence_tier,
                triage_decision=ev.triage_decision,
                reasoning=res.prediction.reasoning,
                detected_signals=res.prediction.detected_signals,
                contradictions=[c.model_dump() for c in ev.contradictions],
                alternative_category=res.prediction.alternative_category,
                alternative_confidence=res.prediction.alternative_confidence,
                is_overridden=bool(override is not None),
                overridden_category=override["new_category"] if override else None,
                override_reason=override["override_reason"] if override else None,
                reviewer_id=override["reviewer_id"] if override else None,
                override_timestamp=override["timestamp"] if override else None,
                custom_fields=txn.custom_populated_fields if txn else {},
            )
        )

    return PaginatedPredictionsResponse(
        dataset_id=dataset_id,
        total_records=total_records,
        filtered_records=filtered_records,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        predictions=records,
    )


@router.get("/{row_id}", response_model=PredictionRecordResponse)
def get_prediction_detail(dataset_id: str, row_id: int):
    """Retrieve complete classification audit trace for a single transaction record."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    item = dataset_storage.get_prediction(dataset_id, row_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Prediction for row {row_id} not found in dataset '{dataset_id}'.")

    txns_by_row = {t.row_id: t for t in ds["transactions"]}
    txn = txns_by_row.get(row_id)
    res = item["result"]
    ev = item["evaluation"]
    override = item.get("override")

    return PredictionRecordResponse(
        row_id=row_id,
        doc_no=txn.invoice_number if txn else None,
        invoice_date=str(txn.invoice_date) if txn and txn.invoice_date else None,
        seller_supplier=txn.seller_supplier if txn else None,
        buyer_customer=txn.buyer_customer if txn else None,
        total_amount=txn.total_amount if txn else None,
        predicted_category=res.prediction.category,
        confidence=ev.calibrated_confidence,
        confidence_tier=ev.confidence_tier,
        triage_decision=ev.triage_decision,
        reasoning=res.prediction.reasoning,
        detected_signals=res.prediction.detected_signals,
        contradictions=[c.model_dump() for c in ev.contradictions],
        alternative_category=res.prediction.alternative_category,
        alternative_confidence=res.prediction.alternative_confidence,
        is_overridden=bool(override is not None),
        overridden_category=override["new_category"] if override else None,
        override_reason=override["override_reason"] if override else None,
        reviewer_id=override["reviewer_id"] if override else None,
        override_timestamp=override["timestamp"] if override else None,
        custom_fields=txn.custom_populated_fields if txn else {},
    )


@router.post("/{row_id}/override", response_model=HumanOverrideResponse)
def apply_human_override(dataset_id: str, row_id: int, payload: HumanOverrideRequest):
    """Apply an authoritative human reviewer correction to a voucher classification."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    item = dataset_storage.get_prediction(dataset_id, row_id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Prediction for row {row_id} not found in dataset '{dataset_id}'.")

    if not is_valid_voucher_label(payload.overridden_category):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid override category '{payload.overridden_category}'. Must match one of the 27 authoritative labels.",
        )

    normalized_cat = normalize_voucher_label(payload.overridden_category)

    override_record = dataset_storage.record_override(
        dataset_id=dataset_id,
        row_id=row_id,
        new_category=normalized_cat,
        override_reason=payload.override_reason,
        reviewer_id=payload.reviewer_id or "auditor-1",
    )

    if not override_record:
        raise HTTPException(status_code=500, detail="Failed to apply human override.")

    return HumanOverrideResponse(
        row_id=row_id,
        status="OVERRIDDEN",
        previous_category=override_record["previous_category"],
        new_category=override_record["new_category"],
        override_reason=override_record["override_reason"],
        reviewer_id=override_record["reviewer_id"],
        timestamp=override_record["timestamp"],
    )
