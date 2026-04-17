#!/bin/bash
# Finae Runbook — starts backend and frontend in parallel

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
mkdir -p "$ROOT_DIR/logs"

echo "=== Finae Runbook ==="
echo "  Backend log:  logs/backend.log"
echo "  Frontend log: logs/frontend.log"
echo ""

bash "$ROOT_DIR/run_backend.sh" &
BACKEND_PID=$!

# Give backend a moment to bind before frontend starts
sleep 3

bash "$ROOT_DIR/run_frontend.sh" &
FRONTEND_PID=$!

echo "=== Services starting (PIDs: backend=$BACKEND_PID, frontend=$FRONTEND_PID) ==="
echo "Press Ctrl+C to stop all services."

cleanup() {
  echo ""
  echo "Stopping services..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null
  echo "All services stopped."
}

trap cleanup SIGINT SIGTERM
wait
