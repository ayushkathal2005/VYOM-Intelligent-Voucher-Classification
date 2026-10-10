"""In-memory thread-safe state store for datasets, classification jobs, and predictions."""

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.ingestion.schema import CanonicalTransaction
from app.ml.gemma.schemas import GemmaClassificationResult
from app.ml.guardrails.models import GuardrailEvaluation, TriageDecision, ConfidenceTier


class DatasetStorage:
    """Thread-safe storage manager for dataset ingestion, batch jobs, and audit predictions."""

    def __init__(self):
        self._lock = threading.Lock()
        self.datasets: Dict[str, Dict[str, Any]] = {}
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.predictions: Dict[str, Dict[int, Dict[str, Any]]] = {}
        self._pause_events: Dict[str, threading.Event] = {}
        self._cancel_flags: Dict[str, bool] = {}

    def save_dataset(
        self,
        dataset_id: str,
        filename: str,
        transactions: List[CanonicalTransaction],
        raw_rows: List[Dict[str, Any]],
        columns_detected: List[str],
        canonical_fields_mapped: Dict[str, str],
        unmapped_columns: List[str],
        warnings: List[str],
    ) -> Dict[str, Any]:
        """Register a newly ingested dataset."""
        with self._lock:
            record = {
                "dataset_id": dataset_id,
                "filename": filename,
                "transactions": transactions,
                "raw_rows": raw_rows,
                "total_rows": len(transactions),
                "columns_detected": columns_detected,
                "canonical_fields_mapped": canonical_fields_mapped,
                "unmapped_columns": unmapped_columns,
                "warnings": warnings,
                "created_at": datetime.now(timezone.utc),
                "is_classified": False,
                "processed_rows": 0,
                "status": "PENDING",
            }
            self.datasets[dataset_id] = record
            self.predictions[dataset_id] = {}
            return record

    def get_dataset(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.datasets.get(dataset_id)

    def list_datasets(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self.datasets.values())

    def create_job(self, job_id: str, dataset_id: str, total_rows: int, mode: str = "fast") -> Dict[str, Any]:
        with self._lock:
            job = {
                "job_id": job_id,
                "dataset_id": dataset_id,
                "status": "PROCESSING",
                "total_rows": total_rows,
                "processed_rows": 0,
                "progress_percent": 0.0,
                "mode": mode,
                "started_at": datetime.now(timezone.utc),
                "completed_at": None,
                "error_message": None,
            }
            self.jobs[job_id] = job
            ev = threading.Event()
            ev.set()  # running by default
            self._pause_events[job_id] = ev
            self._cancel_flags[job_id] = False

            if dataset_id in self.datasets:
                self.datasets[dataset_id]["status"] = "PROCESSING"
            return job

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self.jobs.get(job_id)

    def pause_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Cooperatively pause an active job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job or job["status"] not in ("PROCESSING", "QUEUED"):
                return job
            job["status"] = "PAUSED"
            ev = self._pause_events.get(job_id)
            if ev:
                ev.clear()
            ds_id = job["dataset_id"]
            if ds_id in self.datasets:
                self.datasets[ds_id]["status"] = "PAUSED"
            return job

    def resume_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Resume a paused job."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job or job["status"] != "PAUSED":
                return job
            job["status"] = "PROCESSING"
            ev = self._pause_events.get(job_id)
            if ev:
                ev.set()
            ds_id = job["dataset_id"]
            if ds_id in self.datasets:
                self.datasets[ds_id]["status"] = "PROCESSING"
            return job

    def cancel_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Cooperatively cancel an active or paused job, preserving completed work."""
        with self._lock:
            job = self.jobs.get(job_id)
            if not job or job["status"] in ("COMPLETED", "FAILED", "CANCELLED"):
                return job
            job["status"] = "CANCELLED"
            job["completed_at"] = datetime.now(timezone.utc)
            self._cancel_flags[job_id] = True
            ev = self._pause_events.get(job_id)
            if ev:
                ev.set()  # unblock if paused so the loop terminates immediately
            ds_id = job["dataset_id"]
            if ds_id in self.datasets:
                self.datasets[ds_id]["status"] = "CANCELLED"
            return job

    def check_job_control(self, job_id: str) -> str:
        """
        Check cooperative pause and cancel state.
        Blocks while paused until resumed or cancelled.
        Returns 'CONTINUE' or 'CANCELLED'.
        """
        import time
        if self._cancel_flags.get(job_id, False):
            return "CANCELLED"
        ev = self._pause_events.get(job_id)
        if ev and not ev.is_set():
            # Block while paused, checking cancellation periodically
            while ev and not ev.is_set():
                if self._cancel_flags.get(job_id, False):
                    return "CANCELLED"
                time.sleep(0.2)
        if self._cancel_flags.get(job_id, False):
            return "CANCELLED"
        return "CONTINUE"

    def update_job_progress(
        self,
        job_id: str,
        processed_rows: int,
        status: str = "PROCESSING",
        error_message: Optional[str] = None,
    ) -> None:
        with self._lock:
            if job_id not in self.jobs:
                return
            job = self.jobs[job_id]
            job["processed_rows"] = processed_rows
            total = job["total_rows"]
            job["progress_percent"] = round((processed_rows / max(total, 1)) * 100.0, 1)
            job["status"] = status
            if error_message:
                job["error_message"] = error_message
            if status in ("COMPLETED", "FAILED"):
                job["completed_at"] = datetime.now(timezone.utc)
                ds_id = job["dataset_id"]
                if ds_id in self.datasets:
                    self.datasets[ds_id]["is_classified"] = (status == "COMPLETED")
                    self.datasets[ds_id]["status"] = status
                    self.datasets[ds_id]["processed_rows"] = processed_rows

    def save_prediction(
        self,
        dataset_id: str,
        row_id: int,
        result: GemmaClassificationResult,
        evaluation: GuardrailEvaluation,
    ) -> None:
        with self._lock:
            if dataset_id not in self.predictions:
                self.predictions[dataset_id] = {}
            self.predictions[dataset_id][row_id] = {
                "row_id": row_id,
                "result": result,
                "evaluation": evaluation,
                "override": None,
            }

    def get_predictions(self, dataset_id: str) -> Dict[int, Dict[str, Any]]:
        with self._lock:
            return dict(self.predictions.get(dataset_id, {}))

    def get_prediction(self, dataset_id: str, row_id: int) -> Optional[Dict[str, Any]]:
        with self._lock:
            ds_preds = self.predictions.get(dataset_id, {})
            return ds_preds.get(row_id)

    def record_override(
        self,
        dataset_id: str,
        row_id: int,
        new_category: str,
        override_reason: str,
        reviewer_id: str,
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            ds_preds = self.predictions.get(dataset_id)
            if not ds_preds or row_id not in ds_preds:
                return None

            entry = ds_preds[row_id]
            prev_cat = entry["result"].prediction.category

            override_info = {
                "previous_category": prev_cat,
                "new_category": new_category,
                "override_reason": override_reason,
                "reviewer_id": reviewer_id,
                "timestamp": datetime.now(timezone.utc),
            }
            entry["override"] = override_info

            # Update prediction category and set triage decision to AUTO_VERIFIED
            entry["result"].prediction.category = new_category
            entry["evaluation"].predicted_category = new_category
            entry["evaluation"].triage_decision = TriageDecision.AUTO_VERIFIED
            entry["evaluation"].confidence_tier = ConfidenceTier.HIGH
            entry["evaluation"].contradictions = []
            entry["evaluation"].audit_notes.append(
                f"Human override applied by '{reviewer_id}': '{prev_cat}' -> '{new_category}'. Reason: {override_reason}"
            )
            return override_info


# Global singleton storage
dataset_storage = DatasetStorage()
