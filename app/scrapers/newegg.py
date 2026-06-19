import logging
from typing import Optional

from bs4 import BeautifulSoup
from app.scrapers.base import BaseScraper, ScrapeResult

logger = logging.getLogger(__name__)


class NeweggScraper(BaseScraper):
    store_name = "Newegg"
    url_patterns = ["newegg.com"]

    def _scrape_with_requests(self, url: str) -> Optional[ScrapeResult]:
        soup = self._get_soup(url)
        return self._parse(soup, url)

    def _parse(self, soup: BeautifulSoup, url: str) -> Optional[ScrapeResult]:
        name_tag = soup.find("h1", {"class": "product-title"})
        if not name_tag:
            return None
        name = name_tag.get_text(strip=True)

        price = None
        price_tag = soup.find("li", {"class": "price-current"})
        if price_tag:
            strong = price_tag.find("strong")
            sup = price_tag.find("sup")
            if strong:
                raw = strong.get_text(strip=True)
                if sup:
                    raw += "." + sup.get_text(strip=True)
                price = self._clean_price(raw)

        if price is None:
            return None

        image_url = None
        img = soup.find("img", {"class": "product-view-img-original"})
        if img:
            image_url = img.get("src")

        avail = soup.find("div", {"class": "product-inventory"})
        in_stock = True
        if avail:
            in_stock = "in stock" in avail.get_text(strip=True).lower()

        return ScrapeResult(name=name, price=price, image_url=image_url, in_stock=in_stock)
