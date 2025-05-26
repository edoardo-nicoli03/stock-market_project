from decimal import Decimal
from sqlalchemy import func, desc
from app.models import db
from app.models.user import User
from app.models.stock import Stock
from app.models.portfolio import Portfolio, Transaction
from app.services.stock_service import StockService

class PortfolioService:
    """Service class for handling portfolio operations."""
    
    @staticmethod
    def get_user_portfolio(user_id):
        """Get user's complete portfolio with current values."""
        portfolios = Portfolio.query.filter(
            Portfolio.user_id == user_id,
            Portfolio.quantity > 0
        ).all()
        
        portfolio_data = []
        total_value = 0
        total_cost = 0
        
        for portfolio in portfolios:
            stock = portfolio.stock
            latest_price = StockService.get_latest_price(stock.id)
            
            if latest_price:
                current_price = float(latest_price.price)
                market_value = portfolio.quantity * current_price
                cost_basis = portfolio.quantity * float(portfolio.average_price)
                unrealized_gain_loss = market_value - cost_basis
                unrealized_gain_loss_percent = (unrealized_gain_loss / cost_basis) * 100 if cost_basis > 0 else 0
                
                portfolio_item = {
                    'stock_symbol': stock.symbol,
                    'stock_name': stock.name,
                    'quantity': portfolio.quantity,
                    'average_price': float(portfolio.average_price),
                    'current_price': current_price,
                    'market_value': round(market_value, 2),
                    'cost_basis': round(cost_basis, 2),
                    'unrealized_gain_loss': round(unrealized_gain_loss, 2),
                    'unrealized_gain_loss_percent': round(unrealized_gain_loss_percent, 2),
                    'last_updated': latest_price.timestamp.isoformat()
                }
                
                portfolio_data.append(portfolio_item)
                total_value += market_value
                total_cost += cost_basis
        
        total_gain_loss = total_value - total_cost
        total_gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        return {
            'holdings': portfolio_data,
            'summary': {
                'total_value': round(total_value, 2),
                'total_cost': round(total_cost, 2),
                'total_gain_loss': round(total_gain_loss, 2),
                'total_gain_loss_percent': round(total_gain_loss_percent, 2),
                'holdings_count': len(portfolio_data)
            }
        }
    
    @staticmethod
    def buy_stock(user_id, stock_symbol, quantity, price=None):
        """Execute a buy order for a stock."""
        try:
            # Validate inputs
            if quantity <= 0:
                return {'success': False, 'message': 'Quantity must be positive'}
            
            # Get stock
            stock = StockService.get_stock_by_symbol(stock_symbol)
            if not stock:
                return {'success': False, 'message': 'Stock not found'}
            
            # Use current market price if not specified
            if price is None:
                latest_price = StockService.get_latest_price(stock.id)
                if not latest_price:
                    return {'success': False, 'message': 'Stock price not available'}
                price = float(latest_price.price)
            
            total_amount = quantity * price
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                stock_id=stock.id,
                transaction_type='buy',
                quantity=quantity,
                price=Decimal(str(price)),
                total_amount=Decimal(str(total_amount))
            )
            
            # Update or create portfolio entry
            portfolio = Portfolio.query.filter(
                Portfolio.user_id == user_id,
                Portfolio.stock_id == stock.id
            ).first()
            
            if portfolio:
                # Update existing holding
                old_value = portfolio.quantity * float(portfolio.average_price)
                new_value = old_value + total_amount
                new_quantity = portfolio.quantity + quantity
                new_average_price = new_value / new_quantity
                
                portfolio.quantity = new_quantity
                portfolio.average_price = Decimal(str(new_average_price))
            else:
                # Create new holding
                portfolio = Portfolio(
                    user_id=user_id,
                    stock_id=stock.id,
                    quantity=quantity,
                    average_price=Decimal(str(price))
                )
                db.session.add(portfolio)
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully bought {quantity} shares of {stock.symbol}',
                'transaction': transaction.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Transaction failed: {str(e)}'}
    
    @staticmethod
    def sell_stock(user_id, stock_symbol, quantity, price=None):
        """Execute a sell order for a stock."""
        try:
            # Validate inputs
            if quantity <= 0:
                return {'success': False, 'message': 'Quantity must be positive'}
            
            # Get stock
            stock = StockService.get_stock_by_symbol(stock_symbol)
            if not stock:
                return {'success': False, 'message': 'Stock not found'}
            
            # Check if user has sufficient shares
            portfolio = Portfolio.query.filter(
                Portfolio.user_id == user_id,
                Portfolio.stock_id == stock.id
            ).first()
            
            if not portfolio or portfolio.quantity < quantity:
                return {'success': False, 'message': 'Insufficient shares to sell'}
            
            # Use current market price if not specified
            if price is None:
                latest_price = StockService.get_latest_price(stock.id)
                if not latest_price:
                    return {'success': False, 'message': 'Stock price not available'}
                price = float(latest_price.price)
            
            total_amount = quantity * price
            
            # Create transaction record
            transaction = Transaction(
                user_id=user_id,
                stock_id=stock.id,
                transaction_type='sell',
                quantity=quantity,
                price=Decimal(str(price)),
                total_amount=Decimal(str(total_amount))
            )
            
            # Update portfolio
            portfolio.quantity -= quantity
            
            # Remove portfolio entry if no shares left
            if portfolio.quantity == 0:
                db.session.delete(portfolio)
            
            db.session.add(transaction)
            db.session.commit()
            
            return {
                'success': True,
                'message': f'Successfully sold {quantity} shares of {stock.symbol}',
                'transaction': transaction.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'message': f'Transaction failed: {str(e)}'}
    
    @staticmethod
    def get_transaction_history(user_id, page=1, per_page=20):
        """Get user's transaction history."""
        query = Transaction.query.filter(
            Transaction.user_id == user_id
        ).order_by(desc(Transaction.timestamp))
        
        from app.utils.helpers import paginate_query
        return paginate_query(query, page, per_page)
    
    @staticmethod
    def get_portfolio_performance(user_id, days=30):
        """Get portfolio performance analytics."""
        from datetime import datetime, timedelta
        
        # Get current portfolio
        current_portfolio = PortfolioService.get_user_portfolio(user_id)
        
        # Get transactions in the specified period
        start_date = datetime.utcnow() - timedelta(days=days)
        transactions = Transaction.query.filter(
            Transaction.user_id == user_id,
            Transaction.timestamp >= start_date
        ).order_by(Transaction.timestamp).all()
        
        # Calculate performance metrics
        total_invested = 0
        total_divested = 0
        realized_gain_loss = 0
        
        for transaction in transactions:
            if transaction.transaction_type == 'buy':
                total_invested += float(transaction.total_amount)
            else:  # sell
                total_divested += float(transaction.total_amount)
                # Calculate realized gain/loss (simplified)
                # In reality, we'd need to track cost basis more precisely
        
        return {
            'current_portfolio': current_portfolio,
            'period_days': days,
            'total_invested': round(total_invested, 2),
            'total_divested': round(total_divested, 2),
            'net_invested': round(total_invested - total_divested, 2),
            'transactions_count': len(transactions),
            'performance_period': {
                'start_date': start_date.isoformat(),
                'end_date': datetime.utcnow().isoformat()
            }
        }