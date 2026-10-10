"""Machine learning baselines, evaluation, and taxonomy package for VYOM+."""

from app.ml.taxonomy import (
    AUTHORITATIVE_VOUCHER_LABELS,
    LABEL_TO_ID,
    ID_TO_LABEL,
    normalize_voucher_label,
    is_valid_voucher_label,
)
from app.ml.baseline import (
    MajorityClassBaseline,
    TfidfBaselineClassifier,
    extract_text_representation,
)
from app.ml.evaluation import evaluate_classifier_performance
from app.ml.leakage import DataLeakageAudit
from app.ml.fixtures.synthetic_voucher_dataset import SYNTHETIC_DATASET

__all__ = [
    "AUTHORITATIVE_VOUCHER_LABELS",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
    "normalize_voucher_label",
    "is_valid_voucher_label",
    "MajorityClassBaseline",
    "TfidfBaselineClassifier",
    "extract_text_representation",
    "evaluate_classifier_performance",
    "DataLeakageAudit",
    "SYNTHETIC_DATASET",
]
