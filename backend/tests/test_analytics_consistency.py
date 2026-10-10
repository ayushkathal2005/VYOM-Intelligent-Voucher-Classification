"""Unit and integration tests for VYOM+ Analytics Dashboard consistency,
contradiction severity routing, event vs transaction accounting, and triage reconciliation.
"""

import pytest
from app.ingestion.schema import CanonicalTransaction
from app.ml.guardrails.models import (
    AccountingContradiction,
    ConfidenceTier,
    ContradictionSeverity,
    GuardrailEvaluation,
    TriageDecision,
)
from app.ml.guardrails.scorer import ConfidenceScorer
from app.ml.guardrails.pipeline import GuardrailsPipeline
from app.ml.guardrails.detector import AccountingContradictionDetector
from app.ml.gemma.schemas import GemmaClassificationResult, GemmaVoucherPrediction
from app.api.storage import DatasetStorage
from app.api.routes.analytics import get_dataset_analytics


def test_scorer_warning_never_routes_to_auto_verified():
    """Verify that a transaction with a WARNING contradiction is NEVER auto-verified,
    even if the base score or calibrated score is high.
    """
    txn = CanonicalTransaction(
        row_id=1,
        doc_no="INV-100",
        seller_supplier="Vendor Corp",
        buyer_customer="Client Inc",
        total_amount=0.0,
        quantity=50.0,
    )
    warning_contra = AccountingContradiction(
        code="ZERO_AMOUNT_COMMERCIAL_INVOICE",
        severity=ContradictionSeverity.WARNING,
        title="Zero-Valued Commercial Tax Invoice",
        message="Monetary amount is zero while quantity is positive.",
        suggested_action="Verify challan.",
    )

    # Even with raw confidence 1.0 (perfect LLM certainty), warning must hold auto-posting
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
        raw_confidence=1.0,
        contradictions=[warning_contra],
    )

    assert triage == TriageDecision.FLAGGED_FOR_REVIEW
    assert tier in (ConfidenceTier.MEDIUM, ConfidenceTier.LOW)
    assert any("automated posting held" in n for n in notes)


def test_scorer_critical_always_routes_to_critical_rejection():
    """Verify that any CRITICAL contradiction strictly forces CRITICAL_REJECTION."""
    txn = CanonicalTransaction(
        row_id=2,
        doc_no="CNT-200",
        seller_supplier="Commercial Supplier Ltd",
        total_amount=50000.0,
    )
    crit_contra = AccountingContradiction(
        code="CONTRA_EXTERNAL_COUNTERPARTY",
        severity=ContradictionSeverity.CRITICAL,
        title="Contra Entry With External Commercial Counterparty",
        message="Contra cannot have external vendor.",
        suggested_action="Reclassify to Payment.",
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
        raw_confidence=0.98,
        contradictions=[crit_contra],
    )

    assert triage == TriageDecision.CRITICAL_REJECTION
    assert tier == ConfidenceTier.LOW
    assert any("Routed to CRITICAL_REJECTION" in n for n in notes)


def test_scorer_clean_prediction_routes_to_auto_verified():
    """Verify that a high-confidence prediction with ZERO contradictions is AUTO_VERIFIED."""
    txn = CanonicalTransaction(
        row_id=3,
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

    assert triage == TriageDecision.AUTO_VERIFIED
    assert tier == ConfidenceTier.HIGH
    assert calibrated_conf >= 0.85


def test_multiple_contradictions_on_single_transaction_and_event_accounting():
    """Verify that multiple contradictions on a single row do not inflate affected transaction count,
    while correctly tracking the total event count.
    """
    storage = DatasetStorage()
    ds_id = "test_multi_contra"
    
    t1 = CanonicalTransaction(row_id=1, doc_no="DOC-1", total_amount=100.0)
    t2 = CanonicalTransaction(row_id=2, doc_no="DOC-2", total_amount=200.0)
    
    storage.save_dataset(
        dataset_id=ds_id,
        filename="test.xlsx",
        transactions=[t1, t2],
        raw_rows=[{}, {}],
        columns_detected=[],
        canonical_fields_mapped={},
        unmapped_columns=[],
        warnings=[],
    )

    c1 = AccountingContradiction(
        code="RULE_A",
        severity=ContradictionSeverity.WARNING,
        title="Warning A",
        message="msg",
        suggested_action="act",
    )
    c2 = AccountingContradiction(
        code="RULE_B",
        severity=ContradictionSeverity.WARNING,
        title="Warning B",
        message="msg",
        suggested_action="act",
    )

    # Row 1 has 2 contradiction events
    storage.predictions[ds_id][1] = {
        "result": GemmaClassificationResult(
            row_id=1,
            prediction=GemmaVoucherPrediction(
                category="Purchase",
                confidence=0.75,
                reasoning="Purchase pattern observed",
            ),
            model_name="fast",
            latency_ms=10.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=1,
            predicted_category="Purchase",
            raw_model_confidence=0.75,
            retriever_affinity=0.8,
            signal_compatibility=0.8,
            calibrated_confidence=0.70,
            confidence_tier=ConfidenceTier.MEDIUM,
            contradictions=[c1, c2],
            triage_decision=TriageDecision.FLAGGED_FOR_REVIEW,
        ),
        "override": None,
    }

    # Row 2 is clean auto-verified
    storage.predictions[ds_id][2] = {
        "result": GemmaClassificationResult(
            row_id=2,
            prediction=GemmaVoucherPrediction(
                category="Sales",
                confidence=0.92,
                reasoning="Clean outward sales invoice",
            ),
            model_name="fast",
            latency_ms=10.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=2,
            predicted_category="Sales",
            raw_model_confidence=0.92,
            retriever_affinity=0.9,
            signal_compatibility=0.9,
            calibrated_confidence=0.91,
            confidence_tier=ConfidenceTier.HIGH,
            contradictions=[],
            triage_decision=TriageDecision.AUTO_VERIFIED,
        ),
        "override": None,
    }

    from app.api.routes import analytics as analytics_module
    orig_storage = analytics_module.dataset_storage
    analytics_module.dataset_storage = storage

    try:
        analytics = get_dataset_analytics(ds_id)
        assert analytics.total_transactions == 2
        assert analytics.processed_transactions == 2
        assert analytics.auto_verified_count == 1
        assert analytics.flagged_for_review_count == 1
        assert analytics.critical_rejection_count == 0
        # Exactly 2 contradiction events across 1 unique transaction
        assert analytics.total_contradiction_events == 2
        assert analytics.transactions_with_contradictions == 1
        assert analytics.warning_contradiction_events == 2
        assert analytics.critical_contradiction_events == 0
        assert analytics.inconsistent_auto_verified_count == 0
    finally:
        analytics_module.dataset_storage = orig_storage


def test_mixed_triage_outcomes_reconcile_with_total_processed():
    """Verify that Auto-Verified + Review Queue + Critical Rejection == Processed Rows."""
    storage = DatasetStorage()
    ds_id = "test_mixed_triage"

    txns = [CanonicalTransaction(row_id=i, doc_no=f"DOC-{i}", total_amount=float(i * 100)) for i in range(1, 4)]
    storage.save_dataset(
        dataset_id=ds_id,
        filename="mixed.xlsx",
        transactions=txns,
        raw_rows=[{}, {}, {}],
        columns_detected=[],
        canonical_fields_mapped={},
        unmapped_columns=[],
        warnings=[],
    )

    # 1. AUTO_VERIFIED
    storage.predictions[ds_id][1] = {
        "result": GemmaClassificationResult(
            row_id=1,
            prediction=GemmaVoucherPrediction(
                category="Sales",
                confidence=0.95,
                reasoning="Clean revenue invoice",
            ),
            model_name="fast",
            latency_ms=5.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=1,
            predicted_category="Sales",
            raw_model_confidence=0.95,
            retriever_affinity=0.95,
            signal_compatibility=0.95,
            calibrated_confidence=0.95,
            confidence_tier=ConfidenceTier.HIGH,
            contradictions=[],
            triage_decision=TriageDecision.AUTO_VERIFIED,
        ),
    }

    # 2. FLAGGED_FOR_REVIEW (Warning)
    w = AccountingContradiction(
        code="RETURN_WITHOUT_RETURN_SIGNALS",
        severity=ContradictionSeverity.WARNING,
        title="Warning",
        message="msg",
        suggested_action="act",
    )
    storage.predictions[ds_id][2] = {
        "result": GemmaClassificationResult(
            row_id=2,
            prediction=GemmaVoucherPrediction(
                category="Sales Return / Credit Note",
                confidence=0.70,
                reasoning="Possible return without negative quantity",
            ),
            model_name="fast",
            latency_ms=5.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=2,
            predicted_category="Sales Return / Credit Note",
            raw_model_confidence=0.70,
            retriever_affinity=0.70,
            signal_compatibility=0.70,
            calibrated_confidence=0.68,
            confidence_tier=ConfidenceTier.MEDIUM,
            contradictions=[w],
            triage_decision=TriageDecision.FLAGGED_FOR_REVIEW,
        ),
    }

    # 3. CRITICAL_REJECTION (Critical)
    crit = AccountingContradiction(
        code="CONTRA_STATUTORY_TAX",
        severity=ContradictionSeverity.CRITICAL,
        title="Critical Contra",
        message="msg",
        suggested_action="act",
    )
    storage.predictions[ds_id][3] = {
        "result": GemmaClassificationResult(
            row_id=3,
            prediction=GemmaVoucherPrediction(
                category="Contra",
                confidence=0.88,
                reasoning="Contra entry with tax conflict",
            ),
            model_name="fast",
            latency_ms=5.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=3,
            predicted_category="Contra",
            raw_model_confidence=0.88,
            retriever_affinity=0.88,
            signal_compatibility=0.20,
            calibrated_confidence=0.45,
            confidence_tier=ConfidenceTier.LOW,
            contradictions=[crit],
            triage_decision=TriageDecision.CRITICAL_REJECTION,
        ),
    }

    from app.api.routes import analytics as analytics_module
    orig_storage = analytics_module.dataset_storage
    analytics_module.dataset_storage = storage

    try:
        analytics = get_dataset_analytics(ds_id)
        assert analytics.total_transactions == 3
        assert analytics.processed_transactions == 3
        assert analytics.auto_verified_count == 1
        assert analytics.flagged_for_review_count == 1
        assert analytics.critical_rejection_count == 1
        
        # Mathematical reconciliation check: A + F + C == Total Processed
        assert (
            analytics.auto_verified_count + analytics.flagged_for_review_count + analytics.critical_rejection_count
            == analytics.processed_transactions
        )

        # Percentages check
        assert analytics.auto_verified_percentage == 33.3
        assert analytics.flagged_percentage == 33.3
        assert analytics.critical_rejection_percentage == 33.3

        assert analytics.total_contradiction_events == 2
        assert analytics.transactions_with_contradictions == 2
        assert analytics.critical_contradiction_events == 1
        assert analytics.warning_contradiction_events == 1
        assert analytics.critical_transactions_count == 1
        assert analytics.warning_transactions_count == 1
        assert analytics.inconsistent_auto_verified_count == 0
    finally:
        analytics_module.dataset_storage = orig_storage


def test_human_override_refreshes_analytics():
    """Verify that applying a human override clears resolved contradictions, updates triage to AUTO_VERIFIED,
    and accurately decrements contradiction counts.
    """
    storage = DatasetStorage()
    ds_id = "test_override_refresh"
    t1 = CanonicalTransaction(row_id=1, doc_no="DOC-1", seller_supplier="Global Tech", total_amount=50000.0)

    storage.save_dataset(
        dataset_id=ds_id,
        filename="override.xlsx",
        transactions=[t1],
        raw_rows=[{}],
        columns_detected=[],
        canonical_fields_mapped={},
        unmapped_columns=[],
        warnings=[],
    )

    crit = AccountingContradiction(
        code="CONTRA_EXTERNAL_COUNTERPARTY",
        severity=ContradictionSeverity.CRITICAL,
        title="Critical Contra",
        message="msg",
        suggested_action="Payment",
    )
    storage.predictions[ds_id][1] = {
        "result": GemmaClassificationResult(
            row_id=1,
            prediction=GemmaVoucherPrediction(
                category="Contra",
                confidence=0.80,
                reasoning="Contra entry with vendor",
            ),
            model_name="fast",
            latency_ms=10.0,
            is_mock=True,
        ),
        "evaluation": GuardrailEvaluation(
            row_id=1,
            predicted_category="Contra",
            raw_model_confidence=0.80,
            retriever_affinity=0.80,
            signal_compatibility=0.30,
            calibrated_confidence=0.45,
            confidence_tier=ConfidenceTier.LOW,
            contradictions=[crit],
            triage_decision=TriageDecision.CRITICAL_REJECTION,
        ),
        "override": None,
    }

    from app.api.routes import analytics as analytics_module
    orig_storage = analytics_module.dataset_storage
    analytics_module.dataset_storage = storage

    try:
        # Before override: 1 critical rejection
        analytics_before = get_dataset_analytics(ds_id)
        assert analytics_before.critical_rejection_count == 1
        assert analytics_before.total_contradiction_events == 1

        # Auditor verifies and reclassifies to Payment
        override_res = storage.record_override(
            dataset_id=ds_id,
            row_id=1,
            new_category="Payment",
            override_reason="Auditor confirmed vendor disbursement.",
            reviewer_id="lead_auditor_01",
        )
        assert override_res is not None

        # After override: 1 auto-verified, 0 critical rejections, 0 contradiction events
        analytics_after = get_dataset_analytics(ds_id)
        assert analytics_after.critical_rejection_count == 0
        assert analytics_after.auto_verified_count == 1
        assert analytics_after.overridden_count == 1
        assert analytics_after.total_contradiction_events == 0
        assert analytics_after.inconsistent_auto_verified_count == 0
    finally:
        analytics_module.dataset_storage = orig_storage
