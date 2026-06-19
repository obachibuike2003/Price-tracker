import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

from app.config import Config
from app.database import SessionLocal
from app.models import Product, PriceHistory, Alert
from app.scrapers import get_scraper
from app.notifier.alerts import send_price_drop_email

logger = logging.getLogger(__name__)

celery = Celery("price_tracker", broker=Config.CELERY_BROKER_URL, backend=Config.CELERY_RESULT_BACKEND)
celery.conf.timezone = "UTC"
celery.conf.beat_schedule = {
    "scrape-all-products": {
        "task": "app.tasks.scrape_tasks.scrape_all_products",
        "schedule": crontab(minute=0, hour=f"*/{Config.SCRAPE_INTERVAL_HOURS}"),
    },
}


@celery.task(bind=True, max_retries=3, default_retry_delay=300)
def scrape_product(self, product_id: int):
    db = SessionLocal()
    try:
        product = db.get(Product, product_id)
        if not product or not product.is_active:
            return {"status": "skipped", "reason": "not found or inactive"}

        scraper = get_scraper(product.url)
        result = scraper.scrape(product.url)

        if result is None:
            raise ValueError(f"Scraper returned no data for product {product_id}")

        # Update product metadata if it changed
        if result.name and result.name != product.name:
            product.name = result.name
        if result.image_url and result.image_url != product.image_url:
            product.image_url = result.image_url
        product.updated_at = datetime.utcnow()

        # Record price
        entry = PriceHistory(
            product_id=product_id,
            price=result.price,
            currency=result.currency,
            in_stock=result.in_stock,
        )
        db.add(entry)
        db.flush()

        # Check alerts
        active_alerts = db.query(Alert).filter(
            Alert.product_id == product_id,
            Alert.is_active == True,
        ).all()

        for alert in active_alerts:
            if result.price <= alert.target_price:
                sent = send_price_drop_email(
                    to_email=alert.email,
                    product_name=product.name,
                    product_url=product.url,
                    target_price=alert.target_price,
                    current_price=result.price,
                    store=product.store,
                )
                if sent:
                    alert.triggered_at = datetime.utcnow()
                    alert.is_active = False  # fire once

        db.commit()
        logger.info("Scraped %s — price: %.2f %s", product.name, result.price, result.currency)
        return {"status": "ok", "price": result.price}

    except Exception as exc:
        db.rollback()
        logger.error("Error scraping product %s: %s", product_id, exc)
        raise self.retry(exc=exc)
    finally:
        db.close()


@celery.task
def scrape_all_products():
    db = SessionLocal()
    try:
        ids = [r[0] for r in db.query(Product.id).filter(Product.is_active == True).all()]
    finally:
        db.close()

    for pid in ids:
        scrape_product.delay(pid)

    logger.info("Enqueued %d products for scraping", len(ids))
    return {"enqueued": len(ids)}
