# VYOM+ — Project State & Phase Gate Tracking

> **Authoritative Phase-Gated Tracking Document**
> Last Updated: 2026-10-10
> Current Authorized Phase: **Phase 9 — Connected Dashboard & Interactive Review Interface**
> Status: **COMPLETE** (Awaiting user review at Phase 9 Gate)

---

## 1. Executive Status & Phase Progress

| Phase | Name | Status | Commit | Remote Push | Gate Approval |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 0 | Repository Audit | COMPLETE | `8a2dc3c` | Verified (`origin/main`) | Approved |
| 1 | Project Foundation | COMPLETE | `0d12553` | Verified (`origin/main`) | Approved |
| 2 | Visual Foundation | COMPLETE | `f7e8692` | Verified (`origin/main`) | Approved |
| 3 | Data Ingestion | COMPLETE | `787a7f7` | Verified (`origin/main`) | Approved |
| 4 | Baseline Classifier | COMPLETE | `89e42c6` | Verified (`origin/main`) | Approved |
| 5 | Gemma 4 Integration | COMPLETE | `cb1303c` | Verified (`origin/main`) | Approved |
| 6 | Accounting Signals & Semantic Retrieval | COMPLETE | `4935175` | Verified (`origin/main`) | Approved |
| 7 | Confidence & Guardrails | COMPLETE | `bef4e46` | Verified (`origin/main`) | Approved |
| 8 | Backend REST API | COMPLETE | `369f67f` | Verified (`origin/main`) | Approved |
| **9** | **Connected Dashboard** | **COMPLETE** | Pending | Pending (`origin/main`) | **Current Phase Gate** |
| 10 | Robustness & Evaluation | PENDING | — | — | Not Authorized |
| 11 | Release & Deployment | PENDING | — | — | Not Authorized |


---

## 2. Environment & System Audit

- **Operating System**: Windows (x64)
- **Repository Path**: `C:\VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs`
- **Active Branch**: `main`
- **Remote Upstream**: `origin -> https://github.com/ayushkathal2005/VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs.git`
- **Remote Push Connectivity**: Verified (`git push --dry-run origin main` returned code 0)
- **Git User**: `ayushkathal2005 <ayush.kathal100@gmail.com>`
- **Node.js**: `v24.12.0`
- **npm / npx**: `v11.6.2` (invoked via `npm.cmd` / `npx.cmd` to comply with Windows PowerShell script execution policy)
- **Python Runtimes**:
  - `C:\Python314\python.exe` (Python 3.14.0)
  - `C:\Python313\python.exe` (Python 3.13.0 — recommended for venv to ensure stable prebuilt binary wheel compatibility for scientific/ML packages)
  - Python 3.11 also installed via WindowsApps

---

## 3. Existing Repository State & Assets

- **Pre-existing Files**:
  - `README.md` (2,120 lines, 53,268 bytes): Preserved completely. Contains the comprehensive Hacktoberfest challenge proposal, problem formulation, and 27-class taxonomy.
- **Pre-existing Code & Tests**: None. Repository was in initial qualifier documentation state.
- **Working Tree**: Clean prior to Phase 0. No untracked code or conflicting stashes.

---

## 4. Master Architectural Blueprint

### 4.1 System Components
1. **Frontend**:
   - Next.js (App Router, React 19 / TypeScript).
   - Tailwind CSS with centralized design tokens matching the reference aesthetic:
     - Main Background: `#050505`
     - Elevated Surface: `#0B0805`
     - Secondary Surface: `#11100E`
     - Primary Text: `#F4EBDD`
     - Muted Text: `#A69A87`
     - Gold Accent: `#F0AE2C`
     - Deep Gold: `#9D7019`
     - Subtle Border: `rgba(191, 145, 51, 0.16)`
   - Hero visual featuring cinematic glass-jar aesthetic and editorial typography ("Your books. Understood by AI.").
   - Comprehensive dashboard suite: Dataset Upload, Schema Discovery, Record Preview, Processing Queue, Prediction Results, Transaction Detail, Low-Confidence Review Queue, Analytics/Metrics, and Export Engine.
2. **Backend**:
   - Python FastAPI service with Pydantic v2 schemas.
   - Pandas and openpyxl for robust tabular ingestion (.xlsx and .csv).
   - Pytest for test-driven validation.
3. **AI & Machine Learning Engine**:
   - **Primary Model**: **Gemma 4** accessed through the official Google Gemini API via the `google-genai` SDK.
   - **Default Model Identifier**: `gemma-4-26b-a4b-it` (configurable via `GEMINI_MODEL`, fallback `gemma-4-31b-it`).
   - **Semantic Embeddings / Retrieval**: BGE-M3 when feasible for semantic voucher candidate selection.
   - **Classical Baselines & Calibration**: scikit-learn (Majority class, TF-IDF + linear classifier, probability calibration, Macro-F1).
   - **Knowledge Base**: 27 authoritative voucher definitions, positive/negative signals, and confusion pairs.
4. **27 Authoritative Voucher Categories**:
   1. Purchase
   2. Sales
   3. Purchase Return / Debit Note
   4. Sales Return / Credit Note
   5. Payment
   6. Receipt
   7. Contra
   8. Journal
   9. Salary / Payroll
   10. Attendance
   11. Purchase Order
   12. Sales Order
   13. Receipt Note
   14. Delivery Note
   15. Rejection In
   16. Rejection Out
   17. Stock Journal
   18. Physical Stock
   19. Material In
   20. Material Out
   21. Job Work In Order
   22. Job Work Out Order
   23. Import
   24. Export
   25. Expense
   26. Advance / Prepayment
   27. Other / Miscellaneous

---

## 5. Security & Credential Policy

- Never commit `.env` or any secret keys.
- Environment variables configured via `.env.example`:
  ```bash
  GEMINI_API_KEY=
  GEMINI_MODEL=gemma-4-26b-a4b-it
  ```
- Before the user supplies the real `GEMINI_API_KEY`:
  - Provide a deterministic mock adapter for testing plumbing and schemas.
  - The UI and API must explicitly declare mock mode and must never present mock predictions as real AI inference.
  - Fail with a descriptive configuration error if real inference is attempted without an API key.

---

## 6. Implementation Sequence & Phase Gates

- **Phase 0 — Repository Audit**: Inspect repo, audit environment, document architecture, verify Git remote, establish `PROJECT_STATE.md`. [CURRENT]
- **Phase 1 — Project Foundation**: Scaffold Next.js frontend and FastAPI backend, configuration management, health endpoints, test runners.
- **Phase 2 — Visual Foundation**: Implement reference design system, design tokens, hero glass visual, responsive layout, accessible UI components.
- **Phase 3 — Data Ingestion**: Robust XLSX/CSV parser, alias mapping, null/date/currency handling, row ID preservation, schema validation.
- **Phase 4 — Baseline Classifier**: Majority class, TF-IDF + classifier, reproducible evaluation metrics (Accuracy, Macro-F1, confusion matrix).
- **Phase 5 — Gemma 4 Integration**: `google-genai` provider adapter, prompt templates, Pydantic output validation, deterministic mock adapter, smoke tests.
- **Phase 6 — Accounting Signals & Semantic Retrieval**: Derivation of money-flow, role semantics, 27 voucher cards, candidate retrieval.
- **Phase 7 — Confidence & Guardrails**: Reliability scoring, contradiction detection, review flag, second-pass reasoning pipeline.
- **Phase 8 — Backend API**: REST endpoints for upload, validation, preview, classification jobs, status polling, pagination, and export.
- **Phase 9 — Connected Dashboard**: End-to-end integration connecting frontend dashboard to backend API, filtering, review queue, and analytics.
- **Phase 10 — Robustness & Evaluation**: Extensive test suite covering malformed inputs, error taxonomy, regression fixtures, leakage audits.
- **Phase 11 — Release & Deployment**: Production builds, Docker/Compose setup, comprehensive documentation, clean checkout validation.

---

## 7. Known Blockers & Considerations

1. **Gemini API Key**: `GEMINI_API_KEY` is pending user provision. Handled via mock adapter in early phases; live inference phase gate will require real key.
2. **Windows PowerShell Execution Policy**: Script execution (`npm.ps1`) is restricted by system policy. Solved by invoking `npm.cmd` and `npx.cmd`.
3. **Python Version**: Python 3.14 default runtime; recommended to pin virtual environments to Python 3.13 or 3.11 for wheel binary compatibility.

---

## 8. Reference Judging Dataset Integration & Schema Generalization

- **Reference Workbook**: `Voucher_Classification_Test_Cases_v2.xlsx` (120 rows × 169 columns, sheet `'Test Cases'`).
- **Data Security**: Added to `.gitignore` to prevent committing raw judging data; local untracked development fixture.
- **Schema Structure**: Wide union schema with 14 functional field families (Purchase Orders, GRN, Delivery Notes, Sales Orders, Invoices, Returns, Payments/Receipts, Contra, Journal, Payroll, Job Work, Foreign Trade, Inventory/Stock, Expense).
- **Category Coverage**:
  - 24 categories present with balanced support (5 rows each = 120 total).
  - 3 categories absent (`Advance / Prepayment`, `Attendance`, `Other / Miscellaneous`).
  - Authoritative 27 taxonomy preserved in `AUTHORITATIVE_VOUCHER_LABELS`; missing categories supported via isolated synthetic regression fixtures (`is_synthetic: True`).
- **Target Leakage Firewall**:
  - `Voucher Category` column discovered and partitioned strictly into `CanonicalTransaction.ground_truth_label`.
  - Stripped from feature mapping, canonical fields, `custom_populated_fields`, and `compact_representation()`.
  - Zero leakage verified across all 120 rows via `test_strict_zero_target_leakage_audit`.
- **Wide Schema Normalization**:
  - Dynamic extraction of populated non-null fields (~9 to 14 fields per transaction) reduces prompt token overhead by ~88% compared to sparse 169-column representation.
- **Cross-Validation Benchmark (TF-IDF + Logistic Regression)**:
  - Stratified 5-Fold Cross-Validation Accuracy: **98.33%** (118/120 correct).
  - Macro-F1: **98.26%**, Weighted-F1: **98.26%**.
  - Confusion analysis: 2 confusions between `Purchase` and `Sales` due to 12 shared columns, emphasizing the importance of role and reference semantics (`PO Ref` vs `Delivery Ref`).
- **Test Suite**: 30 passing tests (12 ingestion, 7 baseline/leakage, 3 health, 8 reference workbook).

---

## 9. Phase 5 — Gemma 4 Integration Summary

- **Designated AI Model**: Gemma 4 (`gemma-4-26b-a4b-it`) accessed through the official `google-genai` SDK (`google-genai==2.29.0`).
- **Pydantic Response Validation**:
  - `GemmaVoucherPrediction`: Strictly validates that category matches one of the 27 authoritative labels. Normalizes case/spacing variations and bounds confidence scores [0.0, 1.0].
  - `GemmaClassificationResult`: Captures row ID, model identifier, latency in ms, token usage metrics, and audit flags.
- **Auditable Mock Adapter**:
  - `MockGemmaAdapter` provides deterministic rule-and-semantic classification for offline development and CI before user supplies `GEMINI_API_KEY`.
  - Truthfulness guarantee: Explicitly records `is_mock=True` and `model_name="mock-gemma-4-adapter"`. Never misrepresents mock predictions as live inference.
- **Client & Fallback Resilience**:
  - `GemmaClassifier` dynamically activates live Gemini generation when `GEMINI_API_KEY` is present.
  - Automatically activates mock mode when API key is absent or when `use_mock_llm=True`.
  - Strict leakage check: Prompts use `compact_representation()` and never inject `Voucher Category` or ground truth into the prompt.
- **Test Suite Expansion**:
  - Added `backend/tests/test_gemma.py` (11 unit/integration tests).
  - Full test suite now passes: **41 passed, 0 failed** across ingestion, baselines, reference workbook, and Gemma 4 modules.

---

## 10. Phase 6 — Accounting Signals & Semantic Retrieval Summary

- **Objective**: Implement financial domain intelligence to derive money-flow direction, entity roles, statutory indicators, and candidate retrieval from 27 authoritative voucher knowledge cards with zero target-label leakage.
- **Accounting Signals Engine (`backend/app/ml/signals/engine.py`)**:
  - `MoneyFlowDirection`: Categorizes transactions into `INFLOW`, `OUTFLOW`, `INTERNAL`, `ADJUSTMENT`, `NON_FINANCIAL_MOVEMENT`, `ORDER_COMMITMENT`, `ATTENDANCE_LOG`, or `UNKNOWN`.
  - Hierarchical signal detection resolves logistical movement (Delivery Notes, GRN, Rejection Notes, Stock Recounts/Adjustments) before monetary fallbacks.
  - Entity role classification detects `VENDOR_SUPPLIER`, `CUSTOMER_BUYER`, `EMPLOYEE`, `INTERNAL_ACCOUNT`, `CONTRACTOR_JOBWORKER`, `OVERSEAS_COUNTERPARTY`, `TAX_AUTHORITY`.
  - Tax applicability and return indicator detection (negative quantities, units returned, debit/credit notes).
- **27 Voucher Knowledge Cards (`backend/app/ml/signals/voucher_cards.py`)**:
  - Full accounting profiles across all 27 categories detailing expected flow, typical debit/credit ledgers, primary identifiers/prefixes, key signals, negative signals, confusion pairs, and disambiguation rules.
- **Semantic Candidate Retriever (`backend/app/ml/signals/retriever.py`)**:
  - Multi-signal ranking algorithm combining TF-IDF similarity across card knowledge, ERP document prefix resolution (`ERP_PREFIX_MAP`), money flow compatibility, return/trade disambiguation, and negative signal penalties.
  - Generates zero-leakage prompt context injection (`get_candidate_context`) for the Gemma classifier.
  - **Empirical Validation**: **100% Top-5 candidate recall (0 misses out of 120)** across all reference workbook transactions.
- **Test Suite Expansion (`backend/tests/test_signals.py`)**:
  - 12 new unit and integration tests covering signal extraction, money-flow derivation, card integrity, disambiguation rules, prompt context formatting, and reference workbook cases.
  - Full repository test suite: **53 passed, 0 failed** (100% green).
  - Frontend production build (`npm run build`): Clean compilation in Next.js 16.4.0.

---

## 11. Phase 7 — Confidence Scoring & Guardrails Pipeline Summary

- **Objective**: Implement enterprise reliability scoring, structural accounting contradiction detection, review queue triage routing, and second-pass arbitration for ambiguous/borderline predictions.
- **Accounting Contradiction Detector (`backend/app/ml/guardrails/detector.py`)**:
  - Implements 9 domain integrity rules covering:
    - Contra external counterparty conflicts (`CONTRA_EXTERNAL_COUNTERPARTY` - CRITICAL)
    - Contra statutory sales/purchase tax billing (`CONTRA_STATUTORY_TAX` - CRITICAL)
    - Contra missing internal account pairs (`CONTRA_MISSING_INTERNAL_PAIR` - WARNING)
    - Sales outward procurement flow inversion (`SALES_OUTWARD_DISBURSEMENT` - CRITICAL)
    - Purchase inward customer collection inversion (`PURCHASE_INWARD_COLLECTION` - CRITICAL)
    - Zero/missing monetary totals on physical commercial invoices (`ZERO_AMOUNT_COMMERCIAL_INVOICE` - WARNING)
    - Return vouchers without negative quantity or reversal references (`RETURN_WITHOUT_RETURN_SIGNALS` - WARNING)
    - Internal treasury pairs classified as external payments (`INTERNAL_ACCOUNT_AS_PAYMENT` - WARNING)
    - Cross-border vouchers lacking international trade indicators (`CROSSBORDER_WITHOUT_FOREIGN_INDICATORS` - WARNING)
- **Confidence Calibration Scorer (`backend/app/ml/guardrails/scorer.py`)**:
  - Synthesizes model confidence (50%), rank-normalized candidate retriever affinity (30%), and signal compatibility (20%).
  - Deducts weighted penalties for detected contradictions (-0.35 per critical, -0.12 per warning, -0.04 per info).
  - Classifies into tiers: `HIGH` (>= 0.85), `MEDIUM` (0.65 - 0.84), `LOW` (< 0.65).
  - Determines operational routing: `AUTO_VERIFIED`, `FLAGGED_FOR_REVIEW`, or `CRITICAL_REJECTION`.
- **Second-Pass Reasoning Engine (`backend/app/ml/guardrails/second_pass.py`)**:
  - Automatically arbitrates borderline classifications, warning contradictions, or close candidate margins.
  - Re-routes contradicted vouchers to valid accounting counterparts (e.g., Contra with vendor counterparty re-routed to Payment).
  - Employs disambiguation rules from authoritative voucher cards.
- **Unified Pipeline Orchestrator (`backend/app/ml/guardrails/pipeline.py`)**:
  - `GuardrailsPipeline.evaluate_and_classify` unifies signal extraction, retrieval, model classification, contradiction detection, confidence scoring, and second-pass reasoning into a single audit-grade call.
- **Test Suite Expansion (`backend/tests/test_guardrails.py`)**:
  - 13 new unit and integration tests covering all contradiction archetypes, scoring math, triage routing, second-pass arbitration, and reference workbook cases.
  - Full repository test suite: **66 passed, 0 failed (100% green)**.
  - Frontend production build (`npm run build`): Verified clean Next.js 16.4.0 compilation.

---

## 12. Phase 8 — Backend REST API Summary

- **Objective**: Expose production-grade FastAPI REST endpoints covering dataset upload, tabular schema discovery, real-time and background batch classification, multi-dimensional review triage queries, human auditor overrides, analytics rollups, and audit-grade XLSX/CSV export.
- **REST Architecture & Route Modularization (`backend/app/api/`)**:
  - `Dataset Ingestion & Schema Discovery` (`POST /api/v1/datasets/upload`, `GET /api/v1/datasets`, `GET /api/v1/datasets/{id}/preview`):
    - Supports `.xlsx`, `.xls`, `.csv` streaming upload with multipart parsing (`python-multipart`).
    - Discovers detected headers, mapped canonical fields, unmapped columns, and schema warnings.
    - Provides paginated raw row inspection for frontend verification.
  - `Classification Engine` (`POST /api/v1/classify/single`, `POST /api/v1/classify/batch`, `GET /api/v1/classify/batch/{id}/status`):
    - Single transaction on-demand inference with complete guardrail evaluation (signals + retrieval + Gemma 4 + contradictions + calibration).
    - Asynchronous batch execution via FastAPI `BackgroundTasks` with real-time status and percentage progress tracking.
  - `Predictions & Review Queue Triage` (`GET /api/v1/datasets/{id}/predictions`, `GET /api/v1/datasets/{id}/predictions/{row_id}`):
    - Paginated query interface with filtering by triage decision (`AUTO_VERIFIED`, `FLAGGED_FOR_REVIEW`, `CRITICAL_REJECTION`), confidence tier (`HIGH`, `MEDIUM`, `LOW`), predicted category, and free-text search across counterparties and doc numbers.
  - `Authoritative Human Reviewer Override` (`POST /api/v1/datasets/{id}/predictions/{row_id}/override`):
    - Validates target category against the 27 authoritative voucher labels.
    - Records auditor identity, reason, previous category, and timestamp.
    - Promotes triage status to `AUTO_VERIFIED` with high confidence and persistent audit notes.
  - `Analytics & Distribution Intelligence` (`GET /api/v1/datasets/{id}/analytics`):
    - Aggregate metrics: total transactions, processed rows, auto-verified / review / rejection percentages, mean confidence, category frequency distribution, confidence tier counts, and contradiction breakdown.
  - `Audited Export Streaming` (`GET /api/v1/datasets/{id}/export?format=xlsx|csv`):
    - Exports all raw transaction columns augmented with `VYOM_PREDICTED_CATEGORY`, `VYOM_CONFIDENCE_SCORE`, `VYOM_CONFIDENCE_TIER`, `VYOM_TRIAGE_DECISION`, `VYOM_CONTRADICTIONS_DETECTED`, `VYOM_IS_OVERRIDDEN`, `VYOM_OVERRIDDEN_CATEGORY`, and `VYOM_REASONING`.
  - `Taxonomy & Knowledge Cards` (`GET /api/v1/taxonomy`, `GET /api/v1/taxonomy/{card_id}`):
    - Full inspection of the 27 accounting voucher profiles with typical debit/credit ledgers, flow patterns, prefixes, and disambiguation rules.
- **Thread-Safe In-Memory State Store (`backend/app/api/storage.py`)**:
  - `DatasetStorage` handles thread-safe concurrent access across uploads, background workers, queries, and reviewer overrides with UTC timestamping.
- **Integration Test Suite (`backend/tests/test_api.py`)**:
  - 9 comprehensive integration tests exercising all routes (upload, preview, single classify, batch classify, status, predictions query, human override, analytics rollup, export streaming, taxonomy cards).
  - Full repository test suite: **75 passed, 0 failed (100% green)**.
  - Frontend production build (`npm run build`): Verified clean Next.js 16.4.0 compilation.

---

## 13. Phase 9 — Connected Dashboard & Interactive Review Interface Summary

- **Objective**: Connect the Next.js 16 dark crystal frontend to live `/api/v1` backend endpoints, delivering an end-to-end audit workspace covering dataset ingestion, real-time & batch inference, analytics distributions, triage queues, deep voucher inspection, and authoritative human overrides.
- **Frontend Architecture & Components Implemented (`frontend/src/`)**:
  - `Typed API Client Layer (`frontend/src/lib/api.ts`)`:
    - Full TypeScript interface definitions matching backend Pydantic models.
    - Robust API callers for dataset uploads, previews, single and batch classification, status polling, predictions queries, human overrides, analytics, export downloads, and taxonomy cards.
  - `Ingestion & Schema Discovery Studio (`frontend/src/components/dashboard/UploadStudio.tsx`)`:
    - Drag-and-drop & file picker supporting `.xlsx` and `.csv` workbooks.
    - Schema mapping intelligence displaying detected columns, mapped canonical fields, unmapped columns, and zero-leakage schema warnings.
    - Paginated raw tabular inspection modal for verifying raw rows prior to classification.
  - `Dual-Engine Classification Controls (`frontend/src/components/dashboard/ClassificationControls.tsx`)`:
    - One-click batch classification trigger.
    - Toggle between deterministic offline Mock Adapter (`is_mock=True` zero-leakage verified) and live Gemma 4 inference.
    - Animated progress bar with live polling (800ms) of job status (`PROCESSING`, `COMPLETED`, `FAILED`).
  - `Analytics & Distribution Dashboard (`frontend/src/components/dashboard/AnalyticsOverview.tsx`)`:
    - 5 executive KPI cards: Total Transactions, Auto-Verified Rate % (emerald glow), Review Queue % (amber indicator), Critical Rejection % (crimson indicator), Mean Calibrated Confidence.
    - Dynamic horizontal frequency distribution bars across active classes from the 27-voucher taxonomy.
    - Confidence tier breakdown (`HIGH` >= 85%, `MEDIUM` 65-84%, `LOW` < 65%).
    - Accounting contradiction violation breakdown by rule name and severity.
  - `Multi-Dimensional Review Queue Table (`frontend/src/components/dashboard/ReviewQueueTable.tsx`)`:
    - Triage tabs: `ALL`, `AUTO_VERIFIED`, `FLAGGED_FOR_REVIEW`, `CRITICAL_REJECTION`.
    - Real-time multi-dimensional filters: Confidence tier, 27-voucher category dropdown, and free-text search (document #, counterparties, narration).
    - Table columns: Row #, Document # & date, Counterparty, Total Amount, Predicted Category (with `OVERRIDDEN` pill if modified), Calibrated Confidence with tier meter, Triage badge, Contradictions violation pill, Actions (`Inspect` & `Override`).
    - Pagination controls with page size selector (10, 15, 25, 50).
  - `Deep Voucher Inspection Drawer (`frontend/src/components/dashboard/VoucherDetailModal.tsx`)`:
    - 4-quadrant accounting signals panel (Money Flow direction & type, Entity Roles, Tax & Returns, Cross-border trade indicators).
    - Semantic candidate retriever top-5 breakdown with affinity scores.
    - Gemma 4 deep reasoning chain-of-thought text.
    - Detected contradiction alerts with rule name, severity, description, and suggested action.
    - Auditor override audit history.
  - `Authoritative Human Auditor Override Modal (`frontend/src/components/dashboard/HumanOverrideModal.tsx`)`:
    - Category reclassification selector across all 27 authoritative labels.
    - Mandatory audit justification reasoning and Reviewer ID input.
    - Submits to `POST /api/v1/datasets/{id}/predictions/{row_id}/override`.
    - Promotes triage decision to `AUTO_VERIFIED`, marks high confidence, records audit notes, and updates local state & analytics in real time.
  - `Real-Time AI Sandbox (`frontend/src/components/dashboard/SingleTestSandbox.tsx`)`:
    - On-demand single transaction classifier with 5 preset templates (Purchase Invoice, Bank Contra Transfer, Sales Return Credit Note, Procurement Purchase Order, Contradiction Test).
    - Real-time classification execution displaying latency, predicted category, confidence, triage, signals, and reasoning.
  - `Streaming Audited Export (`frontend/src/components/dashboard/ExportToolbar.tsx`)`:
    - Direct browser download for `.xlsx` and `.csv` formats appending 8 `VYOM_*` audit trail headers.
  - `Taxonomy & Knowledge Card Explorer (`frontend/src/components/dashboard/TaxonomyModal.tsx`)`:
    - Searchable directory of the 27 authoritative voucher profiles with typical debit/credit ledgers and disambiguation rules.
  - `Master Workspace Container (`frontend/src/components/dashboard/WorkspaceView.tsx`)`:
    - Seamlessly mounted into `frontend/src/app/page.tsx` with smooth navigation from the fixed luxury header and hero section.
- **Verification & Builds**:
  - Frontend production build (`npm run build`): Next.js 16.4.0 (Turbopack) compiled cleanly in 2.2s with zero TypeScript / React errors.
  - Full backend test suite (`pytest -v`): **75 passed, 0 failed (100% green)**.

---

## 14. Next Permitted Action

Upon user authorization of the Phase 9 report:
Proceed to **Phase 10 — Robustness, Edge Cases, Stress Testing & Model Evaluation**.






