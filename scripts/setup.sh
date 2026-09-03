#!/usr/bin/env bash
set -e

echo "=== Setting up FaceTrace Pipeline ==="

# 1. Setup Python virtualenv
if [ ! -d ".venv" ]; then
    echo "[*] Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "[*] Installing Python backend dependencies..."
.venv/bin/pip install -r requirements.txt

# 2. Setup Node frontend
if [ -d "frontend" ]; then
    echo "[*] Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

echo "[*] Generating test sample face..."
.venv/bin/python scripts/create_sample.py

echo "=== Setup complete! ==="
echo "Before the live demo:"
echo "  1. cp .env.example .env and set SERPAPI_API_KEY"
echo "  2. start Anvil: anvil --host 127.0.0.1 --port 8545"
echo "  3. deploy contract: .venv/bin/python scripts/deploy_contract.py"
echo "Run backend:  .venv/bin/uvicorn backend.main:app --reload --port 8000"
echo "Run frontend: cd frontend && npm run dev"
echo "Run CLI demo: .venv/bin/python scripts/demo.py"
