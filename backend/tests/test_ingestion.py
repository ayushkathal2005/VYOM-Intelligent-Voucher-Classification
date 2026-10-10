"""Comprehensive unit tests for the VYOM+ Data Ingestion pipeline."""

import io
import pytest
import openpyxl
from app.ingestion import (
    parse_transaction_file,
    IngestionError,
    resolve_canonical_field,
    clean_header_string,
    CANONICAL_ALIASES,
)


def create_sample_xlsx_bytes(headers, rows) -> bytes:
    """Helper to generate an in-memory openpyxl workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for r in rows:
        ws.append(r)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def create_sample_csv_bytes(content: str, encoding: str = "utf-8") -> bytes:
    """Helper to generate in-memory CSV bytes."""
    return content.encode(encoding)


# -----------------------------------------------------------------------------
# 1. Header Alias Normalization Tests
# -----------------------------------------------------------------------------
def test_clean_header_string():
    """Verify raw header normalization."""
    assert clean_header_string(" Invoice Number ") == "invoice_number"
    assert clean_header_string("Vendor / Supplier Name") == "vendor_supplier_name"
    assert clean_header_string("Taxable (INR)") == "taxable_inr"
    assert clean_header_string("") == ""


def test_resolve_canonical_field():
    """Verify alias mapping against standard business terminology."""
    assert resolve_canonical_field("Vendor") == "seller_supplier"
    assert resolve_canonical_field("Party Name") == "seller_supplier"
    assert resolve_canonical_field("Customer") == "buyer_customer"
    assert resolve_canonical_field("Bill No") == "invoice_number"
    assert resolve_canonical_field("Inv No") == "invoice_number"
    assert resolve_canonical_field("Txn Date") == "invoice_date"
    assert resolve_canonical_field("Particulars") == "item_descriptions"
    assert resolve_canonical_field("Assessable Value") == "taxable_value"
    assert resolve_canonical_field("Tax Amount") == "gst"
    assert resolve_canonical_field("PO Number") == "order_reference"
    assert resolve_canonical_field("Challan No") == "delivery_information"
    assert resolve_canonical_field("Random Custom Header XYZ") is None


# -----------------------------------------------------------------------------
# 2. XLSX Ingestion Tests
# -----------------------------------------------------------------------------
def test_parse_valid_xlsx():
    """Verify parsing of valid XLSX dataset with mixed data types."""
    headers = [
        "Supplier",
        "Buyer",
        "Bill No",
        "Date",
        "Items",
        "Taxable Value",
        "GST",
        "Payment Mode",
    ]
    rows = [
        [
            "ABC Industrial Supplies",
            "XYZ Manufacturing Pvt Ltd",
            "INV-2026-1042",
            "2026-09-18",
            "Industrial bearings, Lubricant",
            50000.0,
            9000.0,
            "Bank Transfer",
        ],
        [
            "Apex Logistics",
            "XYZ Manufacturing Pvt Ltd",
            "INV-2026-1043",
            "2026-09-19",
            "Freight services",
            12500.0,
            2250.0,
            "Cheque",
        ],
    ]
    file_bytes = create_sample_xlsx_bytes(headers, rows)
    result = parse_transaction_file(file_bytes, "transactions.xlsx")

    assert result.file_type == "xlsx"
    assert result.total_rows == 2
    assert result.raw_column_count == 8
    assert len(result.canonical_transactions) == 2

    # Verify first transaction normalization
    t1 = result.canonical_transactions[0]
    assert t1.row_id == 1
    assert t1.seller_supplier == "ABC Industrial Supplies"
    assert t1.buyer_customer == "XYZ Manufacturing Pvt Ltd"
    assert t1.invoice_number == "INV-2026-1042"
    assert t1.invoice_date == "2026-09-18"
    assert "Industrial bearings" in t1.item_descriptions
    assert "Lubricant" in t1.item_descriptions
    assert t1.taxable_value == 50000.0
    assert t1.gst == 9000.0
    assert t1.total_amount == 59000.0
    assert t1.payment_information == "Bank Transfer"

    # Verify raw record preservation
    assert t1.raw_record["Supplier"] == "ABC Industrial Supplies"
    assert t1.raw_record["Bill No"] == "INV-2026-1042"


def test_xlsx_row_preservation_and_null_handling():
    """Verify null equivalents and row ID stability across sparse rows."""
    headers = ["Party", "Document No", "Amount", "GST", "Narration"]
    rows = [
        ["Alpha Ltd", "DOC-01", "₹ 10,000.00", "1,800", "Standard purchase"],
        ["Beta Corp", "DOC-02", "nan", "NULL", "Pending amount"],
        ["Gamma Inc", "DOC-03", "-", "N/A", ""],
    ]
    file_bytes = create_sample_xlsx_bytes(headers, rows)
    result = parse_transaction_file(file_bytes, "sparse.xlsx")

    assert result.total_rows == 3

    t1 = result.canonical_transactions[0]
    assert t1.row_id == 1
    assert t1.taxable_value == 10000.0
    assert t1.gst == 1800.0

    t2 = result.canonical_transactions[1]
    assert t2.row_id == 2
    assert t2.taxable_value is None
    assert t2.gst is None
    assert t2.narration_remarks == "Pending amount"

    t3 = result.canonical_transactions[2]
    assert t3.row_id == 3
    assert t3.taxable_value is None
    assert t3.gst is None
    assert t3.narration_remarks is None


# -----------------------------------------------------------------------------
# 3. CSV Ingestion Tests
# -----------------------------------------------------------------------------
def test_parse_valid_csv():
    """Verify parsing of comma-separated CSV with currencies and dates."""
    csv_text = (
        "Vendor,Customer,Invoice Number,Invoice Date,Description,Taxable Amount,Tax\n"
        "Global Tech,Acme Corp,INV-9901,15/08/2026,Software License,$1250.50,$225.09\n"
        "Local Print,Acme Corp,INV-9902,16-Aug-2026,Office Stationery,450.00,81.00\n"
    )
    result = parse_transaction_file(create_sample_csv_bytes(csv_text), "records.csv")

    assert result.file_type == "csv"
    assert result.total_rows == 2

    t1 = result.canonical_transactions[0]
    assert t1.seller_supplier == "Global Tech"
    assert t1.buyer_customer == "Acme Corp"
    assert t1.invoice_number == "INV-9901"
    assert t1.invoice_date == "2026-08-15"
    assert t1.taxable_value == 1250.50
    assert t1.gst == 225.09


def test_parse_semicolon_delimited_csv():
    """Verify automatic delimiter detection for European-style CSVs."""
    csv_text = (
        "Supplier;Buyer;Invoice_No;Amount\n"
        "Euro Parts;Acme Corp;EUR-100;5400.00\n"
        "Euro Tools;Acme Corp;EUR-101;1200.50\n"
    )
    result = parse_transaction_file(create_sample_csv_bytes(csv_text), "euro.csv")
    assert result.total_rows == 2
    assert result.canonical_transactions[0].seller_supplier == "Euro Parts"
    assert result.canonical_transactions[0].taxable_value == 5400.00


# -----------------------------------------------------------------------------
# 4. Warnings and Duplicate Identifier Tests
# -----------------------------------------------------------------------------
def test_duplicate_identifier_detection():
    """Verify duplicate invoice numbers generate schema warnings."""
    headers = ["Supplier", "Invoice Number", "Amount"]
    rows = [
        ["Supplier A", "INV-DUP-01", 1000],
        ["Supplier B", "INV-DUP-01", 2000],  # Duplicate invoice number
        ["Supplier C", "INV-UNIQUE-02", 3000],
    ]
    file_bytes = create_sample_xlsx_bytes(headers, rows)
    result = parse_transaction_file(file_bytes, "duplicates.xlsx")

    assert "INV-DUP-01" in result.duplicate_identifiers
    warning_codes = [w.code for w in result.warnings]
    assert "DUPLICATE_INVOICE_NUMBERS" in warning_codes


def test_unmapped_columns_warning():
    """Verify extra/custom columns produce an unmapped columns warning while retaining raw data."""
    headers = ["Supplier", "Amount", "Custom_Internal_Tracking_Code"]
    rows = [
        ["Supplier A", 1000, "TRACK-9988"],
    ]
    file_bytes = create_sample_xlsx_bytes(headers, rows)
    result = parse_transaction_file(file_bytes, "custom_cols.xlsx")

    assert "Custom_Internal_Tracking_Code" in result.unmapped_columns
    t = result.canonical_transactions[0]
    assert t.raw_record["Custom_Internal_Tracking_Code"] == "TRACK-9988"


# -----------------------------------------------------------------------------
# 5. Error Handling & Edge Cases
# -----------------------------------------------------------------------------
def test_empty_file_rejected():
    """Verify empty (0-byte) files raise IngestionError."""
    with pytest.raises(IngestionError, match="is empty"):
        parse_transaction_file(b"", "empty.xlsx")


def test_unsupported_format_rejected():
    """Verify unsupported extensions raise IngestionError."""
    with pytest.raises(IngestionError, match="Unsupported file format"):
        parse_transaction_file(b"some content", "statement.pdf")


def test_corrupted_xlsx_rejected():
    """Verify corrupted binary raises IngestionError cleanly."""
    with pytest.raises(IngestionError, match="Failed to open Excel workbook"):
        parse_transaction_file(b"PK\x03\x04not-a-valid-zip-or-excel", "corrupted.xlsx")


def test_no_data_rows_xlsx_rejected():
    """Verify header-only sheet with zero transaction rows raises IngestionError."""
    headers = ["Supplier", "Amount", "Date"]
    file_bytes = create_sample_xlsx_bytes(headers, [])
    with pytest.raises(IngestionError, match="contains no transaction rows"):
        parse_transaction_file(file_bytes, "no_rows.xlsx")


def test_canonical_transaction_compact_dict_and_json():
    """Verify compact dict and JSON representation exclude nulls and isolate target labels."""
    from app.ingestion.schema import CanonicalTransaction

    txn = CanonicalTransaction(
        row_id=42,
        seller_supplier="Acme Industrial",
        invoice_number="INV-4200",
        total_amount=15500.0,
        ground_truth_label="Purchase",
        custom_populated_fields={"Cost_Center": "ENG-01", "Voucher Category": "Purchase"},
    )

    compact_dict = txn.to_compact_dict()
    assert compact_dict["row_id"] == 42
    assert compact_dict["fields"]["supplier"] == "Acme Industrial"
    assert compact_dict["fields"]["doc_no"] == "INV-4200"
    assert compact_dict["fields"]["total_amount"] == 15500.0
    assert compact_dict["fields"]["Cost_Center"] == "ENG-01"

    # Verify target label isolation in compact dict
    assert "ground_truth_label" not in compact_dict
    assert "ground_truth_label" not in compact_dict["fields"]
    assert "Voucher Category" not in compact_dict["fields"]

    compact_json = txn.to_compact_json()
    assert '"supplier":"Acme Industrial"' in compact_json
    assert "Purchase" not in compact_json

