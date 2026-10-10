"""Aggregate analytics and audit metrics endpoints."""

from collections import Counter
from fastapi import APIRouter, HTTPException

from app.api.storage import dataset_storage
from app.api.schemas import AnalyticsResponse
from app.ml.guardrails.models import TriageDecision

router = APIRouter(prefix="/datasets/{dataset_id}/analytics", tags=["Analytics"])


@router.get("", response_model=AnalyticsResponse)
def get_dataset_analytics(dataset_id: str):
    """Retrieve comprehensive aggregate distribution metrics, reliability statistics, and contradiction summaries."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    all_preds = dataset_storage.get_predictions(dataset_id)
    total_txns = len(all_preds)

    if total_txns == 0:
        return AnalyticsResponse(
            dataset_id=dataset_id,
            total_transactions=0,
            category_distribution={},
            confidence_tier_distribution={},
            triage_distribution={},
            average_confidence=0.0,
            average_latency_ms=0.0,
            contradiction_counts={},
            auto_verified_percentage=0.0,
            review_queue_percentage=0.0,
            human_override_count=0,
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

    auto_verified_count = triage_counter.get(TriageDecision.AUTO_VERIFIED.value, 0)
    review_queue_count = triage_counter.get(TriageDecision.FLAGGED_FOR_REVIEW.value, 0) + triage_counter.get(TriageDecision.CRITICAL_REJECTION.value, 0)

    return AnalyticsResponse(
        dataset_id=dataset_id,
        total_transactions=total_txns,
        category_distribution=dict(cat_counter.most_common()),
        confidence_tier_distribution=dict(tier_counter),
        triage_distribution=dict(triage_counter),
        average_confidence=round(conf_sum / total_txns, 4),
        average_latency_ms=round(latency_sum / total_txns, 2),
        contradiction_counts=dict(contradiction_counter.most_common()),
        auto_verified_percentage=round((auto_verified_count / total_txns) * 100.0, 1),
        review_queue_percentage=round((review_queue_count / total_txns) * 100.0, 1),
        human_override_count=override_count,
    )
