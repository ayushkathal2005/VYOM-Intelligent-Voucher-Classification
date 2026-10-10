"""Tabular dataset parser supporting .xlsx and .csv files with schema discovery."""

import io
import re
import logging
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple, Union
import openpyxl
import pandas as pd

from app.ingestion.schema import (
    CanonicalTransaction,
    IngestionResult,
    SchemaWarning,
)
from app.ingestion.aliases import resolve_canonical_field, is_target_column

logger = logging.getLogger("vyom.ingestion")

MAX_ALLOWED_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB
MAX_ALLOWED_ROWS = 50_000

NULL_EQUIVALENTS = {
    "",
    "nan",
    "null",
    "none",
    "n/a",
    "na",
    "#n/a",
    "#value!",
    "#ref!",
    "nil",
    "-",
    "--",
}


def sanitize_cell_value(val: Any) -> Any:
    """Normalize null equivalents and strip excessive whitespace."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return val
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    s = str(val).strip()
    if s.lower() in NULL_EQUIVALENTS:
        return None
    return s


def parse_numeric(val: Any) -> Optional[float]:
    """Parse a cell value into float, safely handling currency symbols, commas, and parentheses."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        if pd.isna(val):
            return None
        return float(val)

    s = str(val).strip()
    if s.lower() in NULL_EQUIVALENTS:
        return None

    # Handle accounting negative format: (123.45) -> -123.45
    is_negative = False
    if s.startswith("(") and s.endswith(")"):
        is_negative = True
        s = s[1:-1]
    elif s.startswith("-"):
        is_negative = True
        s = s[1:]

    # Remove currency symbols and separators: ₹, $, €, £, commas
    cleaned = re.sub(r"[^\d.]", "", s)
    if not cleaned:
        return None

    try:
        num = float(cleaned)
        return -num if is_negative else num
    except (ValueError, TypeError):
        return None


def parse_date_string(val: Any) -> Optional[str]:
    """Format dates into ISO YYYY-MM-DD."""
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")

    s = str(val).strip()
    if s.lower() in NULL_EQUIVALENTS:
        return None

    # Try common business date formats
    for fmt in (
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y/%m/%d",
        "%d.%m.%Y",
        "%d %b %Y",
        "%d-%b-%Y",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    return s


def parse_items_list(val: Any) -> List[str]:
    """Parse item descriptions, splitting by commas, semicolons, or newlines if present."""
    if val is None:
        return []
    s = str(val).strip()
    if s.lower() in NULL_EQUIVALENTS:
        return []
    # Split on commas, semicolons, or pipe
    parts = re.split(r"[,;|\n]+", s)
    cleaned = [p.strip() for p in parts if p.strip() and p.strip().lower() not in NULL_EQUIVALENTS]
    return cleaned if cleaned else [s]


class IngestionError(Exception):
    """Raised when file parsing fails fatally."""
    pass


def parse_transaction_file(
    file_bytes: bytes,
    filename: str,
) -> IngestionResult:
    """
    Ingest, validate, and normalize a .xlsx or .csv financial transaction dataset.

    Security & Safety Guarantees:
    - Never executes spreadsheet formulas (openpyxl data_only=True).
    - Enforces file size and row thresholds.
    - Preserves all original row values in raw_record.
    - Strips ground truth target labels from feature representations to prevent leakage.
    - Never logs customer/financial payload data.
    """
    if not file_bytes or len(file_bytes) == 0:
        raise IngestionError(f"Uploaded file '{filename}' is empty (0 bytes).")

    if len(file_bytes) > MAX_ALLOWED_FILE_SIZE_BYTES:
        raise IngestionError(
            f"File '{filename}' exceeds maximum allowed size of {MAX_ALLOWED_FILE_SIZE_BYTES // (1024 * 1024)}MB."
        )

    lower_name = filename.lower()
    if lower_name.endswith(".xlsx"):
        file_type = "xlsx"
        raw_headers, raw_rows = _read_xlsx(file_bytes, filename)
    elif lower_name.endswith(".csv"):
        file_type = "csv"
        raw_headers, raw_rows = _read_csv(file_bytes, filename)
    else:
        raise IngestionError(
            f"Unsupported file format '{filename}'. Only .xlsx and .csv are supported."
        )

    if not raw_rows:
        raise IngestionError(
            f"Dataset '{filename}' contains no transaction rows."
        )

    if len(raw_rows) > MAX_ALLOWED_ROWS:
        raise IngestionError(
            f"Dataset '{filename}' contains {len(raw_rows)} rows, which exceeds the limit of {MAX_ALLOWED_ROWS}."
        )

    # Discover target label column if present (e.g. for development evaluation/benchmarks)
    target_col = next((h for h in raw_headers if is_target_column(h)), None)
    has_target = target_col is not None

    # Header discovery and mapping (strictly omitting target column from feature mapping)
    mapped_fields: Dict[str, str] = {}
    unmapped_columns: List[str] = []
    for h in raw_headers:
        if is_target_column(h):
            continue  # NEVER map target column into canonical features
        canon = resolve_canonical_field(h)
        if canon:
            mapped_fields[h] = canon
        else:
            unmapped_columns.append(h)

    warnings: List[SchemaWarning] = []
    if unmapped_columns:
        warnings.append(
            SchemaWarning(
                code="UNMAPPED_COLUMNS",
                message=f"Preserved {len(unmapped_columns)} columns without canonical mapping.",
                affected_columns=unmapped_columns,
            )
        )

    # Core field check
    found_canonicals = set(mapped_fields.values())
    has_amount = bool(found_canonicals & {"taxable_value", "total_amount"})
    if not has_amount:
        warnings.append(
            SchemaWarning(
                code="MISSING_AMOUNT_FIELD",
                message="No taxable value or total amount column detected. Accounting signals may be restricted.",
                affected_columns=[],
            )
        )

    canonical_txns: List[CanonicalTransaction] = []
    seen_invoices: Dict[str, int] = {}
    duplicates: List[str] = []

    for idx, row in enumerate(raw_rows, start=1):
        # Extract ground truth label strictly for evaluation container (never for inference features)
        gt_label = None
        if target_col and row.get(target_col) is not None:
            raw_gt = sanitize_cell_value(row.get(target_col))
            if raw_gt is not None:
                gt_label = str(raw_gt).strip()

        # Build canonical object while preserving full raw_record
        txn_data: Dict[str, Any] = {
            "row_id": idx,
            "ground_truth_label": gt_label,
            "raw_record": row,
            "custom_populated_fields": {},
        }

        # Populate mapped canonical fields
        for raw_col, canon_field in mapped_fields.items():
            raw_val = row.get(raw_col)
            if raw_val is None:
                continue

            # If this canonical attribute was already populated by an earlier column in this row,
            # preserve this column in custom_populated_fields so its critical data is NOT lost or overwritten
            if canon_field in txn_data and txn_data[canon_field] is not None:
                sanitized_dup = sanitize_cell_value(raw_val)
                if sanitized_dup is not None:
                    txn_data["custom_populated_fields"][raw_col] = sanitized_dup
                continue

            if canon_field in ("taxable_value", "gst", "discount", "freight", "total_amount", "quantity"):
                parsed_num = parse_numeric(raw_val)
                if parsed_num is not None:
                    txn_data[canon_field] = parsed_num

            elif canon_field == "invoice_date":
                parsed_dt = parse_date_string(raw_val)
                if parsed_dt is not None:
                    txn_data[canon_field] = parsed_dt
            elif canon_field == "item_descriptions":
                items = parse_items_list(raw_val)
                if items:
                    txn_data[canon_field] = items
            else:
                sanitized = sanitize_cell_value(raw_val)
                if sanitized is not None:
                    txn_data[canon_field] = str(sanitized)

        # Collect any unmapped columns that are populated (non-null) for this specific row
        # STRICT LEAKAGE PREVENTION: target column is never added to custom_populated_fields
        for unmapped_col in unmapped_columns:
            if is_target_column(unmapped_col):
                continue
            val = row.get(unmapped_col)
            sanitized = sanitize_cell_value(val)
            if sanitized is not None:
                txn_data["custom_populated_fields"][unmapped_col] = sanitized

        # Compute total_amount approximation if missing
        if "total_amount" not in txn_data and "taxable_value" in txn_data:
            tax = txn_data.get("gst", 0.0) or 0.0
            freight = txn_data.get("freight", 0.0) or 0.0
            disc = txn_data.get("discount", 0.0) or 0.0
            txn_data["total_amount"] = round(txn_data["taxable_value"] + tax + freight - disc, 2)

        # Track invoice duplicates
        inv_no = txn_data.get("invoice_number")
        if inv_no:
            inv_clean = str(inv_no).strip()
            if inv_clean:
                if inv_clean in seen_invoices:
                    seen_invoices[inv_clean] += 1
                    if inv_clean not in duplicates:
                        duplicates.append(inv_clean)
                else:
                    seen_invoices[inv_clean] = 1

        canonical_obj = CanonicalTransaction(**txn_data)
        canonical_txns.append(canonical_obj)

    if duplicates:
        warnings.append(
            SchemaWarning(
                code="DUPLICATE_INVOICE_NUMBERS",
                message=f"Found {len(duplicates)} duplicate document/invoice numbers across rows.",
                affected_columns=["invoice_number"],
                row_count=len(duplicates),
            )
        )

    logger.info(
        "Successfully ingested %s: %d rows, %d columns, %d mapped, has_target=%s.",
        filename,
        len(canonical_txns),
        len(raw_headers),
        len(mapped_fields),
        has_target,
    )

    return IngestionResult(
        filename=filename,
        file_type=file_type,
        total_rows=len(canonical_txns),
        raw_column_count=len(raw_headers),
        detected_columns=raw_headers,
        mapped_canonical_fields=mapped_fields,
        unmapped_columns=unmapped_columns,
        warnings=warnings,
        duplicate_identifiers=duplicates,
        has_target_column=has_target,
        target_column_name=target_col,
        canonical_transactions=canonical_txns,
    )



def _read_xlsx(file_bytes: bytes, filename: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Parse Excel workbook with openpyxl in data_only mode (no formula execution)."""
    try:
        wb = openpyxl.load_workbook(
            io.BytesIO(file_bytes),
            read_only=True,
            data_only=True,  # Crucial security setting: retrieve evaluated values, never execute formulas
        )
    except Exception as e:
        raise IngestionError(f"Failed to open Excel workbook '{filename}': {str(e)}")

    sheet_names = wb.sheetnames
    if not sheet_names:
        raise IngestionError(f"Excel workbook '{filename}' has no sheets.")

    ws = wb[sheet_names[0]]
    rows_iter = ws.iter_rows(values_only=True)

    try:
        header_row = next(rows_iter, None)
    except Exception as e:
        raise IngestionError(f"Error reading header row from '{filename}': {str(e)}")

    if not header_row:
        raise IngestionError(f"Spreadsheet '{filename}' is empty.")

    # Headers
    raw_headers = [str(h).strip() if h is not None else f"Column_{i+1}" for i, h in enumerate(header_row)]

    data_rows: List[Dict[str, Any]] = []
    for r in rows_iter:
        if not r or all(c is None for c in r):
            continue  # Skip completely empty rows
        row_dict = {}
        has_content = False
        for i, val in enumerate(r):
            col_name = raw_headers[i] if i < len(raw_headers) else f"Column_{i+1}"
            sanitized = sanitize_cell_value(val)
            row_dict[col_name] = sanitized
            if sanitized is not None:
                has_content = True
        if has_content:
            data_rows.append(row_dict)

    wb.close()
    return raw_headers, data_rows


def _read_csv(file_bytes: bytes, filename: str) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Parse CSV with delimiter and encoding auto-detection."""
    # Attempt UTF-8 then Latin-1
    text = None
    for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if text is None:
        raise IngestionError(f"Failed to decode text for CSV file '{filename}'.")

    # Delimiter sniff
    sample = text[:4096]
    delimiter = ","
    for d in (",", ";", "\t", "|"):
        if sample.count(d) > sample.count(delimiter):
            delimiter = d

    try:
        df = pd.read_csv(
            io.StringIO(text),
            sep=delimiter,
            dtype=object,  # Read all raw columns as strings to prevent automatic lossy truncation
            keep_default_na=False,
        )
    except Exception as e:
        raise IngestionError(f"Failed to parse CSV file '{filename}': {str(e)}")

    if df.empty and len(df.columns) == 0:
        raise IngestionError(f"CSV file '{filename}' contains no data.")

    raw_headers = [str(col).strip() for col in df.columns]

    data_rows: List[Dict[str, Any]] = []
    for _, series in df.iterrows():
        row_dict = {}
        has_content = False
        for col in raw_headers:
            val = series.get(col)
            sanitized = sanitize_cell_value(val)
            row_dict[col] = sanitized
            if sanitized is not None:
                has_content = True
        if has_content:
            data_rows.append(row_dict)

    return raw_headers, data_rows
