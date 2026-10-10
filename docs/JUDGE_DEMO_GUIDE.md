# VYOM+ — Live Judge Demonstration & Product Walkthrough Guide

> **Authoritative Presenter Playbook for Hackathon Judges & Technical Evaluators**  
> **System**: VYOM+ Intelligent Voucher Classification Engine  
> **Version**: 1.0 Production-Ready Qualifier Release  
> **Primary Stack**: Next.js 16 (React 19 / Turbopack / Three.js R3F) + Python FastAPI + Calibrated Linear SVM + Gemma 4 (Gemini API)

---

## Table of Contents

1. [A. Two-Minute Executive Pitch & Problem Statement](#a-two-minute-executive-pitch--problem-statement)
2. [B. Chronological Click-by-Click Demonstration Script](#b-chronological-click-by-click-demonstration-script)
3. [C. Technical Architecture & End-to-End Data Flow](#c-technical-architecture--end-to-end-data-flow)
4. [D. Feature Inventory & Implementation Audit](#d-feature-inventory--implementation-audit)
5. [E. KPI & Metrics Dictionary](#e-kpi--metrics-dictionary)
6. [F. The 27 Authoritative Voucher Categories & Confusion Matrix](#f-the-27-authoritative-voucher-categories--confusion-matrix)
7. [G. Model Benchmarks & Evaluation Methodology](#g-model-benchmarks--evaluation-methodology)
8. [H. Judge Q&A Defense (18 Technical & Business Questions)](#h-judge-qa-defense-18-technical--business-questions)
9. [I. Live Demo Recovery Checklist & Fallbacks](#i-live-demo-recovery-checklist--fallbacks)
10. [J. Final Closing Statement](#j-final-closing-statement)

---

## A. Two-Minute Executive Pitch & Problem Statement

### 25-Second Spoken Opening Statement
> *"Judges, manual accounting voucher classification is one of the highest-friction, error-prone bottlenecks in financial enterprise software. Raw transaction descriptions like 'Apex Steel Invoice 881' or 'HDFC ATM 0041' are ambiguous without accounting context.  
> **VYOM+** solves this by unifying high-throughput local machine learning, semantic retrieval across all 27 authoritative voucher classes, and a deterministic accounting guardrails engine. It achieves **97.99% multi-class accuracy** at over **3,800 transactions per second**, while catching structural accounting contradictions before they ever hit the general ledger."*

### The Core Problem
1. **The Context Gap**: A standard LLM or regex looking only at a transaction description cannot tell whether an invoice is a forward procurement or a credit reversal, or whether an internal transfer has been illegally assessed with GST.
2. **Ambiguous Accounting Signal Overlap**:
   - *Purchase Order* (contractual commitment) vs. *Purchase* (recognized commercial liability).
   - *Contra* (internal liquidity repositioning) vs. *Payment/Receipt* (third-party settlement).
   - *Attendance* (operational labor log) vs. *Payroll* (monetary compensation disbursement).
3. **The Production Requirement**: Real ERPs process tens of thousands of rows. An architecture relying 100% on external LLM API calls introduces prohibitive latency ($0.50+/batch and seconds per row). VYOM+ introduces a **Tri-Mode Architecture**:
   - **Fast Mode**: Calibrated Word+Char SVM with <0.3ms latency per row.
   - **AI Mode**: Deep reasoning using Gemma 4 via the official Google Gemini API.
   - **Hybrid Mode**: High-speed triage that automatically escalates only low-confidence or non-auto-verified transactions to Gemma 4.

---

## B. Chronological Click-by-Click Demonstration Script

Follow this step-by-step sequence during the live presentation.

```
[ Homepage: 3D Coin ] ➔ [ Upload Studio ] ➔ [ Classify Controls ] ➔ [ Results Inspection ] ➔ [ Review Queue & Override ] ➔ [ Analytics Dashboard ] ➔ [ Audited Export ]
```

| Step # | Screen / Route | Action | What Judges See | Spoken Script ("What to Say") | Behind the Scenes | Duration | Fallback |
| :---: | :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **1** | Homepage (`/`) | Open `http://localhost:3001/` | Dark finance aesthetic (`#050505`), gleaming 3D Gold Coin rotating in hero, headline fades in smoothly. | *"Welcome to VYOM+. Notice our 3D gold coin visual, physically rendered with full PBR maps. It represents financial transaction intelligence across all 27 authoritative voucher classes."* | WebGL Canvas loads `Gold.glb`, PBR material with normal/roughness/metallic maps, frame loop executes cubic intro spin, continuous idle loop. | 15s | Static fallback container renders automatically if WebGL disabled. |
| **2** | Homepage (`/`) | Hover pointer over 3D Coin | Coin rotation accelerates smoothly; tilts slightly following pointer coordinates. | *"The interface is responsive and tactile. As we hover, the coin accelerates and tilts, demonstrating real-time interactive 3D in the modern financial web."* | Pointer event listener normalizes coordinates to `[-1, 1]`, `MathUtils.lerp` interpolates rotation speed from 0.65 to 2.4 rad/s and clamps tilt to `[-0.3, 0.3]` rad. | 10s | Continue to Step 3. |
| **3** | Navigation | Click **"Upload"** in top navbar | Navigates to `/upload`. Upload Studio dropzone appears with supported formats (`.XLSX`, `.CSV`, `AUTO-SCHEMA`). | *"We start in the Upload Studio. VYOM+ supports multi-format ERP workbooks with automatic schema discovery and strict zero-leakage protection."* | Next.js App Router navigates without full page reload. | 5s | Direct URL `http://localhost:3001/upload`. |
| **4** | Upload Studio (`/upload`) | Click **"Load Curated Demo Dataset (25 Vouchers)"** (or drag `demo_voucher_sample.xlsx`) | Parsing spinner displays briefly, followed by the **Schema Discovery Card** showing 25 rows, 169 detected columns, and canonical field mappings. | *"With one click, we load a curated 25-voucher dataset representing all key accounting scenarios. Notice that VYOM+ detected 169 ERP columns and mapped them to canonical fields, while isolating target labels so the model never cheats."* | `POST /api/datasets/upload` parses workbook via `openpyxl`, cleans whitespace/nulls, sanitizes numeric values, creates `CanonicalTransaction` instances, stores raw rows in in-memory session storage. | 10s | Drag and drop `demo_voucher_sample.xlsx` from file explorer. |
| **5** | Upload Studio (`/upload`) | Click **"Inspect Raw Rows (25)"** | Modal opens displaying paginated table of raw ingested records with canonical field tags. | *"Here auditors can inspect the original raw records before classification begins. Unmapped custom columns are preserved safely for downstream export."* | `GET /api/datasets/{id}/preview?page=1&page_size=10` streams paginated records. | 10s | Close modal by clicking outside or 'Done'. |
| **6** | Navigation | Click **"Continue to Classify →"** | Navigates to `/classify`. Mode selection cards appear: **Fast Mode**, **AI Mode**, and **Hybrid Mode**. | *"Now we configure inference. VYOM+ offers three distinct modes: Fast Mode uses our locally trained calibrated Linear SVM running in sub-millisecond time. AI Mode utilizes Gemma 4 for deep reasoning. Hybrid Mode combines both."* | `WorkspaceContext` maintains `activeDataset` across route boundaries. | 10s | Click "Classify" in top navbar. |
| **7** | Classify (`/classify`) | Select **"Fast Mode"** and click **"Run Classification Job"** | Live progress bar fills smoothly from 0% to 100%. Job completes in under 1 second. Notification displays *"Job Completed Successfully"*. | *"Watch the speed. In Fast Mode, 25 complex accounting transactions are parsed, normalized, feature-engineered, and classified in under one second—delivering over 3,800 rows per second throughput."* | `POST /api/classify/batch` starts asynchronous background task. Worker iterates through transactions, applies `FastVoucherClassifier`, runs `AccountingContradictionDetector`, computes calibrated confidence, and saves predictions. | 10s | If error, toggle `Mock Adapter` and retry. |
| **8** | Classify (`/classify`) | (Optional Demo of Job Controls) | If classifying a large workbook, demonstrate **Pause**, **Resume**, and **Cancel** buttons. | *"For enterprise workloads, VYOM+ supports cooperative pause, resume, and cancellation at transaction boundaries, ensuring partial progress is never lost."* | Background worker checks `check_job_control(job_id)` at every row boundary. Cancel persists completed rows to session storage. | 10s | Skip if using 25-row demo. |
| **9** | Navigation | Click **"Continue to Results →"** | Navigates to `/results`. Full table of classified vouchers appears with Predicted Category, Calibrated Confidence, Confidence Tier badge, Triage Decision badge, and Action buttons. | *"Here are the classified vouchers. Every prediction is assigned an authoritative category, a calibrated confidence score, and a triage routing decision: Auto-Verified, Flagged for Review, or Critical Rejection."* | `GET /api/datasets/{id}/predictions?page=1&page_size=20` returns sorted, paginated records. | 15s | Click "Results" in top navbar. |
| **10** | Results (`/results`) | Click **"Inspect Audit Trace"** on **Row 1** (Purchase Order) | Detail modal opens showing: Document No `PO-2026-881`, Category `Purchase Order`, Confidence `97.3%`, Top-5 Candidates, Derived Signals, and Audit Notes. | *"Let's inspect Row 1. The model correctly classified this as a Purchase Order—not a Purchase invoice—because our signal engine detected forward procurement order commitment, promised delivery dates, and quotation terms."* | Modal displays `CandidateRetriever` top-5 rankings, `AccountingSignalProfile` (`ORDER_COMMITMENT`), and step-by-step scoring breakdown notes. | 20s | Click row anywhere to open modal. |
| **11** | Results (`/results`) | Filter or scroll to **Row 8** (Contra Entry with Statutory Tax) | Row 8 displays **CRITICAL REJECTION** badge in red, Calibrated Confidence `59.6%`, and contradiction badge `CONTRA_STATUTORY_TAX`. Click **"Inspect Audit Trace"**. | *"Now look at Row 8. This is a critical feature: a human or rogue script entered an internal bank transfer as a Contra, but incorrectly included statutory GST. Our guardrails engine caught this immediately, issued a CRITICAL penalty of -0.35, and blocked it from automatic ledger posting!"* | `AccountingContradictionDetector` detected `gst > 0` on category `Contra`, appended `CONTRA_STATUTORY_TAX` with severity `CRITICAL`. `ConfidenceScorer` automatically routed transaction to `CRITICAL_REJECTION`. | 25s | Show contradiction list in modal. |
| **12** | Navigation | Click **"Review"** in top navbar | Navigates to `/review`. The Review Queue table shows only records needing human attention (Flagged for Review & Critical Rejections). | *"Any transaction that fails auto-verification lands in the Review Queue. Auditors don't waste time re-checking 100% of transactions; they focus exclusively on uncertain or contradictory items."* | `GET /api/datasets/{id}/predictions?triage_decision=FLAGGED_FOR_REVIEW` isolates pending review items. | 15s | Filter by triage in `/results`. |
| **13** | Review Queue (`/review`) | Click **"Override"** on **Row 25** (`MISC-TXN-2026-999`, Retainer adjustment) | Override modal opens. Select `Journal` from dropdown, enter reason *"Reclassifying retainer adjustment to Journal per GAAP"*, click **"Apply Authoritative Override"**. | *"Row 25 was ambiguous, predicted as Payment with low confidence. As a qualified auditor, I can select the correct category 'Journal', log my professional rationale, and apply the override. The system immediately records my reviewer ID and timestamp."* | `POST /api/datasets/{id}/predictions/25/override` validates category against 27 taxonomy, persists override record, and flags row as `OVERRIDDEN`. Original AI prediction is permanently preserved. | 20s | Show confirmation toast. |
| **14** | Navigation | Click **"Analytics"** in top navbar | Navigates to `/analytics`. Dashboard displays 4 primary KPI cards, Ground-Truth Benchmark Card (Actual Accuracy: **96.0%**, Macro-F1: **0.958**), Category Distribution Bar Chart, and Guardrail Contradiction Breakdown. | *"The Analytics dashboard provides complete visibility. Notice the Honest Benchmark card: because our demo workbook contains labeled test cases, VYOM+ calculates true multi-class accuracy and Macro-F1. Our auto-verified rate is 56%, review queue is 40%, and exactly 1 critical rejection was stopped."* | `GET /api/datasets/{id}/analytics` computes exact mutually exclusive counts and percentages: `count / total_transactions * 100`. | 25s | Click "Analytics" in navbar. |
| **15** | Navigation | Click **"Results"** → Click **"Export Audited XLSX"** | Browser downloads `demo_voucher_sample_vyom_classified.xlsx`. | *"Finally, auditors can export the fully audited workbook to Excel or CSV. Every original ERP column is preserved alongside dedicated VYOM_ audit columns: predicted category, calibrated score, guardrail violations, and human override logs."* | `GET /api/datasets/{id}/export?format=xlsx` generates streaming workbook via `openpyxl` with `VYOM_*` metadata headers. | 15s | Export CSV if Excel viewer not open. |
| **16** | Navigation | Click **"Sandbox"** (`/test`) | Navigates to interactive Single Transaction Classifier. | *"For ad-hoc queries, accountants can test individual transactions in real-time in our interactive sandbox."* | `POST /api/classify/single` runs on-demand pipeline. | 10s | Wrap presentation. |

---

## C. Technical Architecture & End-to-End Data Flow

The following Mermaid diagram documents the authoritative data flow implemented in the VYOM+ codebase:

```mermaid
flowchart TD
    subgraph Ingestion ["1. INGESTION & NORMALIZATION"]
        A[Uploaded Workbook .xlsx / .csv] --> B[Tabular Parser & Sanitize]
        B --> C[Schema Discovery & Alias Resolver]
        C --> D[Strict Zero-Leakage Isolation\nTarget labels stripped from model input]
        D --> E[CanonicalTransaction Record]
    end

    subgraph FeatureEngineering ["2. FEATURE & SIGNAL EXTRACTION"]
        E --> F[AccountingSignalsEngine\nMoney flow, entity roles, tax, negation]
        E --> G[Compact Representation Synthesizer\norder_ref, doc_no, date, items, amounts]
        E --> H[CandidateRetriever\n27 Voucher Cards Top-5 Ranking]
    end

    subgraph InferenceEngine ["3. MULTI-MODE INFERENCE"]
        G --> I{Inference Mode}
        I -->|Fast Mode| J[FastVoucherClassifier\nWord+Char-WB Calibrated Linear SVM\n0.26ms/row]
        I -->|AI Mode| K[GemmaClassifier\nGemma 4 via Gemini API\nJSON Schema Pydantic]
        I -->|Hybrid Mode| L[Fast Mode Triage]
        L -->|Conf >= 0.85 & Auto-Verified| J
        L -->|Conf < 0.85 or Flawed| K
    end

    subgraph Guardrails ["4. GUARDRAILS & CONFIDENCE SCORING"]
        J --> M[AccountingContradictionDetector\n9 Deterministic Domain Rules]
        K --> M
        M --> N[SecondPassResolver\nAutomatic correction of known inversions]
        N --> O[ConfidenceScorer]
        F --> O
        H --> O
        O --> P[Calibrated Reliability Score\n50% Model + 30% Retriever + 20% Signals - Penalties]
    end

    subgraph TriageRouting ["5. OPERATIONAL TRIAGE"]
        P --> Q{Triage Decision}
        Q -->|No Critical Contradictions & Conf >= 0.85| R[AUTO_VERIFIED\nStraight-through ledger posting]
        Q -->|0.65 <= Conf < 0.85 or Warning| S[FLAGGED_FOR_REVIEW\nQueued for human audit]
        Q -->|Critical Contradiction or Conf < 0.65| T[CRITICAL_REJECTION\nBlocked from posting]
    end

    subgraph HumanInTheLoop ["6. HUMAN-IN-THE-LOOP & EXPORT"]
        S --> U[Review Queue /review]
        T --> U
        U --> V[Auditor Human Override\nCategory, Reason, Reviewer ID]
        V --> W[Audited Session Storage]
        R --> W
        W --> X[Audited Excel / CSV Export]
        W --> Y[Analytics Dashboard & Honest Metrics]
    end
```

---

## D. Feature Inventory & Implementation Audit

| Feature | UI Location | User Action | Backend Endpoint / Function | Inputs | Outputs | Metrics Affected | Implementation Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **3D Gold Coin Hero** | `/` | Rotate, hover, tilt | Client Three.js / R3F Canvas | Pointer `(x, y)` | 3D mesh transforms, lighting lerp | N/A (Aesthetic / Branding) | **Fully Implemented** |
| **Workbook Upload** | `/upload` | Drag & drop or browse | `POST /api/datasets/upload` | File bytes (`.xlsx`, `.csv`) | `DatasetUploadResponse` | Total Rows, Columns Detected | **Fully Implemented** |
| **Curated Demo Loader** | `/upload` | 1-click button | `fetch('/demo_voucher_sample.xlsx')` | Static demo asset | Loaded dataset in state | Total Rows: 25 | **Fully Implemented** |
| **Schema Discovery & Preview** | `/upload` | Click "Inspect Raw Rows" | `GET /api/datasets/{id}/preview` | `dataset_id`, page | `PaginatedPreviewResponse` | Ingested column counts | **Fully Implemented** |
| **Fast Mode Classification** | `/classify` | Select Fast & Run | `POST /api/classify/batch` (`mode='fast'`) | `dataset_id`, mode | Batch Job ID, status | Processed Rows, Throughput | **Fully Implemented** |
| **AI Mode Classification** | `/classify` | Select AI & Run | `POST /api/classify/batch` (`mode='ai'`) | `dataset_id`, mode, mock flag | Batch Job ID, status | Latency, Processed Rows | **Fully Implemented** |
| **Hybrid Mode Classification** | `/classify` | Select Hybrid & Run | `POST /api/classify/batch` (`mode='hybrid'`) | `dataset_id`, mode | Batch Job ID, status | Escalated row count | **Fully Implemented** |
| **Batch Job Controls** | `/classify` | Pause, Resume, Cancel | `POST /api/classify/jobs/{id}/[pause\|resume\|cancel]` | `job_id` | `BatchClassifyJobResponse` | Job status, processed count | **Fully Implemented** |
| **Prediction Inspection** | `/results` | Filter by category, triage | `GET /api/datasets/{id}/predictions` | Query params (triage, tier, search) | `PaginatedPredictionsResponse` | Total records, filtered count | **Fully Implemented** |
| **Voucher Detail Audit Trace** | `/results` | Click "Inspect Audit Trace" | `GET /api/datasets/{id}/predictions/{row_id}` | `dataset_id`, `row_id` | `PredictionRecordResponse` | Individual confidence & penalties | **Fully Implemented** |
| **Contradiction Detection** | Backend / Modals | Evaluated on every row | `AccountingContradictionDetector` | Transaction + proposed category | `List[AccountingContradiction]` | Critical Rejection Count | **Fully Implemented** |
| **Review Queue** | `/review` | Filter pending review items | `GET /api/datasets/{id}/predictions?triage_decision=...` | `dataset_id` | Flagged transactions | Review Queue Percentage | **Fully Implemented** |
| **Human Auditor Override** | `/review` & `/results` | Select new class & reason | `POST /api/datasets/{id}/predictions/{row_id}/override` | `new_category`, `override_reason`, `reviewer_id` | `HumanOverrideResponse` | Overridden count, review count | **Fully Implemented** |
| **Analytics Dashboard** | `/analytics` | View charts & KPIs | `GET /api/datasets/{id}/analytics` | `dataset_id` | `AnalyticsResponse` | All 4 KPI cards & distributions | **Fully Implemented** |
| **Audited Export** | `/results` | Export XLSX / CSV | `GET /api/datasets/{id}/export?format=[xlsx\|csv]` | `dataset_id`, format | Audited binary stream | Exported row count | **Fully Implemented** |
| **Single Voucher Sandbox** | `/test` | Enter custom fields & classify | `POST /api/classify/single` | `SingleClassifyRequest` | `SingleClassifyResponse` | Ad-hoc latency | **Fully Implemented** |

---

## E. KPI & Metrics Dictionary

Every metric on the VYOM+ dashboard is computed deterministically from authoritative session records.

| Metric Name | Authoritative Formula | Denominator | Units | Interpretation & Meaning | Common Presentation Trap |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Transactions** | $N_{\text{total}} = \max(\text{Total Rows Ingested}, \text{Predictions Count})$ | None (Cardinality) | Integer (Rows) | Total number of transaction rows registered in the active dataset. | Not the number of unique companies or documents. |
| **Auto-Verified Rate** | $\frac{N_{\text{Auto-Verified}}}{N_{\text{total}}} \times 100\%$ | Total Transactions | Percentage (`%`) | Percentage of transactions eligible for straight-through posting ($0$ critical contradictions and confidence $\ge 0.85$). | **DO NOT confuse with accuracy.** High auto-verification means high system confidence, not guaranteed truth. |
| **Review Queue Rate** | $\frac{N_{\text{Flagged For Review}}}{N_{\text{total}}} \times 100\%$ | Total Transactions | Percentage (`%`) | Transactions requiring qualified human auditor inspection ($0.65 \le \text{Conf} < 0.85$ or non-critical warnings). | Displays `0%` if zero; displays `N/A` if dataset is empty. Never silently converts error to 0. |
| **Critical Rejections** | $\frac{N_{\text{Critical Rejection}}}{N_{\text{total}}} \times 100\%$ | Total Transactions | Percentage (`%`) | Transactions blocked from ledger posting due to severe accounting contradictions (e.g., Contra with GST). | These are domain violations, not HTTP errors or software crashes. |
| **Mean Calibrated Confidence** | $\frac{1}{N_{\text{processed}}} \sum_{i=1}^{N_{\text{processed}}} C_i$ | Processed Transactions | Normalized scalar ($0.0000 - 1.0000$) | Synthesized reliability score combining model confidence, candidate affinity, and signal compatibility minus penalties. | **Confidence is NOT accuracy.** A model can be confidently wrong if data is adversarial without guardrails. |
| **Actual Multi-Class Accuracy** | $\frac{\sum_{i=1}^{N} \mathbb{I}(y_i == \hat{y}_i)}{N} \times 100\%$ | Evaluated Labeled Rows ($N$) | Percentage (`%`) | Correct predictions divided by total labeled ground-truth records. Only displayed when ground truth is present. | **Never display an accuracy percentage when analyzing an unlabeled blind dataset.** VYOM+ displays `N/A (Unlabelled Dataset)`. |
| **Macro-F1 Score** | $\frac{1}{27} \sum_{c=1}^{27} \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$ | 27 Voucher Classes | Normalized scalar ($0.0000 - 1.0000$) | Unweighted arithmetic mean of F1 scores across all 27 categories, giving rare classes equal weight to frequent classes. | Ordinary accuracy can be misleading on imbalanced datasets; Macro-F1 measures true multi-class robustness. |
| **Inference Throughput** | $\frac{N_{\text{rows}}}{\Delta t_{\text{inference}}}$ | Elapsed Inference Time | Rows / Second | Number of complete voucher classifications executed per second of compute. | Does not include network file upload time. |
| **Per-Row Latency** | $\frac{\Delta t_{\text{inference}}}{N_{\text{rows}}} \times 1000$ | Total Rows Processed | Milliseconds (`ms`) | Average compute duration per transaction record. Fast mode is $\approx 0.26$ ms; AI mode is $\approx 150 - 400$ ms. | Fast mode is CPU-bound; AI mode is network I/O-bound. |

---

## F. The 27 Authoritative Voucher Categories & Confusion Matrix

VYOM+ strictly supports the 27 authoritative voucher classes defined in the challenge taxonomy.

### The 10 Critical Confusion Pairs & Disambiguation Rules

| Confusion Pair | Key Distinguishing Signal | Decisive Rules in VYOM+ |
| :--- | :--- | :--- |
| **Purchase** vs. **Purchase Order** | Order Commitment vs. Commercial Liability | `Purchase Order` has future promised delivery dates, order terms, and zero recognized tax liability. `Purchase` has tax invoice numbers, statutory GST, and payable ledgers. |
| **Sales** vs. **Sales Order** | Customer Order Quote vs. Recognized Revenue | `Sales Order` tracks unfulfilled quotes and order quantities. `Sales` records tax invoices, outward dispatch references, and taxable value. |
| **Payment** vs. **Expense** | Trade Vendor Settlement vs. Operational Overhead | `Payment` settles external supplier accounts payable against prior invoices. `Expense` covers internal operating costs (travel, rent, utilities, employee petty cash). |
| **Receipt** vs. **Sales** | Cash/Bank Collection vs. Commercial Invoice Billing | `Receipt` records incoming liquid funds into bank/cash accounts settling receivables. `Sales` generates the commercial tax invoice billing the customer. |
| **Contra** vs. **Payment / Receipt** | Internal Treasury vs. Third-Party Commercial Counterparty | `Contra` is strictly internal movement between company-owned bank accounts or cash vaults. If an external vendor or customer is named, or GST is charged, it **cannot** be Contra. |
| **Purchase Return** vs. **Sales Return** | Procurement Inversion vs. Revenue Inversion | `Purchase Return (Debit Note)` reverses vendor procurement (negative units to supplier). `Sales Return (Credit Note)` reverses customer billing (negative units from buyer). |
| **Delivery Note** vs. **Receipt Note** | Outward Dispatch vs. Inward Warehouse GRN | `Delivery Note` accompanies outward shipment to customer with transport challan. `Receipt Note (GRN)` records physical inward receipt and QC acceptance at warehouse. |
| **Material In** vs. **Material Out** | Jobwork Return vs. Jobwork Outward Dispatch | `Material In` logs return of processed goods from subcontractors. `Material Out` logs raw material issued to subcontractors under jobwork rules. |
| **Salary / Payroll** vs. **Attendance** | Monetary Disbursement vs. Operational Labor Hours | `Salary / Payroll` contains net pay, basic salary, PF, and tax deductions. `Attendance` is a non-monetary shift log (days worked, overtime hours, leaves). |
| **Advance / Prepayment** vs. **Expense** | Mobilization Deposit vs. Incurred Consumed Cost | `Advance / Prepayment` is an advance remittance against upcoming milestone orders. `Expense` is an incurred, consumed operational cost. |

---

## G. Model Benchmarks & Evaluation Methodology

### Verified Baseline Benchmark on `voucher_test_large.xlsx` (5,000 Transactions)
The benchmark was executed using **disjoint grouped stratified splitting** across all 27 categories with **zero duplicate or template leakage**:
- **Total Dataset Size**: 5,000 rows
- **Unique Group Templates**: 4,949 groups
- **Split Distribution**:
  - Training Set: 3,503 rows (70.1%)
  - Validation Set: 750 rows (15.0%)
  - Held-Out Test Set: 747 rows (14.9%)

### Model Comparison Results (Validation Set)

| Model Architecture | Features | Fit Time | Val Latency | Throughput | Val Accuracy | Val Macro-F1 | Weighted F1 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| 1. Baseline Logistic Regression | Word TF-IDF (1-2 ngrams) | 0.82 s | 0.035 ms | 28,207 rows/s | 98.53% | 0.9858 | 0.9853 |
| 2. Calibrated Linear SVM | Word TF-IDF (1-2 ngrams) | 0.61 s | 0.046 ms | 21,930 rows/s | 98.40% | 0.9845 | 0.9840 |
| 3. Logistic Regression | Word + Char-WB TF-IDF (3-5) | 2.78 s | 0.240 ms | 4,170 rows/s | 99.20% | 0.9917 | 0.9920 |
| **4. Calibrated Linear SVM (Selected)** | **Word + Char-WB TF-IDF (3-5)** | **2.66 s** | **0.246 ms** | **4,069 rows/s** | **99.20%** | **0.9925** | **0.9920** |
| 5. SGDClassifier (Log Loss) | Word + Char-WB TF-IDF (3-5) | 1.53 s | 0.239 ms | 4,189 rows/s | 99.20% | 0.9915 | 0.9919 |

### Final Held-Out Test Set Evaluation (Unseen Test Partition: N=747)
- **Held-Out Test Accuracy**: **97.99%**
- **Held-Out Test Macro-F1**: **0.9779**
- **Held-Out Test Weighted-F1**: **0.9798**
- **Production Throughput**: **3,834.6 rows/second** (0.261 ms per row)

### Performance Breakdown by Transaction Tier

| Difficulty Tier | Test Rows ($N$) | Tier Accuracy | Tier Macro-F1 | Key Characteristics |
| :--- | :---: | :---: | :---: | :--- |
| **Clean Tier** | 186 | **100.00%** | **1.0000** | Canonical headers, unambiguous amounts, standard entity names. |
| **Noisy Tier** | 293 | **100.00%** | **1.0000** | OCR character substitutions, irregular casing, messy document prefixes. |
| **Hard Tier** | 197 | **96.95%** | **0.9569** | Subcontracting vs procurement overlap, contra with complex bank narrations. |
| **Sparse Tier** | 71 | **87.32%** | **0.8369** | Single-field descriptions, missing vendor/customer names, unmapped columns. |

---

## H. Judge Q&A Defense (18 Technical & Business Questions)

### Q1: What makes VYOM+ different from just prompting Gemma 4 with a CSV row?
> **Answer**: Calling an LLM directly on raw CSV text is slow, expensive, and blind to accounting constraints. A raw prompt cannot process 50,000 rows in an enterprise ERP without massive API costs and rate limits. VYOM+ uses a **Tri-Mode Architecture**: a local calibrated model handles high-throughput classifications in 0.26 ms with 97.99% accuracy. Gemma 4 is used where it truly shines—deep reasoning over ambiguous edge cases. Furthermore, pure LLMs hallucinate; our **9 deterministic guardrails** guarantee that illegal accounting states (like Contra with GST) are stopped.

### Q2: How do you prevent data leakage during training and evaluation?
> **Answer**: We enforce strict leakage isolation at three levels:
> 1. In `CanonicalTransaction`, the target column is completely stripped before constructing the `compact_representation()` text.
> 2. Metadata columns like `family`, `tier`, and `primary_id` are never fed to the vectorizer.
> 3. Splitting uses **disjoint group stratification**: duplicate or template-derived transactions are grouped together so that no duplicate ever spans both the training and test sets.

### Q3: What happens if the Gemini API goes down or hits a rate limit?
> **Answer**: VYOM+ has a built-in automated fallback hierarchy. If the live Gemini API returns a 429 rate limit, 503 service unavailable, or connection timeout, the system catches the exception, engages our offline mock adapter or local classifier, logs an audit trace note (`"Row fallback applied: API unavailable"`), and ensures the batch job never crashes.

### Q4: How is the confidence score calculated? Is it just the model's softmax probability?
> **Answer**: No. Softmax outputs from neural networks or SVMs are notoriously uncalibrated. VYOM+ synthesizes confidence using an authoritative formula:
> $$\text{Base Score} = 0.50 \times P_{\text{model}} + 0.30 \times A_{\text{retriever}} + 0.20 \times S_{\text{signal}}$$
> Then, detected contradictions apply explicit accounting penalties: Critical penalties deduct $-0.35$, Warnings deduct $-0.12$. A transaction only achieves the High tier ($\ge 0.85$) if the model, retriever, and derived accounting signals all agree with zero structural contradictions.

### Q5: What are the 9 contradiction guardrails?
> **Answer**:
> 1. `CONTRA_STATUTORY_TAX`: Contra voucher assessing statutory GST or sales tax.
> 2. `CONTRA_EXTERNAL_COUNTERPARTY`: Contra naming third-party vendors or commercial customers.
> 3. `SALES_OUTWARD_DISBURSEMENT`: Sales voucher assigned to procurement outflow.
> 4. `PURCHASE_INWARD_COLLECTION`: Purchase voucher assigned to customer inward collection.
> 5. `ZERO_AMOUNT_COMMERCIAL_INVOICE`: Commercial invoice with $0$ billing amount but positive physical quantity.
> 6. `RETURN_WITHOUT_RETURN_SIGNALS`: Return category without reversal notes or negative quantities.
> 7. `INTERNAL_ACCOUNT_AS_PAYMENT`: Internal treasury transfer classified as external payment.
> 8. `CROSSBORDER_WITHOUT_FOREIGN_INDICATORS`: Import/Export category lacking customs or foreign country metadata.
> 9. `ATTENDANCE_WITH_MONETARY_PAYMENT`: Non-financial attendance log containing monetary wage disbursement.

### Q6: Can a human auditor override an AI prediction?
> **Answer**: Yes. In both the Review Queue and the Results view, an auditor can click **Override**, select any of the 27 authoritative categories, and enter their professional rationale. The system updates the triage status to `OVERRIDDEN`, records the auditor's ID and timestamp, and preserves the original AI prediction for audit trail compliance.

### Q7: Does the model automatically retrain when an auditor overrides a voucher?
> **Answer**: In our current prototype, overrides are stored in session audit logs and exported in the audit workbook. We intentionally do not perform automatic on-the-fly model retraining to prevent adversarial poisoning and maintain model audit stability. Batch retraining from validated override logs is our recommended production enhancement.

### Q8: What is the maximum tested dataset size?
> **Answer**: We have verified datasets up to 5,000 rows (`voucher_test_large.xlsx`). The ingestion parser enforces limits of 25 MB and 50,000 rows per workbook to prevent server memory exhaustion.

### Q9: Does VYOM+ store sensitive financial data on third-party servers?
> **Answer**: In Fast Mode, 100% of data processing occurs locally on the server; zero bytes leave your environment. In AI Mode, only the compact transaction representation is transmitted over TLS to the Gemini API under Google Cloud enterprise terms.

### Q10: How does VYOM+ handle unmapped or custom ERP columns?
> **Answer**: Our parser automatically discovers standard columns (e.g., invoice number, date, amount) via an extensive alias dictionary. Any unmapped custom columns (e.g., project code, branch ID, vehicle number) are preserved in `custom_populated_fields` and exported into the final audited workbook with zero loss.

### Q11: Why is Macro-F1 more important than Accuracy here?
> **Answer**: Financial datasets exhibit significant class imbalance—standard Purchases and Sales often outnumber Job Work or Physical Stock vouchers 10 to 1. Accuracy can appear deceptively high (e.g., 90%) even if rare categories are completely misclassified. Macro-F1 computes the unweighted average across all 27 categories, ensuring rare classes are evaluated with equal rigor.

### Q12: How do you handle multi-currency or international trade?
> **Answer**: Our signals engine parses currency codes (USD, EUR, GBP, INR), customs duties, Bill of Entry numbers, and CIF/FOB indicators, routing cross-border transactions specifically to `Import` or `Export` and preventing confusion with domestic procurement.

### Q13: What happens if a user uploads a malformed CSV with missing headers or corrupted encoding?
> **Answer**: Our ingestion engine uses multi-encoding detection (UTF-8, Latin-1, CP1252), delimiter sniffing (comma, semicolon, tab, pipe), and openpyxl row validation. Empty files or files without valid data rows return clear HTTP 422 errors explaining the issue without crashing.

### Q14: How does the system handle negative numbers in accounting formats?
> **Answer**: The parser supports accounting parentheses notation (e.g., `(1,250.00)` $\rightarrow -1250.0$), minus signs, and currency symbols (₹, $, €, £). Negative quantities automatically trigger return/reversal signal profiles.

### Q15: Why is the 3D coin visual in the hero instead of a standard dashboard image?
> **Answer**: The 3D gold coin reflects enterprise luxury financial design. Built with React Three Fiber, WebGL, and custom PBR shaders, it proves modern financial applications can be visually stunning, responsive, and performant without compromising core data science capabilities.

### Q16: How do job pause, resume, and cancel controls work under the hood?
> **Answer**: The backend batch runner executes inside a cooperative thread worker. At every row boundary, it queries `check_job_control(job_id)`. If paused, it suspends execution; if resumed, it picks up from `processed_rows`; if cancelled, it terminates cleanly and commits all previously classified rows to storage so partial work is never lost.

### Q17: Can this integrate with SAP, Tally, or Oracle ERP?
> **Answer**: Yes. The REST API exposes `POST /api/classify/single` and `POST /api/classify/batch` accepting JSON or standard ERP CSV exports. Our canonical transaction schema maps cleanly to standard SAP IDocs and Tally XML vouchers.

### Q18: What remains before this prototype can be deployed to production?
> **Answer**: Three key milestones:
> 1. Persistent relational database storage (PostgreSQL with SQLAlchemy) replacing in-memory session dictionaries.
> 2. Enterprise role-based access control (RBAC) and OAuth2 / SSO authentication.
> 3. Production task queuing (Celery with Redis) for concurrent multi-tenant batch workloads exceeding 100,000 rows.

---

## I. Demo Recovery Checklist & Fallbacks

| Scenario | Symptom | Immediate Fix Action | Fallback Explanation to Judges |
| :--- | :--- | :--- | :--- |
| **Network Disconnected** | Gemini API calls fail | Switch mode toggle from **AI Mode** to **Fast Mode**. | *"Because VYOM+ includes a fully trained local classifier, we can operate completely offline with zero degradation in speed or accuracy."* |
| **API Key Missing or Quota Exceeded** | 403 / 429 HTTP response | Keep **Use Mock Adapter** checked under AI Mode. | *"We are using our deterministic mock adapter which simulates Gemma 4's exact reasoning schema without hitting rate limits."* |
| **Uploaded File Rejected** | File format error | Click **"Load Curated Demo Dataset"** in Upload Studio. | *"I'll load our standard 25-voucher benchmark workbook which covers all 27 categories."* |
| **Browser WebGL Crash** | 3D Coin fails to render | `WebGLErrorBoundary` automatically renders the gold pulsating VYOM fallback. | *"Our 3D container includes a WebGL error boundary that falls back gracefully to a lightweight CSS asset on older hardware."* |
| **Accidental Page Refresh** | Dataset state reset | Re-click **"Load Curated Demo Dataset"** and run **Fast Mode** (takes < 2 seconds). | *"Our session state restores instantaneously thanks to our fast ingestion parser."* |

---

## J. Final Closing Statement

### 20-Second Spoken Conclusion
> *"Judges, VYOM+ bridges the gap between raw financial data and trustworthy accounting intelligence. By uniting sub-millisecond local machine learning, deep Gemma 4 reasoning, and deterministic accounting guardrails, we eliminate manual classification bottlenecks while ensuring complete ledger integrity.  
> Thank you, and we welcome your questions!"*
