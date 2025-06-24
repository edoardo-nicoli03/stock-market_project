"""
Authentication Blueprint
Contains all authentication and user-related endpoints
"""

from flask import Blueprint, request, jsonify, g
from models import User, db
from utils import (
    validate_email, validate_password, generate_tokens,
    verify_token, token_required, success_response, error_response
)
from functools import wraps

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    for field in required_fields:
        if not data.get(field):
            return error_response(f"Missing required field: {field}")

    # Validate email
    if not validate_email(data['email']):
        return error_response("Invalid email format")

    # Validate password
    is_valid, message = validate_password(data['password'])
    if not is_valid:
        return error_response(message)

    # Check if user exists
    if User.query.filter_by(email=data['email'].lower()).first():
        return error_response("User already exists", 409)

    # NEW: Get role from request data, default to 'basic'
    role = data.get('role', 'basic')
    if role not in ['basic', 'pro']:
        role = 'basic'  # Fallback to basic for invalid roles

    # Create user with role
    user = User(
        email=data['email'].lower(),
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=role  # NEW: Set user role
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    # Generate tokens
    tokens = generate_tokens(user.id)

    return success_response({
        'user': user.to_dict(),
        'tokens': tokens
    }, "User registered successfully")


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data.get('email') or not data.get('password'):
        return error_response("Email and password are required")

    user = User.query.filter_by(email=data['email'].lower()).first()

    if not user or not user.check_password(data['password']):
        return error_response("Invalid email or password", 401)

    tokens = generate_tokens(user.id)

    return success_response({
        'user': user.to_dict(),
        'tokens': tokens
    }, "Login successful")


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    data = request.get_json()

    if not data.get('refresh_token'):
        return error_response("Refresh token is required")

    user_id = verify_token(data['refresh_token'], 'refresh')
    if not user_id:
        return error_response("Invalid or expired refresh token", 401)

    user = User.query.get(user_id)
    if not user:
        return error_response("User not found", 401)

    tokens = generate_tokens(user.id)
    return success_response({'tokens': tokens}, "Token refreshed successfully")


@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    return success_response({'user': g.current_user.to_dict()})