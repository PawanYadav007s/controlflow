from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.models import ProductionOrder, MaterialIssue, WasteRecord, InventoryTransaction, SalesOrder, Material, Inventory
from datetime import datetime, timezone

production_bp = Blueprint('production', __name__, url_prefix='/production')


def record_inventory_transaction(material_id, quantity, weight, movement_type, reference, performed_by):
    try:
        tx = InventoryTransaction(
            material_id=material_id,
            quantity=quantity,
            weight=weight,
            movement_type=movement_type,
            reference=reference,
            performed_by=performed_by,
            timestamp=datetime.now(timezone.utc)
        )
        db.session.add(tx)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to record inventory transaction: {str(e)}", "danger")


def delete_inventory_transaction(reference_type, reference_id):
    try:
        tx = InventoryTransaction.query.filter_by(reference=reference_type + ':' + str(reference_id)).first()
        if tx:
            db.session.delete(tx)
            db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete inventory transaction: {str(e)}", "danger")



@production_bp.route('/')
def production_orders():
    try:
        sales_order_id = request.args.get('sales_order_id', type=int)
        query = ProductionOrder.query.order_by(ProductionOrder.start_date.desc())

        if sales_order_id:
            sales_order = SalesOrder.query.get(sales_order_id)
            if sales_order:
                query = query.filter_by(sales_order_id=sales_order.id)
            else:
                flash(f"No Sales Order found with ID '{sales_order_id}'", 'warning')
                query = query.filter_by(sales_order_id=None)

        orders = query.all()
        sales_orders = SalesOrder.query.all()

        return render_template(
            'production/production_orders.html',
            orders=orders,
            sales_orders=sales_orders,
            selected_sales_order=sales_order_id,
            active_tab='orders'
        )
    except Exception as e:
        flash(f"Error loading production orders: {str(e)}", "danger")
        return redirect(url_for('production.production_orders'))



@production_bp.route('/create', methods=['GET', 'POST'])
def create_production_order():
    if request.method == 'POST':
        try:
            # ✅ Get the sales order ID directly
            sales_order_id = request.form.get('sales_order_id', type=int)
            production_code = request.form.get('production_code')
            material_id = request.form.get('material_id', type=int)
            planned_quantity = request.form.get('planned_quantity', type=float)
            start_date = request.form.get('start_date')
            end_date = request.form.get('end_date')
            status = request.form.get('status', 'Planned')

            # ✅ Check for required fields
            if not (sales_order_id and production_code and material_id and planned_quantity):
                flash("Please fill all required fields.", "warning")
                return redirect(url_for('production.create_production_order'))

            # ✅ Validate the sales order exists
            sales_order = SalesOrder.query.get(sales_order_id)
            if not sales_order:
                flash("Sales Order not found.", "danger")
                return redirect(url_for('production.create_production_order'))

            # ✅ Create Production Order
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

        except Exception as e:
            db.session.rollback()
            flash(f"Error creating production order: {str(e)}", "danger")
            return redirect(url_for('production.create_production_order'))

    # ✅ Pass all sales orders and materials to the form
    sales_orders = SalesOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_production_order.html', sales_orders=sales_orders, materials=materials)



@production_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_production_order(id):
    po = ProductionOrder.query.get_or_404(id)
    if request.method == 'POST':
        try:
            sales_order_id = request.form.get('sales_order_id', type=int)
            sales_order = SalesOrder.query.get(sales_order_id)
            if not sales_order:
                flash(f"Sales Order with ID '{sales_order_id}' not found.", "danger")
                return redirect(url_for('production.edit_production_order', id=id))

            po.sales_order_id = sales_order_id
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
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating production order: {str(e)}", "danger")
            return redirect(url_for('production.edit_production_order', id=id))

    sales_orders = SalesOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_production_order.html', po=po, sales_orders=sales_orders, materials=materials)



@production_bp.route('/<int:id>/delete', methods=['POST'])
def delete_production_order(id):
    try:
        po = ProductionOrder.query.get_or_404(id)
        db.session.delete(po)
        db.session.commit()
        flash("Production Order deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting production order: {str(e)}", "danger")
    return redirect(url_for('production.production_orders'))


@production_bp.route('/material_issues')
def material_issues():
    try:
        production_order_id = request.args.get('production_order_id', type=int)
        query = MaterialIssue.query.order_by(MaterialIssue.issue_date.desc())
        if production_order_id:
            query = query.filter_by(production_order_id=production_order_id)
        issues = query.all()

        # Load related inventory transactions for each issue
        transactions_map = {}
        for mi in issues:
            ref = f"Material Issue ID-{mi.id}"
            txns = InventoryTransaction.query.filter_by(reference=ref).order_by(InventoryTransaction.timestamp).all()
            transactions_map[mi.id] = txns

        production_orders = ProductionOrder.query.all()
        materials = Material.query.all()
        return render_template(
            'production/material_issues.html',
            issues=issues,
            production_orders=production_orders,
            materials=materials,
            selected_production_order=production_order_id,
            transactions_map=transactions_map
        )
    except Exception as e:
        flash(f"Error loading material issues: {str(e)}", "danger")
        return redirect(url_for('production.material_issues'))


@production_bp.route('/material_issues/create', methods=['GET', 'POST'])
def create_material_issue():
    if request.method == 'POST':
        try:
            production_order_id = request.form.get('production_order_id', type=int)
            material_id = request.form.get('material_id', type=int)
            issued_quantity = request.form.get('issued_quantity', type=float)
            issued_weight = request.form.get('issued_weight', type=float, default=0)
            issued_by = request.form.get('issued_by')

            if not (production_order_id and material_id and issued_quantity):
                flash("Please fill all required fields.", "warning")
                return redirect(url_for('production.create_material_issue'))

            inv = Inventory.query.filter_by(material_id=material_id).first()
            if not inv:
                flash("Inventory record not found for the material.", "danger")
                return redirect(url_for('production.create_material_issue'))

            if inv.quantity < issued_quantity:
                flash("Insufficient stock in inventory.", "danger")
                return redirect(url_for('production.create_material_issue'))

            mi = MaterialIssue(
                production_order_id=production_order_id,
                material_id=material_id,
                issued_quantity=issued_quantity,
                issued_weight=issued_weight or 0.0,
                issued_by=issued_by,
                issue_date=datetime.now(timezone.utc)
            )
            db.session.add(mi)
            inv.quantity -= issued_quantity
            db.session.flush()  # ensures mi.id is available

            record_inventory_transaction(
                material_id,
                issued_quantity,
                issued_weight,
                'OUT',
                f"Material Issue ID-{mi.id}",
                issued_by
            )

            db.session.commit()

            flash("Material Issue recorded successfully.", "success")
            return redirect(url_for('production.material_issues'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating material issue: {str(e)}", "danger")
            return redirect(url_for('production.create_material_issue'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_material_issue.html', production_orders=production_orders, materials=materials)



@production_bp.route('/material_issues/<int:id>/edit', methods=['GET', 'POST'])
def edit_material_issue(id):
    mi = MaterialIssue.query.get_or_404(id)

    if request.method == 'POST':
        try:
            old_quantity = mi.issued_quantity
            old_material_id = mi.material_id

            # Parse new values
            mi.production_order_id = request.form.get('production_order_id', type=int)
            mi.material_id = request.form.get('material_id', type=int)
            mi.issued_quantity = request.form.get('issued_quantity', type=float)
            mi.issued_weight = request.form.get('issued_weight', type=float, default=0)
            mi.issued_by = request.form.get('issued_by')

            issue_date_str = request.form.get('issue_date')
            if issue_date_str:
                mi.issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d')

            new_quantity = mi.issued_quantity
            new_material_id = mi.material_id

            inv_old = Inventory.query.filter_by(material_id=old_material_id).first()
            inv_new = Inventory.query.filter_by(material_id=new_material_id).first()

            # Handle inventory adjustments
            if old_material_id == new_material_id:
                diff = new_quantity - old_quantity
                if diff > 0 and inv_old and inv_old.quantity < diff:
                    flash("Insufficient stock in inventory for increased quantity.", "danger")
                    return redirect(url_for('production.edit_material_issue', id=id))
                if inv_old:
                    inv_old.quantity -= diff
            else:
                if inv_old:
                    inv_old.quantity += old_quantity
                if inv_new:
                    if inv_new.quantity < new_quantity:
                        flash("Insufficient stock in inventory for new material.", "danger")
                        return redirect(url_for('production.edit_material_issue', id=id))
                    inv_new.quantity -= new_quantity

            # Delete old inventory transaction
            delete_inventory_transaction('MaterialIssue', mi.id)

            # Record new transaction
            reference = f"MaterialIssue:{mi.id}"
            record_inventory_transaction(
                material_id=new_material_id,
                quantity=new_quantity,
                weight=mi.issued_weight,
                movement_type='OUT',
                reference=reference,
                performed_by=mi.issued_by
            )

            db.session.commit()
            flash("Material Issue updated.", "success")
            return redirect(url_for('production.material_issues'))

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating material issue: {str(e)}", "danger")
            return redirect(url_for('production.edit_material_issue', id=id))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_material_issue.html', issue=mi, production_orders=production_orders, materials=materials)


@production_bp.route('/material_issues/<int:id>/delete', methods=['POST'])
def delete_material_issue(id):
    try:
        mi = MaterialIssue.query.get_or_404(id)

        # Restore inventory
        inv = Inventory.query.filter_by(material_id=mi.material_id).first()
        if inv:
            inv.quantity += mi.issued_quantity

        # Delete inventory transaction
        delete_inventory_transaction('MaterialIssue', mi.id)

        db.session.delete(mi)
        db.session.commit()
        flash("Material Issue deleted and inventory updated.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting material issue: {str(e)}", "danger")

    return redirect(url_for('production.material_issues'))



@production_bp.route('/waste_records')
def waste_records():
    try:
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
    except Exception as e:
        flash(f"Error loading waste records: {str(e)}", "danger")
        return redirect(url_for('production.waste_records'))


@production_bp.route('/waste_records/create', methods=['GET', 'POST'])
def create_waste_record():
    if request.method == 'POST':
        try:
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
                recorded_on=datetime.now(timezone.utc)
            )
            db.session.add(wr)
            db.session.commit()
            flash("Waste record added.", "success")
            return redirect(url_for('production.waste_records'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating waste record: {str(e)}", "danger")
            return redirect(url_for('production.create_waste_record'))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/create_waste_record.html', production_orders=production_orders, materials=materials)


@production_bp.route('/waste_records/<int:id>/edit', methods=['GET', 'POST'])
def edit_waste_record(id):
    wr = WasteRecord.query.get_or_404(id)
    if request.method == 'POST':
        try:
            wr.production_order_id = request.form.get('production_order_id', type=int)
            wr.material_id = request.form.get('material_id', type=int)
            wr.waste_quantity = request.form.get('waste_quantity', type=float)
            wr.waste_weight = request.form.get('waste_weight', type=float, default=0)
            wr.reason = request.form.get('reason')
            db.session.commit()
            flash("Waste record updated.", "success")
            return redirect(url_for('production.waste_records'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating waste record: {str(e)}", "danger")
            return redirect(url_for('production.edit_waste_record', id=id))

    production_orders = ProductionOrder.query.all()
    materials = Material.query.all()
    return render_template('production/edit_waste_record.html', wr=wr, production_orders=production_orders, materials=materials)


@production_bp.route('/waste_records/<int:id>/delete', methods=['POST'])
def delete_waste_record(id):
    try:
        wr = WasteRecord.query.get_or_404(id)
        db.session.delete(wr)
        db.session.commit()
        flash("Waste record deleted.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting waste record: {str(e)}", "danger")
    return redirect(url_for('production.waste_records'))
