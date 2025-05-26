import os
from app import create_app
from app.services.stock_service import stock_service

app = create_app()

# Set the app instance for the stock service
stock_service.set_app(app)

if __name__ == '__main__':
    # Start real-time stock updates
    stock_service.start_real_time_updates()
    
    try:
        app.run(
            host=app.config.get('API_HOST', '0.0.0.0'),
            port=app.config.get('API_PORT', 5500),
            debug=app.config.get('DEBUG', False)
        )
    finally:
        # Stop real-time updates when app shuts down
        stock_service.stop_real_time_updates()