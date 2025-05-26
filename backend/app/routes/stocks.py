from flask import Blueprint, request
from app.services.stock_service import StockService
from app.utils.decorators import token_required
from app.utils.helpers import success_response, error_response

stocks_bp = Blueprint('stocks', __name__, url_prefix='/api/stocks')

@stocks_bp.route('', methods=['GET'])
@token_required
def get_stocks():
    """Get all stocks with optional search and pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    search = request.args.get('search')
    
    result = StockService.get_all_stocks(page, per_page, search)
    
    if result is None:
        return error_response("Invalid pagination parameters", 400)
    
    return success_response(result)

@stocks_bp.route('/<symbol>', methods=['GET'])
@token_required
def get_stock(symbol):
    """Get stock information by symbol."""
    stock = StockService.get_stock_by_symbol(symbol)
    
    if not stock:
        return error_response("Stock not found", 404)
    
    return success_response({'stock': stock.to_dict()})

@stocks_bp.route('/<symbol>/quote', methods=['GET'])
@token_required
def get_stock_quote(symbol):
    """Get real-time stock quote."""
    quote = StockService.get_stock_quote(symbol)
    
    if not quote:
        return error_response("Stock not found or no price data available", 404)
    
    return success_response({'quote': quote})

@stocks_bp.route('/<symbol>/history', methods=['GET'])
@token_required
def get_stock_history(symbol):
    """Get historical stock data."""
    days = request.args.get('days', 30, type=int)
    days = min(days, 365)  # Limit to 1 year
    
    history = StockService.get_historical_data(symbol, days)
    
    if not history:
        return error_response("Stock not found", 404)
    
    return success_response({'history': history})

@stocks_bp.route('/search', methods=['GET'])
@token_required
def search_stocks():
    """Search stocks by symbol, name, or sector."""
    query = request.args.get('q')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if not query:
        return error_response("Search query is required", 400)
    
    result = StockService.get_all_stocks(page, per_page, query)
    
    if result is None:
        return error_response("Invalid search parameters", 400)
    
    return success_response(result)

