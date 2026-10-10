"""Comprehensive test suite for Phase 7: Accounting Guardrails, Contradiction Detection, and Confidence Calibration."""

from pathlib import Path
import pytest

from app.ingestion.schema import CanonicalTransaction
from app.ml.signals.models import MoneyFlowDirection, EntityRole, AccountingSignalProfile
from app.ml.guardrails.models import (
    ConfidenceTier,
    TriageDecision,
    ContradictionSeverity,
    AccountingContradiction,
    GuardrailEvaluation,
)
from app.ml.guardrails.detector import AccountingContradictionDetector
from app.ml.guardrails.scorer import ConfidenceScorer
from app.ml.guardrails.second_pass import SecondPassReasoningEngine
from app.ml.guardrails.pipeline import GuardrailsPipeline, guardrails_pipeline
from app.ml.fixtures.reference_workbook_fixture import load_reference_workbook


# -----------------------------------------------------------------------------
# 1. Contradiction Detection Tests
# -----------------------------------------------------------------------------
def test_contra_with_external_vendor_contradiction():
    """Verify Contra with named external vendor counterparty triggers CRITICAL contradiction."""
    txn = CanonicalTransaction(
        row_id=1,
        doc_no="CNT-101",
        seller_supplier="Acme Industrial Supplies Ltd",
        total_amount=50000.0,
        custom_populated_fields={
            "Source Account": "HDFC Current A/c",
            "Destination Account": "ICICI Petty Cash",
        },
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Contra")
    codes = [c.code for c in contradictions]
    assert "CONTRA_EXTERNAL_COUNTERPARTY" in codes
    crit = [c for c in contradictions if c.code == "CONTRA_EXTERNAL_COUNTERPARTY"][0]
    assert crit.severity == ContradictionSeverity.CRITICAL
    assert "Acme Industrial Supplies Ltd" in crit.message


def test_contra_with_statutory_tax_contradiction():
    """Verify Contra with statutory tax assessed triggers CRITICAL contradiction."""
    txn = CanonicalTransaction(
        row_id=2,
        doc_no="CNT-102",
        taxable_value=10000.0,
        gst=1800.0,
        total_amount=11800.0,
        custom_populated_fields={
            "Source Account": "HDFC Current A/c",
            "Destination Account": "ICICI Savings",
        },
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Contra")
    codes = [c.code for c in contradictions]
    assert "CONTRA_STATUTORY_TAX" in codes
    crit = [c for c in contradictions if c.code == "CONTRA_STATUTORY_TAX"][0]
    assert crit.severity == ContradictionSeverity.CRITICAL


def test_sales_outward_disbursement_contradiction():
    """Verify Sales voucher assigned to an outward vendor disbursement triggers CRITICAL contradiction."""
    txn = CanonicalTransaction(
        row_id=3,
        doc_no="DISB-901",
        seller_supplier="Industrial Heavy Machinery Ltd",
        total_amount=85000.0,
        custom_populated_fields={"PO Ref": "PO-8821"},
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Sales")
    codes = [c.code for c in contradictions]
    assert "SALES_OUTWARD_DISBURSEMENT" in codes
    crit = [c for c in contradictions if c.code == "SALES_OUTWARD_DISBURSEMENT"][0]
    assert crit.severity == ContradictionSeverity.CRITICAL


def test_purchase_inward_collection_contradiction():
    """Verify Purchase voucher assigned to an inward customer collection triggers CRITICAL contradiction."""
    txn = CanonicalTransaction(
        row_id=4,
        doc_no="RCPT-501",
        buyer_customer="Apex Retail Systems",
        total_amount=42000.0,
        custom_populated_fields={"Receipt Nature": "Direct Inward Collection"},
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Purchase")
    codes = [c.code for c in contradictions]
    assert "PURCHASE_INWARD_COLLECTION" in codes
    crit = [c for c in contradictions if c.code == "PURCHASE_INWARD_COLLECTION"][0]
    assert crit.severity == ContradictionSeverity.CRITICAL


def test_zero_amount_commercial_invoice_contradiction():
    """Verify Purchase invoice with quantity but zero/missing monetary amount triggers WARNING."""
    txn = CanonicalTransaction(
        row_id=5,
        doc_no="PUR-001",
        seller_supplier="Raw Metals Inc",
        quantity=250.0,
        total_amount=None,
        taxable_value=None,
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Purchase")
    codes = [c.code for c in contradictions]
    assert "ZERO_AMOUNT_COMMERCIAL_INVOICE" in codes
    warn = [c for c in contradictions if c.code == "ZERO_AMOUNT_COMMERCIAL_INVOICE"][0]
    assert warn.severity == ContradictionSeverity.WARNING


def test_return_without_return_signals_contradiction():
    """Verify Return category without negative quantity or return keywords triggers WARNING."""
    txn = CanonicalTransaction(
        row_id=6,
        doc_no="DOC-771",
        seller_supplier="Textile Mills Ltd",
        quantity=100.0,
        total_amount=25000.0,
        taxable_value=23000.0,
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Purchase Return / Debit Note")
    codes = [c.code for c in contradictions]
    assert "RETURN_WITHOUT_RETURN_SIGNALS" in codes
    warn = [c for c in contradictions if c.code == "RETURN_WITHOUT_RETURN_SIGNALS"][0]
    assert warn.severity == ContradictionSeverity.WARNING


def test_internal_account_as_payment_contradiction():
    """Verify internal account transfer classified as external Payment triggers WARNING."""
    txn = CanonicalTransaction(
        row_id=7,
        doc_no="TRF-100",
        total_amount=15000.0,
        custom_populated_fields={
            "Source Account": "Main Branch Bank A",
            "Destination Account": "Cash Reserve Account",
            "Bank IFSC Code": "HDFC0001234",
        },
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Payment")
    codes = [c.code for c in contradictions]
    assert "INTERNAL_ACCOUNT_AS_PAYMENT" in codes


# -----------------------------------------------------------------------------
# 2. Confidence Calibration & Scorer Tests
# -----------------------------------------------------------------------------
def test_confidence_scorer_clean_high_tier():
    """Verify clean transaction with strong alignment scores HIGH tier and AUTO_VERIFIED."""
    txn = CanonicalTransaction(
        row_id=10,
        doc_no="SAL-1001",
        buyer_customer="Global Enterprises",
        total_amount=50000.0,
        taxable_value=45000.0,
        gst=5000.0,
        custom_populated_fields={"Delivery Ref": "DN-500"},
    )
    (
        calibrated_conf,
        retriever_affinity,
        signal_compat,
        tier,
        triage,
        notes,
    ) = ConfidenceScorer.score_prediction(
        txn=txn,
        category="Sales",
        raw_confidence=0.95,
        contradictions=[],
    )
    assert calibrated_conf >= 0.85
    assert tier == ConfidenceTier.HIGH
    assert triage == TriageDecision.AUTO_VERIFIED
    assert len(notes) >= 2


def test_confidence_scorer_critical_contradiction_routes_to_critical_rejection():
    """Verify transaction with CRITICAL contradiction is routed to CRITICAL_REJECTION regardless of raw confidence."""
    txn = CanonicalTransaction(
        row_id=11,
        doc_no="CNT-999",
        seller_supplier="Vendor Corp",
        total_amount=30000.0,
    )
    crit = AccountingContradiction(
        code="CONTRA_EXTERNAL_COUNTERPARTY",
        severity=ContradictionSeverity.CRITICAL,
        title="Test Critical",
        message="Test message",
        conflicting_fields=["seller_supplier"],
        suggested_action="Reclassify",
    )
    (
        calibrated_conf,
        retriever_affinity,
        signal_compat,
        tier,
        triage,
        notes,
    ) = ConfidenceScorer.score_prediction(
        txn=txn,
        category="Contra",
        raw_confidence=0.95,
        contradictions=[crit],
    )
    assert tier == ConfidenceTier.LOW
    assert triage == TriageDecision.CRITICAL_REJECTION
    assert any("CRITICAL penalty" in n for n in notes)


# -----------------------------------------------------------------------------
# 3. Second-Pass Reasoning Tests
# -----------------------------------------------------------------------------
def test_second_pass_re_routes_contra_to_payment():
    """Verify second-pass engine resolves Contra with vendor counterparty to Payment."""
    txn = CanonicalTransaction(
        row_id=20,
        doc_no="DOC-200",
        seller_supplier="Apex Steel Mills",
        total_amount=75000.0,
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Contra")
    category, justification = SecondPassReasoningEngine.arbitrate(
        txn=txn,
        primary_category="Contra",
        alternative_category="Payment",
        contradictions=contradictions,
    )
    assert category == "Payment"
    assert "Second-pass re-routed" in justification
    assert "Payment" in justification


def test_second_pass_re_routes_sales_to_purchase():
    """Verify second-pass engine resolves Sales assigned to vendor disbursement to Purchase."""
    txn = CanonicalTransaction(
        row_id=21,
        doc_no="PUR-991",
        seller_supplier="Precision Tooling Corp",
        total_amount=12000.0,
        custom_populated_fields={"PO Ref": "PO-1002"},
    )
    contradictions = AccountingContradictionDetector.detect_contradictions(txn, "Sales")
    category, justification = SecondPassReasoningEngine.arbitrate(
        txn=txn,
        primary_category="Sales",
        alternative_category="Purchase",
        contradictions=contradictions,
    )
    assert category == "Purchase"
    assert "Second-pass re-routed" in justification


# -----------------------------------------------------------------------------
# 4. Pipeline Integration & Reference Dataset Tests
# -----------------------------------------------------------------------------
def test_guardrails_pipeline_end_to_end_on_clean_purchase():
    """Verify GuardrailsPipeline processes clean purchase to AUTO_VERIFIED state."""
    pipeline = GuardrailsPipeline()
    txn = CanonicalTransaction(
        row_id=30,
        doc_no="PUR-1234",
        seller_supplier="Industrial Fasteners Ltd",
        taxable_value=25000.0,
        gst=4500.0,
        total_amount=29500.0,
        custom_populated_fields={"PO Ref": "PO-4412"},
    )
    result, eval_res = pipeline.evaluate_and_classify(txn)
    assert result.prediction.category == "Purchase"
    assert eval_res.confidence_tier in (ConfidenceTier.HIGH, ConfidenceTier.MEDIUM)
    assert isinstance(eval_res.calibrated_confidence, float)
    assert eval_res.calibrated_confidence > 0.65
    assert len(eval_res.audit_notes) > 0


def test_guardrails_pipeline_on_reference_workbook():
    """Verify GuardrailsPipeline runs on real reference dataset cases with high verification rate."""
    path = Path(__file__).resolve().parents[2] / "Voucher_Classification_Test_Cases_v2.xlsx"
    if not path.is_file():
        pytest.skip("Voucher_Classification_Test_Cases_v2.xlsx not present on disk.")

    txns, labels = load_reference_workbook(path)
    pipeline = GuardrailsPipeline()

    auto_verified_count = 0
    total_evaluated = 0

    # Test every 10th row across the dataset
    for t, true_label in zip(txns[::10], labels[::10]):
        result, eval_res = pipeline.evaluate_and_classify(t)
        total_evaluated += 1
        assert eval_res.predicted_category is not None
        assert 0.0 <= eval_res.calibrated_confidence <= 1.0
        assert eval_res.triage_decision in (
            TriageDecision.AUTO_VERIFIED,
            TriageDecision.FLAGGED_FOR_REVIEW,
            TriageDecision.CRITICAL_REJECTION,
        )
        if eval_res.triage_decision == TriageDecision.AUTO_VERIFIED:
            auto_verified_count += 1

    # In our reference test cases, majority (>= 60%) qualify for automated straight-through verification
    assert auto_verified_count >= total_evaluated * 0.60
