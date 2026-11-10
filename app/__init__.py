import os
from flask import Flask, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

def create_app(test_config=None):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-only-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost/sales_inventory"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    from app.models import User
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    from app.cli import init_db_command   
    app.cli.add_command(init_db_command)    
    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.master import master_bp
    from app.routes.orders import orders_bp
    from app.routes.reports import reports_bp
    from app.routes.imports import imports_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(master_bp, url_prefix="/admin")
    app.register_blueprint(orders_bp)
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(imports_bp, url_prefix="/admin")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    return app
