"""Unit and integration tests for Phase 4 Baseline Classifier & Evaluation."""

import time
import pytest
from app.ml import (
    AUTHORITATIVE_VOUCHER_LABELS,
    LABEL_TO_ID,
    ID_TO_LABEL,
    normalize_voucher_label,
    is_valid_voucher_label,
    MajorityClassBaseline,
    TfidfBaselineClassifier,
    extract_text_representation,
    evaluate_classifier_performance,
    DataLeakageAudit,
    SYNTHETIC_DATASET,
)


# -----------------------------------------------------------------------------
# 1. Authoritative Taxonomy Tests
# -----------------------------------------------------------------------------
def test_taxonomy_label_count_and_uniqueness():
    """Verify exactly 27 unique authoritative voucher categories exist."""
    assert len(AUTHORITATIVE_VOUCHER_LABELS) == 27
    assert len(set(AUTHORITATIVE_VOUCHER_LABELS)) == 27
    assert len(LABEL_TO_ID) == 27
    assert len(ID_TO_LABEL) == 27


def test_taxonomy_normalization():
    """Verify robust case and spacing normalization for valid labels."""
    assert normalize_voucher_label("purchase") == "Purchase"
    assert normalize_voucher_label("SALES") == "Sales"
    assert normalize_voucher_label("Contra") == "Contra"
    assert normalize_voucher_label("Salary/Payroll") == "Salary / Payroll"
    assert normalize_voucher_label("Purchase Return/Debit Note") == "Purchase Return / Debit Note"
    assert normalize_voucher_label("non_existent_category") is None
    assert is_valid_voucher_label("Journal") is True
    assert is_valid_voucher_label("Random Fake Label") is False


# -----------------------------------------------------------------------------
# 2. Majority Class Baseline Tests
# -----------------------------------------------------------------------------
def test_majority_class_baseline():
    """Verify majority class model predicts most frequent training class."""
    X_train = [{"text_repr": "A"}, {"text_repr": "B"}, {"text_repr": "C"}]
    y_train = ["Purchase", "Purchase", "Sales"]

    clf = MajorityClassBaseline()
    clf.fit(X_train, y_train)

    assert clf.majority_class == "Purchase"

    X_test = [{"text_repr": "X"}, {"text_repr": "Y"}]
    preds = clf.predict(X_test)
    assert preds == ["Purchase", "Purchase"]


# -----------------------------------------------------------------------------
# 3. TF-IDF Baseline Classifier Tests
# -----------------------------------------------------------------------------
def test_tfidf_baseline_training_and_prediction():
    """Verify TF-IDF classifier fits on synthetic dataset and generates predictions."""
    assert len(SYNTHETIC_DATASET) >= 54  # At least 2 per class for 27 classes

    # Train / test split (every even index train, odd index test)
    train_data = SYNTHETIC_DATASET[0::2]
    test_data = SYNTHETIC_DATASET[1::2]

    y_train = [d["voucher_type"] for d in train_data]
    y_test = [d["voucher_type"] for d in test_data]

    clf = TfidfBaselineClassifier(random_state=42)
    clf.fit(train_data, y_train)

    assert clf.pipeline is not None
    assert clf.training_time_seconds > 0.0

    # Single prediction inspection
    single_res = clf.predict_single(test_data[0])
    assert "voucher_type" in single_res
    assert is_valid_voucher_label(single_res["voucher_type"])
    assert 0.0 <= single_res["confidence"] <= 1.0
    assert "alternative" in single_res
    assert "latency_ms" in single_res
    assert single_res["latency_ms"] >= 0.0

    # Batch prediction
    start_batch = time.perf_counter()
    preds = clf.predict(test_data)
    batch_latency_ms = (time.perf_counter() - start_batch) * 1000.0

    assert len(preds) == len(test_data)
    for p in preds:
        assert is_valid_voucher_label(p)

    # Evaluate performance
    metrics = evaluate_classifier_performance(
        y_true=y_test,
        y_pred=preds,
        latency_ms_total=batch_latency_ms,
    )

    assert metrics["total_evaluated_records"] == len(y_test)
    assert 0.0 <= metrics["overall_accuracy"] <= 1.0
    assert 0.0 <= metrics["macro_f1"] <= 1.0
    assert 0.0 <= metrics["weighted_f1"] <= 1.0
    assert metrics["average_latency_ms_per_row"] >= 0.0

    # Confusion matrix checks
    cm = metrics["confusion_matrix"]
    assert len(cm) == 27
    assert len(cm[0]) == 27
    assert len(metrics["confusion_matrix_labels"]) == 27

    # Per-class metrics
    per_class = metrics["per_class_metrics"]
    assert len(per_class) == 27
    assert "Purchase" in per_class
    assert "precision" in per_class["Purchase"]


# -----------------------------------------------------------------------------
# 4. Data Leakage Audit Tests
# -----------------------------------------------------------------------------
def test_data_leakage_audit_clean_split():
    """Verify leakage audit passes when splits are cleanly partitioned."""
    train_records = [
        {"invoice_number": "INV-001", "text_repr": "supplier steel plates"},
        {"invoice_number": "INV-002", "text_repr": "customer finished goods"},
    ]
    test_records = [
        {"invoice_number": "INV-003", "text_repr": "vendor logistics fee"},
        {"invoice_number": "INV-004", "text_repr": "overseas export order"},
    ]

    report = DataLeakageAudit.audit_splits(train_records, test_records)
    assert report["is_clean"] is True
    assert report["overlapping_identifier_count"] == 0
    assert report["verdict"] == "PASS"


def test_data_leakage_audit_detects_duplicate_invoice():
    """Verify leakage audit fails when an invoice ID appears in both train and test."""
    train_records = [
        {"invoice_number": "INV-SHARED-99", "text_repr": "purchase transaction"},
    ]
    test_records = [
        {"invoice_number": "INV-SHARED-99", "text_repr": "test transaction"},
    ]

    report = DataLeakageAudit.audit_splits(train_records, test_records)
    assert report["is_clean"] is False
    assert report["overlapping_identifier_count"] == 1
    assert "INV-SHARED-99" in report["overlapping_identifiers"]
    assert "FAIL" in report["verdict"]


def test_extract_text_representation():
    """Verify textual extraction from dictionary and object formats."""
    record = {
        "seller_supplier": "Alpha Corp",
        "buyer_customer": "Beta Ltd",
        "item_descriptions": ["Item 1", "Item 2"],
        "narration_remarks": "Test remarks",
    }
    repr_str = extract_text_representation(record)
    assert "supplier: Alpha Corp" in repr_str
    assert "buyer: Beta Ltd" in repr_str
    assert "items: Item 1 Item 2" in repr_str
    assert "narration: Test remarks" in repr_str
