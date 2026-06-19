from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from sqlalchemy import desc

from app.database import SessionLocal
from app.models import Product, PriceHistory, Alert
from app.scrapers import get_scraper, SCRAPERS

bp = Blueprint("dashboard", __name__)


def _db():
    return SessionLocal()


# ------------------------------------------------------------------ #
# Pages
# ------------------------------------------------------------------ #

@bp.route("/")
def index():
    db = _db()
    try:
        products = (
            db.query(Product)
            .filter(Product.is_active == True)
            .order_by(desc(Product.updated_at))
            .all()
        )
        stats = {
            "total": len(products),
            "with_drop": sum(1 for p in products if p.price_drop_pct > 0),
        }
        return render_template("index.html", products=products, stats=stats)
    finally:
        db.close()


@bp.route("/product/<int:product_id>")
def product_detail(product_id):
    db = _db()
    try:
        product = db.get(Product, product_id)
        if not product:
            abort(404)
        alerts = db.query(Alert).filter(Alert.product_id == product_id).all()
        return render_template("product_detail.html", product=product, alerts=alerts)
    finally:
        db.close()


@bp.route("/add", methods=["GET", "POST"])
def add_product():
    stores = [cls.store_name for cls in SCRAPERS]
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        category = request.form.get("category", "").strip()

        if not url:
            flash("URL is required.", "error")
            return render_template("add_product.html", stores=stores)

        try:
            scraper = get_scraper(url)
        except ValueError:
            flash("Unsupported store. Currently supporting: Amazon, Best Buy, Newegg.", "error")
            return render_template("add_product.html", stores=stores)

        result = scraper.scrape(url)
        if result is None:
            flash("Could not fetch product data. Check the URL and try again.", "error")
            return render_template("add_product.html", stores=stores)

        db = _db()
        try:
            product = Product(
                name=result.name,
                url=url,
                store=result.store,
                image_url=result.image_url,
                category=category or None,
            )
            db.add(product)
            db.flush()
            db.add(PriceHistory(
                product_id=product.id,
                price=result.price,
                currency=result.currency,
                in_stock=result.in_stock,
            ))
            db.commit()
            flash(f"Now tracking: {result.name}", "success")
            return redirect(url_for("dashboard.product_detail", product_id=product.id))
        finally:
            db.close()

    return render_template("add_product.html", stores=stores)


@bp.route("/product/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    db = _db()
    try:
        product = db.get(Product, product_id)
        if product:
            product.is_active = False
            db.commit()
            flash(f"Stopped tracking: {product.name}", "info")
    finally:
        db.close()
    return redirect(url_for("dashboard.index"))


@bp.route("/product/<int:product_id>/refresh", methods=["POST"])
def refresh_product(product_id):
    from app.tasks.scrape_tasks import scrape_product
    scrape_product.delay(product_id)
    flash("Refresh enqueued — results will appear shortly.", "info")
    return redirect(url_for("dashboard.product_detail", product_id=product_id))


@bp.route("/alert/add", methods=["POST"])
def add_alert():
    product_id = request.form.get("product_id", type=int)
    email = request.form.get("email", "").strip()
    target_price = request.form.get("target_price", type=float)

    if not all([product_id, email, target_price]):
        flash("All fields are required.", "error")
        return redirect(url_for("dashboard.product_detail", product_id=product_id))

    db = _db()
    try:
        db.add(Alert(product_id=product_id, email=email, target_price=target_price))
        db.commit()
        flash(f"Alert set: notify {email} when price drops below ${target_price:.2f}", "success")
    finally:
        db.close()

    return redirect(url_for("dashboard.product_detail", product_id=product_id))


@bp.route("/alert/<int:alert_id>/delete", methods=["POST"])
def delete_alert(alert_id):
    db = _db()
    try:
        alert = db.get(Alert, alert_id)
        if alert:
            product_id = alert.product_id
            db.delete(alert)
            db.commit()
            return redirect(url_for("dashboard.product_detail", product_id=product_id))
    finally:
        db.close()
    return redirect(url_for("dashboard.index"))


# ------------------------------------------------------------------ #
# API (used by Chart.js)
# ------------------------------------------------------------------ #

@bp.route("/api/product/<int:product_id>/history")
def api_price_history(product_id):
    db = _db()
    try:
        rows = (
            db.query(PriceHistory)
            .filter(PriceHistory.product_id == product_id)
            .order_by(PriceHistory.scraped_at)
            .all()
        )
        return jsonify([r.to_dict() for r in rows])
    finally:
        db.close()


@bp.route("/api/products")
def api_products():
    db = _db()
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
        return jsonify([p.to_dict() for p in products])
    finally:
        db.close()
