from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import PurchaseOrder, SalesOrder

purchase_order_routes = Blueprint('purchase_order_routes', __name__)

@purchase_order_routes.route('/purchase-orders')
def manage_purchase_orders():
    purchase_orders = PurchaseOrder.query.all()
    return render_template('purchase_order/manage_purchase_orders.html', purchase_orders=purchase_orders)

@purchase_order_routes.route('/purchase-orders/create', methods=['GET', 'POST'])
def create_purchase_order():
    sales_orders = SalesOrder.query.all()
    if request.method == 'POST':
        try:
            po_number = request.form['po_number']
            po_date = request.form['po_date']
            vendor_name = request.form['vendor_name']
            total_amount = request.form['total_amount']
            status = request.form['status']
            sales_order_id = request.form['sales_order_id']

            new_po = PurchaseOrder(
                po_number=po_number,
                po_date=po_date,
                vendor_name=vendor_name,
                total_amount=total_amount,
                status=status,
                sales_order_id=sales_order_id
            )
            db.session.add(new_po)
            db.session.commit()
            flash('Purchase Order created successfully.', 'success')
            return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('purchase_order/create_purchase_order.html', sales_orders=sales_orders)

@purchase_order_routes.route('/purchase-orders/edit/<int:id>', methods=['GET', 'POST'])
def edit_purchase_order(id):
    purchase_order = PurchaseOrder.query.get_or_404(id)
    sales_orders = SalesOrder.query.all()
    if request.method == 'POST':
        try:
            purchase_order.po_number = request.form['po_number']
            purchase_order.po_date = request.form['po_date']
            purchase_order.vendor_name = request.form['vendor_name']
            purchase_order.total_amount = request.form['total_amount']
            purchase_order.status = request.form['status']
            purchase_order.sales_order_id = request.form['sales_order_id']

            db.session.commit()
            flash('Purchase Order updated successfully.', 'success')
            return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
    return render_template('purchase_order/edit_purchase_order.html', purchase_order=purchase_order, sales_orders=sales_orders)

@purchase_order_routes.route('/purchase-orders/delete/<int:id>', methods=['POST'])
def delete_purchase_order(id):
    purchase_order = PurchaseOrder.query.get_or_404(id)
    db.session.delete(purchase_order)
    db.session.commit()
    flash('Purchase Order deleted successfully.', 'success')
    return redirect(url_for('purchase_order_routes.manage_purchase_orders'))
