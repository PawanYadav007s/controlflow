from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Material

material_bp = Blueprint('material_routes', __name__)

# List & Search Materials
@material_bp.route('/materials')
def list_materials():
    try:
        search_query = request.args.get('q')
        if search_query:
            materials = Material.query.filter(
                Material.name.ilike(f"%{search_query}%") |
                Material.code.ilike(f"%{search_query}%")
            ).all()
        else:
            materials = Material.query.all()
        return render_template('materials/list.html', materials=materials)
    except Exception as e:
        flash(f"Error loading materials: {str(e)}", "danger")
        return redirect(url_for('material_routes.list_materials'))

# Add Material
@material_bp.route('/materials/add', methods=['GET', 'POST'])
def add_material():
    if request.method == 'POST':
        try:
            code = request.form['code']
            name = request.form['name']
            description = request.form.get('description', '')
            category = request.form['category']
            unit = request.form['unit']
            min_stock_level = float(request.form.get('min_stock_level', 0.0))

            if Material.query.filter_by(code=code).first():
                flash('Material code already exists.', 'danger')
                return redirect(url_for('material_routes.add_material'))

            new_material = Material(
                code=code,
                name=name,
                description=description,
                category=category,
                unit=unit,
                min_stock_level=min_stock_level
            )
            db.session.add(new_material)
            db.session.commit()
            flash('Material added successfully.', 'success')
            return redirect(url_for('material_routes.list_materials'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding material: {str(e)}", "danger")

    try:
        return render_template('materials/add.html')
    except Exception as e:
        flash(f"Error loading add material form: {str(e)}", "danger")
        return redirect(url_for('material_routes.list_materials'))

# Edit Material
@material_bp.route('/materials/edit/<int:id>', methods=['GET', 'POST'])
def edit_material(id):
    try:
        material = Material.query.get_or_404(id)
    except Exception as e:
        flash(f"Material not found: {str(e)}", "danger")
        return redirect(url_for('material_routes.list_materials'))

    if request.method == 'POST':
        try:
            material.code = request.form['code']
            material.name = request.form['name']
            material.description = request.form.get('description', '')
            material.category = request.form['category']
            material.unit = request.form['unit']
            material.min_stock_level = float(request.form.get('min_stock_level', 0.0))

            db.session.commit()
            flash('Material updated successfully.', 'success')
            return redirect(url_for('material_routes.list_materials'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating material: {str(e)}", "danger")

    try:
        return render_template('materials/edit.html', material=material)
    except Exception as e:
        flash(f"Error loading edit form: {str(e)}", "danger")
        return redirect(url_for('material_routes.list_materials'))

# Delete Material
@material_bp.route('/materials/delete/<int:id>', methods=['POST'])
def delete_material(id):
    try:
        material = Material.query.get_or_404(id)
        db.session.delete(material)
        db.session.commit()
        flash('Material deleted.', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting material: {str(e)}", "danger")

    return redirect(url_for('material_routes.list_materials'))
