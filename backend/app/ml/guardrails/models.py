"""Data models for accounting guardrails, confidence calibration, and review triage."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConfidenceTier(str, Enum):
    """Calibrated confidence tier determining downstream automation vs review."""
    HIGH = "HIGH"          # >= 0.85: Safe for automated straight-through ledger posting
    MEDIUM = "MEDIUM"      # 0.65 - 0.84: Qualified confidence; recommended for auditor check or second-pass
    LOW = "LOW"            # < 0.65: Low reliability or contradicted; mandatory human review


class TriageDecision(str, Enum):
    """Operational triage decision for workflow routing."""
    AUTO_VERIFIED = "AUTO_VERIFIED"                # Passed all guardrails with high confidence
    FLAGGED_FOR_REVIEW = "FLAGGED_FOR_REVIEW"      # Routed to human reviewer queue
    CRITICAL_REJECTION = "CRITICAL_REJECTION"      # Severe structural contradiction; blocked from posting


class ContradictionSeverity(str, Enum):
    """Severity of detected accounting domain contradiction."""
    CRITICAL = "CRITICAL"    # Violates fundamental double-entry rule (e.g. Contra with external vendor)
    WARNING = "WARNING"      # Anomaly or mismatch requiring verification (e.g. Return without negative quantity)
    INFO = "INFO"            # Informational observation (e.g. Non-standard payment method)


class AccountingContradiction(BaseModel):
    """Structured record of an accounting domain contradiction."""

    code: str = Field(..., description="Unique machine-readable error code (e.g. 'CONTRA_EXTERNAL_COUNTERPARTY')")
    severity: ContradictionSeverity = Field(..., description="Severity level of the contradiction")
    title: str = Field(..., description="Human-readable summary title")
    message: str = Field(..., description="Detailed explanation of the contradiction")
    conflicting_fields: List[str] = Field(default_factory=list, description="Fields involved in the conflict")
    suggested_action: str = Field(..., description="Recommended remediation or alternate category candidate")


class GuardrailEvaluation(BaseModel):
    """Complete audit-grade evaluation result for a voucher prediction."""

    row_id: int = Field(..., description="Stable 1-indexed row number from dataset")
    predicted_category: str = Field(..., description="Voucher category under evaluation")
    raw_model_confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence reported by LLM or mock adapter")
    retriever_affinity: float = Field(..., ge=0.0, le=1.0, description="Relevance score from semantic candidate retriever")
    signal_compatibility: float = Field(..., ge=0.0, le=1.0, description="Accounting signal flow and entity compatibility score")
    calibrated_confidence: float = Field(..., ge=0.0, le=1.0, description="Calibrated final reliability score")
    confidence_tier: ConfidenceTier = Field(..., description="High, Medium, or Low confidence classification")
    contradictions: List[AccountingContradiction] = Field(default_factory=list, description="Detected accounting contradictions")
    triage_decision: TriageDecision = Field(..., description="Workflow triage routing decision")
    requires_second_pass: bool = Field(default=False, description="Whether second-pass arbitration was triggered")
    second_pass_applied: bool = Field(default=False, description="Whether second-pass reasoning completed")
    second_pass_category: Optional[str] = Field(default=None, description="Adjusted or confirmed category after second-pass")
    second_pass_justification: Optional[str] = Field(default=None, description="Reasoning narrative explaining second-pass arbitration")
    audit_notes: List[str] = Field(default_factory=list, description="Audit log trail detailing score calculations")
