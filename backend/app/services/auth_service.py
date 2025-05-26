import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from app.models.user import User
from app.config import config

class AuthService:
    """Service class for handling authentication operations."""
    
    @staticmethod
    def generate_tokens(user_id):
        """Generate access and refresh tokens for a user."""
        now = datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user_id,
            'token_type': 'access',
            'iat': now,
            'exp': now + config.JWT_ACCESS_TOKEN_EXPIRES
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user_id,
            'token_type': 'refresh',
            'iat': now,
            'exp': now + config.JWT_REFRESH_TOKEN_EXPIRES
        }
        
        access_token = jwt.encode(
            access_payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            config.JWT_SECRET_KEY,
            algorithm=config.JWT_ALGORITHM
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': config.JWT_ACCESS_TOKEN_EXPIRES.total_seconds()
        }
    
    @staticmethod
    def verify_token(token, token_type='access'):
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                config.JWT_SECRET_KEY,
                algorithms=[config.JWT_ALGORITHM]
            )
            
            # Check token type
            if payload.get('token_type') != token_type:
                return None
            
            # Check expiration
            if datetime.utcnow() > datetime.fromtimestamp(payload['exp']):
                return None
            
            return payload
            
        except jwt.InvalidTokenError:
            return None
    
    @staticmethod
    def refresh_access_token(refresh_token):
        """Generate new access token using refresh token."""
        payload = AuthService.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
        
        return AuthService.generate_tokens(user.id)
