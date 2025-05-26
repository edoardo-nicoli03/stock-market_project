from functools import wraps
from flask import request, jsonify, g
from app.services.auth_service import AuthService
from app.models.user import User

def token_required(f):
    """Decorator to require valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if auth_header:
            try:
                token = auth_header.split(" ")[1]  # Bearer <token>
            except IndexError:
                return jsonify({'error': 'Invalid token format'}), 401
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        # Verify token
        payload = AuthService.verify_token(token)
        if not payload:
            return jsonify({'error': 'Token is invalid or expired'}), 401
        
        # Get user
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return jsonify({'error': 'User not found or inactive'}), 401
        
        # Store user in request context
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated

def admin_required(f):
    """Decorator to require admin privileges."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(g, 'current_user') or not g.current_user.is_admin:
            return jsonify({'error': 'Admin privileges required'}), 403
        return f(*args, **kwargs)
    
    return decorated