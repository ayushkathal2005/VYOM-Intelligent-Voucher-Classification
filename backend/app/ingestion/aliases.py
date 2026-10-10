"""Header alias normalization and canonical field resolution."""

import re
from typing import Dict, List, Optional

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
        "invoice",
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
    ],
    "discount": [
        "discount",
        "disc",
        "discount_amount",
        "rebate",
        "trade_discount",
    ],
    "freight": [
        "freight",
        "shipping",
        "shipping_charges",
        "freight_charges",
        "transport",
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
    ],
    "return_information": [
        "return_information",
        "return_details",
        "return_note",
        "debit_note_ref",
        "credit_note_ref",
        "rejection_note",
        "return_reason",
        "sales_return",
        "purchase_return",
    ],
    "order_reference": [
        "order_reference",
        "po_number",
        "order_no",
        "order_id",
        "po_no",
        "so_no",
        "purchase_order_ref",
        "sales_order_ref",
        "po_date",
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
    ],
    "currency": [
        "currency",
        "curr",
        "curr_code",
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
    ],
    "narration_remarks": [
        "narration",
        "remarks",
        "notes",
        "memo",
        "description_narration",
        "comments",
        "transaction_narration",
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


def resolve_canonical_field(raw_header: str) -> Optional[str]:
    """Resolve a raw header to a canonical field name, or None if unrecognized."""
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
        "to", "from", "date", "type", "no", "val", "disc", "curr", "party", "amount"
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
