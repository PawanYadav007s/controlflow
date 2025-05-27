from datetime import date
from app import db

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

