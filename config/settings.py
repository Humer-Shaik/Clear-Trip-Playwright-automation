from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"

EXCEL_FILE = DATA_DIR / "flight_search_data.xlsx"
EXCEL_SHEET = "FlightSearch"

BASE_URL = "https://www.cleartrip.com"
DEFAULT_TIMEOUT_MS = 30_000
NAVIGATION_TIMEOUT_MS = 60_000
