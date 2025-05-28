from flask import Blueprint, render_template, redirect, url_for
from app.models import Quotation

base_routes = Blueprint('base_routes', __name__)

# Dashboard with live quotation stats
@base_routes.route('/')
def dashboard():
    total_quotations = Quotation.query.count()
    pending_quotations = Quotation.query.filter_by(status='Pending').count()
    accepted_quotations = Quotation.query.filter_by(status='Accepted').count()

    return render_template('index.html',
                           total_quotations=total_quotations,
                           pending_quotations=pending_quotations,
                           accepted_quotations=accepted_quotations)



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
