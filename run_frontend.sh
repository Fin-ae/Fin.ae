#!/bin/bash
# Start the Finae frontend dev server

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_FILE="$ROOT_DIR/logs/frontend.log"
DEFAULT_PORT=3000

mkdir -p "$ROOT_DIR/logs"

# Check node/npm
if ! command -v npm >/dev/null 2>&1; then
  echo "[frontend] ERROR: npm not found. Install Node.js and add it to PATH." | tee -a "$LOG_FILE"
  exit 1
fi

# Install dependencies if node_modules is missing
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "[frontend] Installing npm dependencies..." | tee -a "$LOG_FILE"
  cd "$FRONTEND_DIR" && npm install 2>&1 | tee -a "$LOG_FILE"
fi

# Find a free port starting from DEFAULT_PORT
port_busy() {
  netstat -ano 2>/dev/null | grep -i "LISTEN" | grep -qE ":$1\s" && return 0
  (echo >/dev/tcp/localhost/$1) 2>/dev/null && return 0
  return 1
}
PORT=$DEFAULT_PORT
echo "[frontend] Checking ports from $PORT..." | tee -a "$LOG_FILE"
while port_busy "$PORT"; do
  echo "[frontend] Port $PORT is busy, trying $((PORT+1))..." | tee -a "$LOG_FILE"
  PORT=$((PORT + 1))
done
echo "[frontend] Port $PORT is free." | tee -a "$LOG_FILE"

# Write/update .env with the chosen port and backend URL
BACKEND_URL="${REACT_APP_BACKEND_URL:-http://localhost:8000}"
cat > "$FRONTEND_DIR/.env" <<EOF
REACT_APP_BACKEND_URL=$BACKEND_URL
PORT=$PORT
EOF

echo "[frontend] Starting on port $PORT — logs: logs/frontend.log" | tee -a "$LOG_FILE"
cd "$FRONTEND_DIR"
exec npm start 2>&1 | tee -a "$LOG_FILE"
