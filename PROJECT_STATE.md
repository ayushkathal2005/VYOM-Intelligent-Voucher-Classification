# VYOM+ — Project State & Phase Gate Tracking

> **Authoritative Phase-Gated Tracking Document**
> Last Updated: 2026-10-10
> Current Authorized Phase: **Phase 3 — Data Ingestion**
> Status: **COMPLETE** (Awaiting user review at Phase 3 Gate)

---

## 1. Executive Status & Phase Progress

| Phase | Name | Status | Commit | Remote Push | Gate Approval |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 0 | Repository Audit | COMPLETE | `8a2dc3c` | Verified (`origin/main`) | Approved |
| 1 | Project Foundation | COMPLETE | `0d12553` | Verified (`origin/main`) | Approved |
| 2 | Visual Foundation | COMPLETE | `f7e8692` | Verified (`origin/main`) | Approved |
| **3** | **Data Ingestion** | **COMPLETE** | `e7e1dac` | Verified (`origin/main`) | **Current Phase Gate** |
| 4 | Baseline Classifier | PENDING | — | — | Not Authorized |
| 5 | Gemma 4 Integration | PENDING | — | — | Not Authorized |
| 6 | Accounting Signals & Semantic Retrieval | PENDING | — | — | Not Authorized |
| 7 | Confidence & Guardrails | PENDING | — | — | Not Authorized |
| 8 | Backend API | PENDING | — | — | Not Authorized |
| 9 | Connected Dashboard | PENDING | — | — | Not Authorized |
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

## 8. Next Permitted Action

Upon user review and authorization of the Phase 3 report:
Proceed to **Phase 4 — Baseline Classifier**.
