from flask import Blueprint, render_template, jsonify
from app.models import Quotation, SalesOrder, PurchaseOrder, MaterialReceipt, Inventory, Material, Location
from sqlalchemy import func
from datetime import datetime, timedelta
from app import db

base_routes = Blueprint('base_routes', __name__)

@base_routes.route('/')
def dashboard():
    data = get_dashboard_data()
    return render_template('index.html', **data)

@base_routes.route('/api/dashboard-stats')
def dashboard_stats():
    data = get_dashboard_data()
    return jsonify(data)

def get_dashboard_data():
    # Quotations
    total_quotations = Quotation.query.count()
    pending_quotations = Quotation.query.filter_by(status='Pending').count()
    accepted_quotations = Quotation.query.filter_by(status='Accepted').count()
    rejected_quotations = Quotation.query.filter_by(status='Rejected').count()
    
    # Calculate quotation values
    total_quotation_value = db.session.query(func.sum(Quotation.estimated_cost)).scalar() or 0
    pending_quotation_value = db.session.query(func.sum(Quotation.estimated_cost)).filter_by(status='Pending').scalar() or 0
    accepted_quotation_value = db.session.query(func.sum(Quotation.estimated_cost)).filter_by(status='Accepted').scalar() or 0
    
    # Sales Orders
    total_sales_orders = SalesOrder.query.count()
    delivered_sales_orders = SalesOrder.query.filter_by(approval_status='Delivered').count()
    pending_sales_orders = SalesOrder.query.filter_by(approval_status='Pending').count()
    approved_sales_orders = SalesOrder.query.filter_by(approval_status='Approved').count()
    
    # Purchase Orders
    total_purchase_orders = PurchaseOrder.query.count()
    pending_purchase_orders = PurchaseOrder.query.filter_by(status='Pending').count()
    received_purchase_orders = PurchaseOrder.query.filter_by(status='Received').count()
    partial_purchase_orders = PurchaseOrder.query.filter_by(status='Partially Received').count()
    
    # Calculate PO values
    total_po_value = db.session.query(func.sum(PurchaseOrder.quantity * PurchaseOrder.unit_price)).scalar() or 0
    pending_po_value = db.session.query(
        func.sum(PurchaseOrder.quantity * PurchaseOrder.unit_price)
    ).filter_by(status='Pending').scalar() or 0
    
    # Material Receipts
    total_materials_received = db.session.query(func.sum(MaterialReceipt.received_quantity)).scalar() or 0
    total_materials_damaged = db.session.query(func.sum(MaterialReceipt.damaged_quantity)).scalar() or 0
    total_materials_rejected = db.session.query(func.sum(MaterialReceipt.rejected_quantity)).scalar() or 0
    
    # Inventory Stats
    total_inventory_items = Inventory.query.count()
    total_inventory_quantity = db.session.query(func.sum(Inventory.quantity)).scalar() or 0
    low_stock_items = Inventory.query.filter(Inventory.quantity < 10).count()
    total_locations = Location.query.count()
    
    # Calculate inventory value (you may need to adjust this based on your model)
    total_inventory_value = 0
    if hasattr(Material, 'unit_price'):
        total_inventory_value = db.session.query(
            func.sum(Inventory.quantity * Material.unit_price)
        ).join(Material).scalar() or 0
    
    # Recent activity (last 7 days)
    last_week = datetime.now() - timedelta(days=7)
    recent_quotations = Quotation.query.filter(Quotation.quotation_date >= last_week).count()
    recent_sales_orders = SalesOrder.query.filter(SalesOrder.so_date >= last_week).count()
    recent_purchase_orders = PurchaseOrder.query.filter(PurchaseOrder.po_date >= last_week).count()
    
    # Monthly trends (current month)
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    monthly_quotation_value = db.session.query(
        func.sum(Quotation.estimated_cost)
    ).filter(Quotation.quotation_date >= current_month_start).scalar() or 0
    
    monthly_sales_orders = SalesOrder.query.filter(
        SalesOrder.so_date >= current_month_start
    ).count()
    
    # Performance metrics
    conversion_rate = round((accepted_quotations / total_quotations * 100) if total_quotations > 0 else 0, 1)
    fulfillment_rate = round((delivered_sales_orders / total_sales_orders * 100) if total_sales_orders > 0 else 0, 1)
    material_acceptance_rate = round(
        (total_materials_received / (total_materials_received + total_materials_rejected) * 100) 
        if (total_materials_received + total_materials_rejected) > 0 else 0, 1
    )
    
    return {
        # Quotations
        'total_quotations': total_quotations,
        'pending_quotations': pending_quotations,
        'accepted_quotations': accepted_quotations,
        'rejected_quotations': rejected_quotations,
        'total_quotation_value': total_quotation_value,
        'pending_quotation_value': pending_quotation_value,
        'accepted_quotation_value': accepted_quotation_value,
        
        # Sales Orders
        'total_sales_orders': total_sales_orders,
        'delivered_sales_orders': delivered_sales_orders,
        'pending_sales_orders': pending_sales_orders,
        'approved_sales_orders': approved_sales_orders,
        
        # Purchase Orders
        'total_purchase_orders': total_purchase_orders,
        'pending_purchase_orders': pending_purchase_orders,
        'received_purchase_orders': received_purchase_orders,
        'partial_purchase_orders': partial_purchase_orders,
        'total_po_value': total_po_value,
        'pending_po_value': pending_po_value,
        
        # Material Management
        'total_materials_received': int(total_materials_received),
        'total_materials_damaged': int(total_materials_damaged),
        'total_materials_rejected': int(total_materials_rejected),
        
        # Inventory
        'total_inventory_items': total_inventory_items,
        'total_inventory_quantity': int(total_inventory_quantity),
        'total_inventory_value': total_inventory_value,
        'low_stock_items': low_stock_items,
        'total_locations': total_locations,
        
        # Recent Activity
        'recent_quotations': recent_quotations,
        'recent_sales_orders': recent_sales_orders,
        'recent_purchase_orders': recent_purchase_orders,
        'monthly_quotation_value': monthly_quotation_value,
        'monthly_sales_orders': monthly_sales_orders,
        
        # Performance Metrics
        'conversion_rate': conversion_rate,
        'fulfillment_rate': fulfillment_rate,
        'material_acceptance_rate': material_acceptance_rate,
        
        # Timestamp
        'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }