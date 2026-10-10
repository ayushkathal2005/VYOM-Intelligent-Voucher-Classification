"""Confidence calibration and review triage scoring engine."""

from typing import Any, Dict, List, Tuple, Union
from app.ingestion.schema import CanonicalTransaction
from app.ml.signals.models import MoneyFlowDirection, AccountingSignalProfile
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.signals.voucher_cards import VOUCHER_CARDS
from app.ml.signals.retriever import candidate_retriever
from app.ml.guardrails.models import (
    AccountingContradiction,
    ConfidenceTier,
    ContradictionSeverity,
    TriageDecision,
)


class ConfidenceScorer:
    """
    Computes calibrated reliability scores and operational triage routing
    by synthesizing model confidence, semantic retriever affinity,
    accounting signal compatibility, and contradiction deductions.
    """

    @classmethod
    def calculate_signal_compatibility(
        cls,
        category: str,
        profile: AccountingSignalProfile,
    ) -> float:
        """Evaluate how cleanly the predicted category aligns with the derived accounting signal profile."""
        card = VOUCHER_CARDS.get(category)
        if not card:
            return 0.50

        # Return compatibility
        if "Return" in category and profile.has_negative_quantity:
            return 1.0

        if card.expected_flow == profile.money_flow:
            return 1.0

        if card.expected_flow == MoneyFlowDirection.UNKNOWN or profile.money_flow == MoneyFlowDirection.UNKNOWN:
            return 0.70

        # Partial compatibility between order commitments and underlying procurement/sales
        if profile.money_flow == MoneyFlowDirection.ORDER_COMMITMENT and category in ("Purchase Order", "Sales Order", "Job Work - In Order", "Job Work Out Order"):
            return 1.0

        if profile.money_flow == MoneyFlowDirection.NON_FINANCIAL_MOVEMENT and category in (
            "Delivery Note", "Receipt Note", "Rejection In", "Rejection Out", "Stock Journal", "Physical Stock", "Material In", "Material Out"
        ):
            return 1.0

        # Direct flow conflict
        if (card.expected_flow == MoneyFlowDirection.INFLOW and profile.money_flow == MoneyFlowDirection.OUTFLOW) or (
            card.expected_flow == MoneyFlowDirection.OUTFLOW and profile.money_flow == MoneyFlowDirection.INFLOW
        ):
            return 0.15

        return 0.50

    @classmethod
    def score_prediction(
        cls,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        category: str,
        raw_confidence: float,
        contradictions: List[AccountingContradiction],
        signals_profile: Union[AccountingSignalProfile, None] = None,
        retriever_top_candidates: Union[List[Tuple[Any, float]], None] = None,
    ) -> Tuple[float, float, float, ConfidenceTier, TriageDecision, List[str]]:
        """
        Calculate calibrated confidence, confidence tier, triage decision, and audit trail notes.
        Returns: (calibrated_confidence, retriever_affinity, signal_compatibility, tier, triage, notes)
        """
        if signals_profile is None:
            signals_profile = AccountingSignalsEngine.extract_signals(txn)

        if retriever_top_candidates is None:
            retriever_top_candidates = candidate_retriever.retrieve_candidates(txn, top_k=5)

        # 1. Retrieve Candidate Affinity (Rank + Relative Score normalization)
        top_score = float(retriever_top_candidates[0][1]) if retriever_top_candidates else 1.0
        top_score = max(top_score, 0.01)

        rank_found = None
        cand_score = 0.0
        for rank, (card, score) in enumerate(retriever_top_candidates, start=1):
            if card.category == category:
                rank_found = rank
                cand_score = float(score)
                break

        if rank_found == 1:
            retriever_affinity = 1.00
        elif rank_found == 2:
            retriever_affinity = round(0.85 * min(1.0, cand_score / top_score), 4)
        elif rank_found == 3:
            retriever_affinity = round(0.70 * min(1.0, cand_score / top_score), 4)
        elif rank_found == 4:
            retriever_affinity = round(0.55 * min(1.0, cand_score / top_score), 4)
        elif rank_found == 5:
            retriever_affinity = round(0.40 * min(1.0, cand_score / top_score), 4)
        else:
            retriever_affinity = 0.15

        # 2. Signal Compatibility
        signal_compatibility = cls.calculate_signal_compatibility(category, signals_profile)

        # 3. Base Synthesis (50% Model, 30% Retriever, 20% Signal Alignment)
        bounded_raw = max(0.0, min(1.0, float(raw_confidence)))
        base_score = (0.50 * bounded_raw) + (0.30 * retriever_affinity) + (0.20 * signal_compatibility)

        # 4. Contradiction Penalty Assessment
        penalties = 0.0
        critical_count = 0
        warning_count = 0
        audit_notes: List[str] = [
            f"Base confidence synthesized: {base_score:.3f} (Model: {bounded_raw:.2f}, Retriever: {retriever_affinity:.2f}, Signal: {signal_compatibility:.2f})"
        ]

        for c in contradictions:
            if c.severity == ContradictionSeverity.CRITICAL:
                penalties += 0.35
                critical_count += 1
                audit_notes.append(f"CRITICAL penalty (-0.35): {c.code}")
            elif c.severity == ContradictionSeverity.WARNING:
                penalties += 0.12
                warning_count += 1
                audit_notes.append(f"WARNING penalty (-0.12): {c.code}")
            elif c.severity == ContradictionSeverity.INFO:
                penalties += 0.04
                audit_notes.append(f"INFO penalty (-0.04): {c.code}")

        calibrated = max(0.05, min(0.99, base_score - penalties))
        calibrated = round(calibrated, 4)
        audit_notes.append(f"Final calibrated reliability score: {calibrated:.4f}")

        # 5. Tier & Triage Routing
        if critical_count > 0:
            tier = ConfidenceTier.LOW
            triage = TriageDecision.CRITICAL_REJECTION
            audit_notes.append("Routed to CRITICAL_REJECTION due to severe structural contradiction.")
        elif calibrated >= 0.85:
            tier = ConfidenceTier.HIGH
            triage = TriageDecision.AUTO_VERIFIED
            audit_notes.append("Routed to AUTO_VERIFIED for straight-through automated posting.")
        elif calibrated >= 0.65:
            tier = ConfidenceTier.MEDIUM
            triage = TriageDecision.FLAGGED_FOR_REVIEW
            audit_notes.append("Routed to FLAGGED_FOR_REVIEW for qualified auditor verification.")
        else:
            tier = ConfidenceTier.LOW
            triage = TriageDecision.FLAGGED_FOR_REVIEW
            audit_notes.append("Routed to FLAGGED_FOR_REVIEW due to low calibrated reliability.")

        return (calibrated, round(retriever_affinity, 4), round(signal_compatibility, 4), tier, triage, audit_notes)
