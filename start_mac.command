#!/bin/bash
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 isn't installed yet. Install it from python.org/downloads, then double-click this file again."
  read -p "Press Enter to close"; exit 1
fi
if [ ! -f .venv/.ready ]; then
  echo "First-time setup (a few minutes)..."
  python3 -m venv .venv && .venv/bin/pip install flask httpx playwright \
    && .venv/bin/python -m playwright install chromium && touch .venv/.ready \
    || { echo "Setup failed. Take a screenshot of this window and send it to your helper."; read -p "Press Enter to close"; exit 1; }
fi
.venv/bin/python app.py
