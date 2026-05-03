"""Admin blueprint for character and system configuration management.

This blueprint provides comprehensive administrative interfaces for:
- Character management (CRUD operations, image generation)
- System configuration management with version control
- Administrative task monitoring and management
- Database-driven configuration over legacy JSON/markdown files
"""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

from ephergent_generator.admin import routes
