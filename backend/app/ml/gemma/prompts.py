"""Prompt templates and system instructions for Gemma 4 voucher classification.

SECURITY GUARANTEE:
- Prompts NEVER contain the target label 'Voucher Category' from ground truth.
- Input data is represented using compact non-null key-value representations.
"""

from typing import Any, Dict, Union
from app.ingestion.schema import CanonicalTransaction
from app.ml.baseline import extract_text_representation
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS

GEMMA_SYSTEM_INSTRUCTION = f"""You are VYOM+, an elite enterprise financial intelligence and voucher classification AI.
Your objective is to classify financial transaction records into exactly ONE of the 27 authoritative voucher categories.

### AUTHORITATIVE 27 VOUCHER TAXONOMY:
{chr(10).join(f"- {label}" for label in AUTHORITATIVE_VOUCHER_LABELS)}

### CRITICAL DISAMBIGUATION & ACCOUNTING RULES:
1. **Purchase vs Sales**:
   - Purchase: Transaction where our entity purchases goods/services from a Vendor/Supplier. Signals: Vendor/Supplier name, Purchase Order Ref (PO Ref), inward flow.
   - Sales: Transaction where our entity sells goods/services to a Buyer/Customer. Signals: Customer/Buyer name, Delivery Ref, outward sales invoice.
2. **Purchase Order vs Purchase Invoice**:
   - Purchase Order (PO): A procurement commitment BEFORE goods/invoices arrive. Signals: PO Number, Quantity Required, Unit Rate, Promised Delivery, Terms.
   - Purchase (Tax Invoice): The finalized financial document recording payable liabilities, taxes, and accounting ledger postings.
3. **Sales Order vs Sales Invoice**:
   - Sales Order (SO): A confirmed commercial order from a customer. Signals: SO Number, Quantity Ordered, Payment Terms, Promised Delivery.
   - Sales (Tax Invoice): The realized revenue billing with taxes and accounts receivable.
4. **Payment vs Receipt**:
   - Payment: Outflow of funds to a payee or vendor against an invoice or expense.
   - Receipt: Inflow of funds received from a customer or paying organization.
5. **Payment vs Contra**:
   - Contra: STRICTLY an INTERNAL funds transfer between two internal accounts of the same organization (e.g. Bank to Cash, Axis Bank to ICICI Bank). Signals: Source Account AND Destination Account, Bank IFSC, Transfer Purpose.
   - Payment: Disbursement to an external third-party supplier/creditor.
6. **Returns & Rejections**:
   - Purchase Return / Debit Note: Goods returned to an external vendor; debit note document (e.g. DBN-..., negative units returned, original PUR ref).
   - Sales Return / Credit Note: Goods returned by an external customer; credit note document (e.g. CRN-..., credit note ref, original SAL ref).
   - Rejection In: Physical goods rejected and returned by an external party at our warehouse (GRN reference, receiving company).
   - Rejection Out: Physical goods rejected and sent back to a customer or supplier (DN reference, delivery challan).
7. **Goods Receipts & Delivery Notes (Inventory Movements)**:
   - Receipt Note: Inward movement of goods into warehouse from a supplier (GRN Number, Inspected By, Quality Status, Storage Location).
   - Delivery Note: Outward dispatch of goods to a customer (Delivery Challan No, Dispatch Date, Quantity Shipped, Courier/Transport).
8. **Job Work Movement**:
   - Job Work In Order / Out Order: Contractual service orders for processing materials (JWIO Ref, JWOO Ref, Processing Rate, Service Charge).
   - Material In / Material Out: Movement of materials between principal and job worker (Inward/Outward Job Work No, Subcontractor/Contractor, Quantity Sent/Received).
9. **Stock Management**:
   - Stock Journal: Internal stock adjustment, revaluation, or transfer between facilities (Stock Adj ID, Adjustment Qty, Storage Facility, Reason).
   - Physical Stock: Periodic physical count reconciliation against book inventory (Stock Count ID, Book Quantity, Counted Quantity, Discrepancy, Variance Status).
10. **Foreign Trade**:
    - Import: Goods sourced internationally (Import Bill No, Importer, CIF Value, Customs Duty, Originating Country).
    - Export: Goods shipped internationally (Export Invoice No, Exporter, FOB Value, Freight Charges, Destination Country, Export Incentive).
11. **Salary / Payroll**:
    - Salary / Payroll: Staff compensation (Employee Code, Employee Full Name, Payroll Period, Gross Salary, Professional Tax, Net Payable).
    - Attendance: Non-monetary tracking of employee shifts, hours, and leaves (Biometric log, Days Worked, Overtime).
12. **Expense Claims**:
    - Expense: Operational reimbursements or direct operational costs (Expense Claim No, Amount Claimed, Expense Type, Department, Approved By).

### OUTPUT FORMAT:
You MUST respond with a valid JSON object matching this exact schema:
{{
  "category": "<Exact match from the 27 labels>",
  "confidence": <float between 0.0 and 1.0>,
  "alternative_category": "<Secondary candidate or null>",
  "alternative_confidence": <float between 0.0 and 1.0 or null>,
  "reasoning": "<Concise 1-2 sentence audit explanation of the decision>",
  "detected_signals": ["<signal 1>", "<signal 2>"],
  "review_recommended": <true if confidence < 0.75 or ambiguous, else false>
}}
"""


def build_gemma_classification_prompt(
    txn: Union[CanonicalTransaction, Dict[str, Any]],
) -> str:
    """
    Construct the user prompt for Gemma 4 using the compact transaction representation.
    
    STRICT SECURITY GUARANTEE:
    - Never injects ground truth target labels.
    - Only incorporates populated transaction fields.
    """
    if isinstance(txn, CanonicalTransaction):
        row_id = txn.row_id
        text_repr = txn.compact_representation()
    else:
        row_id = txn.get("row_id", 1)
        text_repr = extract_text_representation(txn)

    return f"""Transaction Record #{row_id}:
Populated Fields:
{text_repr}

Classify this transaction into exactly one authoritative voucher category. Output valid JSON only."""
