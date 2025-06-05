from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate

db = SQLAlchemy()
ma = Marshmallow()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    ma.init_app(app)
    migrate.init_app(app, db)

    # Import blueprints
    from .routes.base_routes import base_routes
    from .routes.quotation_routes import quotation_routes
    from .routes.sales_order_routes import sales_order_routes
    from .routes.purchase_order_routes import purchase_order_routes
    from .routes.material_receipt_routes import material_receipt_routes
    from .routes.material_routes import material_bp
    from .routes.location_routes import location_routes
    from .routes.inventory_routes import inventory_bp
    from .routes.production import production_bp  # ✅ Enabled production routes

    # Register blueprints
    app.register_blueprint(base_routes)
    app.register_blueprint(quotation_routes)
    app.register_blueprint(sales_order_routes)
    app.register_blueprint(purchase_order_routes)
    app.register_blueprint(material_receipt_routes)
    app.register_blueprint(material_bp)
    app.register_blueprint(location_routes)
    app.register_blueprint(inventory_bp)
    app.register_blueprint(production_bp)  # ✅ Register production routes

    with app.app_context():
        from . import models
        db.create_all()

    return app
