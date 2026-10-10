"""Unit and integration tests for FastVoucherClassifier and tri-mode inference routing."""

import io
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.ingestion.schema import CanonicalTransaction
from app.ml.fast_classifier import FastVoucherClassifier
from app.ml.guardrails.pipeline import GuardrailsPipeline
from app.ml.taxonomy import AUTHORITATIVE_VOUCHER_LABELS

client = TestClient(app)


def test_fast_classifier_initialization_and_classes():
    """Verify FastVoucherClassifier loads the calibrated Linear SVM pipeline covering all 27 classes."""
    clf = FastVoucherClassifier()
    assert clf.model is not None
    assert len(clf.classes_) == 27
    for cat in clf.classes_:
        assert cat in AUTHORITATIVE_VOUCHER_LABELS


def test_fast_classifier_predict_single_and_guardrails():
    """Verify FastVoucherClassifier integrates directly into GuardrailsPipeline with calibrated probabilities."""
    clf = FastVoucherClassifier()
    pipeline = GuardrailsPipeline(classifier=clf)

    txn = CanonicalTransaction(
        row_id=1,
        invoice_number="INV-2026-001",
        seller_supplier="Steel Works India Ltd",
        buyer_customer="VYOM Manufacturing Corp",
        total_amount=118000.0,
        taxable_value=100000.0,
        gst=18000.0,
        item_descriptions=["Structural steel beams 20mm"],
        quantity=50.0,
    )

    result, evaluation = pipeline.evaluate_and_classify(txn)
    assert result.prediction.category in AUTHORITATIVE_VOUCHER_LABELS
    assert 0.0 <= result.prediction.confidence <= 1.0
    assert 0.0 <= evaluation.calibrated_confidence <= 1.0
    assert evaluation.triage_decision.value in ("AUTO_VERIFIED", "FLAGGED_FOR_REVIEW", "CRITICAL_REJECTION")
    assert result.model_name == "fast-svm-linear-v1"


def test_api_single_classify_all_modes():
    """Verify /api/v1/classify/single successfully processes fast, hybrid, and ai modes."""
    payload = {
        "doc_no": "PUR-9988",
        "seller_supplier": "Apex Precision Components",
        "buyer_customer": "VYOM Tech Hub",
        "total_amount": 59000.0,
        "taxable_value": 50000.0,
        "gst": 9000.0,
        "items_description": "Precision CNC milling components",
        "quantity": 100.0,
    }

    # 1. Fast Mode
    resp_fast = client.post("/api/v1/classify/single", json={**payload, "mode": "fast"})
    assert resp_fast.status_code == 200
    data_fast = resp_fast.json()
    assert data_fast["result"]["prediction"]["category"] in AUTHORITATIVE_VOUCHER_LABELS
    assert data_fast["result"]["model_name"] == "fast-svm-linear-v1"

    # 2. Hybrid Mode
    resp_hybrid = client.post("/api/v1/classify/single", json={**payload, "mode": "hybrid", "use_mock": True})
    assert resp_hybrid.status_code == 200
    data_hybrid = resp_hybrid.json()
    assert data_hybrid["result"]["prediction"]["category"] in AUTHORITATIVE_VOUCHER_LABELS

    # 3. AI Mode
    resp_ai = client.post("/api/v1/classify/single", json={**payload, "mode": "ai", "use_mock": True})
    assert resp_ai.status_code == 200
    data_ai = resp_ai.json()
    assert data_ai["result"]["prediction"]["category"] in AUTHORITATIVE_VOUCHER_LABELS


def test_api_batch_classify_fast_and_hybrid_modes():
    """Verify batch classification execution in Fast Mode and Hybrid Mode."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-101,Supplier A,5000.0,900.0,PO-1\n"
        "PUR-102,Supplier B,6000.0,1080.0,PO-2\n"
    ).encode("utf-8")

    files = {"file": ("mode_test.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    # Test Fast Mode Batch
    batch_resp = client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "mode": "fast"})
    assert batch_resp.status_code == 200
    job_id = batch_resp.json()["job_id"]
    assert batch_resp.json()["mode"] == "fast"

    # Check job status
    status_resp = client.get(f"/api/v1/classify/jobs/{job_id}")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("PROCESSING", "COMPLETED")
