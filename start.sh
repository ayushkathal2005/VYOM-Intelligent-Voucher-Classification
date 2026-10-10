#!/usr/bin/env bash
# ==============================================================================
# VYOM+ Local Development Startup Script (POSIX / Linux / macOS)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo " VYOM+ Intelligent Voucher Classification Platform"
echo " Local Full-Stack Development Launcher"
echo "=========================================================="

# 1. Environment Configuration Check
if [ ! -f "$SCRIPT_DIR/.env" ]; then
    echo "[INFO] .env not found. Copying from .env.example..."
    cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
fi

# 2. Backend Environment Check
VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[SETUP] Python virtualenv not found in backend/venv. Creating..."
    python3 -m venv "$SCRIPT_DIR/backend/venv"
    "$SCRIPT_DIR/backend/venv/bin/pip" install --upgrade pip
    "$SCRIPT_DIR/backend/venv/bin/pip" install -r "$SCRIPT_DIR/backend/requirements-dev.txt"
fi

# 3. Frontend Dependencies Check
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
    echo "[SETUP] Frontend node_modules not found. Installing..."
    (cd "$SCRIPT_DIR/frontend" && npm install)
fi

echo "[STARTING] Launching Backend FastAPI service on http://127.0.0.1:8000..."
(cd "$SCRIPT_DIR/backend" && "$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload) &
BACKEND_PID=$!

echo "[STARTING] Launching Frontend Next.js service on http://localhost:3000..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

cleanup() {
    echo ""
    echo "[STOPPING] Terminating services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "[STOPPED] Done."
}

trap cleanup SIGINT SIGTERM

echo "=========================================================="
echo " Both services running in background:"
echo " - Frontend:    http://localhost:3000"
echo " - Backend API: http://127.0.0.1:8000/docs"
echo " Press Ctrl+C to stop both services."
echo "=========================================================="

wait
