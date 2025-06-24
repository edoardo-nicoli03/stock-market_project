"""
Simple Stock Market API
A streamlined Flask application following MVC principles with Blueprint architecture
"""

from flask import Flask, jsonify, Blueprint, request, g
from flask.views import MethodView
from flask_cors import CORS
from models import db, User, Stock, HistoricalPrice, Transaction, Portfolio  # Import models and db
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
except ImportError as e:
    print(f"⚠️  Warning: Auth blueprint import failed: {e}")
    print("Creating placeholder auth blueprint...")
    auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Import or create utils
try:
    from utils import token_required, success_response, error_response
except ImportError:
    print("⚠️  Warning: Utils not found, creating basic implementations...")
    from functools import wraps
    import jwt


    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Basic token validation - replace with your actual implementation
            token = request.headers.get('Authorization')
            if not token:
                return jsonify({'error': 'Token is missing'}), 401
            try:
                if token.startswith('Bearer '):
                    token = token.split(' ')[1]
                # For demo purposes, accept any token and use first user
                g.current_user = User.query.first()
                if not g.current_user:
                    return jsonify({'error': 'User not found'}), 401
            except Exception as e:
                return jsonify({'error': 'Token is invalid'}), 401
            return f(*args, **kwargs)

        return decorated


    def success_response(data, message="Success"):
        return jsonify({'success': True, 'message': message, 'data': data})


    def error_response(message, status_code=400):
        return jsonify({'success': False, 'error': message}), status_code

# =============================================================================
# MARKET BLUEPRINT - STOCK AND PORTFOLIO ENDPOINTS
# =============================================================================

# Create market blueprint
market_bp = Blueprint('market', __name__, url_prefix='/api')


# Class-based view for stocks endpoint
class StockListAPI(MethodView):
    """
    Class-based view for handling stock listing
    Implements role-based permissions for stock access
    """
    decorators = [token_required]  # Apply token_required to all methods

    def get(self):
        """
        GET /api/stocks - List stocks with role-based filtering
        """
        search = request.args.get('search', '').strip()

        query = Stock.query
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Stock.symbol.ilike(search_term),
                    Stock.name.ilike(search_term),
                    Stock.sector.ilike(search_term)
                )
            )

        stocks = query.order_by(Stock.symbol).all()

        # Apply role-based permissions
        if hasattr(g, 'current_user') and g.current_user and g.current_user.role == 'basic':
            # Basic users get only first 3 stocks (free tier limitation)
            stocks = stocks[:3]
        # Pro users get full list (no limitation)

        user_role = g.current_user.role if hasattr(g, 'current_user') and g.current_user else 'unknown'

        return success_response({
            'items': [stock.to_dict() for stock in stocks],
            'pagination': {'total': len(stocks)},
            'user_role': user_role,
            'access_level': 'limited' if user_role == 'basic' else 'full'
        })


# Register the class-based view
market_bp.add_url_rule('/stocks', view_func=StockListAPI.as_view('stock_list'))


@market_bp.route('/stocks/<symbol>/quote', methods=['GET'])
@token_required
@limiter.limit(
    lambda: "1000/day" if g.current_user.role == 'pro' else "100/day",
    key_func=lambda: f"{g.current_user.id}:{g.current_user.role}"
)
def get_stock_quote(symbol):
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    if not stock:
        return error_response("Stock not found", 404)

    # Simulate price change for quote
    base_price = float(stock.current_price)
    change = random.uniform(-2.0, 2.0)  # Random change between -$2 and +$2
    change_percent = (change / base_price) * 100 if base_price > 0 else 0

    quote = {
        'stock': stock.to_dict(),
        'price': base_price,
        'change': round(change, 2),
        'change_percent': round(change_percent, 2),
        'volume': random.randint(100000, 1000000),
        'timestamp': datetime.utcnow().isoformat()
    }

    return success_response({'quote': quote})


@market_bp.route('/portfolio', methods=['GET'])
@token_required
def get_portfolio():
    try:
        portfolios = Portfolio.query.filter_by(user_id=g.current_user.id).all()

        holdings = []
        total_value = 0
        total_cost = 0

        for portfolio in portfolios:
            if portfolio.quantity > 0:
                holding = portfolio.to_dict()
                unrealized_gain_loss = holding['market_value'] - holding['cost_basis']
                unrealized_gain_loss_percent = (unrealized_gain_loss / holding['cost_basis']) * 100 if holding[
                                                                                                           'cost_basis'] > 0 else 0

                holding.update({
                    'unrealized_gain_loss': round(unrealized_gain_loss, 2),
                    'unrealized_gain_loss_percent': round(unrealized_gain_loss_percent, 2),
                    'last_updated': portfolio.stock.updated_at.isoformat() if portfolio.stock.updated_at else datetime.utcnow().isoformat()
                })

                holdings.append(holding)
                total_value += holding['market_value']
                total_cost += holding['cost_basis']

        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0

        portfolio_data = {
            'holdings': holdings,
            'summary': {
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_gain_loss': round(total_gain_loss, 2),
                'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                'holdings_count': len(holdings)
            }
        }

        return success_response({'portfolio': portfolio_data})
    except Exception as e:
        return error_response(f"Error fetching portfolio: {str(e)}", 500)


@market_bp.route('/portfolio/buy', methods=['POST'])
@token_required
def buy_stock():
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided")

        if not data.get('symbol') or not data.get('quantity'):
            return error_response("Symbol and quantity are required")

        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                return error_response("Quantity must be positive")
        except (ValueError, TypeError):
            return error_response("Invalid quantity")

        stock = Stock.query.filter_by(symbol=data['symbol'].upper()).first()
        if not stock:
            return error_response("Stock not found")

        price = float(stock.current_price)
        total_amount = quantity * price

        # Create transaction
        transaction = Transaction(
            user_id=g.current_user.id,
            stock_id=stock.id,
            transaction_type='buy',
            quantity=quantity,
            price=Decimal(str(price)),
            total_amount=Decimal(str(total_amount))
        )

        # Update portfolio
        portfolio = Portfolio.query.filter_by(
            user_id=g.current_user.id,
            stock_id=stock.id
        ).first()

        if portfolio:
            # Update existing holding
            old_value = portfolio.quantity * float(portfolio.average_price)
            new_value = old_value + total_amount
            new_quantity = portfolio.quantity + quantity
            portfolio.quantity = new_quantity
            portfolio.average_price = Decimal(str(new_value / new_quantity))
        else:
            # Create new holding
            portfolio = Portfolio(
                user_id=g.current_user.id,
                stock_id=stock.id,
                quantity=quantity,
                average_price=Decimal(str(price))
            )
            db.session.add(portfolio)

        db.session.add(transaction)
        db.session.commit()

        return success_response({
            'transaction': transaction.to_dict()
        }, f"Successfully bought {quantity} shares of {stock.symbol}")

    except Exception as e:
        db.session.rollback()
        return error_response(f"Error processing buy order: {str(e)}", 500)


@market_bp.route('/portfolio/sell', methods=['POST'])
@token_required
def sell_stock():
    try:
        data = request.get_json()
        if not data:
            return error_response("No data provided")

        if not data.get('symbol') or not data.get('quantity'):
            return error_response("Symbol and quantity are required")

        try:
            quantity = int(data['quantity'])
            if quantity <= 0:
                return error_response("Quantity must be positive")
        except (ValueError, TypeError):
            return error_response("Invalid quantity")

        stock = Stock.query.filter_by(symbol=data['symbol'].upper()).first()
        if not stock:
            return error_response("Stock not found")

        portfolio = Portfolio.query.filter_by(
            user_id=g.current_user.id,
            stock_id=stock.id
        ).first()

        if not portfolio or portfolio.quantity < quantity:
            return error_response("Insufficient shares to sell")

        price = float(stock.current_price)
        total_amount = quantity * price

        # Create transaction
        transaction = Transaction(
            user_id=g.current_user.id,
            stock_id=stock.id,
            transaction_type='sell',
            quantity=quantity,
            price=Decimal(str(price)),
            total_amount=Decimal(str(total_amount))
        )

        # Update portfolio
        portfolio.quantity -= quantity
        if portfolio.quantity == 0:
            db.session.delete(portfolio)

        db.session.add(transaction)
        db.session.commit()

        return success_response({
            'transaction': transaction.to_dict()
        }, f"Successfully sold {quantity} shares of {stock.symbol}")

    except Exception as e:
        db.session.rollback()
        return error_response(f"Error processing sell order: {str(e)}", 500)


@market_bp.route('/portfolio/transactions', methods=['GET'])
@token_required
def get_transactions():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)  # Max 100 per page

        transactions = Transaction.query.filter_by(
            user_id=g.current_user.id
        ).order_by(Transaction.timestamp.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        return success_response({
            'items': [transaction.to_dict() for transaction in transactions.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': transactions.total,
                'pages': transactions.pages,
                'has_next': transactions.has_next,
                'has_prev': transactions.has_prev
            }
        })
    except Exception as e:
        return error_response(f"Error fetching transactions: {str(e)}", 500)


@market_bp.route('/stocks/<symbol>/history', methods=['GET'])
@token_required
@limiter.limit(
    lambda: "1000/day" if g.current_user.role == 'pro' else "100/day",
    key_func=lambda: f"{g.current_user.id}:{g.current_user.role}"
)
def get_stock_history(symbol):
    """
    GET /api/stocks/<symbol>/history
    Basic users: last 30 days only
    Pro users: exactly 5+ years of historical data (5 years and 1 month to be safe)
    """
    try:
        # Get the stock
        stock = Stock.query.filter_by(symbol=symbol.upper()).first()
        if not stock:
            return error_response("Stock not found", 404)

        # Filter based on user role
        if g.current_user.role == 'basic':
            # Basic users: only last 30 days
            cutoff = datetime.utcnow().date() - timedelta(days=30)
            query = (
                HistoricalPrice.query
                .filter_by(stock_id=stock.id)
                .filter(HistoricalPrice.date >= cutoff)
            )
            period_description = "30 days"

        elif g.current_user.role == 'pro':
            # Pro users: exactly 5+ years (5 years and 1 month = 1856 days)
            cutoff = datetime.utcnow().date() - timedelta(days=1856)  # 5 years + 1 month
            query = (
                HistoricalPrice.query
                .filter_by(stock_id=stock.id)
                .filter(HistoricalPrice.date >= cutoff)
            )
            period_description = "5+ years"

        else:
            # Unknown role - default to basic access
            cutoff = datetime.utcnow().date() - timedelta(days=30)
            query = (
                HistoricalPrice.query
                .filter_by(stock_id=stock.id)
                .filter(HistoricalPrice.date >= cutoff)
            )
            period_description = "30 days (default)"

        # Execute query and order by date
        history = query.order_by(HistoricalPrice.date.asc()).all()

        # Build response
        return success_response({
            'symbol': stock.symbol,
            'name': stock.name,
            'current_price': float(stock.current_price),
            'history': [hp.to_dict() for hp in history],
            'period_description': period_description,
            'data_points': len(history),
            'user_role': g.current_user.role,
            'access_level': 'pro' if g.current_user.role == 'pro' else 'basic'
        })

    except Exception as e:
        return error_response(f"Error fetching stock history: {str(e)}", 500)


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