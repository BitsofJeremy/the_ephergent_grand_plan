"""Authentication service for the Season 03 Story Generator.

This service provides comprehensive authentication and authorization
functionality including user management, API key validation, and
session management.
"""

import logging
from datetime import datetime, timedelta
from functools import wraps
from typing import Optional, Tuple, Dict, Any
from flask import request, jsonify, session, current_app, g
from flask_login import current_user, login_required, login_user, logout_user
from ephergent_generator import db
from ephergent_generator.models import User, APIKey

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Custom exception for authentication errors."""
    def __init__(self, message: str, status_code: int = 401):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthorizationError(Exception):
    """Custom exception for authorization errors."""
    def __init__(self, message: str, status_code: int = 403):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class AuthService:
    """Central authentication service for the application."""

    @staticmethod
    def create_user(username: str, email: str, password: str, is_admin: bool = False) -> User:
        """Create a new user with secure password hashing."""
        try:
            # Check if user already exists
            existing_user = User.query.filter(
                (User.username == username) | (User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    raise ValueError(f"Username '{username}' already exists")
                else:
                    raise ValueError(f"Email '{email}' already exists")

            # Create new user
            user = User(
                username=username,
                email=email,
                is_admin=is_admin
            )
            user.set_password(password)

            db.session.add(user)
            db.session.commit()

            logger.info(f"Created new user: {username} (admin: {is_admin})")
            return user
        except ValueError:
            # Re-raise ValueError as-is
            raise
        except Exception as e:
            logger.error(f"Database error creating user {username}: {str(e)}")
            db.session.rollback()
            raise

    @staticmethod
    def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        try:
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()

            if user and user.is_active and user.check_password(password):
                user.update_login_info()
                db.session.commit()
                logger.info(f"User authenticated successfully: {user.username}")
                return user

            logger.warning(f"Authentication failed for: {username}")
            return None
        except Exception as e:
            logger.error(f"Database error during authentication for {username}: {str(e)}")
            db.session.rollback()
            return None

    @staticmethod
    def authenticate_api_key(api_key: str) -> Optional[APIKey]:
        """Authenticate and validate an API key."""
        if not api_key or not api_key.startswith('ephg_'):
            logger.warning("Invalid API key format")
            return None

        # Find API key by prefix (first 10 chars)
        key_prefix = api_key[:10]
        api_key_obj = APIKey.query.filter_by(
            key_prefix=key_prefix,
            is_active=True
        ).first()

        if not api_key_obj:
            logger.warning(f"API key not found: {key_prefix}...")
            return None

        # Verify the full key
        if not api_key_obj.verify_key(api_key):
            logger.warning(f"API key verification failed: {key_prefix}...")
            return None

        # Check if key can be used (not expired, not rate limited)
        if not api_key_obj.can_be_used():
            if api_key_obj.is_expired():
                logger.warning(f"API key expired: {key_prefix}...")
            elif api_key_obj.is_rate_limited():
                logger.warning(f"API key rate limited: {key_prefix}...")
            return None

        # Record usage
        api_key_obj.record_usage()
        db.session.commit()

        logger.info(f"API key authenticated: {api_key_obj.name}")
        return api_key_obj

    @staticmethod
    def create_api_key(
        user_id: int,
        name: str,
        permissions: Optional[list] = None,
        expires_days: Optional[int] = None,
        rate_limit: int = 1000
    ) -> Tuple[APIKey, str]:
        """Create a new API key for a user."""
        user = User.query.get(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Create the API key
        api_key_obj, raw_key = APIKey.create_key(
            user_id=user_id,
            name=name,
            permissions=permissions,
            expires_days=expires_days,
            rate_limit=rate_limit
        )

        db.session.add(api_key_obj)
        db.session.commit()

        logger.info(f"Created API key '{name}' for user {user.username}")
        return api_key_obj, raw_key

    @staticmethod
    def revoke_api_key(api_key_id: int, user_id: Optional[int] = None) -> bool:
        """Revoke an API key."""
        query = APIKey.query.filter_by(id=api_key_id)
        if user_id:
            query = query.filter_by(user_id=user_id)

        api_key = query.first()
        if not api_key:
            return False

        api_key.deactivate()
        db.session.commit()

        logger.info(f"Revoked API key: {api_key.name}")
        return True

    @staticmethod
    def get_user_api_keys(user_id: int, include_inactive: bool = False) -> list:
        """Get all API keys for a user."""
        query = APIKey.query.filter_by(user_id=user_id)
        if not include_inactive:
            query = query.filter_by(is_active=True)

        return query.order_by(APIKey.created_at.desc()).all()

    @staticmethod
    def validate_session() -> Optional[User]:
        """Validate current user session."""
        if current_user.is_authenticated:
            return current_user
        return None

    @staticmethod
    def login_user_session(user: User, remember: bool = False) -> None:
        """Log in a user and create a session."""
        login_user(user, remember=remember)
        session.permanent = True

        # Set session timeout
        current_app.permanent_session_lifetime = timedelta(hours=24)

        logger.info(f"User logged in: {user.username}")

    @staticmethod
    def logout_user_session() -> None:
        """Log out the current user."""
        if current_user.is_authenticated:
            logger.info(f"User logged out: {current_user.username}")
        logout_user()
        session.clear()


class AuthDecorators:
    """Decorators for route protection and API key authentication."""

    @staticmethod
    def require_login(f):
        """Decorator to require user login for web routes."""
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def require_admin(f):
        """Decorator to require admin privileges."""
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if not current_user.is_admin:
                logger.warning(f"Non-admin user attempted admin access: {current_user.username}")
                return jsonify({
                    'error': 'Admin privileges required',
                    'message': 'You do not have permission to access this resource'
                }), 403
            return f(*args, **kwargs)
        return decorated_function

    @staticmethod
    def require_api_key(permissions: Optional[list] = None):
        """Decorator to require valid API key for API routes."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Check for API key in headers
                api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')

                if api_key and api_key.startswith('Bearer '):
                    api_key = api_key[7:]  # Remove 'Bearer ' prefix

                if not api_key:
                    logger.warning("API request without API key")
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'API key is required in X-API-Key header or Authorization header'
                    }), 401

                # Authenticate API key
                api_key_obj = AuthService.authenticate_api_key(api_key)
                if not api_key_obj:
                    return jsonify({
                        'error': 'Invalid API key',
                        'message': 'The provided API key is invalid, expired, or rate limited'
                    }), 401

                # Check permissions if specified
                if permissions:
                    for permission in permissions:
                        if not api_key_obj.has_permission(permission):
                            logger.warning(
                                f"API key lacks permission '{permission}': {api_key_obj.name}"
                            )
                            return jsonify({
                                'error': 'Insufficient permissions',
                                'message': f'API key does not have required permission: {permission}'
                            }), 403

                # Store API key info in request context
                g.api_key = api_key_obj
                g.api_user = api_key_obj.user

                return f(*args, **kwargs)
            return decorated_function
        return decorator

    @staticmethod
    def require_auth_or_api_key(permissions: Optional[list] = None):
        """Decorator to require either user login or valid API key."""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                # Try session authentication first
                if current_user.is_authenticated:
                    # Check admin permission if required
                    if permissions and 'admin' in permissions and not current_user.is_admin:
                        return jsonify({
                            'error': 'Admin privileges required',
                            'message': 'You do not have permission to access this resource'
                        }), 403
                    g.authenticated_user = current_user
                    return f(*args, **kwargs)

                # Try API key authentication
                api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')

                if api_key and api_key.startswith('Bearer '):
                    api_key = api_key[7:]

                if not api_key:
                    return jsonify({
                        'error': 'Authentication required',
                        'message': 'Please log in or provide a valid API key'
                    }), 401

                # Authenticate API key
                api_key_obj = AuthService.authenticate_api_key(api_key)
                if not api_key_obj:
                    return jsonify({
                        'error': 'Authentication failed',
                        'message': 'Invalid credentials or API key'
                    }), 401

                # Check permissions if specified
                if permissions:
                    for permission in permissions:
                        if not api_key_obj.has_permission(permission):
                            return jsonify({
                                'error': 'Insufficient permissions',
                                'message': f'Required permission: {permission}'
                            }), 403

                # Store API key info in request context
                g.api_key = api_key_obj
                g.authenticated_user = api_key_obj.user

                return f(*args, **kwargs)
            return decorated_function
        return decorator


class RateLimiter:
    """Rate limiting utilities for API endpoints."""

    @staticmethod
    def check_rate_limit(api_key: APIKey) -> Dict[str, Any]:
        """Check rate limit status for an API key."""
        now = datetime.utcnow()

        # Reset hourly counter if needed
        if now >= api_key.hour_reset_time + timedelta(hours=1):
            api_key.current_hour_usage = 0
            api_key.hour_reset_time = now.replace(minute=0, second=0, microsecond=0)
            db.session.commit()

        remaining = max(0, api_key.rate_limit - api_key.current_hour_usage)
        reset_time = api_key.hour_reset_time + timedelta(hours=1)

        return {
            'limit': api_key.rate_limit,
            'remaining': remaining,
            'reset_time': reset_time.isoformat(),
            'is_limited': remaining == 0
        }


# Convenience decorators
require_login = AuthDecorators.require_login
require_admin = AuthDecorators.require_admin
require_api_key = AuthDecorators.require_api_key
require_auth_or_api_key = AuthDecorators.require_auth_or_api_key