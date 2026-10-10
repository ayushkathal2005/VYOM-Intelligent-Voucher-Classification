"""Semantic Candidate Retriever ranking the 27 authoritative voucher cards for any transaction."""

from typing import Any, Dict, List, Tuple, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.ingestion.schema import CanonicalTransaction
from app.ml.baseline import extract_text_representation
from app.ml.signals.models import MoneyFlowDirection, EntityRole, AccountingSignalProfile
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.signals.voucher_cards import VOUCHER_CARDS, VoucherKnowledgeCard

# Authoritative prefix to voucher category mapping common across enterprise ERPs (Tally, SAP, Oracle)
ERP_PREFIX_MAP: Dict[str, str] = {
    "pur-": "Purchase",
    "sal-": "Sales",
    "dbn-": "Purchase Return / Debit Note",
    "crn-": "Sales Return / Credit Note",
    "pay-": "Payment",
    "pmt-": "Payment",
    "rcpt-": "Receipt",
    "rct-": "Receipt",
    "rec-": "Receipt",
    "cnt-": "Contra",
    "jv-": "Journal",
    "po-": "Purchase Order",
    "so-": "Sales Order",
    "dc": "Delivery Note",
    "grn": "Receipt Note",
    "rjn-in": "Rejection In",
    "rjn-out": "Rejection Out",
    "stk-adj": "Stock Journal",
    "stk-cnt": "Physical Stock",
    "jwio": "Job Work - In Order",
    "jwoo": "Job Work Out Order",
    "mat-in": "Material In",
    "mat-out": "Material Out",
    "exp": "Export",
    "imp": "Import",
    "emp": "Salary / Payroll",
    "att": "Attendance",
    "exp-clm": "Expense",
    "adv": "Advance / Prepayment",
}


class SemanticCandidateRetriever:
    """
    Retrieves and ranks the most relevant candidate voucher categories for a transaction.
    Combines TF-IDF card semantic similarity, accounting money-flow compatibility,
    document identifier/prefix resolution, and domain disambiguation rules.
    """

    def __init__(self):
        self.categories = list(VOUCHER_CARDS.keys())
        self.cards = [VOUCHER_CARDS[cat] for cat in self.categories]

        # Build comprehensive corpus of card knowledge for TF-IDF index
        self.corpus = []
        for card in self.cards:
            doc = (
                f"{card.category} {card.description} "
                f"{' '.join(card.primary_identifiers)} "
                f"{' '.join(card.typical_ledgers)} "
                f"{' '.join(card.key_signals)}"
            )
            self.corpus.append(doc)

        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        self.card_vectors = self.vectorizer.fit_transform(self.corpus)

    def retrieve_candidates(
        self,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Tuple[VoucherKnowledgeCard, float]]:
        """
        Rank the 27 voucher cards for the given transaction and return top_k candidates with relevance scores.
        """
        if isinstance(txn, CanonicalTransaction):
            text = txn.compact_representation()
            quantity = txn.quantity
        else:
            text = extract_text_representation(txn)
            raw_qty = txn.get("quantity") or txn.get("units")
            try:
                quantity = float(raw_qty) if raw_qty is not None else None
            except (ValueError, TypeError):
                quantity = None

        text_lower = text.lower()
        signals_profile = AccountingSignalsEngine.extract_signals(txn)

        # 1. Base TF-IDF Cosine Similarity against 27 Knowledge Cards
        txn_vec = self.vectorizer.transform([text])
        sim_scores = cosine_similarity(txn_vec, self.card_vectors)[0]

        combined_scores: List[Tuple[VoucherKnowledgeCard, float]] = []

        # Return signal detection
        is_return_signal = (
            signals_profile.has_negative_quantity
            or (quantity is not None and quantity < 0)
            or any(k in text_lower for k in ("return", "dbn", "crn", "units returned", "reason for return"))
        )

        # Cross-border international trade detection
        is_crossborder = signals_profile.has_customs_or_crossborder or any(
            k in text_lower for k in ("export invoice", "import bill", "destination country", "originating country", "customs duty", "trade:", "cif", "fob")
        )

        for idx, card in enumerate(self.cards):
            cat = card.category
            # Base similarity (0.25 max)
            score = float(sim_scores[idx]) * 0.25

            # 2. Money Flow Compatibility (Weight: 0.20)
            if is_return_signal and "Return" in cat:
                score += 0.20
            elif card.expected_flow == signals_profile.money_flow:
                score += 0.20
            elif card.expected_flow == MoneyFlowDirection.UNKNOWN:
                score += 0.08

            # 3. Direct Document / Voucher Prefix Match (Weight: 0.35)
            for prefix, mapped_cat in ERP_PREFIX_MAP.items():
                if prefix in text_lower:
                    if cat == mapped_cat:
                        score += 0.35
                    elif mapped_cat in card.common_confusion_pairs:
                        score += 0.12

            # 4. Return Disambiguation
            if is_return_signal:
                if cat in ("Purchase Return / Debit Note", "Sales Return / Credit Note"):
                    score += 0.25
                    if "dbn" in text_lower or "supplier" in text_lower or "vendor" in text_lower or "pur-" in text_lower:
                        if cat == "Purchase Return / Debit Note":
                            score += 0.20
                    if "crn" in text_lower or "customer" in text_lower or "buyer" in text_lower or "sal-" in text_lower:
                        if cat == "Sales Return / Credit Note":
                            score += 0.20

            # 5. Cross-Border International Trade Disambiguation
            if is_crossborder:
                if cat in ("Export", "Import"):
                    score += 0.25
                    if any(k in text_lower for k in ("destination country", "exporter", "fob", "units exported")) or "doc_no: exp" in text_lower or "exp" in text_lower:
                        if cat == "Export":
                            score += 0.20
                    if any(k in text_lower for k in ("originating country", "importer", "cif", "customs duty", "units imported")) or "doc_no: imp" in text_lower or "imp" in text_lower:
                        if cat == "Import":
                            score += 0.20

            # 6. Physical Logistics & Warehouse Movements
            if signals_profile.money_flow == MoneyFlowDirection.NON_FINANCIAL_MOVEMENT or any(
                k in text_lower for k in ("grn", "delivery challan", "dc-", "dc", "item received", "item dispatched", "rejection note", "rjn-in", "rjn-out", "stock count", "stock adj")
            ):
                if cat in ("Receipt Note", "Delivery Note", "Rejection In", "Rejection Out", "Stock Journal", "Physical Stock", "Material In", "Material Out"):
                    score += 0.25

            # 7. Internal Treasury Contra vs External Payment/Receipt
            if signals_profile.has_internal_account_pair or signals_profile.money_flow == MoneyFlowDirection.INTERNAL:
                if cat == "Contra":
                    score += 0.40
                elif cat in ("Payment", "Receipt"):
                    score -= 0.20

            # 8. Dual Nominal Ledger Journal Entry
            if signals_profile.money_flow == MoneyFlowDirection.ADJUSTMENT or any(
                k in text_lower for k in ("journal id", "debit side", "credit side", "journal type", "jv-")
            ):
                if cat == "Journal":
                    score += 0.40

            # 9. Workforce Payroll vs Operational Attendance
            if signals_profile.has_employee_metadata or any(
                k in text_lower for k in ("employee code", "gross salary", "payroll period", "net payable", "days worked", "attendance")
            ):
                if cat in ("Salary / Payroll", "Attendance"):
                    score += 0.35

            # 10. Pre-Fulfillment Commercial Orders
            if signals_profile.money_flow == MoneyFlowDirection.ORDER_COMMITMENT:
                if cat in ("Purchase Order", "Sales Order", "Job Work - In Order", "Job Work Out Order"):
                    score += 0.25

            score = max(0.0, min(1.0, score))
            combined_scores.append((card, round(score, 4)))

        # Sort by relevance score descending
        combined_scores.sort(key=lambda x: x[1], reverse=True)
        return combined_scores[:top_k]

    def get_candidate_context(
        self,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        top_k: int = 3,
    ) -> str:
        """
        Generate a concise prompt injection snippet detailing the top candidate definitions and disambiguation rules.
        """
        top_candidates = self.retrieve_candidates(txn, top_k=top_k)
        lines = ["CANDIDATE VOUCHER CATEGORIES (Retrieved by Accounting Semantics):"]
        for rank, (card, score) in enumerate(top_candidates, start=1):
            lines.append(
                f"{rank}. {card.category} (Relevance: {score:.2f})\n"
                f"   Scope: {card.description}\n"
                f"   Disambiguation: {card.disambiguation_rule}"
            )
        return "\n".join(lines)


# Singleton retriever instance
candidate_retriever = SemanticCandidateRetriever()
