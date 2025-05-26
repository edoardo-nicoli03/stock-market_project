from flask import Blueprint, request, g
from app.models import db
from app.models.user import User
from app.services.auth_service import AuthService
from app.utils.decorators import token_required
from app.utils.helpers import validate_email, validate_password, success_response, error_response

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", 400)
    
    # Validate required fields
    required_fields = ['email', 'password', 'first_name', 'last_name']
    missing_fields = [field for field in required_fields if not data.get(field)]
    
    if missing_fields:
        return error_response(f"Missing required fields: {', '.join(missing_fields)}", 400)
    
    # Validate email
    if not validate_email(data['email']):
        return error_response("Invalid email format", 400)
    
    # Validate password
    is_valid_password, password_message = validate_password(data['password'])
    if not is_valid_password:
        return error_response(password_message, 400)
    
    # Check if user already exists
    if User.query.filter_by(email=data['email'].lower()).first():
        return error_response("User with this email already exists", 409)
    
    try:
        # Create new user
        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate tokens
        tokens = AuthService.generate_tokens(user.id)
        
        return success_response({
            'user': user.to_dict(),
            'tokens': tokens
        }, "User registered successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response("Registration failed", 500)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Authenticate user and return tokens."""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return error_response("Email and password are required", 400)
    
    # Find user
    user = User.query.filter_by(email=data['email'].lower()).first()
    
    if not user or not user.check_password(data['password']):
        return error_response("Invalid email or password", 401)
    
    if not user.is_active:
        return error_response("Account is inactive", 401)
    
    # Generate tokens
    tokens = AuthService.generate_tokens(user.id)
    
    return success_response({
        'user': user.to_dict(),
        'tokens': tokens
    }, "Login successful")

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Refresh access token using refresh token."""
    data = request.get_json()
    
    if not data or not data.get('refresh_token'):
        return error_response("Refresh token is required", 400)
    
    # Refresh tokens
    tokens = AuthService.refresh_access_token(data['refresh_token'])
    
    if not tokens:
        return error_response("Invalid or expired refresh token", 401)
    
    return success_response({'tokens': tokens}, "Token refreshed successfully")

@auth_bp.route('/profile', methods=['GET'])
@token_required
def get_profile():
    """Get current user profile."""
    return success_response({'user': g.current_user.to_dict()})

@auth_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile():
    """Update current user profile."""
    data = request.get_json()
    
    if not data:
        return error_response("No data provided", 400)
    
    try:
        # Update allowed fields
        if 'first_name' in data:
            g.current_user.first_name = data['first_name']
        if 'last_name' in data:
            g.current_user.last_name = data['last_name']
        
        db.session.commit()
        
        return success_response({'user': g.current_user.to_dict()}, "Profile updated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response("Profile update failed", 500)
