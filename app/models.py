from datetime import date
from app import db
from datetime import datetime


class Quotation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quotation_number = db.Column(db.String(20), nullable=False)
    quotation_date = db.Column(db.Date, nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    project_description = db.Column(db.Text, nullable=False)
    estimated_cost = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending')
    

    def __repr__(self):
        return f'<Quotation {self.quotation_number}>'




class SalesOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quotation_id = db.Column(db.Integer, db.ForeignKey('quotation.id'), nullable=False)
    so_date = db.Column(db.Date, nullable=False)
    project_name = db.Column(db.String(150), nullable=False)
    project_details = db.Column(db.Text, nullable=False)
    approval_status = db.Column(db.String(20), nullable=False, default='Pending')
    payment_terms = db.Column(db.String(100), nullable=True)
    delivery_schedule = db.Column(db.Date, nullable=True)
    quotation = db.relationship('Quotation', backref=db.backref('sales_orders', lazy=True))




class PurchaseOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    po_number = db.Column(db.String(50), unique=True, nullable=False)
    po_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)

    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)  # NEW

    supplier_name = db.Column(db.String(100), nullable=False)
    material_description = db.Column(db.Text, nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='Pending')
    expected_delivery_date = db.Column(db.Date, nullable=True)

    sales_order = db.relationship('SalesOrder', backref=db.backref('purchase_orders', lazy=True))
    material = db.relationship('Material', backref=db.backref('purchase_orders', lazy=True))  # NEW

    def __init__(self, po_number, po_date, sales_order_id, material_id, supplier_name, material_description,
                 quantity, unit_price, expected_delivery_date):
        self.po_number = po_number
        self.po_date = po_date
        self.sales_order_id = sales_order_id
        self.material_id = material_id
        self.supplier_name = supplier_name
        self.material_description = material_description
        self.quantity = quantity
        self.unit_price = unit_price
        self.total_price = quantity * unit_price
        self.expected_delivery_date = expected_delivery_date






class MaterialReceipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    purchase_order_id = db.Column(db.Integer, db.ForeignKey('purchase_order.id'), nullable=False)
    receipt_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    received_quantity = db.Column(db.Float, nullable=False)
    damaged_quantity = db.Column(db.Float, nullable=False, default=0.0)
    rejected_quantity = db.Column(db.Float, nullable=False, default=0.0)
    remarks = db.Column(db.Text)

    purchase_order = db.relationship('PurchaseOrder', backref=db.backref('material_receipts', lazy=True))



class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))  # e.g., Raw Material, Consumable, Finished Good
    unit = db.Column(db.String(20))  # kg, meter, pieces, etc.
    min_stock_level = db.Column(db.Float, default=0.0)


class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)  # e.g., Rack-A1
    description = db.Column(db.String(150))



class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'), nullable=False)

    quantity = db.Column(db.Float, default=0.0)  # Total quantity in stock
    weight = db.Column(db.Float, default=0.0)    # For weighted materials
    reserved_quantity = db.Column(db.Float, default=0.0)  # For linked SOs

    material = db.relationship('Material', backref=db.backref('stock_entries', lazy=True))
    location = db.relationship('Location', backref=db.backref('stock_entries', lazy=True))


class InventoryTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    quantity = db.Column(db.Float)
    weight = db.Column(db.Float)
    movement_type = db.Column(db.String(10))  # IN / OUT
    reference = db.Column(db.String(100))  # PO, SO, or Production ref
    performed_by = db.Column(db.String(100))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material')



class ProductionOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sales_order_id = db.Column(db.Integer, db.ForeignKey('sales_order.id'))
    production_code = db.Column(db.String(50), unique=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    planned_quantity = db.Column(db.Float)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='Planned')

    material = db.relationship('Material')
    sales_order = db.relationship('SalesOrder')



class MaterialIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_order.id'))
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    issued_quantity = db.Column(db.Float)
    issued_weight = db.Column(db.Float)
    issued_by = db.Column(db.String(100))
    issue_date = db.Column(db.DateTime, default=datetime.utcnow)

    production_order = db.relationship('ProductionOrder')
    material = db.relationship('Material')



class WasteRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    production_order_id = db.Column(db.Integer, db.ForeignKey('production_order.id'))
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'))
    waste_quantity = db.Column(db.Float)
    waste_weight = db.Column(db.Float)
    reason = db.Column(db.String(200))
    recorded_on = db.Column(db.DateTime, default=datetime.utcnow)
