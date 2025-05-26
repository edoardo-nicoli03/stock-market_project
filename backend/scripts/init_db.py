"""
Database initialization script.
Creates tables and sets up the database schema.
"""
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.stock import Stock, StockPrice
from app.models.portfolio import Portfolio, Transaction

def init_database():
    """Initialize the database with tables."""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully!")

if __name__ == "__main__":
    init_database()