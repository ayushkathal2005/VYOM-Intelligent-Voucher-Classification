"""Data schemas for transaction ingestion and normalization."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CanonicalTransaction(BaseModel):
    """Normalized, canonical financial transaction object."""

    row_id: int = Field(..., description="Stable 1-indexed row number from source dataset")
    seller_supplier: Optional[str] = Field(default=None, description="Seller / Supplier entity name")
    buyer_customer: Optional[str] = Field(default=None, description="Buyer / Customer entity name")
    invoice_number: Optional[str] = Field(default=None, description="Invoice or document number reference")
    invoice_date: Optional[str] = Field(default=None, description="Standardized ISO date (YYYY-MM-DD) if parseable")
    item_descriptions: List[str] = Field(default_factory=list, description="Item descriptions, products, or line items")
    quantity: Optional[float] = Field(default=None, description="Quantity of goods or units")
    taxable_value: Optional[float] = Field(default=None, description="Base taxable amount")
    gst: Optional[float] = Field(default=None, description="GST / Tax amount")
    discount: Optional[float] = Field(default=0.0, description="Discount amount")
    freight: Optional[float] = Field(default=0.0, description="Freight or shipping charge")
    total_amount: Optional[float] = Field(default=None, description="Total transaction or gross amount")
    payment_information: Optional[str] = Field(default=None, description="Payment details, mode, bank account or cash")
    return_information: Optional[str] = Field(default=None, description="Return notes, debit/credit note context")
    order_reference: Optional[str] = Field(default=None, description="Order reference (PO/SO) or purchase order number")
    delivery_information: Optional[str] = Field(default=None, description="Delivery note, challan, or dispatch details")
    currency: Optional[str] = Field(default="INR", description="Transaction currency code")
    debit_credit_information: Optional[str] = Field(default=None, description="Debit/credit account or entry direction")
    payroll_information: Optional[str] = Field(default=None, description="Payroll, salary, attendance or employee metadata")
    import_export_information: Optional[str] = Field(default=None, description="Customs, shipping bill, or foreign trade details")
    narration_remarks: Optional[str] = Field(default=None, description="General narration, remarks, or notes")
    custom_populated_fields: Dict[str, Any] = Field(
        default_factory=dict,
        description="Meaningful populated non-null fields not mapped to standard canonical attributes (strictly excluding target label)",
    )
    ground_truth_label: Optional[str] = Field(
        default=None,
        description="Ground truth voucher category if present for evaluation. NEVER used in inference or compact representation.",
    )
    raw_record: Dict[str, Any] = Field(default_factory=dict, description="Preserved original input fields and raw values")

    def compact_representation(self) -> str:
        """
        Generate a compact, information-rich text representation containing ONLY populated fields.
        STRICT GUARANTEE: Never includes ground_truth_label or any target category column.
        """
        parts: List[str] = []
        if self.order_reference:
            parts.append(f"order_ref: {self.order_reference}")
        if self.invoice_number:
            parts.append(f"doc_no: {self.invoice_number}")
        if self.invoice_date:
            parts.append(f"date: {self.invoice_date}")
        if self.seller_supplier:
            parts.append(f"supplier: {self.seller_supplier}")
        if self.buyer_customer:
            parts.append(f"buyer: {self.buyer_customer}")
        if self.item_descriptions:
            parts.append(f"items: {' '.join(str(i) for i in self.item_descriptions)}")
        if self.quantity is not None:
            parts.append(f"quantity: {self.quantity}")
        if self.taxable_value is not None:
            parts.append(f"taxable_val: {self.taxable_value}")
        if self.gst is not None and self.gst > 0:
            parts.append(f"tax: {self.gst}")
        if self.total_amount is not None:
            parts.append(f"total_amount: {self.total_amount}")
        if self.currency and self.currency != "INR":
            parts.append(f"currency: {self.currency}")
        if self.payment_information:
            parts.append(f"payment: {self.payment_information}")
        if self.return_information:
            parts.append(f"return: {self.return_information}")
        if self.delivery_information:
            parts.append(f"delivery: {self.delivery_information}")
        if self.debit_credit_information:
            parts.append(f"accounts: {self.debit_credit_information}")
        if self.payroll_information:
            parts.append(f"payroll: {self.payroll_information}")
        if self.import_export_information:
            parts.append(f"trade: {self.import_export_information}")
        if self.narration_remarks:
            parts.append(f"narration: {self.narration_remarks}")

        # Add custom populated fields (safely ignoring any target labels or empty values)
        for k, v in self.custom_populated_fields.items():
            if v is None:
                continue
            k_clean = str(k).strip()
            # Double safety: ensure target label is never emitted
            if k_clean.lower() in ("voucher category", "category", "target", "label", "voucher_type"):
                continue
            v_clean = str(v).strip()
            if v_clean and v_clean.lower() not in ("nan", "null", "none", ""):
                parts.append(f"{k_clean}: {v_clean}")

        return " | ".join(parts) if parts else "unspecified transaction"


class SchemaWarning(BaseModel):
    """Warning emitted during dataset schema discovery and parsing."""

    code: str = Field(..., description="Machine-readable warning code")
    message: str = Field(..., description="Human-readable warning description")
    affected_columns: List[str] = Field(default_factory=list, description="Associated column names")
    row_count: Optional[int] = Field(default=None, description="Number of rows affected if applicable")


class IngestionResult(BaseModel):
    """Output bundle of parsed and validated dataset ingestion."""

    filename: str = Field(..., description="Source filename")
    file_type: str = Field(..., description="Detected file type: xlsx or csv")
    total_rows: int = Field(..., description="Total valid transactions parsed")
    raw_column_count: int = Field(..., description="Total columns found in the source sheet")
    detected_columns: List[str] = Field(default_factory=list, description="Raw column headers found in dataset")
    mapped_canonical_fields: Dict[str, str] = Field(
        default_factory=dict, description="Mapping of raw column -> canonical field name"
    )
    unmapped_columns: List[str] = Field(default_factory=list, description="Columns preserved but not canonically mapped")
    warnings: List[SchemaWarning] = Field(default_factory=list, description="Schema and data warnings")
    duplicate_identifiers: List[str] = Field(
        default_factory=list, description="Duplicate invoice/document numbers detected"
    )
    has_target_column: bool = Field(
        default=False, description="True if a ground truth category column was detected for evaluation"
    )
    target_column_name: Optional[str] = Field(
        default=None, description="Name of the detected target column if present"
    )
    canonical_transactions: List[CanonicalTransaction] = Field(
        default_factory=list, description="Canonical transactions ready for signals and classification"
    )

