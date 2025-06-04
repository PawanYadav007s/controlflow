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




