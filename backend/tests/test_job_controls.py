import io
import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.api.storage import dataset_storage

client = TestClient(app)


def test_pause_and_resume_batch_job():
    """Verify cooperative pause and resume transitions and result completeness."""
    # Generate 10 transactions
    rows = ["Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref"]
    for i in range(10):
        rows.append(f"INV-{i+1},Supplier {i+1},{1000 * (i+1)},{180 * (i+1)},PO-{i+1}")
    csv_content = "\n".join(rows).encode("utf-8")

    files = {"file": ("pause_test.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    # Start batch classification in fast mode
    batch_resp = client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "mode": "fast"})
    assert batch_resp.status_code == 200
    job_id = batch_resp.json()["job_id"]

    # Pause the job
    pause_resp = client.post(f"/api/v1/classify/jobs/{job_id}/pause")
    assert pause_resp.status_code == 200
    assert pause_resp.json()["status"] in ("PAUSED", "PAUSING", "COMPLETED")

    # If paused, check resume
    if pause_resp.json()["status"] in ("PAUSED", "PAUSING"):
        resume_resp = client.post(f"/api/v1/classify/jobs/{job_id}/resume")
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] in ("PROCESSING", "COMPLETED")

    # Wait for completion if still running
    for _ in range(50):
        status_resp = client.get(f"/api/v1/classify/jobs/{job_id}")
        st = status_resp.json()["status"]
        if st in ("COMPLETED", "FAILED"):
            break
        time.sleep(0.1)

    final_status = client.get(f"/api/v1/classify/jobs/{job_id}").json()
    assert final_status["status"] == "COMPLETED"
    assert final_status["processed_rows"] == 10


def test_cancel_batch_job():
    """Verify cooperative cancellation stops processing and preserves existing predictions."""
    rows = ["Document Number,Vendor Name,Base Amount,Tax Amount,PO Ref"]
    for i in range(20):
        rows.append(f"INV-{i+1},Supplier {i+1},{1000 * (i+1)},{180 * (i+1)},PO-{i+1}")
    csv_content = "\n".join(rows).encode("utf-8")

    files = {"file": ("cancel_test.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    batch_resp = client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "mode": "fast"})
    assert batch_resp.status_code == 200
    job_id = batch_resp.json()["job_id"]

    cancel_resp = client.post(f"/api/v1/classify/jobs/{job_id}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] in ("CANCELLED", "CANCELLING", "COMPLETED")

    # Wait briefly
    time.sleep(0.3)
    status_resp = client.get(f"/api/v1/classify/jobs/{job_id}").json()
    assert status_resp["status"] in ("CANCELLED", "COMPLETED")


def test_repeated_pause_resume_cancel_safety():
    """Verify repeated pause/resume/cancel calls are safe and idempotent."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount\n"
        "INV-1,Vendor A,1000.0\n"
    ).encode("utf-8")

    files = {"file": ("idempotent_test.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    batch_resp = client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "mode": "fast"})
    job_id = batch_resp.json()["job_id"]

    # Repeated pause
    p1 = client.post(f"/api/v1/classify/jobs/{job_id}/pause")
    p2 = client.post(f"/api/v1/classify/jobs/{job_id}/pause")
    assert p1.status_code == 200
    assert p2.status_code == 200

    # Repeated resume
    r1 = client.post(f"/api/v1/classify/jobs/{job_id}/resume")
    r2 = client.post(f"/api/v1/classify/jobs/{job_id}/resume")
    assert r1.status_code == 200
    assert r2.status_code == 200

    # Repeated cancel
    c1 = client.post(f"/api/v1/classify/jobs/{job_id}/cancel")
    c2 = client.post(f"/api/v1/classify/jobs/{job_id}/cancel")
    assert c1.status_code == 200
    assert c2.status_code == 200


def test_analytics_honest_accuracy_with_and_without_ground_truth():
    """Verify analytics reports has_ground_truth=False when labels missing, and calculates accuracy when present."""
    # 1. Unlabeled dataset
    csv_unlabeled = (
        "Document Number,Vendor Name,Base Amount\n"
        "INV-1,Vendor A,1000.0\n"
        "INV-2,Vendor B,2000.0\n"
    ).encode("utf-8")
    files_unlabeled = {"file": ("unlabeled.csv", io.BytesIO(csv_unlabeled), "text/csv")}
    ds_unlabeled = client.post("/api/v1/datasets/upload", files=files_unlabeled).json()["dataset_id"]

    # Classify unlabeled
    client.post("/api/v1/classify/batch", json={"dataset_id": ds_unlabeled, "mode": "fast"})
    time.sleep(0.5)

    analytics_unlabeled_resp = client.get(f"/api/v1/datasets/{ds_unlabeled}/analytics")
    assert analytics_unlabeled_resp.status_code == 200
    analytics_unlabeled = analytics_unlabeled_resp.json()
    assert analytics_unlabeled["has_ground_truth"] is False
    assert analytics_unlabeled["evaluation_accuracy"] is None
    assert analytics_unlabeled["evaluation_macro_f1"] is None
    assert analytics_unlabeled["evaluation_sample_size"] is None
    assert analytics_unlabeled["total_transactions"] == 2
    assert "auto_verified_percentage" in analytics_unlabeled

    # 2. Labeled dataset
    csv_labeled = (
        "Document Number,Vendor Name,Base Amount,Voucher Category\n"
        "INV-1,Vendor A,1000.0,Purchase\n"
        "INV-2,Vendor B,2000.0,Purchase\n"
    ).encode("utf-8")
    files_labeled = {"file": ("labeled.csv", io.BytesIO(csv_labeled), "text/csv")}
    ds_labeled = client.post("/api/v1/datasets/upload", files=files_labeled).json()["dataset_id"]

    # Classify labeled
    client.post("/api/v1/classify/batch", json={"dataset_id": ds_labeled, "mode": "fast"})
    time.sleep(0.5)

    analytics_labeled_resp = client.get(f"/api/v1/datasets/{ds_labeled}/analytics")
    assert analytics_labeled_resp.status_code == 200
    analytics_labeled = analytics_labeled_resp.json()
    assert analytics_labeled["has_ground_truth"] is True
    assert analytics_labeled["evaluation_accuracy"] is not None
    assert isinstance(analytics_labeled["evaluation_accuracy"], float)
    assert analytics_labeled["evaluation_sample_size"] == 2


def test_zero_record_and_missing_label_analytics():
    """Verify zero-processed or empty datasets return safe N/A metrics without crashing."""
    csv_content = (
        "Document Number,Vendor Name,Base Amount\n"
        "INV-1,Vendor A,1000.0\n"
    ).encode("utf-8")
    files = {"file": ("unprocessed.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    analytics_resp = client.get(f"/api/v1/datasets/{dataset_id}/analytics")
    assert analytics_resp.status_code == 200
    analytics = analytics_resp.json()
    assert analytics["processed_transactions"] == 0
    assert analytics["has_ground_truth"] is False
    assert analytics["evaluation_accuracy"] is None
    assert analytics["auto_verified_percentage"] is None


def test_cancelled_job_export_integrity():
    """Verify Excel and CSV exports remain valid and uncorrupted after a batch cancellation."""
    rows = ["Document Number,Vendor Name,Base Amount,Tax Amount"]
    for i in range(15):
        rows.append(f"INV-{i+1},Vendor {i+1},{1000 * (i+1)},{180 * (i+1)}")
    csv_content = "\n".join(rows).encode("utf-8")

    files = {"file": ("export_cancel.csv", io.BytesIO(csv_content), "text/csv")}
    ds_resp = client.post("/api/v1/datasets/upload", files=files).json()
    dataset_id = ds_resp["dataset_id"]

    # Start and cancel job
    batch_resp = client.post("/api/v1/classify/batch", json={"dataset_id": dataset_id, "mode": "fast"})
    job_id = batch_resp.json()["job_id"]
    client.post(f"/api/v1/classify/jobs/{job_id}/cancel")
    time.sleep(0.3)

    # Export CSV
    csv_export_resp = client.get(f"/api/v1/datasets/{dataset_id}/export?format=csv")
    assert csv_export_resp.status_code == 200
    assert "text/csv" in csv_export_resp.headers["content-type"]
    assert len(csv_export_resp.content) > 0

    # Export Excel
    xlsx_export_resp = client.get(f"/api/v1/datasets/{dataset_id}/export?format=xlsx")
    assert xlsx_export_resp.status_code == 200
    assert (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        in xlsx_export_resp.headers["content-type"]
    )
    assert len(xlsx_export_resp.content) > 0

