from app import db
from datetime import datetime
import json

class Invoice(db.Model):
    """Invoice model to store extracted invoice data"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    
    # Extracted invoice data
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.String(50))
    vendor_name = db.Column(db.String(200))
    vendor_address = db.Column(db.Text)
    customer_name = db.Column(db.String(200))
    customer_address = db.Column(db.Text)
    
    # Financial data
    subtotal = db.Column(db.String(50))
    tax_amount = db.Column(db.String(50))
    total_amount = db.Column(db.String(50))
    
    # Items as JSON string
    items = db.Column(db.Text)  # Stored as JSON
    
    # New fields
    category = db.Column(db.String(100), default='Uncategorized')
    status = db.Column(db.String(50), default='Processed')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_items(self, items_list):
        """Convert items list to JSON string"""
        self.items = json.dumps(items_list)
    
    def get_items(self):
        """Parse items from JSON string"""
        if self.items:
            return json.loads(self.items)
        return []
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}>'
