"""Machine learning baselines, evaluation, and taxonomy package for VYOM+."""

from app.ml.taxonomy import (
    AUTHORITATIVE_VOUCHER_LABELS,
    LABEL_TO_ID,
    ID_TO_LABEL,
    normalize_voucher_label,
    is_valid_voucher_label,
)
from app.ml.baseline import (
    MajorityClassBaseline,
    TfidfBaselineClassifier,
    extract_text_representation,
)
from app.ml.evaluation import evaluate_classifier_performance
from app.ml.leakage import DataLeakageAudit
from app.ml.fixtures.synthetic_voucher_dataset import SYNTHETIC_DATASET
from app.ml.fixtures.reference_workbook_fixture import (
    load_reference_workbook,
    get_missing_categories_synthetic_fixtures,
    run_reference_cv_benchmark,
    MISSING_REFERENCE_CATEGORIES,
)

from app.ml.gemma import (
    GemmaVoucherPrediction,
    GemmaClassificationResult,
    GEMMA_SYSTEM_INSTRUCTION,
    build_gemma_classification_prompt,
    MockGemmaAdapter,
    GemmaClassifier,
    GemmaConfigurationError,
)

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

__all__ = [
    "AUTHORITATIVE_VOUCHER_LABELS",
    "LABEL_TO_ID",
    "ID_TO_LABEL",
    "normalize_voucher_label",
    "is_valid_voucher_label",
    "MajorityClassBaseline",
    "TfidfBaselineClassifier",
    "extract_text_representation",
    "evaluate_classifier_performance",
    "DataLeakageAudit",
    "SYNTHETIC_DATASET",
    "load_reference_workbook",
    "get_missing_categories_synthetic_fixtures",
    "run_reference_cv_benchmark",
    "MISSING_REFERENCE_CATEGORIES",
    "GemmaVoucherPrediction",
    "GemmaClassificationResult",
    "GEMMA_SYSTEM_INSTRUCTION",
    "build_gemma_classification_prompt",
    "MockGemmaAdapter",
    "GemmaClassifier",
    "GemmaConfigurationError",
    "MoneyFlowDirection",
    "EntityRole",
    "AccountingSignalProfile",
    "VoucherKnowledgeCard",
    "VOUCHER_CARDS",
    "AccountingSignalsEngine",
    "SemanticCandidateRetriever",
    "candidate_retriever",
]



