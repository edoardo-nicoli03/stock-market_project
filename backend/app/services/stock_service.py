import random
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import desc
from app.models import db
from app.models.stock import Stock, StockPrice
from app.config import config

class StockService:
    """Service class for handling stock operations and real-time data simulation."""
    
    def __init__(self):
        self.update_thread = None
        self.stop_updates = False
    
    @staticmethod
    def get_all_stocks(page=1, per_page=20, search=None):
        """Get all stocks with optional search and pagination."""
        query = Stock.query.filter(Stock.is_active == True)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                db.or_(
                    Stock.symbol.ilike(search_term),
                    Stock.name.ilike(search_term),
                    Stock.sector.ilike(search_term)
                )
            )
        
        from app.utils.helpers import paginate_query
        return paginate_query(query.order_by(Stock.symbol), page, per_page)
    
    @staticmethod
    def get_stock_by_symbol(symbol):
        """Get stock by symbol."""
        return Stock.query.filter(
            Stock.symbol == symbol.upper(),
            Stock.is_active == True
        ).first()
    
    @staticmethod
    def get_latest_price(stock_id):
        """Get latest price for a stock."""
        return StockPrice.query.filter(
            StockPrice.stock_id == stock_id
        ).order_by(desc(StockPrice.timestamp)).first()
    
    @staticmethod
    def get_stock_quote(symbol):
        """Get real-time quote for a stock."""
        stock = StockService.get_stock_by_symbol(symbol)
        if not stock:
            return None
        
        latest_price = StockService.get_latest_price(stock.id)
        if not latest_price:
            return None
        
        # Get previous price for change calculation
        previous_price = StockPrice.query.filter(
            StockPrice.stock_id == stock.id,
            StockPrice.timestamp < latest_price.timestamp
        ).order_by(desc(StockPrice.timestamp)).first()
        
        change = 0
        change_percent = 0
        if previous_price:
            change = float(latest_price.price - previous_price.price)
            change_percent = (change / float(previous_price.price)) * 100
        
        return {
            'stock': stock.to_dict(),
            'price': float(latest_price.price),
            'open': float(latest_price.open_price) if latest_price.open_price else None,
            'high': float(latest_price.high_price) if latest_price.high_price else None,
            'low': float(latest_price.low_price) if latest_price.low_price else None,
            'volume': latest_price.volume,
            'change': round(change, 2),
            'change_percent': round(change_percent, 2),
            'timestamp': latest_price.timestamp.isoformat()
        }
    
    @staticmethod
    def get_historical_data(symbol, days=30):
        """Get historical price data for a stock."""
        stock = StockService.get_stock_by_symbol(symbol)
        if not stock:
            return None
        
        start_date = datetime.utcnow() - timedelta(days=days)
        prices = StockPrice.query.filter(
            StockPrice.stock_id == stock.id,
            StockPrice.timestamp >= start_date
        ).order_by(StockPrice.timestamp).all()
        
        return {
            'stock': stock.to_dict(),
            'prices': [price.to_dict() for price in prices]
        }
    
    @staticmethod
    def simulate_price_update(stock_id):
        """Simulate real-time price update for a stock."""
        latest_price = StockService.get_latest_price(stock_id)
        if not latest_price:
            return None
        
        # Calculate new price with volatility
        volatility = config.STOCK_VOLATILITY_FACTOR
        current_price = float(latest_price.price)
        
        # Random walk with slight upward bias (0.1%)
        change_percent = random.normalvariate(0.001, volatility)
        new_price = current_price * (1 + change_percent)
        
        # Ensure price doesn't go below 0.01
        new_price = max(0.01, new_price)
        
        # Create new price entry
        new_stock_price = StockPrice(
            stock_id=stock_id,
            price=Decimal(str(round(new_price, 2))),
            open_price=latest_price.open_price,
            high_price=Decimal(str(max(float(latest_price.high_price or 0), new_price))),
            low_price=Decimal(str(min(float(latest_price.low_price or float('inf')), new_price))),
            volume=random.randint(1000, 10000),
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_stock_price)
        db.session.commit()
        
        return new_stock_price
    
    def start_real_time_updates(self):
        """Start real-time price updates in background thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        self.stop_updates = False
        self.update_thread = threading.Thread(target=self._update_prices_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
    
    def stop_real_time_updates(self):
        """Stop real-time price updates."""
        self.stop_updates = True
        if self.update_thread:
            self.update_thread.join(timeout=5)
    
    def _update_prices_loop(self):
        """Background loop to update stock prices."""
        while not self.stop_updates:
            try:
                # Get all active stocks
                stocks = Stock.query.filter(Stock.is_active == True).all()
                
                for stock in stocks:
                    if self.stop_updates:
                        break
                    self.simulate_price_update(stock.id)
                
                # Sleep for the configured interval
                time.sleep(config.STOCK_UPDATE_INTERVAL)
                
            except Exception as e:
                print(f"Error updating stock prices: {e}")
                time.sleep(5)  # Wait before retrying

# Global stock service instance
stock_service = StockService()