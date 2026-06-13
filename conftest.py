from __future__ import annotations

import time
from pathlib import Path

import pytest
from playwright.sync_api import Browser, BrowserContext, Page

from config.settings import (
    BASE_URL,
    DATA_DIR,
    DEFAULT_TIMEOUT_MS,
    EXCEL_FILE,
    EXCEL_SHEET,
    NAVIGATION_TIMEOUT_MS,
    REPORTS_DIR,
    SCREENSHOTS_DIR,
)
from utils.excel_reader import ExcelReader, create_sample_excel
from utils.report_generator import ReportGenerator, TestResult


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "locale": "en-IN",
        "timezone_id": "Asia/Kolkata",
        "ignore_https_errors": True,
    }


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args: dict, pytestconfig: pytest.Config) -> dict:
    return {
        **browser_type_launch_args,
        "headless": not pytestconfig.getoption("--headed"),
        "slow_mo": pytestconfig.getoption("--slowmo"),
    }


@pytest.fixture(scope="session", autouse=True)
def ensure_excel_data() -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not EXCEL_FILE.exists():
        create_sample_excel(EXCEL_FILE, EXCEL_SHEET)
    return EXCEL_FILE


@pytest.fixture(scope="session")
def flight_search_test_data(ensure_excel_data: Path) -> list:
    reader = ExcelReader(ensure_excel_data, EXCEL_SHEET)
    data = reader.read_flight_search_data()
    if not data:
        pytest.exit("No enabled test rows found in Excel data file.", returncode=1)
    return data


@pytest.fixture(scope="session")
def execution_report() -> ReportGenerator:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    return ReportGenerator(REPORTS_DIR)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    report: ReportGenerator | None = getattr(session.config, "_execution_report", None)
    if report and report.results:
        paths = report.write_all_reports()
        session.config._report_paths = paths  # type: ignore[attr-defined]


@pytest.fixture
def cleartrip_page(page: Page) -> Page:
    page.set_default_timeout(DEFAULT_TIMEOUT_MS)
    page.set_default_navigation_timeout(NAVIGATION_TIMEOUT_MS)
    return page


@pytest.fixture
def record_test_result(request: pytest.FixtureRequest, execution_report: ReportGenerator):
    started_at = time.time()

    def _record(
        *,
        test_id: str,
        from_city: str,
        to_city: str,
        journey_type: str,
        status: str,
        message: str,
        screenshot_path: str = "",
    ) -> None:
        result = TestResult(
            test_id=test_id,
            from_city=from_city,
            to_city=to_city,
            journey_type=journey_type,
            status=status,
            duration_seconds=round(time.time() - started_at, 2),
            message=message,
            screenshot_path=screenshot_path,
        )
        execution_report.add_result(result)
        request.config._execution_report = execution_report  # type: ignore[attr-defined]

    return _record
