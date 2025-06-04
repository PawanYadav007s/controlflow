# app/routes/inventory_routes.py

from flask import Blueprint, render_template, request
from app import db
from app.models import Inventory, Material, Location

inventory_bp = Blueprint('inventory_routes', __name__)

@inventory_bp.route('/inventory/manage')
def manage_inventory():
    location_id = request.args.get('location_id', type=int)
    locations = Location.query.all()

    if location_id:
        inventory = Inventory.query.filter_by(location_id=location_id).all()
    else:
        inventory = Inventory.query.all()

    return render_template('inventory/manage_inventory.html',
                           inventory=inventory,
                           locations=locations,
                           selected_location=location_id)
