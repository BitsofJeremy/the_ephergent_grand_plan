"""Admin API endpoints for character management.

This module provides comprehensive CRUD operations for character configuration,
including version history tracking, profile image regeneration, and character
data management.
"""

from flask import request, current_app, g
from flask_restx import Namespace, Resource, fields, reqparse
from marshmallow import Schema, fields as ma_fields, ValidationError, validate
from datetime import datetime
from ephergent_generator import db
from ephergent_generator.models import Character, CharacterVersion, AdminTask
from ephergent_generator.services.auth_service import require_auth_or_api_key
from ephergent_generator.services.character_service import CharacterService
import logging

logger = logging.getLogger(__name__)

# Create namespace for admin character operations
ns = Namespace('admin/characters', description='Admin character management operations')

# Request/Response Models
character_model = ns.model('Character', {
    'id': fields.Integer(readonly=True, description='Database ID'),
    'character_id': fields.String(required=True, description='Unique character identifier'),
    'name': fields.String(required=True, description='Character name'),
    'email': fields.String(description='Character email'),
    'personality_prompt': fields.String(description='AI personality prompt'),
    'stable_diffusion_prompt': fields.String(description='Image generation prompt'),
    'voice_model': fields.String(description='TTS voice model'),
    'ai_model': fields.String(description='AI model for generation'),
    'topics': fields.List(fields.String, description='Character topics/specializations'),
    'tags': fields.List(fields.String, description='Character tags'),
    'is_default': fields.Boolean(description='Is default character'),
    'is_active': fields.Boolean(description='Is character active'),
    'sort_order': fields.Integer(description='Sort order for display'),
    'profile_image_path': fields.String(description='Profile image file path'),
    'profile_image_url': fields.String(description='Profile image URL'),
    'image_last_generated': fields.DateTime(description='Last image generation time'),
    'version': fields.Integer(description='Current version number'),
    'created_at': fields.DateTime(readonly=True, description='Creation timestamp'),
    'updated_at': fields.DateTime(readonly=True, description='Last update timestamp'),
})

character_version_model = ns.model('CharacterVersion', {
    'id': fields.Integer(readonly=True, description='Version ID'),
    'character_id': fields.Integer(description='Character database ID'),
    'version': fields.Integer(description='Version number'),
    'snapshot': fields.Raw(description='Character data snapshot'),
    'change_description': fields.String(description='Description of changes'),
    'changed_by': fields.Integer(description='User ID who made changes'),
    'changed_at': fields.DateTime(description='Version creation timestamp')
})

# Request schemas using Marshmallow for validation
class CharacterCreateSchema(Schema):
    """Schema for creating a new character."""
    character_id = ma_fields.Str(required=True, validate=validate.Length(min=1, max=100))
    name = ma_fields.Str(required=True, validate=validate.Length(min=1, max=100))
    email = ma_fields.Email(allow_none=True)
    personality_prompt = ma_fields.Str(required=True, validate=validate.Length(min=10))
    stable_diffusion_prompt = ma_fields.Str(allow_none=True)
    voice_model = ma_fields.Str(allow_none=True)
    ai_model = ma_fields.Str(allow_none=True)
    topics = ma_fields.List(ma_fields.Str(), allow_none=True)
    tags = ma_fields.List(ma_fields.Str(), allow_none=True)
    is_default = ma_fields.Boolean(allow_none=True)
    is_active = ma_fields.Boolean(allow_none=True)
    sort_order = ma_fields.Integer(allow_none=True)

class CharacterUpdateSchema(Schema):
    """Schema for updating an existing character."""
    name = ma_fields.Str(validate=validate.Length(min=1, max=100))
    email = ma_fields.Email(allow_none=True)
    personality_prompt = ma_fields.Str(validate=validate.Length(min=10))
    stable_diffusion_prompt = ma_fields.Str(allow_none=True)
    voice_model = ma_fields.Str(allow_none=True)
    ai_model = ma_fields.Str(allow_none=True)
    topics = ma_fields.List(ma_fields.Str(), allow_none=True)
    tags = ma_fields.List(ma_fields.Str(), allow_none=True)
    is_default = ma_fields.Boolean(allow_none=True)
    is_active = ma_fields.Boolean(allow_none=True)
    sort_order = ma_fields.Integer(allow_none=True)
    change_description = ma_fields.Str(allow_none=True)

# Request parsers
list_parser = reqparse.RequestParser()
list_parser.add_argument('include_inactive', type=bool, default=False,
                        help='Include inactive characters')
list_parser.add_argument('include_sensitive', type=bool, default=True,
                        help='Include sensitive data (prompts, paths)')

@ns.route('/')
class CharacterList(Resource):
    """Character list and creation endpoints."""

    @ns.expect(list_parser)
    @ns.marshal_list_with(character_model)
    @require_auth_or_api_key(['admin'])
    def get(self):
        """List all characters with optional filters.

        Query Parameters:
            include_inactive (bool): Include inactive characters (default: False)
            include_sensitive (bool): Include sensitive data like prompts (default: True)

        Returns:
            list[Character]: List of characters with full details

        Security:
            Requires admin authentication via session or API key with 'admin' permission
        """
        try:
            args = list_parser.parse_args()

            # Build query
            query = Character.query

            if not args['include_inactive']:
                query = query.filter_by(is_active=True)

            # Order by sort_order and name
            query = query.order_by(Character.sort_order.asc(), Character.name.asc())

            characters = query.all()

            # Convert to dict with appropriate detail level
            result = [char.to_dict(include_sensitive=args['include_sensitive'])
                     for char in characters]

            logger.info(f"Retrieved {len(result)} characters (admin request)")
            return result, 200

        except Exception as e:
            logger.error(f"Error listing characters: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving characters: {str(e)}")

    @ns.expect(character_model)
    @ns.marshal_with(character_model, code=201)
    @require_auth_or_api_key(['admin'])
    def post(self):
        """Create a new character.

        Request Body:
            character_id (str): Unique character identifier (required)
            name (str): Character name (required)
            personality_prompt (str): AI personality prompt (required)
            email (str): Character email (optional)
            stable_diffusion_prompt (str): Image generation prompt (optional)
            voice_model (str): TTS voice model (optional)
            ai_model (str): AI model identifier (optional)
            topics (list[str]): Character specialization topics (optional)
            tags (list[str]): Character tags (optional)
            is_default (bool): Set as default character (optional)
            is_active (bool): Character active status (optional, default: True)
            sort_order (int): Display sort order (optional, default: 0)

        Returns:
            Character: Newly created character with full details

        Errors:
            400: Validation error or duplicate character_id
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            data = request.get_json()

            # Validate input
            schema = CharacterCreateSchema()
            validated_data = schema.load(data)

            # Check for duplicate character_id
            existing = Character.query.filter_by(
                character_id=validated_data['character_id']
            ).first()

            if existing:
                ns.abort(400, message=f"Character with ID '{validated_data['character_id']}' already exists")

            # Get authenticated user ID for audit
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create new character
            character = Character(
                character_id=validated_data['character_id'],
                name=validated_data['name'],
                email=validated_data.get('email'),
                personality_prompt=validated_data['personality_prompt'],
                stable_diffusion_prompt=validated_data.get('stable_diffusion_prompt'),
                voice_model=validated_data.get('voice_model'),
                ai_model=validated_data.get('ai_model', 'gemini-2.5-flash'),
                is_default=validated_data.get('is_default', False),
                is_active=validated_data.get('is_active', True),
                sort_order=validated_data.get('sort_order', 0),
                created_by=user_id,
                updated_by=user_id
            )

            # Set topics and tags
            if 'topics' in validated_data:
                character.set_topics(validated_data['topics'])
            if 'tags' in validated_data:
                character.set_tags(validated_data['tags'])

            db.session.add(character)
            db.session.commit()

            logger.info(f"Created new character: {character.character_id} by user {user_id}")

            return character.to_dict(include_sensitive=True), 201

        except ValidationError as e:
            logger.warning(f"Validation error creating character: {e.messages}")
            ns.abort(400, message=f"Validation error: {e.messages}")
        except Exception as e:
            logger.error(f"Error creating character: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating character: {str(e)}")


@ns.route('/<int:character_id>')
class CharacterDetail(Resource):
    """Single character operations: retrieve, update, delete."""

    @ns.marshal_with(character_model)
    @require_auth_or_api_key(['admin'])
    def get(self, character_id):
        """Get detailed information about a specific character.

        Path Parameters:
            character_id (int): Database ID of the character

        Returns:
            Character: Full character details including sensitive data

        Errors:
            404: Character not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            character = Character.query.get(character_id)

            if not character:
                ns.abort(404, message=f"Character with ID {character_id} not found")

            logger.info(f"Retrieved character {character.character_id} (admin request)")
            return character.to_dict(include_sensitive=True), 200

        except Exception as e:
            logger.error(f"Error retrieving character {character_id}: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving character: {str(e)}")

    @ns.expect(character_model)
    @ns.marshal_with(character_model)
    @require_auth_or_api_key(['admin'])
    def put(self, character_id):
        """Update an existing character.

        Creates a version snapshot before applying changes for audit trail.

        Path Parameters:
            character_id (int): Database ID of the character

        Request Body:
            Any character field can be updated (all optional)
            change_description (str): Description of changes for version history

        Returns:
            Character: Updated character with full details

        Errors:
            400: Validation error
            404: Character not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            character = Character.query.get(character_id)

            if not character:
                ns.abort(404, message=f"Character with ID {character_id} not found")

            data = request.get_json()

            # Validate input
            schema = CharacterUpdateSchema()
            validated_data = schema.load(data)

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create version snapshot before changes
            change_description = validated_data.pop('change_description', None)
            version_snapshot = character.create_version_snapshot(
                user_id=user_id,
                change_description=change_description
            )
            db.session.add(version_snapshot)

            # Update character fields
            for field, value in validated_data.items():
                if field == 'topics':
                    character.set_topics(value)
                elif field == 'tags':
                    character.set_tags(value)
                elif hasattr(character, field):
                    setattr(character, field, value)

            # Update audit fields
            character.updated_by = user_id
            character.updated_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Updated character {character.character_id} to version {character.version} by user {user_id}")

            return character.to_dict(include_sensitive=True), 200

        except ValidationError as e:
            logger.warning(f"Validation error updating character: {e.messages}")
            ns.abort(400, message=f"Validation error: {e.messages}")
        except Exception as e:
            logger.error(f"Error updating character {character_id}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error updating character: {str(e)}")

    @require_auth_or_api_key(['admin'])
    def delete(self, character_id):
        """Soft delete a character (sets is_active=False).

        This is a soft delete to preserve data integrity and version history.
        The character record remains in the database but is marked as inactive.

        Path Parameters:
            character_id (int): Database ID of the character

        Returns:
            dict: Success message with character ID

        Errors:
            404: Character not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            character = Character.query.get(character_id)

            if not character:
                ns.abort(404, message=f"Character with ID {character_id} not found")

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create version snapshot before soft delete
            version_snapshot = character.create_version_snapshot(
                user_id=user_id,
                change_description="Character soft deleted (marked inactive)"
            )
            db.session.add(version_snapshot)

            # Soft delete
            character.is_active = False
            character.updated_by = user_id
            character.updated_at = datetime.utcnow()

            db.session.commit()

            logger.info(f"Soft deleted character {character.character_id} by user {user_id}")

            return {
                'message': f'Character {character.character_id} successfully deactivated',
                'character_id': character.character_id,
                'id': character.id
            }, 200

        except Exception as e:
            logger.error(f"Error deleting character {character_id}: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error deleting character: {str(e)}")


@ns.route('/<int:character_id>/image')
class CharacterImageRegeneration(Resource):
    """Character profile image regeneration endpoint."""

    @require_auth_or_api_key(['admin'])
    def post(self, character_id):
        """Regenerate profile image for a specific character.

        Creates an async admin task to regenerate the character's profile image
        using the character's stable_diffusion_prompt.

        Path Parameters:
            character_id (int): Database ID of the character

        Returns:
            dict: Task creation confirmation with task_id and status URL

        Errors:
            404: Character not found or no image prompt configured
            500: Error creating task

        Security:
            Requires admin authentication

        Business Logic:
            1. Validates character exists and has image generation prompt
            2. Creates AdminTask record with 'character_image_generation' type
            3. Task will be picked up by background worker for async processing
            4. Returns task ID for status monitoring
        """
        try:
            character = Character.query.get(character_id)

            if not character:
                ns.abort(404, message=f"Character with ID {character_id} not found")

            if not character.stable_diffusion_prompt:
                ns.abort(404, message=f"Character {character.character_id} has no image generation prompt configured")

            # Get authenticated user ID
            user_id = None
            if hasattr(g, 'authenticated_user') and g.authenticated_user:
                user_id = g.authenticated_user.id

            # Create admin task for async processing
            task = AdminTask(
                task_type='character_image_generation',
                task_status='pending',
                started_by=user_id
            )
            task.set_params({
                'character_id': character.id,
                'character_identifier': character.character_id,
                'force_regenerate': True
            })

            db.session.add(task)
            db.session.commit()

            logger.info(f"Created image regeneration task {task.id} for character {character.character_id}")

            return {
                'message': f'Image regeneration task created for {character.name}',
                'task_id': task.id,
                'character_id': character.character_id,
                'status_url': f'/api/admin/tasks/{task.id}'
            }, 202

        except Exception as e:
            logger.error(f"Error creating image regeneration task: {str(e)}", exc_info=True)
            db.session.rollback()
            ns.abort(500, message=f"Error creating regeneration task: {str(e)}")


@ns.route('/<int:character_id>/versions')
class CharacterVersionHistory(Resource):
    """Character version history endpoint."""

    @ns.marshal_list_with(character_version_model)
    @require_auth_or_api_key(['admin'])
    def get(self, character_id):
        """Get version history for a specific character.

        Returns all version snapshots showing the evolution of the character's
        configuration over time, including who made changes and when.

        Path Parameters:
            character_id (int): Database ID of the character

        Returns:
            list[CharacterVersion]: List of version snapshots in reverse chronological order

        Errors:
            404: Character not found
            500: Database error

        Security:
            Requires admin authentication
        """
        try:
            character = Character.query.get(character_id)

            if not character:
                ns.abort(404, message=f"Character with ID {character_id} not found")

            # Get all versions in descending order (newest first)
            versions = character.versions.all()

            result = [version.to_dict() for version in versions]

            logger.info(f"Retrieved {len(result)} versions for character {character.character_id}")

            return result, 200

        except Exception as e:
            logger.error(f"Error retrieving version history: {str(e)}", exc_info=True)
            ns.abort(500, message=f"Error retrieving version history: {str(e)}")
