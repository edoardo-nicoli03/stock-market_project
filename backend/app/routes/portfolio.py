from flask import Blueprint, request, g
from app.services.portfolio_service import PortfolioService
from app.utils.decorators import token_required
from app.utils.helpers import success_response, error_response

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/portfolio')

@portfolio_bp.route('', methods=['GET'])
@token_required
def get_portfolio():
    """Get user's portfolio."""
    portfolio = PortfolioService.get_user_portfolio(g.current_user.id)
    return success_response({'portfolio': portfolio})

@portfolio_bp.route('/buy', methods=['POST'])
@token_required
def buy_stock():
    """Buy stocks."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", 400)
    
    required_fields = ['symbol', 'quantity']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
    
    try:
        quantity = int(data['quantity'])
        price = float(data['price']) if data.get('price') else None
    except (ValueError, TypeError):
        return error_response("Invalid quantity or price format", 400)
    
    result = PortfolioService.buy_stock(
        g.current_user.id,
        data['symbol'],
        quantity,
        price
    )
    
    if result['success']:
        return success_response(result, result['message'])
    else:
        return error_response(result['message'], 400)

@portfolio_bp.route('/sell', methods=['POST'])
@token_required
def sell_stock():
    """Sell stocks."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", 400)
    
    required_fields = ['symbol', 'quantity']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
    
    try:
        quantity = int(data['quantity'])
        price = float(data['price']) if data.get('price') else None
    except (ValueError, TypeError):
        return error_response("Invalid quantity or price format", 400)
    
    result = PortfolioService.sell_stock(
        g.current_user.id,
        data['symbol'],
        quantity,
        price
    )
    
    if result['success']:
        return success_response(result, result['message'])
    else:
        return error_response(result['message'], 400)

@portfolio_bp.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    """Get user's transaction history."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    result = PortfolioService.get_transaction_history(g.current_user.id, page, per_page)
    
    if result is None:
        return error_response("Invalid pagination parameters", 400)
    
    return success_response(result)

@portfolio_bp.route('/performance', methods=['GET'])
@token_required
def get_performance():
    """Get portfolio performance analytics."""
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)  # Limit to 1 year
    
    performance = PortfolioService.get_portfolio_performance(g.current_user.id, days)
    return success_response({'performance': performance})