# app/routes/inventory_routes.py

from flask import Blueprint, render_template, request
from app import db
from app.models import Inventory, Location, InventoryTransaction, WasteRecord
from sqlalchemy import func

inventory_bp = Blueprint('inventory_routes', __name__)

@inventory_bp.route('/inventory/manage')
def manage_inventory():
    location_id = request.args.get('location_id', type=int)
    locations = Location.query.all()

    if location_id:
        inventory = Inventory.query.filter_by(location_id=location_id).all()
    else:
        inventory = Inventory.query.all()

    # Sum of OUT movements per material (consumed)
    consumed_data = (
        db.session.query(
            InventoryTransaction.material_id,
            func.sum(InventoryTransaction.quantity).label('total_consumed')
        )
        .filter(InventoryTransaction.movement_type == 'OUT')
        .group_by(InventoryTransaction.material_id)
        .all()
    )
    consumed_map = {c.material_id: c.total_consumed for c in consumed_data}

    # Sum waste per material from WasteRecord if you have that table, else zero
    waste_data = (
        db.session.query(
            WasteRecord.material_id,
            func.sum(WasteRecord.waste_quantity).label('total_waste')

        )
        .group_by(WasteRecord.material_id)
        .all()
    )
    waste_map = {w.material_id: w.total_waste for w in waste_data}

    return render_template(
        'inventory/manage_inventory.html',
        inventory=inventory,
        locations=locations,
        selected_location=location_id,
        consumed_map=consumed_map,
        waste_map=waste_map
    )
