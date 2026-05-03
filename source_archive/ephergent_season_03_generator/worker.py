#!/usr/bin/env python3
"""
Story processing worker for Season 02 Generator.

This worker processes stories from the queue through the workflow steps:
1. Story Generation (from topic)
2. Title Generation
3. Image Generation (future)
4. Audio Generation (future)
5. Completion

Usage:
    python worker.py [--continuous] [--max-stories N]
    
    --continuous    Keep running and processing stories continuously
    --max-stories   Maximum number of stories to process (default: 1)
"""

import os
import sys
import time
import argparse
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ephergent_generator import create_app
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.queue_service import StoryQueueService
from config import get_config

logger = logging.getLogger(__name__)

class StoryWorker:
    """Worker for processing stories from the queue."""
    
    def __init__(self, config_name=None):
        # Create app with configuration
        self.app = create_app(config_name)
        self.config = get_config(config_name)
        
        # Set up logging based on config
        with self.app.app_context():
            logging.basicConfig(
                level=getattr(logging, self.app.config['LOG_LEVEL']),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(self.app.config.get('LOG_FILE', 'worker.log')),
                    logging.StreamHandler()
                ]
            )
        
        self.workflow_service = None
        self.queue_service = None
        
    def initialize_services(self):
        """Initialize services within Flask app context."""
        with self.app.app_context():
            self.workflow_service = StoryWorkflowService()
            self.queue_service = StoryQueueService()
    
    def process_single_story(self):
        """Process a single story from the queue."""
        with self.app.app_context():
            try:
                story = self.workflow_service.process_next_story()
                if story:
                    logger.info(f"Processed story {story.id}, current step: {story.current_step.value}")
                    return True
                else:
                    # Changed noisy informational message to DEBUG so it won't clutter logs at INFO level
                    logger.debug("No stories to process in queue")
                    return False
            except Exception as e:
                logger.error(f"Error processing story: {str(e)}")
                return False
    
    def run_continuous(self, sleep_interval=None, max_stories=None):
        """Run worker continuously, processing stories as they appear."""
        if sleep_interval is None:
            with self.app.app_context():
                sleep_interval = self.app.config.get('WORKER_SLEEP_INTERVAL', 5)
        
        logger.info(f"Starting continuous worker (sleep interval: {sleep_interval}s)")
        
        if max_stories:
            logger.info(f"Will process maximum {max_stories} stories")
        
        processed_count = 0
        
        try:
            while True:
                had_work = self.process_single_story()
                
                if had_work:
                    processed_count += 1
                    if max_stories and processed_count >= max_stories:
                        logger.info(f"Reached maximum story limit ({max_stories}), stopping")
                        break
                else:
                    # No work available, sleep before checking again
                    time.sleep(sleep_interval)
                
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down gracefully")
        except Exception as e:
            logger.error(f"Unexpected error in continuous worker: {str(e)}")
            raise
        
        logger.info(f"Worker processed {processed_count} stories")
    
    def run_batch(self, max_stories):
        """Run worker in batch mode, processing up to max_stories."""
        logger.info(f"Starting batch worker (max stories: {max_stories})")
        
        processed_count = 0
        
        while processed_count < max_stories:
            had_work = self.process_single_story()
            
            if had_work:
                processed_count += 1
            else:
                # Changed noisy informational message to DEBUG so batch runs aren't noisy when empty
                logger.debug("No more stories to process")
                break
        
        logger.info(f"Batch worker processed {processed_count} stories")
    
    def cleanup_stale_workers(self, timeout_minutes=None):
        """Clean up stale worker assignments."""
        with self.app.app_context():
            try:
                if timeout_minutes is None:
                    timeout_minutes = self.app.config.get('WORKER_TIMEOUT_MINUTES', 30)
                
                cleaned = self.queue_service.cleanup_stale_workers(timeout_minutes)
                logger.info(f"Cleaned up {cleaned} stale worker assignments")
                return cleaned
            except Exception as e:
                logger.error(f"Error cleaning up stale workers: {str(e)}")
                return 0
    
    def show_queue_status(self):
        """Display current queue status."""
        with self.app.app_context():
            try:
                status = self.queue_service.get_queue_status()
                
                print("\n=== Queue Status ===")
                print(f"Total queued stories: {status['queue']['total_queued']}")
                print(f"  - Waiting: {status['queue']['waiting']}")
                print(f"  - Processing: {status['queue']['processing']}")
                
                print("\n=== Stories by Step ===")
                for step, count in status['stories_by_step'].items():
                    print(f"  - {step}: {count}")
                print()
                
            except Exception as e:
                logger.error(f"Error getting queue status: {str(e)}")

def main():
    """Main entry point for the worker."""
    parser = argparse.ArgumentParser(
        description="Story processing worker for Season 02 Generator"
    )
    parser.add_argument(
        '--env',
        choices=['development', 'testing', 'production'],
        help='Configuration environment to use'
    )
    parser.add_argument(
        '--continuous', 
        action='store_true',
        help='Run continuously, processing stories as they appear'
    )
    parser.add_argument(
        '--max-stories',
        type=int,
        default=1,
        help='Maximum number of stories to process (default: 1)'
    )
    parser.add_argument(
        '--sleep-interval',
        type=int,
        default=5,
        help='Sleep interval in seconds between queue checks (continuous mode only)'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up stale worker assignments and exit'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show queue status and exit'
    )
    
    args = parser.parse_args()
    
    # Create worker with specified environment
    config_name = args.env or os.environ.get('FLASK_ENV', 'development')
    worker = StoryWorker(config_name)
    
    # Validate configuration
    config_class = get_config(config_name)
    validation_errors = config_class.validate_required_config()
    if validation_errors:
        logger.error("Configuration errors:")
        for error in validation_errors:
            logger.error(f"  - {error}")
        sys.exit(1)
    
    # Initialize services
    worker.initialize_services()
    
    logger.info(f"Worker starting with {config_class.__name__}")
    with worker.app.app_context():
        logger.info(f"Database: {worker.app.config['SQLALCHEMY_DATABASE_URI']}")
        logger.info(f"Gemini Model: {worker.app.config['GEMINI_MODEL']}")
    
    # Handle special commands
    if args.cleanup:
        worker.cleanup_stale_workers()
        return
    
    if args.status:
        worker.show_queue_status()
        return
    
    # Run worker
    if args.continuous:
        worker.run_continuous(
            sleep_interval=args.sleep_interval,
            max_stories=args.max_stories if args.max_stories > 1 else None
        )
    else:
        worker.run_batch(args.max_stories)

if __name__ == "__main__":
    main()