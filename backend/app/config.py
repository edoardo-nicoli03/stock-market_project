# app/config.py
import os
import yaml
from datetime import timedelta
from pathlib import Path

class Config:
    """Application configuration class."""
    
    def __init__(self):
        self._load_config()
    
    def _load_config(self):
        """Load configuration from YAML file and environment variables."""
        config_path = Path(__file__).parent.parent / 'config.yaml'
        
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Database configuration
        self.DATABASE_URL = self._get_env_or_config('DATABASE_URL', config['database']['url'])
        self.SQLALCHEMY_DATABASE_URI = self.DATABASE_URL
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': config['database']['pool_size'],
            'pool_timeout': config['database']['pool_timeout'],
            'pool_recycle': config['database']['pool_recycle']
        }
        
        # JWT configuration
        self.JWT_SECRET_KEY = self._get_env_or_config('JWT_SECRET_KEY', config['jwt']['secret_key'])
        self.JWT_ALGORITHM = config['jwt']['algorithm']
        self.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=config['jwt']['access_token_expire_minutes'])
        self.JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=config['jwt']['refresh_token_expire_days'])
        
        # API configuration
        self.API_HOST = config['api']['host']
        self.API_PORT = config['api']['port']
        self.DEBUG = config['api']['debug']
        self.CORS_ORIGINS = config['api']['cors_origins']
        
        # Stock API configuration
        self.STOCK_UPDATE_INTERVAL = config['stock_api']['update_interval']
        self.STOCK_VOLATILITY_FACTOR = config['stock_api']['volatility_factor']
        self.STOCK_API_KEY = self._get_env_or_config('STOCK_API_KEY', config['stock_api'].get('api_key'))
        
        # Redis configuration
        self.REDIS_URL = self._get_env_or_config('REDIS_URL', config.get('redis', {}).get('url'))
        
        # Security configuration
        self.RATE_LIMIT_DEFAULT = config['security']['rate_limit']['default']
        self.RATE_LIMIT_AUTH = config['security']['rate_limit']['auth']
        self.PASSWORD_HASH_ROUNDS = config['security']['password_hash_rounds']
        
        # Admin configuration
        self.ADMIN_EMAIL = config['admin']['email']
        self.ADMIN_PASSWORD = self._get_env_or_config('ADMIN_PASSWORD', config['admin']['password'])
        self.ADMIN_FIRST_NAME = config['admin']['first_name']
        self.ADMIN_LAST_NAME = config['admin']['last_name']
        
        # Logging configuration
        self.LOG_LEVEL = config['logging']['level']
        self.LOG_FORMAT = config['logging']['format']
    
    def _get_env_or_config(self, env_var, config_value):
        """Get value from environment variable or config file."""
        env_value = os.getenv(env_var)
        if env_value:
            return env_value
        
        # Handle placeholder values like ${VAR_NAME}
        if isinstance(config_value, str) and config_value.startswith('${') and config_value.endswith('}'):
            var_name = config_value[2:-1]
            return os.getenv(var_name, config_value)
        
        return config_value

# Global configuration instance
config = Config()