from datetime import datetime, timedelta
from sqlalchemy import and_, or_
from ephergent_generator import db
from ephergent_generator.models import Story, StoryQueue, WorkflowStep
import uuid
import logging

logger = logging.getLogger(__name__)

class StoryQueueService:
    """Service for managing the story processing queue."""
    
    @staticmethod
    def enqueue_story(story_id, priority=0):
        """Add a story to the processing queue."""
        try:
            # Check if already queued
            existing = StoryQueue.query.filter_by(story_id=story_id).first()
            if existing:
                logger.info(f"Story {story_id} already in queue")
                return existing
            
            # Create queue entry
            queue_entry = StoryQueue(
                story_id=story_id,
                priority=priority
            )
            db.session.add(queue_entry)
            db.session.commit()
            
            logger.info(f"Story {story_id} added to queue with priority {priority}")
            return queue_entry
            
        except Exception as e:
            logger.error(f"Error enqueuing story {story_id}: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_next_story(worker_id=None):
        """Get the next story to process from the queue."""
        try:
            # Generate worker ID if not provided
            if not worker_id:
                worker_id = f"worker_{uuid.uuid4().hex[:8]}"
            
            # Find stories that need processing, ordered by priority (desc) then creation time (asc)
            # Phase 1.2: Filter out stories not ready for retry
            now = datetime.utcnow()
            query = db.session.query(StoryQueue, Story).join(Story).filter(
                and_(
                    StoryQueue.processing_started_at.is_(None),  # Not currently being processed
                    Story.current_step != WorkflowStep.COMPLETED,  # Not completed
                    Story.current_step != WorkflowStep.FAILED,  # Not failed
                    # Phase 1.2: Only process stories ready for retry
                    or_(
                        Story.next_retry_at.is_(None),  # No retry scheduled
                        Story.next_retry_at <= now  # Retry time has passed
                    )
                )
            ).order_by(
                StoryQueue.priority.desc(),
                StoryQueue.created_at.asc()
            )
            
            result = query.first()
            if not result:
                return None
            
            queue_entry, story = result
            
            # Mark as being processed
            queue_entry.processing_started_at = datetime.utcnow()
            queue_entry.worker_id = worker_id
            db.session.commit()
            
            logger.info(f"Worker {worker_id} claimed story {story.id} from queue")
            return story
            
        except Exception as e:
            logger.error(f"Error getting next story from queue: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def complete_story(story_id, worker_id):
        """Mark a story as completed and remove from queue."""
        try:
            # Find the queue entry
            queue_entry = StoryQueue.query.filter_by(
                story_id=story_id,
                worker_id=worker_id
            ).first()
            
            if queue_entry:
                db.session.delete(queue_entry)
                db.session.commit()
                logger.info(f"Story {story_id} completed by worker {worker_id}, removed from queue")
                return True
            else:
                logger.warning(f"No queue entry found for story {story_id} and worker {worker_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error completing story {story_id}: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def release_story(story_id, worker_id):
        """Release a story back to the queue (if worker fails or times out)."""
        try:
            queue_entry = StoryQueue.query.filter_by(
                story_id=story_id,
                worker_id=worker_id
            ).first()
            
            if queue_entry:
                queue_entry.processing_started_at = None
                queue_entry.worker_id = None
                db.session.commit()
                logger.info(f"Story {story_id} released back to queue by worker {worker_id}")
                return True
            else:
                logger.warning(f"No queue entry found for story {story_id} and worker {worker_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error releasing story {story_id}: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def cleanup_stale_workers(timeout_minutes=30):
        """Clean up stale worker assignments (workers that started but never finished)."""
        try:
            timeout_time = datetime.utcnow() - timedelta(minutes=timeout_minutes)
            
            stale_entries = StoryQueue.query.filter(
                and_(
                    StoryQueue.processing_started_at.isnot(None),
                    StoryQueue.processing_started_at < timeout_time
                )
            ).all()
            
            for entry in stale_entries:
                logger.warning(f"Releasing stale worker assignment: story {entry.story_id}, worker {entry.worker_id}")
                entry.processing_started_at = None
                entry.worker_id = None
            
            db.session.commit()
            logger.info(f"Cleaned up {len(stale_entries)} stale worker assignments")
            return len(stale_entries)
            
        except Exception as e:
            logger.error(f"Error cleaning up stale workers: {str(e)}")
            db.session.rollback()
            raise
    
    @staticmethod
    def get_queue_status():
        """Get current queue statistics."""
        try:
            total_queued = StoryQueue.query.count()
            processing = StoryQueue.query.filter(StoryQueue.processing_started_at.isnot(None)).count()
            waiting = total_queued - processing
            
            # Get story status counts
            stories_by_step = db.session.query(
                Story.current_step, 
                db.func.count(Story.id)
            ).group_by(Story.current_step).all()
            
            step_counts = {}
            for step, count in stories_by_step:
                step_counts[step.value if step else 'unknown'] = count
            
            return {
                'queue': {
                    'total_queued': total_queued,
                    'waiting': waiting,
                    'processing': processing
                },
                'stories_by_step': step_counts
            }
            
        except Exception as e:
            logger.error(f"Error getting queue status: {str(e)}")
            raise