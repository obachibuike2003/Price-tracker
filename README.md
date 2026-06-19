# E-Commerce Price Tracker

A full-stack price tracking app that monitors product prices across multiple stores, alerts you when prices drop, and visualises history with interactive charts.

---

## Features

- **Multi-store scraping** — Amazon, Best Buy, Newegg (requests + Selenium fallback)
- **Price history** — every scrape logged to PostgreSQL
- **Price drop alerts** — email notifications when price hits your target
- **Interactive charts** — Chart.js line graphs with all-time low highlighted
- **Dashboard** — track Phones, Laptops, Gaming Consoles and more
- **Background workers** — Celery + Redis run scrapes automatically every N hours
- **Task monitor** — Flower UI to inspect queued/running tasks
- **Fully Dockerised** — one command to spin up the entire stack

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.12 |
| Web framework | Flask |
| Scraping | Selenium + BeautifulSoup4 |
| Database | PostgreSQL + SQLAlchemy |
| Task queue | Celery + Redis |
| Charts | Chart.js |
| Deployment | Docker + Docker Compose |

---

## Quick Start

### 1. Clone

```bash
git clone https://github.com/obachibuike2003/Price-tracker.git
cd Price-tracker
```

### 2. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in your details:

```env
SECRET_KEY=change-me-in-production

# Email alerts (Gmail App Password)
SMTP_USER=you@gmail.com
SMTP_PASSWORD=xxxx xxxx xxxx xxxx
ALERT_FROM_EMAIL=you@gmail.com

# How often to scrape (hours)
SCRAPE_INTERVAL_HOURS=6
```

### 3. Run with Docker

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Dashboard | http://localhost:5000 |
| Task monitor (Flower) | http://localhost:5555 |

### 4. Run locally (no Docker)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt

# Start Flask dashboard
python main.py

# In a separate terminal — start Celery worker
celery -A worker.celery worker --loglevel=info

# In a third terminal — start Celery Beat scheduler
celery -A worker.celery beat --loglevel=info
```

---

## Project Structure

```
price-tracker/
├── docker-compose.yml          # Full stack: web, worker, beat, flower, db, redis
├── Dockerfile
├── requirements.txt
├── .env.example
├── main.py                     # Flask entrypoint
├── worker.py                   # Celery entrypoint
├── migrations/
│   └── 001_init.sql            # DB schema
└── app/
    ├── config.py               # Env-based configuration
    ├── database.py             # SQLAlchemy engine + session
    ├── models.py               # Product, PriceHistory, Alert
    ├── scrapers/
    │   ├── base.py             # BaseScraper (requests → Selenium fallback)
    │   ├── amazon.py
    │   ├── bestbuy.py
    │   └── newegg.py
    ├── tasks/
    │   └── scrape_tasks.py     # Celery tasks + Beat schedule
    ├── notifier/
    │   └── alerts.py           # SMTP email notifications
    └── dashboard/
        ├── routes.py           # Flask routes + JSON API
        ├── templates/          # Jinja2 HTML templates
        └── static/             # CSS + JS
```

---

## Supported Stores

| Store | URL pattern |
|---|---|
| Amazon | amazon.com |
| Best Buy | bestbuy.com |
| Newegg | newegg.com |

---

## How to Track a Product

1. Open the dashboard at **http://localhost:5000**
2. Click **"+ Track Product"**
3. Paste any product URL from Amazon, Best Buy, or Newegg
4. Select a category (Phones, Laptops, Gaming Consoles, etc.)
5. Click **"Fetch & Track"** — the current price is scraped immediately
6. On the product page, set a **Price Drop Alert** with your email and target price

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | postgresql://... | PostgreSQL connection string |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection string |
| `SECRET_KEY` | — | Flask session secret (change in prod) |
| `SMTP_HOST` | smtp.gmail.com | SMTP server |
| `SMTP_PORT` | 587 | SMTP port |
| `SMTP_USER` | — | Email address to send alerts from |
| `SMTP_PASSWORD` | — | Gmail App Password |
| `SCRAPE_INTERVAL_HOURS` | 6 | How often Celery scrapes all products |
| `HEADLESS` | true | Run Chrome headless (set false to debug) |
| `REQUEST_DELAY_SECONDS` | 2 | Delay between requests to avoid rate limiting |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Dashboard — all tracked products |
| GET | `/product/<id>` | Product detail + price chart |
| POST | `/add` | Add a new product URL to track |
| POST | `/product/<id>/refresh` | Trigger an immediate scrape |
| POST | `/product/<id>/delete` | Stop tracking a product |
| POST | `/alert/add` | Add a price drop alert |
| GET | `/api/products` | JSON list of all products |
| GET | `/api/product/<id>/history` | JSON price history (used by Chart.js) |

---

## Example Products to Track

- iPhone 16 Pro — amazon.com
- Sony PlayStation 5 — bestbuy.com
- NVIDIA RTX 4070 — newegg.com
- Dell XPS 15 Laptop — bestbuy.com

---

## License

MIT
