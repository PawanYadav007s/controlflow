from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow

db = SQLAlchemy()
ma = Marshmallow()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    db.init_app(app)
    ma.init_app(app)

    from .routes.base_routes import base_routes
    from .routes.quotation_routes import quotation_routes
    from app.routes.sales_order_routes import sales_order_routes
    from app.routes.purchase_order_routes import purchase_order_routes



    app.register_blueprint(base_routes)
    app.register_blueprint(quotation_routes)
    app.register_blueprint(sales_order_routes)
    app.register_blueprint(purchase_order_routes)
   



    with app.app_context():
        from . import models
        db.create_all()

    return app
