"""Dataset upload, schema discovery, and tabular preview endpoints."""

import math
import uuid
from typing import List, Optional
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.ingestion.parser import parse_transaction_file
from app.api.storage import dataset_storage
from app.api.schemas import (
    DatasetUploadResponse,
    DatasetSummaryResponse,
    PreviewRecord,
    PaginatedPreviewResponse,
)

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(file: UploadFile = File(...)):
    """
    Upload and parse an accounting dataset workbook (.xlsx) or delimiter-separated file (.csv).
    Discovers columns, validates schemas, and prepares transactions for classification.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename cannot be empty.")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed_doc = parse_transaction_file(content, filename=file.filename)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to parse transaction file: {str(e)}")

    raw_rows = [t.raw_record for t in parsed_doc.canonical_transactions]
    dataset_id = str(uuid.uuid4())

    stored = dataset_storage.save_dataset(
        dataset_id=dataset_id,
        filename=file.filename,
        transactions=parsed_doc.canonical_transactions,
        raw_rows=raw_rows,
        columns_detected=parsed_doc.detected_columns,
        canonical_fields_mapped=parsed_doc.mapped_canonical_fields,
        unmapped_columns=parsed_doc.unmapped_columns,
        warnings=[w.message for w in parsed_doc.warnings],
    )

    return DatasetUploadResponse(
        dataset_id=dataset_id,
        filename=file.filename,
        total_rows=stored["total_rows"],
        columns_detected=stored["columns_detected"],
        canonical_fields_mapped=stored["canonical_fields_mapped"],
        unmapped_columns=stored["unmapped_columns"],
        warnings=stored["warnings"],
        created_at=stored["created_at"],
    )


@router.get("", response_model=List[DatasetSummaryResponse])
def list_datasets():
    """List all registered datasets in the active session."""
    datasets = dataset_storage.list_datasets()
    return [
        DatasetSummaryResponse(
            dataset_id=d["dataset_id"],
            filename=d["filename"],
            total_rows=d["total_rows"],
            is_classified=d["is_classified"],
            processed_rows=d["processed_rows"],
            created_at=d["created_at"],
            status=d["status"],
        )
        for d in datasets
    ]


@router.get("/{dataset_id}", response_model=DatasetSummaryResponse)
def get_dataset(dataset_id: str):
    """Retrieve metadata summary for a single dataset."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    return DatasetSummaryResponse(
        dataset_id=ds["dataset_id"],
        filename=ds["filename"],
        total_rows=ds["total_rows"],
        is_classified=ds["is_classified"],
        processed_rows=ds["processed_rows"],
        created_at=ds["created_at"],
        status=ds["status"],
    )


@router.get("/{dataset_id}/preview", response_model=PaginatedPreviewResponse)
def preview_dataset(
    dataset_id: str,
    page: int = Query(1, ge=1, description="1-indexed page number"),
    page_size: int = Query(20, ge=1, le=100, description="Records per page"),
):
    """Retrieve paginated preview records with both canonical mappings and custom populated fields."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found.")

    txns = ds["transactions"]
    total_rows = len(txns)
    total_pages = max(1, math.ceil(total_rows / page_size))

    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    sliced = txns[start_idx:end_idx]

    records = [
        PreviewRecord(
            row_id=t.row_id,
            doc_no=t.invoice_number,
            invoice_date=str(t.invoice_date) if t.invoice_date else None,
            seller_supplier=t.seller_supplier,
            buyer_customer=t.buyer_customer,
            total_amount=t.total_amount,
            taxable_value=t.taxable_value,
            gst=t.gst,
            quantity=t.quantity,
            custom_fields=t.custom_populated_fields,
        )
        for t in sliced
    ]

    return PaginatedPreviewResponse(
        dataset_id=dataset_id,
        total_rows=total_rows,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
        records=records,
    )
