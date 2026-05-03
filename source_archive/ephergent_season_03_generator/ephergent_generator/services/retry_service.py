"""Retry service for Phase 1.2 automatic error recovery.

Provides exponential backoff calculation and retry decision logic.
Integrates with error classification to determine retry strategy.
"""

import logging
import random
from datetime import datetime, timedelta
from typing import Optional
from ephergent_generator import db
from ephergent_generator.models import Story, SystemConfig
from ephergent_generator.utils.error_classifier import ErrorType, error_classifier

logger = logging.getLogger(__name__)


class RetryService:
    """Manages retry logic with exponential backoff for story workflow failures."""

    # Default configuration (can be overridden via SystemConfig)
    DEFAULT_MAX_RETRIES = 5
    DEFAULT_BASE_DELAY_SECONDS = 60  # 1 minute
    DEFAULT_BACKOFF_MULTIPLIER = 2.0
    DEFAULT_MAX_DELAY_SECONDS = 1800  # 30 minutes
    DEFAULT_JITTER_FACTOR = 0.1  # 10% random jitter

    def __init__(self):
        """Initialize retry service."""
        self._load_config()

    def _load_config(self):
        """Load retry configuration from SystemConfig."""
        try:
            self.max_retries = SystemConfig.get_config('retry.max_attempts', self.DEFAULT_MAX_RETRIES)
            self.base_delay = SystemConfig.get_config('retry.base_delay_seconds', self.DEFAULT_BASE_DELAY_SECONDS)
            self.backoff_multiplier = SystemConfig.get_config('retry.backoff_multiplier', self.DEFAULT_BACKOFF_MULTIPLIER)
            self.max_delay = SystemConfig.get_config('retry.max_delay_seconds', self.DEFAULT_MAX_DELAY_SECONDS)
            self.jitter_factor = SystemConfig.get_config('retry.jitter_factor', self.DEFAULT_JITTER_FACTOR)
        except Exception as e:
            logger.warning(f"Failed to load retry config from SystemConfig, using defaults: {e}")
            self.max_retries = self.DEFAULT_MAX_RETRIES
            self.base_delay = self.DEFAULT_BASE_DELAY_SECONDS
            self.backoff_multiplier = self.DEFAULT_BACKOFF_MULTIPLIER
            self.max_delay = self.DEFAULT_MAX_DELAY_SECONDS
            self.jitter_factor = self.DEFAULT_JITTER_FACTOR

    def should_retry_story(self, story: Story, exception: Exception, error_message: str = None) -> bool:
        """Determine if a story should be retried based on error type and retry count.

        Args:
            story: Story that failed
            exception: Exception that occurred
            error_message: Optional error message

        Returns:
            True if story should be retried automatically
        """
        # Classify the error
        error_type, friendly_message = error_classifier.classify_error(exception, error_message)

        # Check if error type is retryable
        if not error_classifier.should_retry(error_type):
            logger.info(f"Story {story.id} error type {error_type.value} is not retryable")
            return False

        # Check if we've exhausted retries
        if story.retry_count >= story.max_retries:
            logger.info(f"Story {story.id} has exhausted retries ({story.retry_count}/{story.max_retries})")
            return False

        logger.info(f"Story {story.id} is eligible for retry (attempt {story.retry_count + 1}/{story.max_retries})")
        return True

    def calculate_retry_delay(self, story: Story, error_type: ErrorType) -> timedelta:
        """Calculate exponential backoff delay for next retry.

        Formula: delay = base_delay * (backoff_multiplier ^ retry_count) * error_multiplier * (1 + random_jitter)

        Args:
            story: Story to calculate delay for
            error_type: Classified error type

        Returns:
            timedelta for next retry
        """
        # Base exponential backoff
        exponential_delay = self.base_delay * (self.backoff_multiplier ** story.retry_count)

        # Apply error-type specific multiplier
        error_multiplier = error_classifier.get_retry_delay_multiplier(error_type)
        delay = exponential_delay * error_multiplier

        # Cap at maximum delay
        delay = min(delay, self.max_delay)

        # Add random jitter to prevent thundering herd
        jitter = random.uniform(-self.jitter_factor, self.jitter_factor)
        delay_with_jitter = delay * (1 + jitter)

        # Ensure minimum delay of 10 seconds
        delay_with_jitter = max(delay_with_jitter, 10)

        logger.info(
            f"Retry delay for story {story.id}: "
            f"{delay_with_jitter:.1f}s (base={self.base_delay}s, "
            f"attempt={story.retry_count}, error_type={error_type.value})"
        )

        return timedelta(seconds=delay_with_jitter)

    def record_retry_attempt(self, story: Story, exception: Exception, error_message: str = None):
        """Record a retry attempt on a story.

        Args:
            story: Story that failed
            exception: Exception that occurred
            error_message: Optional error message
        """
        # Classify error
        error_type, friendly_message = error_classifier.classify_error(exception, error_message)

        # Increment retry count
        story.retry_count += 1
        story.last_retry_at = datetime.utcnow()

        # Store error classification
        story.error_type = error_type.value
        story.error_message = error_message or str(exception)

        # Calculate next retry time
        retry_delay = self.calculate_retry_delay(story, error_type)
        story.next_retry_at = datetime.utcnow() + retry_delay

        # Store current workflow step as failed_at_step
        story.failed_at_step = story.current_step

        logger.info(
            f"Recorded retry attempt for story {story.id}: "
            f"attempt {story.retry_count}/{story.max_retries}, "
            f"error_type={error_type.value}, "
            f"next_retry_at={story.next_retry_at.isoformat()}"
        )

    def reset_retry_state(self, story: Story):
        """Reset retry state after successful operation.

        Args:
            story: Story to reset
        """
        story.retry_count = 0
        story.last_retry_at = None
        story.next_retry_at = None
        story.error_type = None
        story.failed_at_step = None
        # Note: Don't clear error_message - keep for historical context

        logger.debug(f"Reset retry state for story {story.id}")

    def is_ready_for_retry(self, story: Story) -> bool:
        """Check if a story is ready for retry based on next_retry_at.

        Args:
            story: Story to check

        Returns:
            True if current time >= next_retry_at
        """
        if not story.next_retry_at:
            return True  # No retry scheduled, ready immediately

        now = datetime.utcnow()
        is_ready = now >= story.next_retry_at

        if not is_ready:
            wait_seconds = (story.next_retry_at - now).total_seconds()
            logger.debug(f"Story {story.id} not ready for retry - wait {wait_seconds:.0f}s more")

        return is_ready


# Singleton instance
retry_service = RetryService()
