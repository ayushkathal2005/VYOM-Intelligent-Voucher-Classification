"""Pydantic schemas for the VYOM+ REST API."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.ml.guardrails.models import (
    ConfidenceTier,
    TriageDecision,
    GuardrailEvaluation,
)
from app.ml.gemma.schemas import GemmaClassificationResult


# -----------------------------------------------------------------------------
# Dataset Schemas
# -----------------------------------------------------------------------------
class DatasetUploadResponse(BaseModel):
    """Metadata response after successful workbook or CSV upload."""

    dataset_id: str = Field(..., description="Unique UUID identifier for the uploaded dataset")
    filename: str = Field(..., description="Original uploaded filename")
    total_rows: int = Field(..., description="Total data rows parsed")
    columns_detected: List[str] = Field(..., description="All raw column headers discovered")
    canonical_fields_mapped: Dict[str, str] = Field(..., description="Mapping of raw header to canonical attribute")
    unmapped_columns: List[str] = Field(..., description="Columns preserved in custom populated fields")
    warnings: List[str] = Field(default_factory=list, description="Ingestion anomalies or schema notes")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Upload timestamp UTC")


class DatasetSummaryResponse(BaseModel):
    """High-level summary of a registered dataset."""

    dataset_id: str
    filename: str
    total_rows: int
    is_classified: bool = False
    processed_rows: int = 0
    created_at: datetime
    status: str = "PENDING"


class PreviewRecord(BaseModel):
    """Individual transaction record preview."""

    row_id: int
    doc_no: Optional[str] = None
    invoice_date: Optional[str] = None
    seller_supplier: Optional[str] = None
    buyer_customer: Optional[str] = None
    total_amount: Optional[float] = None
    taxable_value: Optional[float] = None
    gst: Optional[float] = None
    quantity: Optional[float] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class PaginatedPreviewResponse(BaseModel):
    """Paginated preview of dataset transactions."""

    dataset_id: str
    total_rows: int
    page: int
    page_size: int
    total_pages: int
    records: List[PreviewRecord]


# -----------------------------------------------------------------------------
# Classification Schemas
# -----------------------------------------------------------------------------
class SingleClassifyRequest(BaseModel):
    """Request payload to classify a single transaction on demand."""

    row_id: Optional[int] = 1
    doc_no: Optional[str] = None
    invoice_date: Optional[str] = None
    seller_supplier: Optional[str] = None
    buyer_customer: Optional[str] = None
    total_amount: Optional[float] = None
    taxable_value: Optional[float] = None
    gst: Optional[float] = None
    quantity: Optional[float] = None
    items_description: Optional[str] = None
    custom_populated_fields: Dict[str, Any] = Field(default_factory=dict)
    use_mock: Optional[bool] = None
    mode: Optional[str] = Field(default=None, description="Inference mode: 'fast' (Local SVM), 'ai' (Gemma 4), or 'hybrid'")


class SingleClassifyResponse(BaseModel):
    """Combined inference prediction and guardrails evaluation."""

    result: GemmaClassificationResult
    evaluation: GuardrailEvaluation


class BatchClassifyRequest(BaseModel):
    """Request to initiate background batch classification on an uploaded dataset."""

    dataset_id: str
    use_mock: Optional[bool] = None
    batch_size: Optional[int] = 50
    mode: Optional[str] = Field(default=None, description="Inference mode: 'fast' (Local SVM), 'ai' (Gemma 4), or 'hybrid'")


class BatchClassifyJobResponse(BaseModel):
    """Job status container for background batch classification."""

    job_id: str
    dataset_id: str
    status: str = Field(..., description="'QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED'")
    total_rows: int
    processed_rows: int = 0
    progress_percent: float = 0.0
    mode: Optional[str] = "fast"
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


# -----------------------------------------------------------------------------
# Prediction & Review Schemas
# -----------------------------------------------------------------------------
class PredictionRecordResponse(BaseModel):
    """Detailed audit record for a single classified row."""

    row_id: int
    doc_no: Optional[str] = None
    invoice_date: Optional[str] = None
    seller_supplier: Optional[str] = None
    buyer_customer: Optional[str] = None
    total_amount: Optional[float] = None
    predicted_category: str
    confidence: float
    confidence_tier: ConfidenceTier
    triage_decision: TriageDecision
    reasoning: str
    detected_signals: List[str]
    contradictions: List[Dict[str, Any]]
    alternative_category: Optional[str] = None
    alternative_confidence: Optional[float] = None
    is_overridden: bool = False
    overridden_category: Optional[str] = None
    override_reason: Optional[str] = None
    reviewer_id: Optional[str] = None
    override_timestamp: Optional[datetime] = None
    custom_fields: Dict[str, Any] = Field(default_factory=dict)


class PaginatedPredictionsResponse(BaseModel):
    """Paginated collection of classification predictions with triage metadata."""

    dataset_id: str
    total_records: int
    filtered_records: int
    page: int
    page_size: int
    total_pages: int
    predictions: List[PredictionRecordResponse]


class HumanOverrideRequest(BaseModel):
    """Payload to record an authoritative human reviewer adjustment."""

    overridden_category: str = Field(..., description="Corrected category from 27 authoritative labels")
    override_reason: str = Field(..., description="Auditor explanation for overriding model prediction")
    reviewer_id: Optional[str] = Field(default="auditor-1", description="Identifier of the human reviewer")


class HumanOverrideResponse(BaseModel):
    """Confirmation of human reviewer override."""

    row_id: int
    status: str = "OVERRIDDEN"
    previous_category: str
    new_category: str
    override_reason: str
    reviewer_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# -----------------------------------------------------------------------------
# Analytics Schemas
# -----------------------------------------------------------------------------
class AnalyticsResponse(BaseModel):
    """Aggregate metrics and distribution analytics for an evaluated dataset."""

    dataset_id: str
    total_transactions: int
    processed_transactions: int = 0
    auto_verified_count: int = 0
    flagged_for_review_count: int = 0
    critical_rejection_count: int = 0
    overridden_count: int = 0
    human_override_count: int = 0
    average_confidence: float = 0.0
    average_latency_ms: float = 0.0
    auto_verified_percentage: Optional[float] = None
    flagged_percentage: Optional[float] = None
    critical_rejection_percentage: Optional[float] = None
    review_queue_percentage: Optional[float] = None
    category_distribution: Dict[str, int] = Field(default_factory=dict)
    confidence_tier_distribution: Dict[str, int] = Field(default_factory=dict)
    triage_distribution: Dict[str, int] = Field(default_factory=dict)
    triage_decision_distribution: Dict[str, int] = Field(default_factory=dict)
    contradiction_counts: Dict[str, int] = Field(default_factory=dict)
    contradiction_breakdown: Dict[str, int] = Field(default_factory=dict)


# -----------------------------------------------------------------------------
# Taxonomy & Knowledge Card Schemas
# -----------------------------------------------------------------------------
class TaxonomyCardResponse(BaseModel):
    """Structured voucher knowledge card detailing accounting rules."""

    category: str
    description: str
    expected_flow: str
    primary_identifiers: List[str]
    typical_ledgers: List[str]
    key_signals: List[str]
    negative_signals: List[str]
    common_confusion_pairs: List[str]
    disambiguation_rule: str


# -----------------------------------------------------------------------------
# Evaluation & Benchmark Schemas
# -----------------------------------------------------------------------------
class EvaluationMetricsResponse(BaseModel):
    """Multi-class model evaluation, accuracy, F1, and confusion metrics."""

    dataset_id: str
    total_samples: int
    accuracy: float
    macro_f1: float
    weighted_f1: float
    per_class_metrics: Dict[str, Dict[str, Any]]
    top_confused_pairs: List[Dict[str, Any]]
    triage_analytics: Dict[str, Any]

