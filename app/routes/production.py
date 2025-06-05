from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import ProductionOrder, MaterialIssue, WasteRecord, InventoryTransaction, SalesOrder, Material,Inventory
from datetime import datetime,timezone

production_bp = Blueprint('production', __name__, url_prefix='/production')


# Helper function to record inventory transactions
def record_inventory_transaction(material_id, quantity, weight, movement_type, reference, performed_by):
    tx = InventoryTransaction(
        material_id=material_id,
        quantity=quantity,
        weight=weight,
        movement_type=movement_type,
        reference=reference,
        performed_by=performed_by,
        timestamp= datetime.now(timezone.utc)
    )
    db.session.add(tx)
    db.session.commit()


# === Production Orders ===

@production_bp.route('/')
def production_orders():
    """List all production orders with optional filters."""
    sales_order_id = request.args.get('sales_order_id', type=int)
    query = ProductionOrder.query.order_by(ProductionOrder.start_date.desc())
    if sales_order_id:
        query = query.filter_by(sales_order_id=sales_order_id)
    orders = query.all()

    # Fetch related sales orders for filter dropdown in template
    sales_orders = SalesOrder.query.all()
    return render_template('production/production_orders.html', orders=orders, sales_orders=sales_orders, selected_sales_order=sales_order_id)


@production_bp.route('/create', methods=['GET', 'POST'])
def create_production_order():
    if request.method == 'POST':
        sales_order_id = request.form.get('sales_order_id', type=int)
        production_code = request.form.get('production_code')
        material_id = request.form.get('material_id', type=int)
        planned_quantity = request.form.get('planned_quantity', type=float)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        status = request.form.get('status', 'Planned')

        # Basic validation
        if not (sales_order_id and production_code and material_id and planned_quantity):
            flash("Please fill all required fields.", "warning")
            return redirect(url_for('production.create_production_order'))

        po = ProductionOrder(
            sales_order_id=sales_order_id,
            production_code=production_code,
            material_id=material_id,
            planned_quantity=planned_quantity,
            start_date=datetime.strptime(start_date, '%Y-%m-%d') if start_date else None,
            end_date=datetime.strptime(end_date, '%Y-%m-%d') if end_date else None,
            status=status
        )
        db.session.add(po)
        db.session.commit()
        flash("Production Order created successfully.", "success")
        return redirect(url_for('production.production_orders'))

    sales_orders = SalesOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_production_order.html', sales_orders=sales_orders, materials=materials)


@production_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_production_order(id):
    po = ProductionOrder.query.get_or_404(id)

    if request.method == 'POST':
        po.sales_order_id = request.form.get('sales_order_id', type=int)
        po.production_code = request.form.get('production_code')
        po.material_id = request.form.get('material_id', type=int)
        po.planned_quantity = request.form.get('planned_quantity', type=float)
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        po.status = request.form.get('status', 'Planned')

        po.start_date = datetime.strptime(start_date, '%Y-%m-%d') if start_date else None
        po.end_date = datetime.strptime(end_date, '%Y-%m-%d') if end_date else None

        db.session.commit()
        flash("Production Order updated successfully.", "success")
        return redirect(url_for('production.production_orders'))

    sales_orders = SalesOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_production_order.html', po=po, sales_orders=sales_orders, materials=materials)


@production_bp.route('/<int:id>/delete', methods=['POST'])
def delete_production_order(id):
    po = ProductionOrder.query.get_or_404(id)
    db.session.delete(po)
    db.session.commit()
    flash("Production Order deleted.", "success")
    return redirect(url_for('production.production_orders'))


# === Material Issues ===

@production_bp.route('/material_issues')
def material_issues():
    """List all material issues with optional filter by production order."""
    production_order_id = request.args.get('production_order_id', type=int)
    query = MaterialIssue.query.order_by(MaterialIssue.issue_date.desc())
    if production_order_id:
        query = query.filter_by(production_order_id=production_order_id)
    issues = query.all()

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/material_issues.html', issues=issues,
                           production_orders=production_orders, materials=materials,
                           selected_production_order=production_order_id)


@production_bp.route('/material_issues/create', methods=['GET', 'POST'])
def create_material_issue():
    if request.method == 'POST':
        production_order_id = request.form.get('production_order_id', type=int)
        material_id = request.form.get('material_id', type=int)
        issued_quantity = request.form.get('issued_quantity', type=float)
        issued_weight = request.form.get('issued_weight', type=float, default=0)
        issued_by = request.form.get('issued_by')

        if not (production_order_id and material_id and issued_quantity):
            flash("Please fill all required fields.", "warning")
            return redirect(url_for('production.create_material_issue'))

        mi = MaterialIssue(
            production_order_id=production_order_id,
            material_id=material_id,
            issued_quantity=issued_quantity,
            issued_weight=issued_weight or 0.0,
            issued_by=issued_by,
            issue_date= datetime.now(timezone.utc)
        )
        db.session.add(mi)
        # Reduce inventory quantity accordingly
        inv = db.session.query(Inventory).filter_by(material_id=material_id).first()
        if inv:
            if inv.quantity < issued_quantity:
                flash("Insufficient stock in inventory.", "danger")
                return redirect(url_for('production.create_material_issue'))
            inv.quantity -= issued_quantity
            db.session.commit()
        else:
            flash("Inventory record not found for the material.", "danger")
            return redirect(url_for('production.create_material_issue'))

        # Record inventory transaction (OUT)
        record_inventory_transaction(material_id, issued_quantity, issued_weight, 'OUT', f"Material Issue for PO-{production_order_id}", issued_by)

        flash("Material Issue recorded successfully.", "success")
        return redirect(url_for('production.material_issues'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_material_issue.html', production_orders=production_orders, materials=materials)


@production_bp.route('/material_issues/<int:id>/edit', methods=['GET', 'POST'])
def edit_material_issue(id):
    mi = MaterialIssue.query.get_or_404(id)

    if request.method == 'POST':
        old_quantity = mi.issued_quantity
        old_material_id = mi.material_id

        mi.production_order_id = request.form.get('production_order_id', type=int)
        mi.material_id = request.form.get('material_id', type=int)
        mi.issued_quantity = request.form.get('issued_quantity', type=float)
        mi.issued_weight = request.form.get('issued_weight', type=float, default=0)
        mi.issued_by = request.form.get('issued_by')

        new_quantity = mi.issued_quantity
        new_material_id = mi.material_id

        # Adjust inventory quantity based on difference
        inv_old = db.session.query(Inventory).filter_by(material_id=old_material_id).first()
        inv_new = db.session.query(Inventory).filter_by(material_id=new_material_id).first()

        if old_material_id == new_material_id:
            # Same material, adjust by difference
            diff = new_quantity - old_quantity
            if diff > 0 and inv_old and inv_old.quantity < diff:
                flash("Insufficient stock in inventory for increased quantity.", "danger")
                return redirect(url_for('production.edit_material_issue', id=id))
            if inv_old:
                inv_old.quantity -= diff
        else:
            # Different material, restore old quantity and deduct new
            if inv_old:
                inv_old.quantity += old_quantity
            if inv_new:
                if inv_new.quantity < new_quantity:
                    flash("Insufficient stock in inventory for new material.", "danger")
                    return redirect(url_for('production.edit_material_issue', id=id))
                inv_new.quantity -= new_quantity

        db.session.commit()

        # Ideally, record inventory transactions for changes (skipped here for brevity)

        db.session.commit()
        flash("Material Issue updated.", "success")
        return redirect(url_for('production.material_issues'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_material_issue.html', mi=mi, production_orders=production_orders, materials=materials)


@production_bp.route('/material_issues/<int:id>/delete', methods=['POST'])
def delete_material_issue(id):
    mi = MaterialIssue.query.get_or_404(id)

    # Restore inventory quantity
    inv = db.session.query(Inventory).filter_by(material_id=mi.material_id).first()
    if inv:
        inv.quantity += mi.issued_quantity

    db.session.delete(mi)
    db.session.commit()
    flash("Material Issue deleted and inventory updated.", "success")
    return redirect(url_for('production.material_issues'))


# === Waste Records ===

@production_bp.route('/waste_records')
def waste_records():
    """List all waste records with filter option by production order."""
    production_order_id = request.args.get('production_order_id', type=int)
    query = WasteRecord.query.order_by(WasteRecord.recorded_on.desc())
    if production_order_id:
        query = query.filter_by(production_order_id=production_order_id)
    waste_records = query.all()


    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/waste_records.html', waste_records=waste_records,
                       production_orders=production_orders, materials=materials,
                       selected_production_order=production_order_id)



@production_bp.route('/waste_records/create', methods=['GET', 'POST'])
def create_waste_record():
    if request.method == 'POST':
        production_order_id = request.form.get('production_order_id', type=int)
        material_id = request.form.get('material_id', type=int)
        waste_quantity = request.form.get('waste_quantity', type=float)
        waste_weight = request.form.get('waste_weight', type=float, default=0)
        reason = request.form.get('reason')

        if not (production_order_id and material_id and waste_quantity):
            flash("Please fill all required fields.", "warning")
            return redirect(url_for('production.create_waste_record'))

        wr = WasteRecord(
            production_order_id=production_order_id,
            material_id=material_id,
            waste_quantity=waste_quantity,
            waste_weight=waste_weight or 0.0,
            reason=reason,
            recorded_on= datetime.now(timezone.utc)
        )
        db.session.add(wr)
        db.session.commit()
        flash("Waste record added.", "success")
        return redirect(url_for('production.waste_records'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_waste_record.html', production_orders=production_orders, materials=materials)


@production_bp.route('/waste_records/<int:id>/edit', methods=['GET', 'POST'])
def edit_waste_record(id):
    wr = WasteRecord.query.get_or_404(id)

    if request.method == 'POST':
        wr.production_order_id = request.form.get('production_order_id', type=int)
        wr.material_id = request.form.get('material_id', type=int)
        wr.waste_quantity = request.form.get('waste_quantity', type=float)
        wr.waste_weight = request.form.get('waste_weight', type=float, default=0)
        wr.reason = request.form.get('reason')
        db.session.commit()
        flash("Waste record updated.", "success")
        return redirect(url_for('production.waste_records'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_waste_record.html', wr=wr, production_orders=production_orders, materials=materials)


@production_bp.route('/waste_records/<int:id>/delete', methods=['POST'])
def delete_waste_record(id):
    wr = WasteRecord.query.get_or_404(id)
    db.session.delete(wr)
    db.session.commit()
    flash("Waste record deleted.", "success")
    return redirect(url_for('production.waste_records'))


# === API Endpoint to get materials by sales order (for frontend dynamic selection) ===

@production_bp.route('/materials/by_sales_order/<int:sales_order_id>')
def materials_by_sales_order(sales_order_id):
    # Assuming materials linked to sales order via ProductionOrder or PurchaseOrder
    # Let's get materials from production orders related to that sales order
    materials = Material.query.join(ProductionOrder, ProductionOrder.material_id == Material.id)\
        .filter(ProductionOrder.sales_order_id == sales_order_id).all()

    result = [{
        'id': m.id,
        'code': m.code,
        'name': m.name,
        'description': m.description,
        'category': m.category,
        'unit': m.unit
    } for m in materials]

    return jsonify(result)


# === API Endpoint to get production orders by sales order (for filtering) ===

@production_bp.route('/production_orders/by_sales_order/<int:sales_order_id>')
def production_orders_by_sales_order(sales_order_id):
    orders = ProductionOrder.query.filter_by(sales_order_id=sales_order_id).all()
    result = [{
        'id': o.id,
        'production_code': o.production_code,
        'material_id': o.material_id,
        'planned_quantity': o.planned_quantity,
        'start_date': o.start_date.strftime('%Y-%m-%d') if o.start_date else None,
        'end_date': o.end_date.strftime('%Y-%m-%d') if o.end_date else None,
        'status': o.status
    } for o in orders]
    return jsonify(result)
