from __future__ import annotations

import re
from datetime import date, timedelta

from playwright.sync_api import Locator, Page, expect

from pages.base_page import BasePage


class CleartripHomePage(BasePage):
    CITY_ALIASES = {
        "bangalore": ["Bangalore", "Bengaluru", "BLR"],
        "bengaluru": ["Bengaluru", "Bangalore", "BLR"],
        "mumbai": ["Mumbai", "BOM"],
        "delhi": ["Delhi", "New Delhi", "DEL"],
        "new delhi": ["New Delhi", "Delhi", "DEL"],
        "goa": ["Goa", "GOI"],
        "chennai": ["Chennai", "MAA"],
        "hyderabad": ["Hyderabad", "HYD"],
    }
    SIGN_IN_CLOSE_SELECTORS = [
        "[data-testid='closeIcon']",
        "button[aria-label='Close']",
        "button[aria-label='close']",
        "[class*='modal'] button:has-text('×')",
        "[class*='Modal'] button:has-text('×')",
        "button:has-text('Not now')",
        "button:has-text('Skip')",
        "button:has-text('Maybe later')",
    ]

    def open_homepage(self) -> None:
        self.navigate()
        self.page.wait_for_load_state("domcontentloaded")
        self.dismiss_sign_in_prompts()

    def dismiss_sign_in_prompts(self) -> None:
        close_icon = self.page.locator("[data-testid='closeIcon']")
        try:
            close_icon.first.wait_for(state="visible", timeout=8_000)
            close_icon.first.click()
            expect(self.page.locator(".overlay-bg").first).to_be_hidden(timeout=5_000)
            return
        except Exception:
            pass

        overlay = self.page.locator(".overlay-bg")
        if overlay.count() > 0 and overlay.first.is_visible(timeout=2_000):
            if close_icon.count() > 0:
                close_icon.first.click(force=True)
                self.page.wait_for_timeout(500)

        self.page.keyboard.press("Escape")
        for selector in self.SIGN_IN_CLOSE_SELECTORS:
            close_button = self.page.locator(selector).first
            if close_button.is_visible(timeout=1_000):
                close_button.click()
                self.page.wait_for_timeout(300)

    def _ensure_overlay_closed(self) -> None:
        overlay = self.page.locator(".overlay-bg")
        if overlay.count() > 0 and overlay.first.is_visible(timeout=1_000):
            self.dismiss_sign_in_prompts()

    def select_flights_tab(self) -> None:
        flights_tab = self.page.get_by_role("link", name=re.compile(r"^Flights$", re.I))
        if flights_tab.count() > 0 and flights_tab.first.is_visible():
            flights_tab.first.click()
            self.page.wait_for_timeout(500)

    def select_journey_type(self, journey_type: str) -> None:
        normalized = journey_type.strip().lower()
        if "round" in normalized:
            self.page.get_by_role("radio", name=re.compile(r"round\s*trip", re.I)).check(force=True)
        else:
            self.page.get_by_role("radio", name=re.compile(r"one\s*way", re.I)).check(force=True)

    def _city_input(self, field: str) -> Locator:
        placeholder = "Where from?" if field.lower() == "from" else "Where to?"
        return self.page.get_by_placeholder(placeholder)

    def enter_city_with_suggestion(self, field: str, city: str) -> None:
        self._ensure_overlay_closed()
        city_input = self._city_input(field)
        city_input.click()
        city_input.fill("")
        city_input.type(city, delay=80)
        self._select_city_suggestion(city)

    def _city_search_terms(self, city: str) -> list[str]:
        normalized = city.strip().lower()
        aliases = self.CITY_ALIASES.get(normalized, [])
        terms = [city, *aliases]
        unique_terms: list[str] = []
        for term in terms:
            if term not in unique_terms:
                unique_terms.append(term)
        return unique_terms

    def _select_city_suggestion(self, city: str) -> None:
        for term in self._city_search_terms(city):
            suggestion = self.page.locator("li").filter(
                has_text=re.compile(re.escape(term), re.I)
            ).first
            if suggestion.is_visible(timeout=4_000):
                suggestion.click()
                return

        fallback = self.page.locator("li").filter(
            has_text=re.compile(r"\([A-Z]{3}\)", re.I)
        ).first
        expect(fallback).to_be_visible(timeout=10_000)
        fallback.click()

    def select_departure_date(self, days_ahead: int) -> None:
        target_date = date.today() + timedelta(days=days_ahead)
        calendar_trigger = self.page.locator("[data-testid='dateSelectOnward']").first
        if not calendar_trigger.is_visible(timeout=2_000):
            calendar_trigger = self.page.locator(".homeCalender").first

        calendar_trigger.click()
        self._pick_date_from_calendar(target_date)

    def _pick_date_from_calendar(self, target_date: date) -> None:
        month_year_pattern = re.compile(
            rf"{target_date.strftime('%b')}|{target_date.strftime('%B')}|{target_date.year}",
            re.I,
        )
        next_month_button = self.page.locator("button[aria-label='next']").first

        for _ in range(12):
            day_cell = self.page.locator(
                ".DayPicker-Day:not(.DayPicker-Day--disabled) .day-gridContent"
            ).filter(has_text=re.compile(rf"^{target_date.day}$")).first

            if day_cell.is_visible(timeout=1_500):
                day_cell.click()
                return

            if next_month_button.is_visible(timeout=1_000):
                next_month_button.click()
                self.page.wait_for_timeout(400)
                continue

            visible_month = self.page.locator("div, span").filter(has_text=month_year_pattern)
            if visible_month.count() > 0:
                break

        fallback = self.page.locator(
            ".DayPicker-Day:not(.DayPicker-Day--disabled) .day-gridContent"
        ).filter(has_text=re.compile(rf"^{target_date.day}$")).first
        expect(fallback).to_be_visible(timeout=10_000)
        fallback.click()

    def click_search_flights(self) -> None:
        search_button = self.page.get_by_role("button", name=re.compile(r"search\s*flights", re.I))
        expect(search_button).to_be_enabled(timeout=10_000)
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=60_000):
            search_button.click()

    def verify_flight_results(self) -> dict[str, str | int]:
        if "captcha" in self.page.url.lower():
            raise RuntimeError("Captcha detected on results page. Stopping before payment/booking.")

        self.page.wait_for_load_state("networkidle", timeout=60_000)

        results_container_selectors = [
            "[class*='result']",
            "[class*='Result']",
            "[class*='flight']",
            "[class*='Flight']",
            "[data-testid*='flight']",
        ]
        for selector in results_container_selectors:
            container = self.page.locator(selector)
            if container.count() > 0:
                expect(container.first).to_be_visible(timeout=30_000)
                break

        price_locator = self.page.locator("text=/₹\\s*[\\d,]+/").first
        expect(price_locator).to_be_visible(timeout=30_000)
        price_text = price_locator.inner_text().strip()

        airline_patterns = [
            r"IndiGo|Indigo",
            r"Air India",
            r"SpiceJet|Spicejet",
            r"Vistara",
            r"Akasa",
            r"Go First",
            r"AirAsia",
        ]
        airline_locator = self.page.locator(
            "text=/(" + "|".join(airline_patterns) + ")/i"
        ).first
        expect(airline_locator).to_be_visible(timeout=30_000)
        airline_text = airline_locator.inner_text().strip()

        flight_cards = self.page.locator(
            "[class*='result'], [class*='Result'], [class*='flight-card'], [class*='FlightCard']"
        )
        visible_cards = flight_cards.count() if flight_cards.count() > 0 else 1

        return {
            "price": price_text,
            "airline": airline_text,
            "result_count_hint": visible_cards,
            "results_url": self.page.url,
        }

    def search_flights(
        self,
        from_city: str,
        to_city: str,
        journey_type: str,
        departure_days_ahead: int,
    ) -> dict[str, str | int]:
        self.open_homepage()
        self.select_flights_tab()
        self.select_journey_type(journey_type)
        self.enter_city_with_suggestion("from", from_city)
        self.enter_city_with_suggestion("to", to_city)
        self.select_departure_date(departure_days_ahead)
        self.click_search_flights()
        return self.verify_flight_results()
