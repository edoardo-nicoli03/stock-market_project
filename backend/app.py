"""
Simple Stock Market API
A streamlined Flask application following MVC principles with Blueprint architecture
"""

from flask import Flask, jsonify
from flask_cors import CORS
from models import db, User, Stock, HistoricalPrice, Transaction  # Import models and db
from decimal import Decimal
import threading
import time
import random
from datetime import datetime, timedelta
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Initialize limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[]  # no rate-limit by default
)

# Import blueprints (with error handling)
try:
    from auth import auth_bp
    from market import market_bp
except ImportError as e:
    print(f"⚠️  Warning: Blueprint import failed: {e}")
    print("Creating placeholder blueprints...")
    from flask import Blueprint

    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')
    market_bp = Blueprint('market', __name__, url_prefix='/api')


# =============================================================================
# APP CONFIGURATION
# =============================================================================

def create_app():
    """Application factory pattern"""
    app = Flask(__name__)

    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_market.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

    # Initialize extensions
    db.init_app(app)
    CORS(app)
    limiter.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(market_bp)

    return app


app = create_app()


# =============================================================================
# BACKGROUND PRICE UPDATES
# =============================================================================

class PriceUpdater:
    def __init__(self, app):
        self.app = app
        self.running = False
        self.thread = None

    def start(self):
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
        print("📈 Real-time price updates started")

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        print("📈 Price updates stopped")

    def _update_loop(self):
        while self.running:
            try:
                with self.app.app_context():
                    stocks = Stock.query.all()
                    for stock in stocks:
                        if not self.running:
                            break

                        # Simulate price movement (±2% max change)
                        current_price = float(stock.current_price)
                        change_percent = random.uniform(-0.02, 0.02)  # ±2%
                        new_price = current_price * (1 + change_percent)
                        new_price = max(0.01, new_price)  # Minimum price $0.01

                        stock.current_price = Decimal(str(round(new_price, 2)))
                        stock.updated_at = datetime.utcnow()

                    db.session.commit()

                time.sleep(2)  # Update every 2 seconds

            except Exception as e:
                print(f"❌ Error updating prices: {e}")
                time.sleep(5)


# Global price updater instance
price_updater = PriceUpdater(app)


# =============================================================================
# INITIALIZATION & SAMPLE DATA
# =============================================================================

def init_database():
    """Initialize database with sample data"""
    try:
        with app.app_context():
            db.create_all()

            # Check if stocks already exist
            if Stock.query.count() > 0:
                print("📊 Database already contains stocks, skipping initialization")
                return

            # Sample stocks
            sample_stocks = [
                {'symbol': 'AAPL', 'name': 'Apple Inc.', 'sector': 'Technology', 'price': 180.00},
                {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'sector': 'Technology', 'price': 135.00},
                {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'sector': 'Technology', 'price': 380.00},
                {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': 'Consumer Discretionary', 'price': 145.00},
                {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'sector': 'Consumer Discretionary', 'price': 250.00},
                {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': 'Technology', 'price': 450.00},
                {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'sector': 'Technology', 'price': 350.00},
                {'symbol': 'NFLX', 'name': 'Netflix Inc.', 'sector': 'Communication Services', 'price': 480.00},
            ]

            for stock_data in sample_stocks:
                stock = Stock(
                    symbol=stock_data['symbol'],
                    name=stock_data['name'],
                    sector=stock_data['sector'],
                    current_price=Decimal(str(stock_data['price']))
                )
                db.session.add(stock)

            # Create sample users with different roles
            # Check if users already exist
            if User.query.count() == 0:
                # Basic user
                basic_user = User(
                    email='user@example.com',
                    first_name='Basic',
                    last_name='User',
                    role='basic'  # Basic role - limited access
                )
                basic_user.set_password('user')
                db.session.add(basic_user)

                # Pro user
                pro_user = User(
                    email='pro@example.com',
                    first_name='Pro',
                    last_name='User',
                    role='pro'  # Pro role - full access
                )
                pro_user.set_password('prouser')
                db.session.add(pro_user)

            db.session.commit()
            print("✅ Database initialized with sample data")
            print("👤 Basic user: user@example.com / user (limited to 3 stocks)")
            print("⭐ Pro user: pro@example.com / prouser (full access)")

    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        db.session.rollback()


def seed_historical_prices():
    """Populate 5 years of historical prices for each stock."""
    try:
        with app.app_context():
            stocks = Stock.query.all()
            if not stocks:
                print("⚠️  No stocks found, skipping historical price seeding")
                return

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=5 * 365)

            for stock in stocks:
                # Avoid duplicates
                existing_prices = HistoricalPrice.query.filter_by(stock_id=stock.id).count()
                if existing_prices > 0:
                    continue

                print(f"📊 Seeding historical prices for {stock.symbol}...")
                current_date = start_date
                base_price = float(stock.current_price)

                while current_date <= end_date:
                    # Create more realistic price evolution
                    days_from_start = (current_date - start_date).days
                    trend = random.uniform(-0.0001, 0.0002)  # Slight upward trend
                    daily_change = random.uniform(-0.05, 0.05)  # Daily volatility

                    price = base_price * (1 + trend * days_from_start + daily_change)
                    price = max(0.01, round(price, 2))

                    hp = HistoricalPrice(
                        stock_id=stock.id,
                        date=current_date,
                        price=Decimal(str(price))
                    )
                    db.session.add(hp)
                    current_date += timedelta(days=1)

            db.session.commit()
            print("✅ Historical prices (5 years) populated")

    except Exception as e:
        print(f"❌ Error seeding historical prices: {e}")
        db.session.rollback()


def seed_test_transactions():
    """Create some test transactions for basic and pro users."""
    try:
        with app.app_context():
            basic = User.query.filter_by(role='basic').first()
            pro = User.query.filter_by(role='pro').first()

            if not basic or not pro:
                print("⚠️  Users not found, skipping transaction seeding")
                return

            # Check if transactions already exist
            if Transaction.query.count() > 0:
                print("📊 Transactions already exist, skipping seeding")
                return

            sample_stocks = Stock.query.limit(3).all()
            if not sample_stocks:
                print("⚠️  No stocks found, skipping transaction seeding")
                return

            for user in [basic, pro]:
                for stock in sample_stocks:
                    qty = random.randint(1, 5)
                    price = stock.current_price
                    total = price * qty

                    txn = Transaction(
                        user_id=user.id,
                        stock_id=stock.id,
                        transaction_type='buy',
                        quantity=qty,
                        price=price,
                        total_amount=total,
                        timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                    )
                    db.session.add(txn)

            db.session.commit()
            print("✅ Test transactions created")

    except Exception as e:
        print(f"❌ Error seeding test transactions: {e}")
        db.session.rollback()


# =============================================================================
# MAIN APPLICATION ROUTES
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'simple-stock-api',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'Simple Stock Market API',
        'version': '1.0.0',
        'endpoints': {
            'auth': ['POST /api/auth/register', 'POST /api/auth/login', 'GET /api/auth/profile'],
            'stocks': ['GET /api/stocks', 'GET /api/stocks/{symbol}/quote'],
            'portfolio': ['GET /api/portfolio', 'POST /api/portfolio/buy', 'POST /api/portfolio/sell',
                          'GET /api/portfolio/transactions']
        },
        'user_roles': {
            'basic': 'Limited access - up to 3 stocks visible',
            'pro': 'Full access - all stocks visible'
        },
        'status': 'running',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'The requested resource was not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error', 'message': 'An unexpected error occurred'}), 500


if __name__ == '__main__':
    print("🚀 Simple Stock Market API starting...")

    # Initialize database with error handling
    try:
        init_database()
        seed_historical_prices()
        seed_test_transactions()
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        print("⚠️  Continuing without full initialization...")

    # Start background price updates
    try:
        price_updater.start()
    except Exception as e:
        print(f"❌ Failed to start price updater: {e}")

    print("📊 Sample users:")
    print("   Basic: user@example.com / user")
    print("   Pro: pro@example.com / prouser")
    print("🔗 API docs: http://localhost:5500/api")
    print("💰 Real-time price updates every 2 seconds")
    print("🏗️  Architecture: Flask Blueprints + Class-based Views")

    try:
        app.run(host='0.0.0.0', port=5500, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        price_updater.stop()