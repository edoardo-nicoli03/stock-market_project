"""
Utility Functions and Helpers
Contains validation, authentication, and helper functions
"""

from flask import request, jsonify, g, current_app
from models import User
import jwt
import re
from datetime import datetime, timedelta
from functools import wraps


def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    return True, "Password is valid"


def generate_tokens(user_id):
    # Access token (30 minutes)
    access_payload = {
        'user_id': user_id,
        'token_type': 'access',
        'exp': datetime.utcnow() + timedelta(minutes=30)
    }
    access_token = jwt.encode(access_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    # Refresh token (7 days)
    refresh_payload = {
        'user_id': user_id,
        'token_type': 'refresh',
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    refresh_token = jwt.encode(refresh_payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'token_type': 'Bearer',
        'expires_in': 1800  # 30 minutes
    }


def verify_token(token, token_type='access'):
    try:
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        if payload.get('token_type') != token_type:
            return None
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Token is missing'}), 401

        try:
            token = token.split(' ')[1]  # Remove 'Bearer ' prefix
        except IndexError:
            return jsonify({'error': 'Invalid token format'}), 401

        user_id = verify_token(token)
        if not user_id:
            return jsonify({'error': 'Token is invalid or expired'}), 401

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 401

        g.current_user = user
        return f(*args, **kwargs)

    return decorated


def success_response(data=None, message="Success"):
    response = {'success': True, 'message': message}
    if data is not None:
        response['data'] = data
    return jsonify(response)


def error_response(message="Error", status_code=400):
    return jsonify({'success': False, 'message': message}), status_code