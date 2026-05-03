"""Admin API endpoints for system configuration management.

This module provides comprehensive CRUD operations for system-wide configuration
settings with type safety, version tracking, and category-based organization.
"""

from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields, reqparse
from marshmallow import Schema, fields as ma_fields, ValidationError, validate
from datetime import datetime
from ephergent_generator import db
from ephergent_generator.models import SystemConfig
from ephergent_generator.services.auth_service import require_auth_or_api_key
import logging
import json

logger = logging.getLogger(__name__)

# Create namespace for system configuration
ns = Namespace('admin/config', description='System configuration management')

# Request/Response Models
config_model = ns.model('SystemConfig', {
    'id': fields.Integer(readonly=True, description='Database ID'),
    'config_key': fields.String(required=True, description='Configuration key'),
    'config_value': fields.Raw(description='Configuration value (typed)'),
    'config_type': fields.String(description='Value type: string, int, float, bool, json'),
    'description': fields.String(description='Configuration description'),
    'category': fields.String(description='Configuration category'),
    'is_public': fields.Boolean(description='Is publicly accessible'),
    'version': fields.Integer(description='Current version number'),
    'updated_by': fields.Integer(description='User ID who last updated'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp'),
})

# Request schemas
class ConfigCreateSchema(Schema):
    """Schema for creating a new configuration."""
    config_key = ma_fields.Str(required=True, validate=validate.Length(min=1, max=200))
    config_value = ma_fields.Raw(required=True)
    config_type = ma_fields.Str(required=True,
                               validate=validate.OneOf(['string', 'int', 'float', 'bool', 'json']))
    description = ma_fields.Str(allow_none=True)
    category = ma_fields.Str(allow_none=True, validate=validate.Length(max=50))
    is_public = ma_fields.Boolean(allow_none=True)

class ConfigUpdateSchema(Schema):
    """Schema for updating an existing configuration."""
    config_value = ma_fields.Raw(required=True)
    config_type = ma_fields.Str(validate=validate.OneOf(['string', 'int', 'float', 'bool', 'json']))
    description = ma_fields.Str(allow_none=True)
    category = ma_fields.Str(allow_none=True, validate=validate.Length(max=50))
    is_public = ma_fields.Boolean(allow_none=True)

# Request parsers
list_parser = reqparse.RequestParser()
list_parser.add_argument('category', type=str, help='Filter by category')
list_parser.add_argument('public_only', type=bool, default=False,
                        help='Show only public configurations')
list_parser.add_argument('include_sensitive', type=bool, default=True,
                        help='Include sensitive data (audit fields)')

@ns.route('/')
class ConfigList(Resource):
    """System configuration list and creation endpoints."""

    @ns.expect(list_parser)
    @ns.marshal_list_with(config_model)
    @require_auth_or_api_key(['admin'])
    def get(self):
        """List all system configurations with optional filters.

        Query Parameters:
            category (str): Filter by configuration category
            public_only (bool): Show only public configurations (default: False)
            include_sensitive (bool): Include sensitive data like audit fields (default: True)

        Returns:
            list[SystemConfig]: List of configurations

        Security:
            Requires admin authentication
        """
        try:
            args = list_parser.parse_args()

            # Build query
            query = SystemConfig.query

            if args['category']:
                query = query.filter_by(category=args['category'])

            if args['public_only']:
                query = query.filter_by(is_public=True)

            # Order by category and key
            query = query.order_by(SystemConfig.category.asc(), SystemConfig.config_key.asc())

            configs = query.all()

            # Convert to dict with appropriate detail level
            result = [config.to_dict(include_sensitive=args['include_sensitive'])
                     for config in configs]

            logger.info(f"Retrieved {len(result)} configurations (admin request)")
            return result, 200

        except Exception as e:
            logger.error(f"Error listing configurations: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving configurations: {str(e)}")

    @ns.expect(config_model)
    @ns.marshal_with(config_model, code=201)
    @require_auth_or_api_key(['admin'])
    def post(self):
        """Create a new system configuration.

        Request Body:
            config_key (str): Unique configuration key (required)
            config_value (any): Configuration value (required)
            config_type (str): Value type - string, int, float, bool, json (required)
            description (str): Configuration description (optional)
            category (str): Configuration category (optional)
            is_public (bool): Is publicly accessible (optional, default: False)

        Returns:
            SystemConfig: Newly created configuration

        Errors:
            400: Validation error or duplicate key
            500: Database error

        Security:
            Requires admin authentication

        Business Logic:
            - Validates config_type and value compatibility
            - Automatically converts value to appropriate type
            - JSON values are validated for structure
        """
        try:
            data = request.get_json()

            # Validate input
            schema = ConfigCreateSchema()
            validated_data = schema.load(data)

            # Check for duplicate key
            existing = SystemConfig.query.filter_by(
                config_key=validated_data['config_key']
            ).first()

            if existing:
                ns.abort(400, message=f"Configuration key '{validated_data['config_key']}' already exists")

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Validate value against type
            config_type = validated_data['config_type']
            config_value = validated_data['config_value']

            try:
                if config_type == 'int':
                    int(config_value)
                elif config_type == 'float':
                    float(config_value)
                elif config_type == 'bool':
                    if not isinstance(config_value, bool):
                        if str(config_value).lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                            raise ValueError("Invalid boolean value")
                elif config_type == 'json':
                    if isinstance(config_value, str):
                        json.loads(config_value)
                    else:
                        json.dumps(config_value)
            except (ValueError, json.JSONDecodeError) as e:
                ns.abort(400, message=f"Value incompatible with type '{config_type}': {str(e)}")

            # Create configuration using static method
            config = SystemConfig.set_config(
                key=validated_data['config_key'],
                value=config_value,
                config_type=config_type,
                description=validated_data.get('description'),
                category=validated_data.get('category'),
                is_public=validated_data.get('is_public', False),
                user_id=user_id
            )

            db.session.commit()

            logger.info(f"Created configuration: {config.config_key} by user {user_id}")

            return config.to_dict(include_sensitive=True), 201

        except ValidationError as e:
            logger.warning(f"Validation error creating configuration: {e.messages}")
            ns.abort(400, message=f"Validation error: {e.messages}")
        except Exception as e:
            logger.error(f"Error creating configuration: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating configuration: {str(e)}")


@ns.route('/<string:config_key>')
class ConfigDetail(Resource):
    """Single configuration operations: retrieve, update, delete."""

    @ns.marshal_with(config_model)
    @require_auth_or_api_key(['admin'])
    def get(self, config_key):
        """Get a specific configuration by key.

        Path Parameters:
            config_key (str): Configuration key

        Returns:
            SystemConfig: Configuration details

        Errors:
            404: Configuration not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            config = SystemConfig.query.filter_by(config_key=config_key).first()

            if not config:
                ns.abort(404, message=f"Configuration '{config_key}' not found")

            logger.info(f"Retrieved configuration {config_key} (admin request)")
            return config.to_dict(include_sensitive=True), 200

        except Exception as e:
            logger.error(f"Error retrieving configuration {config_key}: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving configuration: {str(e)}")

    @ns.expect(config_model)
    @ns.marshal_with(config_model)
    @require_auth_or_api_key(['admin'])
    def put(self, config_key):
        """Update an existing configuration (creates new version).

        Path Parameters:
            config_key (str): Configuration key

        Request Body:
            config_value (any): New configuration value (required)
            config_type (str): Value type (optional, uses existing if not provided)
            description (str): Configuration description (optional)
            category (str): Configuration category (optional)
            is_public (bool): Public accessibility (optional)

        Returns:
            SystemConfig: Updated configuration

        Errors:
            400: Validation error
            404: Configuration not found
            500: Database error

        Security:
            Requires admin authentication

        Business Logic:
            - Automatically increments version number
            - Validates value against specified or existing type
            - Preserves type if not specified in update
        """
        try:
            config = SystemConfig.query.filter_by(config_key=config_key).first()

            if not config:
                ns.abort(404, message=f"Configuration '{config_key}' not found")

            data = request.get_json()

            # Validate input
            schema = ConfigUpdateSchema()
            validated_data = schema.load(data)

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Determine config type (use provided or keep existing)
            config_type = validated_data.get('config_type', config.config_type)
            config_value = validated_data['config_value']

            # Validate value against type
            try:
                if config_type == 'int':
                    int(config_value)
                elif config_type == 'float':
                    float(config_value)
                elif config_type == 'bool':
                    if not isinstance(config_value, bool):
                        if str(config_value).lower() not in ('true', 'false', '1', '0', 'yes', 'no'):
                            raise ValueError("Invalid boolean value")
                elif config_type == 'json':
                    if isinstance(config_value, str):
                        json.loads(config_value)
                    else:
                        json.dumps(config_value)
            except (ValueError, json.JSONDecodeError) as e:
                ns.abort(400, message=f"Value incompatible with type '{config_type}': {str(e)}")

            # Update configuration
            config.set_value(config_value, config_type)

            # Update other fields if provided
            if 'description' in validated_data:
                config.description = validated_data['description']
            if 'category' in validated_data:
                config.category = validated_data['category']
            if 'is_public' in validated_data:
                config.is_public = validated_data['is_public']

            config.updated_by = user_id
            config.updated_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Updated configuration {config_key} to version {config.version} by user {user_id}")

            return config.to_dict(include_sensitive=True), 200

        except ValidationError as e:
            logger.warning(f"Validation error updating configuration: {e.messages}")
            ns.abort(400, message=f"Validation error: {e.messages}")
        except Exception as e:
            logger.error(f"Error updating configuration {config_key}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error updating configuration: {str(e)}")

    @require_auth_or_api_key(['admin'])
    def delete(self, config_key):
        """Delete a configuration.

        This is a hard delete that permanently removes the configuration.
        Use with caution as this cannot be undone.

        Path Parameters:
            config_key (str): Configuration key

        Returns:
            dict: Success message

        Errors:
            404: Configuration not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            config = SystemConfig.query.filter_by(config_key=config_key).first()

            if not config:
                ns.abort(404, message=f"Configuration '{config_key}' not found")

            # Get authenticated user ID for logging
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            db.session.delete(config)
            db.session.commit()

            logger.info(f"Deleted configuration {config_key} by user {user_id}")

            return {
                'message': f'Configuration {config_key} successfully deleted',
                'config_key': config_key
            }, 200

        except Exception as e:
            logger.error(f"Error deleting configuration {config_key}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error deleting configuration: {str(e)}")


@ns.route('/category/<string:category>')
class ConfigCategory(Resource):
    """Configuration operations by category."""

    @ns.marshal_list_with(config_model)
    @require_auth_or_api_key(['admin'])
    def get(self, category):
        """Get all configurations in a specific category.

        Path Parameters:
            category (str): Configuration category

        Returns:
            list[SystemConfig]: List of configurations in the category

        Security:
            Requires admin authentication
        """
        try:
            configs = SystemConfig.query.filter_by(category=category).order_by(
                SystemConfig.config_key.asc()
            ).all()

            result = [config.to_dict(include_sensitive=True) for config in configs]

            logger.info(f"Retrieved {len(result)} configurations in category '{category}'")

            return result, 200

        except Exception as e:
            logger.error(f"Error retrieving category {category}: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving category: {str(e)}")


@ns.route('/categories')
class ConfigCategories(Resource):
    """List all configuration categories."""

    @require_auth_or_api_key(['admin'])
    def get(self):
        """Get list of all configuration categories.

        Returns:
            dict: Categories with configuration counts

        Security:
            Requires admin authentication
        """
        try:
            # Get all distinct categories with counts
            categories = db.session.query(
                SystemConfig.category,
                db.func.count(SystemConfig.id).label('count')
            ).group_by(SystemConfig.category).all()

            result = {
                'categories': [
                    {
                        'name': cat[0] or 'uncategorized',
                        'count': cat[1]
                    }
                    for cat in categories
                ],
                'total_categories': len(categories),
                'total_configs': sum(cat[1] for cat in categories)
            }

            logger.info(f"Retrieved {len(categories)} configuration categories")

            return result, 200

        except Exception as e:
            logger.error(f"Error retrieving categories: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving categories: {str(e)}")


@ns.route('/bulk')
class ConfigBulk(Resource):
    """Bulk configuration operations."""

    @require_auth_or_api_key(['admin'])
    def post(self):
        """Bulk create or update configurations.

        Request Body:
            configs (list): List of configuration objects to create/update
                Each object should contain: config_key, config_value, config_type, etc.

        Returns:
            dict: Summary of created/updated/failed configurations

        Security:
            Requires admin authentication

        Business Logic:
            - Processes each configuration individually
            - Creates new configs or updates existing ones
            - Returns detailed results for each operation
            - Partial success: some configs may succeed while others fail
        """
        try:
            data = request.get_json()

            if not isinstance(data, dict) or 'configs' not in data:
                ns.abort(400, message="Request must contain 'configs' array")

            configs = data['configs']
            if not isinstance(configs, list):
                ns.abort(400, message="'configs' must be an array")

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            results = {
                'created': [],
                'updated': [],
                'failed': []
            }

            for config_data in configs:
                try:
                    config_key = config_data.get('config_key')
                    if not config_key:
                        results['failed'].append({
                            'data': config_data,
                            'error': 'Missing config_key'
                        })
                        continue

                    # Check if exists
                    existing = SystemConfig.query.filter_by(config_key=config_key).first()

                    config = SystemConfig.set_config(
                        key=config_key,
                        value=config_data.get('config_value'),
                        config_type=config_data.get('config_type', 'string'),
                        description=config_data.get('description'),
                        category=config_data.get('category'),
                        is_public=config_data.get('is_public', False),
                        user_id=user_id
                    )

                    if existing:
                        results['updated'].append(config.to_dict(include_sensitive=False))
                    else:
                        results['created'].append(config.to_dict(include_sensitive=False))

                except Exception as e:
                    results['failed'].append({
                        'data': config_data,
                        'error': str(e)
                    })

            db.session.commit()

            logger.info(
                f"Bulk config operation: {len(results['created'])} created, "
                f"{len(results['updated'])} updated, {len(results['failed'])} failed"
            )

            return {
                **results,
                'summary': {
                    'created': len(results['created']),
                    'updated': len(results['updated']),
                    'failed': len(results['failed']),
                    'total': len(configs)
                }
            }, 200

        except Exception as e:
            logger.error(f"Error in bulk config operation: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error in bulk operation: {str(e)}")
