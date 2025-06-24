"""
Database Models
Contains all SQLAlchemy models
"""

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='basic')  # NEW: User role field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,  # NEW: Include role in user dict
            'created_at': self.created_at.isoformat()
        }


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(50))
    current_price = db.Column(db.Numeric(10, 2), default=100.00)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'sector': self.sector,
            'current_price': float(self.current_price),
            'updated_at': self.updated_at.isoformat()
        }


class Portfolio(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    average_price = db.Column(db.Numeric(10, 2), nullable=False)

    user = db.relationship('User', backref='portfolios')
    stock = db.relationship('Stock', backref='portfolios')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'stock_symbol': self.stock.symbol,
            'stock_name': self.stock.name,
            'quantity': self.quantity,
            'average_price': float(self.average_price),
            'current_price': float(self.stock.current_price),
            'market_value': self.quantity * float(self.stock.current_price),
            'cost_basis': self.quantity * float(self.average_price)
        }


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
    transaction_type = db.Column(db.String(10), nullable=False)  # 'buy' or 'sell'
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='transactions')
    stock = db.relationship('Stock', backref='transactions')

    def to_dict(self):
        return {
            'id': self.id,
            'stock_symbol': self.stock.symbol,
            'stock_name': self.stock.name,
            'transaction_type': self.transaction_type,
            'quantity': self.quantity,
            'price': float(self.price),
            'total_amount': float(self.total_amount),
            'timestamp': self.timestamp.isoformat()
        }

class HistoricalPrice(db.Model):
        __tablename__ = 'historical_price'

        id = db.Column(db.Integer, primary_key=True)
        stock_id = db.Column(db.Integer, db.ForeignKey('stock.id'), nullable=False)
        date = db.Column(db.Date, nullable=False, index=True)
        price = db.Column(db.Numeric(10, 2), nullable=False)

        stock = db.relationship('Stock', backref='historical_prices')

        def to_dict(self):
            return {
                'date': self.date.isoformat(),
                'price': float(self.price)
            }


