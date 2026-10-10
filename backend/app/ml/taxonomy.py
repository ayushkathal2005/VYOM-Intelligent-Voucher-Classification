"""Authoritative definition of the 27 accounting voucher categories."""

from typing import Dict, List, Optional, Tuple

AUTHORITATIVE_VOUCHER_LABELS: Tuple[str, ...] = (
    "Purchase",
    "Sales",
    "Purchase Return / Debit Note",
    "Sales Return / Credit Note",
    "Payment",
    "Receipt",
    "Contra",
    "Journal",
    "Salary / Payroll",
    "Attendance",
    "Purchase Order",
    "Sales Order",
    "Receipt Note",
    "Delivery Note",
    "Rejection In",
    "Rejection Out",
    "Stock Journal",
    "Physical Stock",
    "Material In",
    "Material Out",
    "Job Work In Order",
    "Job Work Out Order",
    "Import",
    "Export",
    "Expense",
    "Advance / Prepayment",
    "Other / Miscellaneous",
)

LABEL_TO_ID: Dict[str, int] = {label: i for i, label in enumerate(AUTHORITATIVE_VOUCHER_LABELS)}
ID_TO_LABEL: Dict[int, str] = {i: label for i, label in enumerate(AUTHORITATIVE_VOUCHER_LABELS)}

# Normalization mapping for case/spacing variations
_NORMALIZED_LOOKUP: Dict[str, str] = {
    label.lower().replace(" ", "").replace("/", "").replace("-", ""): label
    for label in AUTHORITATIVE_VOUCHER_LABELS
}


def normalize_voucher_label(label: str) -> Optional[str]:
    """Validate and normalize a voucher category string against the 27 authoritative labels."""
    if not label:
        return None
    cleaned = str(label).strip()
    if cleaned in LABEL_TO_ID:
        return cleaned

    key = cleaned.lower().replace(" ", "").replace("/", "").replace("-", "")
    return _NORMALIZED_LOOKUP.get(key)


def is_valid_voucher_label(label: str) -> bool:
    """Return True if the label matches one of the 27 authoritative categories."""
    return normalize_voucher_label(label) is not None
