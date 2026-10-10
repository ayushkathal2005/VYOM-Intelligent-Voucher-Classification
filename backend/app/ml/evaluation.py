"""Evaluation metrics engine for voucher classification benchmarks."""

import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
    confusion_matrix,
)

from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS, normalize_voucher_label


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

    return {
        "total_evaluated_records": total_samples,
        "overall_accuracy": round(acc, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "average_latency_ms_per_row": latency_per_row,
        "per_class_metrics": per_class_metrics,
        "confusion_matrix_labels": eval_labels,
        "confusion_matrix": cm.tolist(),
    }
