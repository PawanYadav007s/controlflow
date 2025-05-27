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
