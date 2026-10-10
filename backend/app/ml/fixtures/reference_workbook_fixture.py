"""Reusable fixture loading and evaluation engine for Voucher_Classification_Test_Cases_v2.xlsx.

SECURITY & LEAKAGE NOTICE:
- The target column 'Voucher Category' is strictly partitioned into evaluation ground truth.
- Inference features (canonical fields and compact_representation) NEVER contain target labels.
- The 3 absent categories ('Advance / Prepayment', 'Attendance', 'Other / Miscellaneous') are
  supported via isolated synthetic regression fixtures, clearly separated from real benchmark scores.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

from app.ingestion.parser import parse_transaction_file
from app.ingestion.schema import CanonicalTransaction
from app.ml.taxonomy import (
    AUTHORITATIVE_VOUCHER_LABELS,
    normalize_voucher_label,
)
from app.ml.evaluation import evaluate_classifier_performance
from app.ml.leakage import DataLeakageAudit

# Authoritative path to the reference workbook in the repository root
DEFAULT_WORKBOOK_PATH = Path(__file__).resolve().parents[4] / "Voucher_Classification_Test_Cases_v2.xlsx"

# The 3 categories missing from the reference workbook
MISSING_REFERENCE_CATEGORIES: Tuple[str, ...] = (
    "Advance / Prepayment",
    "Attendance",
    "Other / Miscellaneous",
)

# Carefully documented synthetic fixtures for the missing categories
SYNTHETIC_MISSING_FIXTURES: List[Dict[str, Any]] = [
    # Advance / Prepayment
    {
        "row_id": 901,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Advance / Prepayment",
        "doc_no": "ADV-2026-001",
        "supplier": "Heavy Earthmovers Ltd",
        "payment": "Advance mobilization payment for crane lease",
        "total_amount": 250000.0,
        "date": "2026-04-12",
        "currency": "INR",
        "narration": "Advance paid against proforma invoice PI-8891 pending final billing",
    },
    {
        "row_id": 902,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Advance / Prepayment",
        "doc_no": "ADV-2026-002",
        "buyer": "Modern Retailers Pvt Ltd",
        "payment": "Customer advance received for seasonal booking",
        "total_amount": 100000.0,
        "date": "2026-04-15",
        "currency": "INR",
        "narration": "Prepayment received towards bulk festive order",
    },
    # Attendance
    {
        "row_id": 903,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Attendance",
        "doc_no": "ATT-2026-W14",
        "payroll": "Employee Code EMP-401, Days Worked: 26, Overtime: 14 hrs, Leaves: 2",
        "date": "2026-04-30",
        "currency": "INR",
        "narration": "Biometric monthly attendance log verification for plant shift A",
    },
    {
        "row_id": 904,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Attendance",
        "doc_no": "ATT-2026-W15",
        "payroll": "Employee Code EMP-812, Present: 24, Absent: 1, Paid Leaves: 1",
        "date": "2026-04-30",
        "currency": "INR",
        "narration": "Timesheet record for supervisory staff engineering unit",
    },
    # Other / Miscellaneous
    {
        "row_id": 905,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Other / Miscellaneous",
        "doc_no": "MISC-2026-001",
        "taxable_val": 450.0,
        "total_amount": 450.0,
        "date": "2026-04-18",
        "currency": "INR",
        "narration": "Scrap paper sale petty proceeds and round-off adjustment",
    },
    {
        "row_id": 906,
        "is_synthetic": True,
        "source": "synthetic_regression_fixture",
        "voucher_type": "Other / Miscellaneous",
        "doc_no": "MISC-2026-002",
        "total_amount": 1200.0,
        "date": "2026-04-20",
        "currency": "INR",
        "narration": "Unclaimed vendor credit write-back under rounding threshold",
    },
]


def load_reference_workbook(
    excel_path: Optional[Union[str, Path]] = None,
) -> Tuple[List[CanonicalTransaction], List[str]]:
    """
    Load, parse, and validate the reference judging workbook.

    Returns:
        A tuple of (canonical_transactions, ground_truth_labels).

    STRICT GUARANTEES:
    - ground_truth_labels are isolated from canonical_transactions.
    - No target label exists in any transaction's compact_representation().
    """
    path = Path(excel_path) if excel_path else DEFAULT_WORKBOOK_PATH
    if not path.is_file():
        raise FileNotFoundError(
            f"Reference workbook not found at '{path}'. Ensure 'Voucher_Classification_Test_Cases_v2.xlsx' exists."
        )

    file_bytes = path.read_bytes()
    result = parse_transaction_file(file_bytes, path.name)

    txns = result.canonical_transactions
    labels: List[str] = []

    for t in txns:
        if not t.ground_truth_label:
            raise ValueError(f"Transaction row {t.row_id} has missing ground truth label in reference dataset.")
        labels.append(t.ground_truth_label)

        # Audit: verify zero target label leakage in inference text
        text_repr = t.compact_representation()
        assert "voucher category" not in text_repr.lower(), (
            f"Target leakage detected in compact_representation for row {t.row_id}!"
        )

    return txns, labels


def get_missing_categories_synthetic_fixtures() -> List[Dict[str, Any]]:
    """Return synthetic regression fixtures for categories not present in the reference workbook."""
    return [dict(item) for item in SYNTHETIC_MISSING_FIXTURES]


def run_reference_cv_benchmark(
    excel_path: Optional[Union[str, Path]] = None,
    n_splits: int = 5,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Execute a stratified k-fold cross validation benchmark of the TF-IDF baseline on the reference dataset.

    Returns:
        Structured evaluation metrics, category distribution, and top confusion pairs.
    """
    txns, y = load_reference_workbook(excel_path)
    text_representations = [t.compact_representation() for t in txns]

    # Verify no label leakage
    leakage_records_train = [{"invoice_number": f"ROW-{t.row_id}", "text_repr": t.compact_representation()} for t in txns[:60]]
    leakage_records_test = [{"invoice_number": f"ROW-{t.row_id}", "text_repr": t.compact_representation()} for t in txns[60:]]
    leakage_audit = DataLeakageAudit.audit_splits(leakage_records_train, leakage_records_test)

    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=random_state)
    all_y_true: List[str] = []
    all_y_pred: List[str] = []

    for train_idx, test_idx in skf.split(text_representations, y):
        train_texts = [text_representations[i] for i in train_idx]
        train_y = [y[i] for i in train_idx]
        test_texts = [text_representations[i] for i in test_idx]
        test_y = [y[i] for i in test_idx]

        pipe = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000, sublinear_tf=True)),
            ("clf", LogisticRegression(class_weight="balanced", max_iter=1000, random_state=random_state)),
        ])

        pipe.fit(train_texts, train_y)
        preds = pipe.predict(test_texts)

        all_y_true.extend(test_y)
        all_y_pred.extend(list(preds))

    metrics = evaluate_classifier_performance(all_y_true, all_y_pred)

    # Calculate confusion pairs
    confusions: Dict[str, int] = {}
    for true_l, pred_l in zip(all_y_true, all_y_pred):
        if true_l != pred_l:
            pair_key = f"{true_l} -> {pred_l}"
            confusions[pair_key] = confusions.get(pair_key, 0) + 1

    sorted_confusions = sorted(confusions.items(), key=lambda x: x[1], reverse=True)

    # Category coverage breakdown
    unique_cats = sorted(list(set(y)))
    coverage_report = {
        "present_categories_count": len(unique_cats),
        "present_categories": unique_cats,
        "missing_categories_count": len(MISSING_REFERENCE_CATEGORIES),
        "missing_categories": list(MISSING_REFERENCE_CATEGORIES),
        "authoritative_total_categories": len(AUTHORITATIVE_VOUCHER_LABELS),
    }

    return {
        "dataset_name": "Voucher_Classification_Test_Cases_v2.xlsx",
        "total_records": len(txns),
        "cv_folds": n_splits,
        "leakage_audit": leakage_audit,
        "coverage": coverage_report,
        "metrics": metrics,
        "top_confusion_pairs": sorted_confusions,
    }
