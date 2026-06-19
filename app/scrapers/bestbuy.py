import logging
from typing import Optional

from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)


class BestBuyScraper(BaseScraper):
    store_name = "Best Buy"
    url_patterns = ["bestbuy.com"]

    def _scrape_with_requests(self, url: str) -> Optional[ScrapeResult]:
        soup = self._get_soup(url)
        return self._parse(soup, url)

    def _parse(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        name_tag = (
            soup.find("h1", {"class": "heading-5"})
            or soup.find("h1", {"itemprop": "name"})
            or soup.find("h1")
        )
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)

        price = None
        for selector in [
            ("div", {"class": "priceView-hero-price"}),
            ("span", {"aria-hidden": "true", "class": "sr-only"}),
            ("div", {"class": "pricing-price"}),
        ]:
            tag = soup.find(*selector)
            if tag:
                price = self._clean_price(tag.get_text(strip=True))
                if price:
                    break

        if price is None:
            return None

        image_url = None
        img = soup.find("img", {"class": "primary-image"}) or soup.find("img", {"itemprop": "image"})
        if img:
            image_url = img.get("src")

        add_btn = soup.find("button", {"class": "add-to-cart-button"})
        in_stock = add_btn is not None and "disabled" not in add_btn.attrs

        return ScrapeResult(name=name, price=price, image_url=image_url, in_stock=in_stock)
