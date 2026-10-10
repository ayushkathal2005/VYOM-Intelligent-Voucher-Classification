"""Deterministic mock adapter for Gemma 4 voucher classification.

Provides faithful, structured, and auditable mock classifications for testing and offline development
prior to configuring a live Google Gemini API key.

STRICT TRUTHFULNESS GUARANTEE:
- Always marks output with is_mock=True.
- Model name explicitly declares 'mock-gemma-4-adapter'.
- Does NOT present mock predictions as verified live LLM inference.
"""

import time
import json
from typing import Any, Dict, List, Optional, Tuple, Union

from app.ingestion.schema import CanonicalTransaction
from app.ml.baseline import extract_text_representation
from app.ml.taxonomy import (
    AUTHORITATIVE_VOUCHER_LABELS,
    normalize_voucher_label,
)
from app.ml.gemma.schemas import (
    GemmaVoucherPrediction,
    GemmaClassificationResult,
)


class MockGemmaAdapter:
    """
    Deterministic rule-and-semantic mock adapter for Gemma 4 voucher classification.
    Produces structured, schema-compliant predictions based on detected field patterns.
    """

    @classmethod
    def classify_transaction(
        cls,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
    ) -> GemmaClassificationResult:
        start_time = time.perf_counter()

        if isinstance(txn, CanonicalTransaction):
            row_id = txn.row_id
            text = txn.compact_representation().lower()
            raw = txn.raw_record
        else:
            row_id = txn.get("row_id", 1)
            text = extract_text_representation(txn).lower()
            raw = txn.get("raw_record") or txn

        # Deterministic accounting rule engine
        pred_cat, confidence, alt_cat, alt_conf, reasoning, signals = cls._infer_category_and_signals(text, raw)

        prediction = GemmaVoucherPrediction(
            category=pred_cat,
            confidence=confidence,
            alternative_category=alt_cat,
            alternative_confidence=alt_conf,
            reasoning=reasoning,
            detected_signals=signals,
            review_recommended=confidence < 0.75,
        )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        raw_output_json = json.dumps(prediction.model_dump(), indent=2)

        return GemmaClassificationResult(
            row_id=row_id,
            prediction=prediction,
            model_name="mock-gemma-4-adapter",
            latency_ms=round(latency_ms, 2),
            is_mock=True,
            prompt_tokens=len(text.split()) * 2 + 100,
            completion_tokens=len(reasoning.split()) + 30,
            raw_model_output=raw_output_json,
        )

    @classmethod
    def _infer_category_and_signals(
        cls, text: str, raw: Dict[str, Any]
    ) -> Tuple[str, float, Optional[str], Optional[float], str, List[str]]:
        raw_keys_lower = [str(k).lower() for k in raw.keys() if raw[k] is not None]
        signals: List[str] = []

        # 1. Contra
        if any(k in text for k in ("source account", "destination account", "bank ifsc", "contra id")) or (
            "source_account" in text and "destination_account" in text
        ):
            signals.extend(["internal bank account transfer", "zero external commercial counterparty"])
            return (
                "Contra",
                0.98,
                "Payment",
                0.02,
                "Identified internal fund transfer between source and destination accounts without third-party vendor involvement.",
                signals,
            )

        # 2. Journal
        if any(k in text for k in ("debit side", "credit side", "journal id", "journal type", "adjusting entry")):
            signals.extend(["dual ledger debit/credit posting", "non-cash accounting adjustment"])
            return (
                "Journal",
                0.97,
                "Expense",
                0.03,
                "Classified as Journal entry due to debit/credit ledger side allocations and accounting narration.",
                signals,
            )

        # 3. Attendance
        if any(k in text for k in ("attendance", "biometric", "days worked", "overtime", "timesheet")):
            signals.extend(["biometric timesheet log", "non-monetary shift record"])
            return (
                "Attendance",
                0.96,
                "Salary / Payroll",
                0.04,
                "Identified non-monetary employee attendance and shift log record.",
                signals,
            )

        # 4. Salary / Payroll
        if any(k in text for k in ("payroll period", "gross salary", "net payable", "dearness allowance", "professional tax")):
            signals.extend(["payroll disbursement period", "statutory tax deduction"])
            return (
                "Salary / Payroll",
                0.98,
                "Expense",
                0.02,
                "Classified as Salary / Payroll based on employee compensation schedule, payroll period, and tax deductions.",
                signals,
            )

        # 5. Import
        if any(k in text for k in ("import bill no", "customs duty", "cost insurance freight", "import gst", "cif")):
            signals.extend(["foreign customs bill of entry", "cross-border import duties"])
            return (
                "Import",
                0.98,
                "Purchase",
                0.02,
                "Recognized international trade import transaction with statutory customs duty and CIF valuation.",
                signals,
            )

        # 6. Export
        if any(k in text for k in ("export invoice no", "free on board", "export incentive", "destination country", "fob")):
            signals.extend(["foreign buyer shipping invoice", "FOB value with export incentive"])
            return (
                "Export",
                0.98,
                "Sales",
                0.02,
                "Recognized foreign trade export shipment with FOB valuation and cross-border destination.",
                signals,
            )

        # 7. Purchase Order
        if any(k in text for k in ("po number", "quantity required", "promised delivery", "order_ref: po")):
            signals.extend(["procurement order authorization", "promised delivery schedule"])
            return (
                "Purchase Order",
                0.97,
                "Purchase",
                0.03,
                "Identified prospective Purchase Order specifying required quantities, unit rate, and delivery terms.",
                signals,
            )


        # 8. Sales Order
        if any(k in text for k in ("so number", "quantity ordered", "selling company", "payment terms", "so date")):
            signals.extend(["customer commercial booking", "agreed payment terms"])
            return (
                "Sales Order",
                0.97,
                "Sales",
                0.03,
                "Identified commercial Sales Order acknowledging customer demand with delivery commitments.",
                signals,
            )

        # 9. Receipt Note (GRN)
        if any(k in text for k in ("grn number", "item received", "quantity received", "quality status", "receiving company")):
            signals.extend(["warehouse goods receipt note (GRN)", "quality inspection passed"])
            return (
                "Receipt Note",
                0.97,
                "Material In",
                0.03,
                "Classified as Receipt Note based on warehouse GRN number, item receipt inspection, and storage logging.",
                signals,
            )

        # 10. Delivery Note
        if any(k in text for k in ("delivery challan no", "dispatch date", "item dispatched", "quantity shipped", "courier/transport")):
            signals.extend(["dispatch challan", "carrier logistics transport"])
            return (
                "Delivery Note",
                0.97,
                "Material Out",
                0.03,
                "Classified as Delivery Note due to outbound dispatch challan, shipment quantities, and transport carrier details.",
                signals,
            )

        # 11. Rejection In
        if "rejection note" in text and any(k in text for k in ("receiving company", "grn reference", "approved by")):
            signals.extend(["inward rejected inventory return", "GRN reference linkage"])
            return (
                "Rejection In",
                0.96,
                "Purchase Return / Debit Note",
                0.04,
                "Classified as Rejection In based on inward rejected materials logged against receiving company GRN.",
                signals,
            )

        # 12. Rejection Out
        if "rejection note" in text and any(k in text for k in ("customer", "dn reference", "authorized by", "rjn-out")):
            signals.extend(["outward rejected shipment", "delivery note reference linkage"])
            return (
                "Rejection Out",
                0.96,
                "Sales Return / Credit Note",
                0.04,
                "Classified as Rejection Out based on customer shipment rejection linked to dispatch delivery note.",
                signals,
            )

        # 13. Purchase Return / Debit Note
        if (any(k in text for k in ("units returned", "reason for return", "dbn-", "original doc ref")) or "debit note" in text) and (
            "vendor" in text or "pur-" in text or "heavy machinery" in text
        ):
            signals.extend(["debit note document reference", "outward goods return to supplier"])
            return (
                "Purchase Return / Debit Note",
                0.97,
                "Purchase",
                0.03,
                "Identified Purchase Return / Debit Note recording returned units and debit note linkage to original purchase.",
                signals,
            )

        # 14. Sales Return / Credit Note
        if any(k in text for k in ("crn-", "original invoice ref", "credit note")) or (
            "units returned" in text and "sal-" in text
        ):
            signals.extend(["credit note document reference", "customer return acknowledgment"])
            return (
                "Sales Return / Credit Note",
                0.97,
                "Sales",
                0.03,
                "Identified Sales Return / Credit Note documenting customer product return and credit liability adjustments.",
                signals,
            )

        # 15. Material In
        if any(k in text for k in ("inward job work no", "quantity sent", "date of dispatch", "miw")):
            signals.extend(["subcontracting inward material intake", "job work reference"])
            return (
                "Material In",
                0.96,
                "Receipt Note",
                0.04,
                "Classified as Material In tracking job work input materials sent by principal/subcontractor.",
                signals,
            )

        # 16. Material Out
        if any(k in text for k in ("outward job work no", "quantity received", "date of receipt", "mow")):
            signals.extend(["subcontracting outward material dispatch", "job work contractor receipt"])
            return (
                "Material Out",
                0.96,
                "Delivery Note",
                0.04,
                "Classified as Material Out documenting processed material return or contractor job work dispatch.",
                signals,
            )

        # 17. Job Work In Order
        if any(k in text for k in ("jwio ref", "processing rate", "jwio")):
            signals.extend(["incoming job work order", "agreed processing fee"])
            return (
                "Job Work In Order",
                0.96,
                "Job Work Out Order",
                0.04,
                "Identified Job Work In Order contracting processing services for principal-supplied materials.",
                signals,
            )

        # 18. Job Work Out Order
        if any(k in text for k in ("jwoo ref", "service charge", "jwoo")):
            signals.extend(["outgoing subcontracting order", "vendor processing agreement"])
            return (
                "Job Work Out Order",
                0.96,
                "Job Work In Order",
                0.04,
                "Identified Job Work Out Order outsourcing manufacturing operations to third-party contractor.",
                signals,
            )

        # 19. Physical Stock
        if any(k in text for k in ("stock count id", "book quantity", "counted quantity", "discrepancy", "variance status")):
            signals.extend(["physical inventory audit count", "book-to-physical quantity discrepancy"])
            return (
                "Physical Stock",
                0.98,
                "Stock Journal",
                0.02,
                "Classified as Physical Stock reconciling physical count against book inventory records.",
                signals,
            )

        # 20. Stock Journal
        if any(k in text for k in ("stock adj id", "adjustment qty", "storage facility", "adjusted by")):
            signals.extend(["inventory adjustment revaluation", "storage location reallocation"])
            return (
                "Stock Journal",
                0.97,
                "Physical Stock",
                0.03,
                "Classified as Stock Journal reflecting ledger adjustment and inventory reallocation.",
                signals,
            )

        # 21. Expense
        if any(k in text for k in ("expense claim no", "amount claimed", "expense type", "vendor/provider", "department")):
            signals.extend(["corporate expense reimbursement", "departmental operational claim"])
            return (
                "Expense",
                0.97,
                "Payment",
                0.03,
                "Classified as Expense claim recording operational departmental expenditures and reimbursements.",
                signals,
            )

        # 22. Payment
        if any(k in text for k in ("payment id", "payer organization", "payee organization", "payment amount", "payment type")):
            signals.extend(["outward disbursement to payee", "invoice settlement"])
            return (
                "Payment",
                0.97,
                "Receipt",
                0.03,
                "Classified as Payment recording financial disbursement to payee organization against an invoice.",
                signals,
            )

        # 23. Receipt
        if any(k in text for k in ("receipt id", "receiving organization", "paying organization", "received amount", "payment method")):
            signals.extend(["inward collection from paying organization", "funds settlement"])
            return (
                "Receipt",
                0.97,
                "Payment",
                0.03,
                "Classified as Receipt recording inward monetary collection into receiving organization accounts.",
                signals,
            )

        # 24. Advance / Prepayment
        if any(k in text for k in ("advance", "prepayment", "proforma")):
            signals.extend(["pre-billing cash consideration", "advance booking payment"])
            return (
                "Advance / Prepayment",
                0.95,
                "Payment",
                0.05,
                "Identified Advance / Prepayment transaction executed prior to commercial invoice finalization.",
                signals,
            )

        # 25. Purchase vs Sales (General Invoices)
        if "po ref" in text or "pur-" in text:
            signals.extend(["vendor supplier payable invoice", "PO reference confirmation"])
            return (
                "Purchase",
                0.96,
                "Sales",
                0.04,
                "Classified as Purchase tax invoice based on supplier vendor billing and PO reference linkage.",
                signals,
            )

        if "delivery ref" in text or "sal-" in text:
            signals.extend(["customer receivable billing", "delivery challan linkage"])
            return (
                "Sales",
                0.96,
                "Purchase",
                0.04,
                "Classified as Sales tax invoice based on customer billing and delivery reference linkage.",
                signals,
            )

        # Default fallback
        signals.append("general commercial transaction")
        return (
            "Other / Miscellaneous",
            0.65,
            "Journal",
            0.35,
            "Classified as Other / Miscellaneous due to insufficient distinguishing accounting indicators; human review recommended.",
            signals,
        )
