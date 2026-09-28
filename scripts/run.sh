#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate

pip install -q -r requirements.txt

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

python data/generate_data.py
python data/seed.py

echo ""
echo "Starting API at http://localhost:8000  (docs at /docs)"
echo "Open frontend/index.html in a browser to use the chat UI."
echo ""
uvicorn app.main:app --reload
