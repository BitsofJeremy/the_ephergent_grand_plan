import json
import os
from pathlib import Path
from ephergent_generator.services.universe_context_service import UniverseContextService
from ephergent_generator.models import Character
import logging
import time
from PIL import Image

logger = logging.getLogger(__name__)

class CharacterService:
    """Service for managing character data and prompts (database-driven)."""

    def __init__(self):
        self.universe_context_service = UniverseContextService()
        logger.info("CharacterService initialized (using database)")
    
    def get_all_characters(self):
        """Get all active characters from database."""
        try:
            characters = Character.query.filter_by(is_active=True).order_by(Character.sort_order).all()
            # Convert to dict format for backward compatibility
            return [self._character_to_dict(char) for char in characters]
        except Exception as e:
            logger.error(f"Error loading characters from database: {str(e)}")
            return []

    def get_character_by_id(self, character_id):
        """Get a specific character by ID from database."""
        try:
            character = Character.query.filter_by(character_id=character_id, is_active=True).first()
            if character:
                return self._character_to_dict(character)
            return None
        except Exception as e:
            logger.error(f"Error loading character {character_id} from database: {str(e)}")
            return None

    def get_default_character(self):
        """Get the default character from database."""
        try:
            character = Character.query.filter_by(is_default=True, is_active=True).first()
            if character:
                return self._character_to_dict(character)

            # Fallback to first active character if no default found
            character = Character.query.filter_by(is_active=True).order_by(Character.sort_order).first()
            if character:
                return self._character_to_dict(character)
            return None
        except Exception as e:
            logger.error(f"Error loading default character from database: {str(e)}")
            return None

    def get_character_prompt(self, character_id):
        """Get the personality prompt text for a character from database."""
        try:
            character = Character.query.filter_by(character_id=character_id, is_active=True).first()
            if character:
                return character.personality_prompt or ''
            return ''
        except Exception as e:
            logger.error(f"Error loading prompt for character {character_id} from database: {str(e)}")
            return ''

    def _character_to_dict(self, character):
        """Convert Character model to dict format for backward compatibility.

        Args:
            character: Character model instance

        Returns:
            Dictionary matching the old JSON structure
        """
        return {
            'id': character.character_id,
            'name': character.name,
            'email': character.email,
            'voice': character.voice_model,
            'model': character.ai_model,
            'topics': character.get_topics(),
            'tags': character.get_tags(),
            'stable_diffusion_prompt': character.stable_diffusion_prompt,
            'default': character.is_default,
            'prompt_file': None  # No longer used, kept for compatibility
        }
    
    def get_characters_for_dropdown(self):
        """Get characters formatted for HTML dropdown."""
        characters = []
        for character in self.get_all_characters():
            # Use local static image path
            image_filename = f"{character['id']}_resized.png"
            static_image_path = f"img/characters/{image_filename}"
            
            characters.append({
                'id': character['id'],
                'name': character['name'],
                'default': character.get('default', False),
                'topics': ', '.join(character.get('topics', [])),
                'description': f"{character['name']} - {', '.join(character.get('topics', []))}",
                'image': static_image_path
            })
        
        # Sort so default character is first
        characters.sort(key=lambda x: (not x['default'], x['name']))
        return characters
    
    def build_character_story_prompt(self, character_id, topic, genre=None, tone=None, word_count=900, dimension_location=None):
        """Build a story prompt incorporating character personality and universe context."""
        character = self.get_character_by_id(character_id)
        character_prompt = self.get_character_prompt(character_id)
        
        # Get full universe context as foundation
        universe_context = self.universe_context_service.get_universe_prompt()
        
        if not character or not character_prompt:
            logger.warning(f"Character or prompt not found for {character_id}, using universe context only")
            return self.universe_context_service.build_story_prompt_with_universe_context(
                topic, genre, tone, word_count, dimension_location
            )
        
        # Build comprehensive prompt with universe context + character specifics
        full_prompt = f"{universe_context}\n\n"
        full_prompt += "=" * 80 + "\n"
        full_prompt += f"CHARACTER-SPECIFIC STORY GENERATION: {character['name'].upper()}\n"
        full_prompt += "=" * 80 + "\n\n"
        
        full_prompt += f"**Primary Narrator**: {character['name']}\n\n"
        full_prompt += f"**Character-Specific Context**:\n{character_prompt}\n\n"
        
        # Add dimension-specific context if provided
        if dimension_location:
            dimension_context = self.universe_context_service._get_dimension_context(dimension_location)
            if dimension_context:
                full_prompt += f"**Primary Setting**: {dimension_context}\n\n"
        
        full_prompt += f"**Story Topic**: {topic}\n\n"
        
        if genre:
            full_prompt += f"**Genre**: {genre}\n"
        
        if tone:
            full_prompt += f"**Tone**: {tone}\n"
        
        if word_count:
            full_prompt += f"**Target Length**: approximately {word_count} words\n"
        
        full_prompt += f"\n**CHARACTER-SPECIFIC INSTRUCTIONS FOR {character['name']}:**\n"
        full_prompt += f"- Write this story entirely in {character['name']}'s distinctive voice and style\n"
        full_prompt += f"- Use {character['name']}'s specific conversational patterns, quirks, and signature elements\n"
        full_prompt += f"- Apply their unique perspective on the Ephergent Universe and interdimensional reporting\n"
        full_prompt += f"- Follow all universe lore and world-building guidelines established above\n"
        full_prompt += f"- Maintain {character['name']}'s personality while delivering compelling narrative\n"
        full_prompt += f"- Include appropriate references to CLX, Corporate Corp, other dimensions, etc. as {character['name']} would\n\n"
        full_prompt += f"Generate the story as if {character['name']} is personally telling this story to Ephergent readers. Focus purely on the narrative content without a separate title."
        
        return full_prompt

    def get_character_image_path(self, character_id, image_type='resized'):
        """Get the file system path for a character image."""
        try:
            app_root = Path(__file__).parent.parent
            static_images_dir = app_root / 'static' / 'img' / 'characters'

            if image_type == 'full':
                image_filename = f"{character_id}.png"
            else:  # resized (default)
                image_filename = f"{character_id}_resized.png"

            return static_images_dir / image_filename

        except Exception as e:
            logger.error(f"Error getting image path for {character_id}: {str(e)}")
            return None

    def get_character_image_url(self, character_id, image_type='resized'):
        """Get the URL path for a character image."""
        try:
            if image_type == 'full':
                image_filename = f"{character_id}.png"
            else:  # resized (default)
                image_filename = f"{character_id}_resized.png"

            return f"img/characters/{image_filename}"

        except Exception as e:
            logger.error(f"Error getting image URL for {character_id}: {str(e)}")
            return None

    def character_image_exists(self, character_id, image_type='resized'):
        """Check if a character image exists."""
        try:
            image_path = self.get_character_image_path(character_id, image_type)
            return image_path and image_path.exists()

        except Exception as e:
            logger.error(f"Error checking image existence for {character_id}: {str(e)}")
            return False

    def get_character_image_info(self, character_id):
        """Get comprehensive image information for a character."""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                return None

            full_image_path = self.get_character_image_path(character_id, 'full')
            resized_image_path = self.get_character_image_path(character_id, 'resized')

            info = {
                'character_id': character_id,
                'character_name': character.get('name', character_id),
                'has_full_image': full_image_path and full_image_path.exists(),
                'has_resized_image': resized_image_path and resized_image_path.exists(),
                'full_image_url': self.get_character_image_url(character_id, 'full'),
                'resized_image_url': self.get_character_image_url(character_id, 'resized'),
                'stable_diffusion_prompt': character.get('stable_diffusion_prompt', ''),
                'last_modified': None
            }

            # Get last modified time if image exists
            if info['has_resized_image']:
                try:
                    stat_info = resized_image_path.stat()
                    info['last_modified'] = stat_info.st_mtime
                except Exception as e:
                    logger.warning(f"Could not get modification time for {resized_image_path}: {str(e)}")

            return info

        except Exception as e:
            logger.error(f"Error getting image info for {character_id}: {str(e)}")
            return None

    def get_all_character_image_info(self):
        """Get image information for all characters."""
        try:
            characters = self.get_all_characters()
            image_info_list = []

            for character in characters:
                character_id = character.get('id')
                if character_id:
                    info = self.get_character_image_info(character_id)
                    if info:
                        image_info_list.append(info)

            return image_info_list

        except Exception as e:
            logger.error(f"Error getting all character image info: {str(e)}")
            return []

    def get_characters_missing_images(self):
        """Get list of characters that are missing images."""
        try:
            characters = self.get_all_characters()
            missing_images = []

            for character in characters:
                character_id = character.get('id')
                if character_id:
                    if not self.character_image_exists(character_id, 'resized'):
                        missing_images.append(character)

            return missing_images

        except Exception as e:
            logger.error(f"Error checking for missing images: {str(e)}")
            return []

    def validate_character_image_setup(self, character_id):
        """Validate that a character has all necessary data for image generation."""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                return False, "Character not found"

            # Check if character has a stable_diffusion_prompt
            if not character.get('stable_diffusion_prompt'):
                return False, "Character missing stable_diffusion_prompt"

            # Check if character has basic required fields
            if not character.get('name'):
                return False, "Character missing name"

            return True, "Character is ready for image generation"

        except Exception as e:
            logger.error(f"Error validating character setup for {character_id}: {str(e)}")
            return False, f"Validation error: {str(e)}"

    def prepare_character_for_generation(self, character_id):
        """Prepare character data for image generation."""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                return None

            # Validate character setup
            is_valid, message = self.validate_character_image_setup(character_id)
            if not is_valid:
                logger.warning(f"Character {character_id} validation failed: {message}")
                return None

            # Prepare generation data
            generation_data = {
                'character_id': character_id,
                'character_name': character.get('name'),
                'stable_diffusion_prompt': character.get('stable_diffusion_prompt'),
                'output_path_full': self.get_character_image_path(character_id, 'full'),
                'output_path_resized': self.get_character_image_path(character_id, 'resized'),
                'character': character  # Full character data for generator
            }

            return generation_data

        except Exception as e:
            logger.error(f"Error preparing character {character_id} for generation: {str(e)}")
            return None

    def get_characters_for_admin_interface(self):
        """Get characters formatted for admin interface display."""
        try:
            characters = self.get_all_characters()
            admin_characters = []

            for character in characters:
                character_id = character.get('id')
                if not character_id:
                    continue

                # Get image information
                image_info = self.get_character_image_info(character_id)

                # Prepare admin display data
                admin_character = {
                    'id': character_id,
                    'name': character.get('name', 'Unknown'),
                    'topics': character.get('topics', []),
                    'default': character.get('default', False),
                    'stable_diffusion_prompt': character.get('stable_diffusion_prompt', ''),
                    'has_prompt': bool(character.get('stable_diffusion_prompt')),
                    'image_url': image_info['resized_image_url'] if image_info else None,
                    'has_image': image_info['has_resized_image'] if image_info else False,
                    'last_modified': image_info['last_modified'] if image_info else None
                }

                admin_characters.append(admin_character)

            # Sort by default character first, then alphabetically
            admin_characters.sort(key=lambda x: (not x['default'], x['name']))

            return admin_characters

        except Exception as e:
            logger.error(f"Error getting characters for admin interface: {str(e)}")
            return []

    def _create_resized_image(self, original_path: Path, resized_path: Path, target_size: tuple = (300, 300)):
        """Create a resized version of the image for web display."""
        try:
            with Image.open(original_path) as img:
                # Resize maintaining aspect ratio
                img.thumbnail(target_size, Image.Resampling.LANCZOS)
                # Create new image with target size and center the thumbnail
                resized_img = Image.new('RGBA', target_size, (0, 0, 0, 0))
                offset = ((target_size[0] - img.width) // 2, (target_size[1] - img.height) // 2)
                resized_img.paste(img, offset)
                resized_img.save(resized_path, 'PNG', optimize=True)
                logger.info(f"Created resized image: {resized_path}")
                return True
        except Exception as e:
            logger.error(f"Error creating resized image {resized_path}: {e}")
            return False

    def generate_character_image(self, character_id: str, force_regenerate: bool = False):
        """Generate profile image for a specific character using ComfyUI."""
        try:
            # Import here to avoid circular imports
            from ephergent_generator.services.comfyui_service import ComfyUIService

            character = self.get_character_by_id(character_id)
            if not character:
                logger.error(f"Character not found: {character_id}")
                return False, "Character not found"

            character_name = character.get('name')
            stable_diffusion_prompt = character.get('stable_diffusion_prompt')

            if not stable_diffusion_prompt:
                logger.warning(f"Skipping character {character_name}: missing stable_diffusion_prompt")
                return False, "Missing stable_diffusion_prompt"

            logger.info(f"--- Generating profile image for: {character_name} ({character_id}) ---")

            # Set up file paths
            full_size_path = self.get_character_image_path(character_id, 'full')
            resized_path = self.get_character_image_path(character_id, 'resized')

            if not full_size_path or not resized_path:
                logger.error(f"Could not determine image paths for {character_id}")
                return False, "Could not determine image paths"

            # Ensure output directory exists
            full_size_path.parent.mkdir(parents=True, exist_ok=True)

            # Skip if files exist and not forcing regeneration
            if not force_regenerate and full_size_path.exists() and resized_path.exists():
                logger.info(f"Images already exist for {character_id}, skipping regeneration")
                return True, "Images already exist"

            # Initialize ComfyUI service
            comfyui_service = ComfyUIService()

            # Test ComfyUI connection
            if not comfyui_service.test_connection():
                logger.error("ComfyUI service is not available. Cannot generate images.")
                return False, "ComfyUI service is not available"

            # Generate the full-size image
            logger.info(f"Generating image with prompt: {stable_diffusion_prompt[:100]}...")

            generated_path = comfyui_service.generate_image(
                prompt=stable_diffusion_prompt,
                output_path=full_size_path,
                width=1024,
                height=1024
            )

            if generated_path and generated_path.exists():
                logger.info(f"Successfully generated full-size image: {generated_path}")

                # Create resized version
                if self._create_resized_image(generated_path, resized_path):
                    logger.info(f"Successfully generated both images for {character_name}")
                    return True, "Images generated successfully"
                else:
                    logger.error(f"Failed to create resized image for {character_name}")
                    return False, "Failed to create resized image"
            else:
                logger.error(f"Failed to generate image for {character_name}")
                return False, "Failed to generate image"

        except Exception as e:
            logger.error(f"Error generating image for character {character_id}: {str(e)}")
            return False, f"Error generating image: {str(e)}"

    def generate_all_character_images(self, force_regenerate: bool = False, delay_seconds: int = 5):
        """Generate profile images for all characters."""
        characters = self.get_all_characters()
        if not characters:
            logger.error("No characters loaded. Cannot generate images.")
            return 0, 1, "No characters loaded"

        logger.info(f"Starting generation for {len(characters)} characters")
        logger.info(f"Force regenerate: {force_regenerate}")
        logger.info(f"Delay between generations: {delay_seconds} seconds")

        successful = 0
        failed = 0
        results = []

        for idx, character in enumerate(characters):
            character_id = character.get('id')
            character_name = character.get('name', f'Character {idx}')

            if not character_id:
                logger.warning(f"Skipping character without ID: {character_name}")
                failed += 1
                results.append({
                    'character_id': None,
                    'character_name': character_name,
                    'success': False,
                    'message': 'No character ID'
                })
                continue

            logger.info(f"Processing character {idx + 1}/{len(characters)}: {character_name}")

            success, message = self.generate_character_image(character_id, force_regenerate)

            results.append({
                'character_id': character_id,
                'character_name': character_name,
                'success': success,
                'message': message
            })

            if success:
                successful += 1
            else:
                failed += 1

            # Add delay between generations to avoid overwhelming ComfyUI
            if idx < len(characters) - 1:  # Don't delay after the last character
                logger.info(f"Waiting {delay_seconds} seconds before next generation...")
                time.sleep(delay_seconds)

        logger.info("=" * 50)
        logger.info("CHARACTER PROFILE GENERATION COMPLETE")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")
        logger.info(f"Total: {len(characters)}")
        logger.info("=" * 50)

        return successful, failed, results

    def get_character_generation_status(self, character_id: str = None):
        """Get status of character image generation."""
        try:
            if character_id:
                # Status for specific character
                character = self.get_character_by_id(character_id)
                if not character:
                    return {'error': 'Character not found'}

                info = self.get_character_image_info(character_id)
                is_valid, validation_message = self.validate_character_image_setup(character_id)

                return {
                    'character_id': character_id,
                    'character_name': character.get('name'),
                    'has_images': info['has_resized_image'] if info else False,
                    'can_generate': is_valid,
                    'validation_message': validation_message,
                    'stable_diffusion_prompt': character.get('stable_diffusion_prompt', ''),
                    'last_modified': info['last_modified'] if info else None
                }
            else:
                # Status for all characters
                characters = self.get_all_characters()
                status_list = []

                total_characters = len(characters)
                characters_with_images = 0
                characters_ready_for_generation = 0

                for character in characters:
                    character_id = character.get('id')
                    if not character_id:
                        continue

                    info = self.get_character_image_info(character_id)
                    is_valid, validation_message = self.validate_character_image_setup(character_id)

                    has_images = info['has_resized_image'] if info else False
                    if has_images:
                        characters_with_images += 1
                    if is_valid:
                        characters_ready_for_generation += 1

                    status_list.append({
                        'character_id': character_id,
                        'character_name': character.get('name'),
                        'has_images': has_images,
                        'can_generate': is_valid,
                        'validation_message': validation_message
                    })

                return {
                    'total_characters': total_characters,
                    'characters_with_images': characters_with_images,
                    'characters_ready_for_generation': characters_ready_for_generation,
                    'characters_missing_images': total_characters - characters_with_images,
                    'characters': status_list
                }

        except Exception as e:
            logger.error(f"Error getting character generation status: {str(e)}")
            return {'error': f'Error getting status: {str(e)}'}

    def delete_character_images(self, character_id: str):
        """Delete character images (both full and resized)."""
        try:
            character = self.get_character_by_id(character_id)
            if not character:
                return False, "Character not found"

            full_path = self.get_character_image_path(character_id, 'full')
            resized_path = self.get_character_image_path(character_id, 'resized')

            deleted_files = []

            if full_path and full_path.exists():
                full_path.unlink()
                deleted_files.append('full size image')

            if resized_path and resized_path.exists():
                resized_path.unlink()
                deleted_files.append('resized image')

            if deleted_files:
                logger.info(f"Deleted {', '.join(deleted_files)} for character {character_id}")
                return True, f"Deleted {', '.join(deleted_files)}"
            else:
                return True, "No images found to delete"

        except Exception as e:
            logger.error(f"Error deleting images for character {character_id}: {str(e)}")
            return False, f"Error deleting images: {str(e)}"