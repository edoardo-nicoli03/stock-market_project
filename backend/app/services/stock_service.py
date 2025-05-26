import random
import threading
import time
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import desc, func
from flask import current_app
from app.models import db
from app.models.stock import Stock, StockPrice
from app.config import config

class StockService:
    """Service class for handling stock operations and real-time data simulation."""
    
    def __init__(self):
        self.update_thread = None
        self.cleanup_thread = None
        self.stop_updates = False
        self._app = None
        self.update_counter = 0  # Track updates for cleanup timing
    
    def set_app(self, app):
        """Set the Flask app instance for background thread."""
        self._app = app
    
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
    
    def cleanup_old_prices(self):
        """Remove old price data to keep database lean."""
        try:
            # Keep only last 7 days of data (configurable)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Delete old prices in batches to avoid locking
            deleted_count = 0
            batch_size = 1000
            
            while True:
                # Find old records to delete
                old_prices = StockPrice.query.filter(
                    StockPrice.timestamp < cutoff_date
                ).limit(batch_size).all()
                
                if not old_prices:
                    break
                
                # Delete batch
                for price in old_prices:
                    db.session.delete(price)
                
                db.session.commit()
                deleted_count += len(old_prices)
                
                # Small delay to avoid overwhelming the database
                time.sleep(0.1)
            
            if deleted_count > 0:
                print(f"Cleaned up {deleted_count} old price records")
                
        except Exception as e:
            print(f"Error cleaning up old prices: {e}")
            db.session.rollback()
    def simulate_price_update(self, stock_id):
        """Simulate real-time price update for a stock."""
        # This method now requires app context
        latest_price = StockService.get_latest_price(stock_id)
        if not latest_price:
            return None
        
        # Calculate new price with volatility (reduced for faster updates)
        volatility = config.STOCK_VOLATILITY_FACTOR * 0.3  # Reduce volatility for faster updates
        current_price = float(latest_price.price)
        
        # Random walk with slight upward bias (0.01% for faster updates)
        change_percent = random.normalvariate(0.0001, volatility)
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
            volume=random.randint(100, 1000),  # Smaller volume for faster updates
            timestamp=datetime.utcnow()
        )
        
        db.session.add(new_stock_price)
        db.session.commit()
        
        return new_stock_price
    
    def start_real_time_updates(self):
        """Start real-time price updates in background thread."""
        if self.update_thread and self.update_thread.is_alive():
            return
        
        # Get current app instance
        if not self._app:
            from flask import current_app
            self._app = current_app._get_current_object()
        
        self.stop_updates = False
        self.update_thread = threading.Thread(target=self._update_prices_loop)
        self.update_thread.daemon = True
        self.update_thread.start()
        print("Started real-time stock price updates")
    
    def stop_real_time_updates(self):
        """Stop real-time price updates."""
        self.stop_updates = True
        if self.update_thread:
            self.update_thread.join(timeout=5)
        if self.cleanup_thread:
            self.cleanup_thread.join(timeout=5)
        print("Stopped real-time stock price updates")
    
    def _update_prices_loop(self):
        """Background loop to update stock prices."""
        while not self.stop_updates:
            try:
                # Use app context for database operations
                with self._app.app_context():
                    # Get all active stocks
                    stocks = Stock.query.filter(Stock.is_active == True).all()
                    
                    for stock in stocks:
                        if self.stop_updates:
                            break
                        try:
                            self.simulate_price_update(stock.id)
                        except Exception as e:
                            print(f"Error updating price for {stock.symbol}: {e}")
                            continue
                    
                    # Increment update counter
                    self.update_counter += 1
                    
                    # Clean up old data every 300 updates (approximately every 10 minutes at 2s intervals)
                    if self.update_counter % 300 == 0:
                        print("Running price data cleanup...")
                        self.cleanup_old_prices()
                
                # Sleep for 1-2 seconds (randomized for more realistic feel)
                sleep_time = random.uniform(1.0, 2.0)
                time.sleep(sleep_time)
                
            except Exception as e:
                print(f"Error in price update loop: {e}")
                time.sleep(2)  # Wait before retrying

# Global stock service instance
stock_service = StockService()