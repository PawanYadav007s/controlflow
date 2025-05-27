from app import ma
from app.models import Quotation

class QuotationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Quotation
        load_instance = True
