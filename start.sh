#!/usr/bin/env bash
# TripPlanner one-click launcher — starts backend + frontend, opens browser.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_PORT=8000
FRONTEND_PORT=5173

cleanup() {
    echo ""
    echo "Shutting down..."
    [ -n "${BACKEND_PID:-}" ] && kill "$BACKEND_PID" 2>/dev/null
    [ -n "${FRONTEND_PID:-}" ] && kill "$FRONTEND_PID" 2>/dev/null
    wait 2>/dev/null
    echo "Done."
}
trap cleanup EXIT

echo "=== TripPlanner ==="

# Kill existing processes on our ports
for port in "$BACKEND_PORT" "$FRONTEND_PORT"; do
    pid=$(lsof -ti :"$port" 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "Port $port in use (PID $pid), killing..."
        kill $pid 2>/dev/null || true
        sleep 0.5
    fi
done

# 1) Backend
echo "[1/3] Starting backend on :${BACKEND_PORT} ..."
(
    cd "$ROOT_DIR"
    .venv/bin/tripplanner web --port "$BACKEND_PORT"
) &
BACKEND_PID=$!

# Wait for backend to be ready
echo "[2/3] Waiting for backend ..."
for i in $(seq 1 20); do
    if curl -sf "http://localhost:${BACKEND_PORT}/docs" >/dev/null 2>&1; then
        echo "       Backend ready."
        break
    fi
    sleep 0.5
done

# 2) Frontend (Vite dev server with proxy to backend)
echo "[3/3] Starting frontend on :${FRONTEND_PORT} ..."
(
    cd "$ROOT_DIR/frontend"
    npx vite --port "$FRONTEND_PORT"
) &
FRONTEND_PID=$!

# Wait for frontend
sleep 2

# 3) Open browser
URL="http://localhost:${FRONTEND_PORT}"
echo ""
echo "============================="
echo "  Frontend:  $URL"
echo "  Backend:   http://localhost:${BACKEND_PORT}/docs"
echo "============================="
echo ""

if [[ "$(uname)" == "Darwin" ]]; then
    open "$URL" 2>/dev/null || true
elif command -v xdg-open &>/dev/null; then
    xdg-open "$URL" 2>/dev/null || true
fi

# Keep script running until Ctrl+C
wait
