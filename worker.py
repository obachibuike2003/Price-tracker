from app.tasks.scrape_tasks import celery  # noqa: F401 — Celery needs this import

# Run with:
#   celery -A worker.celery worker --loglevel=info
#   celery -A worker.celery beat   --loglevel=info
