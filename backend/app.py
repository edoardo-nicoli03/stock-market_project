"""
Simple Stock Market API
A streamlined Flask application following MVC principles
"""

from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import re
from datetime import datetime, timedelta
from decimal import Decimal
import random
import threading
import time
from functools import wraps

# =============================================================================
# APP CONFIGURATION
# =============================================================================

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

db = SQLAlchemy(app)
CORS(app)

# =============================================================================
# MODELS (M in MVC)
# =============================================================================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
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

# =============================================================================
# UTILITIES & HELPERS
# =============================================================================

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"

def generate_tokens(user_id):
    # Access token (30 minutes)
    access_payload = {
        'user_id': user_id,
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }
    access_token = jwt.encode(access_payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    # Refresh token (7 days)
    refresh_payload = {
        'user_id': user_id,
        'token_type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_payload, app.config['SECRET_KEY'], algorithm='HS256')
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 1800  # 30 minutes
    }

def verify_token(token, token_type='access'):
    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload.get('token_type') != token_type:
            return None
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401
        
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401
        
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def success_response(data=None, message="Success"):
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response)

def error_response(message="Error", status_code=400):
    return jsonify({'success': False, 'message': message}), status_code

# =============================================================================
# CONTROLLERS (C in MVC) - Authentication Routes
# =============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return error_response(f"Missing required field: {field}")
    
    # Validate email
    if not validate_email(data['email']):
        return error_response("Invalid email format")
    
    # Validate password
    is_valid, message = validate_password(data['password'])
    if not is_valid:
        return error_response(message)
    
    # Check if user exists
    if User.query.filter_by(email=data['email'].lower()).first():
        return error_response("User already exists", 409)
    
    # Create user
    user = User(
        email=data['email'].lower(),
        first_name=data['first_name'],
        last_name=data['last_name']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    # Generate tokens
    tokens = generate_tokens(user.id)
    
    return success_response({
        'user': user.to_dict(),
        'tokens': tokens
    }, "User registered successfully")

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return error_response("Email and password are required")
    
    user = User.query.filter_by(email=data['email'].lower()).first()
    
    if not user or not user.check_password(data['password']):
        return error_response("Invalid email or password", 401)
    
    tokens = generate_tokens(user.id)
    
    return success_response({
        'user': user.to_dict(),
        'tokens': tokens
    }, "Login successful")

@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()
    
    if not data.get('refresh_token'):
        return error_response("Refresh token is required")
    
    user_id = verify_token(data['refresh_token'], 'refresh')
    if not user_id:
        return error_response("Invalid or expired refresh token", 401)
    
    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 401)
    
    tokens = generate_tokens(user.id)
    return success_response({'tokens': tokens}, "Token refreshed successfully")

@app.route('/api/auth/profile', methods=['GET'])
@token_required
def get_profile():
    return success_response({'user': g.current_user.to_dict()})

# =============================================================================
# CONTROLLERS (C in MVC) - Stock Routes
# =============================================================================

@app.route('/api/stocks', methods=['GET'])
@token_required
def get_stocks():
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
    
    return success_response({
        'items': [stock.to_dict() for stock in stocks],
        'pagination': {'total': len(stocks)}
    })

@app.route('/api/stocks/<symbol>/quote', methods=['GET'])
@token_required
def get_stock_quote(symbol):
    stock = Stock.query.filter_by(symbol=symbol.upper()).first()
    if not stock:
        return error_response("Stock not found", 404)
    
    # Simulate price change for quote
    base_price = float(stock.current_price)
    change = random.uniform(-2.0, 2.0)  # Random change between -$2 and +$2
    change_percent = (change / base_price) * 100
    
    quote = {
        'stock': stock.to_dict(),
        'price': base_price,
        'change': round(change, 2),
        'change_percent': round(change_percent, 2),
        'volume': random.randint(100000, 1000000),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    return success_response({'quote': quote})

# =============================================================================
# CONTROLLERS (C in MVC) - Portfolio Routes
# =============================================================================

@app.route('/api/portfolio', methods=['GET'])
@token_required
def get_portfolio():
    portfolios = Portfolio.query.filter_by(user_id=g.current_user.id).all()
    
    holdings = []
    total_value = 0
    total_cost = 0
    
    for portfolio in portfolios:
        if portfolio.quantity > 0:
            holding = portfolio.to_dict()
            unrealized_gain_loss = holding['market_value'] - holding['cost_basis']
            unrealized_gain_loss_percent = (unrealized_gain_loss / holding['cost_basis']) * 100 if holding['cost_basis'] > 0 else 0
            
            holding.update({
                'unrealized_gain_loss': round(unrealized_gain_loss, 2),
                'unrealized_gain_loss_percent': round(unrealized_gain_loss_percent, 2),
                'last_updated': portfolio.stock.updated_at.isoformat()
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

@app.route('/api/portfolio/buy', methods=['POST'])
@token_required
def buy_stock():
    data = request.get_json()
    
    if not data.get('symbol') or not data.get('quantity'):
        return error_response("Symbol and quantity are required")
    
    try:
        quantity = int(data['quantity'])
        if quantity <= 0:
            return error_response("Quantity must be positive")
    except ValueError:
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

@app.route('/api/portfolio/sell', methods=['POST'])
@token_required
def sell_stock():
    data = request.get_json()
    
    if not data.get('symbol') or not data.get('quantity'):
        return error_response("Symbol and quantity are required")
    
    try:
        quantity = int(data['quantity'])
        if quantity <= 0:
            return error_response("Quantity must be positive")
    except ValueError:
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

@app.route('/api/portfolio/transactions', methods=['GET'])
@token_required
def get_transactions():
    transactions = Transaction.query.filter_by(
        user_id=g.current_user.id
    ).order_by(Transaction.timestamp.desc()).limit(50).all()
    
    return success_response({
        'items': [transaction.to_dict() for transaction in transactions],
        'pagination': {'total': len(transactions)}
    })

# =============================================================================
# BACKGROUND PRICE UPDATES
# =============================================================================

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
    with app.app_context():
        db.create_all()
        
        # Check if stocks already exist
        if Stock.query.count() > 0:
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
        
        # Create sample user
        user = User(
            email='user@example.com',
            first_name='Edo',
            last_name='Gay'
        )
        user.set_password('user')
        db.session.add(user)
        
        db.session.commit()
        print("✅ Database initialized with sample data")

# =============================================================================
# MAIN APPLICATION
# =============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'simple-stock-api'})

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'name': 'Simple Stock Market API',
        'version': '1.0.0',
        'endpoints': {
            'auth': ['POST /api/auth/register', 'POST /api/auth/login', 'GET /api/auth/profile'],
            'stocks': ['GET /api/stocks', 'GET /api/stocks/{symbol}/quote'],
            'portfolio': ['GET /api/portfolio', 'POST /api/portfolio/buy', 'POST /api/portfolio/sell', 'GET /api/portfolio/transactions']
        }
    })

if __name__ == '__main__':
    # Initialize database
    init_database()
    
    # Start background price updates
    price_updater.start()
    
    print("🚀 Simple Stock Market API starting...")
    print("📊 Sample user: user@example.com / user")
    print("🔗 API docs: http://localhost:5500/api")
    print("💰 Real-time price updates every 2 seconds")
    
    try:
        app.run(host='0.0.0.0', port=5500, debug=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        price_updater.stop()