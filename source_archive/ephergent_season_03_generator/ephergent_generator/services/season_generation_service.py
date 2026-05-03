"""Service for managing season-wide story generation from story arc files."""
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from ephergent_generator import db
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services.queue_service import StoryQueueService

logger = logging.getLogger(__name__)


class SeasonGenerationService:
    """Service for managing season-wide story generation from story arc files.

    This service handles loading season story arcs from JSON files and creating
    Story records for automated generation through the workflow pipeline.
    """

    def __init__(self, season_number: int = 3):
        """Initialize the season generation service.

        Args:
            season_number: The season number to generate episodes for (default: 3)
        """
        self.season_number = season_number
        self.queue_service = StoryQueueService()
        self.arc_data = None
        self._load_season_arc()

    def _load_season_arc(self):
        """Load season arc JSON from the_ephergent_lore directory."""
        try:
            # Navigate to the_ephergent_lore directory
            project_root = Path(__file__).parent.parent.parent
            arc_file = project_root / 'the_ephergent_lore' / f'season_0{self.season_number}' / f'season_0{self.season_number}_story_arc.json'

            if not arc_file.exists():
                logger.error(f"Season arc file not found: {arc_file}")
                self.arc_data = {'ephergent_stories_season_03': []}
                return

            with open(arc_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Extract episodes array from the wrapper
                self.arc_data = data.get(f'ephergent_stories_season_0{self.season_number}', [])

            logger.info(f"Loaded season {self.season_number} arc with {len(self.arc_data)} episodes")

        except Exception as e:
            logger.error(f"Error loading season arc: {str(e)}")
            self.arc_data = []

    def build_episode_topic(self, episode_data: Dict) -> str:
        """Build comprehensive topic from episode data.

        Constructs a rich topic prompt that includes all narrative structure
        and character focus details for the AI to generate a complete episode.

        Args:
            episode_data: Episode data dictionary from story arc JSON

        Returns:
            Comprehensive topic string for story generation
        """
        parts = [
            f"## Episode {episode_data['episode']}: {episode_data['title']}",
            f"\n### Hook\n{episode_data['hook']}",
            "\n### Narrative Structure",
        ]

        # Add narrative structure beats
        narrative = episode_data.get('narrative_structure', {})
        for key in ['opening_incident', 'escalating_conflict', 'character_journey',
                   'climactic_choice', 'resolution_setup']:
            if key in narrative:
                label = key.replace('_', ' ').title()
                parts.append(f"\n**{label}:** {narrative[key]}")

        # Add character focus
        parts.append("\n### Character Focus")
        character_focus = episode_data.get('character_focus', {})
        for character, beat in character_focus.items():
            parts.append(f"\n**{character.replace('_', ' ').title()}:** {beat}")

        # Add genre tags
        genre_tags = episode_data.get('genre_tags', [])
        if genre_tags:
            parts.append(f"\n\n### Genre Tags\n{', '.join(genre_tags)}")

        return "\n".join(parts)

    def create_episode_story(self, episode_number: int, priority: int = 0) -> Optional[Story]:
        """Create a Story record for a specific episode and queue it.

        Args:
            episode_number: Episode number (1-12)
            priority: Queue priority (higher = processed first)

        Returns:
            Created Story object, or None if episode not found
        """
        # Find episode in arc data
        episode_data = None
        for ep in self.arc_data:
            if ep.get('episode') == episode_number:
                episode_data = ep
                break

        if not episode_data:
            logger.error(f"Episode {episode_number} not found in season arc")
            return None

        try:
            # Build comprehensive topic
            topic = self.build_episode_topic(episode_data)

            # Extract genre (use first genre tag or default)
            genre_tags = episode_data.get('genre_tags', [])
            genre = genre_tags[0] if genre_tags else 'episodic_adventure'

            # Create story
            story = Story(
                topic=topic,
                title=None,  # Will be generated
                genre=genre,
                tone='conversational',  # Pixel's default tone
                word_count=1000,  # Season 03 target
                narrator_character_id=episode_data.get('suggested_narrator', 'pixel_paradox'),
                dimension_location=episode_data.get('dimension')
            )

            # Store episode metadata in workflow_data
            workflow_data = {
                'season': self.season_number,
                'episode_number': episode_number,
                'original_title': episode_data.get('title'),
                'dimension': episode_data.get('dimension'),
                'genre_tags': genre_tags,
                'character_focus': episode_data.get('character_focus', {}),
                'narrative_beats': episode_data.get('narrative_structure', {})
            }
            story.set_workflow_data(workflow_data)

            # Save to database
            db.session.add(story)
            db.session.commit()

            # Queue for processing
            self.queue_service.enqueue_story(story.id, priority=priority)

            logger.info(f"Created and queued story for Episode {episode_number}: {episode_data.get('title')}")

            return story

        except Exception as e:
            logger.error(f"Error creating episode story: {str(e)}")
            db.session.rollback()
            return None

    def queue_all_episodes(self, priority_mode: str = 'sequential') -> List[Story]:
        """Queue all 12 episodes with specified priority strategy.

        Args:
            priority_mode: Priority strategy - 'sequential' (1 highest),
                          'batch' (all same), or 'reverse' (12 highest)

        Returns:
            List of created Story objects
        """
        stories = []

        for episode_data in self.arc_data:
            episode_num = episode_data.get('episode')

            # Calculate priority based on mode
            if priority_mode == 'sequential':
                priority = 100 - episode_num  # Episode 1 = priority 99, Episode 12 = priority 88
            elif priority_mode == 'reverse':
                priority = 88 + episode_num   # Episode 12 = priority 100, Episode 1 = priority 89
            else:  # batch
                priority = 50  # All same priority

            story = self.create_episode_story(episode_num, priority=priority)
            if story:
                stories.append(story)

        logger.info(f"Queued {len(stories)} episodes with {priority_mode} priority")
        return stories

    def get_season_progress(self) -> Dict:
        """Get generation status for all season episodes.

        Returns:
            Dictionary with season progress information
        """
        # Query all stories with this season in workflow_data
        all_stories = Story.query.all()

        season_stories = []
        for story in all_stories:
            workflow_data = story.get_workflow_data()
            if workflow_data.get('season') == self.season_number:
                season_stories.append(story)

        # Build progress report
        episodes_status = {}
        for i in range(1, 13):  # Episodes 1-12
            episode_story = None
            for story in season_stories:
                if story.get_workflow_data().get('episode_number') == i:
                    episode_story = story
                    break

            if episode_story:
                episodes_status[i] = {
                    'story_id': episode_story.id,
                    'title': episode_story.title or episode_story.get_workflow_data().get('original_title'),
                    'status': episode_story.current_step.value if episode_story.current_step else 'unknown',
                    'completed': episode_story.current_step == WorkflowStep.COMPLETED,
                    'failed': episode_story.current_step == WorkflowStep.FAILED,
                    'created_at': episode_story.created_at.isoformat() if episode_story.created_at else None
                }
            else:
                episodes_status[i] = {
                    'story_id': None,
                    'title': None,
                    'status': 'not_queued',
                    'completed': False,
                    'failed': False,
                    'created_at': None
                }

        # Calculate summary
        completed_count = sum(1 for ep in episodes_status.values() if ep['completed'])
        in_progress_count = sum(1 for ep in episodes_status.values()
                               if ep['status'] not in ['not_queued', 'completed', 'failed'])
        failed_count = sum(1 for ep in episodes_status.values() if ep['failed'])

        return {
            'season': self.season_number,
            'total_episodes': 12,
            'completed': completed_count,
            'in_progress': in_progress_count,
            'failed': failed_count,
            'not_queued': 12 - completed_count - in_progress_count - failed_count,
            'episodes': episodes_status
        }
