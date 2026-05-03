from flask import request, current_app, jsonify
from flask_restx import Namespace, Resource, fields, reqparse
from ephergent_generator.services.character_service import CharacterService
from ephergent_generator.services.auth_service import require_auth_or_api_key, require_api_key
import logging
import threading
import time

logger = logging.getLogger(__name__)

# Create a characters namespace
ns = Namespace('characters', description='Narrator character management')

# Character Model
character_model = ns.model('Character', {
    'id': fields.String(required=True, description='Unique character identifier'),
    'name': fields.String(description='Character name'),
    'description': fields.String(description='Character description'),
    'topics': fields.List(fields.String, description='Character specialization topics'),
    'default': fields.Boolean(description='Whether this is the default character'),
    'image': fields.String(description='Character image path'),
    'stable_diffusion_prompt': fields.String(description='Image generation prompt')
})

# Image Generation Status Model
image_status_model = ns.model('ImageGenerationStatus', {
    'character_id': fields.String(description='Character identifier'),
    'status': fields.String(description='Generation status: idle, generating, completed, failed'),
    'progress': fields.Integer(description='Progress percentage (0-100)'),
    'message': fields.String(description='Status message'),
    'image_path': fields.String(description='Generated image path if completed'),
    'started_at': fields.DateTime(description='Generation start time'),
    'completed_at': fields.DateTime(description='Generation completion time')
})

# Global dictionary to track image generation status
image_generation_status = {}

@ns.route('/')
class CharacterList(Resource):
    @ns.marshal_with(character_model, as_list=True)
    def get(self):
        """List all available narrator characters"""
        try:
            character_service = CharacterService()
            characters = character_service.get_all_characters()
            return characters, 200

        except Exception as e:
            current_app.logger.error(f"Character list error: {str(e)}")
            ns.abort(500, message="An error occurred while retrieving characters")

@ns.route('/<string:character_id>')
class CharacterResource(Resource):
    @ns.marshal_with(character_model)
    def get(self, character_id):
        """Get details of a specific character"""
        try:
            character_service = CharacterService()
            character = character_service.get_character_by_id(character_id)

            if not character:
                ns.abort(404, message="Character not found")

            return character, 200

        except Exception as e:
            current_app.logger.error(f"Character retrieval error: {str(e)}")
            ns.abort(500, message="An error occurred while retrieving the character")

@ns.route('/<string:character_id>/regenerate-image')
class CharacterImageRegenerate(Resource):
    @require_auth_or_api_key(['admin'])
    def post(self, character_id):
        """Regenerate profile image for a specific character"""
        try:
            character_service = CharacterService()
            character = character_service.get_character_by_id(character_id)

            if not character:
                ns.abort(404, message="Character not found")

            # Check if already generating
            if character_id in image_generation_status and image_generation_status[character_id]['status'] == 'generating':
                return {
                    'message': 'Image generation already in progress for this character',
                    'status': 'generating'
                }, 409

            # Initialize status tracking
            image_generation_status[character_id] = {
                'status': 'generating',
                'progress': 0,
                'message': 'Starting image generation...',
                'started_at': time.time(),
                'character_name': character.get('name', character_id)
            }

            # Start image generation in background thread
            # Pass the current app to the background thread
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=self._generate_character_image_async,
                args=(character_id, character, app)
            )
            thread.daemon = True
            thread.start()

            return {
                'message': f'Image generation started for {character.get("name", character_id)}',
                'character_id': character_id,
                'status_url': f'/api/characters/{character_id}/image-status'
            }, 202

        except Exception as e:
            logger.error(f"Error starting image generation for {character_id}: {str(e)}")
            ns.abort(500, message="Failed to start image generation")

    def _generate_character_image_async(self, character_id, character, app):
        """Asynchronously generate character image"""
        try:
            # Update progress
            image_generation_status[character_id]['progress'] = 25
            image_generation_status[character_id]['message'] = 'Initializing generator...'

            # Use CharacterService within app context (no external script needed)
            with app.app_context():
                character_service = CharacterService()

                # Update progress
                image_generation_status[character_id]['progress'] = 50
                image_generation_status[character_id]['message'] = 'Generating image...'

                # Generate image using the service method
                success, message = character_service.generate_character_image(character_id, force_regenerate=True)

                if success:
                    image_generation_status[character_id]['status'] = 'completed'
                    image_generation_status[character_id]['progress'] = 100
                    image_generation_status[character_id]['message'] = 'Image generation completed successfully'
                    image_generation_status[character_id]['completed_at'] = time.time()

                    # Set image paths
                    image_filename = f"{character_id}_resized.png"
                    image_generation_status[character_id]['image_path'] = f"img/characters/{image_filename}"
                else:
                    raise Exception(f"Image generation failed: {message}")

        except Exception as e:
            logger.error(f"Error generating image for {character_id}: {str(e)}")
            image_generation_status[character_id]['status'] = 'failed'
            image_generation_status[character_id]['message'] = f'Image generation failed: {str(e)}'
            image_generation_status[character_id]['completed_at'] = time.time()

@ns.route('/regenerate-all')
class CharacterImageRegenerateAll(Resource):
    @require_auth_or_api_key(['admin'])
    def post(self):
        """Regenerate profile images for all characters"""
        try:
            character_service = CharacterService()
            characters = character_service.get_all_characters()

            if not characters:
                return {'message': 'No characters found'}, 404

            # Check if any generation is already in progress
            active_generations = [cid for cid, status in image_generation_status.items()
                                if status['status'] == 'generating']

            if active_generations:
                return {
                    'message': 'Image generation already in progress for some characters',
                    'active_characters': active_generations
                }, 409

            # Initialize status for all characters
            for character in characters:
                character_id = character['id']
                image_generation_status[character_id] = {
                    'status': 'queued',
                    'progress': 0,
                    'message': 'Queued for generation...',
                    'character_name': character.get('name', character_id)
                }

            # Start bulk generation in background thread
            app = current_app._get_current_object()
            thread = threading.Thread(
                target=self._generate_all_images_async,
                args=(characters, app)
            )
            thread.daemon = True
            thread.start()

            return {
                'message': f'Bulk image generation started for {len(characters)} characters',
                'character_count': len(characters),
                'status_url': '/api/characters/generation-status'
            }, 202

        except Exception as e:
            logger.error(f"Error starting bulk image generation: {str(e)}")
            ns.abort(500, message="Failed to start bulk image generation")

    def _generate_all_images_async(self, characters, app):
        """Asynchronously generate all character images"""
        try:
            with app.app_context():
                character_service = CharacterService()

                for i, character in enumerate(characters):
                    character_id = character['id']
                    character_name = character.get('name', character_id)

                    try:
                        # Update status to generating
                        image_generation_status[character_id]['status'] = 'generating'
                        image_generation_status[character_id]['progress'] = 10
                        image_generation_status[character_id]['message'] = f'Generating image for {character_name}...'
                        image_generation_status[character_id]['started_at'] = time.time()

                        # Generate image using the service method
                        success, message = character_service.generate_character_image(character_id, force_regenerate=True)

                        if success:
                            image_generation_status[character_id]['status'] = 'completed'
                            image_generation_status[character_id]['progress'] = 100
                            image_generation_status[character_id]['message'] = 'Image generation completed successfully'
                            image_generation_status[character_id]['completed_at'] = time.time()

                            # Set image paths
                            image_filename = f"{character_id}_resized.png"
                            image_generation_status[character_id]['image_path'] = f"img/characters/{image_filename}"
                        else:
                            raise Exception(f"Image generation failed: {message}")

                        # Add delay between generations (except for the last one)
                        if i < len(characters) - 1:
                            time.sleep(5)

                    except Exception as e:
                        logger.error(f"Error generating image for {character_id}: {str(e)}")
                        image_generation_status[character_id]['status'] = 'failed'
                        image_generation_status[character_id]['message'] = f'Image generation failed: {str(e)}'
                        image_generation_status[character_id]['completed_at'] = time.time()

        except Exception as e:
            logger.error(f"Error in bulk image generation: {str(e)}")
            # Mark all remaining characters as failed
            for character in characters:
                character_id = character['id']
                if image_generation_status.get(character_id, {}).get('status') not in ['completed', 'failed']:
                    image_generation_status[character_id]['status'] = 'failed'
                    image_generation_status[character_id]['message'] = f'Bulk generation failed: {str(e)}'

@ns.route('/<string:character_id>/image-status')
class CharacterImageStatus(Resource):
    def get(self, character_id):
        """Get image generation status for a specific character"""
        try:
            character_service = CharacterService()
            character = character_service.get_character_by_id(character_id)

            if not character:
                ns.abort(404, message="Character not found")

            # Get status or default to idle
            status = image_generation_status.get(character_id, {
                'status': 'idle',
                'progress': 0,
                'message': 'No generation in progress'
            })

            # Add character info
            status['character_id'] = character_id
            status['character_name'] = character.get('name', character_id)

            return status, 200

        except Exception as e:
            logger.error(f"Error getting image status for {character_id}: {str(e)}")
            ns.abort(500, message="Failed to get image generation status")

@ns.route('/generation-status')
class AllCharacterImageStatus(Resource):
    def get(self):
        """Get image generation status for all characters"""
        try:
            character_service = CharacterService()
            characters = character_service.get_all_characters()

            status_list = []
            for character in characters:
                character_id = character['id']
                status = image_generation_status.get(character_id, {
                    'status': 'idle',
                    'progress': 0,
                    'message': 'No generation in progress'
                })

                status['character_id'] = character_id
                status['character_name'] = character.get('name', character_id)
                status_list.append(status)

            return {
                'characters': status_list,
                'summary': {
                    'total': len(characters),
                    'generating': len([s for s in status_list if s['status'] == 'generating']),
                    'queued': len([s for s in status_list if s['status'] == 'queued']),
                    'completed': len([s for s in status_list if s['status'] == 'completed']),
                    'failed': len([s for s in status_list if s['status'] == 'failed']),
                    'idle': len([s for s in status_list if s['status'] == 'idle'])
                }
            }, 200

        except Exception as e:
            logger.error(f"Error getting generation status: {str(e)}")
            ns.abort(500, message="Failed to get generation status")