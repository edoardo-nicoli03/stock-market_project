from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.models import db, migrate
from app.config import config

def create_app():
    """Create and configure Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_URL
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = config.SQLALCHEMY_ENGINE_OPTIONS
    app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # CORS configuration
    CORS(app, origins=config.CORS_ORIGINS)
    
    # Rate limiting
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[config.RATE_LIMIT_DEFAULT]
    )
    
    limiter.init_app(app)   
    
    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.stocks import stocks_bp
    from app.routes.portfolio import portfolio_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(stocks_bp)
    app.register_blueprint(portfolio_bp)
    
    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        return {'status': 'healthy', 'service': 'stock-market-api'}
    
    # API documentation endpoint
    @app.route('/api', methods=['GET'])
    def api_info():
        return {
            'name': 'Stock Market API',
            'version': '1.0.0',
            'endpoints': {
                'auth': {
                    'POST /api/auth/register': 'Register new user',
                    'POST /api/auth/login': 'Login user',
                    'POST /api/auth/refresh': 'Refresh access token',
                    'GET /api/auth/profile': 'Get user profile',
                    'PUT /api/auth/profile': 'Update user profile'
                },
                'stocks': {
                    'GET /api/stocks': 'List all stocks',
                    'GET /api/stocks/{symbol}': 'Get stock details',
                    'GET /api/stocks/{symbol}/quote': 'Get real-time quote',
                    'GET /api/stocks/{symbol}/history': 'Get historical data',
                    'GET /api/stocks/search': 'Search stocks'
                },
                'portfolio': {
                    'GET /api/portfolio': 'Get user portfolio',
                    'POST /api/portfolio/buy': 'Buy stocks',
                    'POST /api/portfolio/sell': 'Sell stocks',
                    'GET /api/portfolio/transactions': 'Get transaction history',
                    'GET /api/portfolio/performance': 'Get portfolio performance'
                }
            }
        }
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {'success': False, 'message': 'Endpoint not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'success': False, 'message': 'Internal server error'}, 500
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {'success': False, 'message': 'Rate limit exceeded'}, 429
    
    return app
