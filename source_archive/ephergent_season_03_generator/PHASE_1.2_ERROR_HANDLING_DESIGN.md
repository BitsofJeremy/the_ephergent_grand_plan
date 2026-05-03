# Phase 1.2: Error Handling & Recovery System
## Technical Design Document

**Version:** 1.0
**Date:** 2025-10-09
**Author:** A.R.C.H.I.E. (AI Technical Lead)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Architecture Overview](#architecture-overview)
3. [Database Schema Design](#database-schema-design)
4. [Error Classification System](#error-classification-system)
5. [Retry Mechanism Design](#retry-mechanism-design)
6. [Dead Letter Queue (DLQ) Implementation](#dead-letter-queue-dlq-implementation)
7. [Admin UI Components](#admin-ui-components)
8. [Metrics Integration](#metrics-integration)
9. [Service Layer Changes](#service-layer-changes)
10. [Migration Strategy](#migration-strategy)
11. [Implementation Plan](#implementation-plan)
12. [Testing Strategy](#testing-strategy)
13. [Rollout Plan](#rollout-plan)

---

## 1. Executive Summary

### 1.1 Current State

The Ephergent story generation workflow currently lacks robust error handling:

- **Immediate Failure**: Stories fail permanently on first error
- **No Retry Logic**: Transient errors (API timeouts, rate limits) cause permanent failures
- **No Error Classification**: All errors treated equally
- **Limited Observability**: No retry metrics or DLQ tracking
- **Manual Recovery**: Failed stories require complete regeneration from scratch

### 1.2 Goals

Implement a production-grade error handling system with:

1. **Automatic Retry Logic** with exponential backoff and error-specific strategies
2. **Error Classification** to distinguish transient vs. permanent failures
3. **Dead Letter Queue** for permanently failed stories requiring manual intervention
4. **Partial Regeneration** to resume from specific workflow steps
5. **Enhanced Metrics** for retry tracking and failure analysis
6. **Admin UI** for DLQ management and manual recovery

### 1.3 Success Metrics

- **Automatic Recovery Rate**: 70%+ of transient failures auto-recover
- **Mean Time to Recovery**: < 30 minutes for transient errors
- **DLQ Size**: < 5% of total stories
- **Manual Intervention Rate**: < 10% of failures require admin action
- **False Positive Rate**: < 1% of stories incorrectly marked as permanent failures

---

## 2. Architecture Overview

### 2.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Story Workflow Pipeline                     │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
         ┌─────────────────────────────────────┐
         │   StoryWorkflowService              │
         │   (with @retry_workflow_step)       │
         └─────────────────────────────────────┘
                    │                    │
        ┌───────────┴──────────┐        │
        │                      │        │
        ▼                      ▼        ▼
┌──────────────┐      ┌──────────────┐  ┌──────────────┐
│ RetryService │      │ErrorClassify │  │MetricsService│
│              │      │              │  │              │
│ - Backoff    │      │ - Classify   │  │ - Track      │
│ - Max Retries│      │ - Strategy   │  │   Retries    │
│ - Scheduling │      │ - DLQ Check  │  │ - DLQ Size   │
└──────────────┘      └──────────────┘  └──────────────┘
        │                      │
        ▼                      ▼
┌──────────────────────────────────────┐
│          Story Model                 │
│  - retry_count                       │
│  - last_retry_at                     │
│  - next_retry_at                     │
│  - error_classification              │
│  - retry_history (JSON)              │
└──────────────────────────────────────┘
                    │
                    ▼ (on max retries or permanent error)
┌──────────────────────────────────────┐
│       StoryFailure (DLQ)             │
│  - story_id                          │
│  - failed_at_step                    │
│  - error_type                        │
│  - retry_count                       │
│  - can_retry                         │
│  - resolved_at                       │
└──────────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────┐
│         Admin DLQ UI                 │
│  - View failures                     │
│  - Manual retry                      │
│  - Bulk operations                   │
│  - Analytics                         │
└──────────────────────────────────────┘
```

### 2.2 Request Flow with Retry Logic

```
Story Processing Request
    │
    ▼
┌────────────────────────┐
│ Worker picks story     │
│ from queue             │
└────────────────────────┘
    │
    ▼
┌────────────────────────────────────────────────┐
│ Execute workflow step                          │
│ (wrapped with @retry_workflow_step decorator)  │
└────────────────────────────────────────────────┘
    │
    ├─ SUCCESS ──────────────────┐
    │                            │
    └─ FAILURE                   │
        │                        │
        ▼                        │
    ┌─────────────────────┐     │
    │ Classify Error      │     │
    │ (ErrorClassifier)   │     │
    └─────────────────────┘     │
        │                        │
        ├─ TRANSIENT              │
        │   │                     │
        │   ▼                     │
        │ Check retry_count       │
        │   │                     │
        │   ├─ < MAX_RETRIES      │
        │   │   │                 │
        │   │   ▼                 │
        │   │ Calculate backoff   │
        │   │ Set next_retry_at   │
        │   │ Increment retry_count
        │   │ Release to queue    │
        │   │ Record metrics      │
        │   │                     │
        │   └─ >= MAX_RETRIES     │
        │       │                 │
        │       ▼                 │
        │   Send to DLQ           │
        │   Mark as FAILED        │
        │   Record metrics        │
        │                         │
        ├─ RATE_LIMIT             │
        │   │                     │
        │   ▼                     │
        │ Longer backoff (30min)  │
        │ (same retry logic)      │
        │                         │
        └─ PERMANENT              │
            │                     │
            ▼                     │
        Send to DLQ immediately   │
        Mark as FAILED            │
        Record metrics            │
                                  │
                                  ▼
                            Continue to
                            next step
```

---

## 3. Database Schema Design

### 3.1 Story Model Enhancements

**New Fields:**

```python
# Retry Management Fields
retry_count = db.Column(db.Integer, default=0, nullable=False)
max_retries = db.Column(db.Integer, default=5, nullable=False)  # Per-story override
last_retry_at = db.Column(db.DateTime, nullable=True)
next_retry_at = db.Column(db.DateTime, nullable=True)

# Error Classification
error_classification = db.Column(db.String(50), nullable=True)
# Values: TRANSIENT, RATE_LIMIT, CONFIGURATION, VALIDATION, RESOURCE, PERMANENT

# Retry History (JSON)
retry_history = db.Column(db.Text, nullable=True)
# Structure: [
#   {
#     "attempt": 1,
#     "timestamp": "2025-10-09T10:30:00Z",
#     "step": "image_generation",
#     "error_type": "APITimeoutError",
#     "error_classification": "TRANSIENT",
#     "backoff_seconds": 60
#   },
#   ...
# ]
```

**New Methods:**

```python
def increment_retry(self, error_classification, backoff_seconds):
    """Increment retry counter and schedule next retry."""
    self.retry_count += 1
    self.last_retry_at = datetime.utcnow()
    self.next_retry_at = datetime.utcnow() + timedelta(seconds=backoff_seconds)
    self.error_classification = error_classification

    # Append to retry history
    history = self.get_retry_history()
    history.append({
        'attempt': self.retry_count,
        'timestamp': self.last_retry_at.isoformat(),
        'step': self.current_step.value,
        'error_message': self.error_message,
        'error_classification': error_classification,
        'backoff_seconds': backoff_seconds
    })
    self.set_retry_history(history)

def can_retry(self):
    """Check if story can be retried based on retry count and classification."""
    if self.error_classification == 'PERMANENT':
        return False
    return self.retry_count < self.max_retries

def get_retry_history(self):
    """Parse retry_history JSON field."""
    if self.retry_history:
        try:
            return json.loads(self.retry_history)
        except json.JSONDecodeError:
            return []
    return []

def set_retry_history(self, history):
    """Set retry_history as JSON."""
    self.retry_history = json.dumps(history) if history else None

def reset_retry_state(self):
    """Reset retry counters for manual retry."""
    self.retry_count = 0
    self.last_retry_at = None
    self.next_retry_at = None
    self.error_classification = None
    self.retry_history = None
    self.error_message = None

def regenerate_from_step(self, from_step: WorkflowStep):
    """Reset workflow from specific step, preserving prior work."""
    # Reset current step
    self.current_step = from_step

    # Clear error state
    self.reset_retry_state()

    # Clear content/media from this step forward
    step_order = [
        WorkflowStep.QUEUED,
        WorkflowStep.STORY_GENERATION,
        WorkflowStep.TITLE_GENERATION,
        WorkflowStep.IMAGE_GENERATION,
        WorkflowStep.AUDIO_GENERATION,
        WorkflowStep.VIDEO_GENERATION,
        WorkflowStep.YOUTUBE_UPLOAD,
        WorkflowStep.GHOST_PUBLISHING
    ]

    from_index = step_order.index(from_step)

    # Clear content based on step
    if from_index <= step_order.index(WorkflowStep.STORY_GENERATION):
        self.content = None
        self.word_count = None

    if from_index <= step_order.index(WorkflowStep.TITLE_GENERATION):
        self.title = None

    if from_index <= step_order.index(WorkflowStep.IMAGE_GENERATION):
        self.image_paths = None
        self.image_prompts = None

    if from_index <= step_order.index(WorkflowStep.AUDIO_GENERATION):
        self.audio_path = None

    if from_index <= step_order.index(WorkflowStep.VIDEO_GENERATION):
        self.video_path = None

    if from_index <= step_order.index(WorkflowStep.YOUTUBE_UPLOAD):
        self.youtube_video_id = None
        self.youtube_url = None

    if from_index <= step_order.index(WorkflowStep.GHOST_PUBLISHING):
        self.ghost_post_id = None
        self.ghost_post_url = None
        self.ghost_status = 'draft'

    self.updated_at = datetime.utcnow()
```

### 3.2 StoryFailure Model (Dead Letter Queue)

**New Model:**

```python
class StoryFailure(db.Model):
    """Dead Letter Queue for permanently failed stories.

    Tracks stories that have exhausted retries or encountered permanent
    errors requiring manual intervention.
    """
    __tablename__ = 'story_failures'

    id = db.Column(db.Integer, primary_key=True)
    story_id = db.Column(db.Integer, db.ForeignKey('stories.id'), nullable=False, unique=True)

    # Failure Details
    failed_at_step = db.Column(db.Enum(WorkflowStep), nullable=False)
    error_type = db.Column(db.String(100), nullable=False)  # Exception class name
    error_classification = db.Column(db.String(50), nullable=False)  # ErrorClassification enum
    error_message = db.Column(db.Text, nullable=False)
    error_traceback = db.Column(db.Text, nullable=True)  # Full stack trace

    # Retry Context
    retry_count = db.Column(db.Integer, nullable=False)  # How many retries before giving up
    retry_history = db.Column(db.Text, nullable=True)  # JSON history from Story

    # Recovery Metadata
    failure_reason = db.Column(db.Text, nullable=True)  # User-friendly explanation
    can_retry = db.Column(db.Boolean, default=True, nullable=False)  # Whether manual retry possible
    resolution_notes = db.Column(db.Text, nullable=True)  # Admin notes on resolution

    # Status Tracking
    status = db.Column(db.String(20), default='pending', nullable=False)
    # Values: pending, investigating, resolved, archived

    # Timestamps
    failed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    # Audit
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    story = db.relationship('Story', backref=db.backref('failure_record', uselist=False))
    resolver = db.relationship('User', backref='resolved_failures')

    # Indexes
    __table_args__ = (
        db.Index('idx_failure_status', 'status'),
        db.Index('idx_failure_step', 'failed_at_step'),
        db.Index('idx_failure_classification', 'error_classification'),
        db.Index('idx_failure_date', 'failed_at'),
    )

    def __repr__(self):
        return f'<StoryFailure story_id={self.story_id} step={self.failed_at_step.value}>'

    def get_retry_history(self):
        """Parse retry_history JSON field."""
        if self.retry_history:
            try:
                return json.loads(self.retry_history)
            except json.JSONDecodeError:
                return []
        return []

    def mark_resolved(self, user_id, notes=None):
        """Mark failure as resolved."""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = user_id
        if notes:
            self.resolution_notes = notes

    def archive(self):
        """Archive failure record."""
        self.status = 'archived'
        self.archived_at = datetime.utcnow()

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            'id': self.id,
            'story_id': self.story_id,
            'failed_at_step': self.failed_at_step.value,
            'error_type': self.error_type,
            'error_classification': self.error_classification,
            'error_message': self.error_message,
            'retry_count': self.retry_count,
            'retry_history': self.get_retry_history(),
            'failure_reason': self.failure_reason,
            'can_retry': self.can_retry,
            'status': self.status,
            'resolution_notes': self.resolution_notes,
            'failed_at': self.failed_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'story': self.story.to_dict() if self.story else None
        }
```

### 3.3 Migration Script

**File:** `migrations/versions/XXXX_add_retry_and_dlq.py`

```python
"""Add retry mechanism and dead letter queue support

Revision ID: XXXX
Revises: YYYY
Create Date: 2025-10-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = 'XXXX'
down_revision = 'YYYY'
branch_labels = None
depends_on = None


def upgrade():
    # Add retry fields to stories table
    op.add_column('stories', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('stories', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='5'))
    op.add_column('stories', sa.Column('last_retry_at', sa.DateTime(), nullable=True))
    op.add_column('stories', sa.Column('next_retry_at', sa.DateTime(), nullable=True))
    op.add_column('stories', sa.Column('error_classification', sa.String(50), nullable=True))
    op.add_column('stories', sa.Column('retry_history', sa.Text(), nullable=True))

    # Create story_failures table
    op.create_table(
        'story_failures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('failed_at_step', sa.Enum(
            'QUEUED', 'STORY_GENERATION', 'TITLE_GENERATION', 'IMAGE_GENERATION',
            'AUDIO_GENERATION', 'VIDEO_GENERATION', 'YOUTUBE_UPLOAD',
            'GHOST_PUBLISHING', 'COMPLETED', 'FAILED',
            name='workflowstep'
        ), nullable=False),
        sa.Column('error_type', sa.String(100), nullable=False),
        sa.Column('error_classification', sa.String(50), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('error_traceback', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False),
        sa.Column('retry_history', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('can_retry', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('failed_at', sa.DateTime(), nullable=False),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('story_id')
    )

    # Create indexes
    op.create_index('idx_failure_status', 'story_failures', ['status'])
    op.create_index('idx_failure_step', 'story_failures', ['failed_at_step'])
    op.create_index('idx_failure_classification', 'story_failures', ['error_classification'])
    op.create_index('idx_failure_date', 'story_failures', ['failed_at'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_failure_date', table_name='story_failures')
    op.drop_index('idx_failure_classification', table_name='story_failures')
    op.drop_index('idx_failure_step', table_name='story_failures')
    op.drop_index('idx_failure_status', table_name='story_failures')

    # Drop table
    op.drop_table('story_failures')

    # Remove columns from stories
    op.drop_column('stories', 'retry_history')
    op.drop_column('stories', 'error_classification')
    op.drop_column('stories', 'next_retry_at')
    op.drop_column('stories', 'last_retry_at')
    op.drop_column('stories', 'max_retries')
    op.drop_column('stories', 'retry_count')
```

---

## 4. Error Classification System

### 4.1 ErrorClassification Enum

**File:** `ephergent_generator/utils/error_classification.py`

```python
from enum import Enum
from typing import Type, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorClassification(Enum):
    """Classification of errors for retry strategy determination."""

    TRANSIENT = "transient"          # Network timeouts, temporary API issues
    RATE_LIMIT = "rate_limit"        # API rate limiting
    CONFIGURATION = "configuration"   # Missing API keys, bad config
    VALIDATION = "validation"         # Invalid data, missing required fields
    RESOURCE = "resource"             # Disk space, memory issues
    PERMANENT = "permanent"           # Unrecoverable errors


class ErrorClassifier:
    """Classifies exceptions into error categories for retry strategy."""

    # Mapping of exception types/patterns to classifications
    ERROR_PATTERNS = {
        # Transient errors - safe to retry
        'TimeoutError': ErrorClassification.TRANSIENT,
        'ConnectionError': ErrorClassification.TRANSIENT,
        'ConnectionResetError': ErrorClassification.TRANSIENT,
        'BrokenPipeError': ErrorClassification.TRANSIENT,
        'requests.exceptions.Timeout': ErrorClassification.TRANSIENT,
        'requests.exceptions.ConnectionError': ErrorClassification.TRANSIENT,
        'urllib3.exceptions.ReadTimeoutError': ErrorClassification.TRANSIENT,
        'socket.timeout': ErrorClassification.TRANSIENT,
        'httpx.TimeoutException': ErrorClassification.TRANSIENT,
        'httpx.ConnectTimeout': ErrorClassification.TRANSIENT,

        # Rate limiting - retry with longer backoff
        'HTTPError_429': ErrorClassification.RATE_LIMIT,
        'RateLimitError': ErrorClassification.RATE_LIMIT,
        'TooManyRequests': ErrorClassification.RATE_LIMIT,
        'QuotaExceededError': ErrorClassification.RATE_LIMIT,

        # Configuration errors - require human intervention
        'KeyError': ErrorClassification.CONFIGURATION,
        'AttributeError': ErrorClassification.CONFIGURATION,
        'ImportError': ErrorClassification.CONFIGURATION,
        'ModuleNotFoundError': ErrorClassification.CONFIGURATION,

        # Validation errors - data issue, don't retry
        'ValueError': ErrorClassification.VALIDATION,
        'TypeError': ErrorClassification.VALIDATION,
        'json.JSONDecodeError': ErrorClassification.VALIDATION,
        'ValidationError': ErrorClassification.VALIDATION,

        # Resource errors - might resolve with retry
        'OSError': ErrorClassification.RESOURCE,
        'IOError': ErrorClassification.RESOURCE,
        'MemoryError': ErrorClassification.RESOURCE,
        'DiskError': ErrorClassification.RESOURCE,
    }

    # Message patterns for more specific classification
    MESSAGE_PATTERNS = {
        'api key': ErrorClassification.CONFIGURATION,
        'authentication': ErrorClassification.CONFIGURATION,
        'unauthorized': ErrorClassification.CONFIGURATION,
        'forbidden': ErrorClassification.CONFIGURATION,
        'rate limit': ErrorClassification.RATE_LIMIT,
        'quota exceeded': ErrorClassification.RATE_LIMIT,
        'too many requests': ErrorClassification.RATE_LIMIT,
        'timeout': ErrorClassification.TRANSIENT,
        'connection': ErrorClassification.TRANSIENT,
        'network': ErrorClassification.TRANSIENT,
        'disk full': ErrorClassification.RESOURCE,
        'out of memory': ErrorClassification.RESOURCE,
    }

    @classmethod
    def classify(cls, exception: Exception) -> ErrorClassification:
        """Classify an exception into an error category.

        Args:
            exception: The exception to classify

        Returns:
            ErrorClassification enum value
        """
        exc_type = type(exception).__name__
        exc_module = type(exception).__module__
        exc_message = str(exception).lower()

        # Check exact type match
        full_type = f"{exc_module}.{exc_type}" if exc_module != 'builtins' else exc_type

        if full_type in cls.ERROR_PATTERNS:
            classification = cls.ERROR_PATTERNS[full_type]
            logger.debug(f"Classified {full_type} as {classification.value}")
            return classification

        # Check simple type name
        if exc_type in cls.ERROR_PATTERNS:
            classification = cls.ERROR_PATTERNS[exc_type]
            logger.debug(f"Classified {exc_type} as {classification.value}")
            return classification

        # Check for HTTP status codes in message
        if hasattr(exception, 'response'):
            status_code = getattr(exception.response, 'status_code', None)
            if status_code == 429:
                logger.debug(f"Classified HTTP 429 as RATE_LIMIT")
                return ErrorClassification.RATE_LIMIT
            elif status_code in [500, 502, 503, 504]:
                logger.debug(f"Classified HTTP {status_code} as TRANSIENT")
                return ErrorClassification.TRANSIENT
            elif status_code in [401, 403]:
                logger.debug(f"Classified HTTP {status_code} as CONFIGURATION")
                return ErrorClassification.CONFIGURATION

        # Check message patterns
        for pattern, classification in cls.MESSAGE_PATTERNS.items():
            if pattern in exc_message:
                logger.debug(f"Classified by message pattern '{pattern}' as {classification.value}")
                return classification

        # Default to PERMANENT if we can't classify
        logger.warning(f"Could not classify {full_type}: {exc_message}. Defaulting to PERMANENT")
        return ErrorClassification.PERMANENT

    @classmethod
    def should_retry(cls, classification: ErrorClassification) -> bool:
        """Determine if an error classification should be retried.

        Args:
            classification: The error classification

        Returns:
            True if the error should be retried, False otherwise
        """
        return classification in [
            ErrorClassification.TRANSIENT,
            ErrorClassification.RATE_LIMIT,
            ErrorClassification.RESOURCE
        ]

    @classmethod
    def get_retry_strategy(cls, classification: ErrorClassification) -> dict:
        """Get retry strategy for an error classification.

        Args:
            classification: The error classification

        Returns:
            Dictionary with retry strategy parameters
        """
        strategies = {
            ErrorClassification.TRANSIENT: {
                'base_delay': 60,      # 1 minute base
                'max_delay': 1800,     # 30 minutes max
                'exponential': True,
                'jitter': True
            },
            ErrorClassification.RATE_LIMIT: {
                'base_delay': 300,     # 5 minutes base
                'max_delay': 3600,     # 1 hour max
                'exponential': True,
                'jitter': False
            },
            ErrorClassification.RESOURCE: {
                'base_delay': 120,     # 2 minutes base
                'max_delay': 900,      # 15 minutes max
                'exponential': True,
                'jitter': True
            },
            ErrorClassification.CONFIGURATION: {
                'base_delay': 0,
                'max_delay': 0,
                'exponential': False,
                'jitter': False,
                'should_retry': False
            },
            ErrorClassification.VALIDATION: {
                'base_delay': 0,
                'max_delay': 0,
                'exponential': False,
                'jitter': False,
                'should_retry': False
            },
            ErrorClassification.PERMANENT: {
                'base_delay': 0,
                'max_delay': 0,
                'exponential': False,
                'jitter': False,
                'should_retry': False
            }
        }

        return strategies.get(classification, strategies[ErrorClassification.PERMANENT])
```

### 4.2 Retry Configuration in SystemConfig

**Default Configuration Values:**

```python
# To be added to database via migration data or admin UI
RETRY_CONFIG_DEFAULTS = {
    'retry.max_attempts': {
        'value': '5',
        'type': 'int',
        'category': 'retry',
        'description': 'Maximum retry attempts per workflow step',
        'is_public': True
    },
    'retry.transient.base_delay_seconds': {
        'value': '60',
        'type': 'int',
        'category': 'retry',
        'description': 'Base delay in seconds for transient errors',
        'is_public': True
    },
    'retry.rate_limit.base_delay_seconds': {
        'value': '300',
        'type': 'int',
        'category': 'retry',
        'description': 'Base delay in seconds for rate limit errors',
        'is_public': True
    },
    'retry.exponential_backoff_multiplier': {
        'value': '2.0',
        'type': 'float',
        'category': 'retry',
        'description': 'Exponential backoff multiplier',
        'is_public': True
    },
    'retry.enable_jitter': {
        'value': 'true',
        'type': 'bool',
        'category': 'retry',
        'description': 'Add random jitter to retry delays',
        'is_public': True
    }
}
```

---

## 5. Retry Mechanism Design

### 5.1 RetryService

**File:** `ephergent_generator/services/retry_service.py`

```python
from datetime import datetime, timedelta
from typing import Optional, Callable
import logging
import random
import traceback
from functools import wraps

from ephergent_generator import db
from ephergent_generator.models import Story, StoryFailure, WorkflowStep, SystemConfig
from ephergent_generator.utils.error_classification import ErrorClassifier, ErrorClassification
from ephergent_generator.utils.metrics import metrics_service

logger = logging.getLogger(__name__)


class RetryService:
    """Service for managing retry logic and exponential backoff."""

    def __init__(self):
        """Initialize retry service with configuration."""
        self.max_retries = SystemConfig.get_config('retry.max_attempts', default=5)
        self.base_delays = {
            ErrorClassification.TRANSIENT: SystemConfig.get_config(
                'retry.transient.base_delay_seconds', default=60
            ),
            ErrorClassification.RATE_LIMIT: SystemConfig.get_config(
                'retry.rate_limit.base_delay_seconds', default=300
            ),
            ErrorClassification.RESOURCE: SystemConfig.get_config(
                'retry.resource.base_delay_seconds', default=120
            )
        }
        self.backoff_multiplier = SystemConfig.get_config(
            'retry.exponential_backoff_multiplier', default=2.0
        )
        self.enable_jitter = SystemConfig.get_config(
            'retry.enable_jitter', default=True
        )

    def calculate_backoff(
        self,
        attempt: int,
        classification: ErrorClassification
    ) -> int:
        """Calculate backoff delay in seconds using exponential backoff.

        Args:
            attempt: Current retry attempt number (0-indexed)
            classification: Error classification

        Returns:
            Delay in seconds before next retry
        """
        strategy = ErrorClassifier.get_retry_strategy(classification)

        if not strategy.get('should_retry', True):
            return 0

        base_delay = strategy['base_delay']
        max_delay = strategy['max_delay']

        if strategy.get('exponential', False):
            # Exponential backoff: base * (multiplier ^ attempt)
            delay = base_delay * (self.backoff_multiplier ** attempt)
        else:
            # Linear backoff
            delay = base_delay * (attempt + 1)

        # Cap at max delay
        delay = min(delay, max_delay)

        # Add jitter if enabled (±20%)
        if strategy.get('jitter', False) and self.enable_jitter:
            jitter_range = delay * 0.2
            delay = delay + random.uniform(-jitter_range, jitter_range)

        return int(max(0, delay))

    def handle_failure(
        self,
        story: Story,
        exception: Exception,
        step: WorkflowStep
    ) -> bool:
        """Handle a workflow step failure with retry logic.

        Args:
            story: The story that failed
            exception: The exception that occurred
            step: The workflow step that failed

        Returns:
            True if story should be retried, False if sent to DLQ
        """
        # Classify the error
        classification = ErrorClassifier.classify(exception)

        # Store error details
        error_type = type(exception).__name__
        error_message = str(exception)
        error_traceback = traceback.format_exc()

        logger.info(
            f"Story {story.id} failed at {step.value} with {error_type} "
            f"(classified as {classification.value})"
        )

        # Check if we should retry
        if not ErrorClassifier.should_retry(classification):
            logger.warning(
                f"Story {story.id}: {classification.value} error, sending to DLQ"
            )
            self._send_to_dlq(
                story, step, exception, classification,
                error_type, error_message, error_traceback
            )
            metrics_service.record_workflow_step_failed(
                step.value,
                f"{classification.value}_no_retry"
            )
            return False

        # Check retry count
        if story.retry_count >= self.max_retries:
            logger.warning(
                f"Story {story.id} exceeded max retries ({self.max_retries}), "
                f"sending to DLQ"
            )
            self._send_to_dlq(
                story, step, exception, classification,
                error_type, error_message, error_traceback
            )
            metrics_service.record_workflow_step_failed(
                step.value,
                f"{classification.value}_retry_exhausted"
            )
            # Record retry exhaustion metric
            metrics_service.retry_exhausted_total.labels(
                step=step.value,
                error_classification=classification.value
            ).inc()
            return False

        # Calculate backoff and schedule retry
        backoff_seconds = self.calculate_backoff(story.retry_count, classification)

        # Update story with retry information
        story.increment_retry(classification.value, backoff_seconds)
        story.error_message = f"{error_type}: {error_message}"

        # Keep story in current step (don't advance to FAILED)
        # Worker will pick it up again when next_retry_at is reached

        logger.info(
            f"Story {story.id} retry scheduled: attempt {story.retry_count}/{self.max_retries}, "
            f"next retry in {backoff_seconds}s ({classification.value})"
        )

        # Record metrics
        metrics_service.retry_attempts_total.labels(
            step=step.value,
            error_classification=classification.value
        ).inc()

        return True

    def _send_to_dlq(
        self,
        story: Story,
        step: WorkflowStep,
        exception: Exception,
        classification: ErrorClassification,
        error_type: str,
        error_message: str,
        error_traceback: str
    ):
        """Send a story to the Dead Letter Queue.

        Args:
            story: The failed story
            step: The step that failed
            exception: The exception
            classification: Error classification
            error_type: Exception type name
            error_message: Exception message
            error_traceback: Full traceback
        """
        # Create DLQ entry
        failure = StoryFailure(
            story_id=story.id,
            failed_at_step=step,
            error_type=error_type,
            error_classification=classification.value,
            error_message=error_message,
            error_traceback=error_traceback,
            retry_count=story.retry_count,
            retry_history=story.retry_history,
            failure_reason=self._generate_failure_reason(classification, error_message),
            can_retry=(classification != ErrorClassification.PERMANENT)
        )

        db.session.add(failure)

        # Mark story as FAILED
        story.current_step = WorkflowStep.FAILED
        story.error_message = f"{error_type}: {error_message}"
        story.error_classification = classification.value

        logger.error(
            f"Story {story.id} sent to DLQ: {error_type} at {step.value}"
        )

    def _generate_failure_reason(
        self,
        classification: ErrorClassification,
        error_message: str
    ) -> str:
        """Generate a user-friendly failure reason.

        Args:
            classification: Error classification
            error_message: Raw error message

        Returns:
            User-friendly explanation
        """
        reasons = {
            ErrorClassification.TRANSIENT: (
                "Network or API connectivity issues persisted after multiple retries. "
                "This is often temporary. Try manual retry or check external service status."
            ),
            ErrorClassification.RATE_LIMIT: (
                "API rate limits were exceeded repeatedly. "
                "Wait for rate limit reset or upgrade API tier before retrying."
            ),
            ErrorClassification.CONFIGURATION: (
                "Configuration error detected (missing API key, invalid settings, etc.). "
                "Fix configuration in Admin > System Config, then manually retry."
            ),
            ErrorClassification.VALIDATION: (
                "Invalid data or validation error. "
                "Check story content and parameters. Manual editing may be required."
            ),
            ErrorClassification.RESOURCE: (
                "System resource issue (disk space, memory). "
                "Free up resources and manually retry."
            ),
            ErrorClassification.PERMANENT: (
                "Unrecoverable error. "
                "Review error details and logs. May require code changes or manual intervention."
            )
        }

        base_reason = reasons.get(
            classification,
            "Unknown error occurred. Review error details."
        )

        return f"{base_reason}\n\nError: {error_message[:200]}"


def retry_workflow_step(step_name: str):
    """Decorator to add retry logic to workflow step methods.

    Usage:
        @retry_workflow_step('image_generation')
        def _process_image_generation(self, story):
            ...

    Args:
        step_name: Name of the workflow step

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, story: Story, *args, **kwargs):
            retry_service = RetryService()

            try:
                # Execute the workflow step
                result = func(self, story, *args, **kwargs)

                # If successful and this was a retry, record success
                if story.retry_count > 0:
                    logger.info(
                        f"Story {story.id} retry successful at {step_name} "
                        f"after {story.retry_count} attempts"
                    )
                    metrics_service.retry_success_total.labels(
                        step=step_name
                    ).inc()

                    # Reset retry state on success
                    story.reset_retry_state()

                return result

            except Exception as e:
                # Get current workflow step
                current_step = story.current_step

                # Handle the failure with retry logic
                should_retry = retry_service.handle_failure(story, e, current_step)

                if should_retry:
                    # Story will be retried - return False to indicate failure but not permanent
                    logger.info(f"Story {story.id} will be retried")
                    return False
                else:
                    # Story sent to DLQ - return False
                    logger.error(f"Story {story.id} sent to DLQ")
                    return False

        return wrapper
    return decorator
```

### 5.2 Queue Service Enhancements

**Modifications to `StoryQueueService`:**

```python
@staticmethod
def get_next_story(worker_id=None):
    """Get the next story to process from the queue.

    Enhanced to respect next_retry_at timestamps.
    """
    try:
        if not worker_id:
            worker_id = f"worker_{uuid.uuid4().hex[:8]}"

        now = datetime.utcnow()

        # Find stories that need processing, respecting retry schedules
        query = db.session.query(StoryQueue, Story).join(Story).filter(
            and_(
                StoryQueue.processing_started_at.is_(None),  # Not being processed
                Story.current_step != WorkflowStep.COMPLETED,
                Story.current_step != WorkflowStep.FAILED,
                or_(
                    Story.next_retry_at.is_(None),           # Never retried
                    Story.next_retry_at <= now               # Retry time reached
                )
            )
        ).order_by(
            StoryQueue.priority.desc(),
            Story.next_retry_at.asc().nullsfirst(),  # Retry stories first
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

        if story.retry_count > 0:
            logger.info(
                f"Worker {worker_id} claimed story {story.id} from queue "
                f"(retry attempt {story.retry_count})"
            )
        else:
            logger.info(f"Worker {worker_id} claimed story {story.id} from queue")

        return story

    except Exception as e:
        logger.error(f"Error getting next story from queue: {str(e)}")
        db.session.rollback()
        raise
```

---

## 6. Dead Letter Queue (DLQ) Implementation

### 6.1 DLQ Service

**File:** `ephergent_generator/services/dlq_service.py`

```python
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import logging

from ephergent_generator import db
from ephergent_generator.models import StoryFailure, Story, WorkflowStep
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.services.queue_service import StoryQueueService

logger = logging.getLogger(__name__)


class DLQService:
    """Service for managing the Dead Letter Queue."""

    @staticmethod
    def get_failures(
        status: Optional[str] = None,
        error_classification: Optional[str] = None,
        failed_at_step: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[StoryFailure]:
        """Get failures from DLQ with optional filtering.

        Args:
            status: Filter by status (pending, investigating, resolved, archived)
            error_classification: Filter by error classification
            failed_at_step: Filter by workflow step
            limit: Maximum number of results
            offset: Pagination offset

        Returns:
            List of StoryFailure objects
        """
        query = StoryFailure.query

        if status:
            query = query.filter_by(status=status)

        if error_classification:
            query = query.filter_by(error_classification=error_classification)

        if failed_at_step:
            query = query.filter_by(failed_at_step=WorkflowStep(failed_at_step))

        failures = query.order_by(
            desc(StoryFailure.failed_at)
        ).limit(limit).offset(offset).all()

        return failures

    @staticmethod
    def get_failure_stats() -> Dict[str, Any]:
        """Get DLQ statistics.

        Returns:
            Dictionary with DLQ statistics
        """
        total = StoryFailure.query.count()

        # Count by status
        by_status = db.session.query(
            StoryFailure.status,
            func.count(StoryFailure.id)
        ).group_by(StoryFailure.status).all()

        status_counts = {status: count for status, count in by_status}

        # Count by error classification
        by_classification = db.session.query(
            StoryFailure.error_classification,
            func.count(StoryFailure.id)
        ).group_by(StoryFailure.error_classification).all()

        classification_counts = {
            classification: count
            for classification, count in by_classification
        }

        # Count by step
        by_step = db.session.query(
            StoryFailure.failed_at_step,
            func.count(StoryFailure.id)
        ).group_by(StoryFailure.failed_at_step).all()

        step_counts = {
            step.value if step else 'unknown': count
            for step, count in by_step
        }

        # Recent failures (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_count = StoryFailure.query.filter(
            StoryFailure.failed_at >= yesterday
        ).count()

        return {
            'total': total,
            'by_status': status_counts,
            'by_classification': classification_counts,
            'by_step': step_counts,
            'last_24h': recent_count
        }

    @staticmethod
    def retry_failure(
        failure_id: int,
        user_id: int,
        from_step: Optional[WorkflowStep] = None
    ) -> bool:
        """Retry a failed story.

        Args:
            failure_id: ID of the failure record
            user_id: User initiating the retry
            from_step: Optional step to retry from (default: failed step)

        Returns:
            True if retry was successful, False otherwise
        """
        failure = StoryFailure.query.get(failure_id)
        if not failure:
            logger.error(f"Failure {failure_id} not found")
            return False

        story = failure.story
        if not story:
            logger.error(f"Story {failure.story_id} not found for failure {failure_id}")
            return False

        try:
            # Determine which step to retry from
            retry_step = from_step or failure.failed_at_step

            logger.info(
                f"Manually retrying story {story.id} from {retry_step.value} "
                f"(failure {failure_id}) by user {user_id}"
            )

            # Reset story for regeneration from specific step
            story.regenerate_from_step(retry_step)

            # Mark failure as resolved
            failure.mark_resolved(
                user_id=user_id,
                notes=f"Manually retried from {retry_step.value}"
            )

            # Re-enqueue story with high priority
            queue_service = StoryQueueService()
            queue_service.enqueue_story(story.id, priority=10)

            db.session.commit()

            logger.info(
                f"Story {story.id} retry initiated from {retry_step.value}, "
                f"failure {failure_id} marked resolved"
            )

            return True

        except Exception as e:
            logger.error(f"Error retrying failure {failure_id}: {str(e)}")
            db.session.rollback()
            return False

    @staticmethod
    def bulk_retry(
        failure_ids: List[int],
        user_id: int
    ) -> Dict[str, Any]:
        """Retry multiple failures at once.

        Args:
            failure_ids: List of failure IDs to retry
            user_id: User initiating the bulk retry

        Returns:
            Dictionary with success/failure counts
        """
        results = {
            'total': len(failure_ids),
            'success': 0,
            'failed': 0,
            'errors': []
        }

        for failure_id in failure_ids:
            try:
                if DLQService.retry_failure(failure_id, user_id):
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failure {failure_id}: retry failed")
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Failure {failure_id}: {str(e)}")

        logger.info(
            f"Bulk retry completed by user {user_id}: "
            f"{results['success']}/{results['total']} successful"
        )

        return results

    @staticmethod
    def archive_failure(failure_id: int, user_id: int) -> bool:
        """Archive a failure record.

        Args:
            failure_id: ID of the failure to archive
            user_id: User archiving the failure

        Returns:
            True if successful, False otherwise
        """
        failure = StoryFailure.query.get(failure_id)
        if not failure:
            return False

        try:
            failure.archive()
            db.session.commit()

            logger.info(f"Failure {failure_id} archived by user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Error archiving failure {failure_id}: {str(e)}")
            db.session.rollback()
            return False
```

---

## 7. Admin UI Components

### 7.1 New Admin Routes

**File:** `ephergent_generator/admin/routes.py` (additions)

```python
# ============================================================================
# Dead Letter Queue Routes
# ============================================================================

@admin_bp.route('/dlq')
@admin_required
def dlq_list():
    """List stories in Dead Letter Queue."""
    # Get filter parameters
    status_filter = request.args.get('status', 'pending')
    classification_filter = request.args.get('classification', 'all')
    step_filter = request.args.get('step', 'all')
    page = int(request.args.get('page', 1))
    per_page = 50

    # Get DLQ service
    dlq_service = DLQService()

    # Build query
    query = StoryFailure.query

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    if classification_filter != 'all':
        query = query.filter_by(error_classification=classification_filter)

    if step_filter != 'all':
        query = query.filter_by(failed_at_step=WorkflowStep(step_filter))

    # Paginate
    pagination = query.order_by(desc(StoryFailure.failed_at)).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    # Get statistics
    stats = dlq_service.get_failure_stats()

    return render_template(
        'admin/dlq/list.html',
        failures=pagination.items,
        pagination=pagination,
        stats=stats,
        status_filter=status_filter,
        classification_filter=classification_filter,
        step_filter=step_filter,
        WorkflowStep=WorkflowStep
    )


@admin_bp.route('/dlq/<int:id>')
@admin_required
def dlq_detail(id):
    """View detailed information about a failed story."""
    failure = StoryFailure.query.get_or_404(id)

    return render_template(
        'admin/dlq/detail.html',
        failure=failure,
        story=failure.story,
        WorkflowStep=WorkflowStep
    )


@admin_bp.route('/dlq/<int:id>/retry', methods=['POST'])
@admin_required
def dlq_retry(id):
    """Retry a failed story from DLQ."""
    from_step = request.form.get('from_step')

    dlq_service = DLQService()

    # Parse from_step if provided
    retry_step = None
    if from_step and from_step != 'failed_step':
        try:
            retry_step = WorkflowStep(from_step)
        except ValueError:
            flash(f'Invalid workflow step: {from_step}', 'error')
            return redirect(url_for('admin.dlq_detail', id=id))

    # Retry the failure
    if dlq_service.retry_failure(id, current_user.id, retry_step):
        flash('Story retry initiated successfully!', 'success')
        logger.info(f"DLQ retry initiated for failure {id} by user {current_user.username}")
    else:
        flash('Failed to retry story. Check logs for details.', 'error')
        logger.error(f"DLQ retry failed for failure {id}")

    return redirect(url_for('admin.dlq_list'))


@admin_bp.route('/dlq/bulk-retry', methods=['POST'])
@admin_required
def dlq_bulk_retry():
    """Retry multiple failures at once."""
    failure_ids = request.form.getlist('failure_ids[]', type=int)

    if not failure_ids:
        flash('No failures selected for retry.', 'warning')
        return redirect(url_for('admin.dlq_list'))

    dlq_service = DLQService()
    results = dlq_service.bulk_retry(failure_ids, current_user.id)

    flash(
        f'Bulk retry completed: {results["success"]}/{results["total"]} successful',
        'success' if results['success'] > 0 else 'error'
    )

    if results['errors']:
        for error in results['errors'][:5]:  # Show first 5 errors
            flash(error, 'warning')

    logger.info(
        f"Bulk retry initiated for {len(failure_ids)} failures by {current_user.username}: "
        f"{results['success']} successful"
    )

    return redirect(url_for('admin.dlq_list'))


@admin_bp.route('/dlq/<int:id>/archive', methods=['POST'])
@admin_required
def dlq_archive(id):
    """Archive a failure record."""
    dlq_service = DLQService()

    if dlq_service.archive_failure(id, current_user.id):
        flash('Failure archived successfully.', 'success')
    else:
        flash('Failed to archive failure.', 'error')

    return redirect(url_for('admin.dlq_list'))


@admin_bp.route('/dlq/<int:id>/update-status', methods=['POST'])
@admin_required
def dlq_update_status(id):
    """Update failure status."""
    failure = StoryFailure.query.get_or_404(id)
    new_status = request.form.get('status')
    notes = request.form.get('notes')

    if new_status not in ['pending', 'investigating', 'resolved', 'archived']:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin.dlq_detail', id=id))

    try:
        failure.status = new_status
        if notes:
            failure.resolution_notes = notes
        if new_status == 'resolved':
            failure.resolved_at = datetime.utcnow()
            failure.resolved_by = current_user.id

        db.session.commit()
        flash(f'Status updated to {new_status}.', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Error updating status: {str(e)}', 'error')

    return redirect(url_for('admin.dlq_detail', id=id))


# ============================================================================
# DLQ AJAX/API Routes
# ============================================================================

@admin_bp.route('/api/dlq/stats')
@admin_required
def api_dlq_stats():
    """Get DLQ statistics for dashboard widgets."""
    dlq_service = DLQService()
    stats = dlq_service.get_failure_stats()
    return jsonify(stats)
```

### 7.2 Admin Templates

**File:** `ephergent_generator/templates/admin/dlq/list.html`

```jinja2
{% extends "admin/base.html" %}

{% block title %}Dead Letter Queue - Admin{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col">
            <h1 class="h2">Dead Letter Queue</h1>
            <p class="text-muted">Failed stories requiring manual intervention</p>
        </div>
    </div>

    <!-- Statistics Cards -->
    <div class="row mb-4">
        <div class="col-md-3">
            <div class="card border-danger">
                <div class="card-body">
                    <h5 class="card-title">Total Failures</h5>
                    <p class="display-4">{{ stats.total }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-warning">
                <div class="card-body">
                    <h5 class="card-title">Pending</h5>
                    <p class="display-4">{{ stats.by_status.get('pending', 0) }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-info">
                <div class="card-body">
                    <h5 class="card-title">Investigating</h5>
                    <p class="display-4">{{ stats.by_status.get('investigating', 0) }}</p>
                </div>
            </div>
        </div>
        <div class="col-md-3">
            <div class="card border-success">
                <div class="card-body">
                    <h5 class="card-title">Last 24h</h5>
                    <p class="display-4">{{ stats.last_24h }}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Filters -->
    <div class="card mb-4">
        <div class="card-body">
            <form method="GET" class="row g-3">
                <div class="col-md-3">
                    <label for="status" class="form-label">Status</label>
                    <select name="status" id="status" class="form-select">
                        <option value="all" {% if status_filter == 'all' %}selected{% endif %}>All</option>
                        <option value="pending" {% if status_filter == 'pending' %}selected{% endif %}>Pending</option>
                        <option value="investigating" {% if status_filter == 'investigating' %}selected{% endif %}>Investigating</option>
                        <option value="resolved" {% if status_filter == 'resolved' %}selected{% endif %}>Resolved</option>
                        <option value="archived" {% if status_filter == 'archived' %}selected{% endif %}>Archived</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label for="classification" class="form-label">Error Classification</label>
                    <select name="classification" id="classification" class="form-select">
                        <option value="all" {% if classification_filter == 'all' %}selected{% endif %}>All</option>
                        <option value="transient" {% if classification_filter == 'transient' %}selected{% endif %}>Transient</option>
                        <option value="rate_limit" {% if classification_filter == 'rate_limit' %}selected{% endif %}>Rate Limit</option>
                        <option value="configuration" {% if classification_filter == 'configuration' %}selected{% endif %}>Configuration</option>
                        <option value="validation" {% if classification_filter == 'validation' %}selected{% endif %}>Validation</option>
                        <option value="resource" {% if classification_filter == 'resource' %}selected{% endif %}>Resource</option>
                        <option value="permanent" {% if classification_filter == 'permanent' %}selected{% endif %}>Permanent</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label for="step" class="form-label">Failed At Step</label>
                    <select name="step" id="step" class="form-select">
                        <option value="all" {% if step_filter == 'all' %}selected{% endif %}>All</option>
                        {% for step in WorkflowStep %}
                        <option value="{{ step.value }}" {% if step_filter == step.value %}selected{% endif %}>
                            {{ step.value|title|replace('_', ' ') }}
                        </option>
                        {% endfor %}
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary">Filter</button>
                    <a href="{{ url_for('admin.dlq_list') }}" class="btn btn-secondary ms-2">Reset</a>
                </div>
            </form>
        </div>
    </div>

    <!-- Bulk Actions -->
    <form method="POST" action="{{ url_for('admin.dlq_bulk_retry') }}" id="bulkForm">
        <div class="card mb-4">
            <div class="card-body">
                <button type="submit" class="btn btn-warning" id="bulkRetryBtn" disabled>
                    Retry Selected
                </button>
                <span class="text-muted ms-3" id="selectedCount">0 selected</span>
            </div>
        </div>

        <!-- Failures Table -->
        <div class="card">
            <div class="card-body">
                <div class="table-responsive">
                    <table class="table table-hover">
                        <thead>
                            <tr>
                                <th><input type="checkbox" id="selectAll"></th>
                                <th>ID</th>
                                <th>Story</th>
                                <th>Failed At Step</th>
                                <th>Error Type</th>
                                <th>Classification</th>
                                <th>Retries</th>
                                <th>Failed At</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for failure in failures %}
                            <tr>
                                <td>
                                    <input type="checkbox" name="failure_ids[]" value="{{ failure.id }}"
                                           class="failure-checkbox">
                                </td>
                                <td>{{ failure.id }}</td>
                                <td>
                                    <a href="{{ url_for('admin.dlq_detail', id=failure.id) }}">
                                        {{ failure.story.topic[:50] }}...
                                    </a>
                                </td>
                                <td>
                                    <span class="badge bg-secondary">
                                        {{ failure.failed_at_step.value|replace('_', ' ')|title }}
                                    </span>
                                </td>
                                <td><code>{{ failure.error_type }}</code></td>
                                <td>
                                    {% if failure.error_classification == 'transient' %}
                                    <span class="badge bg-warning">Transient</span>
                                    {% elif failure.error_classification == 'rate_limit' %}
                                    <span class="badge bg-info">Rate Limit</span>
                                    {% elif failure.error_classification == 'configuration' %}
                                    <span class="badge bg-danger">Configuration</span>
                                    {% elif failure.error_classification == 'permanent' %}
                                    <span class="badge bg-dark">Permanent</span>
                                    {% else %}
                                    <span class="badge bg-secondary">{{ failure.error_classification }}</span>
                                    {% endif %}
                                </td>
                                <td>{{ failure.retry_count }}</td>
                                <td>{{ failure.failed_at.strftime('%Y-%m-%d %H:%M') }}</td>
                                <td>
                                    {% if failure.status == 'pending' %}
                                    <span class="badge bg-warning">Pending</span>
                                    {% elif failure.status == 'investigating' %}
                                    <span class="badge bg-info">Investigating</span>
                                    {% elif failure.status == 'resolved' %}
                                    <span class="badge bg-success">Resolved</span>
                                    {% else %}
                                    <span class="badge bg-secondary">{{ failure.status|title }}</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <a href="{{ url_for('admin.dlq_detail', id=failure.id) }}"
                                       class="btn btn-sm btn-primary">View</a>
                                </td>
                            </tr>
                            {% else %}
                            <tr>
                                <td colspan="10" class="text-center text-muted">
                                    No failures found matching the current filters.
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <!-- Pagination -->
                {% if pagination.pages > 1 %}
                <nav aria-label="DLQ pagination">
                    <ul class="pagination justify-content-center">
                        {% if pagination.has_prev %}
                        <li class="page-item">
                            <a class="page-link" href="{{ url_for('admin.dlq_list', page=pagination.prev_num, status=status_filter, classification=classification_filter, step=step_filter) }}">
                                Previous
                            </a>
                        </li>
                        {% endif %}

                        {% for page_num in pagination.iter_pages(left_edge=1, right_edge=1, left_current=2, right_current=2) %}
                            {% if page_num %}
                                <li class="page-item {% if page_num == pagination.page %}active{% endif %}">
                                    <a class="page-link" href="{{ url_for('admin.dlq_list', page=page_num, status=status_filter, classification=classification_filter, step=step_filter) }}">
                                        {{ page_num }}
                                    </a>
                                </li>
                            {% else %}
                                <li class="page-item disabled"><span class="page-link">...</span></li>
                            {% endif %}
                        {% endfor %}

                        {% if pagination.has_next %}
                        <li class="page-item">
                            <a class="page-link" href="{{ url_for('admin.dlq_list', page=pagination.next_num, status=status_filter, classification=classification_filter, step=step_filter) }}">
                                Next
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
                {% endif %}
            </div>
        </div>
    </form>
</div>

<script>
// Bulk selection handling
document.getElementById('selectAll').addEventListener('change', function() {
    const checkboxes = document.querySelectorAll('.failure-checkbox');
    checkboxes.forEach(cb => cb.checked = this.checked);
    updateBulkActions();
});

document.querySelectorAll('.failure-checkbox').forEach(cb => {
    cb.addEventListener('change', updateBulkActions);
});

function updateBulkActions() {
    const checked = document.querySelectorAll('.failure-checkbox:checked').length;
    document.getElementById('selectedCount').textContent = `${checked} selected`;
    document.getElementById('bulkRetryBtn').disabled = checked === 0;
}
</script>
{% endblock %}
```

**File:** `ephergent_generator/templates/admin/dlq/detail.html`

```jinja2
{% extends "admin/base.html" %}

{% block title %}Failure Details - {{ failure.id }} - Admin{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row mb-4">
        <div class="col">
            <h1 class="h2">Failure Details #{{ failure.id }}</h1>
            <nav aria-label="breadcrumb">
                <ol class="breadcrumb">
                    <li class="breadcrumb-item"><a href="{{ url_for('admin.dashboard') }}">Admin</a></li>
                    <li class="breadcrumb-item"><a href="{{ url_for('admin.dlq_list') }}">Dead Letter Queue</a></li>
                    <li class="breadcrumb-item active">Failure #{{ failure.id }}</li>
                </ol>
            </nav>
        </div>
    </div>

    <!-- Status and Actions -->
    <div class="row mb-4">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header">
                    <h5>Failure Information</h5>
                </div>
                <div class="card-body">
                    <dl class="row">
                        <dt class="col-sm-3">Story ID</dt>
                        <dd class="col-sm-9">
                            <a href="{{ url_for('main.story_detail', id=failure.story_id) }}">
                                {{ failure.story_id }}
                            </a>
                        </dd>

                        <dt class="col-sm-3">Topic</dt>
                        <dd class="col-sm-9">{{ failure.story.topic }}</dd>

                        <dt class="col-sm-3">Failed At Step</dt>
                        <dd class="col-sm-9">
                            <span class="badge bg-secondary">
                                {{ failure.failed_at_step.value|replace('_', ' ')|title }}
                            </span>
                        </dd>

                        <dt class="col-sm-3">Error Type</dt>
                        <dd class="col-sm-9"><code>{{ failure.error_type }}</code></dd>

                        <dt class="col-sm-3">Classification</dt>
                        <dd class="col-sm-9">
                            {% if failure.error_classification == 'transient' %}
                            <span class="badge bg-warning">Transient</span>
                            {% elif failure.error_classification == 'rate_limit' %}
                            <span class="badge bg-info">Rate Limit</span>
                            {% elif failure.error_classification == 'configuration' %}
                            <span class="badge bg-danger">Configuration</span>
                            {% elif failure.error_classification == 'permanent' %}
                            <span class="badge bg-dark">Permanent</span>
                            {% else %}
                            <span class="badge bg-secondary">{{ failure.error_classification }}</span>
                            {% endif %}
                        </dd>

                        <dt class="col-sm-3">Retry Count</dt>
                        <dd class="col-sm-9">{{ failure.retry_count }}</dd>

                        <dt class="col-sm-3">Failed At</dt>
                        <dd class="col-sm-9">{{ failure.failed_at.strftime('%Y-%m-%d %H:%M:%S UTC') }}</dd>

                        <dt class="col-sm-3">Status</dt>
                        <dd class="col-sm-9">
                            {% if failure.status == 'pending' %}
                            <span class="badge bg-warning">Pending</span>
                            {% elif failure.status == 'investigating' %}
                            <span class="badge bg-info">Investigating</span>
                            {% elif failure.status == 'resolved' %}
                            <span class="badge bg-success">Resolved</span>
                            {% else %}
                            <span class="badge bg-secondary">{{ failure.status|title }}</span>
                            {% endif %}
                        </dd>

                        {% if failure.resolved_at %}
                        <dt class="col-sm-3">Resolved At</dt>
                        <dd class="col-sm-9">{{ failure.resolved_at.strftime('%Y-%m-%d %H:%M:%S UTC') }}</dd>
                        {% endif %}
                    </dl>
                </div>
            </div>
        </div>

        <div class="col-md-4">
            <div class="card">
                <div class="card-header">
                    <h5>Actions</h5>
                </div>
                <div class="card-body">
                    {% if failure.can_retry and failure.status != 'resolved' %}
                    <form method="POST" action="{{ url_for('admin.dlq_retry', id=failure.id) }}"
                          onsubmit="return confirm('Are you sure you want to retry this story?');">
                        <div class="mb-3">
                            <label for="from_step" class="form-label">Retry From Step</label>
                            <select name="from_step" id="from_step" class="form-select">
                                <option value="failed_step">Failed Step ({{ failure.failed_at_step.value }})</option>
                                {% for step in WorkflowStep %}
                                {% if step.value not in ['completed', 'failed'] %}
                                <option value="{{ step.value }}">{{ step.value|title|replace('_', ' ') }}</option>
                                {% endif %}
                                {% endfor %}
                            </select>
                        </div>
                        <button type="submit" class="btn btn-warning w-100">Retry Story</button>
                    </form>
                    {% else %}
                    <div class="alert alert-info">
                        {% if not failure.can_retry %}
                        This failure cannot be retried automatically. Manual intervention required.
                        {% else %}
                        This failure has already been resolved.
                        {% endif %}
                    </div>
                    {% endif %}

                    <hr>

                    <form method="POST" action="{{ url_for('admin.dlq_update_status', id=failure.id) }}">
                        <div class="mb-3">
                            <label for="status" class="form-label">Update Status</label>
                            <select name="status" id="status" class="form-select">
                                <option value="pending" {% if failure.status == 'pending' %}selected{% endif %}>Pending</option>
                                <option value="investigating" {% if failure.status == 'investigating' %}selected{% endif %}>Investigating</option>
                                <option value="resolved" {% if failure.status == 'resolved' %}selected{% endif %}>Resolved</option>
                                <option value="archived" {% if failure.status == 'archived' %}selected{% endif %}>Archived</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="notes" class="form-label">Notes</label>
                            <textarea name="notes" id="notes" class="form-control" rows="3">{{ failure.resolution_notes or '' }}</textarea>
                        </div>
                        <button type="submit" class="btn btn-primary w-100">Update Status</button>
                    </form>

                    <hr>

                    <form method="POST" action="{{ url_for('admin.dlq_archive', id=failure.id) }}"
                          onsubmit="return confirm('Are you sure you want to archive this failure?');">
                        <button type="submit" class="btn btn-secondary w-100">Archive</button>
                    </form>
                </div>
            </div>
        </div>
    </div>

    <!-- Error Details -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Error Message</h5>
                </div>
                <div class="card-body">
                    <pre class="bg-light p-3 rounded"><code>{{ failure.error_message }}</code></pre>
                </div>
            </div>
        </div>
    </div>

    <!-- Failure Reason -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Failure Reason (User-Friendly)</h5>
                </div>
                <div class="card-body">
                    <p>{{ failure.failure_reason or 'No failure reason provided.' }}</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Retry History -->
    {% if failure.retry_history %}
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Retry History</h5>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-sm">
                            <thead>
                                <tr>
                                    <th>Attempt</th>
                                    <th>Timestamp</th>
                                    <th>Step</th>
                                    <th>Classification</th>
                                    <th>Backoff (seconds)</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for retry in failure.get_retry_history() %}
                                <tr>
                                    <td>{{ retry.attempt }}</td>
                                    <td>{{ retry.timestamp }}</td>
                                    <td>{{ retry.step }}</td>
                                    <td>
                                        <span class="badge bg-secondary">
                                            {{ retry.error_classification }}
                                        </span>
                                    </td>
                                    <td>{{ retry.backoff_seconds }}</td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
    {% endif %}

    <!-- Stack Trace -->
    {% if failure.error_traceback %}
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h5>Stack Trace</h5>
                </div>
                <div class="card-body">
                    <pre class="bg-dark text-light p-3 rounded" style="max-height: 500px; overflow-y: auto;"><code>{{ failure.error_traceback }}</code></pre>
                </div>
            </div>
        </div>
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

## 8. Metrics Integration

### 8.1 New Prometheus Metrics

**File:** `ephergent_generator/utils/metrics.py` (additions)

```python
# Add to MetricsService.__init__():

# ====================================================================
# Retry and DLQ Metrics
# ====================================================================

self.retry_attempts_total = Counter(
    'ephergent_retry_attempts_total',
    'Total number of retry attempts',
    ['step', 'error_classification'],
    registry=self.registry
)

self.retry_success_total = Counter(
    'ephergent_retry_success_total',
    'Total number of successful retries',
    ['step'],
    registry=self.registry
)

self.retry_exhausted_total = Counter(
    'ephergent_retry_exhausted_total',
    'Total number of stories that exhausted retry attempts',
    ['step', 'error_classification'],
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
    'Number of DLQ stories by error classification',
    ['error_classification'],
    registry=self.registry
)

self.dlq_by_step = Gauge(
    'ephergent_dlq_by_step',
    'Number of DLQ stories by failed workflow step',
    ['step'],
    registry=self.registry
)

self.retry_backoff_seconds = Histogram(
    'ephergent_retry_backoff_seconds',
    'Distribution of retry backoff delays',
    ['error_classification'],
    buckets=[60, 120, 300, 600, 1800, 3600],  # 1min to 1hour
    registry=self.registry
)
```

**Add to `update_workflow_metrics()` method:**

```python
# Update DLQ metrics
from ephergent_generator.models import StoryFailure

# DLQ size by status
dlq_by_status = db.session.query(
    StoryFailure.status,
    func.count(StoryFailure.id)
).group_by(StoryFailure.status).all()

for status in ['pending', 'investigating', 'resolved', 'archived']:
    count = next((c for s, c in dlq_by_status if s == status), 0)
    self.dlq_size.labels(status=status).set(count)

# DLQ by error classification
dlq_by_classification = db.session.query(
    StoryFailure.error_classification,
    func.count(StoryFailure.id)
).group_by(StoryFailure.error_classification).all()

for classification, count in dlq_by_classification:
    self.dlq_by_error_type.labels(
        error_classification=classification
    ).set(count)

# DLQ by step
dlq_by_step = db.session.query(
    StoryFailure.failed_at_step,
    func.count(StoryFailure.id)
).group_by(StoryFailure.failed_at_step).all()

for step, count in dlq_by_step:
    if step:
        self.dlq_by_step.labels(step=step.value).set(count)
```

### 8.2 Grafana Dashboard Queries

**Panel: Retry Success Rate**
```promql
rate(ephergent_retry_success_total[5m]) /
(rate(ephergent_retry_attempts_total[5m]) + rate(ephergent_retry_success_total[5m]))
```

**Panel: DLQ Size Over Time**
```promql
sum(ephergent_dlq_size) by (status)
```

**Panel: Retry Attempts by Error Type**
```promql
sum(rate(ephergent_retry_attempts_total[5m])) by (error_classification)
```

**Panel: Stories Exhausting Retries**
```promql
increase(ephergent_retry_exhausted_total[1h])
```

---

## 9. Service Layer Changes

### 9.1 Workflow Service Integration

**File:** `ephergent_generator/services/workflow_service.py` (modifications)

```python
# Add imports
from ephergent_generator.services.retry_service import retry_workflow_step
from ephergent_generator.utils.error_classification import ErrorClassifier

# Wrap all workflow step methods with retry decorator
@retry_workflow_step('story_generation')
def _process_story_generation(self, story):
    """Process the story generation step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('title_generation')
def _process_title_generation(self, story):
    """Process the title generation step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('image_generation')
def _process_image_generation(self, story):
    """Process the image generation step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('audio_generation')
def _process_audio_generation(self, story):
    """Process the audio generation step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('video_generation')
def _process_video_generation(self, story):
    """Process the video generation step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('youtube_upload')
def _process_youtube_upload(self, story):
    """Process the YouTube upload step."""
    # ... existing code remains the same
    pass

@retry_workflow_step('ghost_publishing')
def _process_ghost_publishing(self, story):
    """Process the Ghost blog publishing step."""
    # ... existing code remains the same
    pass
```

### 9.2 Add Regeneration Methods

```python
def regenerate_story_from_step(self, story_id: int, from_step: WorkflowStep) -> Optional[Story]:
    """Regenerate a story from a specific workflow step.

    Args:
        story_id: ID of the story to regenerate
        from_step: Workflow step to start regeneration from

    Returns:
        Story object or None if not found
    """
    story = Story.query.get(story_id)
    if not story:
        logger.error(f"Story {story_id} not found for regeneration")
        return None

    logger.info(
        f"Regenerating story {story_id} from {from_step.value}: {story.topic}"
    )

    # Reset story from specific step
    story.regenerate_from_step(from_step)

    # Add back to queue with high priority
    self.queue_service.enqueue_story(story.id, priority=5)

    # Commit changes
    db.session.commit()

    logger.info(
        f"Story {story_id} reset to {from_step.value} and queued for regeneration"
    )

    return story
```

---

## 10. Migration Strategy

### 10.1 Data Migration for Existing Failed Stories

**Script:** `scripts/migrate_existing_failures.py`

```python
#!/usr/bin/env python3
"""Migrate existing failed stories to new retry/DLQ system.

This script should be run AFTER the database migration is applied.
It will:
1. Find all stories in FAILED state
2. Create StoryFailure records for them
3. Attempt to classify their errors
4. Set appropriate retry flags
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ephergent_generator import create_app, db
from ephergent_generator.models import Story, StoryFailure, WorkflowStep
from ephergent_generator.utils.error_classification import ErrorClassifier, ErrorClassification
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def migrate_failed_stories():
    """Migrate existing failed stories to DLQ."""
    app = create_app()

    with app.app_context():
        # Find all failed stories
        failed_stories = Story.query.filter_by(current_step=WorkflowStep.FAILED).all()

        logger.info(f"Found {len(failed_stories)} failed stories to migrate")

        migrated = 0
        skipped = 0

        for story in failed_stories:
            # Check if already in DLQ
            existing = StoryFailure.query.filter_by(story_id=story.id).first()
            if existing:
                logger.debug(f"Story {story.id} already in DLQ, skipping")
                skipped += 1
                continue

            # Determine failed step from workflow_data or default to last known step
            workflow_data = story.get_workflow_data()
            failed_step = story.current_step  # Default to FAILED

            # Try to infer actual step from available data
            if story.content and not story.title:
                failed_step = WorkflowStep.TITLE_GENERATION
            elif story.title and not story.image_paths:
                failed_step = WorkflowStep.IMAGE_GENERATION
            elif story.image_paths and not story.audio_path:
                failed_step = WorkflowStep.AUDIO_GENERATION
            elif story.audio_path and not story.video_path:
                failed_step = WorkflowStep.VIDEO_GENERATION
            elif story.video_path and not story.youtube_video_id:
                failed_step = WorkflowStep.YOUTUBE_UPLOAD
            elif story.youtube_video_id and not story.ghost_post_id:
                failed_step = WorkflowStep.GHOST_PUBLISHING

            # Classify error if possible
            error_message = story.error_message or "Unknown error (migrated from legacy system)"
            error_type = "UnknownError"
            classification = ErrorClassification.PERMANENT  # Conservative default

            # Try to parse error type from message
            if ":" in error_message:
                potential_type = error_message.split(":")[0].strip()
                if potential_type and not " " in potential_type:
                    error_type = potential_type

            # Simple classification heuristics
            error_lower = error_message.lower()
            if any(word in error_lower for word in ['timeout', 'connection', 'network']):
                classification = ErrorClassification.TRANSIENT
            elif 'rate limit' in error_lower or '429' in error_message:
                classification = ErrorClassification.RATE_LIMIT
            elif any(word in error_lower for word in ['key', 'auth', 'config']):
                classification = ErrorClassification.CONFIGURATION

            # Create DLQ entry
            failure = StoryFailure(
                story_id=story.id,
                failed_at_step=failed_step,
                error_type=error_type,
                error_classification=classification.value,
                error_message=error_message,
                error_traceback=None,  # Not available for legacy failures
                retry_count=0,  # Unknown for legacy
                retry_history=None,
                failure_reason=f"Migrated from legacy system. Original error: {error_message[:200]}",
                can_retry=True,  # Allow retry by default
                status='pending'
            )

            db.session.add(failure)
            migrated += 1

            logger.info(
                f"Migrated story {story.id} to DLQ "
                f"(step: {failed_step.value}, classification: {classification.value})"
            )

        # Commit all changes
        db.session.commit()

        logger.info(
            f"Migration complete: {migrated} migrated, {skipped} skipped, "
            f"{migrated + skipped} total"
        )


if __name__ == '__main__':
    migrate_failed_stories()
```

### 10.2 Configuration Seeding

**Script:** `scripts/seed_retry_config.py`

```python
#!/usr/bin/env python3
"""Seed retry configuration defaults into SystemConfig."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ephergent_generator import create_app, db
from ephergent_generator.models import SystemConfig
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


RETRY_CONFIG = {
    'retry.max_attempts': {
        'value': '5',
        'type': 'int',
        'category': 'retry',
        'description': 'Maximum retry attempts per workflow step',
        'is_public': True
    },
    'retry.transient.base_delay_seconds': {
        'value': '60',
        'type': 'int',
        'category': 'retry',
        'description': 'Base delay in seconds for transient errors (1 minute)',
        'is_public': True
    },
    'retry.rate_limit.base_delay_seconds': {
        'value': '300',
        'type': 'int',
        'category': 'retry',
        'description': 'Base delay in seconds for rate limit errors (5 minutes)',
        'is_public': True
    },
    'retry.resource.base_delay_seconds': {
        'value': '120',
        'type': 'int',
        'category': 'retry',
        'description': 'Base delay in seconds for resource errors (2 minutes)',
        'is_public': True
    },
    'retry.exponential_backoff_multiplier': {
        'value': '2.0',
        'type': 'float',
        'category': 'retry',
        'description': 'Exponential backoff multiplier',
        'is_public': True
    },
    'retry.enable_jitter': {
        'value': 'true',
        'type': 'bool',
        'category': 'retry',
        'description': 'Add random jitter to retry delays (±20%)',
        'is_public': True
    }
}


def seed_config():
    """Seed retry configuration."""
    app = create_app()

    with app.app_context():
        for key, config_data in RETRY_CONFIG.items():
            existing = SystemConfig.query.filter_by(config_key=key).first()

            if existing:
                logger.info(f"Config {key} already exists, skipping")
                continue

            SystemConfig.set_config(
                key=key,
                value=config_data['value'],
                config_type=config_data['type'],
                description=config_data['description'],
                category=config_data['category'],
                is_public=config_data.get('is_public', False)
            )

            logger.info(f"Created config: {key} = {config_data['value']}")

        db.session.commit()
        logger.info("Retry configuration seeding complete")


if __name__ == '__main__':
    seed_config()
```

---

## 11. Implementation Plan

### 11.1 Phase 1: Foundation (Week 1)

**Tasks:**
1. Database schema changes
   - Create migration for Story model enhancements
   - Create StoryFailure model and table
   - Test migration up/down

2. Error classification system
   - Implement `ErrorClassification` enum
   - Implement `ErrorClassifier` class
   - Write unit tests for classification logic

3. Configuration setup
   - Create retry configuration seed script
   - Run on dev/staging environments
   - Verify SystemConfig integration

**Deliverables:**
- Migration file (`XXXX_add_retry_and_dlq.py`)
- Error classification module (`error_classification.py`)
- Configuration seed script (`seed_retry_config.py`)
- Unit tests for error classification

**Success Criteria:**
- Migration runs successfully in dev
- All error patterns correctly classified
- Configuration loads from database

### 11.2 Phase 2: Retry Logic (Week 2)

**Tasks:**
1. Implement RetryService
   - Backoff calculation
   - Retry decision logic
   - DLQ sending logic
   - Unit tests

2. Create retry decorator
   - `@retry_workflow_step` implementation
   - Integration with workflow methods
   - Metrics recording

3. Queue service enhancements
   - Respect `next_retry_at` in queue selection
   - Priority handling for retries
   - Integration tests

**Deliverables:**
- `RetryService` class (`retry_service.py`)
- Retry decorator implementation
- Updated `StoryQueueService`
- Integration tests

**Success Criteria:**
- Retry logic correctly calculates backoffs
- Stories respect retry schedules
- Metrics recorded accurately

### 11.3 Phase 3: DLQ Service & Admin UI (Week 3)

**Tasks:**
1. Implement DLQService
   - CRUD operations for failures
   - Statistics gathering
   - Bulk operations
   - Unit tests

2. Admin routes
   - List view with filtering
   - Detail view
   - Retry actions
   - Status updates

3. Admin templates
   - DLQ list template
   - Detail template
   - Navigation integration

**Deliverables:**
- `DLQService` class (`dlq_service.py`)
- Admin routes (`admin/routes.py` additions)
- Admin templates (Jinja2)
- API endpoint documentation

**Success Criteria:**
- Admin can view all DLQ failures
- Filtering and pagination work correctly
- Manual retry functionality works
- Bulk operations execute successfully

### 11.4 Phase 4: Metrics & Monitoring (Week 4)

**Tasks:**
1. Implement retry metrics
   - Add new Prometheus metrics
   - Integration with MetricsService
   - Update `/metrics` endpoint

2. Grafana dashboard
   - Create retry/DLQ panels
   - Configure alerts
   - Documentation

3. Data migration
   - Run migration script for existing failures
   - Verify DLQ populated correctly
   - Cleanup old failed stories

**Deliverables:**
- Updated `metrics.py` with retry metrics
- Grafana dashboard JSON
- Migration script (`migrate_existing_failures.py`)
- Monitoring documentation

**Success Criteria:**
- All retry metrics appear in Prometheus
- Grafana dashboard displays correctly
- Legacy failures migrated to DLQ

### 11.5 Phase 5: Integration & Testing (Week 5)

**Tasks:**
1. End-to-end testing
   - Test all error classifications
   - Test retry flow
   - Test DLQ workflow
   - Load testing

2. Documentation
   - Admin user guide
   - Developer documentation
   - Runbook for common issues

3. Staging deployment
   - Deploy to staging
   - Monitor for 1 week
   - Fix any issues

**Deliverables:**
- E2E test suite
- User documentation
- Deployment guide
- Staging deployment

**Success Criteria:**
- All tests pass
- Documentation complete
- Staging runs successfully for 1 week
- No critical bugs found

---

## 12. Testing Strategy

### 12.1 Unit Tests

**File:** `tests/test_error_classification.py`

```python
import pytest
from ephergent_generator.utils.error_classification import (
    ErrorClassifier, ErrorClassification
)


class TestErrorClassifier:
    """Test error classification logic."""

    def test_transient_errors(self):
        """Test transient error classification."""
        errors = [
            TimeoutError("Connection timed out"),
            ConnectionError("Connection refused"),
        ]

        for exc in errors:
            assert ErrorClassifier.classify(exc) == ErrorClassification.TRANSIENT

    def test_rate_limit_errors(self):
        """Test rate limit error classification."""
        class HTTPError429(Exception):
            pass

        exc = HTTPError429("429 Too Many Requests")
        # Would need to mock response attribute
        # This is pseudocode

    def test_configuration_errors(self):
        """Test configuration error classification."""
        errors = [
            KeyError("api_key"),
            AttributeError("'NoneType' has no attribute 'get'"),
        ]

        for exc in errors:
            assert ErrorClassifier.classify(exc) == ErrorClassification.CONFIGURATION

    def test_should_retry(self):
        """Test retry decision logic."""
        assert ErrorClassifier.should_retry(ErrorClassification.TRANSIENT) is True
        assert ErrorClassifier.should_retry(ErrorClassification.PERMANENT) is False
```

**File:** `tests/test_retry_service.py`

```python
import pytest
from datetime import datetime, timedelta
from ephergent_generator.services.retry_service import RetryService
from ephergent_generator.utils.error_classification import ErrorClassification
from ephergent_generator.models import Story, WorkflowStep


class TestRetryService:
    """Test retry service functionality."""

    @pytest.fixture
    def retry_service(self):
        return RetryService()

    @pytest.fixture
    def story(self, db_session):
        story = Story(
            topic="Test story",
            current_step=WorkflowStep.IMAGE_GENERATION,
            retry_count=0,
            max_retries=5
        )
        db_session.add(story)
        db_session.commit()
        return story

    def test_calculate_backoff_transient(self, retry_service):
        """Test backoff calculation for transient errors."""
        # First attempt (0)
        backoff = retry_service.calculate_backoff(0, ErrorClassification.TRANSIENT)
        assert backoff == 60  # Base delay

        # Second attempt (1)
        backoff = retry_service.calculate_backoff(1, ErrorClassification.TRANSIENT)
        assert 100 <= backoff <= 140  # 120 ± jitter

    def test_handle_failure_retry(self, retry_service, story):
        """Test failure handling that results in retry."""
        exception = TimeoutError("Connection timeout")

        result = retry_service.handle_failure(
            story, exception, WorkflowStep.IMAGE_GENERATION
        )

        assert result is True  # Should retry
        assert story.retry_count == 1
        assert story.error_classification == 'transient'
        assert story.next_retry_at is not None

    def test_handle_failure_dlq_permanent(self, retry_service, story, db_session):
        """Test failure handling that sends to DLQ."""
        exception = ValueError("Invalid data")

        result = retry_service.handle_failure(
            story, exception, WorkflowStep.IMAGE_GENERATION
        )

        assert result is False  # Should not retry
        assert story.current_step == WorkflowStep.FAILED

        # Verify DLQ entry created
        from ephergent_generator.models import StoryFailure
        failure = StoryFailure.query.filter_by(story_id=story.id).first()
        assert failure is not None
        assert failure.error_classification == 'validation'
```

### 12.2 Integration Tests

**File:** `tests/test_workflow_retry_integration.py`

```python
import pytest
from unittest.mock import patch, MagicMock
from ephergent_generator.services.workflow_service import StoryWorkflowService
from ephergent_generator.models import Story, WorkflowStep


class TestWorkflowRetryIntegration:
    """Integration tests for workflow retry logic."""

    @pytest.fixture
    def workflow_service(self):
        return StoryWorkflowService()

    @pytest.fixture
    def story(self, db_session):
        story = Story(
            topic="Integration test story",
            current_step=WorkflowStep.IMAGE_GENERATION,
            title="Test Title",
            content="Test content",
            retry_count=0
        )
        db_session.add(story)
        db_session.commit()
        return story

    @patch('ephergent_generator.services.image_service.ImageService.generate_story_images')
    def test_transient_failure_retry(self, mock_generate, workflow_service, story, db_session):
        """Test that transient failures trigger retry."""
        # Mock service to raise timeout on first call, succeed on second
        mock_generate.side_effect = [
            TimeoutError("Connection timeout"),
            {'feature': '/path/to/image.png'}
        ]

        # First attempt - should fail and schedule retry
        result = workflow_service._process_image_generation(story)
        assert result is False
        assert story.retry_count == 1
        assert story.next_retry_at is not None

        # Simulate retry after backoff period
        story.next_retry_at = datetime.utcnow() - timedelta(seconds=1)
        db_session.commit()

        # Second attempt - should succeed
        result = workflow_service._process_image_generation(story)
        assert result is True
        assert story.retry_count == 0  # Reset on success
        assert story.current_step == WorkflowStep.AUDIO_GENERATION
```

### 12.3 Load Tests

**File:** `tests/load_test_retry_system.py`

```python
import pytest
import time
from concurrent.futures import ThreadPoolExecutor
from ephergent_generator.models import Story, WorkflowStep
from ephergent_generator.services.retry_service import RetryService


class TestRetrySystemLoad:
    """Load tests for retry system under concurrent load."""

    def test_concurrent_retry_scheduling(self, db_session):
        """Test retry scheduling under concurrent load."""
        retry_service = RetryService()

        # Create 100 stories
        stories = []
        for i in range(100):
            story = Story(
                topic=f"Load test story {i}",
                current_step=WorkflowStep.IMAGE_GENERATION,
                retry_count=0
            )
            db_session.add(story)
            stories.append(story)

        db_session.commit()

        # Simulate concurrent failures
        def fail_story(story):
            exception = TimeoutError("Load test timeout")
            return retry_service.handle_failure(
                story, exception, WorkflowStep.IMAGE_GENERATION
            )

        with ThreadPoolExecutor(max_workers=10) as executor:
            start = time.time()
            results = list(executor.map(fail_story, stories))
            duration = time.time() - start

        # Verify all scheduled for retry
        assert all(results)
        assert duration < 5.0  # Should complete in < 5 seconds

        # Verify database state
        for story in stories:
            db_session.refresh(story)
            assert story.retry_count == 1
            assert story.next_retry_at is not None
```

---

## 13. Rollout Plan

### 13.1 Pre-Deployment Checklist

- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Load tests passing
- [ ] Database migration tested in staging
- [ ] Retry configuration seeded
- [ ] Admin UI tested manually
- [ ] Metrics verified in staging Prometheus
- [ ] Grafana dashboard created and tested
- [ ] Documentation complete
- [ ] Runbook prepared

### 13.2 Deployment Sequence

**Step 1: Database Migration (Maintenance Window)**
```bash
# Backup database
pg_dump ephergent_prod > backup_pre_retry_$(date +%Y%m%d).sql

# Run migration
flask db upgrade

# Verify migration
flask db current
```

**Step 2: Seed Configuration**
```bash
python scripts/seed_retry_config.py
```

**Step 3: Migrate Existing Failures**
```bash
python scripts/migrate_existing_failures.py
```

**Step 4: Deploy Application Code**
```bash
# Deploy new code with retry system
git pull origin main
pip install -r requirements.txt

# Restart services
systemctl restart ephergent-web
systemctl restart ephergent-worker
```

**Step 5: Verify Deployment**
```bash
# Check metrics endpoint
curl http://localhost:5000/metrics | grep retry

# Check DLQ admin UI
# Navigate to /admin/dlq

# Monitor logs
tail -f logs/season_03_generator.log | grep -i retry
```

### 13.3 Rollback Plan

If critical issues are discovered:

1. **Stop workers** to prevent new retries
   ```bash
   systemctl stop ephergent-worker
   ```

2. **Revert code** to previous version
   ```bash
   git checkout <previous-commit>
   systemctl restart ephergent-web
   ```

3. **Rollback database** if necessary
   ```bash
   flask db downgrade
   ```

4. **Restore from backup** (last resort)
   ```bash
   psql ephergent_prod < backup_pre_retry_YYYYMMDD.sql
   ```

### 13.4 Monitoring Plan

**First 24 Hours:**
- Monitor retry metrics every hour
- Check DLQ size growth
- Verify retry success rate > 50%
- Check for worker timeouts
- Monitor database performance

**First Week:**
- Daily review of DLQ failures
- Classify any new error patterns
- Adjust retry configuration if needed
- Monitor system resource usage

**First Month:**
- Weekly DLQ cleanup
- Analyze retry success patterns
- Tune backoff parameters
- Update documentation based on learnings

---

## 14. Appendix

### 14.1 Configuration Reference

| Config Key | Default | Type | Description |
|-----------|---------|------|-------------|
| `retry.max_attempts` | 5 | int | Maximum retry attempts per step |
| `retry.transient.base_delay_seconds` | 60 | int | Base delay for transient errors (1 min) |
| `retry.rate_limit.base_delay_seconds` | 300 | int | Base delay for rate limits (5 min) |
| `retry.resource.base_delay_seconds` | 120 | int | Base delay for resource errors (2 min) |
| `retry.exponential_backoff_multiplier` | 2.0 | float | Exponential backoff multiplier |
| `retry.enable_jitter` | true | bool | Enable random jitter (±20%) |

### 14.2 Error Classification Decision Tree

```
Exception Occurred
    │
    ├─ Is HTTP status 429? ──> RATE_LIMIT
    ├─ Is HTTP 5xx? ──> TRANSIENT
    ├─ Is HTTP 401/403? ──> CONFIGURATION
    ├─ Is TimeoutError/ConnectionError? ──> TRANSIENT
    ├─ Is KeyError/AttributeError? ──> CONFIGURATION
    ├─ Is ValueError/TypeError? ──> VALIDATION
    ├─ Is OSError/IOError? ──> RESOURCE
    ├─ Message contains "api key"? ──> CONFIGURATION
    ├─ Message contains "rate limit"? ──> RATE_LIMIT
    ├─ Message contains "timeout"? ──> TRANSIENT
    └─ Default ──> PERMANENT
```

### 14.3 Retry Backoff Tables

**Transient Errors (base=60s, multiplier=2.0, jitter=±20%):**

| Attempt | Delay (no jitter) | Delay Range (with jitter) |
|---------|-------------------|---------------------------|
| 1 | 60s | 48s - 72s |
| 2 | 120s | 96s - 144s |
| 3 | 240s | 192s - 288s |
| 4 | 480s | 384s - 576s |
| 5 | 960s | 768s - 1152s |

**Rate Limit Errors (base=300s, multiplier=2.0, no jitter):**

| Attempt | Delay |
|---------|-------|
| 1 | 300s (5 min) |
| 2 | 600s (10 min) |
| 3 | 1200s (20 min) |
| 4 | 2400s (40 min) |
| 5 | 3600s (60 min) |

### 14.4 DLQ Status Workflow

```
pending ──> investigating ──> resolved
   │                             │
   └──────> archived <───────────┘
```

**Status Definitions:**
- **pending**: New failure awaiting review
- **investigating**: Admin is actively investigating
- **resolved**: Issue fixed, story retried successfully
- **archived**: Permanently archived (no further action)

---

## Summary

This design provides a comprehensive, production-ready error handling and recovery system for the Ephergent story generation workflow. Key highlights:

1. **Automatic Retry**: Intelligent retry logic with exponential backoff and error-specific strategies
2. **Error Classification**: Robust classification system distinguishing transient vs. permanent failures
3. **Dead Letter Queue**: Comprehensive DLQ for failed stories with admin UI
4. **Partial Regeneration**: Ability to resume from specific workflow steps
5. **Metrics & Monitoring**: Full Prometheus integration with Grafana dashboards
6. **Production Ready**: Migration scripts, testing strategy, and rollout plan included

**Implementation Timeline:** 5 weeks
**Estimated Lines of Code:** ~3,000 LOC (excluding tests)
**Test Coverage Target:** 85%+

This design follows Python/Flask best practices, leverages the existing SystemConfig and metrics infrastructure, and provides a scalable foundation for production error handling.
