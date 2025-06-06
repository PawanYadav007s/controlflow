from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Location

location_routes = Blueprint('location_routes', __name__)

@location_routes.route('/locations')
def list_locations():
    try:
        query = request.args.get('q', '')
        if query:
            locations = Location.query.filter(Location.name.ilike(f'%{query}%')).all()
        else:
            locations = Location.query.all()
        return render_template('locations/list.html', locations=locations)
    except Exception as e:
        flash(f"Error fetching locations: {str(e)}", "danger")
        return redirect(url_for('location_routes.list_locations'))

@location_routes.route('/locations/add', methods=['GET', 'POST'])
def add_location():
    try:
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']

            if Location.query.filter_by(name=name).first():
                flash('Location name already exists.', 'warning')
                return redirect(url_for('location_routes.add_location'))

            new_location = Location(name=name, description=description)
            db.session.add(new_location)
            db.session.commit()
            flash('Location added successfully.', 'success')
            return redirect(url_for('location_routes.list_locations'))

        return render_template('locations/add.html')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding location: {str(e)}", "danger")
        return redirect(url_for('location_routes.list_locations'))

@location_routes.route('/locations/edit/<int:id>', methods=['GET', 'POST'])
def edit_location(id):
    try:
        location = Location.query.get_or_404(id)

        if request.method == 'POST':
            location.name = request.form['name']
            location.description = request.form['description']
            db.session.commit()
            flash('Location updated successfully.', 'success')
            return redirect(url_for('location_routes.list_locations'))

        return render_template('locations/edit.html', location=location)
    except Exception as e:
        db.session.rollback()
        flash(f"Error updating location: {str(e)}", "danger")
        return redirect(url_for('location_routes.list_locations'))

@location_routes.route('/locations/delete/<int:id>', methods=['POST'])
def delete_location(id):
    try:
        location = Location.query.get_or_404(id)
        db.session.delete(location)
        db.session.commit()
        flash('Location deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting location: {str(e)}", 'danger')
    return redirect(url_for('location_routes.list_locations'))
