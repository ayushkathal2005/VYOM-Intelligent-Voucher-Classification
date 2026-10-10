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
    raw_record: Dict[str, Any] = Field(default_factory=dict, description="Preserved original input fields and raw values")


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
    canonical_transactions: List[CanonicalTransaction] = Field(
        default_factory=list, description="Canonical transactions ready for signals and classification"
    )
