from datetime import datetime
from . import db

class Portfolio(db.Model):
    """Portfolio model for user stock holdings."""
    
    __tablename__ = 'portfolios'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('user_id', 'stock_id', name='unique_user_stock'),)
    
    def to_dict(self):
        """Convert portfolio object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol if self.stock else None,
            'stock_name': self.stock.name if self.stock else None,
            'quantity': self.quantity,
            'average_price': float(self.average_price),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class Transaction(db.Model):
    """Transaction model for buy/sell operations."""
    
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    transaction_type = db.Column(db.Enum('buy', 'sell', name='transaction_types'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert transaction object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_id': self.stock_id,
            'stock_symbol': self.stock.symbol if self.stock else None,
            'stock_name': self.stock.name if self.stock else None,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price': float(self.price),
            'total_amount': float(self.total_amount),
            'timestamp': self.timestamp.isoformat()
        }