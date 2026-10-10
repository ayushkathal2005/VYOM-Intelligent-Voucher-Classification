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
    """
    Combine textual and semantic transaction fields into a compact, leak-free text representation.
    STRICT LEAKAGE GUARANTEE: Never includes target category columns or ground-truth labels.
    """
    if isinstance(txn, CanonicalTransaction):
        return txn.compact_representation()

    # Dictionary representation with target column isolation
    EXCLUDED_TARGET_KEYS = {
        "voucher_category",
        "voucher_type",
        "category",
        "target",
        "label",
        "voucher_cat",
        "vch_type",
        "vch_category",
        "target_label",
    }

    parts = []
    # 1. Standard canonical keys if present
    if txn.get("order_reference"):
        parts.append(f"order_ref: {txn['order_reference']}")
    if txn.get("invoice_number"):
        parts.append(f"doc_no: {txn['invoice_number']}")
    if txn.get("invoice_date"):
        parts.append(f"date: {txn['invoice_date']}")
    if txn.get("seller_supplier"):
        parts.append(f"supplier: {txn['seller_supplier']}")
    if txn.get("buyer_customer"):
        parts.append(f"buyer: {txn['buyer_customer']}")

    items = txn.get("item_descriptions")
    if items:
        if isinstance(items, list):
            parts.append(f"items: {' '.join(str(i) for i in items)}")
        else:
            parts.append(f"items: {items}")

    if txn.get("quantity") is not None:
        parts.append(f"quantity: {txn['quantity']}")
    if txn.get("taxable_value") is not None:
        parts.append(f"taxable_val: {txn['taxable_value']}")
    if txn.get("gst") is not None and txn.get("gst") > 0:
        parts.append(f"tax: {txn['gst']}")
    if txn.get("total_amount") is not None:
        parts.append(f"total_amount: {txn['total_amount']}")
    if txn.get("currency") and txn.get("currency") != "INR":
        parts.append(f"currency: {txn['currency']}")
    if txn.get("payment_information"):
        parts.append(f"payment: {txn['payment_information']}")
    if txn.get("return_information"):
        parts.append(f"return: {txn['return_information']}")
    if txn.get("delivery_information"):
        parts.append(f"delivery: {txn['delivery_information']}")
    if txn.get("debit_credit_information"):
        parts.append(f"accounts: {txn['debit_credit_information']}")
    if txn.get("payroll_information"):
        parts.append(f"payroll: {txn['payroll_information']}")
    if txn.get("import_export_information"):
        parts.append(f"trade: {txn['import_export_information']}")
    if txn.get("narration_remarks"):
        parts.append(f"narration: {txn['narration_remarks']}")

    # 2. Any additional custom populated fields
    standard_keys = {
        "order_reference", "invoice_number", "invoice_date", "seller_supplier",
        "buyer_customer", "item_descriptions", "quantity", "taxable_value",
        "gst", "total_amount", "currency", "payment_information", "return_information",
        "delivery_information", "debit_credit_information", "payroll_information",
        "import_export_information", "narration_remarks", "raw_record", "row_id",
        "ground_truth_label", "custom_populated_fields",
    }

    for k, v in txn.items():
        if k in standard_keys or k.lower() in EXCLUDED_TARGET_KEYS:
            continue
        # Double check for category/type/target in key
        if "voucher" in k.lower() or "target" in k.lower():
            continue
        if v is not None and str(v).strip() and str(v).strip().lower() not in ("nan", "null", "none"):
            parts.append(f"{k}: {str(v).strip()}")

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
