from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Quotation
from datetime import datetime

quotation_routes = Blueprint('quotation_routes', __name__)

@quotation_routes.route('/quotations', methods=['GET', 'POST'])
def quotation():
    if request.method == 'POST':
        try:
            new_quotation = Quotation(
                quotation_number=request.form['quotation_number'],
                quotation_date=datetime.strptime(request.form['quotation_date'], '%Y-%m-%d').date(),
                client_name=request.form['client_name'],
                project_name=request.form['project_name'],
                project_description=request.form['project_description'],
                estimated_cost=request.form['estimated_cost'],
                status='Pending'
            )
            db.session.add(new_quotation)
            db.session.commit()
            flash('Quotation added successfully!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding quotation: {str(e)}', 'danger')

        return redirect(url_for('quotation_routes.quotation'))

    quotations = Quotation.query.order_by(Quotation.id.desc()).all()
    return render_template('quotation.html', quotations=quotations)

# Edit Route
@quotation_routes.route('/quotations/edit/<int:id>', methods=['POST'])
def edit_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        quotation.quotation_number = request.form['quotation_number']
        quotation.quotation_date = datetime.strptime(request.form['quotation_date'], '%Y-%m-%d').date()
        quotation.client_name = request.form['client_name']
        quotation.project_name = request.form['project_name']
        quotation.project_description = request.form['project_description']
        quotation.estimated_cost = request.form['estimated_cost']
        
        db.session.commit()
        flash('Quotation updated successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating quotation: {str(e)}', 'danger')
    
    return redirect(url_for('quotation_routes.quotation'))

# Delete Route
@quotation_routes.route('/quotations/delete/<int:id>', methods=['POST'])
def delete_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
        db.session.delete(quotation)
        db.session.commit()
        flash('Quotation deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting quotation: {str(e)}', 'danger')
    
    return redirect(url_for('quotation_routes.quotation'))
