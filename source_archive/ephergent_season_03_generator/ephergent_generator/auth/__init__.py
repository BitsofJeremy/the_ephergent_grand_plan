"""Authentication blueprint for the Season 03 Story Generator.

This blueprint handles user authentication including login, logout,
and authentication-related web interface routes.
"""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

from ephergent_generator.auth import routes