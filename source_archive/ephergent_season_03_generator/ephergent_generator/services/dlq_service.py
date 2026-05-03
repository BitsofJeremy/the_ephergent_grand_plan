"""Dead Letter Queue (DLQ) service for Phase 1.2.

Manages permanently failed stories that have exhausted retries or
encountered unrecoverable errors. Provides manual review and retry capabilities.
"""

import logging
import traceback
from datetime import datetime
from typing import List, Optional
from sqlalchemy import desc
from ephergent_generator import db
from ephergent_generator.models import Story, StoryFailure, WorkflowStep
from ephergent_generator.utils.error_classifier import ErrorType, error_classifier

logger = logging.getLogger(__name__)


class DLQService:
    """Manages Dead Letter Queue for permanently failed stories."""

    def add_to_dlq(
        self,
        story: Story,
        exception: Exception,
        error_message: str = None,
        stack_trace_str: str = None
    ) -> StoryFailure:
        """Add a story to the Dead Letter Queue.

        Args:
            story: Story that failed permanently
            exception: Exception that caused the failure
            error_message: Optional custom error message
            stack_trace_str: Optional stack trace string

        Returns:
            Created StoryFailure record
        """
        # Classify the error
        error_type, friendly_reason = error_classifier.classify_error(exception, error_message)

        # Get stack trace if not provided
        if stack_trace_str is None:
            stack_trace_str = traceback.format_exc()

        # Determine if story can be manually retried
        can_retry = error_type not in (ErrorType.VALIDATION, ErrorType.PERMANENT)

        # Determine if intervention is required
        requires_intervention = error_type in (
            ErrorType.CONFIGURATION,
            ErrorType.VALIDATION,
            ErrorType.PERMANENT
        )

        # Set priority (higher for more critical errors)
        priority = self._calculate_priority(error_type, story)

        # Check if failure already exists (shouldn't happen, but handle it)
        existing_failure = StoryFailure.query.filter_by(story_id=story.id).first()
        if existing_failure:
            logger.warning(f"Story {story.id} already in DLQ - updating existing record")
            failure = existing_failure
            failure.failed_at_step = story.failed_at_step or story.current_step
            failure.error_type = error_type.value
            failure.error_message = error_message or str(exception)
            failure.stack_trace = stack_trace_str
            failure.retry_count = story.retry_count
            failure.failure_reason = friendly_reason
            failure.can_retry = can_retry
            failure.requires_intervention = requires_intervention
            failure.priority = priority
            failure.updated_at = datetime.utcnow()
        else:
            # Create new failure record
            failure = StoryFailure(
                story_id=story.id,
                failed_at_step=story.failed_at_step or story.current_step,
                error_type=error_type.value,
                error_message=error_message or str(exception),
                stack_trace=stack_trace_str,
                retry_count=story.retry_count,
                failure_reason=friendly_reason,
                can_retry=can_retry,
                requires_intervention=requires_intervention,
                dlq_status='pending',
                priority=priority,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(failure)

        # Mark story as FAILED
        story.current_step = WorkflowStep.FAILED

        db.session.commit()

        logger.info(
            f"Added story {story.id} to DLQ: "
            f"error_type={error_type.value}, "
            f"can_retry={can_retry}, "
            f"priority={priority}"
        )

        return failure

    def _calculate_priority(self, error_type: ErrorType, story: Story) -> int:
        """Calculate priority for DLQ entry (higher = more urgent).

        Args:
            error_type: Classified error type
            story: Failed story

        Returns:
            Priority score (0-10)
        """
        priority = 0

        # Base priority by error type
        if error_type == ErrorType.PERMANENT:
            priority += 3  # Unknown errors need investigation
        elif error_type == ErrorType.CONFIGURATION:
            priority += 2  # Config errors need fixing
        elif error_type == ErrorType.VALIDATION:
            priority += 1  # Data errors less urgent

        # Increase priority for stories that made it further in workflow
        workflow_steps = list(WorkflowStep)
        if story.current_step and story.current_step in workflow_steps:
            step_index = workflow_steps.index(story.current_step)
            priority += min(step_index // 2, 3)  # Max +3 for advanced failures

        # Increase priority for stories with many retries
        if story.retry_count >= 5:
            priority += 2

        return min(priority, 10)  # Cap at 10

    def get_dlq_stories(
        self,
        status: str = None,
        error_type: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[StoryFailure]:
        """Retrieve stories from DLQ with filtering.

        Args:
            status: Filter by DLQ status (pending, investigating, resolved, archived)
            error_type: Filter by error type
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of StoryFailure records
        """
        query = StoryFailure.query

        if status:
            query = query.filter_by(dlq_status=status)

        if error_type:
            query = query.filter_by(error_type=error_type)

        # Order by priority (high to low) then creation time (newest first)
        query = query.order_by(desc(StoryFailure.priority), desc(StoryFailure.created_at))

        return query.limit(limit).offset(offset).all()

    def get_dlq_count(self, status: str = None) -> int:
        """Get count of stories in DLQ.

        Args:
            status: Optional status filter

        Returns:
            Count of DLQ entries
        """
        query = StoryFailure.query

        if status:
            query = query.filter_by(dlq_status=status)

        return query.count()

    def resolve_failure(self, failure_id: int, user_id: int, notes: str = None):
        """Mark a DLQ entry as resolved.

        Args:
            failure_id: StoryFailure ID
            user_id: User who resolved the failure
            notes: Optional resolution notes
        """
        failure = StoryFailure.query.get(failure_id)
        if not failure:
            raise ValueError(f"StoryFailure {failure_id} not found")

        failure.mark_resolved(user_id, notes)
        db.session.commit()

        logger.info(f"Marked StoryFailure {failure_id} as resolved by user {user_id}")

    def retry_from_dlq(self, failure_id: int) -> Story:
        """Retry a story from DLQ by resetting it to failed step.

        Args:
            failure_id: StoryFailure ID to retry

        Returns:
            Story that was reset for retry
        """
        failure = StoryFailure.query.get(failure_id)
        if not failure:
            raise ValueError(f"StoryFailure {failure_id} not found")

        if not failure.can_retry:
            raise ValueError(f"StoryFailure {failure_id} is not retryable")

        story = failure.story
        if not story:
            raise ValueError(f"Story {failure.story_id} not found")

        # Reset story to the step where it failed
        story.current_step = failure.failed_at_step
        story.retry_count = 0  # Reset retry count for manual retry
        story.last_retry_at = None
        story.next_retry_at = None
        story.error_type = None
        story.error_message = None

        # Mark failure as investigating (will be resolved if retry succeeds)
        failure.mark_investigating()

        db.session.commit()

        logger.info(
            f"Retrying story {story.id} from DLQ - reset to step {failure.failed_at_step.value}"
        )

        return story


# Singleton instance
dlq_service = DLQService()
