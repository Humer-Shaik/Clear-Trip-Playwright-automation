from __future__ import annotations

import logging
import re
import pytest
from playwright.sync_api import Page

from config.settings import BASE_URL, EXCEL_FILE, EXCEL_SHEET, SCREENSHOTS_DIR
from pages.cleartrip_home_page import CleartripHomePage
from utils.excel_reader import ExcelReader, create_sample_excel

logger = logging.getLogger(__name__)


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "test_data" not in metafunc.fixturenames:
        return

    if not EXCEL_FILE.exists():
        create_sample_excel(EXCEL_FILE, EXCEL_SHEET)

    data = ExcelReader(EXCEL_FILE, EXCEL_SHEET).read_flight_search_data()
    metafunc.parametrize("test_data", data, ids=[item.test_id for item in data])


@pytest.mark.ui
def test_flight_search_and_validate_results(
    cleartrip_page: Page,
    test_data,
    record_test_result,
    step_logger,
    request,
) -> None:
    steps, log_step = step_logger
    home_page = CleartripHomePage(cleartrip_page, BASE_URL, default_timeout_ms=30_000)

    logger.info(
        "Starting test %s | From=%s | To=%s | Journey=%s",
        test_data.test_id,
        test_data.from_city,
        test_data.to_city,
        test_data.journey_type,
    )

    screenshot_path = ""
    current_step = "Test execution started"

    try:
        current_step = "Search flights using Cleartrip flow"
        results = home_page.search_flights(
            from_city=test_data.from_city,
            to_city=test_data.to_city,
            journey_type=test_data.journey_type,
            departure_days_ahead=test_data.departure_days_ahead,
        )
        log_step(
            current_step,
            "PASSED",
            f"Flight search completed for {test_data.from_city} to {test_data.to_city}",
        )

        current_step = "Validate airline name is visible"
        assert results["airline"], "Airline name was not visible on results page"
        log_step(
            current_step,
            "PASSED",
            f"Airline visible: {results['airline']}",
        )

        current_step = "Validate flight price is visible"
        assert results["price"], "Flight price was not visible on results page"
        log_step(
            current_step,
            "PASSED",
            f"Price visible: {results['price']}",
        )

        current_step = "Validate price format"
        assert re.search(r"₹\s*[\d,]+", str(results["price"])), (
            f"Price format invalid: {results['price']}"
        )
        log_step(
            current_step,
            "PASSED",
            f"Price format valid: {results['price']}",
        )

        current_step = "Capture screenshot"
        screenshot_file = SCREENSHOTS_DIR / f"{test_data.test_id}.png"
        cleartrip_page.screenshot(path=str(screenshot_file), full_page=True)
        screenshot_path = str(screenshot_file)
        log_step(
            current_step,
            "PASSED",
            f"Screenshot saved at {screenshot_path}",
        )

        request.node.screenshot = screenshot_path
        request.node.log_info = (
            f"Test ID: {test_data.test_id}\n"
            f"From: {test_data.from_city}\n"
            f"To: {test_data.to_city}\n"
            f"Journey Type: {test_data.journey_type}\n"
            f"Status: PASSED\n"
            f"Results URL: {results['results_url']}\n"
            f"Airline: {results['airline']}\n"
            f"Price: {results['price']}"
        )

        logger.info(
            "PASSED %s | Airline=%s | Price=%s | URL=%s",
            test_data.test_id,
            results["airline"],
            results["price"],
            results["results_url"],
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
            steps=steps,
            screenshot_path=screenshot_path,
        )

    except Exception as exc:
        log_step(
            current_step,
            "FAILED",
            str(exc),
        )

        screenshot_file = SCREENSHOTS_DIR / f"{test_data.test_id}_failure.png"
        cleartrip_page.screenshot(path=str(screenshot_file), full_page=True)
        screenshot_path = str(screenshot_file)

        request.node.screenshot = screenshot_path
        request.node.log_info = (
            f"Test ID: {test_data.test_id}\n"
            f"From: {test_data.from_city}\n"
            f"To: {test_data.to_city}\n"
            f"Journey Type: {test_data.journey_type}\n"
            f"Status: FAILED\n"
            f"Error: {str(exc)}"
        )

        logger.exception("FAILED %s", test_data.test_id)

        record_test_result(
            test_id=test_data.test_id,
            from_city=test_data.from_city,
            to_city=test_data.to_city,
            journey_type=test_data.journey_type,
            status="FAILED",
            message=str(exc),
            steps=steps,
            screenshot_path=screenshot_path,
        )
        raise