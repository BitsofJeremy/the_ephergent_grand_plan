from flask import Blueprint
from flask_restx import Api

# Create a blueprint for the API routes
api_blueprint = Blueprint('api', __name__, url_prefix='/api/v1')

# Create the Flask-RESTX API
api = Api(
    api_blueprint,
    version='1.0',
    title='Ephergent Season 03 Generator API',
    description='REST API for managing story generation workflow',
    doc='/swagger',
    validate=True
)

# Import namespaces to register them
from . import stories, workflow, health, characters, files, archive

# Register the namespaces with the API
api.add_namespace(stories.ns)
api.add_namespace(workflow.ns)
api.add_namespace(health.ns)
api.add_namespace(characters.ns)
api.add_namespace(files.ns)
api.add_namespace(archive.ns)

# Note: Admin API is registered as a separate blueprint in the main app
# See ephergent_generator/__init__.py for admin_api_blueprint registration