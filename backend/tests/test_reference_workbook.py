"""Comprehensive validation suite for the VYOM+ Reference Judging Workbook.

Tests include:
- Ingestion and schema generalization on the reference dataset.
- Strict data-leakage audits ensuring the target column NEVER leaks into features.
- Generalized handling of reordered, missing, and additional columns.
- Handling of unlabeled datasets (as expected in judging).
- Stratified cross-validation performance of baseline classifier on reference data.
- Clear separation between real reference workbook data and synthetic regression fixtures.
"""

import io
from pathlib import Path
import pytest
import openpyxl
import pandas as pd

from app.ingestion import (
    parse_transaction_file,
    CanonicalTransaction,
    IngestionError,
)
from app.ml import (
    load_reference_workbook,
    get_missing_categories_synthetic_fixtures,
    run_reference_cv_benchmark,
    MISSING_REFERENCE_CATEGORIES,
    AUTHORITATIVE_VOUCHER_LABELS,
    TfidfBaselineClassifier,
    is_valid_voucher_label,
    DataLeakageAudit,
    extract_text_representation,
)


@pytest.fixture
def workbook_path() -> Path:
    """Path to the local reference workbook fixture."""
    path = Path(__file__).resolve().parents[2] / "Voucher_Classification_Test_Cases_v2.xlsx"
    if not path.is_file():
        pytest.skip("Voucher_Classification_Test_Cases_v2.xlsx not present on disk.")
    return path


# -----------------------------------------------------------------------------
# 1. Loading & Schema Verification
# -----------------------------------------------------------------------------
def test_reference_workbook_loading(workbook_path):
    """Verify reference workbook loads exactly 120 rows across 24 categories."""
    txns, labels = load_reference_workbook(workbook_path)
    assert len(txns) == 120
    assert len(labels) == 120

    unique_labels = sorted(list(set(labels)))
    assert len(unique_labels) == 24

    # Each category should have exactly 5 samples
    from collections import Counter
    counts = Counter(labels)
    for cat, cnt in counts.items():
        assert cnt == 5, f"Expected 5 samples for {cat}, got {cnt}"


def test_missing_categories_coverage():
    """Verify the 3 absent categories are clearly identified and handled with synthetic fixtures."""
    assert len(MISSING_REFERENCE_CATEGORIES) == 3
    assert set(MISSING_REFERENCE_CATEGORIES) == {
        "Advance / Prepayment",
        "Attendance",
        "Other / Miscellaneous",
    }

    synthetic_fixtures = get_missing_categories_synthetic_fixtures()
    assert len(synthetic_fixtures) == 6  # 2 per missing category

    for fix in synthetic_fixtures:
        assert fix["is_synthetic"] is True
        assert fix["source"] == "synthetic_regression_fixture"
        assert fix["voucher_type"] in MISSING_REFERENCE_CATEGORIES
        assert is_valid_voucher_label(fix["voucher_type"])


# -----------------------------------------------------------------------------
# 2. Strict Target Label Leakage Prevention
# -----------------------------------------------------------------------------
def test_strict_zero_target_leakage_audit(workbook_path):
    """
    CRITICAL SECURITY CHECK:
    Verify that the target column 'Voucher Category' NEVER leaks into:
    1. CanonicalTransaction attributes
    2. custom_populated_fields
    3. compact_representation() text used for inference / vectorization / LLM prompts
    """
    txns, labels = load_reference_workbook(workbook_path)

    for idx, (t, true_label) in enumerate(zip(txns, labels), start=1):
        # 1. Target column name must not be in custom_populated_fields keys
        for key in t.custom_populated_fields.keys():
            assert "voucher" not in key.lower() or "category" not in key.lower(), (
                f"Row {idx}: Target column '{key}' leaked into custom_populated_fields!"
            )

        # 2. Compact representation must NOT contain target column name
        text_repr = t.compact_representation()
        assert "voucher category" not in text_repr.lower(), (
            f"Row {idx}: 'Voucher Category' found in compact_representation!"
        )

        # 3. Target label value must NOT appear prefixed as target
        assert "target:" not in text_repr.lower()
        assert "voucher_type:" not in text_repr.lower()

        # 4. CanonicalTransaction ground_truth_label must equal true_label
        assert t.ground_truth_label == true_label


# -----------------------------------------------------------------------------
# 3. Wide Schema Compactness & Efficiency
# -----------------------------------------------------------------------------
def test_sparse_wide_representation_compactness(workbook_path):
    """
    Verify that 169-column sparse records are compactly formatted:
    Only ~9-14 populated fields are included, never ~155 null values.
    """
    txns, _ = load_reference_workbook(workbook_path)

    for t in txns:
        text = t.compact_representation()
        tokens = text.split(" | ")
        # Each transaction should have between 5 and 20 populated fields
        assert 5 <= len(tokens) <= 20, (
            f"Row {t.row_id} representation has unexpected field count {len(tokens)}: {text}"
        )
        # Ensure no null/nan strings were concatenated
        for token in tokens:
            assert ": nan" not in token.lower()
            assert ": none" not in token.lower()
            assert ": null" not in token.lower()


# -----------------------------------------------------------------------------
# 4. Unlabeled Judging Dataset Workflow
# -----------------------------------------------------------------------------
def test_unlabeled_judging_workflow(workbook_path):
    """
    Simulate the judging scenario: an unlabeled Excel file without 'Voucher Category'.
    The pipeline must ingest, extract features, and predict labels seamlessly.
    """
    df = pd.read_excel(workbook_path, sheet_name=0)
    # Drop the target column
    unlabeled_df = df.drop(columns=["Voucher Category"])

    buf = io.BytesIO()
    unlabeled_df.to_excel(buf, index=False)
    file_bytes = buf.getvalue()

    result = parse_transaction_file(file_bytes, "judging_unlabeled.xlsx")
    assert result.has_target_column is False
    assert result.target_column_name is None
    assert result.total_rows == 120

    for t in result.canonical_transactions:
        assert t.ground_truth_label is None
        # Verify compact representation still builds cleanly
        repr_str = t.compact_representation()
        assert len(repr_str) > 10

    # Train a baseline model and predict on all 120 unlabeled transactions
    clf = TfidfBaselineClassifier(random_state=42)
    # Train on synthetic dataset
    from app.ml.fixtures.synthetic_voucher_dataset import SYNTHETIC_DATASET
    clf.fit(SYNTHETIC_DATASET, [d["voucher_type"] for d in SYNTHETIC_DATASET])

    preds = clf.predict(result.canonical_transactions)
    assert len(preds) == 120
    for p in preds:
        assert is_valid_voucher_label(p)


# -----------------------------------------------------------------------------
# 5. Reordered, Missing, and Extra Columns Robustness
# -----------------------------------------------------------------------------
def test_reordered_and_extra_columns(workbook_path):
    """
    Verify parser correctly handles shuffled columns and unexpected judging metadata columns.
    """
    df = pd.read_excel(workbook_path, sheet_name=0)
    # Shuffle columns and inject arbitrary extra columns
    cols = list(df.columns)
    import random
    rng = random.Random(123)
    rng.shuffle(cols)
    shuffled_df = df[cols].copy()

    shuffled_df["Judging_Zone_ID"] = "ZONE-NORTH-04"
    shuffled_df["Auditor_Remarks"] = "Preliminary compliance pass"
    shuffled_df["Arbitrary_Custom_Tag"] = "XYZ-TAG-99"

    buf = io.BytesIO()
    shuffled_df.to_excel(buf, index=False)
    file_bytes = buf.getvalue()

    result = parse_transaction_file(file_bytes, "reordered_with_extra.xlsx")
    assert result.total_rows == 120
    assert result.has_target_column is True

    sample_txn = result.canonical_transactions[0]
    # Unmapped arbitrary metadata goes into custom_populated_fields
    assert "Judging_Zone_ID" in sample_txn.custom_populated_fields
    assert sample_txn.custom_populated_fields["Judging_Zone_ID"] == "ZONE-NORTH-04"
    assert "Arbitrary_Custom_Tag" in sample_txn.custom_populated_fields
    assert sample_txn.custom_populated_fields["Arbitrary_Custom_Tag"] == "XYZ-TAG-99"

    # Auditor_Remarks was recognized via alias as narration_remarks
    assert sample_txn.narration_remarks == "Preliminary compliance pass"



# -----------------------------------------------------------------------------
# 6. Stratified Cross-Validation Benchmark on Reference Data
# -----------------------------------------------------------------------------
def test_reference_cv_benchmark(workbook_path):
    """
    Execute 5-fold cross validation on reference workbook.
    Confirms baseline accuracy >= 90%, zero data leakage, and confusion matrix integrity.
    """
    benchmark = run_reference_cv_benchmark(workbook_path, n_splits=5, random_state=42)

    assert benchmark["total_records"] == 120
    assert benchmark["cv_folds"] == 5
    assert benchmark["leakage_audit"]["is_clean"] is True
    assert benchmark["leakage_audit"]["verdict"] == "PASS"

    metrics = benchmark["metrics"]
    assert metrics["overall_accuracy"] >= 0.90
    assert metrics["macro_f1"] >= 0.90
    assert metrics["weighted_f1"] >= 0.90

    # Verify confusion matrix covers all 27 categories
    assert len(metrics["confusion_matrix"]) == 27
    assert len(metrics["confusion_matrix"][0]) == 27

    # Check top confusion pairs (e.g. Purchase vs Sales)
    confusion_pairs = benchmark["top_confusion_pairs"]
    assert isinstance(confusion_pairs, list)


# -----------------------------------------------------------------------------
# 7. Edge Cases: Empty & Corrupted Files
# -----------------------------------------------------------------------------
def test_empty_and_corrupt_files():
    """Verify clear IngestionError on empty bytes or non-Excel binary files."""
    with pytest.raises(IngestionError, match="empty"):
        parse_transaction_file(b"", "empty.xlsx")

    with pytest.raises(IngestionError, match="Failed to open"):
        parse_transaction_file(b"NOT_A_VALID_ZIP_OR_XLSX_DATA", "corrupted.xlsx")
