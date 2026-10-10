"""Header alias normalization and canonical field resolution."""

import re
from typing import Dict, List, Optional

# Target category columns that must NEVER be resolved to input features or canonical fields
TARGET_LABEL_COLUMNS = {
    "voucher_category",
    "voucher_type",
    "category",
    "target",
    "target_label",
    "label",
    "voucher_cat",
    "vch_type",
    "vch_category",
}

# Mapping canonical field -> list of recognized aliases
CANONICAL_ALIASES: Dict[str, List[str]] = {
    "seller_supplier": [
        "seller",
        "supplier",
        "vendor",
        "party_name",
        "from",
        "party",
        "seller_supplier",
        "supplier_name",
        "vendor_name",
        "creditor",
        "supplier_ledger",
        "exporter",
        "subcontractor",
    ],
    "buyer_customer": [
        "buyer",
        "customer",
        "client",
        "to",
        "consignee",
        "buyer_customer",
        "customer_name",
        "party_account",
        "debtor",
        "customer_ledger",
        "importer",
        "contractor",
        "principal",
        "ordering_company",
        "receiving_company",
        "selling_company",
    ],
    "invoice_number": [
        "invoice_no",
        "invoice_number",
        "bill_no",
        "inv_no",
        "doc_no",
        "voucher_no",
        "vch_no",
        "reference_no",
        "ref_no",
        "inv_num",
        "bill_num",
        "document_no",
        "document_number",
        "invoice",
        "grn_number",
        "delivery_challan_no",
        "import_bill_no",
        "export_invoice_no",
        "expense_claim_no",
        "payment_id",
        "receipt_id",
        "contra_id",
        "journal_id",
        "stock_adj_id",
        "stock_count_id",
    ],
    "invoice_date": [
        "invoice_date",
        "date",
        "bill_date",
        "vch_date",
        "doc_date",
        "txn_date",
        "transaction_date",
        "document_date",
        "po_date",
        "so_date",
        "receipt_date",
        "dispatch_date",
        "rejection_date",
        "payment_date",
        "entry_date",
        "claim_date",
        "adjustment_date",
        "count_date",
        "order_date",
        "date_of_dispatch",
        "date_of_receipt",
    ],
    "item_descriptions": [
        "item",
        "items",
        "item_description",
        "item_descriptions",
        "description",
        "particulars",
        "product",
        "goods",
        "services",
        "line_item",
        "product_name",
        "stock_item",
        "item_received",
        "item_dispatched",
        "item_rejected",
        "material_description",
        "export_item",
        "import_item",
        "item_name",
        "material",
    ],
    "quantity": [
        "qty",
        "quantity",
        "quantities",
        "units",
        "pcs",
        "pieces",
        "count",
        "item_quantity",
        "quantity_required",
        "quantity_ordered",
        "quantity_received",
        "quantity_shipped",
        "quantity_rejected",
        "units_returned",
        "units_exported",
        "units_imported",
        "adjustment_qty",
        "quantity_sent",
    ],
    "taxable_value": [
        "taxable_value",
        "taxable_amount",
        "taxable_val",
        "assessable_value",
        "base_amount",
        "amount",
        "net_amount",
        "subtotal",
        "taxable",
        "basic_amount",
        "cost_insurance_freight",
        "free_on_board_value",
    ],
    "gst": [
        "gst",
        "tax",
        "gst_amount",
        "total_tax",
        "cgst_sgst_igst",
        "igst",
        "cgst",
        "sgst",
        "tax_amount",
        "vat",
        "vat_amount",
        "customs_duty",
        "import_gst",
    ],
    "discount": [
        "discount",
        "disc",
        "discount_amount",
        "rebate",
        "trade_discount",
        "export_incentive",
    ],
    "freight": [
        "freight",
        "shipping",
        "shipping_charges",
        "freight_charges",
        "transport",
        "transport_cost",
        "delivery_charges",
        "cartage",
    ],
    "total_amount": [
        "total",
        "total_amount",
        "invoice_total",
        "grand_total",
        "gross_amount",
        "bill_total",
        "final_amount",
        "invoice_value",
        "total_value",
        "transfer_amount",
        "amount_claimed",
        "received_amount",
        "payment_amount",
    ],
    "payment_information": [
        "payment_information",
        "payment_mode",
        "payment_details",
        "mode_of_payment",
        "bank_cash",
        "payment_type",
        "payment_info",
        "bank_name",
        "payment_status",
        "cheque_no",
        "utr",
        "payment_method",
        "bank_details",
        "payment_terms",
    ],
    "return_information": [
        "return_information",
        "return_details",
        "return_note",
        "debit_note_ref",
        "credit_note_ref",
        "rejection_note",
        "rejection_note_no",
        "return_reason",
        "reason_for_return",
        "rejection_reason",
        "sales_return",
        "purchase_return",
        "original_doc_ref",
        "original_invoice_ref",
    ],
    "order_reference": [
        "order_reference",
        "po_number",
        "order_no",
        "order_id",
        "po_no",
        "so_no",
        "so_number",
        "purchase_order_ref",
        "sales_order_ref",
        "reference_po",
        "po_ref",
        "jwio_ref",
        "jwoo_ref",
        "order_details",
    ],
    "delivery_information": [
        "delivery_information",
        "delivery_note",
        "challan_no",
        "dispatch_details",
        "lr_no",
        "shipping_bill",
        "dispatch_note",
        "receipt_note_no",
        "delivery_status",
        "delivery_ref",
        "so_reference",
        "dn_reference",
        "grn_reference",
    ],
    "currency": [
        "currency",
        "curr",
        "curr_code",
        "currency_code",
        "payment_currency",
        "original_currency",
    ],
    "debit_credit_information": [
        "debit_credit",
        "dr_cr",
        "type",
        "entry_type",
        "transaction_type",
        "debit_credit_information",
        "ledger_type",
        "account_type",
        "debit_side",
        "credit_side",
        "source_account",
        "destination_account",
        "bank_ifsc_code",
    ],
    "payroll_information": [
        "payroll",
        "salary",
        "payroll_information",
        "employee_id",
        "emp_name",
        "attendance",
        "wages",
        "staff_name",
        "employee_code",
        "employee_full_name",
        "payroll_period",
        "gross_salary",
        "net_payable",
    ],
    "import_export_information": [
        "import_export",
        "trade_type",
        "country",
        "port_code",
        "bill_of_entry",
        "shipping_bill_no",
        "customs",
        "port_of_loading",
        "port_of_discharge",
        "destination_country",
        "originating_country",
    ],
    "narration_remarks": [
        "narration",
        "remarks",
        "notes",
        "memo",
        "description_narration",
        "comments",
        "transaction_narration",
        "transfer_purpose",
        "agreement_terms",
    ],
}


def clean_header_string(header: str) -> str:
    """Normalize a raw header string by stripping, lowercasing, and removing punctuation."""
    if not header:
        return ""
    text = str(header).strip().lower()
    # Replace non-alphanumeric with underscores
    text = re.sub(r"[^a-z0-9]+", "_", text)
    # Remove leading/trailing underscores
    text = text.strip("_")
    return text


def is_target_column(header: str) -> bool:
    """Return True if header indicates a target voucher classification label."""
    if not header:
        return False
    cleaned = clean_header_string(header)
    if not cleaned:
        return False
    if cleaned in TARGET_LABEL_COLUMNS:
        return True
    if "voucher" in cleaned and any(k in cleaned for k in ("category", "type", "label", "cat")):
        return True
    return False


def resolve_canonical_field(raw_header: str) -> Optional[str]:
    """Resolve a raw header to a canonical field name, or None if unrecognized.
    
    CRITICAL: Target category columns ALWAYS return None to prevent leakage into features.
    """
    if is_target_column(raw_header):
        return None

    cleaned = clean_header_string(raw_header)
    if not cleaned:
        return None

    # 1. Exact canonical name or alias match
    for canonical, aliases in CANONICAL_ALIASES.items():
        if cleaned == canonical or cleaned in aliases:
            return canonical

    # 2. Token-level matching (split on underscores)
    tokens = [t for t in cleaned.split("_") if t]
    token_set = set(tokens)

    # Generic short words that must be exact matches only to avoid false positives
    RESTRICTED_SHORT_WORDS = {
        "to", "from", "date", "type", "no", "val", "disc", "curr", "party", "amount",
        "count", "id", "ref", "code", "side", "rate", "due", "status", "company",
    }

    # 3. Check multi-token and distinct single-token aliases
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            alias_tokens = [a for a in alias.split("_") if a]
            if not alias_tokens:
                continue

            if len(alias_tokens) == 1:
                single_token = alias_tokens[0]
                if single_token in RESTRICTED_SHORT_WORDS:
                    if cleaned == single_token:
                        return canonical
                elif single_token in token_set:
                    return canonical
            else:
                # Multi-word alias: require all alias tokens present in header tokens
                if all(t in token_set for t in alias_tokens):
                    return canonical

    return None

