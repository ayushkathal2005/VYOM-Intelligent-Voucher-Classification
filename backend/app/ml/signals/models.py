"""Domain models and enumerations for accounting signals extraction."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class MoneyFlowDirection(str, Enum):
    """Directional flow of financial liquidity or inventory value."""

    INFLOW = "INFLOW"  # Inward funds: Receipts, customer collections, sales revenue
    OUTFLOW = "OUTFLOW"  # Outward funds: Vendor disbursements, payments, expenses, payroll
    INTERNAL = "INTERNAL"  # Zero net change: Bank-to-bank transfers, cash repositioning (Contra)
    NON_FINANCIAL_MOVEMENT = "NON_FINANCIAL_MOVEMENT"  # Physical inventory movement without direct ledger cash settlement
    ORDER_COMMITMENT = "ORDER_COMMITMENT"  # Commercial agreement prior to fulfillment or invoicing (PO, SO, JW orders)
    ADJUSTMENT = "ADJUSTMENT"  # Dual-sided non-cash ledger adjustment (Journal)
    ATTENDANCE_LOG = "ATTENDANCE_LOG"  # Non-monetary workforce shift/hours tracking
    UNKNOWN = "UNKNOWN"


class EntityRole(str, Enum):
    """Identified legal or accounting counterparty role in the transaction."""

    VENDOR_SUPPLIER = "VENDOR_SUPPLIER"
    CUSTOMER_BUYER = "CUSTOMER_BUYER"
    EMPLOYEE = "EMPLOYEE"
    INTERNAL_ACCOUNT = "INTERNAL_ACCOUNT"
    CONTRACTOR_JOBWORKER = "CONTRACTOR_JOBWORKER"
    OVERSEAS_COUNTERPARTY = "OVERSEAS_COUNTERPARTY"
    TAX_AUTHORITY = "TAX_AUTHORITY"
    UNKNOWN = "UNKNOWN"


class AccountingSignalProfile(BaseModel):
    """Comprehensive accounting and structural signal profile derived from a transaction."""

    row_id: int = Field(..., description="Stable 1-indexed row number from dataset")
    money_flow: MoneyFlowDirection = Field(..., description="Inferred directional flow of funds/value")
    detected_entity_roles: List[EntityRole] = Field(
        default_factory=list, description="Roles identified for the transacting parties"
    )
    is_tax_applicable: bool = Field(default=False, description="True if statutory taxes (GST, VAT, Customs) are present")
    has_negative_quantity: bool = Field(default=False, description="True if quantity is negative (indicating returns)")
    has_order_reference: bool = Field(default=False, description="True if transaction references a PO or SO")
    has_dispatch_reference: bool = Field(default=False, description="True if transaction references a Delivery Challan or GRN")
    has_internal_account_pair: bool = Field(default=False, description="True if dual internal bank/cash accounts are present")
    has_customs_or_crossborder: bool = Field(default=False, description="True if foreign trade indicators are present")
    has_employee_metadata: bool = Field(default=False, description="True if payroll/employee indicators are present")
    primary_signals: List[str] = Field(default_factory=list, description="Top identified accounting signals")
    risk_flags: List[str] = Field(default_factory=list, description="Ambiguity or inconsistency risk flags")
