@echo off
setlocal

cd /d "%~dp0"

if not exist .venv (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium

if not exist data\flight_search_data.xlsx (
    python scripts\create_sample_data.py
)

pytest %*

endlocal
