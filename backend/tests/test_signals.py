"""Unit and integration tests for Phase 6: Accounting Signals & Semantic Candidate Retrieval."""

from pathlib import Path
import pytest

from app.ingestion.schema import CanonicalTransaction
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS
from app.ml.signals import (
    MoneyFlowDirection,
    EntityRole,
    AccountingSignalProfile,
    VoucherKnowledgeCard,
    VOUCHER_CARDS,
    AccountingSignalsEngine,
    SemanticCandidateRetriever,
    candidate_retriever,
)
from app.ml.fixtures.reference_workbook_fixture import load_reference_workbook


# -----------------------------------------------------------------------------
# 1. 27 Authoritative Voucher Knowledge Cards Integrity
# -----------------------------------------------------------------------------
def test_27_voucher_cards_integrity():
    """Verify that all 27 authoritative voucher categories have complete knowledge cards."""
    assert len(VOUCHER_CARDS) == 27
    assert set(VOUCHER_CARDS.keys()) == set(AUTHORITATIVE_VOUCHER_LABELS)

    for cat_name, card in VOUCHER_CARDS.items():
        assert card.category == cat_name
        assert len(card.description) > 15
        assert isinstance(card.expected_flow, MoneyFlowDirection)
        assert len(card.primary_identifiers) > 0
        assert len(card.typical_ledgers) > 0
        assert len(card.key_signals) > 0
        assert len(card.disambiguation_rule) > 10


# -----------------------------------------------------------------------------
# 2. Money Flow Direction Derivation Tests
# -----------------------------------------------------------------------------
def test_money_flow_derivation_internal_contra():
    """Verify Contra is correctly derived as INTERNAL money flow."""
    txn = CanonicalTransaction(
        row_id=1,
        debit_credit_information="Source: Axis Current, Destination: ICICI Current",
        custom_populated_fields={"Contra ID": "CTR-101", "Bank IFSC Code": "HDFC0001234"},
        total_amount=50000.0,
    )
    profile = AccountingSignalsEngine.extract_signals(txn)
    assert profile.money_flow == MoneyFlowDirection.INTERNAL
    assert profile.has_internal_account_pair is True
    assert EntityRole.INTERNAL_ACCOUNT in profile.detected_entity_roles


def test_money_flow_derivation_order_commitment():
    """Verify Purchase Order is classified as ORDER_COMMITMENT."""
    txn = CanonicalTransaction(
        row_id=2,
        order_reference="PO-9921",
        seller_supplier="Industrial Steels Ltd",
        custom_populated_fields={"Quantity Required": 500, "Promised Delivery": "2026-06-15", "Terms": "Net 30"},
    )
    profile = AccountingSignalsEngine.extract_signals(txn)
    assert profile.money_flow == MoneyFlowDirection.ORDER_COMMITMENT
    assert profile.has_order_reference is True
    assert EntityRole.VENDOR_SUPPLIER in profile.detected_entity_roles


def test_money_flow_derivation_non_financial_movement():
    """Verify Goods Receipt Note (GRN) is classified as NON_FINANCIAL_MOVEMENT."""
    txn = CanonicalTransaction(
        row_id=3,
        item_descriptions=["Precision Ball Bearings"],
        custom_populated_fields={
            "GRN Number": "GRN-8821",
            "Quality Status": "Passed",
            "Storage Location": "Bay 4",
            "Item Received": "Precision Ball Bearings",
        },
    )
    profile = AccountingSignalsEngine.extract_signals(txn)
    assert profile.money_flow == MoneyFlowDirection.NON_FINANCIAL_MOVEMENT
    assert profile.has_dispatch_reference is True


def test_money_flow_derivation_outflow_and_inflow():
    """Verify standard Payment is OUTFLOW and Receipt is INFLOW."""
    txn_payment = CanonicalTransaction(
        row_id=4,
        payment_information="Disbursement via NEFT to vendor",
        custom_populated_fields={"Payment ID": "PAY-1001", "Payee Organization": "Apex Logistics"},
        total_amount=25000.0,
    )
    profile_p = AccountingSignalsEngine.extract_signals(txn_payment)
    assert profile_p.money_flow == MoneyFlowDirection.OUTFLOW

    txn_receipt = CanonicalTransaction(
        row_id=5,
        payment_information="Inward cheque clearance from customer",
        custom_populated_fields={"Receipt ID": "REC-2002", "Paying Organization": "Global Client Corp"},
        total_amount=40000.0,
    )
    profile_r = AccountingSignalsEngine.extract_signals(txn_receipt)
    assert profile_r.money_flow == MoneyFlowDirection.INFLOW


# -----------------------------------------------------------------------------
# 3. Tax and Quantity Semantics Tests
# -----------------------------------------------------------------------------
def test_tax_and_negative_quantity_semantics():
    """Verify statutory tax applicability and negative quantity returns detection."""
    txn_return = CanonicalTransaction(
        row_id=6,
        invoice_number="DBN-5511",
        quantity=-25.0,  # Negative units returned
        taxable_value=10000.0,
        gst=1800.0,
        total_amount=11800.0,
        custom_populated_fields={"Units Returned": -25.0, "Reason for Return": "Manufacturing Defect"},
    )
    profile = AccountingSignalsEngine.extract_signals(txn_return)
    assert profile.has_negative_quantity is True
    assert profile.is_tax_applicable is True
    assert any("negative quantity" in s.lower() for s in profile.primary_signals)


def test_crossborder_trade_indicators():
    """Verify import/export foreign trade signals are extracted."""
    txn_import = CanonicalTransaction(
        row_id=7,
        custom_populated_fields={
            "Import Bill No": "IMP-7788",
            "Originating Country": "Germany",
            "Cost Insurance Freight": 150000.0,
            "Customs Duty": 30000.0,
        },
    )
    profile = AccountingSignalsEngine.extract_signals(txn_import)
    assert profile.has_customs_or_crossborder is True
    assert EntityRole.OVERSEAS_COUNTERPARTY in profile.detected_entity_roles


# -----------------------------------------------------------------------------
# 4. Semantic Candidate Retriever Ranking Tests
# -----------------------------------------------------------------------------
def test_candidate_retriever_ranking_contra():
    """Verify SemanticCandidateRetriever ranks Contra as top candidate for internal transfer."""
    retriever = SemanticCandidateRetriever()
    txn = CanonicalTransaction(
        row_id=1,
        debit_credit_information="Source Account: Axis, Destination Account: HDFC",
        custom_populated_fields={"Contra ID": "CTR-991", "Bank IFSC Code": "HDFC0001234"},
        total_amount=100000.0,
    )
    candidates = retriever.retrieve_candidates(txn, top_k=3)
    assert len(candidates) == 3
    top_card, top_score = candidates[0]
    assert top_card.category == "Contra"
    assert top_score >= 0.50
    assert 0.0 <= top_score <= 1.0


def test_candidate_retriever_ranking_journal():
    """Verify SemanticCandidateRetriever ranks Journal as top candidate for adjusting entry."""
    retriever = SemanticCandidateRetriever()
    txn = CanonicalTransaction(
        row_id=2,
        custom_populated_fields={"Journal ID": "JNL-44", "Debit Side": "Insurance", "Credit Side": "Prepaid Exp"},
        narration_remarks="Monthly amortization entry",
        total_amount=5000.0,
    )
    candidates = retriever.retrieve_candidates(txn, top_k=3)
    top_card, _ = candidates[0]
    assert top_card.category == "Journal"


def test_candidate_retriever_ranking_purchase_order():
    """Verify SemanticCandidateRetriever ranks Purchase Order at top."""
    retriever = SemanticCandidateRetriever()
    txn = CanonicalTransaction(
        row_id=3,
        seller_supplier="Apex Tools",
        order_reference="PO992211",
        custom_populated_fields={"Quantity Required": 150, "Promised Delivery": "2026-05-20"},
    )
    candidates = retriever.retrieve_candidates(txn, top_k=3)
    top_categories = [card.category for card, _ in candidates]
    assert "Purchase Order" in top_categories[:2]


def test_get_candidate_context_prompt_formatting():
    """Verify prompt snippet formatting contains candidate names, scopes, and disambiguation."""
    retriever = SemanticCandidateRetriever()
    txn = CanonicalTransaction(
        row_id=4,
        seller_supplier="Vendor Corp",
        custom_populated_fields={"PO Ref": "PO-100"},
        total_amount=12000.0,
    )
    context_str = retriever.get_candidate_context(txn, top_k=3)
    assert "CANDIDATE VOUCHER CATEGORIES" in context_str
    assert "Disambiguation:" in context_str
    assert "Scope:" in context_str
    # Verify zero target leakage
    assert "ground_truth_label" not in context_str


# -----------------------------------------------------------------------------
# 5. Reference Workbook Integration Tests
# -----------------------------------------------------------------------------
def test_signals_engine_on_reference_workbook_cases():
    """Verify signals engine and candidate retrieval operate smoothly across real reference records."""
    path = Path(__file__).resolve().parents[2] / "Voucher_Classification_Test_Cases_v2.xlsx"
    if not path.is_file():
        pytest.skip("Voucher_Classification_Test_Cases_v2.xlsx not present on disk.")

    txns, labels = load_reference_workbook(path)
    # Check 12 evenly distributed transactions
    for t, true_label in zip(txns[::10], labels[::10]):
        profile = AccountingSignalsEngine.extract_signals(t)
        assert isinstance(profile.money_flow, MoneyFlowDirection)
        assert len(profile.primary_signals) > 0

        # Retrieve candidates
        candidates = candidate_retriever.retrieve_candidates(t, top_k=5)
        top_cats = [c.category for c, _ in candidates]
        # Verify the true category is present within top 5 candidates
        assert true_label in top_cats, (
            f"True label '{true_label}' not in top candidates {top_cats} for row {t.row_id}!"
        )
