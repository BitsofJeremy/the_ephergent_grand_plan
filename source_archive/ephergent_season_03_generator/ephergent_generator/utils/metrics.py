"""Prometheus metrics collection for the Ephergent story generation system.

This module provides comprehensive metrics collection for monitoring system health,
performance, and business KPIs. Metrics are exported in Prometheus format for
scraping by Prometheus server and visualization in Grafana.

Usage:
    from ephergent_generator.utils.metrics import metrics_service

    # Initialize metrics (call once during app startup)
    metrics_service.init_app(app)

    # Record metrics throughout the application
    metrics_service.record_story_created()
    metrics_service.record_workflow_step_completed('image_generation', duration_seconds=45.2)
    metrics_service.record_api_request('/api/stories', 'POST', 201, duration_seconds=0.523)
"""

import logging
import time
from functools import wraps
from typing import Optional, Callable
from flask import Flask, request, g
from prometheus_client import (
    Counter, Histogram, Gauge, Info, Summary,
    CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST
)

logger = logging.getLogger(__name__)

# Import db lazily to avoid circular imports
db = None


class MetricsService:
    """Centralized Prometheus metrics collection service.

    Provides business metrics, infrastructure metrics, and request tracking
    for comprehensive observability of the story generation system.
    """

    def __init__(self):
        """Initialize metrics collectors."""
        self.registry = CollectorRegistry()
        self._initialized = False

        # ====================================================================
        # Business Metrics - Story Generation Workflow
        # ====================================================================

        self.stories_created_total = Counter(
            'ephergent_stories_created_total',
            'Total number of stories created',
            ['source'],  # web_ui, api, mcp_server
            registry=self.registry
        )

        self.workflow_steps_completed_total = Counter(
            'ephergent_workflow_steps_completed_total',
            'Total number of workflow steps completed successfully',
            ['step'],  # story_generation, image_generation, audio_generation, etc.
            registry=self.registry
        )

        self.workflow_steps_failed_total = Counter(
            'ephergent_workflow_steps_failed_total',
            'Total number of workflow steps that failed',
            ['step', 'error_type'],
            registry=self.registry
        )

        self.workflow_step_duration_seconds = Histogram(
            'ephergent_workflow_step_duration_seconds',
            'Duration of each workflow step in seconds',
            ['step'],
            buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600],  # 1s to 1 hour
            registry=self.registry
        )

        self.stories_completed_total = Counter(
            'ephergent_stories_completed_total',
            'Total number of stories that completed all workflow steps',
            registry=self.registry
        )

        self.story_queue_size = Gauge(
            'ephergent_story_queue_size',
            'Current number of stories in the processing queue',
            ['status'],  # pending, processing, failed
            registry=self.registry
        )

        self.story_processing_time_seconds = Summary(
            'ephergent_story_processing_time_seconds',
            'Total time from story creation to completion',
            registry=self.registry
        )

        # ====================================================================
        # Media Generation Metrics
        # ====================================================================

        self.images_generated_total = Counter(
            'ephergent_images_generated_total',
            'Total number of images generated',
            ['character'],
            registry=self.registry
        )

        self.audio_generated_total = Counter(
            'ephergent_audio_generated_total',
            'Total number of audio files generated',
            ['voice_model'],
            registry=self.registry
        )

        self.videos_generated_total = Counter(
            'ephergent_videos_generated_total',
            'Total number of videos generated',
            registry=self.registry
        )

        self.media_generation_errors_total = Counter(
            'ephergent_media_generation_errors_total',
            'Total number of media generation errors',
            ['media_type', 'error_type'],
            registry=self.registry
        )

        # ====================================================================
        # External Service Metrics
        # ====================================================================

        self.external_api_requests_total = Counter(
            'ephergent_external_api_requests_total',
            'Total number of external API requests',
            ['service', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.external_api_duration_seconds = Histogram(
            'ephergent_external_api_duration_seconds',
            'Duration of external API calls',
            ['service', 'endpoint'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry
        )

        self.external_service_available = Gauge(
            'ephergent_external_service_available',
            'Whether external service is available (1=up, 0=down)',
            ['service'],
            registry=self.registry
        )

        # ====================================================================
        # Database Metrics
        # ====================================================================

        self.database_connections_active = Gauge(
            'ephergent_database_connections_active',
            'Number of active database connections',
            registry=self.registry
        )

        self.database_query_duration_seconds = Histogram(
            'ephergent_database_query_duration_seconds',
            'Duration of database queries',
            ['query_type'],  # select, insert, update, delete
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5],
            registry=self.registry
        )

        self.database_errors_total = Counter(
            'ephergent_database_errors_total',
            'Total number of database errors',
            ['error_type'],
            registry=self.registry
        )

        # ====================================================================
        # HTTP Request Metrics
        # ====================================================================

        self.http_requests_total = Counter(
            'ephergent_http_requests_total',
            'Total HTTP requests received',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'ephergent_http_request_duration_seconds',
            'HTTP request latency',
            ['method', 'endpoint'],
            buckets=[0.01, 0.05, 0.1, 0.5, 1, 2, 5, 10],
            registry=self.registry
        )

        self.http_requests_in_progress = Gauge(
            'ephergent_http_requests_in_progress',
            'Number of HTTP requests currently being processed',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # ====================================================================
        # Worker Metrics
        # ====================================================================

        self.worker_heartbeat_timestamp = Gauge(
            'ephergent_worker_heartbeat_timestamp',
            'Unix timestamp of last worker heartbeat',
            ['worker_id'],
            registry=self.registry
        )

        self.worker_tasks_processed_total = Counter(
            'ephergent_worker_tasks_processed_total',
            'Total number of tasks processed by worker',
            ['worker_id', 'task_type'],
            registry=self.registry
        )

        self.worker_task_duration_seconds = Histogram(
            'ephergent_worker_task_duration_seconds',
            'Duration of worker task processing',
            ['task_type'],
            buckets=[1, 5, 10, 30, 60, 300, 600],
            registry=self.registry
        )

        # ====================================================================
        # Workflow-Specific Aggregated Metrics (Database-Driven)
        # ====================================================================

        self.stories_by_status = Gauge(
            'ephergent_stories_by_status',
            'Total number of stories by workflow status',
            ['status'],  # queued, story_generation, completed, failed, etc.
            registry=self.registry
        )

        self.stories_published_youtube = Gauge(
            'ephergent_stories_published_youtube',
            'Total number of stories published to YouTube',
            registry=self.registry
        )

        self.stories_published_ghost = Gauge(
            'ephergent_stories_published_ghost',
            'Total number of stories published to Ghost',
            ['ghost_status'],  # draft, published
            registry=self.registry
        )

        self.media_generated_total_count = Gauge(
            'ephergent_media_generated_total_count',
            'Total count of media items generated (cumulative from database)',
            ['media_type'],  # image, audio, video
            registry=self.registry
        )

        self.workflow_step_distribution = Gauge(
            'ephergent_workflow_step_distribution',
            'Number of stories currently at each workflow step',
            ['step'],
            registry=self.registry
        )

        self.average_workflow_duration_seconds = Gauge(
            'ephergent_average_workflow_duration_seconds',
            'Average time for completed stories from creation to completion',
            registry=self.registry
        )

        # ====================================================================
        # System Information
        # ====================================================================


        #
        # Phase 1.2: Retry and DLQ Metrics
        # ====================================================================

        self.retry_attempts_total = Counter(
            'ephergent_retry_attempts_total',
            'Total number of retry attempts made',
            ['step', 'error_type'],
            registry=self.registry
        )

        self.retry_success_total = Counter(
            'ephergent_retry_success_total',
            'Total number of successful retries (story completed after retry)',
            ['step'],
            registry=self.registry
        )

        self.retry_exhausted_total = Counter(
            'ephergent_retry_exhausted_total',
            'Total number of stories that exhausted all retries',
            ['step', 'error_type'],
            registry=self.registry
        )

        self.dlq_size = Gauge(
            'ephergent_dlq_size',
            'Current number of stories in Dead Letter Queue',
            ['status'],  # pending, investigating, resolved, archived
            registry=self.registry
        )

        self.dlq_by_error_type = Gauge(
            'ephergent_dlq_by_error_type',
            'Number of DLQ stories by error type',
            ['error_type'],  # TRANSIENT, RATE_LIMIT, CONFIGURATION, etc.
            registry=self.registry
        )

        self.dlq_entries_total = Counter(
            'ephergent_dlq_entries_total',
            'Total number of stories added to DLQ',
            ['error_type'],
            registry=self.registry
        )

        self.dlq_resolved_total = Counter(
            'ephergent_dlq_resolved_total',
            'Total number of DLQ entries resolved',
            registry=self.registry
        )

        self.retry_delay_seconds = Histogram(
            'ephergent_retry_delay_seconds',
            'Retry delay calculated for failed stories',
            ['error_type'],
            buckets=[10, 30, 60, 120, 300, 600, 1800, 3600],  # 10s to 1 hour
            registry=self.registry
        )

        # ====================================================================
        self.app_info = Info(
            'ephergent_app',
            'Application version and environment information',
            registry=self.registry
        )

    def init_app(self, app: Flask):
        """Initialize metrics service with Flask application.

        Args:
            app: Flask application instance
        """
        if self._initialized:
            logger.warning("MetricsService already initialized")
            return

        self.app = app

        # Import db to make it available for workflow metrics
        global db
        from ephergent_generator import db as app_db
        db = app_db

        # Set application info
        self.app_info.info({
            'version': '0.1.1',
            'environment': app.config.get('FLASK_ENV', 'development'),
            'python_version': '3.11+'
        })

        # Register request handlers for automatic HTTP metrics
        app.before_request(self._before_request)
        app.after_request(self._after_request)

        # Add metrics endpoint
        @app.route('/metrics')
        def metrics_endpoint():
            """Prometheus metrics endpoint.

            Before serving metrics, update workflow-specific database metrics
            to ensure they reflect current state.
            """
            try:
                # Update workflow metrics from database
                self.update_workflow_metrics()
                # Update DLQ metrics from database
                self.update_dlq_metrics()
            except Exception as e:
                logger.error(f"Error updating workflow metrics in /metrics endpoint: {str(e)}")

            return generate_latest(self.registry), 200, {'Content-Type': CONTENT_TYPE_LATEST}

        self._initialized = True
        logger.info("MetricsService initialized successfully")

    # ========================================================================
    # Request Tracking Hooks
    # ========================================================================

    def _before_request(self):
        """Track request start time before processing."""
        g.request_start_time = time.time()

        # Increment in-progress gauge
        endpoint = request.endpoint or 'unknown'
        method = request.method

        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).inc()

    def _after_request(self, response):
        """Track request metrics after processing."""
        if not hasattr(g, 'request_start_time'):
            return response

        duration = time.time() - g.request_start_time
        endpoint = request.endpoint or 'unknown'
        method = request.method
        status_code = response.status_code

        # Record request metrics
        self.http_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        self.http_request_duration_seconds.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

        # Decrement in-progress gauge
        self.http_requests_in_progress.labels(
            method=method,
            endpoint=endpoint
        ).dec()

        return response

    # ========================================================================
    # Business Metrics Recording Methods
    # ========================================================================

    def record_story_created(self, source: str = 'web_ui'):
        """Record a new story creation.

        Args:
            source: Source of story creation (web_ui, api, mcp_server)
        """
        self.stories_created_total.labels(source=source).inc()

    def record_workflow_step_completed(self, step: str, duration_seconds: float):
        """Record successful workflow step completion.

        Args:
            step: Workflow step name (e.g., 'story_generation', 'image_generation')
            duration_seconds: Time taken to complete the step
        """
        self.workflow_steps_completed_total.labels(step=step).inc()
        self.workflow_step_duration_seconds.labels(step=step).observe(duration_seconds)

    def record_workflow_step_failed(self, step: str, error_type: str):
        """Record workflow step failure.

        Args:
            step: Workflow step name
            error_type: Type of error (e.g., 'api_error', 'timeout', 'validation_error')
        """
        self.workflow_steps_failed_total.labels(step=step, error_type=error_type).inc()

    def record_story_completed(self, total_duration_seconds: float):
        """Record complete story processing.

        Args:
            total_duration_seconds: Total time from creation to completion
        """
        self.stories_completed_total.inc()
        self.story_processing_time_seconds.observe(total_duration_seconds)

    def update_queue_size(self, pending: int, processing: int, failed: int):
        """Update current queue size gauges.

        Args:
            pending: Number of stories waiting to be processed
            processing: Number of stories currently being processed
            failed: Number of stories in failed state
        """
        self.story_queue_size.labels(status='pending').set(pending)
        self.story_queue_size.labels(status='processing').set(processing)
        self.story_queue_size.labels(status='failed').set(failed)

    def record_image_generated(self, character: str):
        """Record image generation.

        Args:
            character: Character ID for which image was generated
        """
        self.images_generated_total.labels(character=character).inc()

    def record_audio_generated(self, voice_model: str):
        """Record audio generation.

        Args:
            voice_model: Voice model used for generation
        """
        self.audio_generated_total.labels(voice_model=voice_model).inc()

    def record_video_generated(self):
        """Record video generation."""
        self.videos_generated_total.inc()

    def record_media_error(self, media_type: str, error_type: str):
        """Record media generation error.

        Args:
            media_type: Type of media (image, audio, video)
            error_type: Error classification
        """
        self.media_generation_errors_total.labels(
            media_type=media_type,
            error_type=error_type
        ).inc()

    # ========================================================================
    # External Service Metrics
    # ========================================================================

    def record_api_request(self, service: str, endpoint: str, status_code: int,
                          duration_seconds: float):
        """Record external API request.

        Args:
            service: Service name (e.g., 'gemini', 'comfyui', 'youtube')
            endpoint: API endpoint called
            status_code: HTTP status code
            duration_seconds: Request duration
        """
        self.external_api_requests_total.labels(
            service=service,
            endpoint=endpoint,
            status_code=status_code
        ).inc()

        self.external_api_duration_seconds.labels(
            service=service,
            endpoint=endpoint
        ).observe(duration_seconds)

    def set_service_availability(self, service: str, is_available: bool):
        """Update service availability status.

        Args:
            service: Service name
            is_available: Whether service is available
        """
        self.external_service_available.labels(service=service).set(1 if is_available else 0)

    # ========================================================================
    # Database Metrics
    # ========================================================================

    def update_database_connections(self, active_connections: int):
        """Update active database connection count.

        Args:
            active_connections: Number of active connections
        """
        self.database_connections_active.set(active_connections)

    def record_database_query(self, query_type: str, duration_seconds: float):
        """Record database query execution.

        Args:
            query_type: Type of query (select, insert, update, delete)
            duration_seconds: Query duration
        """
        self.database_query_duration_seconds.labels(query_type=query_type).observe(duration_seconds)

    def record_database_error(self, error_type: str):
        """Record database error.

        Args:
            error_type: Error classification
        """
        self.database_errors_total.labels(error_type=error_type).inc()

    # ========================================================================
    # Worker Metrics
    # ========================================================================

    def record_worker_heartbeat(self, worker_id: str):
        """Record worker heartbeat.

        Args:
            worker_id: Unique worker identifier
        """
        self.worker_heartbeat_timestamp.labels(worker_id=worker_id).set(time.time())

    def record_worker_task(self, worker_id: str, task_type: str, duration_seconds: float):
        """Record worker task processing.

        Args:
            worker_id: Worker identifier
            task_type: Type of task processed
            duration_seconds: Processing duration
        """
        self.worker_tasks_processed_total.labels(
            worker_id=worker_id,
            task_type=task_type
        ).inc()

        self.worker_task_duration_seconds.labels(task_type=task_type).observe(duration_seconds)

    # ========================================================================
    # Workflow-Specific Database Metrics
    # ========================================================================

    def update_workflow_metrics(self):
        """Update all workflow-specific metrics from database state.

        This method queries the database to populate gauges with current workflow statistics.
        Should be called periodically (e.g., every minute) or after significant workflow events.

        Note:
            Requires Flask application context to access database.
        """
        try:
            from ephergent_generator.models import Story, WorkflowStep
            from sqlalchemy import func
            from datetime import datetime

            # Update stories by status - count for each workflow step
            status_counts = db.session.query(
                Story.current_step,
                func.count(Story.id)
            ).group_by(Story.current_step).all()

            # Reset all step counts to 0 first
            for step in WorkflowStep:
                self.stories_by_status.labels(status=step.value).set(0)
                self.workflow_step_distribution.labels(step=step.value).set(0)

            # Set actual counts
            for step, count in status_counts:
                if step:
                    self.stories_by_status.labels(status=step.value).set(count)
                    self.workflow_step_distribution.labels(step=step.value).set(count)

            # Update YouTube publishing metrics
            youtube_published = db.session.query(func.count(Story.id)).filter(
                Story.youtube_video_id.isnot(None)
            ).scalar() or 0
            self.stories_published_youtube.set(youtube_published)

            # Update Ghost publishing metrics
            ghost_published = db.session.query(func.count(Story.id)).filter(
                Story.ghost_post_id.isnot(None),
                Story.ghost_status == 'published'
            ).scalar() or 0
            self.stories_published_ghost.labels(ghost_status='published').set(ghost_published)

            ghost_draft = db.session.query(func.count(Story.id)).filter(
                Story.ghost_post_id.isnot(None),
                Story.ghost_status == 'draft'
            ).scalar() or 0
            self.stories_published_ghost.labels(ghost_status='draft').set(ghost_draft)

            # Update media generation counts (cumulative totals from database)
            # Images: count stories with non-null image_paths
            images_count = db.session.query(func.count(Story.id)).filter(
                Story.image_paths.isnot(None),
                Story.image_paths != 'null',
                Story.image_paths != '[]'
            ).scalar() or 0
            self.media_generated_total_count.labels(media_type='image').set(images_count)

            # Audio: count stories with non-null audio_path
            audio_count = db.session.query(func.count(Story.id)).filter(
                Story.audio_path.isnot(None),
                Story.audio_path != ''
            ).scalar() or 0
            self.media_generated_total_count.labels(media_type='audio').set(audio_count)

            # Video: count stories with non-null video_path
            video_count = db.session.query(func.count(Story.id)).filter(
                Story.video_path.isnot(None),
                Story.video_path != ''
            ).scalar() or 0
            self.media_generated_total_count.labels(media_type='video').set(video_count)

            # Calculate average workflow duration for completed stories
            completed_stories = db.session.query(
                Story.created_at,
                Story.completed_at
            ).filter(
                Story.current_step == WorkflowStep.COMPLETED,
                Story.completed_at.isnot(None)
            ).all()

            if completed_stories:
                total_duration = 0
                count = 0
                for created_at, completed_at in completed_stories:
                    if created_at and completed_at:
                        duration = (completed_at - created_at).total_seconds()
                        total_duration += duration
                        count += 1

                if count > 0:
                    average_duration = total_duration / count
                    self.average_workflow_duration_seconds.set(average_duration)
                else:
                    self.average_workflow_duration_seconds.set(0)
            else:
                self.average_workflow_duration_seconds.set(0)

            logger.debug("Workflow metrics updated successfully")

        except Exception as e:
            logger.error(f"Error updating workflow metrics: {str(e)}", exc_info=True)

    def update_story_status_metrics(self, story):
        """Update metrics for a specific story status change.

        This is a convenience method to update relevant metrics when a story
        changes state. More efficient than full update_workflow_metrics().

        Args:
            story: Story model instance that has changed
        """
        try:
            # Update the workflow step distribution
            self.update_workflow_metrics()  # For now, do full update

        except Exception as e:
            logger.error(f"Error updating story status metrics: {str(e)}", exc_info=True)

    # ========================================================================
    # Decorators
    # ========================================================================

    def track_time(self, metric_name: str, **labels):
        """Decorator to track function execution time.

        Args:
            metric_name: Name of the metric to record (without '_seconds' suffix)
            **labels: Metric labels

        Usage:
            @metrics_service.track_time('workflow_step_duration', step='image_generation')
            def generate_image():
                ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start_time

                    # Record duration based on metric name
                    if metric_name == 'workflow_step_duration':
                        self.workflow_step_duration_seconds.labels(**labels).observe(duration)
                    elif metric_name == 'external_api_duration':
                        self.external_api_duration_seconds.labels(**labels).observe(duration)
                    elif metric_name == 'database_query':
                        self.database_query_duration_seconds.labels(**labels).observe(duration)

            return wrapper
        return decorator


# Global singleton instance
metrics_service = MetricsService()


# Convenience decorator for external use
def track_workflow_step(step_name: str):
    """Decorator to automatically track workflow step metrics.

    Args:
        step_name: Name of the workflow step

    Usage:
        @track_workflow_step('image_generation')
        def generate_images(story):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics_service.record_workflow_step_completed(step_name, duration)
                return result
            except Exception as e:
                error_type = type(e).__name__
                metrics_service.record_workflow_step_failed(step_name, error_type)
                raise
        return wrapper
    return decorator

    # ========================================================================
    # Phase 1.2: Retry and DLQ Metrics Recording Methods
    # ========================================================================

    def record_retry_attempt(self, step: str, error_type: str, delay_seconds: float):
        """Record a retry attempt for a failed workflow step.

        Args:
            step: Workflow step that failed
            error_type: Classified error type
            delay_seconds: Calculated retry delay
        """
        self.retry_attempts_total.labels(step=step, error_type=error_type).inc()
        self.retry_delay_seconds.labels(error_type=error_type).observe(delay_seconds)

    def record_retry_success(self, step: str):
        """Record successful retry (story completed after retry).

        Args:
            step: Workflow step that was retried successfully
        """
        self.retry_success_total.labels(step=step).inc()

    def record_retry_exhausted(self, step: str, error_type: str):
        """Record story that exhausted all retries.

        Args:
            step: Workflow step where retries were exhausted
            error_type: Final error type
        """
        self.retry_exhausted_total.labels(step=step, error_type=error_type).inc()

    def record_dlq_entry(self, error_type: str):
        """Record story added to Dead Letter Queue.

        Args:
            error_type: Classified error type
        """
        self.dlq_entries_total.labels(error_type=error_type).inc()

    def record_dlq_resolved(self):
        """Record DLQ entry marked as resolved."""
        self.dlq_resolved_total.inc()

    def update_dlq_metrics(self):
        """Update DLQ gauge metrics from database state.

        Should be called periodically or after DLQ changes.
        """
        try:
            from ephergent_generator.models import StoryFailure
            from sqlalchemy import func

            # Update DLQ size by status
            dlq_by_status = db.session.query(
                StoryFailure.dlq_status,
                func.count(StoryFailure.id)
            ).group_by(StoryFailure.dlq_status).all()

            # Reset all status gauges
            for status in ['pending', 'investigating', 'resolved', 'archived']:
                self.dlq_size.labels(status=status).set(0)

            # Set actual counts
            for status, count in dlq_by_status:
                self.dlq_size.labels(status=status).set(count)

            # Update DLQ by error type
            dlq_by_error = db.session.query(
                StoryFailure.error_type,
                func.count(StoryFailure.id)
            ).filter(
                StoryFailure.dlq_status.in_(['pending', 'investigating'])
            ).group_by(StoryFailure.error_type).all()

            # Reset all error type gauges
            for error_type in ['TRANSIENT', 'RATE_LIMIT', 'CONFIGURATION', 
                              'VALIDATION', 'RESOURCE', 'PERMANENT']:
                self.dlq_by_error_type.labels(error_type=error_type).set(0)

            # Set actual counts
            for error_type, count in dlq_by_error:
                if error_type:
                    self.dlq_by_error_type.labels(error_type=error_type).set(count)

            logger.debug("DLQ metrics updated successfully")

        except Exception as e:
            logger.error(f"Error updating DLQ metrics: {str(e)}", exc_info=True)
