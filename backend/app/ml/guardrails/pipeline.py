"""Unified guardrails pipeline orchestrating signals, contradictions, scoring, and second-pass reasoning."""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

from app.ingestion.schema import CanonicalTransaction
from app.ml.signals.models import AccountingSignalProfile
from app.ml.signals.engine import AccountingSignalsEngine
from app.ml.signals.retriever import candidate_retriever
from app.ml.gemma.client import GemmaClassifier
from app.ml.gemma.schemas import GemmaClassificationResult, GemmaVoucherPrediction
from app.ml.guardrails.models import (
    ConfidenceTier,
    ContradictionSeverity,
    GuardrailEvaluation,
    TriageDecision,
)
from app.ml.guardrails.detector import AccountingContradictionDetector
from app.ml.guardrails.scorer import ConfidenceScorer
from app.ml.guardrails.second_pass import SecondPassReasoningEngine

logger = logging.getLogger("vyom.ml.guardrails.pipeline")


class GuardrailsPipeline:
    """
    End-to-end classification and audit guardrail pipeline.
    Combines Gemma 4 classification, contradiction detection,
    confidence calibration, and second-pass arbitration.
    """

    def __init__(self, classifier: Optional[GemmaClassifier] = None):
        self.classifier = classifier or GemmaClassifier()

    def evaluate_and_classify(
        self,
        txn: Union[CanonicalTransaction, Dict[str, Any]],
        existing_result: Optional[GemmaClassificationResult] = None,
    ) -> Tuple[GemmaClassificationResult, GuardrailEvaluation]:
        """
        Execute full guardrail assessment for a transaction, running classification if not already provided.
        Returns: (classification_result, guardrail_evaluation)
        """
        row_id = txn.row_id if isinstance(txn, CanonicalTransaction) else txn.get("row_id", 1)

        # 1. Accounting Signal Profile Extraction
        profile = AccountingSignalsEngine.extract_signals(txn)

        # 2. Semantic Candidate Retrieval
        candidates = candidate_retriever.retrieve_candidates(txn, top_k=5)

        # 3. Model Classification (if not pre-computed)
        if existing_result is not None:
            result = existing_result
        else:
            result = self.classifier.classify_single(txn)

        primary_cat = result.prediction.category
        raw_conf = result.prediction.confidence
        alt_cat = result.prediction.alternative_category
        alt_conf = result.prediction.alternative_confidence

        # 4. First-Pass Contradiction Detection
        contradictions = AccountingContradictionDetector.detect_contradictions(
            txn=txn,
            category=primary_cat,
            signals_profile=profile,
        )

        # 5. First-Pass Confidence Calibration
        (
            calibrated_conf,
            retriever_affinity,
            signal_compat,
            tier,
            triage,
            audit_notes,
        ) = ConfidenceScorer.score_prediction(
            txn=txn,
            category=primary_cat,
            raw_confidence=raw_conf,
            contradictions=contradictions,
            signals_profile=profile,
            retriever_top_candidates=candidates,
        )

        # 6. Second-Pass Trigger Assessment
        margin_close = False
        if alt_cat and alt_conf is not None and abs(raw_conf - alt_conf) <= 0.15:
            margin_close = True

        requires_second_pass = bool(
            calibrated_conf < 0.85 or len(contradictions) > 0 or margin_close
        )

        second_pass_applied = False
        second_pass_cat = None
        second_pass_justification = None

        if requires_second_pass:
            second_pass_applied = True
            had_critical_contradiction = any(
                getattr(c, "severity", None) == ContradictionSeverity.CRITICAL
                or (hasattr(getattr(c, "severity", None), "value") and getattr(c, "severity").value == "CRITICAL")
                or str(getattr(c, "severity", "")).upper() == "CRITICAL"
                for c in contradictions
            )
            second_pass_cat, second_pass_justification = SecondPassReasoningEngine.arbitrate(
                txn=txn,
                primary_category=primary_cat,
                alternative_category=alt_cat,
                contradictions=contradictions,
                signals_profile=profile,
                gemma_classifier=self.classifier,
            )

            # If second-pass re-routed to a new category, re-score under the revised category
            if second_pass_cat != primary_cat:
                audit_notes.append(
                    f"Second-pass re-routed category from '{primary_cat}' to '{second_pass_cat}'."
                )
                revised_contradictions = AccountingContradictionDetector.detect_contradictions(
                    txn=txn,
                    category=second_pass_cat,
                    signals_profile=profile,
                )
                (
                    calibrated_conf,
                    retriever_affinity,
                    signal_compat,
                    tier,
                    triage,
                    revised_notes,
                ) = ConfidenceScorer.score_prediction(
                    txn=txn,
                    category=second_pass_cat,
                    raw_confidence=raw_conf,
                    contradictions=revised_contradictions,
                    signals_profile=profile,
                    retriever_top_candidates=candidates,
                )

                # An initial critical contradiction that was resolved by second pass MUST be verified by a human auditor
                if had_critical_contradiction and triage == TriageDecision.AUTO_VERIFIED:
                    triage = TriageDecision.FLAGGED_FOR_REVIEW
                    tier = ConfidenceTier.MEDIUM
                    revised_notes.append(
                        "Initial critical contradiction arbitrated by second pass; held in FLAGGED_FOR_REVIEW for qualified auditor verification."
                    )

                contradictions = revised_contradictions
                audit_notes.extend(revised_notes)

                # Update prediction container to reflect reconciled category
                result = GemmaClassificationResult(
                    row_id=result.row_id,
                    prediction=GemmaVoucherPrediction(
                        category=second_pass_cat,
                        confidence=calibrated_conf,
                        alternative_category=primary_cat,
                        alternative_confidence=round(calibrated_conf * 0.75, 2),
                        reasoning=second_pass_justification or result.prediction.reasoning,
                        detected_signals=profile.primary_signals,
                        review_recommended=(tier != ConfidenceTier.HIGH),
                    ),
                    model_name=result.model_name,
                    latency_ms=result.latency_ms,
                    is_mock=result.is_mock,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    raw_model_output=result.raw_model_output,
                )
                primary_cat = second_pass_cat

        evaluation = GuardrailEvaluation(
            row_id=row_id,
            predicted_category=primary_cat,
            raw_model_confidence=raw_conf,
            retriever_affinity=retriever_affinity,
            signal_compatibility=signal_compat,
            calibrated_confidence=calibrated_conf,
            confidence_tier=tier,
            contradictions=contradictions,
            triage_decision=triage,
            requires_second_pass=requires_second_pass,
            second_pass_applied=second_pass_applied,
            second_pass_category=second_pass_cat,
            second_pass_justification=second_pass_justification,
            audit_notes=audit_notes,
        )

        return (result, evaluation)


# Singleton default pipeline instance
guardrails_pipeline = GuardrailsPipeline()
