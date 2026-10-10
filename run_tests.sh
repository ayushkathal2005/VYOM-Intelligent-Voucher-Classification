#!/usr/bin/env bash
# ==============================================================================
# VYOM+ Test & Verification Suite Runner (POSIX / Linux / macOS)
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo " Running VYOM+ Full System Verification Suite"
echo "=========================================================="

VENV_PYTHON="$SCRIPT_DIR/backend/venv/bin/python"

echo ""
echo "[1/2] Running Backend Pytest Suite..."
"$VENV_PYTHON" -m pytest -v "$SCRIPT_DIR/backend/tests"
echo "[OK] All Backend Tests Passed!"

echo ""
echo "[2/2] Running Frontend Production Compilation..."
(cd "$SCRIPT_DIR/frontend" && npm run build)
echo "[OK] Frontend Production Build Verified Successfully!"

echo ""
echo "=========================================================="
echo " ALL CHECKS PASSED: 100% GREEN ACROSS ENTIRE PLATFORM"
echo "=========================================================="
