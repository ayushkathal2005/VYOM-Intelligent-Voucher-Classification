"""Data leakage audits and train/test separation checks."""

from typing import Any, Dict, List, Set, Tuple
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS


class DataLeakageAudit:
    """Audit suite to detect target label leakage, duplicate identifiers, and sample contamination."""

    @staticmethod
    def audit_splits(
        train_records: List[Dict[str, Any]],
        test_records: List[Dict[str, Any]],
        identifier_field: str = "invoice_number",
        feature_text_field: str = "text_repr",
    ) -> Dict[str, Any]:
        """
        Audit train and test splits for data leakage.

        Checks:
        1. Overlapping document identifiers (e.g. invoice numbers in both train and test)
        2. Exact duplicate feature text representations between train and test
        3. Label leakage: target voucher category names appearing in input features
        """
        train_ids: Set[str] = {
            str(r.get(identifier_field)).strip()
            for r in train_records
            if r.get(identifier_field)
        }
        test_ids: Set[str] = {
            str(r.get(identifier_field)).strip()
            for r in test_records
            if r.get(identifier_field)
        }

        overlapping_ids = list(train_ids.intersection(test_ids))

        train_texts: Set[str] = {
            str(r.get(feature_text_field, "")).strip().lower()
            for r in train_records
            if r.get(feature_text_field)
        }
        test_texts: Set[str] = {
            str(r.get(feature_text_field, "")).strip().lower()
            for r in test_records
            if r.get(feature_text_field)
        }

        overlapping_texts = list(train_texts.intersection(test_texts))

        # Check for direct label leakage inside text representations
        label_leakage_violations: List[Dict[str, str]] = []
        for r in train_records + test_records:
            text = str(r.get(feature_text_field, "")).lower()
            ground_truth = str(r.get("voucher_type", "")).lower()
            # If the feature text directly includes the exact target label, record as warning
            if ground_truth and len(ground_truth) > 3 and ground_truth in text:
                label_leakage_violations.append({
                    "id": str(r.get(identifier_field, "unknown")),
                    "label": ground_truth,
                })

        has_leakage = bool(overlapping_ids or (len(overlapping_texts) > len(test_records) * 0.1))

        return {
            "is_clean": not has_leakage,
            "train_count": len(train_records),
            "test_count": len(test_records),
            "overlapping_identifier_count": len(overlapping_ids),
            "overlapping_identifiers": overlapping_ids[:10],
            "overlapping_text_representation_count": len(overlapping_texts),
            "label_leakage_warning_count": len(label_leakage_violations),
            "verdict": "PASS" if not has_leakage else "FAIL - LEAKAGE DETECTED",
        }
