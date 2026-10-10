# VYOM+ — Developer Setup & Installation Guide

This guide describes how to set up, run, and test the VYOM+ full-stack platform locally.

---

## 1. Prerequisites

- **Node.js**: `v20.x` or higher (verified with `v24.12.0`)
- **npm**: `v10.x` or higher (on Windows PowerShell, invoke via `npm.cmd` / `npx.cmd`)
- **Python**: `3.11` to `3.14` (verified with Python `3.13` in virtualenv)
- **Git**: `2.40+`

---

## 2. Repository Configuration

Clone the repository and enter the directory:

```bash
git clone https://github.com/ayushkathal2005/VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs.git
cd VYOM-Intelligent-Voucher-Classification-Using-Open-Source-LLMs
```

Create a local `.env` file from the provided template:

```bash
cp .env.example .env
```

Edit `.env` as appropriate:
```ini
GEMINI_API_KEY=your_gemini_api_key_here  # Leave empty during mock development
GEMINI_MODEL=gemma-4-26b-a4b-it
HOST=127.0.0.1
PORT=8000
ENVIRONMENT=development
```

---

## 3. Backend Setup (FastAPI & Python)

1. **Create and activate a virtual environment**:

   **Windows (PowerShell)**:
   ```powershell
   python -m venv backend/venv
   .\backend\venv\Scripts\Activate.ps1
   ```

   **Linux / macOS**:
   ```bash
   python3 -m venv backend/venv
   source backend/venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r backend/requirements-dev.txt
   ```

3. **Run the backend test suite**:
   ```bash
   pytest -v backend/tests
   ```

4. **Start the development server**:
   ```bash
   uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir backend --reload
   ```

5. **Verify the health check endpoint**:
   ```bash
   curl http://127.0.0.1:8000/health
   ```
   Expected response:
   ```json
   {
     "status": "healthy",
     "app": "VYOM+",
     "version": "0.1.0",
     "environment": "development",
     "gemini_configured": false,
     "gemini_model": "gemma-4-26b-a4b-it"
   }
   ```

---

## 4. Frontend Setup (Next.js, TypeScript & Tailwind CSS)

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install frontend dependencies**:
   ```bash
   npm install
   ```

3. **Run ESLint**:
   ```bash
   npm run lint
   ```

4. **Build the production bundle**:
   ```bash
   npm run build
   ```

5. **Start the development server**:
   ```bash
   npm run dev
   ```
   Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 5. Security & Safety Guidelines

- **Never commit `.env` or credentials** to Git.
- The backend operates in **mock adapter mode** whenever `GEMINI_API_KEY` is unset or empty, ensuring deterministic offline testing without exposing secrets.
