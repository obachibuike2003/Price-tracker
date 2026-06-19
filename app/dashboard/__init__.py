from flask import Flask
from app.config import Config
from app.database import init_db
import app.models  # ensure ORM classes are registered before create_all


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.secret_key = Config.SECRET_KEY

    init_db()

    from app.dashboard.routes import bp
    app.register_blueprint(bp)

    return app
