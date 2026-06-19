import logging
from typing import Optional

from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)


class AmazonScraper(BaseScraper):
    store_name = "Amazon"
    url_patterns = ["amazon.com", "amazon.co.uk", "amazon.ca", "amazon.de"]

    def _scrape_with_requests(self, url: str) -> Optional[ScrapeResult]:
        soup = self._get_soup(url)
        result = self._parse(soup, url)
        # Amazon often serves a CAPTCHA page; detect it
        if result is None and soup.find("form", {"action": "/errors/validateCaptcha"}):
            raise ValueError("CAPTCHA detected — switching to Selenium")
        return result

    def _parse(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        # Product name
        name_tag = soup.find("span", {"id": "productTitle"})
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)

        # Price — try multiple locations Amazon uses
        price = None
        for selector in [
            ("span", {"class": "a-price-whole"}),
            ("span", {"id": "priceblock_ourprice"}),
            ("span", {"id": "priceblock_dealprice"}),
            ("span", {"class": "a-offscreen"}),
        ]:
            tag = soup.find(*selector)
            if tag:
                price = self._clean_price(tag.get_text(strip=True))
                if price:
                    break

        if price is None:
            logger.warning("Could not extract price from %s", url)
            return None

        # Image
        image_url = None
        img = soup.find("img", {"id": "landingImage"}) or soup.find("img", {"id": "imgBlkFront"})
        if img:
            image_url = img.get("src") or img.get("data-old-hires") or img.get("data-src")

        # Stock
        avail = soup.find("div", {"id": "availability"})
        in_stock = True
        if avail:
            text = avail.get_text(strip=True).lower()
            in_stock = "in stock" in text or "available" in text

        return ScrapeResult(name=name, price=price, image_url=image_url, in_stock=in_stock)
