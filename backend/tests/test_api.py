"""Comprehensive test suite for Phase 8: Backend REST API endpoints."""

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import openpyxl

from app.main import app

client = TestClient(app)


# -----------------------------------------------------------------------------
# 1. Taxonomy & Knowledge Base Endpoints
# -----------------------------------------------------------------------------
def test_get_all_taxonomy_cards():
    """Verify GET /api/v1/taxonomy returns all 27 authoritative voucher cards."""
    resp = client.get("/api/v1/taxonomy")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 27
    categories = [c["category"] for c in data]
    assert "Purchase" in categories
    assert "Sales" in categories
    assert "Contra" in categories
    assert "Journal" in categories
    assert "Salary / Payroll" in categories


def test_get_single_taxonomy_card():
    """Verify GET /api/v1/taxonomy/{category} returns details and ledgers."""
    resp = client.get("/api/v1/taxonomy/Contra")
    assert resp.status_code == 200
    card = resp.json()
    assert card["category"] == "Contra"
    assert card["expected_flow"] == "INTERNAL"
    assert len(card["typical_ledgers"]) > 0
    assert len(card["disambiguation_rule"]) > 0

    # Test non-existent category
    err_resp = client.get("/api/v1/taxonomy/InvalidCategory123")
    assert err_resp.status_code == 404


# -----------------------------------------------------------------------------
# 2. Single Transaction Classification Endpoint
# -----------------------------------------------------------------------------
def test_single_classify_endpoint_clean_purchase():
    """Verify POST /api/v1/classify/single classifies an inward supplier procurement record."""
    payload = {
        "row_id": 101,
        "doc_no": "PUR-9921",
        "seller_supplier": "Precision Machine Works Ltd",
        "total_amount": 45000.0,
        "taxable_value": 40000.0,
        "gst": 5000.0,
        "items_description": "Industrial Bearings",
        "custom_populated_fields": {"PO Ref": "PO-10992"},
        "use_mock": True,
    }
    resp = client.post("/api/v1/classify/single", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "result" in data
    assert "evaluation" in data
    assert data["result"]["prediction"]["category"] == "Purchase"
    assert data["evaluation"]["calibrated_confidence"] >= 0.75
    assert data["evaluation"]["triage_decision"] in ("AUTO_VERIFIED", "FLAGGED_FOR_REVIEW")


# -----------------------------------------------------------------------------
# 3. Dataset Upload & Tabular Preview Endpoints
# -----------------------------------------------------------------------------
def test_dataset_upload_csv_and_preview():
    """Verify POST /api/v1/datasets/upload parses CSV and GET /preview paginates records."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-101,Supplier Alpha,1000.0,180.0,PO-01\n"
        "PUR-102,Supplier Beta,2000.0,360.0,PO-02\n"
        "PUR-103,Supplier Gamma,3000.0,540.0,PO-03\n"
    ).encode("utf-8")

    files = {"file": ("test_purchases.csv", io.BytesIO(csv_content), "text/csv")}
    upload_resp = client.post("/api/v1/datasets/upload", files=files)
    assert upload_resp.status_code == 200
    upload_data = upload_resp.json()
    dataset_id = upload_data["dataset_id"]
    assert upload_data["total_rows"] == 3
    assert "Document Number" in upload_data["columns_detected"]

    # Preview
    preview_resp = client.get(f"/api/v1/datasets/{dataset_id}/preview?page=1&page_size=2")
    assert preview_resp.status_code == 200
    preview_data = preview_resp.json()
    assert preview_data["total_rows"] == 3
    assert preview_data["total_pages"] == 2
    assert len(preview_data["records"]) == 2
    assert preview_data["records"][0]["seller_supplier"] == "Supplier Alpha"


def test_dataset_upload_xlsx():
    """Verify POST /api/v1/datasets/upload parses in-memory Excel workbook."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sheet1"
    ws.append(["Document Number", "Customer", "Base Amount", "Tax Amount", "Delivery Ref"])
    ws.append(["SAL-501", "Client One", 5000.0, 900.0, "DN-11"])
    ws.append(["SAL-502", "Client Two", 8000.0, 1440.0, "DN-12"])

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    files = {"file": ("sales_batch.xlsx", buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    resp = client.post("/api/v1/datasets/upload", files=files)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_rows"] == 2
    assert data["filename"] == "sales_batch.xlsx"


# -----------------------------------------------------------------------------
# 4. Batch Classification Job Execution & Polling
# -----------------------------------------------------------------------------
def test_batch_classification_workflow():
    """Verify batch job creation, asynchronous execution, and status polling."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-801,Acme Parts,15000.0,2700.0,PO-991\n"
        "PUR-802,Beta Fasteners,22000.0,3960.0,PO-992\n"
    ).encode("utf-8")

    files = {"file": ("batch_sample.csv", io.BytesIO(csv_content), "text/csv")}
    up_resp = client.post("/api/v1/datasets/upload", files=files)
    dataset_id = up_resp.json()["dataset_id"]

    # Start Batch Job
    job_resp = client.post(
        "/api/v1/classify/batch",
        json={"dataset_id": dataset_id, "use_mock": True},
    )
    assert job_resp.status_code == 200
    job_data = job_resp.json()
    job_id = job_data["job_id"]
    assert job_data["status"] in ("PROCESSING", "COMPLETED")

    # In TestClient, background tasks execute synchronously before return
    poll_resp = client.get(f"/api/v1/classify/jobs/{job_id}")
    assert poll_resp.status_code == 200
    poll_data = poll_resp.json()
    assert poll_data["status"] == "COMPLETED"
    assert poll_data["processed_rows"] == 2
    assert poll_data["progress_percent"] == 100.0

    # Also verify route alias /batch/{job_id}/status
    alias_resp = client.get(f"/api/v1/classify/batch/{job_id}/status")
    assert alias_resp.status_code == 200
    assert alias_resp.json()["status"] == "COMPLETED"


# -----------------------------------------------------------------------------
# 5. Predictions Query, Triage Filtering & Human Override
# -----------------------------------------------------------------------------
def test_predictions_query_and_override():
    """Verify predictions query, category search, and human override update."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-301,Precision Tools,10000.0,1800.0,PO-33\n"
        "PUR-302,Global Steel,25000.0,4500.0,PO-34\n"
    ).encode("utf-8")

    files = {"file": ("override_test.csv", io.BytesIO(csv_content), "text/csv")}
    dataset_id = client.post("/api/v1/datasets/upload", files=files).json()["dataset_id"]

    # Run batch classify
    client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "use_mock": True})

    # Query predictions
    preds_resp = client.get(f"/api/v1/datasets/{dataset_id}/predictions?page=1&page_size=10")
    assert preds_resp.status_code == 200
    preds_data = preds_resp.json()
    assert preds_data["total_records"] == 2
    assert len(preds_data["predictions"]) == 2

    # Query single row detail
    detail_resp = client.get(f"/api/v1/datasets/{dataset_id}/predictions/1")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["row_id"] == 1
    assert detail["predicted_category"] in ("Purchase", "Purchase Order")
    assert detail["is_overridden"] is False

    # Apply Human Override on Row 1
    override_payload = {
        "overridden_category": "Payment",
        "override_reason": "Auditor identified this document is an unfulfilled procurement order.",
        "reviewer_id": "senior-auditor-42",
    }
    over_resp = client.post(
        f"/api/v1/datasets/{dataset_id}/predictions/1/override",
        json=override_payload,
    )
    assert over_resp.status_code == 200
    over_data = over_resp.json()
    assert over_data["status"] == "OVERRIDDEN"
    assert over_data["new_category"] == "Payment"

    # Verify updated prediction detail reflects override
    updated_detail = client.get(f"/api/v1/datasets/{dataset_id}/predictions/1").json()
    assert updated_detail["is_overridden"] is True
    assert updated_detail["predicted_category"] == "Payment"
    assert updated_detail["overridden_category"] == "Payment"
    assert updated_detail["override_reason"] == override_payload["override_reason"]
    assert updated_detail["triage_decision"] == "AUTO_VERIFIED"


# -----------------------------------------------------------------------------
# 6. Analytics & Audit Summary Endpoint
# -----------------------------------------------------------------------------
def test_dataset_analytics_endpoint():
    """Verify GET /api/v1/datasets/{id}/analytics generates accurate distribution metrics."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-401,Supplier A,5000.0,900.0,PO-1\n"
        "PUR-402,Supplier B,6000.0,1080.0,PO-2\n"
    ).encode("utf-8")

    files = {"file": ("analytics_test.csv", io.BytesIO(csv_content), "text/csv")}
    dataset_id = client.post("/api/v1/datasets/upload", files=files).json()["dataset_id"]
    client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "use_mock": True})

    analytics_resp = client.get(f"/api/v1/datasets/{dataset_id}/analytics")
    assert analytics_resp.status_code == 200
    an = analytics_resp.json()
    assert an["total_transactions"] == 2
    assert "Purchase Order" in an["category_distribution"] or "Purchase" in an["category_distribution"]
    assert an["average_confidence"] > 0.0
    assert an["auto_verified_percentage"] >= 0.0


# -----------------------------------------------------------------------------
# 7. Export Engine (CSV and XLSX)
# -----------------------------------------------------------------------------
def test_dataset_export_csv_and_xlsx():
    """Verify audited export generation in CSV and XLSX streaming formats."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref\n"
        "PUR-901,Industrial Supply,12000.0,2160.0,PO-88\n"
    ).encode("utf-8")

    files = {"file": ("export_test.csv", io.BytesIO(csv_content), "text/csv")}
    dataset_id = client.post("/api/v1/datasets/upload", files=files).json()["dataset_id"]
    client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "use_mock": True})

    # Export CSV
    csv_resp = client.get(f"/api/v1/datasets/{dataset_id}/export?format=csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    csv_text = csv_resp.content.decode("utf-8")
    assert "VYOM_Predicted_Category" in csv_text
    assert "VYOM_Calibrated_Confidence" in csv_text
    assert "Purchase" in csv_text

    # Export XLSX
    xlsx_resp = client.get(f"/api/v1/datasets/{dataset_id}/export?format=xlsx")
    assert xlsx_resp.status_code == 200
    assert "spreadsheetml" in xlsx_resp.headers["content-type"]
    wb = openpyxl.load_workbook(io.BytesIO(xlsx_resp.content))
    sheet = wb.active
    headers = [cell.value for cell in sheet[1]]
    assert "VYOM_Predicted_Category" in headers
    assert "VYOM_Triage_Decision" in headers
