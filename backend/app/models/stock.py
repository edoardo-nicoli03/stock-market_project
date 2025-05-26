from datetime import datetime
from . import db

class Stock(db.Model):
    """Stock model for stock information."""
    
    __tablename__ = 'stocks'
    
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(50))
    industry = db.Column(db.String(100))
    market_cap = db.Column(db.BigInteger)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    prices = db.relationship('StockPrice', backref='stock', lazy=True, cascade='all, delete-orphan')
    portfolio_items = db.relationship('Portfolio', backref='stock', lazy=True)
    transactions = db.relationship('Transaction', backref='stock', lazy=True)
    
    def to_dict(self):
        """Convert stock object to dictionary."""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'sector': self.sector,
            'industry': self.industry,
            'market_cap': self.market_cap,
            'description': self.description,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class StockPrice(db.Model):
    """Stock price model for historical and real-time data."""
    
    __tablename__ = 'stock_prices'
    
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    open_price = db.Column(db.Numeric(10, 2))
    high_price = db.Column(db.Numeric(10, 2))
    low_price = db.Column(db.Numeric(10, 2))
    volume = db.Column(db.BigInteger, default=0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convert stock price object to dictionary."""
        return {
            'id': self.id,
            'stock_id': self.stock_id,
            'price': float(self.price),
            'open_price': float(self.open_price) if self.open_price else None,
            'high_price': float(self.high_price) if self.high_price else None,
            'low_price': float(self.low_price) if self.low_price else None,
            'volume': self.volume,
            'timestamp': self.timestamp.isoformat()
        }