"""Classification execution endpoints for single transactions and background batch jobs."""

import asyncio
import logging
import uuid
from typing import Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.ingestion.schema import CanonicalTransaction
from app.ml.gemma.client import GemmaClassifier
from app.ml.guardrails.pipeline import GuardrailsPipeline
from app.api.storage import dataset_storage
from app.api.schemas import (
    SingleClassifyRequest,
    SingleClassifyResponse,
    BatchClassifyRequest,
    BatchClassifyJobResponse,
)

logger = logging.getLogger("vyom.api.classification")
router = APIRouter(prefix="/classify", tags=["Classification"])


from concurrent.futures import ThreadPoolExecutor, as_completed

def run_batch_classification_task(job_id: str, dataset_id: str, use_mock: Optional[bool]):
    """Background task processing all transactions in a dataset with bounded concurrency."""
    ds = dataset_storage.get_dataset(dataset_id)
    if not ds:
        dataset_storage.update_job_progress(job_id, 0, status="FAILED", error_message="Dataset not found.")
        return

    txns = ds["transactions"]
    total = len(txns)

    classifier = GemmaClassifier(force_mock=use_mock) if use_mock is not None else GemmaClassifier()
    pipeline = GuardrailsPipeline(classifier=classifier)

    # Safe bounded concurrency: 4 workers for live API, 1 for mock adapter
    max_workers = 4 if not classifier.is_mock else 1

    try:
        if max_workers > 1:
            completed_count = 0
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_txn = {
                    executor.submit(pipeline.evaluate_and_classify, t): t
                    for t in txns
                }
                for future in as_completed(future_to_txn):
                    t = future_to_txn[future]
                    try:
                        result, evaluation = future.result()
                    except Exception as row_err:
                        logger.error("Error classifying row %d: %s. Applying fallback.", t.row_id, str(row_err))
                        fallback_pipe = GuardrailsPipeline(classifier=GemmaClassifier(force_mock=True))
                        result, evaluation = fallback_pipe.evaluate_and_classify(t)
                        evaluation.audit_notes.append(f"Row fallback applied: {str(row_err)}")

                    dataset_storage.save_prediction(dataset_id, t.row_id, result, evaluation)
                    completed_count += 1
                    dataset_storage.update_job_progress(job_id, processed_rows=completed_count, status="PROCESSING")
        else:
            for idx, t in enumerate(txns, start=1):
                try:
                    result, evaluation = pipeline.evaluate_and_classify(t)
                except Exception as row_err:
                    logger.error("Error classifying row %d: %s. Applying fallback.", t.row_id, str(row_err))
                    fallback_pipe = GuardrailsPipeline(classifier=GemmaClassifier(force_mock=True))
                    result, evaluation = fallback_pipe.evaluate_and_classify(t)
                    evaluation.audit_notes.append(f"Row fallback applied: {str(row_err)}")

                dataset_storage.save_prediction(dataset_id, t.row_id, result, evaluation)
                # Update progress incrementally on every row for real-time UI feedback
                dataset_storage.update_job_progress(job_id, processed_rows=idx, status="PROCESSING")

        dataset_storage.update_job_progress(job_id, processed_rows=total, status="COMPLETED")
        logger.info("Batch classification job '%s' completed successfully (%d rows).", job_id, total)
    except Exception as e:
        logger.error("Batch classification job '%s' failed: %s", job_id, str(e))
        dataset_storage.update_job_progress(job_id, processed_rows=0, status="FAILED", error_message=str(e))


@router.post("/single", response_model=SingleClassifyResponse)
def classify_single(payload: SingleClassifyRequest):
    """Classify a single financial transaction record on-demand with full guardrails evaluation."""
    txn = CanonicalTransaction(
        row_id=payload.row_id or 1,
        invoice_number=payload.doc_no,
        invoice_date=payload.invoice_date,
        seller_supplier=payload.seller_supplier,
        buyer_customer=payload.buyer_customer,
        total_amount=payload.total_amount,
        taxable_value=payload.taxable_value,
        gst=payload.gst,
        quantity=payload.quantity,
        item_descriptions=[payload.items_description] if payload.items_description else [],
        custom_populated_fields=payload.custom_populated_fields,
    )

    classifier = GemmaClassifier(force_mock=payload.use_mock) if payload.use_mock is not None else GemmaClassifier()
    pipeline = GuardrailsPipeline(classifier=classifier)

    result, evaluation = pipeline.evaluate_and_classify(txn)

    return SingleClassifyResponse(
        result=result,
        evaluation=evaluation,
    )


@router.post("/batch", response_model=BatchClassifyJobResponse)
def start_batch_classification(payload: BatchClassifyRequest, background_tasks: BackgroundTasks):
    """
    Launch asynchronous batch classification over all transactions in an uploaded dataset.
    Returns a job identifier for status polling.
    """
    ds = dataset_storage.get_dataset(payload.dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset '{payload.dataset_id}' not found.")

    job_id = str(uuid.uuid4())
    job = dataset_storage.create_job(job_id, payload.dataset_id, ds["total_rows"])

    background_tasks.add_task(
        run_batch_classification_task,
        job_id=job_id,
        dataset_id=payload.dataset_id,
        use_mock=payload.use_mock,
    )

    return BatchClassifyJobResponse(
        job_id=job["job_id"],
        dataset_id=job["dataset_id"],
        status=job["status"],
        total_rows=job["total_rows"],
        processed_rows=job["processed_rows"],
        progress_percent=job["progress_percent"],
        started_at=job["started_at"],
    )


@router.get("/jobs/{job_id}", response_model=BatchClassifyJobResponse)
@router.get("/batch/{job_id}/status", response_model=BatchClassifyJobResponse)
def get_job_status(job_id: str):
    """Poll the status and progress percentage of a running or completed classification job."""
    job = dataset_storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    return BatchClassifyJobResponse(
        job_id=job["job_id"],
        dataset_id=job["dataset_id"],
        status=job["status"],
        total_rows=job["total_rows"],
        processed_rows=job["processed_rows"],
        progress_percent=job["progress_percent"],
        started_at=job["started_at"],
        completed_at=job["completed_at"],
        error_message=job["error_message"],
    )
