"""Baseline voucher classifiers: Majority Class and TF-IDF Linear Model."""

import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

from app.ingestion.schema import CanonicalTransaction
from app.ml.taxonomy import (
    AUTHORITATIVE_VOUCHER_LABELS,
    normalize_voucher_label,
)


def extract_text_representation(txn: Union[CanonicalTransaction, Dict[str, Any]]) -> str:
    """Combine textual and semantic transaction fields into a normalized text representation."""
    if isinstance(txn, CanonicalTransaction):
        parts = [
            f"supplier: {txn.seller_supplier or ''}",
            f"buyer: {txn.buyer_customer or ''}",
            f"items: {' '.join(txn.item_descriptions) if txn.item_descriptions else ''}",
            f"narration: {txn.narration_remarks or ''}",
            f"payment: {txn.payment_information or ''}",
            f"return: {txn.return_information or ''}",
            f"order: {txn.order_reference or ''}",
            f"delivery: {txn.delivery_information or ''}",
            f"debit_credit: {txn.debit_credit_information or ''}",
            f"payroll: {txn.payroll_information or ''}",
            f"trade: {txn.import_export_information or ''}",
        ]
    else:
        # Dictionary representation
        items = txn.get("item_descriptions") or []
        if isinstance(items, list):
            items_str = " ".join(str(i) for i in items)
        else:
            items_str = str(items)

        parts = [
            f"supplier: {txn.get('seller_supplier') or ''}",
            f"buyer: {txn.get('buyer_customer') or ''}",
            f"items: {items_str}",
            f"narration: {txn.get('narration_remarks') or ''}",
            f"payment: {txn.get('payment_information') or ''}",
            f"return: {txn.get('return_information') or ''}",
            f"order: {txn.get('order_reference') or ''}",
            f"delivery: {txn.get('delivery_information') or ''}",
            f"debit_credit: {txn.get('debit_credit_information') or ''}",
            f"payroll: {txn.get('payroll_information') or ''}",
            f"trade: {txn.get('import_export_information') or ''}",
        ]

    # Filter out empty label prefixes and clean up spacing
    clean_parts = [p for p in parts if len(p.split(":", 1)[1].strip()) > 0]
    return " | ".join(clean_parts) if clean_parts else "unspecified transaction"


class MajorityClassBaseline:
    """Predicts the most frequent voucher category observed in the training data."""

    def __init__(self):
        self.majority_class: str = "Purchase"
        self.class_priors: Dict[str, float] = {}

    def fit(self, X: List[Any], y: List[str]) -> "MajorityClassBaseline":
        normalized_y = [normalize_voucher_label(label) or "Other / Miscellaneous" for label in y]
        counts = Counter(normalized_y)
        total = len(normalized_y)
        self.majority_class = counts.most_common(1)[0][0]
        self.class_priors = {cls: count / total for cls, count in counts.items()}
        return self

    def predict(self, X: List[Any]) -> List[str]:
        return [self.majority_class for _ in X]

    def predict_proba(self, X: List[Any]) -> np.ndarray:
        prob = self.class_priors.get(self.majority_class, 1.0)
        # Returns uniform majority confidence
        return np.full((len(X), len(AUTHORITATIVE_VOUCHER_LABELS)), 1.0 / len(AUTHORITATIVE_VOUCHER_LABELS))


class TfidfBaselineClassifier:
    """
    TF-IDF Vectorizer with balanced Logistic Regression.
    Serves as the classical machine-learning baseline.
    """

    def __init__(self, random_state: int = 42):
        self.random_state = random_state
        self.pipeline: Optional[Pipeline] = None
        self.classes_: np.ndarray = np.array([])
        self.training_time_seconds: float = 0.0

    def fit(
        self,
        X: List[Union[CanonicalTransaction, Dict[str, Any]]],
        y: List[str],
    ) -> "TfidfBaselineClassifier":
        start_time = time.perf_counter()
        texts = [extract_text_representation(x) for x in X]
        normalized_y = [normalize_voucher_label(label) or "Other / Miscellaneous" for label in y]

        vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=5000,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=1000,
            random_state=self.random_state,
            C=1.0,
        )

        self.pipeline = Pipeline([
            ("tfidf", vectorizer),
            ("clf", classifier),
        ])

        self.pipeline.fit(texts, normalized_y)
        self.classes_ = self.pipeline.classes_
        self.training_time_seconds = time.perf_counter() - start_time
        return self

    def predict_single(
        self,
        x: Union[CanonicalTransaction, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Predict voucher category for a single transaction with confidence and alternative candidate."""
        if self.pipeline is None:
            raise RuntimeError("Classifier must be fitted before calling predict.")

        text = extract_text_representation(x)
        start_time = time.perf_counter()
        probas = self.pipeline.predict_proba([text])[0]
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        top_indices = np.argsort(probas)[::-1]
        top_idx = top_indices[0]
        second_idx = top_indices[1] if len(top_indices) > 1 else top_idx

        primary_class = self.classes_[top_idx]
        confidence = float(probas[top_idx])
        alternative_class = self.classes_[second_idx]
        alt_confidence = float(probas[second_idx])

        return {
            "voucher_type": primary_class,
            "confidence": round(confidence, 4),
            "alternative": alternative_class,
            "alternative_confidence": round(alt_confidence, 4),
            "latency_ms": round(latency_ms, 2),
            "evidence": f"TF-IDF features: {text[:80]}...",
        }

    def predict(
        self,
        X: List[Union[CanonicalTransaction, Dict[str, Any]]],
    ) -> List[str]:
        """Batch predict voucher categories."""
        if self.pipeline is None:
            raise RuntimeError("Classifier must be fitted before calling predict.")
        texts = [extract_text_representation(x) for x in X]
        return list(self.pipeline.predict(texts))

    def predict_proba(
        self,
        X: List[Union[CanonicalTransaction, Dict[str, Any]]],
    ) -> np.ndarray:
        """Batch predict probabilities."""
        if self.pipeline is None:
            raise RuntimeError("Classifier must be fitted before calling predict.")
        texts = [extract_text_representation(x) for x in X]
        return self.pipeline.predict_proba(texts)
