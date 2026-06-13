from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import EXCEL_FILE, EXCEL_SHEET
from utils.excel_reader import create_sample_excel

if __name__ == "__main__":
    create_sample_excel(EXCEL_FILE, EXCEL_SHEET)
    print(f"Sample Excel created at: {EXCEL_FILE}")
