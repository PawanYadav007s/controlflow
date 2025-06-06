from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Quotation
from datetime import datetime

quotation_routes = Blueprint('quotation_routes', __name__)

# Show Add Quotation Form
@quotation_routes.route('/quotations/add', methods=['GET'])
def add_quotation_form():
    try:
        return render_template('quotation/add_quotation.html')
    except Exception as e:
        flash(f"Error loading form: {str(e)}", "danger")
        return redirect(url_for('quotation_routes.manage_quotations'))

# Handle Add Quotation Form Submission
@quotation_routes.route('/quotations/add', methods=['POST'])
def add_quotation():
    try:
        quotation_date = datetime.strptime(request.form['quotation_date'], '%Y-%m-%d').date()
        new_quotation = Quotation(
            quotation_number=request.form['quotation_number'],
            quotation_date=quotation_date,
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

    return redirect(url_for('quotation_routes.manage_quotations'))

# Manage Quotations (View with pagination/search/etc.)
@quotation_routes.route('/quotations')
def manage_quotations():
    try:
        page = request.args.get('page', 1, type=int)
        quotations = Quotation.query.order_by(Quotation.id.desc()).paginate(page=page, per_page=10)
        return render_template('quotation/manage_quotations.html', quotations=quotations)
    except Exception as e:
        flash(f"Error loading quotations: {str(e)}", "danger")
        return redirect(url_for('quotation_routes.add_quotation_form'))

# Handle Edit Quotation
@quotation_routes.route('/quotations/edit/<int:id>', methods=['GET', 'POST'])
def edit_quotation(id):
    try:
        quotation = Quotation.query.get_or_404(id)
    except Exception as e:
        flash(f"Quotation not found: {str(e)}", "danger")
        return redirect(url_for('quotation_routes.manage_quotations'))

    if request.method == 'POST':
        try:
            quotation.quotation_number = request.form['quotation_number']
            quotation.client_name = request.form['client_name']
            quotation.project_name = request.form['project_name']
            quotation.project_description = request.form['project_description']
            quotation.estimated_cost = request.form['estimated_cost']
            quotation.status = request.form['status']

            try:
                quotation.quotation_date = datetime.strptime(request.form['quotation_date'], '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid date format. Please use YYYY-MM-DD.", "danger")
                return redirect(url_for('quotation_routes.edit_quotation', id=id))

            db.session.commit()
            flash('Quotation updated successfully!', 'success')
            return redirect(url_for('quotation_routes.manage_quotations'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating quotation: {str(e)}', 'danger')
            return redirect(url_for('quotation_routes.edit_quotation', id=id))

    try:
        return render_template('quotation/edit_quotation.html', quotation=quotation)
    except Exception as e:
        flash(f"Error rendering edit form: {str(e)}", "danger")
        return redirect(url_for('quotation_routes.manage_quotations'))

# Handle Delete Quotation
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

    return redirect(url_for('quotation_routes.manage_quotations'))
