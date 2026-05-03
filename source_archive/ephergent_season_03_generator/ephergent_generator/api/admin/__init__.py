"""Admin API Blueprint for Ephergent Season 03 Generator.

This module provides administrative REST API endpoints for managing:
- Character configurations and versions
- System-wide configuration settings
- Background administrative tasks

All endpoints require admin authentication via session or API key with 'admin' permission.
"""

from flask import Blueprint
from flask_restx import Api

# Create admin API blueprint
admin_api_blueprint = Blueprint('admin_api', __name__, url_prefix='/api/admin')

# Create Flask-RESTX API instance
api = Api(
    admin_api_blueprint,
    version='1.0',
    title='Ephergent Admin API',
    description='Administrative REST API for system configuration and management',
    doc='/swagger',
    validate=True,
    authorizations={
        'apikey': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'API Key authentication. Format: X-API-Key: ephg_your_api_key'
        },
        'bearer': {
            'type': 'apiKey',
            'in': 'header',
            'name': 'Authorization',
            'description': 'Bearer token authentication. Format: Authorization: Bearer ephg_your_api_key'
        }
    },
    security=['apikey', 'bearer']
)

# Import and register namespaces
from ephergent_generator.api.admin import characters, config, tasks

# Register namespaces with the API
api.add_namespace(characters.ns, path='/characters')
api.add_namespace(config.ns, path='/config')
api.add_namespace(tasks.ns, path='/tasks')

__all__ = ['admin_api_blueprint', 'api']
