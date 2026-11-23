@echo off
cd /d "%~dp0"
if not exist .venv\.ready (
  echo First-time setup, a few minutes...
  python -m venv .venv
  .venv\Scripts\pip install flask httpx playwright
  .venv\Scripts\python -m playwright install chromium
  echo ready> .venv\.ready
)
.venv\Scripts\python app.py
pause
