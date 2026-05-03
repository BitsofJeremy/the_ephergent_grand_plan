"""Service for migrating file-based data to database."""
import json
import logging
from pathlib import Path
from ephergent_generator import db
from ephergent_generator.models import Character, SystemConfig

logger = logging.getLogger(__name__)


class MigrationService:
    """Service for migrating legacy file-based configuration to database."""

    @staticmethod
    def migrate_characters_from_files(user_id=None):
        """Migrate characters from personality_prompts_s3.json and markdown files to database.

        Args:
            user_id: ID of user performing migration (for audit trail)

        Returns:
            Dictionary with migration results
        """
        try:
            # Get paths
            app_root = Path(__file__).parent.parent
            json_file = app_root / 'prompts' / 'personality_prompts_s3.json'
            characters_dir = app_root / 'prompts' / 'characters'

            if not json_file.exists():
                return {
                    'success': False,
                    'error': f'JSON file not found: {json_file}'
                }

            # Load JSON configuration
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            migrated = []
            skipped = []
            errors = []

            for char_data in data.get('reporters', []):
                try:
                    character_id = char_data.get('id')

                    # Check if already exists
                    existing = Character.query.filter_by(character_id=character_id).first()
                    if existing:
                        skipped.append({
                            'character_id': character_id,
                            'reason': 'Already exists in database'
                        })
                        continue

                    # Load personality prompt from markdown file
                    prompt_file = char_data.get('prompt_file')
                    if prompt_file:
                        # Strip "characters/" prefix if present (legacy format compatibility)
                        if prompt_file.startswith('characters/'):
                            prompt_file = prompt_file.replace('characters/', '', 1)

                        prompt_path = characters_dir / prompt_file
                        if prompt_path.exists():
                            with open(prompt_path, 'r', encoding='utf-8') as f:
                                personality_prompt = f.read()
                        else:
                            personality_prompt = f"[Missing prompt file: {prompt_file}]"
                    else:
                        personality_prompt = "[No prompt file specified]"

                    # Create character
                    character = Character(
                        character_id=character_id,
                        name=char_data.get('name'),
                        email=char_data.get('email'),
                        personality_prompt=personality_prompt,
                        stable_diffusion_prompt=char_data.get('stable_diffusion_prompt'),
                        voice_model=char_data.get('voice'),
                        ai_model=char_data.get('model', 'gemini-2.5-flash'),
                        is_default=char_data.get('default', False),
                        is_active=True,
                        sort_order=len(migrated),  # Use order from JSON
                        created_by=user_id,
                        updated_by=user_id
                    )

                    # Set JSON fields
                    if 'topics' in char_data:
                        character.set_topics(char_data['topics'])
                    if 'tags' in char_data:
                        character.set_tags(char_data['tags'])

                    db.session.add(character)
                    migrated.append({
                        'character_id': character_id,
                        'name': char_data.get('name')
                    })

                except Exception as e:
                    logger.error(f"Error migrating character {char_data.get('id')}: {str(e)}")
                    errors.append({
                        'character_id': char_data.get('id'),
                        'error': str(e)
                    })

            # Commit all changes
            db.session.commit()

            logger.info(f"Character migration complete: {len(migrated)} migrated, {len(skipped)} skipped, {len(errors)} errors")

            return {
                'success': True,
                'migrated_count': len(migrated),
                'skipped_count': len(skipped),
                'error_count': len(errors),
                'migrated': migrated,
                'skipped': skipped,
                'errors': errors
            }

        except Exception as e:
            logger.error(f"Error during character migration: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def migrate_universe_prompt(user_id=None):
        """Migrate universe prompt from markdown file to database.

        Args:
            user_id: ID of user performing migration

        Returns:
            Dictionary with migration results
        """
        try:
            # Get path to universe prompt
            app_root = Path(__file__).parent.parent
            prompt_file = app_root / 'prompts' / 'ephergent_universe_prompt_season_03.md'

            if not prompt_file.exists():
                return {
                    'success': False,
                    'error': f'Universe prompt file not found: {prompt_file}'
                }

            # Load universe prompt
            with open(prompt_file, 'r', encoding='utf-8') as f:
                universe_prompt = f.read()

            # Check if already exists
            existing = SystemConfig.query.filter_by(
                config_key='universe.prompt.season_03'
            ).first()

            if existing:
                return {
                    'success': False,
                    'error': 'Universe prompt already exists in database',
                    'existing_version': existing.version
                }

            # Create system config directly
            config = SystemConfig(
                config_key='universe.prompt.season_03',
                config_value=universe_prompt,
                config_type='markdown',
                description='Season 03 Universe System Prompt',
                category='universe_prompts',
                is_public=False,
                updated_by=user_id,
                version=1
            )
            db.session.add(config)
            db.session.commit()

            logger.info("Universe prompt migrated to database successfully")

            return {
                'success': True,
                'config_key': 'universe.prompt.season_03',
                'config_id': config.id,
                'length': len(universe_prompt)
            }

        except Exception as e:
            logger.error(f"Error migrating universe prompt: {str(e)}")
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def migrate_all(user_id=None):
        """Migrate both characters and universe prompt.

        Args:
            user_id: ID of user performing migration

        Returns:
            Dictionary with combined migration results
        """
        logger.info("Starting full data migration from files to database")

        # Migrate characters
        char_result = MigrationService.migrate_characters_from_files(user_id)

        # Migrate universe prompt
        universe_result = MigrationService.migrate_universe_prompt(user_id)

        return {
            'characters': char_result,
            'universe_prompt': universe_result,
            'overall_success': char_result.get('success', False) and universe_result.get('success', False)
        }

    @staticmethod
    def get_migration_status():
        """Check migration status.

        Returns:
            Dictionary with current migration state
        """
        # Check characters
        char_count = Character.query.count()
        active_char_count = Character.query.filter_by(is_active=True).count()
        default_char = Character.query.filter_by(is_default=True).first()

        # Check universe prompt
        universe_config = SystemConfig.query.filter_by(
            config_key='universe.prompt.season_03'
        ).first()

        return {
            'characters': {
                'total': char_count,
                'active': active_char_count,
                'has_default': default_char is not None,
                'default_character': default_char.character_id if default_char else None
            },
            'universe_prompt': {
                'exists': universe_config is not None,
                'version': universe_config.version if universe_config else None,
                'length': len(universe_config.config_value) if universe_config and universe_config.config_value else 0
            },
            'migration_complete': char_count > 0 and universe_config is not None
        }
