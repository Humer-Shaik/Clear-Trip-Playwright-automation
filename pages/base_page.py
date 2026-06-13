from __future__ import annotations

from playwright.sync_api import Locator, Page, expect


class BasePage:
    def __init__(self, page: Page, base_url: str, default_timeout_ms: int) -> None:
        self.page = page
        self.base_url = base_url
        self.default_timeout_ms = default_timeout_ms
        self.page.set_default_timeout(default_timeout_ms)

    def navigate(self, path: str = "") -> None:
        url = f"{self.base_url.rstrip('/')}/{path.lstrip('/')}" if path else self.base_url
        self.page.goto(url, wait_until="domcontentloaded")

    def wait_for_network_idle(self, timeout_ms: int | None = None) -> None:
        self.page.wait_for_load_state("networkidle", timeout=timeout_ms or self.default_timeout_ms)
