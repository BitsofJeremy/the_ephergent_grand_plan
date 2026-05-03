#!/usr/bin/env python3
"""
Season 03 Episode Generation Manager

Manages automated generation of all Season 03 episodes from story arc.
"""
import sys
from pathlib import Path
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ephergent_generator import create_app
from ephergent_generator.services.season_generation_service import SeasonGenerationService
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_progress(progress):
    """Print season generation progress in a nice format."""
    print("\n" + "=" * 70)
    print(f"SEASON {progress['season']} GENERATION PROGRESS")
    print("=" * 70)
    print(f"\nTotal Episodes: {progress['total_episodes']}")
    print(f"Completed:      {progress['completed']}")
    print(f"In Progress:    {progress['in_progress']}")
    print(f"Failed:         {progress['failed']}")
    print(f"Not Queued:     {progress['not_queued']}")
    print("\n" + "-" * 70)
    print(f"{'Ep':<4} {'Status':<20} {'Story ID':<10} {'Title':<35}")
    print("-" * 70)

    for ep_num in sorted(progress['episodes'].keys()):
        ep = progress['episodes'][ep_num]
        status = ep['status']
        story_id = ep['story_id'] or 'N/A'
        title = (ep['title'] or 'Not Generated')[:34]

        # Color code status (if terminal supports it)
        if ep['completed']:
            status_display = f"✓ {status}"
        elif ep['failed']:
            status_display = f"✗ {status}"
        elif ep['status'] == 'not_queued':
            status_display = f"  {status}"
        else:
            status_display = f"⟳ {status}"

        print(f"{ep_num:<4} {status_display:<20} {story_id:<10} {title:<35}")

    print("=" * 70 + "\n")


def main():
    """Main entry point for season generation script."""
    parser = argparse.ArgumentParser(
        description='Manage Season 03 episode generation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Queue all episodes with sequential priority (Episode 1 first)
  python scripts/generate_season.py --queue-all

  # Queue all episodes in batch mode (all same priority)
  python scripts/generate_season.py --queue-all --priority batch

  # Queue a specific episode
  python scripts/generate_season.py --episode 5

  # Show current progress
  python scripts/generate_season.py --status

  # Queue episodes in reverse order (for testing)
  python scripts/generate_season.py --queue-all --priority reverse
        """
    )

    parser.add_argument(
        '--queue-all',
        action='store_true',
        help='Queue all 12 episodes for generation'
    )

    parser.add_argument(
        '--episode',
        type=int,
        metavar='N',
        help='Queue specific episode number (1-12)'
    )

    parser.add_argument(
        '--priority',
        choices=['sequential', 'batch', 'reverse'],
        default='sequential',
        help='Priority mode: sequential (Ep1 first), batch (all same), reverse (Ep12 first)'
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show season generation progress'
    )

    parser.add_argument(
        '--season',
        type=int,
        default=3,
        help='Season number (default: 3)'
    )

    args = parser.parse_args()

    # Validate episode number if provided
    if args.episode and (args.episode < 1 or args.episode > 12):
        print("Error: Episode number must be between 1 and 12")
        sys.exit(1)

    # Create Flask app context
    app = create_app()

    with app.app_context():
        service = SeasonGenerationService(season_number=args.season)

        if args.status:
            # Show progress
            logger.info("Fetching season generation progress...")
            progress = service.get_season_progress()
            print_progress(progress)

        elif args.queue_all:
            # Queue all episodes
            logger.info(f"Queuing all episodes with {args.priority} priority...")
            stories = service.queue_all_episodes(priority_mode=args.priority)

            print(f"\n✓ Successfully queued {len(stories)} episodes")
            print(f"  Priority mode: {args.priority}")
            print("\nEpisodes queued:")
            for story in stories:
                workflow_data = story.get_workflow_data()
                ep_num = workflow_data.get('episode_number')
                title = workflow_data.get('original_title')
                print(f"  Episode {ep_num}: {title} (Story ID: {story.id})")

            print("\nRun 'python scripts/generate_season.py --status' to check progress")

        elif args.episode:
            # Queue specific episode
            logger.info(f"Queuing episode {args.episode}...")
            story = service.create_episode_story(args.episode, priority=100)

            if story:
                workflow_data = story.get_workflow_data()
                print(f"\n✓ Successfully queued Episode {args.episode}")
                print(f"  Title: {workflow_data.get('original_title')}")
                print(f"  Story ID: {story.id}")
                print(f"  Dimension: {workflow_data.get('dimension')}")
                print("\nRun 'python scripts/generate_season.py --status' to check progress")
            else:
                print(f"\n✗ Failed to queue episode {args.episode}")
                sys.exit(1)

        else:
            parser.print_help()
            sys.exit(1)


if __name__ == '__main__':
    main()
