import time
import random
import logging
from dataclasses import dataclass
from typing import Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from app.config import Config

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Connection": "keep-alive",
}


@dataclass
class ScrapeResult:
    name: str
    price: float
    currency: str = "USD"
    image_url: Optional[str] = None
    in_stock: bool = True
    store: str = ""


class BaseScraper:
    store_name = "unknown"
    # Subclasses list URL patterns that belong to this store
    url_patterns: list[str] = []

    def __init__(self):
        self._session = requests.Session()
        self._session.headers.update(HEADERS)

    # ------------------------------------------------------------------ #
    # Public interface
    # ------------------------------------------------------------------ #

    def scrape(self, url: str) -> Optional[ScrapeResult]:
        delay = Config.REQUEST_DELAY_SECONDS + random.uniform(0, 1)
        time.sleep(delay)
        try:
            result = self._scrape_with_requests(url)
            if result:
                result.store = self.store_name
                return result
        except Exception as exc:
            logger.warning("Requests scrape failed for %s: %s — falling back to Selenium", url, exc)

        try:
            result = self._scrape_with_selenium(url)
            if result:
                result.store = self.store_name
                return result
        except Exception as exc:
            logger.error("Selenium scrape also failed for %s: %s", url, exc)

        return None

    @classmethod
    def matches(cls, url: str) -> bool:
        return any(p in url for p in cls.url_patterns)

    # ------------------------------------------------------------------ #
    # Override in subclasses
    # ------------------------------------------------------------------ #

    def _scrape_with_requests(self, url: str) -> Optional[ScrapeResult]:
        raise NotImplementedError

    def _scrape_with_selenium(self, url: str) -> Optional[ScrapeResult]:
        driver = self._make_driver()
        try:
            driver.get(url)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            time.sleep(2)
            soup = BeautifulSoup(driver.page_source, "lxml")
            return self._parse(soup, url)
        finally:
            driver.quit()

    def _parse(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        raise NotImplementedError

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _get_soup(self, url: str) -> BeautifulSoup:
        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")

    @staticmethod
    def _clean_price(raw: str) -> Optional[float]:
        if not raw:
            return None
        cleaned = "".join(c for c in raw if c.isdigit() or c == ".")
        # Handle cases like "1,299.00" already stripped of comma
        try:
            return float(cleaned)
        except ValueError:
            return None

    @staticmethod
    def _make_driver() -> webdriver.Chrome:
        opts = Options()
        if Config.HEADLESS:
            opts.add_argument("--headless=new")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument(f"--user-agent={HEADERS['User-Agent']}")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
        except Exception:
            service = Service()
        return webdriver.Chrome(service=service, options=opts)
