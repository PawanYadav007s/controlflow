from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import PurchaseOrder, SalesOrder, Material
from datetime import datetime

purchase_order_routes = Blueprint('purchase_order_routes', __name__)

@purchase_order_routes.route('/purchase-orders')
def manage_purchase_orders():
    try:
        purchase_orders = PurchaseOrder.query.all()
        return render_template('purchase_order/manage_purchase_orders.html', purchase_orders=purchase_orders)
    except Exception as e:
        flash(f"Error loading purchase orders: {str(e)}", "danger")
        return redirect(url_for('purchase_order_routes.manage_purchase_orders'))

@purchase_order_routes.route('/purchase-orders/create', methods=['GET', 'POST'])
def create_purchase_order():
    try:
        sales_orders = SalesOrder.query.all()
    except Exception as e:
        flash(f"Error loading sales orders: {str(e)}", "danger")
        sales_orders = []

    if request.method == 'POST':
        try:
            po_number = request.form['po_number']
            po_date = datetime.strptime(request.form['po_date'], "%Y-%m-%d")
            supplier_name = request.form['supplier_name']
            material_description = request.form['material_description']
            quantity = float(request.form['quantity'])
            unit_price = float(request.form['unit_price'])
            expected_delivery_date = request.form.get('expected_delivery_date')
            if expected_delivery_date:
                expected_delivery_date = datetime.strptime(expected_delivery_date, "%Y-%m-%d")
            else:
                expected_delivery_date = None
            sales_order_id = int(request.form['sales_order_id'])
            material_id = int(request.form['material_id'])

            new_po = PurchaseOrder(
                po_number=po_number,
                po_date=po_date,
                supplier_name=supplier_name,
                material_description=material_description,
                quantity=quantity,
                unit_price=unit_price,
                expected_delivery_date=expected_delivery_date,
                sales_order_id=sales_order_id,
                material_id=material_id
            )
            db.session.add(new_po)
            db.session.commit()
            flash('Purchase Order created successfully.', 'success')
            return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
        except Exception as e:
            db.session.rollback()
            if "duplicate key value" in str(e):
                flash("PO number already exists. Please use a different one.", "danger")
            else:
                flash("An error occurred while creating the purchase order.", "danger")


    try:
        materials = Material.query.all()
    except Exception as e:
        flash(f"Error loading materials: {str(e)}", "danger")
        materials = []

    return render_template('purchase_order/create_purchase_order.html', sales_orders=sales_orders, materials=materials)

@purchase_order_routes.route('/purchase-orders/edit/<int:id>', methods=['GET', 'POST'])
def edit_purchase_order(id):
    try:
        purchase_order = PurchaseOrder.query.get_or_404(id)
    except Exception as e:
        flash(f"Purchase Order not found: {str(e)}", "danger")
        return redirect(url_for('purchase_order_routes.manage_purchase_orders'))

    try:
        sales_orders = SalesOrder.query.all()
    except Exception as e:
        flash(f"Error loading sales orders: {str(e)}", "danger")
        sales_orders = []

    if request.method == 'POST':
        try:
            purchase_order.po_number = request.form['po_number']
            purchase_order.po_date = datetime.strptime(request.form['po_date'], "%Y-%m-%d")
            purchase_order.supplier_name = request.form['supplier_name']
            purchase_order.material_description = request.form['material_description']
            purchase_order.quantity = float(request.form['quantity'])
            purchase_order.unit_price = float(request.form['unit_price'])
            purchase_order.material_id = int(request.form['material_id'])
            purchase_order.total_price = purchase_order.quantity * purchase_order.unit_price

            expected_delivery_date = request.form.get('expected_delivery_date')
            if expected_delivery_date:
                purchase_order.expected_delivery_date = datetime.strptime(expected_delivery_date, "%Y-%m-%d")
            else:
                purchase_order.expected_delivery_date = None

            purchase_order.status = request.form['status']
            purchase_order.sales_order_id = int(request.form['sales_order_id'])

            db.session.commit()
            flash('Purchase Order updated successfully.', 'success')
            return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')

    try:
        materials = Material.query.all()
    except Exception as e:
        flash(f"Error loading materials: {str(e)}", "danger")
        materials = []

    return render_template('purchase_order/edit_purchase_order.html', purchase_order=purchase_order, sales_orders=sales_orders, materials=materials)

@purchase_order_routes.route('/purchase-orders/delete/<int:id>', methods=['POST'])
def delete_purchase_order(id):
    try:
        purchase_order = PurchaseOrder.query.get_or_404(id)
        db.session.delete(purchase_order)
        db.session.commit()
        flash('Purchase Order deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting purchase order: {str(e)}', 'danger')

    return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
