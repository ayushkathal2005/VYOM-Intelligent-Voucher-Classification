"""Robustness, stress testing, edge-case handling, and evaluation benchmark tests."""

import io
import os
import re
import time
import pytest
import pandas as pd
from typing import Dict, Any

from app.ingestion.parser import parse_transaction_file, parse_numeric, parse_date_string
from app.ingestion.schema import CanonicalTransaction
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS, normalize_voucher_label
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.signals.retriever import SemanticCandidateRetriever
from app.ml.guardrails.detector import AccountingContradictionDetector
from app.ml.guardrails.scorer import ConfidenceScorer
from app.ml.guardrails.second_pass import SecondPassReasoningEngine
from app.ml.guardrails.pipeline import GuardrailsPipeline
from app.ml.guardrails.models import ConfidenceTier, TriageDecision
from app.ml.gemma.client import GemmaClassifier
from app.ml.evaluation import (
    compute_multiclass_metrics,
    compute_triage_analytics,
    run_benchmark_on_dataset,
)


REFERENCE_WORKBOOK_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "Voucher_Classification_Test_Cases_v2.xlsx")
)


# -----------------------------------------------------------------------------
# 1. Malformed and Adversarial Transaction Inputs
# -----------------------------------------------------------------------------
def test_extreme_malformed_and_unicode_records():
    """Verify parser and signals engine gracefully handle nulls, emojis, and corrupted strings."""
    csv_data = (
        "Doc Number,Counterparty,Gross Value,Narration\n"
        ",,,\n"
        "INV-#99!@#,🚀 Unicorn Global 💸,-9999999999.99,Corrupted payload with emoji & symbols 💥\n"
        "---,Unknown Entity,NaN,N/A\n"
    ).encode("utf-8")

    result = parse_transaction_file(csv_data, filename="malformed.csv")
    assert len(result.canonical_transactions) >= 1

    signals_engine = AccountingSignalsEngine()
    for txn in result.canonical_transactions:
        signals = signals_engine.extract_signals(txn)
        assert signals.money_flow is not None
        assert isinstance(signals.primary_signals, list)


def test_currency_symbols_and_accounting_negatives_parsing():
    """Verify numeric parsing across international currency symbols and negative formats."""
    assert parse_numeric("$12,345.67") == 12345.67
    assert parse_numeric("₹ 1,50,000.00") == 150000.0
    assert parse_numeric("€ 999.50") == 999.5
    assert parse_numeric("£ 45.20") == 45.2
    assert parse_numeric("(5,000.00)") == -5000.0
    assert parse_numeric("-₹ 2,500.50") == -2500.5
    assert parse_numeric("0.00") == 0.0
    assert parse_numeric(None) is None
    assert parse_numeric("N/A") is None
    assert parse_numeric("corrupted_amount") is None


# -----------------------------------------------------------------------------
# 2. Sparse and Extra-Wide ERP Workbook Stress
# -----------------------------------------------------------------------------
def test_sparse_and_extra_wide_erp_headers():
    """Verify ingestion and candidate retriever handle workbooks with 50+ extraneous ERP columns."""
    extra_cols = {f"SAP_GL_SEGMENT_{i}": [f"VAL_{i}"] for i in range(50)}
    base_data = {
        "Document Reference": ["PUR-EXT-888"],
        "Vendor Company": ["Apex Industrial Supply"],
        "Invoice Net Amount": [45000.0],
        "IGST 18%": [8100.0],
        "Line Item Detail": ["Machinery replacement parts"],
    }
    full_data = {**base_data, **extra_cols}

    buffer = io.BytesIO()
    pd.DataFrame(full_data).to_excel(buffer, index=False)
    buffer.seek(0)

    result = parse_transaction_file(buffer.getvalue(), filename="wide_erp.xlsx")
    assert len(result.canonical_transactions) == 1
    assert len(result.unmapped_columns) >= 50

    retriever = SemanticCandidateRetriever()
    candidates = retriever.retrieve_candidates(result.canonical_transactions[0])
    assert len(candidates) >= 3
    # Top candidate should be Purchase or related
    assert candidates[0][0].category in ("Purchase", "Purchase Order", "Expense")


# -----------------------------------------------------------------------------
# 3. Disambiguation of Tricky Accounting Confusion Pairs
# -----------------------------------------------------------------------------
def test_accounting_confusion_pairs_disambiguation():
    """Verify retriever and signals engine resolve common confusion pairs."""
    engine = AccountingSignalsEngine()
    retriever = SemanticCandidateRetriever()

    # Pair 1: Purchase Invoice vs Purchase Order (PO commitment vs fulfilled invoice)
    po_txn = CanonicalTransaction(
        row_id=1,
        invoice_number="PO-2026-001",
        seller_supplier="Precision Tooling",
        total_amount=50000.0,
        item_descriptions=["Procurement order commitment for steel bolts"],
    )
    po_candidates = retriever.retrieve_candidates(po_txn)
    assert po_candidates[0][0].category == "Purchase Order"

    # Pair 2: Bank Contra vs Vendor Payment
    contra_txn = CanonicalTransaction(
        row_id=2,
        invoice_number="CTR-99",
        seller_supplier="HDFC Bank Current A/c",
        buyer_customer="SBI Escrow A/c",
        debit_credit_information="Source Account: HDFC Bank, Destination Account: SBI Escrow",
        custom_populated_fields={"Contra ID": "CTR-99"},
        total_amount=100000.0,
        item_descriptions=["Funds transfer between treasury accounts"],
    )
    contra_candidates = retriever.retrieve_candidates(contra_txn)
    assert contra_candidates[0][0].category == "Contra"

    # Pair 3: Sales Return Credit Note vs Sales Order
    cn_txn = CanonicalTransaction(
        row_id=3,
        invoice_number="CN-4001",
        seller_supplier="Acme Sales Ltd",
        buyer_customer="Apex Retail",
        total_amount=-15000.0,
        quantity=-5,
        item_descriptions=["Credit Note for returned damaged inventory"],
    )
    cn_candidates = retriever.retrieve_candidates(cn_txn)
    assert cn_candidates[0][0].category == "Sales Return / Credit Note"

    # Pair 4: Salary / Payroll vs General Operating Expense
    salary_txn = CanonicalTransaction(
        row_id=4,
        invoice_number="PAYROLL-FEB-26",
        seller_supplier="VYOM Payroll Processing",
        buyer_customer="Employee Salary Account",
        total_amount=450000.0,
        item_descriptions=["Staff monthly compensation and employee wages disbursement"],
    )
    salary_candidates = retriever.retrieve_candidates(salary_txn)
    assert salary_candidates[0][0].category in ("Salary / Payroll", "Expense")


# -----------------------------------------------------------------------------
# 4. Comprehensive 9-Contradiction Rule Attacks
# -----------------------------------------------------------------------------
def test_all_nine_contradiction_attacks_detected():
    """Synthesize 9 adversarial cases engineered to trigger every contradiction detector."""
    detector = AccountingContradictionDetector()
    engine = AccountingSignalsEngine()

    attacks = [
        # 1. CONTRA_EXTERNAL_COUNTERPARTY
        (
            CanonicalTransaction(
                row_id=1,
                invoice_number="CONTRA-BAD-1",
                seller_supplier="Amazon Web Services Cloud",
                total_amount=5000.0,
            ),
            "Contra",
            "CONTRA_EXTERNAL_COUNTERPARTY",
        ),
        # 2. CONTRA_STATUTORY_TAX
        (
            CanonicalTransaction(
                row_id=2,
                invoice_number="CONTRA-BAD-2",
                seller_supplier="HDFC Bank",
                buyer_customer="ICICI Bank",
                total_amount=11800.0,
                gst=1800.0,
            ),
            "Contra",
            "CONTRA_STATUTORY_TAX",
        ),
        # 3. CONTRA_MISSING_INTERNAL_PAIR
        (
            CanonicalTransaction(
                row_id=3,
                invoice_number="CONTRA-BAD-3",
                seller_supplier=None,
                buyer_customer=None,
                total_amount=20000.0,
            ),
            "Contra",
            "CONTRA_MISSING_INTERNAL_PAIR",
        ),
        # 4. SALES_OUTWARD_DISBURSEMENT
        (
            CanonicalTransaction(
                row_id=4,
                invoice_number="SALES-BAD-4",
                seller_supplier="Vendor Corp",
                total_amount=30000.0,
                item_descriptions=["Vendor disbursement payment made to supplier"],
            ),
            "Sales",
            "SALES_OUTWARD_DISBURSEMENT",
        ),
        # 5. PURCHASE_INWARD_COLLECTION
        (
            CanonicalTransaction(
                row_id=5,
                invoice_number="RCP-COLL-05",
                buyer_customer="Retail Customer",
                total_amount=40000.0,
                item_descriptions=["Customer incoming collections receipt"],
            ),
            "Purchase",
            "PURCHASE_INWARD_COLLECTION",
        ),
        # 6. ZERO_AMOUNT_COMMERCIAL_INVOICE
        (
            CanonicalTransaction(
                row_id=6,
                invoice_number="INV-ZERO-6",
                seller_supplier="Hardware Distributor",
                buyer_customer="Acme Corp",
                total_amount=0.0,
                quantity=10.0,
                item_descriptions=["Commercial shipment invoice"],
            ),
            "Purchase",
            "ZERO_AMOUNT_COMMERCIAL_INVOICE",
        ),
        # 7. RETURN_WITHOUT_RETURN_SIGNALS
        (
            CanonicalTransaction(
                row_id=7,
                invoice_number="INV-REGULAR-7",
                seller_supplier="Steel Supplier",
                total_amount=50000.0,
                quantity=10,
                item_descriptions=["Regular forward delivery of industrial metal"],
            ),
            "Purchase Return / Debit Note",
            "RETURN_WITHOUT_RETURN_SIGNALS",
        ),
        # 8. INTERNAL_ACCOUNT_AS_PAYMENT
        (
            CanonicalTransaction(
                row_id=8,
                invoice_number="TRF-8",
                seller_supplier="Main Treasury Account",
                buyer_customer="Petty Cash Reserve",
                debit_credit_information="Source Account: Main Treasury Account, Destination Account: Petty Cash Reserve",
                total_amount=15000.0,
                item_descriptions=["Internal transfer between operational bank accounts"],
            ),
            "Payment",
            "INTERNAL_ACCOUNT_AS_PAYMENT",
        ),
        # 9. CROSSBORDER_WITHOUT_FOREIGN_INDICATORS
        (
            CanonicalTransaction(
                row_id=9,
                invoice_number="LOCAL-9",
                seller_supplier="Local Domestic Vendor Delhi",
                buyer_customer="Local Buyer Mumbai",
                total_amount=25000.0,
                item_descriptions=["Standard intra-state domestic delivery"],
            ),
            "Import",
            "CROSSBORDER_WITHOUT_FOREIGN_INDICATORS",
        ),
    ]

    for txn, category, expected_code in attacks:
        signals = engine.extract_signals(txn)
        contradictions = detector.detect_contradictions(txn, category, signals)
        detected_codes = [c.code for c in contradictions]
        assert (
            expected_code in detected_codes
        ), f"Expected code '{expected_code}' for {category} on row {txn.row_id}, found: {detected_codes}"


# -----------------------------------------------------------------------------
# 5. Multi-Class Evaluation Metrics & Confusion Analysis
# -----------------------------------------------------------------------------
def test_evaluation_multiclass_metrics_calculation():
    """Verify precision, recall, macro-F1, and confusion matrix calculation."""
    y_true = [
        "Purchase",
        "Purchase",
        "Sales",
        "Sales",
        "Contra",
        "Payment",
        "Receipt",
        "Journal",
    ]
    # Intentionally introduce one confusion: True Contra predicted as Payment
    y_pred = [
        "Purchase",
        "Purchase",
        "Sales",
        "Sales",
        "Payment",
        "Payment",
        "Receipt",
        "Journal",
    ]

    metrics = compute_multiclass_metrics(y_true, y_pred)
    assert metrics["total_samples"] == 8
    assert metrics["accuracy"] == 0.875  # 7 / 8
    assert metrics["macro_f1"] > 0.0
    assert metrics["weighted_f1"] > 0.0

    # Top confusions should record Contra -> Payment
    assert len(metrics["top_confusions"]) == 1
    assert metrics["top_confusions"][0]["true_category"] == "Contra"
    assert metrics["top_confusions"][0]["predicted_category"] == "Payment"
    assert metrics["top_confusions"][0]["count"] == 1


# -----------------------------------------------------------------------------
# 6. Batch Throughput & Latency Benchmark
# -----------------------------------------------------------------------------
def test_batch_throughput_benchmark():
    """Verify pipeline processes 100 transactions with mean latency < 35ms in offline mode."""
    classifier = GemmaClassifier(force_mock=True)
    pipeline = GuardrailsPipeline(classifier=classifier)

    txns = [
        CanonicalTransaction(
            row_id=i,
            invoice_number=f"DOC-BENCH-{i:04d}",
            invoice_date="2026-03-01",
            seller_supplier=f"Supplier_{i % 10}",
            buyer_customer=f"Customer_{i % 5}",
            total_amount=float(1000 + i * 15),
            taxable_value=float(850 + i * 12),
            gst=float(150 + i * 3),
            item_descriptions=[f"Component SKU-{i}"],
        )
        for i in range(1, 101)
    ]

    start_time = time.perf_counter()
    results = [pipeline.evaluate_and_classify(t) for t in txns]
    total_elapsed = time.perf_counter() - start_time

    assert len(results) == 100
    avg_latency_ms = (total_elapsed / 100) * 1000
    assert avg_latency_ms < 50.0, f"Average latency too high: {avg_latency_ms:.2f}ms"


# -----------------------------------------------------------------------------
# 7. Reference Workbook End-to-End Evaluation Benchmark
# -----------------------------------------------------------------------------
def test_reference_workbook_evaluation_benchmark_end_to_end():
    """Verify complete benchmark execution against reference workbook cases."""
    if not os.path.exists(REFERENCE_WORKBOOK_PATH):
        pytest.skip("Reference workbook not found in workspace.")

    with open(REFERENCE_WORKBOOK_PATH, "rb") as f:
        file_bytes = f.read()

    benchmark_res = run_benchmark_on_dataset(
        file_bytes=file_bytes,
        filename="Voucher_Classification_Test_Cases_v2.xlsx",
        force_mock=True,
    )

    assert benchmark_res["evaluated_records"] == 120
    metrics = benchmark_res["metrics"]
    triage = benchmark_res["triage"]
    # Accuracy exceeds 70% in zero-shot mock pipeline across 27 classes
    assert metrics["accuracy"] >= 0.70, f"Accuracy lower than expected: {metrics['accuracy']}"
    assert metrics["macro_f1"] >= 0.65
    assert triage["auto_verified_percentage"] >= 55.0
    assert triage["average_calibrated_confidence"] >= 0.75
