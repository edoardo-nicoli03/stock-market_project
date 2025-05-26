# scripts/init_db.py
"""
Database initialization script.
Creates tables and sets up the database schema.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
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

# scripts/seed_data.py
"""
Database seeding script.
Creates admin user and sample stock data for testing.
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

from app import create_app
from app.models import db
from app.models.user import User
from app.models.stock import Stock, StockPrice
from app.config import config

# Sample stock data
SAMPLE_STOCKS = [
    {
        'symbol': 'AAPL',
        'name': 'Apple Inc.',
        'sector': 'Technology',
        'industry': 'Consumer Electronics',
        'market_cap': 3000000000000,  # $3T
        'description': 'Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide.',
        'base_price': 180.00
    },
    {
        'symbol': 'GOOGL',
        'name': 'Alphabet Inc.',
        'sector': 'Technology',
        'industry': 'Internet Services',
        'market_cap': 1800000000000,  # $1.8T
        'description': 'Alphabet Inc. provides various products and platforms in the United States, Europe, the Middle East, Africa, the Asia-Pacific, Canada, and Latin America.',
        'base_price': 135.00
    },
    {
        'symbol': 'MSFT',
        'name': 'Microsoft Corporation',
        'sector': 'Technology',
        'industry': 'Software',
        'market_cap': 2800000000000,  # $2.8T
        'description': 'Microsoft Corporation develops, licenses, and supports software, services, devices, and solutions worldwide.',
        'base_price': 380.00
    },
    {
        'symbol': 'AMZN',
        'name': 'Amazon.com Inc.',
        'sector': 'Consumer Discretionary',
        'industry': 'E-commerce',
        'market_cap': 1500000000000,  # $1.5T
        'description': 'Amazon.com, Inc. engages in the retail sale of consumer products and subscriptions in North America and internationally.',
        'base_price': 145.00
    },
    {
        'symbol': 'TSLA',
        'name': 'Tesla Inc.',
        'sector': 'Consumer Discretionary',
        'industry': 'Electric Vehicles',
        'market_cap': 800000000000,  # $800B
        'description': 'Tesla, Inc. designs, develops, manufactures, leases, and sells electric vehicles, and energy generation and storage systems.',
        'base_price': 250.00
    },
    {
        'symbol': 'NVDA',
        'name': 'NVIDIA Corporation',
        'sector': 'Technology',
        'industry': 'Semiconductors',
        'market_cap': 1700000000000,  # $1.7T
        'description': 'NVIDIA Corporation operates as a computing company in the United States, Taiwan, China, and internationally.',
        'base_price': 450.00
    },
    {
        'symbol': 'META',
        'name': 'Meta Platforms Inc.',
        'sector': 'Technology',
        'industry': 'Social Media',
        'market_cap': 900000000000,  # $900B
        'description': 'Meta Platforms, Inc. develops products that enable people to connect and share with friends and family through mobile devices, personal computers, virtual reality headsets, and wearables worldwide.',
        'base_price': 350.00
    },
    {
        'symbol': 'NFLX',
        'name': 'Netflix Inc.',
        'sector': 'Communication Services',
        'industry': 'Entertainment',
        'market_cap': 200000000000,  # $200B
        'description': 'Netflix, Inc. provides entertainment services. It offers TV series, documentaries, feature films, and mobile games across a wide variety of genres and languages.',
        'base_price': 480.00
    },
    {
        'symbol': 'JPM',
        'name': 'JPMorgan Chase & Co.',
        'sector': 'Financial Services',
        'industry': 'Banking',
        'market_cap': 500000000000,  # $500B
        'description': 'JPMorgan Chase & Co. operates as a financial services company worldwide.',
        'base_price': 170.00
    },
    {
        'symbol': 'JNJ',
        'name': 'Johnson & Johnson',
        'sector': 'Healthcare',
        'industry': 'Pharmaceuticals',
        'market_cap': 450000000000,  # $450B
        'description': 'Johnson & Johnson researches, develops, manufactures, and sells various products in the healthcare field worldwide.',
        'base_price': 160.00
    }
]

def create_admin_user():
    """Create admin user if it doesn't exist."""
    admin = User.query.filter_by(email=config.ADMIN_EMAIL).first()
    
    if not admin:
        print("Creating admin user...")
        admin = User(
            email=config.ADMIN_EMAIL,
            first_name=config.ADMIN_FIRST_NAME,
            last_name=config.ADMIN_LAST_NAME,
            is_admin=True
        )
        admin.set_password(config.ADMIN_PASSWORD)
        
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created: {config.ADMIN_EMAIL}")
    else:
        print("Admin user already exists")

def create_sample_stocks():
    """Create sample stocks with historical price data."""
    print("Creating sample stocks...")
    
    for stock_data in SAMPLE_STOCKS:
        # Check if stock already exists
        existing_stock = Stock.query.filter_by(symbol=stock_data['symbol']).first()
        
        if existing_stock:
            print(f"Stock {stock_data['symbol']} already exists, skipping...")
            continue
        
        # Create stock
        stock = Stock(
            symbol=stock_data['symbol'],
            name=stock_data['name'],
            sector=stock_data['sector'],
            industry=stock_data['industry'],
            market_cap=stock_data['market_cap'],
            description=stock_data['description']
        )
        
        db.session.add(stock)
        db.session.flush()  # Get the stock ID
        
        # Create historical price data (last 30 days)
        base_price = stock_data['base_price']
        current_price = base_price
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        print(f"Creating price history for {stock_data['symbol']}...")
        
        # Generate daily prices
        current_date = start_date
        while current_date <= end_date:
            # Simulate daily price movement
            daily_change = random.normalvariate(0, 0.02)  # 2% daily volatility
            current_price = max(0.01, current_price * (1 + daily_change))
            
            # Create daily high/low/open prices
            daily_volatility = random.uniform(0.005, 0.02)  # 0.5% to 2% intraday volatility
            high_price = current_price * (1 + daily_volatility)
            low_price = current_price * (1 - daily_volatility)
            open_price = random.uniform(low_price, high_price)
            
            volume = random.randint(1000000, 10000000)  # 1M to 10M shares
            
            stock_price = StockPrice(
                stock_id=stock.id,
                price=Decimal(str(round(current_price, 2))),
                open_price=Decimal(str(round(open_price, 2))),
                high_price=Decimal(str(round(high_price, 2))),
                low_price=Decimal(str(round(low_price, 2))),
                volume=volume,
                timestamp=current_date
            )
            
            db.session.add(stock_price)
            current_date += timedelta(days=1)
        
        print(f"Created stock: {stock_data['symbol']} - {stock_data['name']}")
    
    db.session.commit()
    print("Sample stocks created successfully!")

def create_sample_users():
    """Create sample users for testing."""
    print("Creating sample users...")
    
    sample_users = [
        {
            'email': 'john.doe@example.com',
            'password': 'TestPassword123',
            'first_name': 'John',
            'last_name': 'Doe'
        },
        {
            'email': 'jane.smith@example.com',
            'password': 'TestPassword123',
            'first_name': 'Jane',
            'last_name': 'Smith'
        }
    ]
    
    for user_data in sample_users:
        existing_user = User.query.filter_by(email=user_data['email']).first()
        
        if existing_user:
            print(f"User {user_data['email']} already exists, skipping...")
            continue
        
        user = User(
            email=user_data['email'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        user.set_password(user_data['password'])
        
        db.session.add(user)
        print(f"Created user: {user_data['email']}")
    
    db.session.commit()
    print("Sample users created successfully!")

def seed_database():
    """Seed the database with initial data."""
    app = create_app()
    
    with app.app_context():
        print("Seeding database...")
        
        # Create admin user
        create_admin_user()
        
        # Create sample stocks
        create_sample_stocks()
        
        # Create sample users
        create_sample_users()
        
        print("Database seeding completed!")

if __name__ == "__main__":
    seed_database()

# scripts/run_setup.py
"""
Complete setup script that initializes and seeds the database.
"""
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.append(str(Path(__file__).parent.parent))

def main():
    """Run complete database setup."""
    print("=" * 50)
    print("Stock Market API - Database Setup")
    print("=" * 50)
    
    try:
        # Initialize database
        from init_db import init_database
        init_database()
        
        print("\n" + "-" * 30)
        
        # Seed database
        from seed_data import seed_database
        seed_database()
        
        print("\n" + "=" * 50)
        print("Setup completed successfully!")
        print("=" * 50)
        print("\nYou can now:")
        print("1. Start the Flask application: python run.py")
        print("2. Login with admin credentials:")
        print(f"   Email: admin@stockapi.com")
        print(f"   Password: [Set via ADMIN_PASSWORD environment variable]")
        print("3. Or create a new user via the /api/auth/register endpoint")
        print("4. Test the API endpoints with your preferred HTTP client")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()