# VYOM+ — Production Deployment & Operations Guide

> **Enterprise Deployment & Operations Handbook for the VYOM+ Intelligent Voucher Classification Platform**

---

## 1. Architecture Overview

VYOM+ is a modern dual-engine financial transaction intelligence platform comprising:

1. **Frontend Service**:
   - Next.js 16 (React 19, TypeScript, Tailwind CSS with custom Dark Crystal token system).
   - Real-time tabular inspection, dual-engine classification, multi-dimensional review triage, and streaming audited exports.
   - Port: `3000`.

2. **Backend REST API**:
   - Python 3.12+ FastAPI application with Pydantic v2 validation.
   - Modular REST routing (`/api/v1/datasets`, `/api/v1/classify`, `/api/v1/taxonomy`).
   - Port: `8000`.

3. **Inference & Intelligence Layer**:
   - Google Gemma 4 (`gemma-4-26b-a4b-it`) via official `google-genai` SDK.
   - High-throughput offline deterministic Mock Adapter for test plumbing and CI/CD.
   - Dual accounting signals engine (Money flow, role semantics, 27 voucher knowledge cards).
   - 9-rule accounting contradiction guardrails and multi-pass confidence scoring.

---

## 2. Docker & Container Deployment

### 2.1 Quickstart with Docker Compose

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   # Add your GEMINI_API_KEY in .env if running real LLM inference
   ```

2. **Build and Launch All Services**:
   ```bash
   docker compose up --build -d
   ```

3. **Verify Health & Logs**:
   ```bash
   # Check service status
   docker compose ps

   # Stream backend logs
   docker compose logs -f backend

   # Check health endpoint
   curl http://localhost:8000/health
   ```

4. **Access the Applications**:
   - Frontend Dashboard: [http://localhost:3000](http://localhost:3000)
   - Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

5. **Stop Services**:
   ```bash
   docker compose down
   ```

---

## 3. Local Bare-Metal / Developer Deployment

### 3.1 One-Click Launchers

- **Windows (PowerShell)**:
  ```powershell
  .\start.ps1
  ```
- **Linux / macOS (Bash)**:
  ```bash
  chmod +x start.sh run_tests.sh
  ./start.sh
  ```

### 3.2 Manual Step-by-Step Setup

#### Backend:
```bash
# 1. Create and activate virtual environment
python -m venv backend/venv
source backend/venv/bin/activate  # Or .\backend\venv\Scripts\Activate.ps1 on Windows

# 2. Install dependencies
pip install -r backend/requirements-dev.txt

# 3. Run test suite
pytest -v backend/tests

# 4. Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --app-dir backend --reload
```

#### Frontend:
```bash
# 1. Enter frontend folder
cd frontend

# 2. Install dependencies
npm install

# 3. Run production build
npm run build

# 4. Start production server
npm run start  # Or npm run dev for live reloading
```

---

## 4. Environment Variables Reference

| Variable Name | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `GEMINI_API_KEY` | Optional | `""` | Google Gemini API key for live Gemma 4 inference. When unset, platform automatically runs in deterministic mock adapter mode. |
| `GEMINI_MODEL` | Optional | `gemma-4-26b-a4b-it` | Target Gemini model identifier (fallback: `gemma-4-31b-it`). |
| `HOST` | Optional | `0.0.0.0` | Host IP for FastAPI backend. |
| `PORT` | Optional | `8000` | Port for FastAPI backend. |
| `ENVIRONMENT` | Optional | `production` | Runtime mode (`production`, `development`). |
| `LOG_LEVEL` | Optional | `info` | Logging verbosity (`debug`, `info`, `warning`, `error`). |
| `NEXT_PUBLIC_API_URL` | Optional | `http://localhost:8000` | Publicly reachable backend API URL consumed by the frontend client. |

---

## 5. Cloud & Production Hosting Recommendations

### 5.1 Google Cloud Platform (GCP Cloud Run)
Because Gemma 4 and Gemini API live within the Google Cloud ecosystem, GCP Cloud Run offers minimal latency:
- **Backend Service**: Deploy `backend/Dockerfile` as a container on Cloud Run with `--min-instances=1` and secret environment variable `GEMINI_API_KEY` mounted via Secret Manager.
- **Frontend Service**: Deploy `frontend/` as a Cloud Run service or host on Firebase App Hosting / Vercel with `NEXT_PUBLIC_API_URL` pointing to the backend Cloud Run service.

### 5.2 AWS (ECS / Fargate or App Runner)
- Push both images (`vyom-backend` and `vyom-frontend`) to Amazon ECR.
- Deploy task definition with port 8000 and 3000 mapped through an Application Load Balancer (ALB).

### 5.3 Vercel + Backend Host
- Deploy `frontend/` directly to Vercel (zero-config Next.js 16 support).
- Configure environment variable `NEXT_PUBLIC_API_URL=https://api.yourdomain.com`.

---

## 6. Verification & Quality Gates

Run the automated test runner to ensure 100% green compliance:
```powershell
.\run_tests.ps1
```
Expected output:
```text
[1/2] Running Backend Pytest Suite...
======================= 83 passed, 2 warnings in 11.15s =======================
[OK] All Backend Tests Passed!

[2/2] Running Frontend Production Compilation (Turbopack / TypeScript)...
✓ Compiled successfully
✓ Generating static pages (4/4)
[OK] Frontend Production Build Verified Successfully!

==========================================================
 ALL CHECKS PASSED: 100% GREEN ACROSS ENTIRE PLATFORM
==========================================================
```
