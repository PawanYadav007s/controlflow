from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import SalesOrder, Quotation
from datetime import datetime

sales_order_routes = Blueprint('sales_order_routes', __name__)

@sales_order_routes.route('/sales-orders')
def manage_sales_orders():
    sales_orders = SalesOrder.query.all()
    return render_template('sales_order/manage_sales_orders.html', sales_orders=sales_orders)

@sales_order_routes.route('/sales-orders/add', methods=['GET', 'POST'])
def add_sales_order():
    quotations = Quotation.query.filter_by(status='Accepted').all()
    if request.method == 'POST':
        quotation_id = request.form['quotation_id']
        so_date = datetime.strptime(request.form['so_date'], '%Y-%m-%d')
        project_name = request.form['project_name']
        project_details = request.form['project_details']
        approval_status = request.form['approval_status']
        payment_terms = request.form['payment_terms']
        delivery_schedule = datetime.strptime(request.form['delivery_schedule'], '%Y-%m-%d')

        sales_order = SalesOrder(
            quotation_id=quotation_id,
            so_date=so_date,
            project_name=project_name,
            project_details=project_details,
            approval_status=approval_status,
            payment_terms=payment_terms,
            delivery_schedule=delivery_schedule
        )

        db.session.add(sales_order)

        # Also update quotation status to Accepted
        quotation = Quotation.query.get(quotation_id)
        if quotation:
            quotation.status = 'Accepted'

        db.session.commit()
        flash('Sales Order created successfully', 'success')
        return redirect(url_for('sales_order_routes.manage_sales_orders'))

    return render_template('sales_order/add_sales_order.html', quotations=quotations)

@sales_order_routes.route('/sales-orders/edit/<int:id>', methods=['GET', 'POST'])
def edit_sales_order(id):
    sales_order = SalesOrder.query.get_or_404(id)
    quotations = Quotation.query.filter_by(status='Accepted').all()

    if request.method == 'POST':
        sales_order.quotation_id = request.form['quotation_id']
        sales_order.so_date = datetime.strptime(request.form['so_date'], '%Y-%m-%d')
        sales_order.project_name = request.form['project_name']
        sales_order.project_details = request.form['project_details']
        sales_order.approval_status = request.form['approval_status']
        sales_order.payment_terms = request.form['payment_terms']
        sales_order.delivery_schedule = datetime.strptime(request.form['delivery_schedule'], '%Y-%m-%d')

        db.session.commit()
        flash('Sales Order updated successfully', 'success')
        return redirect(url_for('sales_order_routes.manage_sales_orders'))

    return render_template('sales_order/edit_sales_order.html', sales_order=sales_order, quotations=quotations)


@sales_order_routes.route('/sales-orders/delete/<int:id>', methods=['post'])
def delete_sales_order(id):
    try:
        sales_order = SalesOrder.query.get_or_404(id)
        db.session.delete(sales_order)
        db.session.commit()
        flash('Sales Order deleted Successfully', 'success')
    except  Exception as e:
        db.session.rollback()
        flash(f'Error deleting sales order: {str(e)}', 'danger')
    return redirect(url_for('sales_order_routes.manage_sales_orders'))





 

# # Handle Delete Quotation
# @quotation_routes.route('/quotations/delete/<int:id>', methods=['POST'])
# def delete_quotation(id):
#     try:
#         quotation = Quotation.query.get_or_404(id)
#         db.session.delete(quotation)
#         db.session.commit()
#         flash('Quotation deleted successfully!', 'success')
#     except Exception as e:
#         db.session.rollback()
#         flash(f'Error deleting quotation: {str(e)}', 'danger')

#     return redirect(url_for('quotation_routes.manage_quotations'))