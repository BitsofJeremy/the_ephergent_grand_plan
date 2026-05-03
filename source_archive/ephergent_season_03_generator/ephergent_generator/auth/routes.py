"""Authentication routes for login, logout, and user management."""

import logging
from flask import render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import current_user, logout_user
from ephergent_generator.auth import auth_bp
from ephergent_generator.services.auth_service import AuthService
from ephergent_generator import db

logger = logging.getLogger(__name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and form handler."""
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('auth/login.html')

        try:
            # Authenticate user
            user = AuthService.authenticate_user(username, password)
            if user:
                AuthService.login_user_session(user, remember=remember)
                flash(f'Welcome back, {user.username}!', 'success')

                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page and not next_page.startswith('http'):
                    return redirect(next_page)
                return redirect(url_for('main.index'))
            else:
                flash('Invalid username or password.', 'error')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            flash('An error occurred during login. Please try again.', 'error')

    return render_template('auth/login.html')


@auth_bp.route('/logout')
def logout():
    """Logout and redirect to home."""
    AuthService.logout_user_session()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


@auth_bp.route('/profile')
def profile():
    """User profile page."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    # Get user's API keys
    api_keys = AuthService.get_user_api_keys(current_user.id)

    return render_template('auth/profile.html',
                         user=current_user,
                         api_keys=api_keys)


@auth_bp.route('/api-keys', methods=['GET'])
def api_keys():
    """API keys management page."""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

    api_keys = AuthService.get_user_api_keys(current_user.id, include_inactive=True)

    return render_template('auth/api_keys.html', api_keys=api_keys)


@auth_bp.route('/api-keys/create', methods=['POST'])
def create_api_key():
    """Create a new API key."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        data = request.get_json()
        if not data:
            data = request.form.to_dict()

        name = data.get('name', '').strip()
        permissions = data.get('permissions', [])
        expires_days = data.get('expires_days')
        rate_limit = int(data.get('rate_limit', 1000))

        if not name:
            return jsonify({'error': 'API key name is required'}), 400

        # Convert expires_days to int if provided
        if expires_days:
            try:
                expires_days = int(expires_days)
                if expires_days <= 0:
                    expires_days = None
            except (ValueError, TypeError):
                expires_days = None

        # Create the API key
        api_key_obj, raw_key = AuthService.create_api_key(
            user_id=current_user.id,
            name=name,
            permissions=permissions,
            expires_days=expires_days,
            rate_limit=rate_limit
        )

        return jsonify({
            'success': True,
            'message': 'API key created successfully',
            'api_key': raw_key,  # Only shown once!
            'key_info': api_key_obj.to_dict()
        })

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"API key creation error: {str(e)}")
        return jsonify({'error': 'Failed to create API key'}), 500


@auth_bp.route('/api-keys/<int:key_id>/revoke', methods=['POST'])
def revoke_api_key(key_id):
    """Revoke an API key."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Authentication required'}), 401

    try:
        success = AuthService.revoke_api_key(key_id, current_user.id)
        if success:
            return jsonify({
                'success': True,
                'message': 'API key revoked successfully'
            })
        else:
            return jsonify({'error': 'API key not found'}), 404

    except Exception as e:
        logger.error(f"API key revocation error: {str(e)}")
        return jsonify({'error': 'Failed to revoke API key'}), 500


@auth_bp.route('/status')
def auth_status():
    """Get current authentication status."""
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user': current_user.to_dict()
        })
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        })


# Error handlers
@auth_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized access."""
    if request.is_json:
        return jsonify({
            'error': 'Authentication required',
            'message': 'Please log in to access this resource'
        }), 401

    flash('Please log in to access that page.', 'warning')
    return redirect(url_for('auth.login', next=request.url))


@auth_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden access."""
    if request.is_json:
        return jsonify({
            'error': 'Access forbidden',
            'message': 'You do not have permission to access this resource'
        }), 403

    flash('You do not have permission to access that resource.', 'error')
    return redirect(url_for('main.index'))