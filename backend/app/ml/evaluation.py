"""Evaluation metrics engine for voucher classification benchmarks and robustness evaluations."""

import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS, normalize_voucher_label
from app.ml.guardrails.models import GuardrailEvaluation, TriageDecision, ConfidenceTier
from app.ml.guardrails.pipeline import GuardrailsPipeline
from app.ingestion.parser import parse_transaction_file
from app.ingestion.schema import CanonicalTransaction


def evaluate_classifier_performance(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
    latency_ms_total: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Compute rigorous evaluation metrics according to challenge specifications:
    - Accuracy
    - Macro-F1
    - Weighted-F1
    - Per-class precision, recall, F1, and support
    - 27-Class Confusion matrix
    - Average latency per row
    """
    eval_labels = labels or list(AUTHORITATIVE_VOUCHER_LABELS)

    norm_y_true = [normalize_voucher_label(y) or "Other / Miscellaneous" for y in y_true]
    norm_y_pred = [normalize_voucher_label(y) or "Other / Miscellaneous" for y in y_pred]

    acc = float(accuracy_score(norm_y_true, norm_y_pred))
    macro_f1 = float(f1_score(norm_y_true, norm_y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(norm_y_true, norm_y_pred, average="weighted", zero_division=0))

    precision_list, recall_list, f1_list, support_list = precision_recall_fscore_support(
        norm_y_true,
        norm_y_pred,
        labels=eval_labels,
        zero_division=0,
    )

    per_class_metrics: Dict[str, Dict[str, float]] = {}
    for i, label in enumerate(eval_labels):
        per_class_metrics[label] = {
            "precision": round(float(precision_list[i]), 4),
            "recall": round(float(recall_list[i]), 4),
            "f1": round(float(f1_list[i]), 4),
            "support": int(support_list[i]),
        }

    cm = confusion_matrix(norm_y_true, norm_y_pred, labels=eval_labels)

    total_samples = len(norm_y_true)
    latency_per_row = (
        round(latency_ms_total / total_samples, 2)
        if latency_ms_total is not None and total_samples > 0
        else 0.0
    )

    # Confusion counts
    confusion_counts = Counter()
    for yt, yp in zip(norm_y_true, norm_y_pred):
        if yt != yp:
            confusion_counts[(yt, yp)] += 1

    top_confusions = [
        {"true_category": pair[0], "predicted_category": pair[1], "count": count}
        for pair, count in confusion_counts.most_common(10)
    ]

    return {
        "total_evaluated_records": total_samples,
        "overall_accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "average_latency_ms_per_row": latency_per_row,
        "per_class_metrics": per_class_metrics,
        "confusion_matrix_labels": eval_labels,
        "confusion_matrix": cm.tolist(),
        "top_confusions": top_confusions,
    }


def compute_multiclass_metrics(
    y_true: List[str],
    y_pred: List[str],
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compatibility wrapper returning metrics dictionary."""
    base = evaluate_classifier_performance(y_true, y_pred, labels)
    return {
        "total_samples": base["total_evaluated_records"],
        "accuracy": base["overall_accuracy"],
        "macro_f1": base["macro_f1"],
        "weighted_f1": base["weighted_f1"],
        "per_class": base["per_class_metrics"],
        "top_confusions": base["top_confusions"],
    }


def compute_triage_analytics(evaluations: List[GuardrailEvaluation]) -> Dict[str, Any]:
    """Compute enterprise guardrail triage statistics."""
    if not evaluations:
        return {
            "total_evaluated": 0,
            "auto_verified_count": 0,
            "auto_verified_percentage": 0.0,
            "flagged_for_review_count": 0,
            "flagged_percentage": 0.0,
            "critical_rejection_count": 0,
            "critical_rejection_percentage": 0.0,
            "average_calibrated_confidence": 0.0,
            "average_contradictions_per_voucher": 0.0,
            "tier_distribution": {"HIGH": 0, "MEDIUM": 0, "LOW": 0},
            "contradiction_rule_breakdown": {},
        }

    total = len(evaluations)
    auto_ver = sum(1 for e in evaluations if e.triage_decision == TriageDecision.AUTO_VERIFIED)
    flagged = sum(1 for e in evaluations if e.triage_decision == TriageDecision.FLAGGED_FOR_REVIEW)
    rejected = sum(1 for e in evaluations if e.triage_decision == TriageDecision.CRITICAL_REJECTION)

    conf_sum = sum(e.calibrated_confidence for e in evaluations)
    contradictions_count = sum(len(e.contradictions) for e in evaluations)

    tier_counts = Counter(e.confidence_tier.value for e in evaluations)

    rule_counts = Counter()
    for e in evaluations:
        for c in e.contradictions:
            rule_counts[c.rule_name] += 1

    return {
        "total_evaluated": total,
        "auto_verified_count": auto_ver,
        "auto_verified_percentage": round((auto_ver / total) * 100.0, 2),
        "flagged_for_review_count": flagged,
        "flagged_percentage": round((flagged / total) * 100.0, 2),
        "critical_rejection_count": rejected,
        "critical_rejection_percentage": round((rejected / total) * 100.0, 2),
        "average_calibrated_confidence": round(conf_sum / total, 4),
        "average_contradictions_per_voucher": round(contradictions_count / total, 2),
        "tier_distribution": dict(tier_counts),
        "contradiction_rule_breakdown": dict(rule_counts.most_common()),
    }


def run_benchmark_on_dataset(
    file_bytes: bytes,
    filename: str,
    target_column_name: str = "Voucher Category",
    force_mock: bool = True,
) -> Dict[str, Any]:
    """
    Execute full end-to-end benchmark on an accounting workbook or CSV.
    Quarantines the target category column from inference to guarantee zero leakage.
    """
    ingestion = parse_transaction_file(file_bytes, filename=filename)

    pipeline = GuardrailsPipeline()
    if force_mock:
        from app.ml.gemma.client import GemmaClassifier
        pipeline.classifier = GemmaClassifier(force_mock=True)

    y_true: List[str] = []
    y_pred: List[str] = []
    evaluations: List[GuardrailEvaluation] = []

    for txn in ingestion.canonical_transactions:
        # Extract ground truth target from raw record (quarantined during ingestion)
        raw = txn.raw_record or {}
        true_label = None
        for k, v in raw.items():
            if k.strip().lower() == target_column_name.strip().lower():
                true_label = v
                break

        # If not found by exact match, search for category in raw keys
        if not true_label:
            for k, v in raw.items():
                if "category" in k.strip().lower() or "voucher type" in k.strip().lower():
                    true_label = v
                    break

        if true_label is not None:
            norm_true = normalize_voucher_label(str(true_label))
            if norm_true:
                y_true.append(norm_true)

                # Execute classification with full guardrails
                result, eval_obj = pipeline.evaluate_and_classify(txn)
                y_pred.append(result.prediction.category)
                evaluations.append(eval_obj)

    metrics = compute_multiclass_metrics(y_true, y_pred)
    triage = compute_triage_analytics(evaluations)

    return {
        "filename": filename,
        "evaluated_records": len(y_true),
        "metrics": metrics,
        "triage": triage,
    }
