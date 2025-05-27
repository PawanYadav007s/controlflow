from flask import Blueprint, render_template

base_routes = Blueprint('base_routes', __name__)

@base_routes.route('/')
def index():
    return render_template('index.html')

@base_routes.route('/quotation')
def quotation():
    return render_template('quotation.html')

@base_routes.route('/sales-order')
def sales_order():
    return render_template('sales_order.html')

@base_routes.route('/purchase-order')
def purchase_order():
    return render_template('purchase_order.html')

@base_routes.route('/material-receipt')
def material_receipt():
    return render_template('material_receipt.html')

@base_routes.route('/inventory')
def inventory():
    return render_template('inventory.html')

@base_routes.route('/production')
def production():
    return render_template('production.html')

@base_routes.route('/login')
def login():
    return render_template('login.html')
