from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page

from config.settings import BASE_URL, SCREENSHOTS_DIR
from pages.cleartrip_home_page import CleartripHomePage


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "test_data" in metafunc.fixturenames:
        reader_available = "flight_search_test_data" in metafunc.fixturenames
        if reader_available:
            return
        from config.settings import EXCEL_FILE, EXCEL_SHEET
        from utils.excel_reader import ExcelReader, create_sample_excel

        if not EXCEL_FILE.exists():
            create_sample_excel(EXCEL_FILE, EXCEL_SHEET)

        data = ExcelReader(EXCEL_FILE, EXCEL_SHEET).read_flight_search_data()
        metafunc.parametrize(
            "test_data",
            data,
            ids=[item.test_id for item in data],
        )


@pytest.fixture
def test_data(request: pytest.FixtureRequest):
    return request.param


def test_flight_search_and_validate_results(
    cleartrip_page: Page,
    test_data,
    record_test_result,
) -> None:
    home_page = CleartripHomePage(cleartrip_page, BASE_URL, default_timeout_ms=30_000)
    screenshot_path = ""

    try:
        results = home_page.search_flights(
            from_city=test_data.from_city,
            to_city=test_data.to_city,
            journey_type=test_data.journey_type,
            departure_days_ahead=test_data.departure_days_ahead,
        )

        assert results["price"], "Flight price was not visible on results page"
        assert results["airline"], "Airline name was not visible on results page"
        assert re.search(r"₹\s*[\d,]+", str(results["price"])), (
            f"Price format invalid: {results['price']}"
        )

        record_test_result(
            test_id=test_data.test_id,
            from_city=test_data.from_city,
            to_city=test_data.to_city,
            journey_type=test_data.journey_type,
            status="PASSED",
            message=(
                f"Verified results at {results['results_url']} | "
                f"Airline: {results['airline']} | Price: {results['price']}"
            ),
        )
    except Exception as exc:
        screenshot_file = SCREENSHOTS_DIR / f"{test_data.test_id}_failure.png"
        cleartrip_page.screenshot(path=str(screenshot_file), full_page=True)
        screenshot_path = str(screenshot_file)

        record_test_result(
            test_id=test_data.test_id,
            from_city=test_data.from_city,
            to_city=test_data.to_city,
            journey_type=test_data.journey_type,
            status="FAILED",
            message=str(exc),
            screenshot_path=screenshot_path,
        )
        raise
