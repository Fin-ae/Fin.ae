#!/bin/bash
# Start the Finae backend server

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_DIR="$BACKEND_DIR/venv"
LOG_FILE="$ROOT_DIR/logs/backend.log"
DEFAULT_PORT=8000

mkdir -p "$ROOT_DIR/logs"

# Resolve python
PYTHON_CMD=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || command -v py 2>/dev/null || echo "")
if [ -z "$PYTHON_CMD" ]; then
  echo "[backend] ERROR: Python not found. Install Python and add it to PATH." | tee -a "$LOG_FILE"
  exit 1
fi

# Create venv if missing
if [ ! -d "$VENV_DIR" ]; then
  echo "[backend] Creating virtual environment..." | tee -a "$LOG_FILE"
  "$PYTHON_CMD" -m venv "$VENV_DIR"
fi

# Activate venv
source "$VENV_DIR/Scripts/activate" 2>/dev/null || source "$VENV_DIR/bin/activate"

# Install dependencies
echo "[backend] Installing dependencies..." | tee -a "$LOG_FILE"
pip install --upgrade pip -q
pip install -r "$BACKEND_DIR/requirements.txt" -q

# Check .env
if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "[backend] ERROR: backend/.env not found. Copy it and fill in GROQ_API_KEY." | tee -a "$LOG_FILE"
  exit 1
fi

# Find a free port starting from DEFAULT_PORT
port_busy() {
  netstat -ano 2>/dev/null | grep -E ":$1[[:space:]]" | grep -qi "LISTEN" && return 0
  (echo >/dev/tcp/localhost/$1) 2>/dev/null && return 0
  return 1
}
PORT=$DEFAULT_PORT
echo "[backend] Checking ports from $PORT..." | tee -a "$LOG_FILE"
while port_busy "$PORT"; do
  echo "[backend] Port $PORT is busy, trying $((PORT+1))..." | tee -a "$LOG_FILE"
  PORT=$((PORT + 1))
done
echo "[backend] Port $PORT is free." | tee -a "$LOG_FILE"

echo "[backend] Starting on port $PORT — logs: logs/backend.log" | tee -a "$LOG_FILE"
cd "$BACKEND_DIR"
exec uvicorn server:app --reload --host 0.0.0.0 --port "$PORT" 2>&1 | tee -a "$LOG_FILE"
