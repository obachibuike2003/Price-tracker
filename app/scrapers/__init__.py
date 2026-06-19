from app.scrapers.amazon import AmazonScraper
from app.scrapers.bestbuy import BestBuyScraper
from app.scrapers.newegg import NeweggScraper
from app.scrapers.base import BaseScraper, ScrapeResult

SCRAPERS: list[type[BaseScraper]] = [AmazonScraper, BestBuyScraper, NeweggScraper]


def get_scraper(url: str) -> BaseScraper:
    for cls in SCRAPERS:
        if cls.matches(url):
            return cls()
    raise ValueError(f"No scraper available for URL: {url}")
