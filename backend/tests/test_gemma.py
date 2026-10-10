"""Unit and integration tests for Phase 5: Gemma 4 Integration & Deterministic Mock Adapter."""

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from app.ingestion.schema import CanonicalTransaction
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS
from app.ml.gemma import (
    GemmaVoucherPrediction,
    GemmaClassificationResult,
    GEMMA_SYSTEM_INSTRUCTION,
    build_gemma_classification_prompt,
    MockGemmaAdapter,
    GemmaClassifier,
    GemmaConfigurationError,
)
from app.ml.fixtures.reference_workbook_fixture import load_reference_workbook


# -----------------------------------------------------------------------------
# 1. Pydantic Output Validation & Schema Tests
# -----------------------------------------------------------------------------
def test_gemma_voucher_prediction_valid():
    """Verify valid GemmaVoucherPrediction creates and normalizes category."""
    pred = GemmaVoucherPrediction(
        category="Purchase",
        confidence=0.95,
        alternative_category="Purchase Order",
        alternative_confidence=0.05,
        reasoning="Valid tax invoice from supplier with PO reference.",
        detected_signals=["supplier vendor", "PO ref linkage"],
        review_recommended=False,
    )
    assert pred.category == "Purchase"
    assert pred.confidence == 0.95
    assert pred.alternative_category == "Purchase Order"
    assert pred.review_recommended is False


def test_gemma_voucher_prediction_normalizes_case():
    """Verify category normalization maps case variations to authoritative strings."""
    pred = GemmaVoucherPrediction(
        category="sales return / credit note",
        confidence=0.88,
        reasoning="Credit note document from customer.",
    )
    assert pred.category == "Sales Return / Credit Note"

    pred2 = GemmaVoucherPrediction(
        category="salary/payroll",
        confidence=0.99,
        reasoning="Monthly payroll payment.",
    )
    assert pred2.category == "Salary / Payroll"


def test_gemma_voucher_prediction_rejects_invalid_category():
    """Verify prediction fails validation if an invented/invalid category is provided."""
    with pytest.raises(ValidationError):
        GemmaVoucherPrediction(
            category="Invented Invalid Category XYZ",
            confidence=0.90,
            reasoning="Invalid category.",
        )


def test_gemma_voucher_prediction_confidence_bounds():
    """Verify confidence must be bounded between 0.0 and 1.0."""
    with pytest.raises(ValidationError):
        GemmaVoucherPrediction(
            category="Purchase",
            confidence=1.5,  # Exceeds 1.0
            reasoning="Out of bounds confidence.",
        )

    with pytest.raises(ValidationError):
        GemmaVoucherPrediction(
            category="Purchase",
            confidence=-0.1,  # Below 0.0
            reasoning="Negative confidence.",
        )


# -----------------------------------------------------------------------------
# 2. System Instructions & Prompt Construction Tests
# -----------------------------------------------------------------------------
def test_gemma_system_instruction_completeness():
    """Verify system instruction defines all 27 authoritative labels and disambiguation guidelines."""
    assert len(AUTHORITATIVE_VOUCHER_LABELS) == 27
    for label in AUTHORITATIVE_VOUCHER_LABELS:
        assert label in GEMMA_SYSTEM_INSTRUCTION, f"Label '{label}' missing from Gemma system prompt!"

    # Verify critical disambiguation sections exist
    assert "Purchase vs Sales" in GEMMA_SYSTEM_INSTRUCTION
    assert "Purchase Order vs Purchase Invoice" in GEMMA_SYSTEM_INSTRUCTION
    assert "Payment vs Contra" in GEMMA_SYSTEM_INSTRUCTION
    assert "OUTPUT FORMAT" in GEMMA_SYSTEM_INSTRUCTION


def test_build_gemma_classification_prompt_zero_leakage():
    """Verify user prompt incorporates compact features and NEVER includes target labels."""
    txn = CanonicalTransaction(
        row_id=42,
        seller_supplier="Apex Steel Corp",
        buyer_customer="Metro Fabricators Ltd",
        invoice_number="INV-2026-999",
        invoice_date="2026-04-15",
        item_descriptions=["Structural I-beams"],
        quantity=50.0,
        taxable_value=125000.0,
        gst=22500.0,
        total_amount=147500.0,
        ground_truth_label="Purchase",  # Present in object for evaluation
        custom_populated_fields={"PO Ref": "PO-1002"},
    )

    prompt = build_gemma_classification_prompt(txn)

    assert "Transaction Record #42" in prompt
    assert "supplier: Apex Steel Corp" in prompt
    assert "buyer: Metro Fabricators Ltd" in prompt
    assert "items: Structural I-beams" in prompt
    assert "PO Ref: PO-1002" in prompt

    # STRICT LEAKAGE CHECK: ground truth label must not be in prompt
    assert "ground_truth_label" not in prompt
    assert "voucher category:" not in prompt.lower()
    assert "target:" not in prompt.lower()
    assert "voucher_type:" not in prompt.lower()


# -----------------------------------------------------------------------------
# 3. Deterministic Mock Adapter Tests
# -----------------------------------------------------------------------------
def test_mock_gemma_adapter_classifications():
    """Verify mock adapter produces auditable structured results across representative categories."""
    # 1. Contra
    contra_txn = CanonicalTransaction(
        row_id=1,
        debit_credit_information="Source: Axis Current, Destination: HDFC Business",
        custom_populated_fields={"Contra ID": "CTR-901", "Bank IFSC Code": "HDFC0001234"},
        total_amount=500000.0,
    )
    res_contra = MockGemmaAdapter.classify_transaction(contra_txn)
    assert res_contra.is_mock is True
    assert res_contra.model_name == "mock-gemma-4-adapter"
    assert res_contra.prediction.category == "Contra"
    assert res_contra.prediction.confidence >= 0.90
    assert len(res_contra.prediction.detected_signals) > 0
    assert "internal" in res_contra.prediction.reasoning.lower()

    # 2. Journal
    jnl_txn = CanonicalTransaction(
        row_id=2,
        custom_populated_fields={"Journal ID": "JNL-331", "Debit Side": "Depreciation", "Credit Side": "Accumulated Dep"},
        narration_remarks="Monthly asset depreciation allocation",
        total_amount=15000.0,
    )
    res_jnl = MockGemmaAdapter.classify_transaction(jnl_txn)
    assert res_jnl.prediction.category == "Journal"
    assert res_jnl.prediction.confidence >= 0.90

    # 3. Purchase Order
    po_txn = CanonicalTransaction(
        row_id=3,
        seller_supplier="Global Tech Inc",
        order_reference="PO992211",
        custom_populated_fields={"Quantity Required": 200, "Promised Delivery": "2026-06-01"},
    )
    res_po = MockGemmaAdapter.classify_transaction(po_txn)
    assert res_po.prediction.category == "Purchase Order"

    # 4. Import
    import_txn = CanonicalTransaction(
        row_id=4,
        custom_populated_fields={"Import Bill No": "IMP-1122", "Customs Duty": 45000.0, "Cost Insurance Freight": 250000.0},
    )
    res_imp = MockGemmaAdapter.classify_transaction(import_txn)
    assert res_imp.prediction.category == "Import"


# -----------------------------------------------------------------------------
# 4. GemmaClassifier Client & Fallback Tests
# -----------------------------------------------------------------------------
def test_gemma_classifier_mock_mode_execution():
    """Verify GemmaClassifier works cleanly in mock mode for single and batch predictions."""
    classifier = GemmaClassifier(force_mock=True)
    assert classifier.is_mock is True

    txns = [
        CanonicalTransaction(row_id=1, seller_supplier="Vendor A", custom_populated_fields={"PO Ref": "PO-1"}),
        CanonicalTransaction(row_id=2, buyer_customer="Customer B", custom_populated_fields={"Delivery Ref": "DN-1"}),
    ]

    results = classifier.classify_batch(txns)
    assert len(results) == 2
    for r in results:
        assert isinstance(r, GemmaClassificationResult)
        assert r.is_mock is True
        assert r.model_name == "mock-gemma-4-adapter"
        assert r.latency_ms >= 0.0
        assert r.prediction.category in AUTHORITATIVE_VOUCHER_LABELS


def test_gemma_classifier_response_parsing_robustness():
    """Verify response parsing handles raw JSON, markdown-wrapped JSON, and noisy text."""
    # Clean JSON
    raw_clean = json.dumps({
        "category": "Payment",
        "confidence": 0.92,
        "alternative_category": "Receipt",
        "alternative_confidence": 0.08,
        "reasoning": "Payment made to vendor against invoice.",
        "detected_signals": ["vendor settlement"],
        "review_recommended": False,
    })
    p1 = GemmaClassifier._parse_and_validate_response(raw_clean)
    assert p1.category == "Payment"
    assert p1.confidence == 0.92

    # Markdown block
    raw_markdown = f"```json\n{raw_clean}\n```"
    p2 = GemmaClassifier._parse_and_validate_response(raw_markdown)
    assert p2.category == "Payment"

    # JSON with surrounding prose
    raw_prose = f"Here is the classification result:\n{raw_clean}\nPlease review if needed."
    p3 = GemmaClassifier._parse_and_validate_response(raw_prose)
    assert p3.category == "Payment"


def test_gemma_classifier_live_mode_requires_api_key():
    """Verify that instantiating live mode without an API key raises or falls back safely."""
    # When no key is passed and force_mock=False, client detects missing key
    client = GemmaClassifier(api_key="", force_mock=False)
    assert client.is_mock is True  # Automatically recognized missing key and enabled mock fallback


# -----------------------------------------------------------------------------
# 5. Reference Workbook Integration Smoke Tests
# -----------------------------------------------------------------------------
def test_gemma_on_reference_workbook_samples():
    """Verify GemmaClassifier in mock mode processes real reference workbook transactions."""
    path = Path(__file__).resolve().parents[2] / "Voucher_Classification_Test_Cases_v2.xlsx"
    if not path.is_file():
        pytest.skip("Voucher_Classification_Test_Cases_v2.xlsx not present on disk.")

    txns, labels = load_reference_workbook(path)
    # Take a sample of 10 transactions across different categories
    sample_txns = txns[::12]

    classifier = GemmaClassifier(force_mock=True)
    results = classifier.classify_batch(sample_txns)

    assert len(results) == len(sample_txns)
    for r in results:
        assert r.prediction.category in AUTHORITATIVE_VOUCHER_LABELS
        assert 0.0 <= r.prediction.confidence <= 1.0
        assert len(r.prediction.reasoning) > 10
        assert r.is_mock is True
