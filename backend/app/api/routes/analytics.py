"""Aggregate analytics and audit metrics endpoints."""

from collections import Counter
from fastapi import APIRouter, HTTPException

from app.api.storage import dataset_storage
from app.api.schemas import AnalyticsResponse, EvaluationMetricsResponse
from app.ml.guardrails.models import TriageDecision

router = APIRouter(prefix="/datasets/{dataset_id}/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_dataset_analytics(dataset_id: str):
    """Retrieve comprehensive aggregate distribution metrics, reliability statistics, and contradiction summaries."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    dataset_total_rows = ds.get("total_rows", 0)
    all_preds = dataset_storage.get_predictions(dataset_id)
    processed_count = len(all_preds)
    total_txns = max(dataset_total_rows, processed_count)

    if total_txns == 0 or processed_count == 0:
        return AnalyticsResponse(
            dataset_id=dataset_id,
            total_transactions=total_txns,
            processed_transactions=processed_count,
            auto_verified_count=0,
            flagged_for_review_count=0,
            critical_rejection_count=0,
            overridden_count=0,
            human_override_count=0,
            average_confidence=0.0,
            average_latency_ms=0.0,
            auto_verified_percentage=None,
            flagged_percentage=None,
            critical_rejection_percentage=None,
            review_queue_percentage=None,
            category_distribution={},
            confidence_tier_distribution={},
            triage_distribution={},
            triage_decision_distribution={},
            contradiction_counts={},
            contradiction_breakdown={},
        )

    cat_counter = Counter()
    tier_counter = Counter()
    triage_counter = Counter()
    contradiction_counter = Counter()
    conf_sum = 0.0
    latency_sum = 0.0
    override_count = 0

    for item in all_preds.values():
        res = item["result"]
        ev = item["evaluation"]

        cat = res.prediction.category
        cat_counter[cat] += 1

        tier = ev.confidence_tier.value
        tier_counter[tier] += 1

        triage = ev.triage_decision.value
        triage_counter[triage] += 1

        conf_sum += ev.calibrated_confidence
        latency_sum += res.latency_ms

        for c in ev.contradictions:
            contradiction_counter[c.code] += 1

        if item.get("override") is not None:
            override_count += 1

    # Authoritative record counts per triage status (strictly mutually exclusive)
    auto_verified_count = triage_counter.get(TriageDecision.AUTO_VERIFIED.value, 0)
    flagged_for_review_count = triage_counter.get(TriageDecision.FLAGGED_FOR_REVIEW.value, 0)
    critical_rejection_count = triage_counter.get(TriageDecision.CRITICAL_REJECTION.value, 0)

    # Denominator calculation: count / total_transactions * 100
    auto_verified_pct = round((auto_verified_count / total_txns) * 100.0, 1)
    flagged_pct = round((flagged_for_review_count / total_txns) * 100.0, 1)
    critical_rejection_pct = round((critical_rejection_count / total_txns) * 100.0, 1)

    triage_dict = dict(triage_counter)
    contradiction_dict = dict(contradiction_counter.most_common())

    return AnalyticsResponse(
        dataset_id=dataset_id,
        total_transactions=total_txns,
        processed_transactions=processed_count,
        auto_verified_count=auto_verified_count,
        flagged_for_review_count=flagged_for_review_count,
        critical_rejection_count=critical_rejection_count,
        overridden_count=override_count,
        human_override_count=override_count,
        average_confidence=round(conf_sum / processed_count, 4) if processed_count > 0 else 0.0,
        average_latency_ms=round(latency_sum / processed_count, 2) if processed_count > 0 else 0.0,
        auto_verified_percentage=auto_verified_pct,
        flagged_percentage=flagged_pct,
        critical_rejection_percentage=critical_rejection_pct,
        review_queue_percentage=flagged_pct,
        category_distribution=dict(cat_counter.most_common()),
        confidence_tier_distribution=dict(tier_counter),
        triage_distribution=triage_dict,
        triage_decision_distribution=triage_dict,
        contradiction_counts=contradiction_dict,
        contradiction_breakdown=contradiction_dict,
    )


@router.get("/evaluate", response_model=EvaluationMetricsResponse)
def evaluate_classified_dataset(dataset_id: str):
    """
    Evaluate multi-class accuracy, Macro-F1, per-class metrics, and confusion pairs
    if ground-truth voucher labels are present in the dataset's raw ingested records.
    """
    from app.ml.evaluation import compute_multiclass_metrics, compute_triage_analytics
    from app.ml.taxonomy import normalize_voucher_label

    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    all_preds = dataset_storage.get_predictions(dataset_id)
    if not all_preds:
        raise HTTPException(status_code=400, detail="Dataset has not been classified yet.")

    txns_by_row = {t.row_id: t for t in ds["transactions"]}
    y_true = []
    y_pred = []
    evaluations = []

    for row_id, item in all_preds.items():
        txn = txns_by_row.get(row_id)
        if not txn or not txn.raw_record:
            continue

        raw = txn.raw_record
        true_label = None
        for k, v in raw.items():
            if "category" in k.strip().lower() or "voucher type" in k.strip().lower():
                true_label = v
                break

        if true_label is not None:
            norm_true = normalize_voucher_label(str(true_label))
            if norm_true:
                y_true.append(norm_true)
                y_pred.append(item["result"].prediction.category)
                evaluations.append(item["evaluation"])

    if not y_true:
        raise HTTPException(
            status_code=422,
            detail="No ground-truth target label column found in raw dataset records to evaluate against.",
        )

    metrics = compute_multiclass_metrics(y_true, y_pred)
    triage = compute_triage_analytics(evaluations)

    return EvaluationMetricsResponse(
        dataset_id=dataset_id,
        total_samples=metrics["total_samples"],
        accuracy=metrics["accuracy"],
        macro_f1=metrics["macro_f1"],
        weighted_f1=metrics["weighted_f1"],
        per_class_metrics=metrics["per_class"],
        top_confused_pairs=metrics["top_confusions"],
        triage_analytics=triage,
    )

