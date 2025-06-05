from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from app import db
from app.models import PurchaseOrder, MaterialReceipt, SalesOrder,Location, Inventory
from datetime import datetime,timezone
import csv
import io

material_receipt_routes = Blueprint('material_receipt_routes', __name__)

# Helper function to calculate totals per PO
def calculate_totals(po):
    total_received = sum(r.received_quantity for r in po.material_receipts)
    total_damaged = sum(r.damaged_quantity for r in po.material_receipts)
    total_rejected = sum(r.rejected_quantity for r in po.material_receipts)
    pending = max(po.quantity - total_received, 0)
    return total_received, total_damaged, total_rejected, pending


@material_receipt_routes.route('/material-receipts', methods=['GET', 'POST'])
def manage_material_receipts():
    search_so_number = request.args.get('sales_order_number', '').strip()

    # Query all Purchase Orders and filter by Sales Order number if provided
    if search_so_number:
        sales_order = SalesOrder.query.filter_by(id=search_so_number).first()
        if sales_order:
            purchase_orders = PurchaseOrder.query.filter_by(sales_order_id=sales_order.id).all()
        else:
            purchase_orders = []
            flash('No Sales Order found with that number.', 'warning')
    else:
        purchase_orders = PurchaseOrder.query.all()

    po_data = []
    for po in purchase_orders:
        total_received, total_damaged, total_rejected, pending = calculate_totals(po)
        po_data.append({
            'po': po,
            'sales_order': po.sales_order,
            'received_qty': total_received,
            'damaged_qty': total_damaged,
            'rejected_qty': total_rejected,
            'pending_qty': pending,
            'payment_status': getattr(po, 'payment_status', 'N/A')
        })

    return render_template('material_receipt/manage_material_receipts.html', po_data=po_data, search_so_number=search_so_number)


@material_receipt_routes.route('/material-receipts/<int:po_id>/receipts')
def list_receipts_for_po(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    receipts = MaterialReceipt.query.filter_by(purchase_order_id=po_id).all()
    total_received, total_damaged, total_rejected, pending = calculate_totals(po)
    return render_template('material_receipt/list_receipts.html', po=po, receipts=receipts, pending_qty=pending,
                           total_received=total_received)


@material_receipt_routes.route('/material-receipts/<int:po_id>/add', methods=['GET', 'POST'])
def add_material_receipt(po_id):
    po = PurchaseOrder.query.get_or_404(po_id)
    total_received = sum(r.received_quantity for r in po.material_receipts)
    pending_qty = max(po.quantity - total_received, 0)
    locations = Location.query.all()

    if request.method == 'POST':
        received_qty = float(request.form['received_quantity'])
        damaged_qty = float(request.form['damaged_quantity'])
        rejected_qty = float(request.form['rejected_quantity'])
        location_id = int(request.form['location_id'])
        remarks = request.form['remarks']

        if received_qty > pending_qty:
            flash(f'Received quantity cannot exceed pending quantity ({pending_qty}).', 'danger')
            return redirect(url_for('material_receipt_routes.add_material_receipt', po_id=po_id))

        receipt = MaterialReceipt(
            purchase_order_id=po_id,
            received_quantity=received_qty,
            damaged_quantity=damaged_qty,
            rejected_quantity=rejected_qty,
            location_id=location_id,
            remarks=remarks
        )
        db.session.add(receipt)

        # Update inventory
        material_id = po.material_id
        inventory = Inventory.query.filter_by(material_id=material_id, location_id=location_id).first()
        if inventory:
            inventory.quantity += received_qty
        else:
            inventory = Inventory(material_id=material_id, location_id=location_id, quantity=received_qty)
            db.session.add(inventory)

        # Update PO status
        if received_qty + total_received >= po.quantity:
            po.status = 'Received'
        else:
            po.status = 'Partially Received'

        db.session.commit()
        flash('Material receipt added successfully and inventory updated.', 'success')
        return redirect(url_for('material_receipt_routes.list_receipts_for_po', po_id=po_id))

    return render_template('material_receipt/add_receipt.html', po=po, pending_qty=pending_qty, locations=locations)


@material_receipt_routes.route('/material-receipts/edit/<int:receipt_id>', methods=['GET', 'POST'])
def edit_material_receipt(receipt_id):
    receipt = MaterialReceipt.query.get_or_404(receipt_id)
    po = receipt.purchase_order
    old_location_id = receipt.location_id
    old_received_qty = receipt.received_quantity

    # Exclude current receipt from total received calc
    total_received = sum(r.received_quantity for r in po.material_receipts if r.id != receipt.id)
    pending_qty = max(po.quantity - total_received, 0)
    locations = Location.query.all()

    if request.method == 'POST':
        new_received_qty = float(request.form['received_quantity'])
        damaged_qty = float(request.form['damaged_quantity'])
        rejected_qty = float(request.form['rejected_quantity'])
        remarks = request.form['remarks']
        new_location_id = int(request.form['location_id'])

        # Check for pending quantity overflow
        if new_received_qty > pending_qty + old_received_qty:
            flash(f'Received quantity cannot exceed pending quantity ({pending_qty + old_received_qty}).', 'danger')
            return redirect(url_for('material_receipt_routes.edit_material_receipt', receipt_id=receipt_id))

        # Update inventory for old location (subtract old quantity)
        if old_location_id:
            old_inventory = Inventory.query.filter_by(material_id=po.material_id, location_id=old_location_id).first()
            if old_inventory:
                old_inventory.quantity -= old_received_qty

        # Update inventory for new location (add new quantity)
        new_inventory = Inventory.query.filter_by(material_id=po.material_id, location_id=new_location_id).first()
        if new_inventory:
            new_inventory.quantity += new_received_qty
        else:
            new_inventory = Inventory(material_id=po.material_id, location_id=new_location_id, quantity=new_received_qty)
            db.session.add(new_inventory)

        # Update the receipt
        receipt.received_quantity = new_received_qty
        receipt.damaged_quantity = damaged_qty
        receipt.rejected_quantity = rejected_qty
        receipt.remarks = remarks
        receipt.location_id = new_location_id

        # Update PO status
        total_received += new_received_qty
        if total_received >= po.quantity:
            po.status = 'Received'
        else:
            po.status = 'Partially Received'

        db.session.commit()
        flash('Material receipt updated successfully and inventory adjusted.', 'success')
        return redirect(url_for('material_receipt_routes.list_receipts_for_po', po_id=po.id))

    return render_template(
        'material_receipt/edit_receipt.html',
        receipt=receipt,
        pending_qty=pending_qty,
        po=po,
        locations=locations
    )


@material_receipt_routes.route('/material-receipts/delete/<int:receipt_id>', methods=['POST'])
def delete_material_receipt(receipt_id):
    receipt = MaterialReceipt.query.get_or_404(receipt_id)
    po = receipt.purchase_order
    db.session.delete(receipt)
    db.session.commit()

    total_received = sum(r.received_quantity for r in po.material_receipts)
    if total_received >= po.quantity:
        po.status = 'Received'
    elif total_received == 0:
        po.status = 'Pending'
    else:
        po.status = 'Partially Received'

    db.session.commit()
    flash('Material receipt deleted successfully.', 'success')
    return redirect(url_for('material_receipt_routes.list_receipts_for_po', po_id=po.id))


@material_receipt_routes.route('/material-receipts/export/csv')
def export_material_receipts_csv():
    purchase_orders = PurchaseOrder.query.all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        'PO Number', 'SO Number', 'Material Description', 'Supplier', 'Ordered Quantity',
        'Received Quantity', 'Damaged Quantity', 'Rejected Quantity', 'Pending Quantity', 'PO Status'
    ])

    for po in purchase_orders:
        total_received, total_damaged, total_rejected, pending = calculate_totals(po)
        cw.writerow([
            po.po_number,
            po.sales_order_id,
            po.material_description,
            po.supplier_name,
            po.quantity,
            total_received,
            total_damaged,
            total_rejected,
            pending,
            po.status
        ])

    output = si.getvalue()
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=material_receipts_summary.csv"})


@material_receipt_routes.route('/material_receipts/report')
def material_receipt_report():
    purchase_orders = PurchaseOrder.query.all()

    report_data = []
    for po in purchase_orders:
        total_received, total_damaged, total_rejected, pending = calculate_totals(po)
        report_data.append({
            'po': po,
            'sales_order': po.sales_order,
            'shop_name': getattr(po.sales_order, 'shop_name', 'N/A'),
            'received_qty': total_received,
            'damaged_qty': total_damaged,
            'rejected_qty': total_rejected,
            'pending_qty': pending
        })

    return render_template(
        'material_receipt/material_receipt_report.html',
        report_data=report_data,
        company_name="Rasco Industries",
        report_date=datetime.now().strftime('%Y-%m-%d')
    )


@material_receipt_routes.route('/material_receipts/report/export/csv')
def export_material_receipt_report_csv():
    report_data = MaterialReceipt.query \
        .join(PurchaseOrder, MaterialReceipt.po_id == PurchaseOrder.id) \
        .join(Shop, MaterialReceipt.shop_id == Shop.id) \
        .join(SalesOrder, MaterialReceipt.sales_order_id == SalesOrder.id) \
        .add_entity(PurchaseOrder) \
        .add_entity(Shop) \
        .add_entity(SalesOrder) \
        .all()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        'PO Number', 'SO Number', 'Shop Name', 'Material', 'Supplier',
        'Ordered Qty', 'Received Qty', 'Damaged Qty', 'Rejected Qty', 'Pending Qty', 'Status'
    ])

    for receipt, po, shop, so in report_data:
        cw.writerow([
            po.po_number,
            so.id,
            shop.name,
            po.material_description,
            po.supplier_name,
            po.quantity,
            receipt.received_qty,
            receipt.damaged_qty,
            receipt.rejected_qty,
            receipt.pending_qty,
            po.status
        ])

    output = si.getvalue()
    return Response(output, mimetype='text/csv',
                    headers={"Content-Disposition": "attachment;filename=material_receipt_report.csv"})
